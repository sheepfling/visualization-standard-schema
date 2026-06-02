# Workbench JS/TS Refactor Plan

## Goal

Turn the SDJ workbench into a small browser shell on top of a reusable library surface, then layer TypeScript onto the stable seams without changing behavior.

## Current Shape

- `reference/sdj_core_v0_1/src/lib/` contains the reusable, mostly pure compiler layer.
- `reference/sdj_core_v0_1/src/lib/cesium_adapter.ts` contains the explicit Cesium loader/render boundary used by the workbench and other Cesium hosts.
- `reference/sdj_workbench_v0_2/src/workbench/` contains browser orchestration for scene loading, viewer control, panels, and bootstrap wiring.
- `reference/sdj_workbench_v0_2/src/app.js` is now a thin loader that delegates to `reference/sdj_workbench_v0_2/src/workbench/bootstrap.ts`.
- `reference/sdj_workbench_v0_2/src/types/sdj.d.ts` contains the workbench-specific DOM and shell shape types; the core scene/compile types now live in `reference/sdj_core_v0_1/src/lib/`.
- `reference/sdj_workbench_v0_2/src/types/runtime.d.ts` contains the browser dependency injection boundary.
- `reference/sdj_workbench_v0_2/tsconfig.json` is the current TypeScript scaffold for the workbench package.
- `reference/sdj_workbench_v0_2/generated-smoke/browser/` is the browser smoke artifact directory when Chromium can launch.

## Current Verified State

The active browser/library split is already on disk and testable:

- library modules: `reference/sdj_core_v0_1/src/lib/json.ts`, `reference/sdj_core_v0_1/src/lib/scene.ts`, `reference/sdj_core_v0_1/src/lib/plan.ts`, `reference/sdj_core_v0_1/src/lib/compile.ts`, `reference/sdj_core_v0_1/src/lib/zip.ts`, `reference/sdj_core_v0_1/src/lib/index.ts`
- Cesium adapter module: `reference/sdj_core_v0_1/src/lib/cesium_adapter.ts`
- workbench modules: `src/workbench/helpers.ts`, `src/workbench/scene.ts`, `src/workbench/viewer.ts`, `src/workbench/panels.ts`, `src/workbench/smoke.ts`, `src/workbench/bootstrap.ts`
- workbench bootstrap: `src/workbench/bootstrap.ts`
- shared declarations: `src/types/sdj.d.ts`, `src/types/runtime.d.ts`
- TS scaffold: `reference/sdj_workbench_v0_2/tsconfig.json` with `noEmit: true`
- browser smoke evidence: `generated-smoke/browser/browser-smoke-report.json` plus PNG captures when the browser path succeeds
- smoke summary hook: `globalThis.__sdjWorkbenchSmoke.getRenderSummary()`

The first executed TypeScript seams now live under `reference/sdj_core_v0_1/src/lib/json.ts`, `reference/sdj_core_v0_1/src/lib/scene.ts`, `reference/sdj_core_v0_1/src/lib/zip.ts`, and `reference/sdj_core_v0_1/src/lib/plan.ts`, with the workbench shell now on `src/workbench/bootstrap.ts` and `src/app.js` reduced to a thin loader. The workbench package scripts now use Node strip-types mode for the checks that load the typed source graph.

That means the refactor plan is no longer hypothetical; the remaining work is converting the current JS seams into stable typed seams without regressing behavior.

## Existing Regression Coverage

The current package already has concrete tests that should continue to pass throughout the migration:

- `tests/library-modules.test.mjs`: compares the extracted library surface against the legacy compiler wrapper for normalization, planning, and ZIP generation.
- `tests/workbench.test.mjs`: exercises the legacy compiler surface, compile output, and `index.html` wiring.
- `tests/browser-smoke.test.mjs`: validates the browser smoke-support helpers and the required shell markup.
- `tests/exposed-scenes.test.mjs`: checks the tracked exposed-scene corpus manifest.

The package scripts that matter for the plan are:

- `npm --workspace reference/sdj_workbench_v0_2 test`
- `npm --workspace reference/sdj_workbench_v0_2 run check`
- `npm --workspace reference/sdj_workbench_v0_2 run build:exposed-scenes`
- `npm --workspace reference/sdj_workbench_v0_2 run smoke`
- `npm --workspace reference/sdj_workbench_v0_2 run shell-smoke`
- `npm --workspace reference/sdj_workbench_v0_2 run browser-smoke`

## Implementation Snapshot

The workbench is already split into these active modules:

- `reference/sdj_core_v0_1/src/lib/json.ts`
- `reference/sdj_core_v0_1/src/lib/scene.ts`
- `reference/sdj_core_v0_1/src/lib/plan.ts`
- `reference/sdj_core_v0_1/src/lib/compile.ts`
- `reference/sdj_core_v0_1/src/lib/zip.ts`
- `reference/sdj_core_v0_1/src/index.ts`
- `src/workbench/helpers.ts`
- `src/workbench/scene.ts`
- `src/workbench/viewer.ts`
- `src/workbench/panels.ts`
- `src/workbench/smoke.ts`
- `src/workbench/bootstrap.ts`

The shared type declarations already cover:

- `JsonValue` and `JsonObject`
- `Diagnostic`
- `TargetPlan`, `ObjectPlan`, and `CompilePlan`
- `BackendBundle`
- `WorkbenchState` and `WorkbenchElements`
- `AppDeps` for the browser shell dependency injection boundary

## Target Module Boundaries

- `reference/sdj_core_v0_1/src/lib/json.*`: JSON coercion, cloning, and formatting helpers.
- `reference/sdj_core_v0_1/src/lib/scene.*`: scene normalization, flattening, validation, and object lookup.
- `reference/sdj_core_v0_1/src/lib/plan.*`: compile plans, target support scoring, artifact mapping, and inspection planning.
- `reference/sdj_core_v0_1/src/lib/compile.*`: Cesium, SIMDIS, SOAP bundle generation and ZIP file map assembly.
- `reference/sdj_core_v0_1/src/lib/zip.*`: ZIP blob creation.
- `reference/sdj_core_v0_1/src/lib/cesium_adapter.*`: Cesium loader resolution, compile-plan access, semantic validation, and viewer-backed scene loading.
- `src/workbench/helpers.*`: DOM/runtime helpers and browser glue.
- `src/workbench/bootstrap.*`: app initialization, event wiring, and cross-module orchestration.
- `src/workbench/scene.*`: scene loading, catalog handling, import/export, and editor normalization.
- `src/workbench/viewer.*`: Cesium viewer setup, selection, zoom, and pick handling.
- `src/workbench/panels.*`: diagnostics, totals, object table, inspector, and object-report actions.
- `src/app.*`: thin orchestration only.

## Recommended First Pass

If the next implementation step starts from the current JS tree, keep the order narrow and reversible:

1. Keep `reference/sdj_core_v0_1/src/lib/json.ts` and `reference/sdj_core_v0_1/src/lib/scene.ts` stable as the lowest-risk pure helpers.
2. Keep `reference/sdj_core_v0_1/src/lib/plan.ts` stable, since it defines the compile-plan contract consumed by the rest of the tree.
3. Keep `reference/sdj_core_v0_1/src/lib/compile.ts` and `reference/sdj_core_v0_1/src/lib/zip.ts` stable after the plan surface is stable.
4. Keep `reference/sdj_core_v0_1/src/index.ts` as the single supported public barrel until every library import site has moved to the typed surface.
5. Keep `src/workbench/helpers.ts`, `scene.ts`, `viewer.ts`, and `panels.ts` stable after the library layer type-checks cleanly.
6. Leave `src/app.js` as a thin loader until the browser shell no longer needs compatibility wrappers.

Stable entrypoints to preserve during the pass:

- `reference/sdj_core_v0_1/src/index.ts`
- `src/app.js`
- `src/types/sdj.d.ts`
- `src/types/runtime.d.ts`
- `reference/sdj_workbench_v0_2/tsconfig.json`

## Public Surface To Preserve

The plan should keep the current exported surface stable while the implementation moves:

- `reference/sdj_core_v0_1/src/lib/json.ts`: `asObject`, `asArray`, `asNumber`, `asString`, `cloneJson`, `toJson`
- `reference/sdj_core_v0_1/src/lib/scene.ts`: `normalizeSceneForWorkbench`, `flattenObjects`, `isShown`, `findObject`, `validateSemantics`, `validateObjectReferences`
- `reference/sdj_core_v0_1/src/lib/plan.ts`: `buildCompilePlan`, `buildAnalysisPlans`, `buildPresentationPlans`, `buildObjectPlans`, `fallbackSupport`, `artifactForKind`, `artifactPathForKind`, `buildTargetDiagnostics`, `buildObjectDiagnostics`, `inspectObject`, `inspectObjectMapping`, `artifactPathsForInspection`, `actionForSupport`, `encodeArtifactId`
- `reference/sdj_core_v0_1/src/lib/compile.ts`: `compileBackend`, `compileAllBackends`, `compileAllBackendsToFiles`
- `reference/sdj_core_v0_1/src/lib/zip.ts`: `createZipBlob`, `crc32`, `getCrcTable`, `toDosTime`, `toDosDate`
- `reference/sdj_workbench_v0_2/src/workbench/helpers.ts`: `byId`, `escapeHtml`, `errorMessage`, `downloadText`, `downloadBlob`, `getCesium`, `getSdjLoader`
- `src/workbench/bootstrap.ts`: app initialization and event wiring
- `src/workbench/scene.ts`: exposed-scene loading, catalog rendering, editor normalization, export, and token persistence helpers
- `src/workbench/viewer.ts`: viewer initialization, selection, zoom, and Cesium pick helpers
- `src/workbench/panels.ts`: diagnostics, totals, object tables, inspector rendering, and object report helpers
- `src/workbench/smoke.ts`: browser smoke summary hook

The compatibility rule is simple: if a function is still called by `src/app.js`, it remains part of the public surface for the duration of the migration, even if a better typed replacement will eventually supersede it.

## Phase Verification Matrix

Use this matrix to keep each conversion step measurable:

- After Phase 1, run `npm --workspace reference/sdj_workbench_v0_2 test`, `npm --workspace reference/sdj_workbench_v0_2 run check`, and `node --check reference/sdj_workbench_v0_2/src/app.js` to confirm the existing JS split still behaves the same.
- After each library conversion, run `npx tsc -p reference/sdj_workbench_v0_2/tsconfig.json` plus `tests/library-modules.test.mjs`.
- After each workbench conversion, run `npm --workspace reference/sdj_workbench_v0_2 test` plus the shell checks in `tests/workbench.test.mjs` and `tests/browser-smoke.test.mjs`.
- After browser-facing changes, run the browser smoke and confirm it writes a fresh artifact manifest under `reference/sdj_workbench_v0_2/generated-smoke/browser/`.
- After removing compatibility wrappers, rerun `npm --workspace reference/sdj_workbench_v0_2 test`, `npm --workspace reference/sdj_workbench_v0_2 run check`, and `npx tsc -p reference/sdj_workbench_v0_2/tsconfig.json` to confirm there are no stale imports or leaked browser globals.

If a step changes the public barrel or any `src/app.js` dependency, verify the call chain from `src/app.js` into `src/workbench/bootstrap.ts` and the relevant `reference/sdj_core_v0_1/src/index.ts` / `src/workbench/*` entrypoints before moving on.

## Refactor Phases

### Phase 1: Freeze the Boundary

- Keep the current JS module split intact.
- Stop adding new logic to `src/app.js`; treat it as composition only.
- Add tests for `reference/sdj_core_v0_1/src/lib/*` and `src/workbench/*` rather than only the end-to-end smoke path.
- Keep `reference/sdj_core_v0_1/src/index.ts` as the stable public barrel while internal modules can change freely.
- Keep the current `noEmit` TypeScript check in place so the boundary stays visible while the implementation is still JavaScript.

### Phase 2: Introduce TypeScript Types

- Expand `reference/sdj_workbench_v0_2/src/types/sdj.d.ts` into the canonical source for workbench shell types while the SDJ core package owns the shared scene/compile types.
- Keep `tsconfig.json` focused on the typed source graph while the browser loader remains a separate syntax-checked entrypoint.
- Use `.d.ts` files first for module contracts, then convert implementation files one by one.
- Define the browser-side dependency objects explicitly so app wiring stays thin and testable.
- Treat the current declarations as the contract for `reference/sdj_core_v0_1/src/lib` and `src/workbench`, not as a parallel type system.

### Phase 3: Convert Library First

- Keep `reference/sdj_core_v0_1/src/lib/*.ts` moving one file at a time, starting with `json`, `scene`, `plan`, then `compile` and `zip`.
- Preserve the barrel export in `reference/sdj_core_v0_1/src/index.ts` while the source graph stabilizes.
- Keep DOM, Cesium globals, `window`, and `localStorage` out of the library layer.
- Move any remaining target-specific formatting or adapter glue into target-owned modules instead of `app.js`.
- Validate each converted module with direct unit tests before changing the next one.

### Phase 4: Convert Workbench Orchestration

- Keep `src/workbench/helpers.ts`, `scene.ts`, `viewer.ts`, and `panels.ts` stable.
- Keep browser side effects isolated there and passed in through dependency objects.
- Preserve the thin `app.js` loader pattern and avoid reintroducing duplicate domain logic.
- Add narrow tests for the scene/catalog helpers and panel renderers where practical.
- Keep the `AppDeps` boundary stable so the workbench shell remains injectable in tests.
- Keep the same exported helper names during conversion so `src/app.js` can keep importing the existing entrypoints until the typed replacements are ready.
- Keep the browser smoke artifact manifest stable so render verification can be done from disk, not only from console or DOM assertions.

### Phase 5: Clean Up Compatibility

- Remove any remaining duplicate code paths from `src/app.js`.
- Leave only a top-level loader plus bootstrap indirection in `src/app.js`.
- Keep any compatibility barrel only if a downstream consumer still needs it.
- Delete temporary wrappers once the browser shell no longer depends on them.
- Keep the TypeScript config scoped to `.ts` and `.d.ts` sources once the browser loader is isolated.

### Phase 6: Tighten the TS Boundary

- Add `noEmit` type-checking for the workbench package in CI or a local check target.
- Convert `src/types` from ad hoc declarations into a stable contract package.
- Keep the TypeScript config scoped to `.ts` and `.d.ts` sources once the browser loader is isolated.
- Make the repo documentation point at the typed public surface and the conversion order, not just the implementation files.

## Done Criteria

- The library modules compile independently from the browser shell.
- The app shell contains no duplicated domain logic.
- The public API is documented and stable.
- Tests cover the extracted modules directly, not only the full workbench smoke path.
- The TypeScript boundary is explicit and repeatable.
- The current workbench JS modules can be type-checked without depending on browser globals leaking into the library layer.
- The refactor order is encoded in the repository docs rather than only in conversation.
- The browser smoke path produces an on-disk render manifest and screenshot artifacts in environments where Chromium can launch.

## Verification

- `npm --workspace reference/sdj_workbench_v0_2 test`
- `node --check reference/sdj_workbench_v0_2/src/app.js`
- `node --experimental-strip-types --check reference/sdj_workbench_v0_2/src/workbench/*.ts`
- `node --experimental-strip-types --check reference/sdj_core_v0_1/src/lib/*.ts`
- `npx tsc -p reference/sdj_workbench_v0_2/tsconfig.json`

Do not use `node --check` on `src/types/*.d.ts`; rely on `tsc` for declaration validation.

## Non-Goals

- Rewriting the Cesium adapter logic into a new rendering framework.
- Changing the exported scene or bundle formats as part of the refactor.
- Removing the current JavaScript entrypoints before the new boundaries are stable.
