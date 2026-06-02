# SDJ Workbench v0.2

SDJ Workbench is a browser front end for the Spatial Display JSON pipeline.

It gives you a CesiumJS page with a Sandcastle-like control drawer where you can paste, upload, or drag/drop SDJ JSON, validate it, render it in Cesium, inspect per-object backend mappings, and export compiled bundles for Cesium, SIMDIS, and SOAP.

## What this project proves

```text
SDJ JSON
  -> browser-side normalization
  -> semantic validation
  -> backend capability planning
  -> per-object backend inspection
  -> Cesium runtime render
  -> Cesium / SIMDIS / SOAP export ZIPs
```

Cesium is the live renderer in this workbench. SIMDIS and SOAP exports are normalized artifact bundles that preserve backend diagnostics and lossy/partial support notes. They are designed as an adapter boundary, not as a claim that every file is a proprietary native project file.

The ingest/normalize/compile core now lives in the separate `sdj-core` package at `reference/sdj_core_v0_1/`; this workbench keeps the browser shell, showcase pages, and Cesium runtime wiring.

## New in v0.2

- Object coverage rows are clickable.
- Clicking a rendered Cesium entity or primitive selects the corresponding SDJ object when the runtime exposes the id.
- The Backend Object Inspector shows each selected object's Cesium, SIMDIS, and SOAP support status.
- Each target card shows the native backend target, lossiness level, object-specific artifact path, generated bundle files, target-specific diagnostics, renderer hints, and the normalized source object JSON.
- The smoke test now exercises the inspector path in addition to validation and export generation.
- The workbench opens on a browsable catalog of exposed SDJ corpus scenes so default users can see the range of supported examples immediately.

## Project layout

```text
index.html                                  # Cesium page and SDJ drawer UI
src/app.js                                  # Thin browser loader
src/workbench/bootstrap.ts                  # UI orchestration, inspector, and Cesium render calls
sdj-core package in reference/sdj_core_v0_1/ # Browser-visible core compiler entrypoint
src/styles.css                              # Workbench UI styles
vendor/sdj_cesium_loader_v0_4.js             # Cesium runtime adapter from SDJ v0.4
examples/sdj_minimal_scene.json             # Small render/export smoke scene
examples/sdj_full_coverage_scene_v0_4.json   # Comprehensive coverage scene
schemas/sdj_v0_4.schema.json                # SDJ schema reference
data/sdj_backend_capabilities_v0_4.json      # Backend support matrix
data/sdj_exposed_scenes_manifest.json        # Generated gallery of exposed SDJ corpus scenes
scripts/smoke-test.mjs                      # Node smoke test for compiler/export artifacts
scripts/build-exposed-scenes-manifest.mjs    # Regenerates the exposed SDJ gallery manifest
```

## Run locally

With Node installed:

```bash
npm install
npm run dev
```

Then open the printed local URL.

Without installing dependencies, you can also serve the folder with Python:

```bash
npm run serve:static
```

Then open `http://localhost:5173`.

Do not open `index.html` directly from `file://`; the browser blocks local JSON fetches in many environments.

## Use the app

1. Load the minimal example or full coverage example.
2. Press **Validate** to build diagnostics and backend support totals.
3. Click a row in **Object coverage** to inspect how that object maps to Cesium, SIMDIS, and SOAP.
4. Press **Render SDJ** to create Cesium objects, then click rendered entities/primitives to inspect their source SDJ object.
5. Use **Export Cesium ZIP**, **Export SIMDIS ZIP**, **Export SOAP ZIP**, or **Export All ZIP**.
6. Paste or drag/drop your own SDJ JSON to repeat the process.

## Cesium ion token

The UI can run without a token for local SDJ objects. Add a Cesium ion token if your SDJ scene references ion assets, world terrain, or other ion-hosted resources.

## Smoke test

```bash
npm run check
npm run smoke
```

The smoke test reads the comprehensive scene, validates it, compiles all backend bundles, exercises the object inspector helper, and writes a report under `generated-smoke/smoke-report.json`.

To regenerate the exposed-scene catalog after adding or moving corpus files:

```bash
npm run build:exposed-scenes
```

For browser verification:

```bash
npm run browser-smoke
```

The browser smoke prefers a local browser executable when one is available on macOS, or you can point it at a specific browser with `SDJ_BROWSER_EXECUTABLE_PATH`. Set `SDJ_BROWSER_CHANNEL=chrome` to use a Playwright channel, or `SDJ_BROWSER_SMOKE_FALLBACK=none` to disable the HTML fallback. When browser launch is blocked, it falls back to a shell-level markup check unless you disable that fallback.

When the browser path succeeds, it also writes rendered evidence under `generated-smoke/browser/`:

- `browser-smoke-report.json`
- `browser-workbench.png`
- `cesium-container.png`

If you want the CI-safe shell check directly:

```bash
npm run shell-smoke
```

That check reads `index.html` from disk, so it does not need a running local server.
