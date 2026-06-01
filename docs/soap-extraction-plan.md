# SOAP Extraction Plan

## Purpose

Define the SOAP target scope that is "good enough" for the current VSS and `VssScene` models, while keeping the implementation in `vss.soap` and treating `vss.targets` as a facade only.

## Current State

Implemented today:

- `vss.soap.compile_soap_envelope(message)`
- `vss.soap.compile_soap_scene(scene)`
- bundle serialization and deserialization for:
  - `soap/manifest.json`
  - `soap/scenario.json`
  - `soap/views.json`
  - `soap/analysis.json`
  - `soap/presentation.json`
  - `soap/assets.json`
  - `soap/diagnostics.json`
  - `soap/generated/soap-example-bundle.json`

This is enough for the current VSS message model and the current `VssScene` model to round-trip through the SOAP bundle contract we have defined.

## What "Enough" Means

The repo should treat SOAP as sufficiently extracted when all of the following are true:

- The compile target has a target-owned namespace and is not implemented in `vss.targets`.
- The current VSS message and scene object families can be emitted from `vss.soap`.
- The bundle file set can be serialized and loaded back without losing the typed structure we currently claim.
- The remaining gaps are explicit, documented, and tested as gaps rather than hidden assumptions.

## In Scope

Message-level coverage:

- one `EntityUpsertMessage` becomes one SOAP envelope
- envelope output keeps the current VSS SOAP namespace and explicit payload elements

Scene-level coverage:

- `VssScene.entities[]` become SOAP platform entries
- timestamped entities become SOAP trajectory samples
- `analysis`, `presentation`, `assets`, and `views` are emitted as typed empty structures unless future scene data populates them

File contract:

- `manifest.json`
- `scenario.json`
- `views.json`
- `analysis.json`
- `presentation.json`
- `assets.json`
- `diagnostics.json`
- `generated/soap-example-bundle.json`

## Out Of Scope For Now

These are still open and should not be implied by the current code:

- full SOAP modeling for models, sensor swaths, and overlay artifacts
- reverse parsing from SOAP artifacts back into VSS/SDJ source objects
- richer `views.json` generation beyond the current typed empty structure
- deeper `analysis`, `presentation`, and `assets` mapping at scene scope
- any proprietary SOAP project format beyond the bundle contract here

## Extraction Phases

### Phase 1

- Keep all SOAP implementation code in `src/vss/soap/`.
- Keep `vss.targets` as a compatibility facade only.
- Keep round-trip tests for the current bundle contract.

### Phase 2

- Add typed SOAP object models for models, sensor swaths, overlays, and richer views.
- Map additional SDJ object families into the SOAP bundle.
- Expand diagnostics for scene elements that cannot yet be mapped natively.

### Phase 3

- Add fixture-based conformance tests for broader scene coverage.
- Add a documented adapter story for any future SOAP import/parsing path.
- Introduce stricter lossiness reporting for unsupported scene families.

## Acceptance Criteria

The SOAP extraction can be considered complete for the current repo scope when:

- `vss.soap` is the single source of truth for SOAP compile and bundle I/O.
- `vss.targets` only re-exports SOAP entrypoints.
- the current tests cover message-level and scene-level round-trips.
- the known gaps are explicitly listed here instead of being implicit code debt.

