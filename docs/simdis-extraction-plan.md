# SIMDIS Extraction Plan

## Purpose

Define the smallest SIMDIS surface that is "SDJ compatible enough" for this repo, while keeping target-specific implementation in `vss.simdis` and leaving `vss.targets` as a facade.

## Current State

Implemented today:

- `vss.simdis.compile_simdis_lines(message)`
- `vss.simdis.compile_simdis_asi(message)`
- `vss.simdis.compile_simdis_bundle(message)`
- `vss.simdis.compile_simdis_scene(scene)`
- scene-level partitioning for platform, sensor, and vector bundle families
- typed beam, gate, and projector state extraction from `attributes.simdis`
- label or billboard-only entities without a model URI are emitted as annotations
- annotation bundles are reflected in `overlays.gog` as annotation records
- the bundle file set now includes `simdis/scenario.asi`
- bundle serialization and deserialization for:
  - `simdis/manifest.json`
  - `simdis/entities.json`
  - `simdis/scenario.asi`
  - `simdis/overlays.gog`
  - `simdis/analysis.json`
  - `simdis/presentation.json`
  - `simdis/assets.json`
  - `simdis/diagnostics.json`
  - `simdis/generated/simdis-example-bundle.json`

This is enough for the current VSS message model and the current `VssScene` model to round-trip through the SIMDIS bundle contract we have defined.

## What "Enough" Means

The repo should treat SIMDIS as sufficiently extracted when all of the following are true:

- The compile target has a target-owned namespace and is not implemented in `vss.targets`.
- The current SDJ-compatible object families can be emitted from `VssScene`.
- The bundle file set can be serialized and loaded back without losing the typed structure we currently claim.
- The remaining gaps are explicit, documented, and tested as gaps rather than hidden assumptions.

## In Scope

Message-level coverage:

- one `EntityUpsertMessage` becomes one SIMDIS platform bundle entry
- platform text output remains available for compatibility and smoke tests

Scene-level coverage:

- `VssScene.entities[]` become platform or sensor bundle entries depending on category
- label or billboard-only entities without a model URI become annotation bundle entries
- `VssScene.overlays[]` become vector bundle entries and GOG overlay text
- `attributes.simdis` can seed beam, gate, and projector bundle state
- `overlays.gog` is emitted for current platform, annotation, and overlay line coverage
- `scenario.asi` is emitted for the current platform and hosted-command coverage, excluding annotation-only objects
- `analysis`, `presentation`, and `assets` are emitted as typed empty structures unless future scene data populates them

File contract:

- `manifest.json`
- `entities.json`
- `scenario.asi`
- `overlays.gog`
- `analysis.json`
- `presentation.json`
- `assets.json`
- `diagnostics.json`
- `generated/simdis-example-bundle.json`

## Out Of Scope For Now

These are still open and should not be implied by the current code:

- richer annotation styling and native geometry generation
- richer native sensor and vector geometry generation
- reverse parsing from SIMDIS artifacts back into VSS/SDJ source objects
- full-fidelity `analysis`, `presentation`, and `assets` mapping at scene scope
- proprietary SIMDIS project file generation

## Extraction Phases

### Phase 1

- Keep all SIMDIS implementation code in `src/vss/simdis/`.
- Keep `vss.targets` as a compatibility facade only.
- Keep round-trip tests for the current bundle contract.

### Phase 2

- Add richer SIMDIS annotation styling and geometry semantics.
- Add richer sensor/vector semantics beyond the current ASI-lite and bundle-state extraction.
- Map additional SDJ object families into the SIMDIS bundle.
- Expand the overlay emitter beyond line-oriented polylines where we have stable rules.

### Phase 3

- Add richer diagnostics for unsupported or lossy SIMDIS mappings.
- Introduce fixture-based conformance tests for scene coverage beyond the current air-track examples.
- Add a documented adapter story for any future SIMDIS import/parsing path.

## Acceptance Criteria

The SIMDIS extraction can be considered complete for the current repo scope when:

- `vss.simdis` is the single source of truth for SIMDIS compile and bundle I/O.
- `vss.targets` only re-exports SIMDIS entrypoints.
- the current tests cover message-level and scene-level round-trips.
- the known gaps are explicitly listed here instead of being implicit code debt.
