# SOAP Target

SOAP is a compile target, not a cross-target utilities layer.
The canonical Python implementation lives in `vss.soap`.
`vss.targets` only re-exports the target entrypoints for compatibility.

## Canonical APIs

- `vss.soap.compile_soap_envelope(message)`
  Compiles one `EntityUpsertMessage` to a SOAP XML envelope.
- `vss.soap.compile_soap_scene(scene)`
  Compiles one `VssScene` to a `SoapBundle`.
- `vss.soap.serialize_soap_bundle_files(bundle)`
  Serializes a scene bundle to its emitted file map.
- `vss.soap.write_soap_bundle(bundle, directory)`
  Writes the scene bundle artifacts to disk.
- `vss.soap.load_soap_bundle(directory)`
  Rebuilds a typed scene bundle from disk.

## Emitted Artifacts

The current scene-bundle serializer emits:

- `soap/manifest.json`
- `soap/scenario.json`
- `soap/views.json`
- `soap/analysis.json`
- `soap/presentation.json`
- `soap/assets.json`
- `soap/diagnostics.json`
- `soap/generated/soap-example-bundle.json`

## Current Mapping Scope

Message-level compilation:

- one VSS message becomes one SOAP envelope
- the envelope body uses `EntityUpsertMessage` under the VSS SOAP namespace
- payload fields are written as explicit XML elements, including optional orientation, style, and attributes

Scene-level compilation:

- each `VssScene.entities[]` item currently maps to one `scenario.platforms[]` entry
- each timestamped entity currently yields a single-sample `scenario.trajectories[]` entry
- `views.json`, `analysis.json`, `presentation.json`, and `assets.json` are currently emitted with valid empty structures unless populated by future scene features

## Current Contract Notes

- `manifest.target` is always `soap`
- scene bundles currently use mode `scene-to-scenario+scene-to-analysis+scene-to-presentation`
- `diagnostics.json` wraps diagnostics as `{ "diagnostics": [...] }`
- `soap/generated/soap-example-bundle.json` is a convenience bundle artifact for inspection and tests
- entities without timestamps are still exported as platforms, but their trajectory samples are omitted and a warning diagnostic is emitted

## Known Gaps

- there is not yet a richer split into models, sensor swaths, overlays, or overlay sidecar files at scene scope
- `views.json`, `analysis.json`, `presentation.json`, and `assets.json` are placeholders today
- current scene compilation is intentionally minimal and should be extended within `vss.soap`, not in `vss.targets`
