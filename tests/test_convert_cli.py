from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tarfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

from vss.convert.czml import emit_czml_from_scene, parse_czml_file_to_scene
from vss.convert.orb import emit_orb_from_scene, parse_orb_to_scene
from vss.convert.simdis import emit_simdis_asi_from_scene, parse_simdis_asi_to_scene
from vss.convert.soap import emit_soap_envelope_from_scene, parse_soap_to_scene
from vss.orb import build_orb_fixture_set

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"

SIMDIS_ASI_EXAMPLE = REPO_ROOT / "examples/generated/air-track.simdis.txt"
SOAP_EXAMPLE = REPO_ROOT / "examples/generated/air-track.soap.xml"
CZML_EXAMPLE = REPO_ROOT / "examples/generated/air-pair.scene.czml.json"
SCENE_EXAMPLE = REPO_ROOT / "examples/scenes/air-pair.scene.json"


def _run_cli(*args: str) -> None:
    env = dict(os.environ)
    current = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(SRC_ROOT) + (os.pathsep + current if current else "")
    result = subprocess.run(
        [sys.executable, "-m", "vss.cli", *args],
        check=True,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        env=env,
    )
    assert result.returncode == 0


def test_simdis_asi_parse_and_emit_round_trip() -> None:
    scene = parse_simdis_asi_to_scene(SIMDIS_ASI_EXAMPLE.read_text(encoding="utf-8"))
    assert len(scene.entities) == 1

    emitted = emit_simdis_asi_from_scene(scene)
    rebuilt = parse_simdis_asi_to_scene(emitted)

    assert "PLATFORM aircraft-001" in emitted
    assert "PLATFORM_UPDATE aircraft-001" in emitted
    assert len(rebuilt.entities) == 1
    assert rebuilt.entities[0].id == scene.entities[0].id
    assert rebuilt.entities[0].name == scene.entities[0].name
    assert rebuilt.entities[0].position == scene.entities[0].position
    original_simdis = dict(scene.entities[0].attributes.get("simdis", {}))
    rebuilt_simdis = dict(rebuilt.entities[0].attributes.get("simdis", {}))
    original_simdis.pop("platformIcon", None)
    rebuilt_simdis.pop("platformIcon", None)
    assert rebuilt_simdis == original_simdis


def test_soap_parse_and_emit_round_trip() -> None:
    scene = parse_soap_to_scene(SOAP_EXAMPLE)
    assert len(scene.entities) == 1

    emitted = emit_soap_envelope_from_scene(scene)
    rebuilt = parse_soap_to_scene(emitted)
    assert "EntityUpsertMessage" in emitted
    assert "aircraft-001" in emitted
    assert len(rebuilt.entities) == 1
    assert rebuilt.entities[0].id == scene.entities[0].id
    assert rebuilt.entities[0].name == scene.entities[0].name
    assert rebuilt.entities[0].position == scene.entities[0].position
    assert rebuilt.entities[0].orientation == scene.entities[0].orientation
    assert rebuilt.entities[0].style == scene.entities[0].style
    assert rebuilt.entities[0].attributes == scene.entities[0].attributes


def test_czml_parse_and_emit_round_trip() -> None:
    scene = parse_czml_file_to_scene(CZML_EXAMPLE)
    assert len(scene.entities) == 2

    emitted = emit_czml_from_scene(scene)
    packets = json.loads(emitted)

    assert packets[0]["id"] == "document"
    assert packets[1]["id"] == "aircraft-001"


def test_orb_parse_and_emit_round_trip() -> None:
    orb_text = (
        "56 revision\n"
        "SOAP_SCENARIO_FILE\n"
        'DEFINE PLATFORM AIR "Air"\n'
        "\tWAYPOINT 33.93 -118.4 1\n"
    )

    scene = parse_orb_to_scene(orb_text)
    assert len(scene.entities) == 1

    emitted = emit_orb_from_scene(scene)
    parsed = parse_orb_to_scene(emitted)

    assert len(parsed.entities) == 1
    assert emitted.startswith("56 revision")
    assert "DEFINE PLATFORM" in emitted


def test_orb_raw_text_is_not_treated_as_path() -> None:
    orb_text = "56 revision\nSOAP_SCENARIO_FILE\n" + ('DEFINE PLATFORM AIR "Air"\n\tWAYPOINT 33.93 -118.4 1\n' * 200)

    scene = parse_orb_to_scene(orb_text)

    assert len(scene.entities) >= 1


def test_build_orb_fixture_set_from_archive(tmp_path: Path) -> None:
    archive_path = tmp_path / "fixtures.tar"
    with tarfile.open(archive_path, "w") as handle:
        demo = (
            "56 revision\n"
            "SOAP_SCENARIO_FILE\n"
            'DEFINE PLATFORM AIR "Air"\n'
            "\tWAYPOINT 33.93 -118.4 1\n"
        ).encode("utf-8")
        for name in ("demo.orb", "nested/second.orb"):
            info = tarfile.TarInfo(name=f"orb_format_collection/{name}")
            info.size = len(demo)
            handle.addfile(info, fileobj=io.BytesIO(demo))

    output_root = tmp_path / "out"
    manifest = build_orb_fixture_set(archive_path, output_root)

    assert manifest.totals["orbFiles"] == 2
    assert manifest.totals["parsed"] == 2
    assert (output_root / "manifest.json").exists()
    assert (output_root / "sdj" / "orb_format_collection" / "demo.sdj.json").exists()
    assert (output_root / "cesium" / "orb_format_collection" / "demo.czml.json").exists()
    assert (output_root / "soap" / "orb_format_collection" / "demo.bundle.json").exists()


@pytest.mark.parametrize(
    "mode, source, expected",
    [
        (
            "ingest",
            "czml",
            "aircraft-001",
        ),
        (
            "ingest",
            "simdis-asi",
            "aircraft-001",
        ),
        (
            "ingest",
            "soap",
            "aircraft-001",
        ),
        (
            "emit",
            "simdis-asi",
            "PLATFORM",
        ),
        (
            "emit",
            "soap",
            "EntityUpsertMessage",
        ),
    ],
)
def test_cli_modes(mode: str, source: str, expected: str, tmp_path: Path) -> None:
    if mode == "ingest":
        output = tmp_path / "scene.json"
        input_path = CZML_EXAMPLE if source == "czml" else SIMDIS_ASI_EXAMPLE if source == "simdis-asi" else SOAP_EXAMPLE
        _run_cli("ingest", "--input", str(input_path), "--output", str(output), "--format", "soap" if source == "soap" else source)
        assert expected in output.read_text(encoding="utf-8")
    else:
        output = tmp_path / f"scene.{source}"
        ext = "txt" if source == "simdis-asi" else "xml" if source == "soap" else source
        output = tmp_path / f"out.{ext}"
        _run_cli(
            "emit",
            "--input",
            str(SCENE_EXAMPLE),
            "--output",
            str(output),
            "--format",
            source,
        )
        assert expected in output.read_text(encoding="utf-8")
