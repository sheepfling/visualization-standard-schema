# Visualization Standard Schema

Visualization Standard Schema (VSS) is a standard message set for exchanging
visualization-oriented state between simulation, command-and-control, and
rendering systems.

The initial focus is Cesium-compatible scene and entity updates. Cesium,
SIMDIS, and SOAP are treated as separate compile targets with target-owned
Python namespaces.

## Goals

- Define a stable message envelope for transport-agnostic exchange.
- Start with entity state required by geospatial 3D visualization clients.
- Keep source messages simple enough to compile into multiple downstream
  representations.
- Separate core schema from target-specific adapters.

## Repository Layout

- `schemas/` core JSON Schema definitions.
- `src/vss/` Pydantic models, loaders, and compile target packages.
- `scripts/` helper scripts for schema export and example target generation.
- `examples/` example payloads by consumer target.
- `targets/` notes and adapter contracts for compile targets.
- `docs/` design notes and roadmap material.

`INBOX/` is the ignored drop zone for unpacked source assets and scratch imports while they are being evaluated for promotion into tracked `reference/` or `examples/` content.
Imported SDJ workbench integration notes are captured in `docs/sdj-workbench-integration-map.md`, with the tracked bundle now under `reference/sdj_workbench_v0_2/`.
The reusable browser-library layer extracted from that workbench now lives in the separate `sdj-core` package under `reference/sdj_core_v0_1/`.
The JS/TS modularization plan for that split is in `docs/workbench-js-ts-refactor-plan.md`.

For a single overview of the core schema and compile targets, see `docs/schema-and-targets-overview.md`.
For field-level SDJ contracts, see `docs/sdj-schema.md`.
The SDJ survey / exposé / portfolio v0.5 package is tracked in `reference/sdj_survey_v0_5/`.
Tracked ORB sample fixtures used by the regression suite live in `reference/orb_samples/`.

For the Cesium workbench, run from the repo root:

```bash
npm install
npm run dev
```

Useful root-level workbench commands:

```bash
npm run check
npm run build:exposed-scenes
npm run smoke
npm run browser-smoke
npm run shell-smoke
npm run test
```

`browser-smoke` tries a local browser first and falls back to the shell markup check when browser launch is blocked. `shell-smoke` always reads `reference/sdj_workbench_v0_2/index.html` from disk and does not require a running server.

## Initial Message Set

The first schema version includes:

- message envelope metadata
- entity add or update messages
- WGS84 position state
- orientation state
- style hints for Cesium-oriented rendering

## Next Steps

1. Expand the core entity model for tracks, sensors, and overlays.
2. Grow the initial Pydantic binding into scene-level payloads and batch messages.
3. Refine SOAP and SIMDIS field mapping rules from the core schema.
4. Integrate the imported SDJ scene schema and compiler artifacts in layers rather than replacing the transport envelope directly.

## Python Model Layer

The repository now includes a first Python implementation of the current
standard in `src/vss/`.

It currently supports:

- strict Pydantic validation for the `entity.upsert` envelope
- loading from Python dictionaries, JSON strings, and JSON files
- generating a Pydantic-derived JSON Schema
- compiling an example message to Cesium, SIMDIS, and SOAP-oriented outputs
- keeping target-specific code in `vss.cesium`, `vss.simdis`, and `vss.soap`,
  with `vss.targets` kept as a compatibility facade

## Target Capability Surface

The package now exposes a capability-reporting surface for each target so you
can ask both:

- what the adapter claims to support from the current SDJ/VSS scene surface
- what a specific scene uses that the adapter supports strongly, partially, or not at all

The static target declarations are tracked in
`targets/capabilities/target-capabilities.json` and loaded directly by the
runtime capability API.

Python entrypoints:

```python
from vss import get_cesium_capabilities, get_simdis_capabilities, get_soap_capabilities
from vss import assess_scene_for_target, load_scene_file

scene = load_scene_file("examples/scenes/mixed-ops.scene.json")
report = get_simdis_capabilities()
assessment = assess_scene_for_target(scene, "simdis")
```

CLI entrypoint:

```bash
vss capabilities --target simdis
vss capabilities --target simdis --input examples/scenes/mixed-ops.scene.json
```

Current target surfaces are:

- Cesium: `czml`, `cesium-js-viewer`
- SIMDIS: `simdis-asi`, `simdis-gog`, `simdis-bundle`
- SOAP: `soap-envelope`, `soap-bundle`, with `orb` tracked as a related scenario surface

## Quick Start

Set up a local editable install with development dependencies:

```bash
python3 -m pip install -e ".[dev]"
```

Run the smoke tests:

```bash
python3 -m pytest
```

Run just the corpus round-trip checks when you are working on SIMDIS, SOAP, or the exposed SDJ scene set:

```bash
python3 -m pytest -m sdj_roundtrip
python3 -m pytest tests/test_sdj_corpus_roundtrip.py -q
python3 -m pytest tests/test_simdis_corpus.py tests/test_soap_corpus.py -q
```

These tests are designed to be rerunnable from a clean checkout:

- they only read checked-in fixture data
- they write temporary outputs under pytest-managed `tmp_path` directories
- they compare stable semantic fields instead of raw bytes when a native format is lossy

Use the bundled CLI to ingest into SDJ or emit SDJ back out:

```bash
vss ingest --format czml --input examples/generated/air-pair.scene.czml.json --output /tmp/scene.json
vss emit --format simdis-asi --input examples/scenes/air-pair.scene.json --output /tmp/air-track.simdis.txt
vss emit --format soap --input examples/scenes/air-pair.scene.json --output /tmp/air-track.soap.xml
vss emit --format orb --input examples/scenes/air-pair.scene.json --output /tmp/air-track.orb.txt
vss ingest --format simdis-bundle --input /path/to/simdis-bundle-dir --output /tmp/air-track.scene.json
```

Supported ingest formats are `simdis-asi`, `simdis-bundle`, `soap`, `orb`, and `czml`.
Supported emit formats are `simdis-asi`, `soap`, `orb`, and `czml`.

Export the Pydantic-generated schemas:

```bash
python3 scripts/export_schema.py
```

This writes:

- `schemas/vss-message.pydantic.schema.json`
- `schemas/vss-scene.pydantic.schema.json`

Render example target outputs from `examples/cesium/air-track.json`:

```bash
python3 scripts/render_example_targets.py
```

Build the ORB-derived SDJ, Cesium, and SOAP fixture corpus from the bundled archive:

```bash
python3 scripts/build_orb_fixture_set.py --archive reference/orb_format_collection/orb_format_collection.tar --output examples/orb-corpus --timeout-seconds 5
```

## ORB Corpus

`examples/orb-corpus/` is the initial cross-target fixture set built from the
SOAP `.orb` scenario archive in
`reference/orb_format_collection/orb_format_collection.tar`.

The current manifest covers:

- `145` real `.orb` scenarios after filtering macOS `._` sidecar entries
- `131` scenarios converted into SDJ, Cesium, and SOAP artifacts
- `14` scenarios recorded as parse timeouts in `examples/orb-corpus/manifest.json`

Generated layout:

- `examples/orb-corpus/sdj/`: normalized scene files
- `examples/orb-corpus/cesium/`: CZML scene outputs
- `examples/orb-corpus/soap/`: SOAP scene bundle JSON outputs
- `examples/orb-corpus/manifest.json`: per-scenario metadata, output paths, and failures

## Tooling

Use the configured quality checks directly:

```bash
ruff check src tests
pyright src tests
```

Use the developer Makefile for repeatable runs:

```bash
make lint        # run lint checks only
make lint-fix    # auto-fix lint violations
make typecheck   # run pyright
make test        # run pytest
make check       # run lint + typecheck + test
```

For local one-shot resets:

```bash
make lint-fix
make check
```

The `make lint-fix` target handles common autofix passes via Ruff, then `make check` reruns lint, typing, and tests for a full local verification cycle.
