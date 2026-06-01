# Roadmap

## Phase 1

- Lock the transport-agnostic message envelope.
- Confirm Cesium-first entity fields and naming.
- Build basic schema validation examples.

## Phase 2

- Add sensor volumes, paths, and overlay primitives.
- Define target compilation profiles for SOAP and SIMDIS, including the SIMDIS ASI/GOG bundle split.
- Document compatibility and lossiness rules per target.
- Promote the imported SDJ workbench artifacts into tracked schema and target contracts under `reference/`.
- Document the root workbench commands (`dev`, `check`, `smoke`, `browser-smoke`, `shell-smoke`, `test`) in the integration map and README.

## Phase 3

- Add code generation for TypeScript and Python bindings.
- Add conformance fixtures and translation tests.
- Add smoke tests for scene-level compilation across Cesium, SIMDIS, and SOAP.
- Track the SIMDIS extraction boundary in `docs/simdis-extraction-plan.md`.
- Track the SOAP extraction boundary in `docs/soap-extraction-plan.md`.
