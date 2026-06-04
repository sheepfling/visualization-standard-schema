import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vss import load_message_file
from vss.models import EntityUpsertMessage, VssScene


@pytest.fixture
def example_message() -> EntityUpsertMessage:
    return load_message_file(Path("examples/cesium/air-track.json"))


@pytest.fixture
def example_scene(example_message: EntityUpsertMessage) -> VssScene:
    return VssScene.from_messages(
        [example_message],
        scene_id="demo-scene",
        scene_name="Demo Scene",
    )
