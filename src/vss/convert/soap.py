from __future__ import annotations

from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from ..models import EntityUpsertMessage, EntityUpsertPayload, SceneEntity, VssScene, Wgs84Position, scene_entity_from_message
from ..soap import compile_soap_envelope, load_soap_bundle
from ..util import parse_iso_datetime, to_float, utc_now_isoformat
from .categories import _coerce_entity_category
from .scene import _build_scene
from .points import _dict_position_to_lat_lon_alt, _latest_point, _soap_trajectory_point
from .text import _collect_list_values, _coerce_scalar_text, _find_child, _local_name, _text, _value_to_primitive


def _first_entity_message(scene: VssScene) -> EntityUpsertMessage:
    if not scene.entities:
        raise ValueError("scene has no entities to emit")
    return _scene_entity_to_message(scene.entities[0], source_override=scene.document.source or scene.document.id)


def _scene_entity_to_message(entity: SceneEntity, *, source_override: str | None = None) -> EntityUpsertMessage:
    source = source_override or entity.source or "vss"
    payload = EntityUpsertPayload(
        entityId=entity.id,
        name=entity.name,
        category=entity.category,
        position=entity.position,
        orientation=entity.orientation,
        style=entity.style,
        attributes=dict(entity.attributes),
    )
    return EntityUpsertMessage(
        schemaVersion="1.0.0",
        messageType="entity.upsert",
        messageId=f"{source}:{entity.id}",
        timestamp=entity.timestamp or scene_default_timestamp(entity),
        source=source,
        payload=payload,
    )


def scene_default_timestamp(entity: SceneEntity):
    if entity.timestamp is not None:
        return entity.timestamp
    from ..util import utc_now

    return utc_now()


def parse_soap_to_message(raw_text: str | Path) -> EntityUpsertMessage:
    raw = Path(raw_text).read_text(encoding="utf-8") if isinstance(raw_text, Path) else str(raw_text)
    root = ElementTree.fromstring(raw)
    message_node = _find_child(root, "EntityUpsertMessage")
    if message_node is None:
        raise ValueError("SOAP envelope is missing EntityUpsertMessage")
    payload = _find_child(message_node, "payload")
    if payload is None:
        raise ValueError("SOAP envelope is missing payload")
    position = _find_child(payload, "position")
    if position is None:
        raise ValueError("SOAP envelope is missing position")
    orientation_node = _find_child(payload, "orientation")
    style_node = _find_child(payload, "style")
    attributes_node = _find_child(payload, "attributes")

    data: dict[str, Any] = {
        "schemaVersion": _text(message_node, "schemaVersion", default="1.0.0"),
        "messageType": _text(message_node, "messageType", default="entity.upsert"),
        "messageId": _text(message_node, "messageId", default="soap-envelope"),
        "timestamp": _text(message_node, "timestamp", default=utc_now_isoformat()),
        "source": _text(message_node, "source", default="soap-envelope"),
        "payload": {
            "entityId": _text(payload, "entityId"),
            "name": _text(payload, "name"),
            "category": _text(payload, "category"),
            "position": {
                "longitudeDeg": to_float(_text(position, "longitudeDeg")),
                "latitudeDeg": to_float(_text(position, "latitudeDeg")),
                "altitudeM": to_float(_text(position, "altitudeM")),
            },
            "attributes": {},
        },
    }

    if orientation_node is not None:
        orientation = {
            "headingDeg": to_float(_text(orientation_node, "headingDeg")),
            "pitchDeg": to_float(_text(orientation_node, "pitchDeg")),
            "rollDeg": to_float(_text(orientation_node, "rollDeg")),
        }
        data["payload"]["orientation"] = {key: value for key, value in orientation.items() if value is not None}

    if style_node is not None:
        style = {
            "label": _text(style_node, "label"),
            "iconUri": _text(style_node, "iconUri"),
            "modelUri": _text(style_node, "modelUri"),
            "colorRgba": _collect_list_values(_find_child(style_node, "colorRgba")),
        }
        clean_style = {key: value for key, value in style.items() if value is not None}
        if clean_style:
            data["payload"]["style"] = clean_style

    if attributes_node is not None:
        attributes: dict[str, Any] = {}
        for child in attributes_node:
            if _local_name(child.tag) == "attribute":
                key = child.attrib.get("name")
                if key:
                    attributes[key] = _value_to_primitive((child.text or "").strip())
        if attributes:
            data["payload"]["attributes"] = attributes

    return EntityUpsertMessage.model_validate(data)


def parse_soap_bundle_to_scene(path: str | Path, *, source: str | None = None) -> VssScene:
    bundle = load_soap_bundle(path)
    scene_source = source or bundle.source
    entities: list[SceneEntity] = []
    timestamps: list = []

    trajectory_points_by_platform: dict[str, list[tuple]] = {}
    for trajectory in bundle.scenario.trajectories:
        points: list[tuple] = []
        for sample in trajectory.samples:
            point = _soap_trajectory_point(sample)
            if point is not None:
                points.append(point)
        if points:
            trajectory_points_by_platform[trajectory.platformId] = points

    for platform in bundle.scenario.platforms:
        points = list(trajectory_points_by_platform.get(platform.id, []))
        initial = _dict_position_to_lat_lon_alt(getattr(platform, "initialState") or {})
        if initial is not None:
            lon, lat, alt = initial
            points.append((None, lat, lon, alt))
        if not points:
            continue
        lat, lon, alt, stamp = _latest_point(points)
        entities.append(
            SceneEntity(
                objectType="entity",
                id=platform.id,
                name=platform.name,
                category=_coerce_entity_category((platform.properties or {}).get("category") if isinstance(platform.properties, dict) else None),
                position=Wgs84Position(longitudeDeg=lon, latitudeDeg=lat, altitudeM=alt),
                orientation=None,
                style=None,
                attributes=dict(platform.properties) if isinstance(platform.properties, dict) else {},
                source=scene_source,
                timestamp=stamp,
            )
        )
        if stamp is not None:
            timestamps.append(stamp)

    return _build_scene(source=scene_source, name="SOAP Bundle Scene", objects=entities, created=max(timestamps) if timestamps else None)


def parse_soap_to_scene(raw_text_or_path: str | Path, *, source: str | None = None) -> VssScene:
    if isinstance(raw_text_or_path, Path):
        path = raw_text_or_path
        if path.is_dir():
            return parse_soap_bundle_to_scene(path, source=source)
        message = parse_soap_to_message(path)
    elif isinstance(raw_text_or_path, str):
        raw_text = raw_text_or_path
        if "\n" not in raw_text and "<" not in raw_text:
            try:
                path = Path(raw_text)
                if path.exists():
                    if path.is_dir():
                        return parse_soap_bundle_to_scene(path, source=source)
                    message = parse_soap_to_message(path)
                else:
                    message = parse_soap_to_message(raw_text)
            except OSError:
                message = parse_soap_to_message(raw_text)
        else:
            message = parse_soap_to_message(raw_text)
    else:
        message = parse_soap_to_message(str(raw_text_or_path))
    return _build_scene(
        source=source or message.source,
        name="SOAP Message Scene",
        objects=[scene_entity_from_message(message)],
        created=parse_iso_datetime(message.timestamp.isoformat()),
    )


def emit_soap_envelope_from_scene(scene: VssScene) -> str:
    message = _first_entity_message(scene)
    return compile_soap_envelope(message)


__all__ = [
    "emit_soap_envelope_from_scene",
    "parse_soap_bundle_to_scene",
    "parse_soap_to_message",
    "parse_soap_to_scene",
]
