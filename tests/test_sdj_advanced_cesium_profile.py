from __future__ import annotations

import json
from pathlib import Path


PACKAGE_DIR = Path("reference/sdj_v0_5_advanced_cesium_profile")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_advanced_cesium_profile_contains_expected_deliverables() -> None:
    expected = {
        "README.md",
        "sdj_cesium_loader_v0_5.js",
        "sdj_multi_backend_compiler_v0_5.mjs",
        "sdj_acceptance_runner_v0_5.mjs",
        "examples/sdj_advanced_cesium_scene_v0_5.json",
        "schemas/sdj-core.schema.json",
        "schemas/sdj-cesium-advanced.schema.json",
        "schemas/sdj-tactical.schema.json",
        "schemas/sdj-analysis.schema.json",
        "schemas/sdj-presentation.schema.json",
        "schemas/sdj_v0_5.schema.json",
        "data/sdj_backend_capabilities_v0_5.json",
        "data/sdj_exposed_scenes_manifest_v0_5.json",
        "data/coverage_portfolio_v0_5.json",
        "reports/acceptance-report.json",
        "reports/acceptance-report.md",
        "reports/coverage-matrix.csv",
        "reports/backend-diagnostics.json",
        "sdj_workbench_v0_3/package.json",
        "sdj_workbench_v0_3/index.html",
    }
    discovered = {str(path.relative_to(PACKAGE_DIR)) for path in PACKAGE_DIR.rglob("*") if path.is_file()}
    assert expected.issubset(discovered)


def test_advanced_scene_covers_attachment_graph_and_advanced_kinds() -> None:
    scene = _load_json(PACKAGE_DIR / "examples/sdj_advanced_cesium_scene_v0_5.json")
    objects = scene["objects"]
    object_by_id = {obj["id"]: obj for obj in objects}
    kinds = {obj["kind"] for obj in objects}
    ids = {obj["id"] for obj in objects}

    assert scene["schemaVersion"] == "sdj-0.5"
    assert scene["profiles"] == ["sdj-cesium-advanced"]
    assert len(objects) == 20
    assert {
        "tileset",
        "gaussianSplatTileset",
        "tilesetStyle",
        "clippingPlane",
        "clippingPolygon",
        "customShader",
        "classificationPrimitive",
        "groundPolyline",
        "groundPrimitive",
        "terrain",
        "imageryLayer",
        "dataSource",
        "postProcessStage",
        "voxel",
        "cloudCollection",
    } <= kinds
    assert {"downtown-tiles-style", "downtown-clip-planes", "downtown-custom-shader"} <= ids
    assert object_by_id["downtown-tiles-style"]["target"] == "downtown-tileset"
    assert object_by_id["downtown-clip-planes"]["target"] == "downtown-tileset"
    assert object_by_id["downtown-clip-polygon"]["target"] == "downtown-tileset"
    assert object_by_id["downtown-custom-shader"]["target"] == "downtown-tileset"
    assert object_by_id["restricted-area-classification"]["target"] == "scene"
    assert object_by_id["world-terrain"]["target"] == "scene"
    assert object_by_id["base-imagery"]["target"] == "scene"
    assert object_by_id["night-vision-stage"]["target"] == "scene"
    for obj in objects:
        assert obj["profiles"] == ["sdj-cesium-advanced"]
        assert set(obj["expectedBackends"]) == {"cesium", "simdis", "soap"}


def test_acceptance_report_matches_coverage_portfolio() -> None:
    report = _load_json(PACKAGE_DIR / "reports/acceptance-report.json")
    coverage = _load_json(PACKAGE_DIR / "data/coverage_portfolio_v0_5.json")

    assert report["schemaVersion"] == "sdj-acceptance-report-0.5"
    assert report["sceneId"] == "sdj-advanced-cesium-v0-5"
    assert len(report["records"]) == len(coverage["features"]) == 13
    assert report["diagnostics"]["semanticErrors"] == []
    assert report["compilePlanTotals"]["cesium"]["strong"] == 20
    assert report["diagnostics"]["advancedDiagnostics"]

    record_by_feature = {record["feature"]: record for record in report["records"]}
    for feature in coverage["features"]:
        record = record_by_feature[feature["feature"]]
        assert record["examplePresent"] is True
        assert record["schemaValid"] is True
        assert record["semanticValid"] is True
        assert record["workbenchInspectorPresent"] is True
        assert record["exampleObjectId"] == feature["exampleObjectId"]


def test_backend_diagnostics_capture_support_classes() -> None:
    diagnostics = _load_json(PACKAGE_DIR / "reports/backend-diagnostics.json")

    by_feature = {entry["feature"]: entry for entry in diagnostics}
    assert by_feature["tilesetStyle"]["simdis"]["supportClass"] == "unsupported"
    assert by_feature["clippingPolygon"]["simdis"]["supportClass"] == "lossy geometry fallback"
    assert by_feature["gaussianSplatTileset"]["soap"]["supportClass"] == "metadata-only"
    assert by_feature["groundPolyline"]["soap"]["supportClass"] == "native-ish"

    acceptance = _load_json(PACKAGE_DIR / "reports/acceptance-report.json")
    advanced = acceptance["diagnostics"]["advancedDiagnostics"]
    assert any(item["backend"] == "simdis" and item["objectId"] == "downtown-tiles-style" for item in advanced)
    assert any(item["backend"] == "soap" and item["objectId"] == "night-vision-stage" for item in advanced)
