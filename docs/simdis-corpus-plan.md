# SIMDIS Corpus Plan

## Purpose

This is the canonical SIMDIS planning doc. It merges the extraction boundary with the corpus-driven implementation path so there is one source of truth for what SIMDIS supports today, what the corpus proves, and what the next implementation steps should target.

## Current Corpus Status

The corpus package at `INBOX/simdis_corpus_v0_1.zip` is organized by confidence level:

- `public_seed/asi/` contains synthetic-but-source-backed ASI seed examples
- `public_seed/gog/` contains synthetic-but-source-backed GOG seed examples
- `inferred/discn/` contains a candidate `.discn` example that still needs native validation
- `needs_official_samples/fct/` and `needs_official_samples/svml/` are explicit placeholders, not generated samples
- `scripts/collect_simdis_samples.py` is the collector for installed SIMDIS trees
- `scripts/validate_asi_lite.py` is the ASI-lite validator for seed coverage

Current file counts in the zip:

- 3 `.asi` seed files
- 4 `.gog` seed files
- 1 `.discn` candidate file
- 0 `.fct` native samples
- 0 `.svml` native samples

## Current Extraction Boundary

The current SIMDIS boundary lives in `src/vss/simdis/`, with `vss.targets` kept as a compatibility facade only.

Implemented today:

- `vss.simdis.compile_simdis_lines(message)`
- `vss.simdis.compile_simdis_asi(message)`
- `vss.simdis.compile_simdis_bundle(message)`
- `vss.simdis.compile_simdis_scene(scene)`
- typed bundle serialization and deserialization for:
  - `simdis/manifest.json`
  - `simdis/entities.json`
  - `simdis/scenario.asi`
  - `simdis/overlays.gog`
  - `simdis/analysis.json`
  - `simdis/presentation.json`
  - `simdis/assets.json`
  - `simdis/diagnostics.json`
  - `simdis/generated/simdis-example-bundle.json`
- scene-level partitioning for platform, sensor, vector, and annotation families
- typed beam, gate, and projector state extraction from `attributes.simdis`
- label or billboard-only entities without a model URI are emitted as annotations
- annotation bundles are reflected in `overlays.gog` as annotation records
- ASI-lite parsing and export for the current corpus subset
- GOG-lite parsing and rendering for the current corpus subset

Current bundle and round-trip state:

- the current VSS message model and current `VssScene` model can round-trip through the SIMDIS bundle contract defined in this repo
- the bundle output keeps typed structure instead of collapsing SIMDIS or SOAP into generic overlay dictionaries
- `vss.targets` only re-exports SIMDIS entrypoints for compatibility

Out of scope for now:

- richer annotation styling and native geometry generation
- richer native sensor and vector geometry generation
- reverse parsing from SIMDIS artifacts back into VSS/SDJ source objects
- full-fidelity `analysis`, `presentation`, and `assets` mapping at scene scope
- proprietary SIMDIS project file generation

## What We Already Cover

The repo already has:

- target-owned SIMDIS code under `vss.simdis`
- a SIMDIS bundle format with typed entities, overlays, diagnostics, and `scenario.asi`
- ASI-lite parsing and export for the current seed corpus
- GOG-lite parsing and rendering for the current seed corpus
- corpus tests that parse and round-trip the packaged samples

## What This Plan Is Driving Toward

The corpus is the concrete execution driver. The SIMDIS backend should emit a native-ish package instead of only normalized JSON:

- `generated/simdis/manifest.json`
- `generated/simdis/scenario.asi`
- `generated/simdis/overlays.gog`
- `generated/simdis/entities.normalized.json`
- `generated/simdis/overlays.normalized.json`
- `generated/simdis/diagnostics.json`

The key split is:

- tracks, platforms, sensors, beams, gates, and projectors go to `scenario.asi`
- static overlays, annotations, and authored geometry go to `overlays.gog`
- the normalized JSON mirrors remain useful for inspection and tests, but are not the primary export contract

## Immediate Implementation Order

### 1. Keep typed exported overlay models

Do not let SIMDIS or SOAP regress back to generic overlay dictionaries. The exported bundle models should remain typed:

- `geometryType`
- `polyline`
- `polygon`
- `style`
- stable position models, not ad hoc dicts

This keeps the scene model typed all the way through the exporters.

### 2. Make SIMDIS export produce native-ish files

The SIMDIS backend should produce `scenario.asi` and `overlays.gog` as first-class outputs, not just JSON mirrors.

Minimum ASI coverage:

- `ReferenceYear`
- `DegreeAngles`
- `PlatformID`
- `PlatformName`
- `PlatformIcon`
- `PlatformData`
- `BeamID`
- `BeamType`
- `HorzBW`
- `VertBW`
- `BeamOnOffCmd`
- `BeamColorCmd`
- `BeamDataRAE`
- `BeamTargetIDCmd`
- `GateID`
- `GateType`
- `GateOnOffCmd`
- `GateColorCmd`
- `GateDataRAE`
- `Projector`
- `ProjectorRasterFile`
- `ProjectorOn`
- `ProjectorFOV`

Minimum GOG coverage:

- `annotation`
- `points`
- `line`
- `linesegs`
- `polygon`
- `circle`
- `ellipse`
- `arc`
- `sphere`
- `hemisphere`
- `ellipsoid`
- `cylinder`
- `cone`
- `latlonaltbox`
- `imageoverlay`

### 3. Wire the corpus into tests

Add the corpus under tracked fixtures, for example:

- `tests/fixtures/simdis/public_seed/asi/`
- `tests/fixtures/simdis/public_seed/gog/`
- `tests/fixtures/simdis/inferred/discn/`
- `tests/fixtures/simdis/official/README.md`

The tests should be able to run locally without a SIMDIS install.

Planned fixture tests:

- `test_asi_lite_seed_files_parse`
- `test_vss_track_exports_platform_data_asi`
- `test_vss_sensor_exports_beam_gate_asi`
- `test_vss_polyline_exports_gog_line`
- `test_vss_polygon_exports_gog_polygon`
- `test_vss_circle_exports_gog_circle`
- `test_vss_hemisphere_exports_gog_hemisphere`

Later, add optional native integration tests behind `pytest -m simdis_native`.

### 4. Add the import / round-trip lane

Keep the parser surface narrow and semantic:

- ASI-lite parser: `.asi -> normalized scene`
- GOG-lite parser: `.gog -> normalized overlays`

Round-trip tests should compare meaning, not bytes.

For example:

- parse seed `.asi`
- export `.asi`
- parse the export again
- compare stable semantic fields such as platform ids, sample counts, and hosted command coverage

### 5. Treat `.fct`, `.discn`, and `.svml` differently

Do not fake unsupported formats.

- `.discn` stays an inferred candidate until validated against native SIMDIS
- `.fct` stays binary/native and should be collected from official samples only
- `.svml` stays native view/session/presentation data and should be collected from official samples only
- there should be no fake writers for formats we have not validated

### 6. Run the collector against an installed SIMDIS tree

When SIMDIS is installed locally, run:

```bash
python3 scripts/collect_simdis_samples.py \
  --root "$SIMDIS_DIR" \
  --root "$SIMDIS_USER_DIR" \
  --include-env \
  --out collected
```

The important output is a real scenario package that includes multiple files together, such as:

- `scenario.asi`
- `overlays.gog`
- `views.svml`
- `bookmarks.bml`
- `preferences.prefs`
- terrain and asset sidecars

### 7. Update the frontend export button later

Once the backend emits native-ish files, the export bundle should include:

- `manifest.json`
- `scenario.asi`
- `overlays.gog`
- `diagnostics.json`
- normalized JSON mirrors under `normalized/`

The UI should explain the mapping for each object family across Cesium, SIMDIS, and SOAP.

## Recommended Commit Sequence

### Commit 1

`feat(simdis): emit scenario.asi and overlays.gog from typed VSS scene`

Scope:

- typed exported overlay models
- ASI writer for platforms and tracks
- GOG writer for polylines, polygons, circles, and labels
- fixtures from `simdis_corpus_v0_1`
- tests for generated `.asi` and `.gog`

### Commit 2

`feat(simdis): export sensor beams, gates, and projectors to ASI-lite`

Scope:

- beam export
- gate export
- projector export
- corpus tests for hosted command coverage

## Acceptance Criteria

This plan is complete for the current repo scope when:

- the SIMDIS backend emits typed native-ish outputs for the supported corpus
- the corpus fixtures are tracked and tested locally
- `.asi` and `.gog` round-trip at the semantic level for the supported subset
- `.discn`, `.fct`, and `.svml` are tracked honestly with explicit status and no fake writers
- future SIMDIS work lands in `vss.simdis`, not `vss.targets`
