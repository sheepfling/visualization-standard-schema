from __future__ import annotations

from typing import Any

from ..models import Orientation, Wgs84Position
from ..util import safe_get, to_float
from .czml_helpers import _extract_czml_packet_position, _packet_style, _packet_timestamp


def _packet_to_scene_axes_member(packet: dict[str, Any], packet_id: str) -> dict[str, Any] | None:
    props = safe_get(packet, "properties")
    if not isinstance(props, dict):
        return None
    object_type = safe_get(props, "objectType")
    if object_type not in {"bodyAxes", "principalAxes"}:
        return None
    axis_role = safe_get(props, "axisRole")
    axis_group_id = safe_get(props, "axisGroupId")
    axis_index = safe_get(props, "axisIndex")
    axis_length = to_float(safe_get(props, "axisLengthMeters"))
    if not isinstance(axis_role, str) or not isinstance(axis_group_id, str) or axis_length is None:
        return None
    polyline = safe_get(packet, "polyline")
    if not isinstance(polyline, dict):
        return None
    positions = safe_get(polyline, "positions")
    if isinstance(positions, dict):
        positions = safe_get(positions, "cartographicDegrees")
    if not isinstance(positions, list) or len(positions) < 6:
        return None
    origin = _extract_czml_packet_position(packet)
    if origin is None:
        return None
    end_lon = to_float(positions[3])
    end_lat = to_float(positions[4])
    end_alt = to_float(positions[5])
    if end_lon is None or end_lat is None or end_alt is None:
        return None
    orientation = safe_get(props, "orientationDegrees")
    orientation_value = None
    if isinstance(orientation, dict):
        heading = to_float(safe_get(orientation, "heading"))
        pitch = to_float(safe_get(orientation, "pitch"))
        roll = to_float(safe_get(orientation, "roll"))
        if heading is not None or pitch is not None or roll is not None:
            orientation_value = Orientation(headingDeg=heading, pitchDeg=pitch, rollDeg=roll)
    return {
        "objectType": object_type,
        "packetId": packet_id,
        "groupId": axis_group_id,
        "axisRole": axis_role,
        "axisIndex": int(axis_index) if axis_index is not None else None,
        "origin": origin,
        "end": Wgs84Position(longitudeDeg=end_lon, latitudeDeg=end_lat, altitudeM=end_alt),
        "axisLengthMeters": axis_length,
        "orientation": orientation_value,
        "style": _packet_style(packet, for_overlay=True),
        "attributes": {k: v for k, v in props.items() if k not in {"objectType", "axisRole", "axisIndex", "axisGroupId", "axisLengthMeters", "orientationDegrees", "source", "timestamp"}},
        "source": safe_get(props, "source"),
        "timestamp": _packet_timestamp(packet),
    }


__all__ = [
    "_packet_to_scene_axes_member",
]
