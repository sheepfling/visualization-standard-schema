from __future__ import annotations

from os import PathLike
from pathlib import Path

from ..models import SceneEntity
from ..orb.typed import OrbPlatform
from ..util import safe_get, to_float


def _select_orb_position(platform: OrbPlatform) -> tuple[float, float, float] | None:
    candidate_waypoints: list[object] = []
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


def _orb_quote(value: str) -> str:
    return f'"{value.replace("\\", "\\\\").replace("\"", "\\\"")}"'


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
