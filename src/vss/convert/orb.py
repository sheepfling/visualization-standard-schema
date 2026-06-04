from __future__ import annotations

from pathlib import Path

from ..models import SceneEntity, VssScene, Wgs84Position
from ..orb.schema import parse_orb_scenario_file, parse_orb_scenario_text
from ..orb.typed import OrbScenario
from .categories import _coerce_entity_category
from .orb_helpers import _is_probable_raw_orb_text, _select_orb_position
from .scene import _build_scene
from .text import _coerce_scalar_text


def parse_orb_to_scene(path_or_text: str | Path) -> VssScene:
    if _is_probable_raw_orb_text(path_or_text):
        scenario = parse_orb_scenario_text(str(path_or_text))
        scene_source = "orb-scenario"
    else:
        path = Path(path_or_text)
        scenario = parse_orb_scenario_file(path)
        scene_source = path.stem or "orb-scenario"

    return _scene_from_orb_scenario(scenario, scene_source=scene_source)


def _scene_from_orb_scenario(scenario: OrbScenario, *, scene_source: str) -> VssScene:
    entities: list[SceneEntity] = []
    for platform in scenario.platforms:
        position = _select_orb_position(platform)
        if position is None:
            continue
        lat, lon, alt = position
        platform_name = _coerce_scalar_text(platform.name) or _coerce_scalar_text(platform.platform_type) or "platform"
        platform_id = _coerce_scalar_text(platform_name)
        entities.append(
            SceneEntity(
                objectType="entity",
                id=str(platform_id),
                name=str(platform_name),
                category=_coerce_entity_category(_coerce_scalar_text(platform.platform_type)),
                position=Wgs84Position(longitudeDeg=lon, latitudeDeg=lat, altitudeM=alt),
                orientation=None,
                style=None,
                attributes={"platform_type": platform.platform_type},
                source=scene_source,
                timestamp=None,
            )
        )

    return _build_scene(
        source=scene_source if scenario.file_type is None else str(scenario.file_type),
        name=scenario.file_type or "ORB Scenario",
        objects=entities,
        created=None,
    )


def emit_orb_from_scene(scene: VssScene) -> str:
    from .orb_helpers import _build_orb_from_entities

    if not scene.entities:
        raise ValueError("scene has no entities to emit")
    return _build_orb_from_entities(scene.entities)


__all__ = [
    "_scene_from_orb_scenario",
    "emit_orb_from_scene",
    "parse_orb_to_scene",
]
