from __future__ import annotations

from typing import Any

from ..models import (
    SceneAccelerationVector,
    SceneLineOfSight,
    SceneOverlay,
    ScenePolyline,
    SceneInterceptLine,
    SceneRelativeLine,
    SceneVector,
    SceneVelocityVector,
    Wgs84Position,
)
from ..util import safe_get, to_float
from .czml_helpers import _packet_style, _packet_timestamp


def _packet_to_scene_polyline_overlay(packet: dict[str, Any], packet_id: str) -> SceneOverlay | None:
    polyline = safe_get(packet, "polyline")
    if not isinstance(polyline, dict):
        return None
    props = safe_get(packet, "properties")
    object_type = safe_get(props, "objectType") if isinstance(props, dict) else None
    polyline_positions = safe_get(polyline, "positions")
    if isinstance(polyline_positions, dict):
        polyline_positions = safe_get(polyline_positions, "cartographicDegrees")
    if not isinstance(polyline_positions, list) or len(polyline_positions) < 6:
        return None

    points: list[Wgs84Position] = []
    for i in range(0, len(polyline_positions) - 2, 3):
        lon = to_float(polyline_positions[i])
        lat = to_float(polyline_positions[i + 1])
        alt = to_float(polyline_positions[i + 2])
        if lon is None or lat is None or alt is None:
            return None
        points.append(Wgs84Position(longitudeDeg=lon, latitudeDeg=lat, altitudeM=alt))
    if not points:
        return None

    if object_type == "vector":
        return SceneVector(
            objectType="vector",
            id=packet_id,
            name=safe_get(packet, "name") or packet_id,
            startPosition=points[0],
            endPosition=points[-1],
            widthPx=to_float(safe_get(polyline, "width")) or 2.0,
            clampToGround=bool(safe_get(polyline, "clampToGround")),
            style=_packet_style(packet, for_overlay=True),
            attributes={"source": safe_get(packet, "source") or "czml"},
            source=safe_get(packet, "source"),
            timestamp=_packet_timestamp(packet),
        )
    if object_type == "velocityVector":
        return SceneVelocityVector(
            objectType="velocityVector",
            id=packet_id,
            name=safe_get(packet, "name") or packet_id,
            startPosition=points[0],
            endPosition=points[-1],
            widthPx=to_float(safe_get(polyline, "width")) or 2.0,
            clampToGround=bool(safe_get(polyline, "clampToGround")),
            style=_packet_style(packet, for_overlay=True),
            attributes={"source": safe_get(packet, "source") or "czml"},
            source=safe_get(packet, "source"),
            timestamp=_packet_timestamp(packet),
        )
    if object_type == "accelerationVector":
        return SceneAccelerationVector(
            objectType="accelerationVector",
            id=packet_id,
            name=safe_get(packet, "name") or packet_id,
            startPosition=points[0],
            endPosition=points[-1],
            widthPx=to_float(safe_get(polyline, "width")) or 2.0,
            clampToGround=bool(safe_get(polyline, "clampToGround")),
            style=_packet_style(packet, for_overlay=True),
            attributes={"source": safe_get(packet, "source") or "czml"},
            source=safe_get(packet, "source"),
            timestamp=_packet_timestamp(packet),
        )
    if object_type == "lineOfSight":
        return SceneLineOfSight(
            objectType="lineOfSight",
            id=packet_id,
            name=safe_get(packet, "name") or packet_id,
            startPosition=points[0],
            endPosition=points[-1],
            widthPx=to_float(safe_get(polyline, "width")) or 2.0,
            clampToGround=bool(safe_get(polyline, "clampToGround")),
            style=_packet_style(packet, for_overlay=True),
            attributes={"source": safe_get(packet, "source") or "czml"},
            source=safe_get(packet, "source"),
            timestamp=_packet_timestamp(packet),
        )
    if object_type == "relativeLine":
        return SceneRelativeLine(
            objectType="relativeLine",
            id=packet_id,
            name=safe_get(packet, "name") or packet_id,
            startPosition=points[0],
            endPosition=points[-1],
            widthPx=to_float(safe_get(polyline, "width")) or 2.0,
            clampToGround=bool(safe_get(polyline, "clampToGround")),
            style=_packet_style(packet, for_overlay=True),
            attributes={"source": safe_get(packet, "source") or "czml"},
            source=safe_get(packet, "source"),
            timestamp=_packet_timestamp(packet),
        )
    if object_type == "interceptLine":
        return SceneInterceptLine(
            objectType="interceptLine",
            id=packet_id,
            name=safe_get(packet, "name") or packet_id,
            startPosition=points[0],
            endPosition=points[-1],
            widthPx=to_float(safe_get(polyline, "width")) or 2.0,
            clampToGround=bool(safe_get(polyline, "clampToGround")),
            style=_packet_style(packet, for_overlay=True),
            attributes={"source": safe_get(packet, "source") or "czml"},
            source=safe_get(packet, "source"),
            timestamp=_packet_timestamp(packet),
        )

    return SceneOverlay(
        objectType="overlay",
        id=packet_id,
        name=safe_get(packet, "name") or packet_id,
        position=points[0],
        polyline=ScenePolyline(
            positions=points,
            widthPx=to_float(safe_get(polyline, "width")) or to_float(safe_get(polyline, "widthPx")) or 2.0,
            clampToGround=bool(safe_get(polyline, "clampToGround")),
        ),
        style=_packet_style(packet, for_overlay=True),
        attributes={"source": safe_get(packet, "source") or "czml"},
        source=safe_get(packet, "source"),
        timestamp=None,
    )


__all__ = [
    "_packet_to_scene_polyline_overlay",
]
