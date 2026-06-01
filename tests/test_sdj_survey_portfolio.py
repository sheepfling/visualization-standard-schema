from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

SURVEY_DIR = Path("reference/sdj_survey_v0_5")


def _load_json(member: str) -> dict:
    return json.loads((SURVEY_DIR / member).read_text(encoding="utf-8"))


def _read_text(member: str) -> str:
    return (SURVEY_DIR / member).read_text(encoding="utf-8")


def test_survey_package_contains_expected_artifacts() -> None:
    expected = {
        "README.md",
        "sdj_schema_modules_v0_5.json",
        "sdj_feature_inventory_v0_5.json",
        "sdj_portfolio_scene_seed_v0_5.json",
        "sdj_survey_portfolio_v0_5.md",
        "sdj_coverage_backlog_v0_5.md",
        "sdj_acceptance_matrix_v0_5.md",
    }
    assert expected.issubset({path.name for path in SURVEY_DIR.iterdir()})


def test_feature_inventory_describes_the_full_sdj_expose() -> None:
    inventory = _load_json("sdj_feature_inventory_v0_5.json")
    features = inventory["features"]

    assert inventory["schemaVersion"] == "sdj-survey-0.5"
    assert inventory["generatedFor"] == "Spatial Display JSON coverage survey"
    assert inventory["featureCount"] == len(features) == 144

    feature_ids = [feature["id"] for feature in features]
    assert len(feature_ids) == len(set(feature_ids))

    allowed_statuses = {"existing", "proposed", "partial"}
    allowed_examples = {"existing", "existing-hidden", "needed", "mixed"}
    allowed_runtime = {"strong", "partial", "reserved", "weak", "unsupported"}
    allowed_priorities = {"P0", "P1", "P2", "P3"}

    for feature in features:
        assert set(feature.keys()) == {"id", "category", "sdjKind", "description", "status", "priority", "notes"}
        assert feature["id"]
        assert feature["category"]
        assert feature["sdjKind"]
        assert feature["description"]
        assert feature["priority"] in allowed_priorities

        status = feature["status"]
        assert set(status.keys()) == {"schema", "example", "cesiumRuntime", "simdisExport", "soapExport"}
        assert status["schema"] in allowed_statuses
        assert status["example"] in allowed_examples
        assert status["cesiumRuntime"] in allowed_runtime
        assert status["simdisExport"] in allowed_runtime
        assert status["soapExport"] in allowed_runtime

    assert Counter(feature["priority"] for feature in features) == Counter({"P1": 70, "P0": 61, "P2": 11, "P3": 2})
    assert Counter(feature["status"]["schema"] for feature in features) == Counter({"existing": 97, "proposed": 43, "partial": 4})


def test_schema_modules_cover_the_expected_family_surface() -> None:
    schema_modules = _load_json("sdj_schema_modules_v0_5.json")
    families = schema_modules["moduleFamilies"]

    assert schema_modules["schemaVersion"] == "sdj-survey-0.5"
    assert schema_modules["recommendedSdjVersion"] == "sdj-0.5"
    assert len(families) == 10

    family_ids = {family["id"] for family in families}
    assert family_ids == {
        "sdj-core",
        "sdj-temporal-properties",
        "sdj-frames-and-pose",
        "sdj-czml-parity",
        "sdj-cesium-advanced",
        "sdj-tactical-geometry",
        "sdj-trajectory-diagnostics",
        "sdj-analysis-products",
        "sdj-presentation",
        "sdj-backend-bindings",
    }

    for family in families:
        assert family["purpose"]
        assert isinstance(family["required"], bool)
        if family["id"] in {"sdj-core", "sdj-temporal-properties", "sdj-frames-and-pose", "sdj-czml-parity", "sdj-backend-bindings"}:
            assert family["required"] is True
        else:
            assert family["required"] is False
        if "sections" in family:
            assert family["sections"]
        if "objectKinds" in family:
            assert family["objectKinds"]
        if "analysisKinds" in family:
            assert family["analysisKinds"]
        if "presentationKinds" in family:
            assert family["presentationKinds"]


def test_seed_scene_spans_the_survey_surface_and_flags_known_gaps() -> None:
    seed = _load_json("sdj_portfolio_scene_seed_v0_5.json")
    inventory = _load_json("sdj_feature_inventory_v0_5.json")

    assert seed["schemaVersion"] == "sdj-0.5-portfolio-seed"
    assert seed["document"] == {"id": "sdj-portfolio-seed-v0-5", "name": "SDJ portfolio seed scene"}
    assert seed["units"] == {"linear": "meter", "angular": "degree", "time": "iso8601"}
    assert seed["clock"]["shouldAnimate"] is True
    assert len(seed["objects"]) == 61
    assert len({obj["kind"] for obj in seed["objects"]}) == 60
    assert len(seed["analysis"]) == 2
    assert len(seed["presentation"]) == 2

    inventory_kinds = {feature["sdjKind"] for feature in inventory["features"]}
    seed_kinds = {obj["kind"] for obj in seed["objects"]}

    assert seed_kinds - inventory_kinds == {"tilesetStyle", "voxel"}
    assert {"gaussianSplatTileset", "pointCloudTileset", "tileset", "model", "customShader"} <= inventory_kinds
    assert {"accessIntervals", "rfLinkBudget"} <= {item["kind"] for item in seed["analysis"]}
    assert {"slide", "view"} <= {item["kind"] for item in seed["presentation"]}


def test_acceptance_matrix_includes_all_gates() -> None:
    matrix = _read_text("sdj_acceptance_matrix_v0_5.md")
    for gate in range(1, 11):
        assert f"| G{gate} " in matrix
