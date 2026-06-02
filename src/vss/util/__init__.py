from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

__all__ = [
    "parse_iso_datetime",
    "to_int",
    "safe_int",
    "safe_get",
    "simdis_fallback_timestamp_iso",
    "ensure_trailing_newline",
    "to_float",
    "safe_float",
    "to_bool",
    "bool_to_int",
    "float_or_default",
    "format_float",
    "normalize_configs",
    "utc_now_isoformat",
    "utc_now",
    "dumps_json",
    "isoformat_or_default",
    "write_text_file",
]


def parse_iso_datetime(raw: Any) -> datetime | None:
    if not isinstance(raw, str):
        return None
    cleaned = raw.strip().replace("Z", "+00:00")
    if not cleaned:
        return None
    try:
        parsed = datetime.fromisoformat(cleaned)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_now_isoformat() -> str:
    return utc_now().isoformat()


def to_float(raw: Any) -> float | None:
    try:
        if raw is None:
            return None
        return float(raw)
    except (TypeError, ValueError):
        return None


def safe_float(raw: Any) -> float | None:
    return to_float(raw)


def to_int(raw: Any) -> int | None:
    try:
        if raw is None:
            return None
        return int(raw)
    except (TypeError, ValueError):
        return None


def safe_int(raw: Any) -> int | None:
    return to_int(raw)


def to_bool(raw: Any) -> bool | None:
    if raw is None:
        return None
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, (int, float)):
        return bool(raw)
    if isinstance(raw, str):
        value = raw.strip().lower()
        if value in {"1", "true", "yes", "on"}:
            return True
        if value in {"0", "false", "no", "off"}:
            return False
    return None


def bool_to_int(value: Any) -> int:
    return 1 if bool(value) else 0


def float_or_default(value: Any, default: float) -> float:
    parsed = to_float(value)
    return parsed if parsed is not None else float(default)


def format_float(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "0"
    if number.is_integer():
        return str(int(number))
    return f"{number:.3f}".rstrip("0").rstrip(".")


def normalize_configs(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def dumps_json(value: Any, *, indent: int = 2) -> str:
    return json.dumps(value, indent=indent)


def safe_get(mapping: Any, key: str) -> Any | None:
    if isinstance(mapping, dict):
        return mapping.get(key)
    return None


def isoformat_or_default(value: datetime | None, *, fallback_iso: str) -> str:
    if value is None:
        return fallback_iso
    return value.isoformat()


simdis_fallback_timestamp_iso: str = "1970-01-01T00:00:00+00:00"


def ensure_trailing_newline(text: str) -> str:
    return text if text.endswith("\n") else f"{text}\n"


def write_text_file(
    path: str | Path,
    text: str,
    *,
    encoding: str = "utf-8",
    trailing_newline: bool = True,
) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = ensure_trailing_newline(text) if trailing_newline else text
    output_path.write_text(payload, encoding=encoding)
    return output_path
