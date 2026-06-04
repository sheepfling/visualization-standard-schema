from __future__ import annotations

"""Corpus-driven SDJ round-trip tests for the supported native paths.

These tests deliberately keep the comparison surface narrow. The current SIMDIS
and SOAP importers preserve the SDJ entity identity and pose fields that matter
for the native export/import loop, but they do not fully reconstruct every
scene-level decoration from the source JSON corpus.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vss.convert.simdis import parse_simdis_bundle_to_scene
from vss.convert.soap import parse_soap_bundle_to_scene
from vss.io import load_scene_file
from vss.simdis import compile_simdis_scene, write_simdis_bundle
from vss.soap import compile_soap_scene, write_soap_bundle

pytestmark = pytest.mark.sdj_roundtrip

REPO_ROOT = Path(__file__).resolve().parents[1]
SDJ_MANIFEST_PATH = REPO_ROOT / "reference" / "sdj_workbench_v0_2" / "data" / "sdj_exposed_scenes_manifest.json"
SDJ_MANIFEST_DIR = SDJ_MANIFEST_PATH.parent


def _load_manifest() -> dict[str, object]:
    """Load the exposed SDJ scene manifest once and keep test IDs stable."""
    return json.loads(SDJ_MANIFEST_PATH.read_text(encoding="utf-8"))


def _scene_paths() -> list[Path]:
    """Return the concrete scene JSON files listed by the exposed corpus manifest."""
    manifest = _load_manifest()
    return sorted((SDJ_MANIFEST_DIR / Path(str(item["path"]))).resolve() for item in manifest["scenes"])


def _entity_signature(entity) -> dict[str, object]:
    """Track the stable fields we expect the native adapters to preserve."""
    return {
        "id": entity.id,
        "name": entity.name,
        "longitudeDeg": entity.position.longitudeDeg,
        "latitudeDeg": entity.position.latitudeDeg,
        "altitudeM": entity.position.altitudeM,
    }


def _simdis_scene_signature(scene) -> dict[str, object]:
    """SIMDIS round-trips preserve entity identity and pose for this corpus."""
    return {
        "entities": [_entity_signature(entity) for entity in scene.entities],
    }


def _soap_scene_signature(scene) -> dict[str, object]:
    """SOAP round-trips preserve entity identity and pose for this corpus."""
    return {
        "entities": [_entity_signature(entity) for entity in scene.entities],
    }


@pytest.mark.parametrize("entry", _load_manifest()["scenes"], ids=lambda item: item["path"])
def test_sdj_corpus_scene_files_are_all_present(entry: dict[str, object]) -> None:
    """Fail fast if the exposed SDJ manifest drifts away from the checked-in files."""
    relative_path = Path(str(entry["path"]))
    fixture_path = (SDJ_MANIFEST_DIR / relative_path).resolve()
    assert fixture_path.is_file(), f"missing SDJ corpus scene: {relative_path}"


def test_sdj_corpus_scene_manifest_matches_scene_files() -> None:
    """Keep the manifest and the actual scene tree in sync."""
    manifest = _load_manifest()
    tracked_paths = {str(item["path"]) for item in manifest["scenes"]}
    actual_paths = {
        str(path.relative_to(REPO_ROOT).as_posix())
        for path in _scene_paths()
    }

    assert manifest["totalCount"] == len(_scene_paths()) == 134
    assert tracked_paths == {
        "../../../" + path for path in actual_paths
    }


@pytest.mark.parametrize("path", _scene_paths(), ids=lambda item: item.name)
def test_sdj_scene_round_trip_through_simdis_native(path: Path, tmp_path: Path) -> None:
    """Round-trip an SDJ scene through the supported SIMDIS native bundle path."""
    scene = load_scene_file(path)
    bundle = compile_simdis_scene(scene)
    written = write_simdis_bundle(bundle, tmp_path / path.stem)
    assert "simdis/scenario.asi" in written
    assert "simdis/overlays.gog" in written

    rebuilt = parse_simdis_bundle_to_scene(tmp_path / path.stem)

    assert _simdis_scene_signature(rebuilt) == _simdis_scene_signature(scene)


@pytest.mark.parametrize("path", _scene_paths(), ids=lambda item: item.name)
def test_sdj_scene_round_trip_through_soap_native(path: Path, tmp_path: Path) -> None:
    """Round-trip an SDJ scene through the supported SOAP native bundle path."""
    scene = load_scene_file(path)
    bundle = compile_soap_scene(scene)
    written = write_soap_bundle(bundle, tmp_path / path.stem)
    assert "soap/scenario.json" in written
    assert "soap/generated/soap-example-bundle.json" in written

    rebuilt = parse_soap_bundle_to_scene(tmp_path / path.stem)

    assert _soap_scene_signature(rebuilt) == _soap_scene_signature(scene)
