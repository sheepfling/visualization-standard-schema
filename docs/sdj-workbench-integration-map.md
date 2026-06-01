# SDJ Workbench Integration Map

## Purpose

This repo currently defines a narrow transport envelope in `schemas/vss-message.schema.json`.
The imported workbench under `reference/sdj_workbench_v0_2/` brings in a much broader scene schema plus concrete Cesium, SIMDIS, and SOAP compile behavior.

This document turns that import into an integration plan with explicit merge boundaries.

## Current Baseline

- `schemas/vss-message.schema.json` defines a `1.0.0` `entity.upsert` envelope with one entity payload.
- `examples/cesium/air-track.json` exercises that envelope.
- `targets/simdis/README.md` and `targets/soap/README.md` are placeholders only.
- No tracked compiler or validation code exists yet.

## Imported Reference

The unpacked workbench now lives at `reference/sdj_workbench_v0_2/` and includes:

- `schemas/sdj_v0_4.schema.json`: full scene/object schema with `schemaVersion: "sdj-0.4"`.
- `src/sdj_browser_compiler.js`: normalization, semantic validation, compile planning, object inspection, and backend export logic.
- `data/sdj_backend_capabilities_v0_4.json`: backend capability matrix for Cesium, SIMDIS, and SOAP.
- `scripts/smoke-test.mjs`: reference smoke test.
- `data/sdj_exposed_scenes_manifest.json`: generated catalog of exposed SDJ corpus scenes used by the workbench gallery.
- `examples/sdj_full_coverage_scene_v0_4.json`: broad coverage fixture.

The imported smoke report claims:

- `79` objects
- `11` analysis records
- `13` presentation records
- backend outputs for Cesium, SIMDIS, and SOAP

## Workbench Commands

The workbench is wired through the repo root, with workspace passthrough scripts for the common checks:

```bash
npm run dev
npm run check
npm run smoke
npm run browser-smoke
npm run shell-smoke
npm run test
```

`browser-smoke` tries a local browser first and falls back to the shell markup check when browser launch is blocked. `shell-smoke` reads `reference/sdj_workbench_v0_2/index.html` from disk and does not require a server.

## Track 1: Schema Merge

### Gap Summary

Current VSS is message-oriented. Imported SDJ is scene-oriented.

Current VSS top-level fields:

- `schemaVersion`
- `messageType`
- `messageId`
- `timestamp`
- `source`
- `payload`

Imported SDJ top-level fields:

- `schemaVersion`
- `profiles`
- `document`
- `units`
- `clock`
- `scene`
- `assets`
- `materials`
- `layers`
- `objects`
- `views`
- `extensions`
- `backend`
- `backendCapabilities`
- `analysis`
- `presentation`

### Recommended Merge Strategy

Do not replace `vss-message.schema.json` directly.

Instead create a layered schema layout:

1. Keep the current message envelope as a transport schema.
2. Introduce a new scene schema derived from `sdj_v0_4.schema.json`.
3. Define explicit mapping from envelope payloads to scene objects.

### Proposed Target Layout

- `schemas/vss-message.schema.json`
  Keep as the transport envelope.
- `schemas/vss-scene.schema.json`
  New tracked scene schema based on `sdj_v0_4.schema.json`.
- `schemas/profiles/`
  Optional future split for backend or domain profiles if the monolithic scene schema becomes hard to maintain.

### First-Pass Schema Cuts

Phase A should bring over these stable scene concepts first:

- `document`
- `units`
- `clock`
- `scene`
- `objects`
- `views`
- `assets`
- `materials`

Phase B should add:

- `layers`
- `analysis`
- `presentation`
- `backendCapabilities`
- `extensions`

### Envelope-to-Scene Bridge

The current `entity.upsert` payload can map into an SDJ `track` or `point` object with:

- `payload.entityId` -> `objects[].id`
- `payload.name` -> `objects[].name`
- `payload.position` -> `objects[].pose.position`
- `payload.orientation` -> `objects[].pose.orientation`
- `payload.style` -> object label/material/model hints
- `payload.attributes` -> `objects[].properties`

That bridge should be documented in a separate adapter contract before any breaking schema change.

## Track 2: Target Contracts

The imported compiler already defines concrete backend bundle shapes. Those should become tracked contracts in `targets/`.

### Cesium Contract

Compiler entry point:

- `compileBackend(scene, "cesium")`

Current exported files:

- `cesium/manifest.json`
- `cesium/scene.sdj.json`
- `cesium/compile-plan.json`
- `cesium/diagnostics.json`
- `cesium/README.md`

Contract intent:

- Cesium is the primary runtime renderer.
- Bundle includes the normalized scene plus compile diagnostics.

### SIMDIS Contract

Compiler entry point:

- `compileBackend(scene, "simdis")`

Current exported files:

- `simdis/manifest.json`
- `simdis/entities.json`
- `simdis/overlays.gog`
- `simdis/analysis.json`
- `simdis/presentation.json`
- `simdis/assets.json`
- `simdis/diagnostics.json`
- `simdis/generated/simdis-example-bundle.json`

Current object families routed by compiler:

- `track` -> platform state
- `point` / `billboard` / `label` -> annotations
- sensor volumes -> sensor state
- vectors and lines -> vector state or GOG overlays

Tracked repo work needed:

- Replace placeholder `targets/simdis/README.md` with a contract document derived from the above artifact set.
- Add example output fixtures generated from a stable scene.

### SOAP Contract

Compiler entry point:

- `compileBackend(scene, "soap")`

Current exported files:

- `soap/manifest.json`
- `soap/scenario.json`
- `soap/views.json`
- `soap/analysis.json`
- `soap/presentation.json`
- `soap/assets.json`
- `soap/diagnostics.json`
- `soap/generated/soap-example-bundle.json`
- additional overlay files emitted by `buildSoapAnalysisOverlayFiles(scene)`

Current object families routed by compiler:

- `track` -> platforms and trajectories
- `model` -> models
- sensor volumes -> sensor swaths
- geometric overlays -> overlay artifacts

Tracked repo work needed:

- Replace placeholder `targets/soap/README.md` with a contract document that defines scenario, view, analysis, presentation, and overlay artifacts.
- Add fixture outputs for one small scene and one broad coverage scene.

## Track 3: Code Reuse

The imported compiler should not be copied wholesale into the repo root.
It already mixes reusable logic with browser workbench concerns.

### Reusable First

These functions are good extraction candidates:

- `normalizeSceneForWorkbench`
- `buildCompilePlan`
- `validateSemantics`
- `inspectObject`
- `compileBackend`
- `compileAllBackends`
- `compileAllBackendsToFiles`

These helper families are also useful:

- JSON coercion helpers: `asObject`, `asArray`, `asNumber`, `asString`, `cloneJson`
- object flattening and diagnostics builders
- target-specific emitters for Cesium, SIMDIS, and SOAP

### Keep Out of Core

These belong in a UI or demo package, not in the core schema package:

- `src/app.js`
- `src/styles.css`
- `index.html`
- direct Cesium browser wiring

### Proposed Code Layout

- `src/compiler/core/`
  normalization, semantic validation, compile planning
- `src/compiler/targets/cesium/`
  Cesium bundle emitter
- `src/compiler/targets/simdis/`
  SIMDIS bundle emitter
- `src/compiler/targets/soap/`
  SOAP bundle emitter
- `src/compiler/fixtures/`
  imported example scenes and expected bundle summaries

If the repo wants to stay schema-only for now, keep this code under `reference/` or `prototype/` until packaging decisions are made.

## Immediate Actions

1. The workbench has been promoted into the tracked `reference/sdj_workbench_v0_2/` subtree.
2. Add `schemas/vss-scene.schema.json` as a first tracked import from `sdj_v0_4.schema.json`.
3. Replace target placeholder READMEs with concrete artifact contracts.
4. Add a smoke-test-equivalent script once Node tooling is established in this repo.
5. Add one adapter spec for `entity.upsert` -> scene object translation.

## Risks

- Directly renaming SDJ to VSS without a compatibility story will blur whether VSS is an envelope, a scene model, or both.
- Importing the compiler before defining package boundaries will entangle browser demo code with core schema artifacts.
- Target contracts will drift unless generated fixtures are checked into the repo and diffed in CI.

## Verification Notes

The imported assets were unpacked successfully and verified locally with Node `v26.0.0`.

Confirmed checks:

- `node --check reference/sdj_workbench_v0_2/src/app.js`
- `node --check reference/sdj_workbench_v0_2/src/sdj_browser_compiler.js`
- `node reference/sdj_workbench_v0_2/scripts/smoke-test.mjs`

Confirmed smoke result:

- `ok: true`
- `semanticErrors: 0`
- `semanticWarnings: 34`
- `objectCount: 79`
- `analysisCount: 11`
- `presentationCount: 13`
- `cesiumFiles: 5`
- `simdisFiles: 8`
- `soapFiles: 19`
- `allFiles: 36`
