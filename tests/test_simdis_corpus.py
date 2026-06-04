from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vss.convert.simdis import parse_simdis_asi_to_scene, parse_simdis_bundle_to_scene
from vss.simdis import (
    compile_simdis_asi,
    compile_simdis_scene,
    load_simdis_bundle_files,
    parse_simdis_gog_text,
    parse_simdis_gog_to_scene,
    render_simdis_gog_text,
    serialize_simdis_bundle_files,
    write_simdis_bundle,
)

CORPUS_ROOT = Path("tests/fixtures/simdis/simdis_corpus_v0_1")
CORPUS_MANIFEST_PATH = CORPUS_ROOT / "manifests" / "corpus-file-manifest.json"
ASI_FIXTURES = sorted((CORPUS_ROOT / "public_seed" / "asi").glob("*.asi"))
GOG_FIXTURES = sorted((CORPUS_ROOT / "public_seed" / "gog").glob("*.gog"))
DISCN_FIXTURES = sorted((CORPUS_ROOT / "inferred" / "discn").glob("*.discn"))


def _load_corpus_manifest() -> dict[str, object]:
    return json.loads(CORPUS_MANIFEST_PATH.read_text(encoding="utf-8"))


def _scene_signature(scene) -> dict[str, object]:
    return {
        "entity_ids": [entity.id for entity in scene.entities],
        "entity_names": [entity.name for entity in scene.entities],
        "entity_categories": [entity.category.value if entity.category else None for entity in scene.entities],
        "entity_timestamps": [entity.timestamp.isoformat() if entity.timestamp else None for entity in scene.entities],
        "platform_sample_counts": [
            len((entity.attributes or {}).get("simdis", {}).get("platformSamples", [])) for entity in scene.entities
        ],
        "beam_ids": [
            sorted(
                beam.get("beamId")
                for beam in (entity.attributes or {}).get("simdis", {}).get("beams", [])
                if isinstance(beam, dict)
            )
            for entity in scene.entities
        ],
        "gate_ids": [
            sorted(
                gate.get("gateId")
                for gate in (entity.attributes or {}).get("simdis", {}).get("gates", [])
                if isinstance(gate, dict)
            )
            for entity in scene.entities
        ],
        "projector_ids": [
            sorted(
                projector.get("projectorId")
                for projector in (entity.attributes or {}).get("simdis", {}).get("projectors", [])
                if isinstance(projector, dict)
            )
            for entity in scene.entities
        ],
        "overlay_ids": [overlay.id for overlay in scene.overlays],
        "overlay_geometry_types": [overlay.geometryType for overlay in scene.overlays],
        "overlay_vertex_counts": [
            len(overlay.polyline.positions)
            if overlay.polyline is not None
            else len(overlay.polygon.positions)
            if overlay.polygon is not None
            else 0
            for overlay in scene.overlays
        ],
    }


def _bundle_scene_signature(scene) -> dict[str, object]:
    return {
        "entity_ids": [entity.id for entity in scene.entities],
        "entity_names": [entity.name for entity in scene.entities],
        "entity_positions": [
            {
                "longitudeDeg": entity.position.longitudeDeg,
                "latitudeDeg": entity.position.latitudeDeg,
                "altitudeM": entity.position.altitudeM,
            }
            for entity in scene.entities
        ],
        "overlay_ids": [overlay.id for overlay in scene.overlays],
        "overlay_geometry_types": [overlay.geometryType for overlay in scene.overlays],
        "overlay_vertex_counts": [
            len(overlay.polyline.positions)
            if overlay.polyline is not None
            else len(overlay.polygon.positions)
            if overlay.polygon is not None
            else 0
            for overlay in scene.overlays
        ],
    }


@pytest.mark.parametrize("entry", _load_corpus_manifest()["files"], ids=lambda item: item["path"])
def test_simdis_corpus_fixture_file_hashes_match_manifest(entry: dict[str, object]) -> None:
    relative_path = Path(str(entry["path"]))
    fixture_path = CORPUS_ROOT / relative_path
    assert fixture_path.is_file(), f"missing fixture file: {relative_path}"
    expected_sha256 = str(entry["sha256"])
    actual_sha256 = hashlib.sha256(fixture_path.read_bytes()).hexdigest()
    assert actual_sha256 == expected_sha256


@pytest.mark.parametrize("path", ASI_FIXTURES + DISCN_FIXTURES, ids=lambda item: item.name)
def test_simdis_asi_like_fixture_files_round_trip(path: Path, tmp_path: Path) -> None:
    raw_text = path.read_text(encoding="utf-8")
    scene = parse_simdis_asi_to_scene(raw_text, source=path.stem)
    compiled = compile_simdis_asi(scene)
    rebuilt = parse_simdis_asi_to_scene(compiled, source=f"{path.stem}:roundtrip")

    assert _scene_signature(rebuilt) == _scene_signature(scene)
    assert compiled.strip()
    assert "ReferenceYear" in compiled
    assert "PlatformID" in compiled

    bundle = compile_simdis_scene(scene)
    files = serialize_simdis_bundle_files(bundle)
    assert "simdis/entities.json" in files
    assert "simdis/entities.normalized.json" in files
    assert "simdis/overlays.gog" in files
    assert "simdis/overlays.normalized.json" in files

    rebuilt_bundle = load_simdis_bundle_files(files)
    assert [entity.id for entity in rebuilt_bundle.entities.platforms] == [entity.id for entity in scene.entities]
    assert rebuilt_bundle.manifest.target == "simdis"
    assert rebuilt_bundle.scenarioAsi

    written = write_simdis_bundle(bundle, tmp_path)
    assert "simdis/entities.normalized.json" in written
    assert "simdis/overlays.normalized.json" in written
    rebuilt_scene = parse_simdis_bundle_to_scene(tmp_path)
    assert _bundle_scene_signature(rebuilt_scene) == _bundle_scene_signature(scene)


@pytest.mark.parametrize("path", GOG_FIXTURES, ids=lambda item: item.name)
def test_simdis_gog_fixture_files_round_trip(path: Path, tmp_path: Path) -> None:
    raw_text = path.read_text(encoding="utf-8")
    document = parse_simdis_gog_text(raw_text, source=path.stem)
    rendered = render_simdis_gog_text(document)
    rebuilt = parse_simdis_gog_text(rendered, source=path.stem)

    assert rebuilt.model_dump(mode="json", exclude_none=True, exclude={"source"}) == document.model_dump(
        mode="json",
        exclude_none=True,
        exclude={"source"},
    )
    assert render_simdis_gog_text(rebuilt) == rendered

    scene = parse_simdis_gog_to_scene(raw_text, source=path.stem)
    bundle = compile_simdis_scene(scene)
    files = serialize_simdis_bundle_files(bundle)
    assert "simdis/entities.json" in files
    assert "simdis/entities.normalized.json" in files
    assert "simdis/overlays.gog" in files
    assert "simdis/overlays.normalized.json" in files

    rebuilt_bundle = load_simdis_bundle_files(files)
    assert rebuilt_bundle.manifest.target == "simdis"
    assert rebuilt_bundle.overlaysGog

    written = write_simdis_bundle(bundle, tmp_path)
    assert "simdis/entities.normalized.json" in written
    assert "simdis/overlays.normalized.json" in written
    rebuilt_scene = parse_simdis_bundle_to_scene(tmp_path)
    assert _bundle_scene_signature(rebuilt_scene) == _bundle_scene_signature(scene)


def test_simdis_corpus_fixture_paths_cover_all_tracked_samples() -> None:
    manifest = _load_corpus_manifest()
    tracked_paths = {str(item["path"]) for item in manifest["files"]}
    tracked_paths.add("manifests/corpus-file-manifest.json")

    fixture_paths = {
        str(path.relative_to(CORPUS_ROOT).as_posix())
        for path in CORPUS_ROOT.rglob("*")
        if path.is_file()
    }

    assert tracked_paths == fixture_paths
