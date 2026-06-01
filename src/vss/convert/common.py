from __future__ import annotations

import json
import shlex
from datetime import datetime, timedelta, timezone
from os import PathLike
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from ..cesium import dump_cesium_scene_json
from ..models import (
    EntityCategory,
    EntityUpsertMessage,
    EntityUpsertPayload,
    Orientation,
    SceneCircle,
    SceneCorridor,
    SceneDocument,
    SceneEllipse,
    SceneEntity,
    SceneOverlay,
    ScenePolyline,
    SceneRectangle,
    SceneBox,
    SceneWall,
    Style,
    VssScene,
    Wgs84Position,
    scene_entity_from_message,
)
from ..orb.schema import parse_orb_scenario_file, parse_orb_scenario_text
from ..orb.typed import OrbPlatform, OrbScenario
from ..simdis import compile_simdis_asi, load_simdis_bundle
from ..simdis.gog import parse_simdis_gog_to_scene
from ..soap import compile_soap_envelope, load_soap_bundle
from ..util import (
    float_or_default,
    parse_iso_datetime,
    safe_get,
    to_float,
    to_int,
    utc_now,
    utc_now_isoformat,
)


def parse_simdis_asi_to_scene(raw_text: str, *, source: str = "simdis-asi") -> VssScene:
    reference_year = 1970
    platform_meta: dict[str, dict[str, Any]] = {}
    platform_samples: dict[str, list[dict[str, Any]]] = {}
    beam_states: dict[str, dict[str, Any]] = {}
    gate_states: dict[str, dict[str, Any]] = {}
    projector_states: dict[str, dict[str, Any]] = {}

    for raw_line in raw_text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        tokens = _tokenize(raw_line)
        if not tokens:
            continue
        command = tokens[0]

        if command == "ReferenceYear" and len(tokens) >= 2:
            parsed = _safe_int(tokens[1])
            if parsed is not None:
                reference_year = parsed
            continue
        if command == "DegreeAngles":
            continue
        if command in {"PlatformID", "PLATFORM"} and len(tokens) >= 2:
            platform_id = tokens[1]
            meta = platform_meta.setdefault(platform_id, {"platformId": platform_id})
            if command == "PLATFORM":
                meta["platformName"] = _after(tokens, "NAME", default=platform_id)
                meta["category"] = _coerce_entity_category(_after(tokens, "CATEGORY"))
            continue
        if command == "PlatformName" and len(tokens) >= 3:
            platform_meta.setdefault(tokens[1], {"platformId": tokens[1]})["platformName"] = tokens[2]
            continue
        if command == "PLATFORM_LABEL" and len(tokens) >= 3:
            platform_meta.setdefault(tokens[1], {"platformId": tokens[1]})["platformLabel"] = tokens[2]
            continue
        if command == "PlatformIcon" and len(tokens) >= 3:
            meta = platform_meta.setdefault(tokens[1], {"platformId": tokens[1]})
            meta["platformIcon"] = tokens[2]
            if meta.get("category") is None:
                guessed_category = _category_from_platform_icon(tokens[2])
                if guessed_category is not None:
                    meta["category"] = guessed_category
            continue
        if command == "PlatformData" and len(tokens) >= 12:
            platform_id = tokens[1]
            sample = _parse_platform_data(tokens[2:], reference_year=reference_year)
            if sample is not None:
                platform_samples.setdefault(platform_id, []).append(sample)
            continue
        if command == "PLATFORM_UPDATE" and len(tokens) >= 9:
            platform_id = tokens[1]
            sample = _parse_platform_update(tokens[2:], reference_year=reference_year)
            if sample is not None:
                platform_samples.setdefault(platform_id, []).append(sample)
            continue
        if command == "BeamID" and len(tokens) >= 3:
            host_platform_id, beam_id = tokens[1], tokens[2]
            beam_states[beam_id] = {
                "beamId": beam_id,
                "hostPlatformId": host_platform_id,
                "type": "BODY",
                "samples": [],
            }
            continue
        if command == "BeamType" and len(tokens) >= 3:
            beam_states.setdefault(tokens[1], {"beamId": tokens[1], "samples": []})["type"] = tokens[2].strip('"')
            continue
        if command == "HorzBW" and len(tokens) >= 3:
            beam_states.setdefault(tokens[1], {"beamId": tokens[1], "samples": []})["horzBwDeg"] = _safe_float(tokens[2])
            continue
        if command == "VertBW" and len(tokens) >= 3:
            beam_states.setdefault(tokens[1], {"beamId": tokens[1], "samples": []})["vertBwDeg"] = _safe_float(tokens[2])
            continue
        if command in {"BeamOnOffCmd", "BeamColorCmd", "BeamDataRAE", "BeamTargetIDCmd"} and len(tokens) >= 3:
            beam_id = tokens[1]
            beam = beam_states.setdefault(beam_id, {"beamId": beam_id, "samples": []})
            _append_beam_sample(beam, tokens, command, reference_year)
            continue
        if command == "GateID" and len(tokens) >= 3:
            host_beam_id, gate_id = tokens[1], tokens[2]
            gate_states[gate_id] = {
                "gateId": gate_id,
                "hostBeamId": host_beam_id,
                "type": "BODY",
                "samples": [],
            }
            continue
        if command == "GateType" and len(tokens) >= 3:
            gate_states.setdefault(tokens[1], {"gateId": tokens[1], "samples": []})["type"] = tokens[2].strip('"')
            continue
        if command in {"GateOnOffCmd", "GateColorCmd", "GateDataRAE"} and len(tokens) >= 3:
            gate_id = tokens[1]
            gate = gate_states.setdefault(gate_id, {"gateId": gate_id, "samples": []})
            _append_gate_sample(gate, tokens, command, reference_year)
            continue
        if command == "Projector" and len(tokens) >= 3:
            host_platform_id, projector_id = tokens[1], tokens[2]
            projector_states[projector_id] = {
                "projectorId": projector_id,
                "hostPlatformId": host_platform_id,
                "samples": [],
            }
            continue
        if command == "ProjectorRasterFile" and len(tokens) >= 3:
            projector_states.setdefault(tokens[1], {"projectorId": tokens[1], "samples": []})["rasterFile"] = tokens[2]
            continue
        if command == "ProjectorInterpolateFOV" and len(tokens) >= 3:
            projector_states.setdefault(tokens[1], {"projectorId": tokens[1], "samples": []})["interpolateFov"] = _safe_int(tokens[2]) == 1
            continue
        if command in {"ProjectorOn", "ProjectorFOV"} and len(tokens) >= 3:
            projector_id = tokens[1]
            projector = projector_states.setdefault(projector_id, {"projectorId": projector_id, "samples": []})
            _append_projector_sample(projector, tokens, command, reference_year)
            continue

    entities: list[SceneEntity] = []
    timestamps: list[datetime] = []
    platform_ids = sorted(
        set(platform_meta)
        | set(platform_samples)
        | {state.get("hostPlatformId") for state in beam_states.values() if isinstance(state.get("hostPlatformId"), str)}
        | {state.get("hostPlatformId") for state in projector_states.values() if isinstance(state.get("hostPlatformId"), str)}
    )
    for platform_id in platform_ids:
        meta = platform_meta.get(platform_id, {"platformId": platform_id})
        samples = platform_samples.get(platform_id, [])
        latest = _latest_asi_sample(samples)
        if latest is None:
            continue
        position = latest["position"]
        simdis_payload: dict[str, Any] = {
            "platformId": platform_id,
            "platformName": meta.get("platformName", platform_id),
            "platformIcon": meta.get("platformIcon"),
            "platformSamples": [_scene_platform_sample(sample) for sample in samples],
        }
        beams = [state for state in beam_states.values() if state.get("hostPlatformId") == platform_id]
        if beams:
            simdis_payload["beams"] = [dict(state) for state in beams]
        projectors = [state for state in projector_states.values() if state.get("hostPlatformId") == platform_id]
        if projectors:
            simdis_payload["projectors"] = [dict(state) for state in projectors]
        gates = [
            state
            for state in gate_states.values()
            if beam_states.get(state.get("hostBeamId"), {}).get("hostPlatformId") == platform_id
        ]
        if gates:
            simdis_payload["gates"] = [dict(state) for state in gates]

        entity = SceneEntity(
            objectType="entity",
            id=platform_id,
            name=str(meta.get("platformName", platform_id)),
            category=meta.get("category"),
            position=Wgs84Position(longitudeDeg=position["lon"], latitudeDeg=position["lat"], altitudeM=position["alt"]),
            orientation=Orientation(
                headingDeg=latest.get("heading"),
                pitchDeg=latest.get("pitch"),
                rollDeg=latest.get("roll"),
            ),
            style=Style(label=meta.get("platformLabel")),
            attributes={"simdis": simdis_payload},
            source=source,
            timestamp=latest.get("time"),
        )
        entities.append(entity)
        if entity.timestamp is not None:
            timestamps.append(entity.timestamp)

    return _build_scene(
        source=source,
        name="SIMDIS ASI Scene",
        objects=entities,
        created=max(timestamps) if timestamps else None,
    )


def parse_simdis_bundle_to_scene(path_or_bundle: str | Path, *, source: str | None = None) -> VssScene:
    bundle = load_simdis_bundle(path_or_bundle)
    scene_source = source or bundle.source
    objects: list[SceneEntity | SceneOverlay] = []
    timestamps: list[datetime] = []

    for platform in bundle.entities.platforms:
        points = []
        for sample in getattr(platform, "trajectory", []):
            point = _simdis_trajectory_point(sample)
            if point is not None:
                points.append(point)
        initial_position = _dict_position_to_lat_lon_alt(getattr(platform, "initialPosition"))
        if initial_position is not None:
            lon, lat, alt = initial_position
            points.append((None, lat, lon, alt))
        if not points:
            continue
        lat, lon, alt, stamp = _latest_point(points)
        platform_properties = safe_get(platform, "properties")
        if not isinstance(platform_properties, dict):
            platform_properties = {}
        entity = SceneEntity(
            objectType="entity",
            id=platform.id,
            name=platform.name,
            category=_coerce_entity_category(safe_get(platform.properties, "category")),
            position=Wgs84Position(longitudeDeg=lon, latitudeDeg=lat, altitudeM=alt),
            orientation=None,
            style=None,
            attributes=platform_properties,
            source=scene_source,
            timestamp=stamp,
        )
        objects.append(entity)
        if stamp is not None:
            timestamps.append(stamp)

    objects.extend(
        _sensor_state_to_scene_entity(sensor, source=scene_source) for sensor in getattr(bundle.entities, "sensors", [])
    )
    objects.extend(
        _annotation_state_to_scene_entity(annotation, source=scene_source)
        for annotation in getattr(bundle.entities, "annotations", [])
    )

    gog_scene = parse_simdis_gog_to_scene(bundle.overlaysGog, source=scene_source, include_annotations=False)
    objects.extend(gog_scene.objects)

    return _build_scene(
        source=scene_source,
        name="SIMDIS Bundle Scene",
        objects=objects,
        created=max(timestamps) if timestamps else None,
    )


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
    timestamps: list[datetime] = []

    trajectory_points_by_platform: dict[str, list[tuple[datetime | None, float, float, float]]] = {}
    for trajectory in bundle.scenario.trajectories:
        points: list[tuple[datetime | None, float, float, float]] = []
        for sample in trajectory.samples:
            point = _soap_trajectory_point(sample)
            if point is not None:
                points.append(point)
        if points:
            trajectory_points_by_platform[trajectory.platformId] = points

    for platform in bundle.scenario.platforms:
        points = list(trajectory_points_by_platform.get(platform.id, []))
        initial = _dict_position_to_lat_lon_alt(safe_get(platform, "initialState") or {})
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
                category=_coerce_entity_category(safe_get(platform.properties, "category")),
                position=Wgs84Position(longitudeDeg=lon, latitudeDeg=lat, altitudeM=alt),
                orientation=None,
                style=None,
                attributes=dict(platform.properties),
                source=scene_source,
                timestamp=stamp,
            )
        )
        if stamp is not None:
            timestamps.append(stamp)

    return _build_scene(
        source=scene_source,
        name="SOAP Bundle Scene",
        objects=entities,
        created=max(timestamps) if timestamps else None,
    )


def parse_soap_to_scene(raw_text_or_path: str | Path, *, source: str | None = None) -> VssScene:
    if isinstance(raw_text_or_path, Path) or Path(raw_text_or_path).exists():
        path = Path(raw_text_or_path)
        if path.is_dir():
            return parse_soap_bundle_to_scene(path, source=source)
        message = parse_soap_to_message(path)
    else:
        message = parse_soap_to_message(raw_text_or_path)
    return _build_scene(
        source=source or message.source,
        name="SOAP Message Scene",
        objects=[scene_entity_from_message(message)],
        created=parse_iso_datetime(message.timestamp.isoformat()),
    )


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


def parse_czml_to_scene(raw_text: str, *, source: str = "czml") -> VssScene:
    payload = json.loads(raw_text)
    packets = payload if isinstance(payload, list) else payload.get("czml", [])
    if not isinstance(packets, list):
        raise ValueError("CZML payload must be a list")

    objects: list[SceneEntity | SceneOverlay] = []
    timestamps: list[datetime] = []
    for packet in packets:
        if not isinstance(packet, dict):
            continue
        if packet.get("id") == "document":
            continue
        packet_id = packet.get("id")
        if not isinstance(packet_id, str):
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

    return _build_scene(source=source, name="CZML Scene", objects=objects, created=max(timestamps) if timestamps else None)


def parse_czml_file_to_scene(path: str | Path, *, source: str | None = None) -> VssScene:
    raw = Path(path).read_text(encoding="utf-8")
    return parse_czml_to_scene(raw, source=source or Path(path).stem)


def emit_simdis_asi_from_scene(scene: VssScene) -> str:
    if not scene.entities:
        raise ValueError("scene has no entities to emit")
    return compile_simdis_asi(scene)


def emit_soap_envelope_from_scene(scene: VssScene) -> str:
    message = _first_entity_message(scene)
    return compile_soap_envelope(message)


def emit_czml_from_scene(scene: VssScene) -> str:
    return dump_cesium_scene_json(scene)


def emit_orb_from_scene(scene: VssScene) -> str:
    if not scene.entities:
        raise ValueError("scene has no entities to emit")
    return _build_orb_from_entities(scene.entities)


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


def _parse_asi_time(raw: Any, *, reference_year: int) -> datetime | None:
    parsed = parse_iso_datetime(raw)
    if parsed is not None:
        return parsed
    if not isinstance(raw, str):
        return None
    cleaned = raw.strip().strip('"')
    parts = cleaned.split(":")
    if len(parts) != 4:
        return None
    day_of_year = _safe_int(parts[0])
    hour = _safe_int(parts[1])
    minute = _safe_int(parts[2])
    second_part = _safe_float(parts[3])
    if day_of_year is None or hour is None or minute is None or second_part is None:
        return None
    base = datetime(reference_year, 1, 1, tzinfo=timezone.utc) + timedelta(days=max(day_of_year - 1, 0))
    seconds = int(second_part)
    microseconds = int(round((second_part - seconds) * 1_000_000))
    return base.replace(hour=hour, minute=minute, second=seconds, microsecond=microseconds)


def _parse_platform_data(tokens: tuple[str, ...], *, reference_year: int) -> dict[str, Any] | None:
    if len(tokens) < 10:
        return None
    stamp = _parse_asi_time(tokens[0], reference_year=reference_year)
    lat = _safe_float(tokens[1])
    lon = _safe_float(tokens[2])
    alt = _safe_float(tokens[3])
    heading = _safe_float(tokens[4])
    pitch = _safe_float(tokens[5])
    roll = _safe_float(tokens[6])
    vx = _safe_float(tokens[7])
    vy = _safe_float(tokens[8])
    vz = _safe_float(tokens[9])
    if stamp is None or lat is None or lon is None or alt is None:
        return None
    return {
        "time": stamp,
        "position": {"lat": lat, "lon": lon, "alt": alt},
        "heading": heading,
        "pitch": pitch,
        "roll": roll,
        "vx": vx if vx is not None else 0.0,
        "vy": vy if vy is not None else 0.0,
        "vz": vz if vz is not None else 0.0,
    }


def _parse_platform_update(tokens: tuple[str, ...], *, reference_year: int) -> dict[str, Any] | None:
    if len(tokens) < 7:
        return None
    stamp = _parse_asi_time(tokens[0], reference_year=reference_year)
    lat = _safe_float(tokens[1])
    lon = _safe_float(tokens[2])
    alt = _safe_float(tokens[3])
    heading = _safe_float(tokens[4])
    pitch = _safe_float(tokens[5])
    roll = _safe_float(tokens[6])
    if stamp is None or lat is None or lon is None or alt is None:
        return None
    return {
        "time": stamp,
        "position": {"lat": lat, "lon": lon, "alt": alt},
        "heading": heading,
        "pitch": pitch,
        "roll": roll,
        "vx": 0.0,
        "vy": 0.0,
        "vz": 0.0,
    }


def _append_beam_sample(beam: dict[str, Any], tokens: tuple[str, ...], command: str, reference_year: int) -> None:
    samples: list[dict[str, Any]] = beam.setdefault("samples", [])
    timestamp = _parse_asi_time(tokens[2], reference_year=reference_year)
    if timestamp is None:
        return
    sample = _sample_for_timestamp(samples, timestamp)
    sample["time"] = timestamp
    if command == "BeamOnOffCmd" and len(tokens) >= 4:
        sample["on"] = _safe_int(tokens[3]) == 1
    elif command == "BeamColorCmd" and len(tokens) >= 4:
        sample["color"] = tokens[3].strip('"')
    elif command == "BeamDataRAE" and len(tokens) >= 6:
        sample["az"] = _safe_float(tokens[3])
        sample["el"] = _safe_float(tokens[4])
        sample["rangeMeters"] = _safe_float(tokens[5])
    elif command == "BeamTargetIDCmd" and len(tokens) >= 4:
        sample["targetPlatformId"] = tokens[3].strip('"')


def _append_gate_sample(gate: dict[str, Any], tokens: tuple[str, ...], command: str, reference_year: int) -> None:
    samples: list[dict[str, Any]] = gate.setdefault("samples", [])
    timestamp = _parse_asi_time(tokens[2], reference_year=reference_year)
    if timestamp is None:
        return
    sample = _sample_for_timestamp(samples, timestamp)
    sample["time"] = timestamp
    if command == "GateOnOffCmd" and len(tokens) >= 4:
        sample["on"] = _safe_int(tokens[3]) == 1
    elif command == "GateColorCmd" and len(tokens) >= 4:
        sample["color"] = tokens[3].strip('"')
    elif command == "GateDataRAE" and len(tokens) >= 10:
        sample["az"] = _safe_float(tokens[3])
        sample["el"] = _safe_float(tokens[4])
        sample["width"] = _safe_float(tokens[5])
        sample["height"] = _safe_float(tokens[6])
        sample["minRangeMeters"] = _safe_float(tokens[7])
        sample["maxRangeMeters"] = _safe_float(tokens[8])
        sample["centroidMeters"] = _safe_float(tokens[9])


def _append_projector_sample(projector: dict[str, Any], tokens: tuple[str, ...], command: str, reference_year: int) -> None:
    samples: list[dict[str, Any]] = projector.setdefault("samples", [])
    timestamp = _parse_asi_time(tokens[2], reference_year=reference_year)
    if timestamp is None:
        return
    sample = _sample_for_timestamp(samples, timestamp)
    sample["time"] = timestamp
    if command == "ProjectorOn" and len(tokens) >= 4:
        sample["on"] = _safe_int(tokens[3]) == 1
    elif command == "ProjectorFOV" and len(tokens) >= 4:
        sample["fovDegrees"] = _safe_float(tokens[3])


def _sample_for_timestamp(samples: list[dict[str, Any]], timestamp: datetime) -> dict[str, Any]:
    if samples and samples[-1].get("time") == timestamp:
        return samples[-1]
    sample: dict[str, Any] = {}
    samples.append(sample)
    return sample


def _latest_asi_sample(samples: list[dict[str, Any]]) -> dict[str, Any] | None:
    latest: dict[str, Any] | None = None
    latest_stamp: datetime | None = None
    for sample in samples:
        stamp = sample.get("time")
        if not isinstance(stamp, datetime):
            continue
        if latest_stamp is None or stamp >= latest_stamp:
            latest = sample
            latest_stamp = stamp
    return latest


def _scene_platform_sample(sample: dict[str, Any]) -> dict[str, Any]:
    stamp = sample.get("time")
    position = sample.get("position") or {}
    heading = sample.get("heading")
    pitch = sample.get("pitch")
    roll = sample.get("roll")
    result: dict[str, Any] = {
        "time": stamp.isoformat() if isinstance(stamp, datetime) else stamp,
        "position": {
            "lat": _safe_float(safe_get(position, "lat")),
            "lon": _safe_float(safe_get(position, "lon")),
            "alt": _safe_float(safe_get(position, "alt")),
        },
        "yawDeg": heading,
        "pitchDeg": pitch,
        "rollDeg": roll,
        "vx": sample.get("vx", 0.0),
        "vy": sample.get("vy", 0.0),
        "vz": sample.get("vz", 0.0),
    }
    return result


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


def _latest_point(points: list[tuple[datetime | None, float, float, float]]) -> tuple[float, float, float, datetime | None]:
    for stamp, lat, lon, alt in sorted(points, key=lambda item: item[0] or datetime.min.replace(tzinfo=timezone.utc), reverse=True):
        return lat, lon, alt, stamp
    raise ValueError("No points")


def _latest_asi_sample(samples: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not samples:
        return None
    return max(samples, key=lambda sample: sample.get("time") or datetime.min.replace(tzinfo=timezone.utc))


def _scene_platform_sample(sample: dict[str, Any]) -> dict[str, Any]:
    position = sample.get("position")
    if isinstance(position, tuple) and len(position) >= 3:
        lat, lon, alt = position[:3]
    elif isinstance(position, dict):
        lat = _scene_float(position.get("lat"))
        lon = _scene_float(position.get("lon"))
        alt = _scene_float(position.get("alt"))
    else:
        lat = _scene_float(sample.get("lat"))
        lon = _scene_float(sample.get("lon"))
        alt = _scene_float(sample.get("alt"))
    return {
        "time": _iso_datetime(sample.get("time")),
        "position": {"lat": lat, "lon": lon, "alt": alt},
        "orientation": {
            "headingDeg": _scene_float(sample.get("yaw")),
            "pitchDeg": _scene_float(sample.get("pitch")),
            "rollDeg": _scene_float(sample.get("roll")),
        },
    }


def _parse_platform_data(tokens: tuple[str, ...], *, reference_year: int) -> dict[str, Any] | None:
    return _parse_platform_update(tokens, reference_year=reference_year)


def _parse_platform_update(tokens: tuple[str, ...], *, reference_year: int) -> dict[str, Any] | None:
    if len(tokens) < 7:
        return None

    timestamp = _parse_simdis_timestamp(tokens[0], reference_year=reference_year)
    lat = to_float(tokens[1])
    lon = to_float(tokens[2])
    alt = to_float(tokens[3])
    if timestamp is None or lat is None or lon is None or alt is None:
        return None

    return {
        "time": timestamp,
        "position": {"lat": lat, "lon": lon, "alt": alt},
        "yaw": _safe_float(tokens[4]),
        "pitch": _safe_float(tokens[5]),
        "roll": _safe_float(tokens[6]),
    }


def _append_beam_sample(beam: dict[str, Any], tokens: tuple[str, ...], command: str, reference_year: int) -> None:
    samples = beam.setdefault("samples", [])
    timestamp = _parse_simdis_timestamp(tokens[2], reference_year=reference_year)
    sample: dict[str, Any] = {"time": timestamp}
    if command == "BeamOnOffCmd" and len(tokens) >= 4:
        sample["on"] = _safe_int(tokens[3]) == 1
    elif command == "BeamColorCmd" and len(tokens) >= 4:
        sample["color"] = tokens[3]
    elif command == "BeamDataRAE" and len(tokens) >= 6:
        sample["az"] = _safe_float(tokens[3])
        sample["el"] = _safe_float(tokens[4])
        sample["rangeMeters"] = _safe_float(tokens[5])
    elif command == "BeamTargetIDCmd" and len(tokens) >= 4:
        sample["targetPlatformId"] = tokens[3]
    samples.append(sample)


def _append_gate_sample(gate: dict[str, Any], tokens: tuple[str, ...], command: str, reference_year: int) -> None:
    samples = gate.setdefault("samples", [])
    timestamp = _parse_simdis_timestamp(tokens[2], reference_year=reference_year)
    sample: dict[str, Any] = {"time": timestamp}
    if command == "GateOnOffCmd" and len(tokens) >= 4:
        sample["on"] = _safe_int(tokens[3]) == 1
    elif command == "GateColorCmd" and len(tokens) >= 4:
        sample["color"] = tokens[3]
    elif command == "GateDataRAE" and len(tokens) >= 10:
        sample["az"] = _safe_float(tokens[3])
        sample["el"] = _safe_float(tokens[4])
        sample["width"] = _safe_float(tokens[5])
        sample["height"] = _safe_float(tokens[6])
        sample["minRangeMeters"] = _safe_float(tokens[7])
        sample["maxRangeMeters"] = _safe_float(tokens[8])
        sample["centroidMeters"] = _safe_float(tokens[9])
    samples.append(sample)


def _append_projector_sample(projector: dict[str, Any], tokens: tuple[str, ...], command: str, reference_year: int) -> None:
    samples = projector.setdefault("samples", [])
    timestamp = _parse_simdis_timestamp(tokens[2], reference_year=reference_year)
    sample: dict[str, Any] = {"time": timestamp}
    if command == "ProjectorOn" and len(tokens) >= 4:
        sample["on"] = _safe_int(tokens[3]) == 1
    elif command == "ProjectorFOV" and len(tokens) >= 4:
        sample["fovDegrees"] = _safe_float(tokens[3])
    samples.append(sample)


def _parse_simdis_timestamp(raw: Any, *, reference_year: int) -> datetime | None:
    parsed = parse_iso_datetime(raw)
    if parsed is not None:
        return parsed
    if not isinstance(raw, str) or not raw.strip():
        return None
    parts = raw.split()
    if len(parts) < 6:
        ordinal_parts = raw.split(":")
        if len(ordinal_parts) < 4:
            return None
        try:
            day_of_year = int(ordinal_parts[0])
            hour = int(ordinal_parts[1])
            minute = int(ordinal_parts[2])
            second = float(ordinal_parts[3])
        except ValueError:
            return None
        base = datetime(reference_year, 1, 1, tzinfo=timezone.utc)
        delta = timedelta(days=day_of_year - 1, hours=hour, minutes=minute, seconds=second)
        return base + delta
    try:
        year = int(parts[0]) if len(parts[0]) == 4 else reference_year
        month = int(parts[1]) if len(parts[0]) == 4 else int(parts[0])
        day = int(parts[2]) if len(parts[0]) == 4 else int(parts[1])
        hour = int(parts[3]) if len(parts[0]) == 4 else int(parts[2])
        minute = int(parts[4]) if len(parts[0]) == 4 else int(parts[3])
        second = float(parts[5]) if len(parts[0]) == 4 else float(parts[4])
    except ValueError:
        return None
    second_int = int(second)
    microsecond = int(round((second - second_int) * 1_000_000))
    return datetime(year, month, day, hour, minute, second_int, microsecond, tzinfo=timezone.utc)


def _iso_datetime(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, str):
        return value
    return ""


def _parse_simdis_update(tokens: tuple[str, ...]) -> dict[str, Any] | None:
    if len(tokens) < 6:
        return None
    platform_id = tokens[1]
    lat = to_float(tokens[3])
    lon = to_float(tokens[4])
    alt = to_float(tokens[5])
    if lat is None or lon is None or alt is None:
        return None
    return {
        "id": platform_id,
        "timestamp": parse_iso_datetime(tokens[2]),
        "position": (lat, lon, alt),
        "heading": to_float(tokens[6]),
        "pitch": to_float(tokens[7]),
        "roll": to_float(tokens[8]),
    }


def _tokenize(raw_line: str) -> tuple[str, ...]:
    try:
        return tuple(shlex.split(raw_line.strip(), posix=True))
    except ValueError:
        return ()


def _safe_float(value: Any) -> float:
    return float_or_default(value, 0.0)


def _safe_int(value: Any) -> int | None:
    return to_int(value)


def _after(tokens: tuple[str, ...], needle: str, *, default: str | None = None) -> str | None:
    for index, token in enumerate(tokens):
        if token == needle and index + 1 < len(tokens):
            return tokens[index + 1]
    return default


def _coerce_entity_category(raw: str | None) -> EntityCategory | None:
    if raw is None:
        return None
    try:
        return EntityCategory(raw.lower())
    except ValueError:
        return None


def _category_from_platform_icon(raw: str | None) -> EntityCategory | None:
    if raw is None:
        return None
    normalized = raw.strip().lower()
    mapping = {
        "aircraft": EntityCategory.AIR,
        "air": EntityCategory.AIR,
        "ship": EntityCategory.SURFACE,
        "surface": EntityCategory.SURFACE,
        "boat": EntityCategory.SURFACE,
        "site": EntityCategory.GROUND,
        "ground": EntityCategory.GROUND,
        "sensor": EntityCategory.SENSOR,
        "radar": EntityCategory.SENSOR,
        "subsurface": EntityCategory.SUBSURFACE,
        "sub": EntityCategory.SUBSURFACE,
        "satellite": EntityCategory.SPACE,
        "space": EntityCategory.SPACE,
    }
    return mapping.get(normalized)


def _dict_position_to_lat_lon_alt(value: Any) -> tuple[float, float, float] | None:
    if isinstance(value, dict):
        lon = to_float(value.get("lon"))
        lat = to_float(value.get("lat"))
        alt = to_float(value.get("alt"))
    else:
        lon = to_float(getattr(value, "lon", None))
        lat = to_float(getattr(value, "lat", None))
        alt = to_float(getattr(value, "alt", None))
    if lon is None or lat is None or alt is None:
        return None
    return lon, lat, alt


def _simdis_trajectory_point(sample: Any) -> tuple[datetime | None, float, float, float] | None:
    value = safe_get(sample, "value")
    if not isinstance(value, list) or len(value) < 3:
        return None
    if not isinstance(value[0], (int, float)) or not isinstance(value[1], (int, float)) or not isinstance(value[2], (int, float)):
        return None
    stamp = parse_iso_datetime(safe_get(sample, "t"))
    return stamp, float(value[1]), float(value[0]), float(value[2])


def _soap_trajectory_point(sample: Any) -> tuple[datetime | None, float, float, float] | None:
    return _simdis_trajectory_point(sample)


def _select_orb_position(platform: OrbPlatform) -> tuple[float, float, float] | None:
    candidate_waypoints: list[Any] = []
    for waypoint in platform.repeated.get("WAYPOINT", []):
        candidate_waypoints.append(waypoint)

    waypoint_property = safe_get(platform.properties, "WAYPOINT")
    if waypoint_property is not None:
        candidate_waypoints.append(waypoint_property)

    for waypoint in candidate_waypoints:
        if isinstance(waypoint, tuple) and len(waypoint) >= 3 and _looks_like_geo(to_float(waypoint[0]), to_float(waypoint[1])):
            return float(waypoint[0]), float(waypoint[1]), float(waypoint[2])  # type: ignore[arg-type]
    state = platform.state
    if isinstance(state, tuple) and len(state) >= 3 and _looks_like_geo(to_float(state[0]), to_float(state[1])):
        return float(state[0]), float(state[1]), float(state[2])  # type: ignore[arg-type]
    return None


def _looks_like_geo(lat: float | None, lon: float | None) -> bool:
    if lat is None or lon is None:
        return False
    return -90 <= lat <= 90 and -180 <= lon <= 180


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


def _packet_to_scene_overlay(packet: dict[str, Any], packet_id: str) -> SceneOverlay | None:
    polyline = safe_get(packet, "polyline")
    rectangle = safe_get(packet, "rectangle")
    corridor = safe_get(packet, "corridor")
    ellipse = safe_get(packet, "ellipse")
    wall = safe_get(packet, "wall")
    box = safe_get(packet, "box")
    if isinstance(polyline, dict):
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

    if isinstance(corridor, dict):
        corridor_positions = safe_get(corridor, "positions")
        if isinstance(corridor_positions, dict):
            corridor_positions = safe_get(corridor_positions, "cartographicDegrees")
        if not isinstance(corridor_positions, list) or len(corridor_positions) < 6:
            return None

        points: list[Wgs84Position] = []
        for i in range(0, len(corridor_positions) - 2, 3):
            lon = to_float(corridor_positions[i])
            lat = to_float(corridor_positions[i + 1])
            alt = to_float(corridor_positions[i + 2])
            if lon is None or lat is None or alt is None:
                return None
            points.append(Wgs84Position(longitudeDeg=lon, latitudeDeg=lat, altitudeM=alt))
        if not points:
            return None

        corner_type = safe_get(corridor, "cornerType")
        if isinstance(corner_type, str):
            normalized_corner_type = corner_type.lower()
        else:
            normalized_corner_type = None
        width = to_float(safe_get(corridor, "width"))
        if width is None:
            return None

        return SceneOverlay(
            objectType="overlay",
            id=packet_id,
            name=safe_get(packet, "name") or packet_id,
            position=points[0],
            geometryType="corridor",
            corridor=SceneCorridor(
                positions=points,
                widthMeters=width,
                heightMeters=to_float(safe_get(corridor, "height")),
                extrudedHeightMeters=to_float(safe_get(corridor, "extrudedHeight")),
                cornerType=normalized_corner_type,  # type: ignore[arg-type]
                clampToGround=bool(safe_get(corridor, "clampToGround")),
            ),
            style=_packet_style(packet, for_overlay=True),
            attributes={"source": safe_get(packet, "source") or "czml"},
            source=safe_get(packet, "source"),
            timestamp=None,
        )

    if isinstance(rectangle, dict):
        coordinates = safe_get(rectangle, "coordinates")
        if isinstance(coordinates, dict):
            bounds = safe_get(coordinates, "wsenDegrees")
        else:
            bounds = safe_get(rectangle, "wsenDegrees")
        if not isinstance(bounds, list) or len(bounds) != 4:
            return None
        west = to_float(bounds[0])
        south = to_float(bounds[1])
        east = to_float(bounds[2])
        north = to_float(bounds[3])
        if west is None or south is None or east is None or north is None:
            return None
        return SceneOverlay(
            objectType="overlay",
            id=packet_id,
            name=safe_get(packet, "name") or packet_id,
            position=Wgs84Position(longitudeDeg=(west + east) / 2.0, latitudeDeg=(south + north) / 2.0, altitudeM=to_float(safe_get(rectangle, "height")) or 0.0),
            geometryType="rectangle",
            rectangle=SceneRectangle(
                westSouthEastNorthDegrees=(west, south, east, north),
                heightMeters=to_float(safe_get(rectangle, "height")),
                extrudedHeightMeters=to_float(safe_get(rectangle, "extrudedHeight")),
                rotationDegrees=to_float(safe_get(rectangle, "rotation")),
                stRotationDegrees=to_float(safe_get(rectangle, "stRotation")),
            ),
            style=_packet_style(packet, for_overlay=True),
            attributes={"source": safe_get(packet, "source") or "czml"},
            source=safe_get(packet, "source"),
            timestamp=None,
        )

    if isinstance(ellipse, dict):
        major = to_float(safe_get(ellipse, "semiMajorAxis"))
        minor = to_float(safe_get(ellipse, "semiMinorAxis"))
        if major is None or minor is None:
            return None
        center = _extract_czml_packet_position(packet)
        if center is None:
            return None
        lon, lat, alt = center
        is_circle = abs(major - minor) <= 1e-9
        if is_circle:
            return SceneOverlay(
                objectType="overlay",
                id=packet_id,
                name=safe_get(packet, "name") or packet_id,
                position=Wgs84Position(longitudeDeg=lon, latitudeDeg=lat, altitudeM=alt),
                geometryType="circle",
                circle=SceneCircle(
                    radiusMeters=major,
                    heightMeters=to_float(safe_get(ellipse, "height")),
                    extrudedHeightMeters=to_float(safe_get(ellipse, "extrudedHeight")),
                    rotationDegrees=to_float(safe_get(ellipse, "rotation")),
                    stRotationDegrees=to_float(safe_get(ellipse, "stRotation")),
                    clampToGround=bool(safe_get(ellipse, "clampToGround")),
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
            geometryType="ellipse",
            ellipse=SceneEllipse(
                semiMajorAxisMeters=major,
                semiMinorAxisMeters=minor,
                heightMeters=to_float(safe_get(ellipse, "height")),
                extrudedHeightMeters=to_float(safe_get(ellipse, "extrudedHeight")),
                rotationDegrees=to_float(safe_get(ellipse, "rotation")),
                stRotationDegrees=to_float(safe_get(ellipse, "stRotation")),
                clampToGround=bool(safe_get(ellipse, "clampToGround")),
            ),
            style=_packet_style(packet, for_overlay=True),
            attributes={"source": safe_get(packet, "source") or "czml"},
            source=safe_get(packet, "source"),
            timestamp=None,
        )

    if isinstance(wall, dict):
        wall_positions = safe_get(wall, "positions")
        if isinstance(wall_positions, dict):
            wall_positions = safe_get(wall_positions, "cartographicDegrees")
        if not isinstance(wall_positions, list) or len(wall_positions) < 6:
            return None

        points: list[Wgs84Position] = []
        for i in range(0, len(wall_positions) - 2, 3):
            lon = to_float(wall_positions[i])
            lat = to_float(wall_positions[i + 1])
            alt = to_float(wall_positions[i + 2])
            if lon is None or lat is None or alt is None:
                return None
            points.append(Wgs84Position(longitudeDeg=lon, latitudeDeg=lat, altitudeM=alt))
        if not points:
            return None

        min_heights = safe_get(wall, "minimumHeights")
        max_heights = safe_get(wall, "maximumHeights")
        min_values = [to_float(value) for value in min_heights] if isinstance(min_heights, list) else None
        max_values = [to_float(value) for value in max_heights] if isinstance(max_heights, list) else None
        if min_values is not None and any(value is None for value in min_values):
            return None
        if max_values is not None and any(value is None for value in max_values):
            return None

        return SceneOverlay(
            objectType="overlay",
            id=packet_id,
            name=safe_get(packet, "name") or packet_id,
            position=points[0],
            geometryType="wall",
            wall=SceneWall(
                positions=points,
                minimumHeightsMeters=[float(value) for value in min_values] if min_values is not None else None,
                maximumHeightsMeters=[float(value) for value in max_values] if max_values is not None else None,
                clampToGround=bool(safe_get(wall, "clampToGround")),
            ),
            style=_packet_style(packet, for_overlay=True),
            attributes={"source": safe_get(packet, "source") or "czml"},
            source=safe_get(packet, "source"),
            timestamp=None,
        )

    if isinstance(box, dict):
        dimensions = safe_get(box, "dimensions")
        if isinstance(dimensions, dict):
            dimensions = safe_get(dimensions, "cartesian")
        if not isinstance(dimensions, list) or len(dimensions) != 3:
            return None
        x = to_float(dimensions[0])
        y = to_float(dimensions[1])
        z = to_float(dimensions[2])
        if x is None or y is None or z is None:
            return None
        center = _extract_czml_packet_position(packet)
        if center is None:
            return None
        lon, lat, alt = center
        return SceneOverlay(
            objectType="overlay",
            id=packet_id,
            name=safe_get(packet, "name") or packet_id,
            position=Wgs84Position(longitudeDeg=lon, latitudeDeg=lat, altitudeM=alt),
            geometryType="box",
            box=SceneBox(dimensionsMeters=(x, y, z)),
            style=_packet_style(packet, for_overlay=True),
            attributes={"source": safe_get(packet, "source") or "czml"},
            source=safe_get(packet, "source"),
            timestamp=None,
        )

    return None


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
        for geometry_key in ("polyline", "polygon", "rectangle", "corridor", "ellipse", "wall", "box"):
            geometry = safe_get(packet, geometry_key)
            if isinstance(geometry, dict):
                material = safe_get(geometry, "material")
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


def _find_child(node: Any, name: str) -> Any | None:
    for child in node.iter():
        if _local_name(child.tag) == name:
            return child
    return None


def _text(node: Any, name: str, *, default: str | None = None) -> str | None:
    child = _find_child(node, name)
    if child is None or child.text is None:
        return default
    value = child.text.strip()
    return value if value else default


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _value_to_primitive(raw: str) -> Any:
    text = raw.strip()
    if text == "":
        return ""
    if text.lower() in {"true", "false"}:
        return text.lower() == "true"
    try:
        return float(text) if "." in text else int(text)
    except ValueError:
        return text


def _collect_list_values(node: Any) -> list[Any] | None:
    if node is None:
        return None
    values: list[Any] = []
    for child in list(node):
        if child.text is None:
            continue
        values.append(_value_to_primitive(child.text))
    return values


def _coerce_scalar_text(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    return None


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


def scene_default_timestamp(entity: SceneEntity) -> datetime:
    if entity.timestamp is not None:
        return entity.timestamp
    return utc_now()


def _build_orb_from_entities(entities: list[SceneEntity]) -> str:
    lines: list[str] = ["56 revision\n", "SOAP_SCENARIO_FILE\n"]
    for entity in entities:
        kind = (entity.category.value.upper() if entity.category else "PLATFORM")
        name = _orb_quote(entity.id)
        lines.append(f'DEFINE PLATFORM {kind} {name}\n')
        lines.append(
            f'\tWAYPOINT {entity.position.latitudeDeg:.8f} {entity.position.longitudeDeg:.8f} {entity.position.altitudeM:.3f}\n'
        )
    return "".join(lines)


def _orb_quote(value: str) -> str:
    return f'"{value.replace("\\", "\\\\").replace("\"", "\\\"")}"'


def _is_probable_raw_orb_text(path_or_text: str | Path) -> bool:
    if isinstance(path_or_text, PathLike) and not isinstance(path_or_text, str):
        return False
    candidate = str(path_or_text)
    if "\n" in candidate or "\r" in candidate:
        return True
    stripped = candidate.lstrip()
    if not stripped:
        return False
    return stripped.startswith("DEFINE ") or "SOAP_SCENARIO_FILE" in stripped or stripped.endswith(" revision")


def _safe_int(value: Any) -> int | None:
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_asi_time(raw: Any, *, reference_year: int) -> datetime | None:
    parsed = parse_iso_datetime(raw)
    if parsed is not None:
        return parsed
    if not isinstance(raw, str):
        return None
    cleaned = raw.strip().strip('"')
    parts = cleaned.split(":")
    if len(parts) != 4:
        return None
    day_of_year = _safe_int(parts[0])
    hour = _safe_int(parts[1])
    minute = _safe_int(parts[2])
    second_part = _safe_float(parts[3])
    if day_of_year is None or hour is None or minute is None or second_part is None:
        return None
    base = datetime(reference_year, 1, 1, tzinfo=timezone.utc) + timedelta(days=max(day_of_year - 1, 0))
    seconds = int(second_part)
    microseconds = int(round((second_part - seconds) * 1_000_000))
    return base.replace(hour=hour, minute=minute, second=seconds, microsecond=microseconds)


def _parse_platform_data(tokens: tuple[str, ...], *, reference_year: int) -> dict[str, Any] | None:
    if len(tokens) < 10:
        return None
    stamp = _parse_asi_time(tokens[0], reference_year=reference_year)
    lat = _safe_float(tokens[1])
    lon = _safe_float(tokens[2])
    alt = _safe_float(tokens[3])
    heading = _safe_float(tokens[4])
    pitch = _safe_float(tokens[5])
    roll = _safe_float(tokens[6])
    vx = _safe_float(tokens[7])
    vy = _safe_float(tokens[8])
    vz = _safe_float(tokens[9])
    if stamp is None or lat is None or lon is None or alt is None:
        return None
    return {
        "time": stamp,
        "position": {"lat": lat, "lon": lon, "alt": alt},
        "heading": heading,
        "pitch": pitch,
        "roll": roll,
        "vx": vx if vx is not None else 0.0,
        "vy": vy if vy is not None else 0.0,
        "vz": vz if vz is not None else 0.0,
    }


def _parse_platform_update(tokens: tuple[str, ...], *, reference_year: int) -> dict[str, Any] | None:
    if len(tokens) < 7:
        return None
    stamp = _parse_asi_time(tokens[0], reference_year=reference_year)
    lat = _safe_float(tokens[1])
    lon = _safe_float(tokens[2])
    alt = _safe_float(tokens[3])
    heading = _safe_float(tokens[4])
    pitch = _safe_float(tokens[5])
    roll = _safe_float(tokens[6])
    if stamp is None or lat is None or lon is None or alt is None:
        return None
    return {
        "time": stamp,
        "position": {"lat": lat, "lon": lon, "alt": alt},
        "heading": heading,
        "pitch": pitch,
        "roll": roll,
        "vx": 0.0,
        "vy": 0.0,
        "vz": 0.0,
    }


def _append_beam_sample(beam: dict[str, Any], tokens: tuple[str, ...], command: str, reference_year: int) -> None:
    samples: list[dict[str, Any]] = beam.setdefault("samples", [])
    timestamp = _parse_asi_time(tokens[2], reference_year=reference_year)
    if timestamp is None:
        return
    sample = _sample_for_timestamp(samples, timestamp)
    sample["time"] = timestamp
    if command == "BeamOnOffCmd" and len(tokens) >= 4:
        sample["on"] = _safe_int(tokens[3]) == 1
    elif command == "BeamColorCmd" and len(tokens) >= 4:
        sample["color"] = tokens[3].strip('"')
    elif command == "BeamDataRAE" and len(tokens) >= 6:
        sample["az"] = _safe_float(tokens[3])
        sample["el"] = _safe_float(tokens[4])
        sample["rangeMeters"] = _safe_float(tokens[5])
    elif command == "BeamTargetIDCmd" and len(tokens) >= 4:
        sample["targetPlatformId"] = tokens[3].strip('"')


def _append_gate_sample(gate: dict[str, Any], tokens: tuple[str, ...], command: str, reference_year: int) -> None:
    samples: list[dict[str, Any]] = gate.setdefault("samples", [])
    timestamp = _parse_asi_time(tokens[2], reference_year=reference_year)
    if timestamp is None:
        return
    sample = _sample_for_timestamp(samples, timestamp)
    sample["time"] = timestamp
    if command == "GateOnOffCmd" and len(tokens) >= 4:
        sample["on"] = _safe_int(tokens[3]) == 1
    elif command == "GateColorCmd" and len(tokens) >= 4:
        sample["color"] = tokens[3].strip('"')
    elif command == "GateDataRAE" and len(tokens) >= 10:
        sample["az"] = _safe_float(tokens[3])
        sample["el"] = _safe_float(tokens[4])
        sample["width"] = _safe_float(tokens[5])
        sample["height"] = _safe_float(tokens[6])
        sample["minRangeMeters"] = _safe_float(tokens[7])
        sample["maxRangeMeters"] = _safe_float(tokens[8])
        sample["centroidMeters"] = _safe_float(tokens[9])


def _append_projector_sample(projector: dict[str, Any], tokens: tuple[str, ...], command: str, reference_year: int) -> None:
    samples: list[dict[str, Any]] = projector.setdefault("samples", [])
    timestamp = _parse_asi_time(tokens[2], reference_year=reference_year)
    if timestamp is None:
        return
    sample = _sample_for_timestamp(samples, timestamp)
    sample["time"] = timestamp
    if command == "ProjectorOn" and len(tokens) >= 4:
        sample["on"] = _safe_int(tokens[3]) == 1
    elif command == "ProjectorFOV" and len(tokens) >= 4:
        sample["fovDegrees"] = _safe_float(tokens[3])


def _sample_for_timestamp(samples: list[dict[str, Any]], timestamp: datetime) -> dict[str, Any]:
    if samples and samples[-1].get("time") == timestamp:
        return samples[-1]
    sample: dict[str, Any] = {}
    samples.append(sample)
    return sample


def _latest_asi_sample(samples: list[dict[str, Any]]) -> dict[str, Any] | None:
    latest: dict[str, Any] | None = None
    latest_stamp: datetime | None = None
    for sample in samples:
        stamp = sample.get("time")
        if not isinstance(stamp, datetime):
            continue
        if latest_stamp is None or stamp >= latest_stamp:
            latest = sample
            latest_stamp = stamp
    return latest


def _scene_platform_sample(sample: dict[str, Any]) -> dict[str, Any]:
    stamp = sample.get("time")
    position = sample.get("position") or {}
    return {
        "time": stamp.isoformat() if isinstance(stamp, datetime) else stamp,
        "position": {
            "lat": _safe_float(safe_get(position, "lat")),
            "lon": _safe_float(safe_get(position, "lon")),
            "alt": _safe_float(safe_get(position, "alt")),
        },
        "yawDeg": sample.get("heading"),
        "pitchDeg": sample.get("pitch"),
        "rollDeg": sample.get("roll"),
        "vx": sample.get("vx", 0.0),
        "vy": sample.get("vy", 0.0),
        "vz": sample.get("vz", 0.0),
    }
