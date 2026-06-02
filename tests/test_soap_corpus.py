from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vss.convert.soap import parse_soap_bundle_to_scene
from vss.soap import compile_soap_scene
from vss.soap import load_soap_bundle_files, parse_soap_bundle_json, serialize_soap_bundle_files
from vss.soap import write_soap_bundle


CORPUS_ROOT = Path("tests/fixtures/soap")
CORPUS_MANIFEST_PATH = CORPUS_ROOT / "manifests" / "corpus-file-manifest.json"
FORMAT_STATUS_PATH = CORPUS_ROOT / "manifests" / "format-status.json"
SOAP_FIXTURE_ROOT = CORPUS_ROOT / "orb_format_collection" / "soap15"
SOAP_FIXTURES = sorted(SOAP_FIXTURE_ROOT.rglob("*.bundle.json"))


def _load_manifest() -> dict[str, object]:
    return json.loads(CORPUS_MANIFEST_PATH.read_text(encoding="utf-8"))


def _load_format_status() -> dict[str, object]:
    return json.loads(FORMAT_STATUS_PATH.read_text(encoding="utf-8"))


def _scene_signature(scene) -> dict[str, object]:
    return {
        "entity_ids": [entity.id for entity in scene.entities],
        "entity_names": [entity.name for entity in scene.entities],
        "entity_categories": [entity.category.value if entity.category else None for entity in scene.entities],
        "entity_positions": [
            {
                "longitudeDeg": entity.position.longitudeDeg,
                "latitudeDeg": entity.position.latitudeDeg,
                "altitudeM": entity.position.altitudeM,
            }
            for entity in scene.entities
        ],
        "entity_timestamps": [entity.timestamp.isoformat() if entity.timestamp else None for entity in scene.entities],
    }


@pytest.mark.parametrize("entry", _load_manifest()["files"], ids=lambda item: item["path"])
def test_soap_corpus_fixture_file_hashes_match_manifest(entry: dict[str, object]) -> None:
    relative_path = Path(str(entry["path"]))
    fixture_path = CORPUS_ROOT / relative_path
    assert fixture_path.is_file(), f"missing fixture file: {relative_path}"
    expected_sha256 = str(entry["sha256"])
    actual_sha256 = hashlib.sha256(fixture_path.read_bytes()).hexdigest()
    assert actual_sha256 == expected_sha256


def test_soap_corpus_manifest_matches_tracked_bundle_samples() -> None:
    manifest = _load_manifest()
    tracked_paths = {str(item["path"]) for item in manifest["files"]}
    actual_paths = {
        str(path.relative_to(CORPUS_ROOT).as_posix())
        for path in SOAP_FIXTURE_ROOT.rglob("*.bundle.json")
    }

    assert len(tracked_paths) == 134
    assert tracked_paths == actual_paths


def test_soap_corpus_format_status_matches_tracked_bundle_samples() -> None:
    status = _load_format_status()
    formats = status["formats"]
    assert len(formats) == 1
    assert formats[0]["extension"] == ".bundle.json"
    assert formats[0]["includedSamples"] == len(SOAP_FIXTURES)


@pytest.mark.parametrize("path", SOAP_FIXTURES, ids=lambda item: item.name)
def test_soap_bundle_fixture_files_round_trip(path: Path, tmp_path: Path) -> None:
    raw_json = path.read_text(encoding="utf-8")
    bundle = parse_soap_bundle_json(raw_json)
    emitted = serialize_soap_bundle_files(bundle)
    rebuilt = load_soap_bundle_files(emitted)
    written = write_soap_bundle(bundle, tmp_path)
    rebuilt_scene = parse_soap_bundle_to_scene(tmp_path)
    recompiled_bundle = compile_soap_scene(rebuilt_scene)
    roundtrip_dir = tmp_path / "roundtrip"
    write_soap_bundle(recompiled_bundle, roundtrip_dir)
    roundtripped_scene = parse_soap_bundle_to_scene(roundtrip_dir)

    assert rebuilt.model_dump(mode="json", exclude_none=True) == bundle.model_dump(mode="json", exclude_none=True)
    assert set(emitted) == {
        "soap/manifest.json",
        "soap/scenario.json",
        "soap/views.json",
        "soap/analysis.json",
        "soap/presentation.json",
        "soap/assets.json",
        "soap/diagnostics.json",
        "soap/custom-objects.json",
        "soap/runtime-objects.json",
        "soap/generated/soap-example-bundle.json",
    }
    assert "soap/manifest.json" in written
    assert "soap/scenario.json" in written
    assert _scene_signature(roundtripped_scene) == _scene_signature(rebuilt_scene)


def test_soap_corpus_fixture_paths_cover_all_tracked_samples() -> None:
    manifest = _load_manifest()
    tracked_paths = {str(item["path"]) for item in manifest["files"]}
    actual_paths = {
        str(path.relative_to(CORPUS_ROOT).as_posix())
        for path in SOAP_FIXTURE_ROOT.rglob("*.bundle.json")
    }
    assert tracked_paths == actual_paths
