# JS Library Modularization

This repository now has an extracted JavaScript library layer under
`reference/sdj_workbench_v0_2/src/lib/`.

## Current Boundaries

- `json.js`: JSON coercion and formatting helpers.
- `scene.js`: scene normalization, flattening, semantic validation, and object lookup.
- `plan.js`: compile planning, target support scoring, artifact-path mapping, and inspection helpers.
- `zip.js`: ZIP blob creation for browser exports.
- `index.js`: barrel export for downstream imports.

## Why This Exists

The workbench app still lives in `src/app.js`, but the reusable compiler logic is now separated from the DOM/viewer shell. That makes the next step straightforward:

- replace the monolithic browser compiler file with imports from `src/lib/`
- move Cesium/SIMDIS/SOAP adapter logic into target-owned modules
- layer TypeScript on top of the stable module seams

## Migration Rule

Keep browser UI code out of the library layer, and keep target-specific renderer logic out of the scene/validation core.
