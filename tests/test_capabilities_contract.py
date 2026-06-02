from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vss.capabilities import _load_scene_feature_count_rules
from vss.capabilities import get_cesium_capabilities
from vss.capabilities import get_simdis_capabilities
from vss.capabilities import get_soap_capabilities


def _load_ts_cesium_kind_targets() -> dict[str, dict[str, str]]:
    result = subprocess.run(
        [
            "node",
            "--experimental-strip-types",
            "-e",
            "import { CESIUM_KIND_TARGETS } from './reference/sdj_core_v0_1/src/index.ts'; console.log(JSON.stringify(CESIUM_KIND_TARGETS));",
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    return json.loads(result.stdout)


def test_scene_feature_counter_table_covers_all_contract_features() -> None:
    contract_feature_ids = {
        feature.featureId
        for report in (get_cesium_capabilities(), get_simdis_capabilities(), get_soap_capabilities())
        for feature in report.schemaFeatures
    }

    rules = _load_scene_feature_count_rules()
    assert contract_feature_ids <= set(rules)


def test_scene_feature_count_rules_are_structurally_valid() -> None:
    rules = _load_scene_feature_count_rules()
    assert rules
    for feature_id, rule in rules.items():
        assert feature_id
        assert isinstance(rule.get("kind"), str) and rule["kind"].strip()


def test_ts_cesium_contract_is_total_and_matches_the_workbench_loader_shape() -> None:
    targets = _load_ts_cesium_kind_targets()
    assert targets
    assert all(target.get("status") == "implemented" for target in targets.values())
    assert {"point", "track", "tileset", "cameraView"} <= set(targets)
