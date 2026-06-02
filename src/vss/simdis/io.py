from __future__ import annotations

import json
from pathlib import Path

from ..util import dumps_json, write_text_file
from .models import (
    SimdisAnalysis,
    SimdisAssets,
    SimdisBundle,
    SimdisDiagnostic,
    SimdisEntities,
    SimdisManifest,
    SimdisPresentation,
)

SIMDIS_MANIFEST_PATH = "simdis/manifest.json"
SIMDIS_ENTITIES_PATH = "simdis/entities.json"
SIMDIS_ENTITIES_NORMALIZED_PATH = "simdis/entities.normalized.json"
SIMDIS_SCENARIO_PATH = "simdis/scenario.asi"
SIMDIS_OVERLAYS_PATH = "simdis/overlays.gog"
SIMDIS_OVERLAYS_NORMALIZED_PATH = "simdis/overlays.normalized.json"
SIMDIS_ANALYSIS_PATH = "simdis/analysis.json"
SIMDIS_PRESENTATION_PATH = "simdis/presentation.json"
SIMDIS_ASSETS_PATH = "simdis/assets.json"
SIMDIS_DIAGNOSTICS_PATH = "simdis/diagnostics.json"
SIMDIS_CUSTOM_OBJECTS_PATH = "simdis/custom-objects.json"
SIMDIS_RUNTIME_OBJECTS_PATH = "simdis/runtime-objects.json"
SIMDIS_GENERATED_BUNDLE_PATH = "simdis/generated/simdis-example-bundle.json"


def dump_simdis_bundle_json(bundle: SimdisBundle, *, indent: int = 2) -> str:
    return dumps_json(bundle.model_dump(mode="json", exclude_none=True), indent=indent)


def parse_simdis_bundle_json(raw_json: str) -> SimdisBundle:
    return SimdisBundle.model_validate_json(raw_json)


def serialize_simdis_bundle_files(bundle: SimdisBundle, *, indent: int = 2) -> dict[str, str]:
    diagnostics_document = {"diagnostics": [item.model_dump(mode="json") for item in bundle.diagnostics]}
    entities_document = bundle.entities.model_dump(mode="json", exclude_none=True)
    overlays_document = {
        "overlays": [overlay.model_dump(mode="json", exclude_none=True) for overlay in bundle.entities.overlays]
    }
    return {
        SIMDIS_MANIFEST_PATH: dumps_json(bundle.manifest.model_dump(mode="json", exclude_none=True), indent=indent),
        SIMDIS_ENTITIES_PATH: dumps_json(entities_document, indent=indent),
        SIMDIS_ENTITIES_NORMALIZED_PATH: dumps_json(entities_document, indent=indent),
        SIMDIS_SCENARIO_PATH: bundle.scenarioAsi if bundle.scenarioAsi.endswith("\n") else f"{bundle.scenarioAsi}\n",
        SIMDIS_OVERLAYS_PATH: bundle.overlaysGog if bundle.overlaysGog.endswith("\n") else f"{bundle.overlaysGog}\n",
        SIMDIS_OVERLAYS_NORMALIZED_PATH: dumps_json(overlays_document, indent=indent),
        SIMDIS_ANALYSIS_PATH: dumps_json(bundle.analysis.model_dump(mode="json", exclude_none=True), indent=indent),
        SIMDIS_PRESENTATION_PATH: dumps_json(bundle.presentation.model_dump(mode="json", exclude_none=True), indent=indent),
        SIMDIS_ASSETS_PATH: dumps_json(bundle.assets.model_dump(mode="json", exclude_none=True), indent=indent),
        SIMDIS_DIAGNOSTICS_PATH: dumps_json(diagnostics_document, indent=indent),
        SIMDIS_CUSTOM_OBJECTS_PATH: dumps_json({"customObjects": bundle.customObjects}, indent=indent),
        SIMDIS_RUNTIME_OBJECTS_PATH: dumps_json({"runtimeObjects": bundle.runtimeObjects}, indent=indent),
        SIMDIS_GENERATED_BUNDLE_PATH: dump_simdis_bundle_json(bundle, indent=indent),
    }


def write_simdis_bundle(bundle: SimdisBundle, directory: str | Path, *, indent: int = 2) -> dict[str, Path]:
    root = Path(directory)
    written: dict[str, Path] = {}
    for relative_path, contents in serialize_simdis_bundle_files(bundle, indent=indent).items():
        destination = write_text_file(root / relative_path, contents, encoding="utf-8", trailing_newline=False)
        written[relative_path] = destination
    return written


def load_simdis_bundle_files(files: dict[str, str]) -> SimdisBundle:
    manifest = SimdisManifest.model_validate_json(files[SIMDIS_MANIFEST_PATH])
    entities_json = files.get(SIMDIS_ENTITIES_PATH) or files[SIMDIS_ENTITIES_NORMALIZED_PATH]
    entities = SimdisEntities.model_validate_json(entities_json)
    scenario_asi = files.get(SIMDIS_SCENARIO_PATH, "")
    overlays_gog = files[SIMDIS_OVERLAYS_PATH]
    analysis = SimdisAnalysis.model_validate_json(files.get(SIMDIS_ANALYSIS_PATH, '{"results": []}'))
    presentation = SimdisPresentation.model_validate_json(
        files.get(SIMDIS_PRESENTATION_PATH, '{"views": [], "slides": [], "cameraActions": [], "popups": []}')
    )
    assets = SimdisAssets.model_validate_json(files.get(SIMDIS_ASSETS_PATH, '{"assets": []}'))
    diagnostics_payload = json.loads(files.get(SIMDIS_DIAGNOSTICS_PATH, '{"diagnostics": []}'))
    diagnostics = [SimdisDiagnostic.model_validate(item) for item in diagnostics_payload.get("diagnostics", [])]
    custom_objects_payload = json.loads(files.get(SIMDIS_CUSTOM_OBJECTS_PATH, '{"customObjects": []}'))
    runtime_objects_payload = json.loads(files.get(SIMDIS_RUNTIME_OBJECTS_PATH, '{"runtimeObjects": []}'))
    return SimdisBundle(
        source=manifest.source,
        manifest=manifest,
        scenarioAsi=scenario_asi,
        entities=entities,
        overlaysGog=overlays_gog,
        analysis=analysis,
        presentation=presentation,
        assets=assets,
        diagnostics=diagnostics,
        customObjects=list(custom_objects_payload.get("customObjects", [])),
        runtimeObjects=list(runtime_objects_payload.get("runtimeObjects", [])),
    )


def load_simdis_bundle(directory: str | Path) -> SimdisBundle:
    root = Path(directory)
    files = {
        SIMDIS_MANIFEST_PATH: (root / SIMDIS_MANIFEST_PATH).read_text(encoding="utf-8"),
        SIMDIS_ENTITIES_PATH: (root / SIMDIS_ENTITIES_PATH).read_text(encoding="utf-8"),
        SIMDIS_OVERLAYS_PATH: (root / SIMDIS_OVERLAYS_PATH).read_text(encoding="utf-8"),
    }
    for optional_path in [
        SIMDIS_SCENARIO_PATH,
        SIMDIS_ANALYSIS_PATH,
        SIMDIS_PRESENTATION_PATH,
        SIMDIS_ASSETS_PATH,
        SIMDIS_DIAGNOSTICS_PATH,
        SIMDIS_CUSTOM_OBJECTS_PATH,
        SIMDIS_RUNTIME_OBJECTS_PATH,
    ]:
        candidate = root / optional_path
        if candidate.exists():
            files[optional_path] = candidate.read_text(encoding="utf-8")
    return load_simdis_bundle_files(files)
