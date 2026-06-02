from __future__ import annotations

from pathlib import Path
from typing import Any

from ..models import Orientation, SceneEntity, Style, VssScene, Wgs84Position
from ..simdis import compile_simdis_asi, load_simdis_bundle
from ..simdis.gog import parse_simdis_gog_to_scene
from .categories import _category_from_platform_icon, _coerce_entity_category
from .scene import _annotation_state_to_scene_entity, _build_scene, _sensor_state_to_scene_entity
from .points import _after, _append_beam_sample, _append_gate_sample, _append_projector_sample, _dict_position_to_lat_lon_alt, _latest_asi_sample, _latest_point, _parse_platform_data, _parse_platform_update, _scene_platform_sample, _safe_float, _safe_int, _simdis_trajectory_point, _tokenize


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
            beam_states[beam_id] = {"beamId": beam_id, "hostPlatformId": host_platform_id, "type": "BODY", "samples": []}
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
            gate_states[gate_id] = {"gateId": gate_id, "hostBeamId": host_beam_id, "type": "BODY", "samples": []}
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
            projector_states[projector_id] = {"projectorId": projector_id, "hostPlatformId": host_platform_id, "samples": []}
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
    timestamps: list = []
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
        gates = [state for state in gate_states.values() if beam_states.get(state.get("hostBeamId"), {}).get("hostPlatformId") == platform_id]
        if gates:
            simdis_payload["gates"] = [dict(state) for state in gates]

        entities.append(
            SceneEntity(
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
        )
        if latest.get("time") is not None:
            timestamps.append(latest.get("time"))

    return _build_scene(source=source, name="SIMDIS ASI Scene", objects=entities, created=max(timestamps) if timestamps else None)


def parse_simdis_bundle_to_scene(path_or_bundle: str | Path, *, source: str | None = None) -> VssScene:
    bundle = load_simdis_bundle(path_or_bundle)
    scene_source = source or bundle.source
    objects: list[SceneEntity] = []
    timestamps: list = []

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
        platform_properties = getattr(platform, "properties", {})
        if not isinstance(platform_properties, dict):
            platform_properties = {}
        platform_category = getattr(platform, "category", None)
        if platform_category is None:
            platform_category = platform_properties.get("category")
        objects.append(
            SceneEntity(
                objectType="entity",
                id=platform.id,
                name=platform.name,
                category=_coerce_entity_category(platform_category),
                position=Wgs84Position(longitudeDeg=lon, latitudeDeg=lat, altitudeM=alt),
                orientation=None,
                style=None,
                attributes=platform_properties,
                source=scene_source,
                timestamp=stamp,
            )
        )
        if stamp is not None:
            timestamps.append(stamp)

    objects.extend(_sensor_state_to_scene_entity(sensor, source=scene_source) for sensor in getattr(bundle.entities, "sensors", []))
    objects.extend(_annotation_state_to_scene_entity(annotation, source=scene_source) for annotation in getattr(bundle.entities, "annotations", []))

    gog_scene = parse_simdis_gog_to_scene(bundle.overlaysGog, source=scene_source, include_annotations=False)
    objects.extend(gog_scene.objects)

    return _build_scene(source=scene_source, name="SIMDIS Bundle Scene", objects=objects, created=max(timestamps) if timestamps else None)


def emit_simdis_asi_from_scene(scene: VssScene) -> str:
    if not scene.entities:
        raise ValueError("scene has no entities to emit")
    return compile_simdis_asi(scene)


__all__ = [
    "emit_simdis_asi_from_scene",
    "parse_simdis_asi_to_scene",
    "parse_simdis_bundle_to_scene",
]
