from __future__ import annotations

from typing import Any


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


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
