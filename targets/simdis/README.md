# SIMDIS Target

SIMDIS is a compile target, not a shared adapter bucket.
The canonical Python implementation lives in `vss.simdis`.
`vss.targets` only re-exports the target entrypoints for compatibility.

## Canonical APIs

- `vss.simdis.compile_simdis_lines(message)`
  Compiles one `EntityUpsertMessage` to line-oriented SIMDIS text.
- `vss.simdis.compile_simdis_bundle(message)`
  Compiles one `EntityUpsertMessage` to a `SimdisBundle`.
- `vss.simdis.compile_simdis_scene(scene)`
  Compiles one `VssScene` to a `SimdisBundle`.
- `vss.simdis.serialize_simdis_bundle_files(bundle)`
  Serializes a bundle to its emitted file map.
- `vss.simdis.write_simdis_bundle(bundle, directory)`
  Writes the emitted file set to disk.
- `vss.simdis.load_simdis_bundle(directory)`
  Rebuilds a typed bundle from a written directory.

## Emitted Artifacts

The current bundle serializer emits:

- `simdis/manifest.json`
- `simdis/entities.json`
- `simdis/overlays.gog`
- `simdis/analysis.json`
- `simdis/presentation.json`
- `simdis/assets.json`
- `simdis/diagnostics.json`
- `simdis/generated/simdis-example-bundle.json`

## Current Mapping Scope

Message-level compilation:

- one VSS entity becomes one SIMDIS platform record
- line output includes `PLATFORM`, `PLATFORM_UPDATE`, and optional `PLATFORM_LABEL`
- bundle output stores the same entity as `entities.platforms[0]`

Scene-level compilation:

- each `VssScene.entities[]` item currently maps to one `entities.platforms[]` entry
- `overlays.gog` is currently generated as platform-oriented line output
- `analysis.json`, `presentation.json`, and `assets.json` are emitted with valid empty structures unless populated by future scene features

## Current Contract Notes

- `manifest.target` is always `simdis`
- message bundles currently use mode `entity.upsert-to-simdis-platform`
- scene bundles currently use mode `scene-to-gog+scene-to-entities+scene-to-presentation`
- `diagnostics.json` wraps diagnostics as `{ "diagnostics": [...] }`
- the generated bundle JSON is a convenience artifact for inspection and tests, not a separate compile target

## Known Gaps

- scene entities are all routed through the platform path today; there is not yet a separate native scene mapping for annotations, sensors, or vectors
- `analysis.json`, `presentation.json`, and `assets.json` are placeholders at scene scope
- `overlays.gog` currently reflects line-oriented platform export rather than broader GOG scene geometry
