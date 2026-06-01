from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vss.capabilities import _SCENE_FEATURE_COUNTERS
from vss.capabilities import get_cesium_capabilities
from vss.capabilities import get_simdis_capabilities
from vss.capabilities import get_soap_capabilities


def test_scene_feature_counter_table_covers_all_contract_features() -> None:
    contract_feature_ids = {
        feature.featureId
        for report in (get_cesium_capabilities(), get_simdis_capabilities(), get_soap_capabilities())
        for feature in report.schemaFeatures
    }

    assert set(_SCENE_FEATURE_COUNTERS) == contract_feature_ids
