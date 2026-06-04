from __future__ import annotations

import math
from typing import Any

from ..models import (
    Orientation,
    SceneCameraView,
    SceneFrustum,
    SceneOverlay,
    SceneRectangularSensor,
    Wgs84Position,
)
from ..util import safe_get, to_bool, to_float
from .czml_helpers import (
    _extract_czml_packet_position,
    _packet_orientation,
    _packet_style,
    _packet_timestamp,
)


def _packet_to_scene_camera_view(packet: dict[str, Any], packet_id: str) -> SceneCameraView | None:
    props = safe_get(packet, "properties")
    if not isinstance(props, dict) or safe_get(props, "objectType") != "cameraView":
        return None
    position = _extract_czml_packet_position(packet)
    orientation = safe_get(props, "orientationDegrees")
    if isinstance(orientation, dict):
        heading = to_float(safe_get(orientation, "heading"))
        pitch = to_float(safe_get(orientation, "pitch"))
        roll = to_float(safe_get(orientation, "roll"))
        orientation_value = None
        if heading is not None or pitch is not None or roll is not None:
            orientation_value = Orientation(headingDeg=heading, pitchDeg=pitch, rollDeg=roll)
    else:
        orientation_value = None
    view_position = None
    if position is not None:
        view_position = Wgs84Position(longitudeDeg=position[0], latitudeDeg=position[1], altitudeM=position[2])
    return SceneCameraView(
        objectType="cameraView",
        id=packet_id,
        name=safe_get(packet, "name") or packet_id,
        target=safe_get(props, "target"),
        position=view_position,
        orientation=orientation_value,
        rangeMeters=to_float(safe_get(props, "rangeMeters")),
        durationSeconds=to_float(safe_get(props, "durationSeconds")),
        rendererHints=dict(safe_get(props, "rendererHints")) if isinstance(safe_get(props, "rendererHints"), dict) else {},
        timestamp=_packet_timestamp(packet),
        style=None,
        attributes={k: v for k, v in props.items() if k not in {"objectType", "target", "orientationDegrees", "rangeMeters", "durationSeconds", "rendererHints", "source", "timestamp"}},
        source=safe_get(props, "source"),
    )


def _packet_to_scene_rectangular_sensor(packet: dict[str, Any], packet_id: str) -> SceneOverlay | None:
    rectangular_sensor = safe_get(packet, "agi_rectangularSensor") or safe_get(packet, "rectangularSensor")
    if not isinstance(rectangular_sensor, dict):
        return None
    props = safe_get(packet, "properties")
    shape_type = safe_get(props, "shapeType") if isinstance(props, dict) else None
    radius = to_float(safe_get(rectangular_sensor, "radius"))
    x_half_angle = to_float(safe_get(rectangular_sensor, "xHalfAngle"))
    y_half_angle = to_float(safe_get(rectangular_sensor, "yHalfAngle"))
    if radius is None or x_half_angle is None or y_half_angle is None:
        return None
    center = _extract_czml_packet_position(packet)
    if center is None:
        return None
    lon, lat, alt = center
    show_intersection = safe_get(rectangular_sensor, "showIntersection")
    if shape_type == "frustum":
        frustum_data = safe_get(props, "frustum") if isinstance(props, dict) else None
        if isinstance(frustum_data, dict):
            near_meters = to_float(safe_get(frustum_data, "nearMeters"))
            far_meters = to_float(safe_get(frustum_data, "farMeters"))
            horizontal_fov = to_float(safe_get(frustum_data, "horizontalFovDegrees"))
            vertical_fov = to_float(safe_get(frustum_data, "verticalFovDegrees"))
            inner_half_angle = to_float(safe_get(frustum_data, "innerHalfAngleDegrees"))
            outer_half_angle = to_float(safe_get(frustum_data, "outerHalfAngleDegrees"))
            aspect_ratio = to_float(safe_get(frustum_data, "aspectRatio"))
        else:
            near_meters = None
            far_meters = radius
            horizontal_fov = math.degrees(x_half_angle) * 2.0
            vertical_fov = math.degrees(y_half_angle) * 2.0
            inner_half_angle = None
            outer_half_angle = None
            aspect_ratio = None
        if near_meters is None or far_meters is None:
            return None
        return SceneOverlay(
            objectType="overlay",
            id=packet_id,
            name=safe_get(packet, "name") or packet_id,
            position=Wgs84Position(longitudeDeg=lon, latitudeDeg=lat, altitudeM=alt),
            orientation=_packet_orientation(packet),
            geometryType="frustum",
            frustum=SceneFrustum(
                nearMeters=near_meters,
                farMeters=far_meters,
                horizontalFovDegrees=horizontal_fov,
                verticalFovDegrees=vertical_fov,
                innerHalfAngleDegrees=inner_half_angle,
                outerHalfAngleDegrees=outer_half_angle,
                aspectRatio=aspect_ratio,
            ),
            style=_packet_style(packet, for_overlay=True),
            attributes={"source": safe_get(packet, "source") or "czml"},
            source=safe_get(packet, "source"),
            timestamp=None,
        )
    return SceneOverlay(
        objectType="overlay",
        id=packet_id,
        name=safe_get(packet, "name") or packet_id,
        position=Wgs84Position(longitudeDeg=lon, latitudeDeg=lat, altitudeM=alt),
        orientation=_packet_orientation(packet),
        geometryType="rectangularSensor",
        rectangularSensor=SceneRectangularSensor(
            radiusMeters=radius,
            xHalfAngleDegrees=math.degrees(x_half_angle),
            yHalfAngleDegrees=math.degrees(y_half_angle),
            showIntersection=to_bool(show_intersection) if show_intersection is not None else None,
            intersectionWidthPx=to_float(safe_get(rectangular_sensor, "intersectionWidth")),
            showLateralSurfaces=to_bool(safe_get(rectangular_sensor, "showLateralSurfaces")) if safe_get(rectangular_sensor, "showLateralSurfaces") is not None else None,
            showDomeSurfaces=to_bool(safe_get(rectangular_sensor, "showDomeSurfaces")) if safe_get(rectangular_sensor, "showDomeSurfaces") is not None else None,
        ),
        style=_packet_style(packet, for_overlay=True),
        attributes={"source": safe_get(packet, "source") or "czml"},
        source=safe_get(packet, "source"),
        timestamp=None,
    )


__all__ = [
    "_packet_to_scene_camera_view",
    "_packet_to_scene_rectangular_sensor",
]
