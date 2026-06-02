from __future__ import annotations

from datetime import datetime
from typing import Any

from ..models import (
    Orientation,
    SceneEntity,
    Style,
    Wgs84Position,
)
from ..util import safe_get, to_float
from .categories import _coerce_entity_category


def _extract_czml_packet_position(packet: dict[str, Any]) -> tuple[float, float, float] | None:
    position = safe_get(packet, "position")
    if not isinstance(position, dict):
        return None
    values = safe_get(position, "cartographicDegrees")
    if not isinstance(values, list) or len(values) < 3:
        return None
    lon = to_float(values[0])
    lat = to_float(values[1])
    alt = to_float(values[2])
    if lon is None or lat is None or alt is None:
        return None
    return lon, lat, alt


def _packet_timestamp(packet: dict[str, Any]) -> datetime | None:
    props = safe_get(packet, "properties")
    if not isinstance(props, dict):
        return None
    value = safe_get(props, "timestamp")
    if not isinstance(value, str):
        return None
    from ..util import parse_iso_datetime

    return parse_iso_datetime(value)


def _packet_to_scene_entity(packet: dict[str, Any], packet_id: str, position: tuple[float, float, float]) -> SceneEntity:
    lon, lat, alt = position
    props = safe_get(packet, "properties")
    properties: dict[str, Any] = dict(props) if isinstance(props, dict) else {}
    return SceneEntity(
        objectType="entity",
        id=packet_id,
        name=safe_get(packet, "name") or packet_id,
        category=_coerce_entity_category(safe_get(properties, "category")),
        position=Wgs84Position(longitudeDeg=lon, latitudeDeg=lat, altitudeM=alt),
        orientation=_packet_orientation(packet),
        style=_packet_style(packet, for_overlay=False),
        attributes=properties,
        source=safe_get(properties, "source"),
        timestamp=_packet_timestamp(packet),
    )


def _packet_orientation(packet: dict[str, Any]) -> Orientation | None:
    props = safe_get(packet, "properties")
    if not isinstance(props, dict):
        return None
    orientation = safe_get(props, "orientationDegrees")
    if not isinstance(orientation, dict):
        return None
    heading = to_float(safe_get(orientation, "heading"))
    pitch = to_float(safe_get(orientation, "pitch"))
    roll = to_float(safe_get(orientation, "roll"))
    if heading is None and pitch is None and roll is None:
        return None
    return Orientation(headingDeg=heading, pitchDeg=pitch, rollDeg=roll)


def _packet_style(packet: dict[str, Any], *, for_overlay: bool) -> Style | None:
    if for_overlay:
        for geometry_key in ("polyline", "polygon", "rectangle", "corridor", "ellipse", "wall", "box", "cylinder", "cone", "agi_conicSensor", "rectangularSensor", "agi_rectangularSensor", "polylineVolume", "plane", "tileset", "ellipsoid"):
            geometry = safe_get(packet, geometry_key)
            if isinstance(geometry, dict):
                for material_key in ("material", "capMaterial", "outerMaterial", "innerMaterial"):
                    material = safe_get(geometry, material_key)
                    if isinstance(material, dict):
                        solid = safe_get(material, "solidColor")
                        if isinstance(solid, dict):
                            color_payload = safe_get(solid, "color")
                            if isinstance(color_payload, dict):
                                return Style(colorRgba=_rgba_style(safe_get(color_payload, "rgba")))
        return None

    point = safe_get(packet, "point")
    billboard = safe_get(packet, "billboard")
    label = safe_get(packet, "label")
    model = safe_get(packet, "model")
    color = None
    if isinstance(point, dict):
        point_color = safe_get(point, "color")
        if isinstance(point_color, dict):
            color = _rgba_style(safe_get(point_color, "rgba"))
    if color is None:
        color_payload = safe_get(safe_get(packet, "properties") or {}, "colorRgba")
        if isinstance(color_payload, list):
            color = _rgba_style(color_payload)
    return Style(
        label=safe_get(label, "text"),
        iconUri=safe_get(billboard, "image"),
        modelUri=safe_get(model, "uri"),
        colorRgba=color,
    )


def _rgba_style(value: Any) -> tuple[int, int, int, int] | None:
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        return None
    try:
        return (int(value[0]), int(value[1]), int(value[2]), int(value[3]))
    except (TypeError, ValueError):
        return None
