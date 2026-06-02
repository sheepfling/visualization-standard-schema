# JS Library Modularization

This repository now has an extracted typed core library package under
`reference/sdj_core_v0_1/` and a thin workbench compatibility layer under
`reference/sdj_core_v0_1/`.

## Current Boundaries

- `reference/sdj_core_v0_1/src/lib/json.ts`: JSON coercion and formatting helpers.
- `reference/sdj_core_v0_1/src/lib/scene.ts`: scene normalization, flattening, semantic validation, and object lookup.
- `reference/sdj_core_v0_1/src/lib/plan.ts`: compile planning, target support scoring, artifact-path mapping, and inspection helpers.
- `reference/sdj_core_v0_1/src/lib/zip.ts`: ZIP blob creation for browser exports.
- `reference/sdj_core_v0_1/src/lib/index.ts`: barrel export for downstream imports.
- `reference/sdj_core_v0_1/src/lib/cesium_adapter.ts`: explicit loader/render boundary for Cesium hosts that want to reuse the SDJ rendering adapter without the full workbench shell.

## Why This Exists

The workbench app still loads from `src/app.js`, but the shell wiring now lives in `src/workbench/bootstrap.ts` and the reusable compiler logic is separated into the `sdj-core` package. That makes the next step straightforward:

- replace the monolithic browser compiler file with imports from `sdj-core`
- move Cesium/SIMDIS/SOAP adapter logic into target-owned modules
- layer TypeScript on top of the stable module seams

For the concrete refactor sequence and done criteria, see [docs/workbench-js-ts-refactor-plan.md](docs/workbench-js-ts-refactor-plan.md).

The first TypeScript boundary for the workbench now lives in `reference/sdj_workbench_v0_2/tsconfig.json` with shared types under `reference/sdj_workbench_v0_2/src/types/`.

## Migration Rule

Keep browser UI code out of the library layer, and keep target-specific renderer logic out of the scene/validation core.
