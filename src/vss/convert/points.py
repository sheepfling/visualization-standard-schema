from __future__ import annotations

import shlex
from datetime import datetime, timedelta, timezone
from typing import Any

from ..util import parse_iso_datetime, safe_float, safe_get, safe_int, to_float


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


def _sample_for_timestamp(samples: list[dict[str, Any]], timestamp: datetime) -> dict[str, Any]:
    if samples and samples[-1].get("time") == timestamp:
        return samples[-1]
    sample: dict[str, Any] = {}
    samples.append(sample)
    return sample


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
    return {
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


def _latest_point(points: list[tuple[datetime | None, float, float, float]]) -> tuple[float, float, float, datetime | None]:
    for stamp, lat, lon, alt in sorted(points, key=lambda item: item[0] or datetime.min.replace(tzinfo=timezone.utc), reverse=True):
        return lat, lon, alt, stamp
    raise ValueError("No points")


def _tokenize(raw_line: str) -> tuple[str, ...]:
    try:
        return tuple(shlex.split(raw_line.strip(), posix=True))
    except ValueError:
        return ()


def _safe_float(value: Any) -> float | None:
    return safe_float(value)


def _safe_int(value: Any) -> int | None:
    return safe_int(value)


def _after(tokens: tuple[str, ...], needle: str, *, default: str | None = None) -> str | None:
    for index, token in enumerate(tokens):
        if token == needle and index + 1 < len(tokens):
            return tokens[index + 1]
    return default


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
