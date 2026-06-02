from __future__ import annotations

from datetime import datetime
from typing import Any

from ..models import (
    EntityCategory,
    SceneDocument,
    SceneEntity,
    Style,
    VssScene,
    Wgs84Position,
)
from ..util import safe_get


def _build_scene(*, source: str, name: str, objects: list[Any], created: datetime | None = None) -> VssScene:
    return VssScene(
        schemaVersion="1.0.0-scene",
        document=SceneDocument(
            id=source,
            name=name,
            created=created,
            source=source,
        ),
        objects=objects,
    )


def _scene_float(value: Any, *, default: float = 0.0) -> float:
    from ..util import to_float

    parsed = to_float(value)
    return parsed if parsed is not None else default


def _sensor_state_to_scene_entity(sensor: Any, *, source: str) -> SceneEntity:
    pose = safe_get(sensor, "pose") or {}
    position = safe_get(pose, "position") or {}
    style = safe_get(sensor, "style") or {}
    return SceneEntity(
        objectType="entity",
        id=sensor.id,
        name=sensor.name,
        category=EntityCategory.SENSOR,
        position=Wgs84Position(
            longitudeDeg=_scene_float(safe_get(position, "lon")),
            latitudeDeg=_scene_float(safe_get(position, "lat")),
            altitudeM=_scene_float(safe_get(position, "alt")),
        ),
        orientation=None,
        style=Style(
            label=safe_get(style, "label"),
            colorRgba=_tuple_from_list(safe_get(style, "colorRgba")),
        ),
        attributes=dict(sensor.model_dump(exclude_none=True)),
        source=source,
        timestamp=None,
    )


def _annotation_state_to_scene_entity(annotation: Any, *, source: str) -> SceneEntity:
    position = safe_get(annotation, "position") or {}
    label = safe_get(annotation, "label") or {}
    billboard = safe_get(annotation, "billboard") or {}
    point = safe_get(annotation, "point") or {}
    return SceneEntity(
        objectType="entity",
        id=annotation.id,
        name=annotation.name,
        category=EntityCategory.OTHER,
        position=Wgs84Position(
            longitudeDeg=_scene_float(safe_get(position, "lon")),
            latitudeDeg=_scene_float(safe_get(position, "lat")),
            altitudeM=_scene_float(safe_get(position, "alt")),
        ),
        orientation=None,
        style=Style(
            label=safe_get(label, "text"),
            iconUri=safe_get(billboard, "image"),
            colorRgba=_tuple_from_list(safe_get(point, "color")),
        ),
        attributes=dict(annotation.model_dump(exclude_none=True)),
        source=source,
        timestamp=None,
    )


def _tuple_from_list(value: Any) -> tuple[int, int, int, int] | None:
    if not isinstance(value, list) or len(value) < 3:
        return None
    try:
        components = [int(component) for component in value[:4]]
    except (TypeError, ValueError):
        return None
    if len(components) == 3:
        components.append(255)
    return tuple(components[:4])  # type: ignore[return-value]

