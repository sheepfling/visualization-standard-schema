from __future__ import annotations

from datetime import datetime
from pathlib import PurePosixPath
from typing import Any

from ..models import EntityUpsertMessage, SceneEntity, VssScene
from ..util import bool_to_int, float_or_default, format_float, normalize_configs


def compile_simdis_asi(scene: VssScene) -> str:
    lines: list[str] = []
    reference_year = _reference_year(scene)
    lines.append(f"ReferenceYear {reference_year}")
    lines.append("DegreeAngles 1")
    lines.append("")

    for entity in scene.entities:
        if _is_annotation_candidate(entity):
            continue
        lines.extend(_compile_platform_block(entity))
        lines.extend(_compile_hosted_commands(entity))
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def compile_simdis_asi_message(message: EntityUpsertMessage) -> str:
    scene = VssScene.from_messages(
        [message],
        scene_id=message.messageId,
        scene_name=message.payload.name,
        description=f"SIMDIS ASI export for {message.payload.entityId}",
        generator="visualization-standard-schema",
    )
    entity = scene.entities[0]
    lines = [f"ReferenceYear {_reference_year(scene)}", "DegreeAngles 1", ""]
    lines.extend(_compile_platform_block(entity))
    lines.extend(_compile_hosted_commands(entity))
    return "\n".join(lines).rstrip() + "\n"


def _compile_platform_block(entity: SceneEntity) -> list[str]:
    simdis = _simdis_config(entity)
    platform_id = _simdis_string(simdis.get("platformId"), default=entity.id)
    name = _simdis_string(simdis.get("platformName"), default=entity.name)
    icon = _simdis_string(simdis.get("platformIcon"), default=_default_platform_icon(entity))
    label = _simdis_string(simdis.get("platformLabel"), default=entity.style.label if entity.style and entity.style.label else "")
    samples = _platform_samples(entity, simdis)
    category = entity.category.value if entity.category is not None else "other"

    lines = [
        f"PlatformID {platform_id}",
        f'PlatformName {platform_id} "{name}"',
        f'PLATFORM {platform_id} NAME "{name}" CATEGORY {category}',
    ]
    if icon:
        lines.append(f'PlatformIcon {platform_id} "{icon}"')
    if label:
        lines.append(f'PLATFORM_LABEL {platform_id} "{label}"')
    for sample in samples:
        lines.append(
            "PLATFORM_UPDATE "
            f"{platform_id} {sample['time']} {sample['lat']:.4f} {sample['lon']:.4f} {sample['alt']:.3f} "
            f"{sample['yaw']} {sample['pitch']} {sample['roll']} {sample['vx']} {sample['vy']} {sample['vz']}"
        )
    return lines


def _compile_hosted_commands(entity: SceneEntity) -> list[str]:
    simdis = _simdis_config(entity)
    lines: list[str] = []
    lines.extend(_compile_beams(entity, simdis))
    lines.extend(_compile_gates(entity, simdis))
    lines.extend(_compile_projectors(entity, simdis))
    return lines


def _compile_beams(entity: SceneEntity, simdis: dict[str, Any]) -> list[str]:
    beam_configs = normalize_configs(simdis.get("beams") or simdis.get("beam"))
    lines: list[str] = []
    for index, config in enumerate(beam_configs, start=1):
        beam_id = _simdis_string(config.get("beamId"), default=_default_child_id(entity.id, "beam", index))
        host_platform_id = _simdis_string(config.get("hostPlatformId"), default=entity.id)
        beam_type = _simdis_string(config.get("type"), default="BODY")
        lines.append(f"BeamID {host_platform_id} {beam_id}")
        lines.append(f'BeamType {beam_id} "{beam_type}"')
        if config.get("horzBwDeg") is not None:
            lines.append(f"HorzBW {beam_id} {format_float(config['horzBwDeg'])}")
        if config.get("vertBwDeg") is not None:
            lines.append(f"VertBW {beam_id} {format_float(config['vertBwDeg'])}")
        for sample in normalize_configs(config.get("samples")):
            timestamp = _simdis_time(sample.get("time"), default=entity.timestamp)
            if sample.get("on") is not None:
                lines.append(f"BeamOnOffCmd {beam_id} {timestamp} {bool_to_int(sample['on'])}")
            if sample.get("color") is not None:
                lines.append(f"BeamColorCmd {beam_id} {timestamp} {sample['color']}")
            if all(sample.get(key) is not None for key in ("az", "el", "rangeMeters")):
                lines.append(
                    "BeamDataRAE "
                    f"{beam_id} {timestamp} {format_float(sample['az'])} {format_float(sample['el'])} {format_float(sample['rangeMeters'])}"
                )
            if sample.get("targetPlatformId") is not None:
                lines.append(f"BeamTargetIDCmd {beam_id} {timestamp} {sample['targetPlatformId']}")
    return lines


def _compile_gates(entity: SceneEntity, simdis: dict[str, Any]) -> list[str]:
    gate_configs = normalize_configs(simdis.get("gates") or simdis.get("gate"))
    lines: list[str] = []
    for index, config in enumerate(gate_configs, start=1):
        gate_id = _simdis_string(config.get("gateId"), default=_default_child_id(entity.id, "gate", index))
        host_beam_id = _simdis_string(config.get("hostBeamId"), default=_default_child_id(entity.id, "beam", index))
        gate_type = _simdis_string(config.get("type"), default="BODY")
        lines.append(f"GateID {host_beam_id} {gate_id}")
        lines.append(f'GateType {gate_id} "{gate_type}"')
        for sample in normalize_configs(config.get("samples")):
            timestamp = _simdis_time(sample.get("time"), default=entity.timestamp)
            if sample.get("on") is not None:
                lines.append(f"GateOnOffCmd {gate_id} {timestamp} {bool_to_int(sample['on'])}")
            if sample.get("color") is not None:
                lines.append(f"GateColorCmd {gate_id} {timestamp} {sample['color']}")
            if all(sample.get(key) is not None for key in ("az", "el", "width", "height", "minRangeMeters", "maxRangeMeters", "centroidMeters")):
                lines.append(
                    "GateDataRAE "
                    f"{gate_id} {timestamp} {format_float(sample['az'])} {format_float(sample['el'])} "
                    f"{format_float(sample['width'])} {format_float(sample['height'])} {format_float(sample['minRangeMeters'])} "
                    f"{format_float(sample['maxRangeMeters'])} {format_float(sample['centroidMeters'])}"
                )
    return lines


def _compile_projectors(entity: SceneEntity, simdis: dict[str, Any]) -> list[str]:
    projector_configs = normalize_configs(simdis.get("projectors") or simdis.get("projector"))
    lines: list[str] = []
    for index, config in enumerate(projector_configs, start=1):
        projector_id = _simdis_string(config.get("projectorId"), default=_default_child_id(entity.id, "projector", index))
        host_platform_id = _simdis_string(config.get("hostPlatformId"), default=entity.id)
        lines.append(f"Projector {host_platform_id} {projector_id}")
        if config.get("rasterFile") is not None:
            lines.append(f'ProjectorRasterFile {projector_id} "{config["rasterFile"]}"')
        if config.get("interpolateFov") is not None:
            lines.append(f"ProjectorInterpolateFOV {projector_id} {bool_to_int(config['interpolateFov'])}")
        for sample in normalize_configs(config.get("samples")):
            timestamp = _simdis_time(sample.get("time"), default=entity.timestamp)
            if sample.get("on") is not None:
                lines.append(f"ProjectorOn {projector_id} {timestamp} {bool_to_int(sample['on'])}")
            if sample.get("fovDegrees") is not None:
                lines.append(f"ProjectorFOV {projector_id} {timestamp} {format_float(sample['fovDegrees'])}")
    return lines


def _platform_samples(entity: SceneEntity, simdis: dict[str, Any]) -> list[dict[str, Any]]:
    samples = normalize_configs(simdis.get("platformSamples"))
    if samples:
        return [_normalize_platform_sample(sample, default_time=entity.timestamp, entity=entity) for sample in samples]
    return [_normalize_platform_sample({}, default_time=entity.timestamp, entity=entity)]


def _normalize_platform_sample(sample: dict[str, Any], *, default_time: datetime | None, entity: SceneEntity | None = None) -> dict[str, Any]:
    if entity is not None:
        position = entity.position
        orientation = entity.orientation
    else:
        position = None
        orientation = None
    raw_position = sample.get("position")
    if isinstance(raw_position, dict):
        position = raw_position
    elif entity is not None and not isinstance(position, dict):
        position = {
            "lat": entity.position.latitudeDeg,
            "lon": entity.position.longitudeDeg,
            "alt": entity.position.altitudeM,
        }

    raw_orientation = sample.get("orientation")
    if isinstance(raw_orientation, dict):
        orientation = raw_orientation

    timestamp = _simdis_time(sample.get("time"), default=default_time)
    if position is None:
        raise ValueError("platform sample is missing position")
    yaw = sample.get("yawDeg", _dict_lookup(orientation, "headingDeg"))
    pitch = sample.get("pitchDeg", _dict_lookup(orientation, "pitchDeg"))
    roll = sample.get("rollDeg", _dict_lookup(orientation, "rollDeg"))
    return {
        "time": timestamp,
        "lat": float_or_default(
            _dict_lookup(position, "lat", "latitudeDeg"),
            entity.position.latitudeDeg if entity is not None else 0.0,
        ),
        "lon": float_or_default(
            _dict_lookup(position, "lon", "longitudeDeg"),
            entity.position.longitudeDeg if entity is not None else 0.0,
        ),
        "alt": float_or_default(
            _dict_lookup(position, "alt", "altitudeM"),
            entity.position.altitudeM if entity is not None else 0.0,
        ),
        "yaw": _format_heading(yaw if yaw is not None else 0.0),
        "pitch": format_float(pitch if pitch is not None else 0.0),
        "roll": format_float(roll if roll is not None else 0.0),
        "vx": format_float(sample.get("vx", 0)),
        "vy": format_float(sample.get("vy", 0)),
        "vz": format_float(sample.get("vz", 0)),
    }


def _simdis_config(entity: SceneEntity) -> dict[str, Any]:
    raw = entity.attributes.get("simdis") if isinstance(entity.attributes, dict) else None
    return raw if isinstance(raw, dict) else {}


def _reference_year(scene: VssScene) -> int:
    candidates: list[int] = []
    if scene.document.created is not None:
        candidates.append(scene.document.created.year)
    for entity in scene.entities:
        if entity.timestamp is not None:
            candidates.append(entity.timestamp.year)
    return max(candidates) if candidates else 1970


def _simdis_time(value: Any, *, default: datetime | None) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, str) and value.strip():
        return value
    if default is not None:
        return default.isoformat()
    return "-1"


def _simdis_string(value: Any, *, default: str) -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _default_platform_icon(entity: SceneEntity) -> str:
    if entity.style is not None and entity.style.iconUri is not None:
        stem = PurePosixPath(str(entity.style.iconUri)).stem
        return stem or (entity.category.value if entity.category else "platform")
    if entity.category is None:
        return "platform"
    return {
        "air": "aircraft",
        "ground": "site",
        "surface": "ship",
        "subsurface": "subsurface",
        "space": "satellite",
        "sensor": "sensor",
        "overlay": "site",
        "other": "platform",
    }.get(entity.category.value, "platform")


def _default_child_id(parent_id: str, child_kind: str, index: int) -> str:
    return f"{parent_id}-{child_kind}-{index}"


def _dict_lookup(value: Any, *keys: str) -> Any:
    if not isinstance(value, dict):
        for key in keys:
            if hasattr(value, key):
                return getattr(value, key)
        return None
    for key in keys:
        if key in value:
            return value[key]
    return None


def _format_heading(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "000"
    if number.is_integer():
        return f"{int(number):03d}"
    return f"{number:.3f}".rstrip("0").rstrip(".")


def _is_annotation_candidate(entity: SceneEntity) -> bool:
    style = entity.style
    if entity.category is not None and entity.category.value == "sensor":
        return False
    if entity.category is None or entity.category.value != "ground":
        return False
    if style is None:
        return False
    if style.modelUri is not None:
        return False
    return bool(style.label or style.iconUri)
