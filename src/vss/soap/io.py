from __future__ import annotations

import json
from pathlib import Path

from ..util import dumps_json, write_text_file
from .models import (
    SoapAnalysis,
    SoapAssets,
    SoapBundle,
    SoapDiagnostic,
    SoapManifest,
    SoapPresentation,
    SoapScenario,
    SoapViews,
)

SOAP_MANIFEST_PATH = "soap/manifest.json"
SOAP_SCENARIO_PATH = "soap/scenario.json"
SOAP_VIEWS_PATH = "soap/views.json"
SOAP_ANALYSIS_PATH = "soap/analysis.json"
SOAP_PRESENTATION_PATH = "soap/presentation.json"
SOAP_ASSETS_PATH = "soap/assets.json"
SOAP_DIAGNOSTICS_PATH = "soap/diagnostics.json"
SOAP_GENERATED_BUNDLE_PATH = "soap/generated/soap-example-bundle.json"


def dump_soap_bundle_json(bundle: SoapBundle, *, indent: int = 2) -> str:
    return dumps_json(bundle.model_dump(mode="json", exclude_none=True), indent=indent)


def parse_soap_bundle_json(raw_json: str) -> SoapBundle:
    return SoapBundle.model_validate_json(raw_json)


def serialize_soap_bundle_files(bundle: SoapBundle, *, indent: int = 2) -> dict[str, str]:
    diagnostics_document = {"diagnostics": [item.model_dump(mode="json") for item in bundle.diagnostics]}
    return {
        SOAP_MANIFEST_PATH: dumps_json(bundle.manifest.model_dump(mode="json", exclude_none=True), indent=indent),
        SOAP_SCENARIO_PATH: dumps_json(bundle.scenario.model_dump(mode="json", exclude_none=True), indent=indent),
        SOAP_VIEWS_PATH: dumps_json(bundle.views.model_dump(mode="json", exclude_none=True), indent=indent),
        SOAP_ANALYSIS_PATH: dumps_json(bundle.analysis.model_dump(mode="json", exclude_none=True), indent=indent),
        SOAP_PRESENTATION_PATH: dumps_json(bundle.presentation.model_dump(mode="json", exclude_none=True), indent=indent),
        SOAP_ASSETS_PATH: dumps_json(bundle.assets.model_dump(mode="json", exclude_none=True), indent=indent),
        SOAP_DIAGNOSTICS_PATH: dumps_json(diagnostics_document, indent=indent),
        SOAP_GENERATED_BUNDLE_PATH: dump_soap_bundle_json(bundle, indent=indent),
    }


def write_soap_bundle(bundle: SoapBundle, directory: str | Path, *, indent: int = 2) -> dict[str, Path]:
    root = Path(directory)
    written: dict[str, Path] = {}
    for relative_path, contents in serialize_soap_bundle_files(bundle, indent=indent).items():
        destination = write_text_file(root / relative_path, contents, encoding="utf-8", trailing_newline=False)
        written[relative_path] = destination
    return written


def load_soap_bundle_files(files: dict[str, str]) -> SoapBundle:
    manifest = SoapManifest.model_validate_json(files[SOAP_MANIFEST_PATH])
    scenario = SoapScenario.model_validate_json(files[SOAP_SCENARIO_PATH])
    views = SoapViews.model_validate_json(files.get(SOAP_VIEWS_PATH, '{"views": [], "palettes": []}'))
    analysis = SoapAnalysis.model_validate_json(files.get(SOAP_ANALYSIS_PATH, '{"results": []}'))
    presentation = SoapPresentation.model_validate_json(files.get(SOAP_PRESENTATION_PATH, '{"slides": [], "actions": []}'))
    assets = SoapAssets.model_validate_json(files.get(SOAP_ASSETS_PATH, '{"assets": []}'))
    diagnostics_payload = json.loads(files.get(SOAP_DIAGNOSTICS_PATH, '{"diagnostics": []}'))
    diagnostics = [SoapDiagnostic.model_validate(item) for item in diagnostics_payload.get("diagnostics", [])]
    return SoapBundle(
        source=manifest.source,
        manifest=manifest,
        scenario=scenario,
        views=views,
        analysis=analysis,
        presentation=presentation,
        assets=assets,
        diagnostics=diagnostics,
    )


def load_soap_bundle(directory: str | Path) -> SoapBundle:
    root = Path(directory)
    files = {
        SOAP_MANIFEST_PATH: (root / SOAP_MANIFEST_PATH).read_text(encoding="utf-8"),
        SOAP_SCENARIO_PATH: (root / SOAP_SCENARIO_PATH).read_text(encoding="utf-8"),
    }
    for optional_path in [
        SOAP_VIEWS_PATH,
        SOAP_ANALYSIS_PATH,
        SOAP_PRESENTATION_PATH,
        SOAP_ASSETS_PATH,
        SOAP_DIAGNOSTICS_PATH,
    ]:
        candidate = root / optional_path
        if candidate.exists():
            files[optional_path] = candidate.read_text(encoding="utf-8")
    return load_soap_bundle_files(files)
