# SDJ Survey / Exposé / Portfolio v0.5

This package is a coverage artifact for Spatial Display JSON (SDJ). It is meant to answer: "What corners of the Cesium/SIMDIS/SOAP display/API surface should SDJ cover, how do we name them, and what is the implementation status?"

Files:

- `sdj_survey_portfolio_v0_5.md` — human-readable survey and architecture.
- `sdj_feature_inventory_v0_5.json` — machine-readable feature portfolio.
- `sdj_coverage_backlog_v0_5.md` — prioritized implementation backlog.
- `sdj_schema_modules_v0_5.json` — proposed modular schema surface.
- `sdj_portfolio_scene_seed_v0_5.json` — seed scene with representative example objects.
- `sdj_acceptance_matrix_v0_5.md` — testing rules for proving full coverage.

The survey deliberately distinguishes:

- `schema` support: can SDJ represent the thing?
- `example` support: do we have example data for it?
- `cesiumRuntime` support: does the current Cesium adapter create native runtime objects?
- `simdisExport` / `soapExport` support: does the backend compiler emit a meaningful artifact?
