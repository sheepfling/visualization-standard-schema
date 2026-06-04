from __future__ import annotations

import json
from pathlib import Path

from ..cesium import dump_cesium_scene_json
from ..models import SceneBodyAxes, ScenePrincipalAxes, VssScene, Wgs84Position
from .czml_axes import _packet_to_scene_axes_member
from .czml_custom import _packet_to_scene_custom_object
from .czml_helpers import _extract_czml_packet_position, _packet_to_scene_entity
from .czml_overlays import _packet_to_scene_overlay
from .czml_views import _packet_to_scene_camera_view, _packet_to_scene_rectangular_sensor
from .scene import _build_scene


def parse_czml_to_scene(raw_text: str, *, source: str = "czml") -> VssScene:
    payload = json.loads(raw_text)
    packets = payload if isinstance(payload, list) else payload.get("czml", [])
    if not isinstance(packets, list):
        raise ValueError("CZML payload must be a list")

    objects: list = []
    timestamps: list = []
    axes_groups: dict[str, list[dict]] = {}
    for packet in packets:
        if not isinstance(packet, dict):
            continue
        if packet.get("id") == "document":
            continue
        packet_id = packet.get("id")
        if not isinstance(packet_id, str):
            continue
        custom_object = _packet_to_scene_custom_object(packet, packet_id)
        if custom_object is not None:
            objects.append(custom_object)
            continue
        camera_view = _packet_to_scene_camera_view(packet, packet_id)
        if camera_view is not None:
            objects.append(camera_view)
            continue
        rectangular_sensor = _packet_to_scene_rectangular_sensor(packet, packet_id)
        if rectangular_sensor is not None:
            objects.append(rectangular_sensor)
            continue
        axes_member = _packet_to_scene_axes_member(packet, packet_id)
        if axes_member is not None:
            axes_groups.setdefault(axes_member["groupId"], []).append(axes_member)
            continue
        overlay = _packet_to_scene_overlay(packet, packet_id)
        if overlay is not None:
            objects.append(overlay)
            continue
        position = _extract_czml_packet_position(packet)
        if position is not None:
            entity = _packet_to_scene_entity(packet, packet_id, position)
            objects.append(entity)
            if entity.timestamp is not None:
                timestamps.append(entity.timestamp)

    for group_id, members in axes_groups.items():
        if len(members) < 3:
            continue
        object_type = members[0]["objectType"]
        ordered_members = sorted(members, key=lambda item: item.get("axisIndex", 99))
        axis_lengths = tuple(member["axisLengthMeters"] for member in ordered_members[:3])
        orientation = ordered_members[0]["orientation"]
        style = ordered_members[0]["style"]
        attributes = dict(ordered_members[0]["attributes"])
        object_source = ordered_members[0]["source"]
        timestamp = ordered_members[0]["timestamp"]
        origin_tuple = ordered_members[0]["origin"]
        origin = Wgs84Position(
            longitudeDeg=origin_tuple[0],
            latitudeDeg=origin_tuple[1],
            altitudeM=origin_tuple[2],
        )
        if object_type == "bodyAxes":
            objects.append(
                SceneBodyAxes(
                    objectType="bodyAxes",
                    id=group_id,
                    name=ordered_members[0]["packetId"].removesuffix("-x") if ordered_members[0]["packetId"].endswith("-x") else group_id,
                    originPosition=origin,
                    axisLengthsMeters=axis_lengths,  # type: ignore[arg-type]
                    orientation=orientation,
                    style=style,
                    attributes=attributes,
                    source=object_source,
                    timestamp=timestamp,
                )
            )
        elif object_type == "principalAxes":
            objects.append(
                ScenePrincipalAxes(
                    objectType="principalAxes",
                    id=group_id,
                    name=ordered_members[0]["packetId"].removesuffix("-x") if ordered_members[0]["packetId"].endswith("-x") else group_id,
                    originPosition=origin,
                    axisLengthsMeters=axis_lengths,  # type: ignore[arg-type]
                    orientation=orientation,
                    style=style,
                    attributes=attributes,
                    source=object_source,
                    timestamp=timestamp,
                )
            )

    return _build_scene(source=source, name="CZML Scene", objects=objects, created=max(timestamps) if timestamps else None)


def parse_czml_file_to_scene(path: str | Path, *, source: str | None = None) -> VssScene:
    raw = Path(path).read_text(encoding="utf-8")
    return parse_czml_to_scene(raw, source=source or Path(path).stem)


def emit_czml_from_scene(scene: VssScene) -> str:
    return dump_cesium_scene_json(scene)


__all__ = [
    "emit_czml_from_scene",
    "parse_czml_file_to_scene",
    "parse_czml_to_scene",
]
