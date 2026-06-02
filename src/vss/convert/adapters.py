from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Literal

from ..models import VssScene
from .czml import emit_czml_from_scene, parse_czml_file_to_scene, parse_czml_to_scene
from .orb import emit_orb_from_scene, parse_orb_to_scene
from .simdis import parse_simdis_asi_to_scene, parse_simdis_bundle_to_scene
from .simdis import emit_simdis_asi_from_scene
from .soap import emit_soap_envelope_from_scene, parse_soap_bundle_to_scene, parse_soap_to_scene

TargetName = Literal["czml", "simdis", "soap", "orb"]
FormatName = Literal["czml", "simdis-asi", "simdis-bundle", "soap", "orb"]


@dataclass(frozen=True, slots=True)
class TargetAdapter:
    target: TargetName
    ingest: Callable[[str | Path], VssScene]
    emit: Callable[[VssScene], Any]


@dataclass(frozen=True, slots=True)
class FormatAdapter:
    format: FormatName
    target: TargetName
    ingest: Callable[[str | Path], VssScene]
    emit: Callable[[VssScene], Any] | None


def _ingest_czml(source: str | Path, *, input_format: str | None = None, source_name: str | None = None) -> VssScene:
    if isinstance(source, Path) or (input_format == "path" and Path(str(source)).exists()):
        return parse_czml_file_to_scene(source)
    return parse_czml_to_scene(str(source), source=source_name or "czml")


def _ingest_simdis(source: str | Path, *, input_format: str | None = None, source_name: str | None = None) -> VssScene:
    path = Path(source) if isinstance(source, (str, Path)) else None
    if input_format == "simdis-bundle" or (path is not None and path.exists() and path.is_dir()):
        return parse_simdis_bundle_to_scene(path)
    if input_format == "simdis-asi":
        raw_text = path.read_text(encoding="utf-8") if path is not None and path.exists() else str(source)
        return parse_simdis_asi_to_scene(raw_text, source=source_name or "simdis-asi")
    if path is not None and path.exists():
        try:
            return parse_simdis_bundle_to_scene(path)
        except Exception:
            pass
    raw_text = path.read_text(encoding="utf-8") if path is not None and path.exists() else str(source)
    return parse_simdis_asi_to_scene(raw_text, source=source_name or "simdis-asi")


def _ingest_soap(source: str | Path, *, input_format: str | None = None, source_name: str | None = None) -> VssScene:
    path = Path(source) if isinstance(source, (str, Path)) else None
    if input_format == "soap-bundle" or (path is not None and path.exists() and path.is_dir()):
        return parse_soap_bundle_to_scene(path)
    if input_format == "soap":
        return parse_soap_to_scene(source, source=source_name or "soap-envelope")
    if path is not None and path.exists():
        try:
            return parse_soap_bundle_to_scene(path)
        except Exception:
            pass
    return parse_soap_to_scene(source, source=source_name or "soap-envelope")


def _ingest_orb(source: str | Path, *, input_format: str | None = None, source_name: str | None = None) -> VssScene:
    return parse_orb_to_scene(source)


TARGET_ADAPTERS: dict[TargetName, TargetAdapter] = {
    "czml": TargetAdapter(target="czml", ingest=_ingest_czml, emit=emit_czml_from_scene),
    "simdis": TargetAdapter(target="simdis", ingest=_ingest_simdis, emit=emit_simdis_asi_from_scene),
    "soap": TargetAdapter(target="soap", ingest=_ingest_soap, emit=emit_soap_envelope_from_scene),
    "orb": TargetAdapter(target="orb", ingest=_ingest_orb, emit=emit_orb_from_scene),
}


def _ingest_simdis_bundle(source: str | Path, *, input_format: str | None = None, source_name: str | None = None) -> VssScene:
    return parse_simdis_bundle_to_scene(source, source=source_name or "simdis-bundle")


FORMAT_ADAPTERS: dict[FormatName, FormatAdapter] = {
    "czml": FormatAdapter(format="czml", target="czml", ingest=_ingest_czml, emit=emit_czml_from_scene),
    "simdis-asi": FormatAdapter(format="simdis-asi", target="simdis", ingest=_ingest_simdis, emit=emit_simdis_asi_from_scene),
    "simdis-bundle": FormatAdapter(format="simdis-bundle", target="simdis", ingest=_ingest_simdis_bundle, emit=None),
    "soap": FormatAdapter(format="soap", target="soap", ingest=_ingest_soap, emit=emit_soap_envelope_from_scene),
    "orb": FormatAdapter(format="orb", target="orb", ingest=_ingest_orb, emit=emit_orb_from_scene),
}

INGEST_FORMATS: tuple[FormatName, ...] = tuple(FORMAT_ADAPTERS)
EMIT_FORMATS: tuple[FormatName, ...] = tuple(name for name, adapter in FORMAT_ADAPTERS.items() if adapter.emit is not None)


def get_target_adapter(target: TargetName) -> TargetAdapter:
    return TARGET_ADAPTERS[target]


def get_format_adapter(format_name: FormatName) -> FormatAdapter:
    return FORMAT_ADAPTERS[format_name]


__all__ = [
    "EMIT_FORMATS",
    "FORMAT_ADAPTERS",
    "INGEST_FORMATS",
    "FormatAdapter",
    "TARGET_ADAPTERS",
    "TargetAdapter",
    "get_format_adapter",
    "get_target_adapter",
]
