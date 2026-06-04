from __future__ import annotations

from typing import Any

from ..models import (
    SceneClassificationVolume,
    SceneClippingPlane,
    SceneClippingPolygon,
    SceneCustomMesh,
    SceneCustomObject,
    SceneCustomShader,
    ScenePostProcessStage,
    SceneRuntimeObject,
    SceneTerrainSurface,
    Wgs84Position,
)
from ..util import safe_get
from .czml_helpers import _extract_czml_packet_position, _packet_orientation, _packet_timestamp


def _packet_to_scene_custom_object(
    packet: dict[str, Any],
    packet_id: str,
) -> SceneCustomObject | SceneRuntimeObject | SceneTerrainSurface | SceneCustomMesh | SceneClippingPlane | SceneClippingPolygon | SceneClassificationVolume | SceneCustomShader | ScenePostProcessStage | None:
    props = safe_get(packet, "properties")
    if not isinstance(props, dict) or safe_get(props, "objectType") not in {"custom", "runtime", "terrainSurface", "customMesh", "clippingPlane", "clippingPolygon", "classificationVolume", "customShader", "postProcessStage"}:
        return None

    position = _extract_czml_packet_position(packet)
    object_type = safe_get(props, "objectType")
    type_key = "customType" if object_type == "custom" else "runtimeType" if object_type == "runtime" else None
    type_value = safe_get(props, type_key) if type_key else None
    if type_key is not None and (not isinstance(type_value, str) or not type_value):
        return None

    renderer_hints = safe_get(props, "rendererHints")
    payload = safe_get(props, "payload")
    extensions = safe_get(props, "extensions")
    view_position = None
    if position is not None:
        view_position = Wgs84Position(longitudeDeg=position[0], latitudeDeg=position[1], altitudeM=position[2])
    orientation = _packet_orientation(packet)
    common_kwargs = dict(
        id=packet_id,
        name=safe_get(packet, "name") or packet_id,
        payload=dict(payload) if isinstance(payload, dict) else {},
        position=view_position,
        orientation=orientation,
        show=safe_get(props, "show"),
        layer=safe_get(props, "layer"),
        extensions=dict(extensions) if isinstance(extensions, dict) else {},
        rendererHints=dict(renderer_hints) if isinstance(renderer_hints, dict) else {},
        timestamp=_packet_timestamp(packet),
        attributes={
            k: v
            for k, v in props.items()
            if k not in {"objectType", "customType", "runtimeType", "payload", "rendererHints", "extensions", "show", "layer", "source", "timestamp", "orientationDegrees"}
        },
        source=safe_get(props, "source"),
    )
    if object_type == "custom":
        return SceneCustomObject(
            objectType="custom",
            customType=type_value,
            **common_kwargs,
        )
    if object_type == "runtime":
        return SceneRuntimeObject(
            objectType="runtime",
            runtimeType=type_value,
            **common_kwargs,
        )
    if object_type == "terrainSurface":
        return SceneTerrainSurface(
            objectType="terrainSurface",
            **common_kwargs,
        )
    if object_type == "clippingPlane":
        return SceneClippingPlane(
            objectType="clippingPlane",
            clippingPlane=dict(safe_get(props, "clippingPlane")) if isinstance(safe_get(props, "clippingPlane"), dict) else {},
            **common_kwargs,
        )
    if object_type == "clippingPolygon":
        return SceneClippingPolygon(
            objectType="clippingPolygon",
            clippingPolygon=dict(safe_get(props, "clippingPolygon")) if isinstance(safe_get(props, "clippingPolygon"), dict) else {},
            **common_kwargs,
        )
    if object_type == "classificationVolume":
        return SceneClassificationVolume(
            objectType="classificationVolume",
            classificationVolume=dict(safe_get(props, "classificationVolume")) if isinstance(safe_get(props, "classificationVolume"), dict) else {},
            **common_kwargs,
        )
    if object_type == "customShader":
        return SceneCustomShader(
            objectType="customShader",
            customShader=dict(safe_get(props, "customShader")) if isinstance(safe_get(props, "customShader"), dict) else {},
            **common_kwargs,
        )
    if object_type == "postProcessStage":
        return ScenePostProcessStage(
            objectType="postProcessStage",
            postProcessStage=dict(safe_get(props, "postProcessStage")) if isinstance(safe_get(props, "postProcessStage"), dict) else {},
            **common_kwargs,
        )
    return SceneCustomMesh(
        objectType="customMesh",
        **common_kwargs,
    )


__all__ = ["_packet_to_scene_custom_object"]
