from __future__ import annotations

from typing import Any

from ..models import EntityCategory


def _coerce_entity_category(raw: Any) -> EntityCategory | None:
    if raw is None:
        return None
    if isinstance(raw, EntityCategory):
        return raw
    if not isinstance(raw, str):
        return None
    try:
        return EntityCategory(raw.strip().lower())
    except ValueError:
        return None


def _category_from_platform_icon(raw: Any) -> EntityCategory | None:
    if raw is None:
        return None
    if isinstance(raw, EntityCategory):
        return raw
    if not isinstance(raw, str):
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
