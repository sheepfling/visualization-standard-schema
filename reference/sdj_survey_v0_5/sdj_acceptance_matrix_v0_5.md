# SDJ v0.5 Acceptance Matrix

Every schema/API corner should be tracked with the following acceptance columns.

| Gate | Requirement | Pass condition |
|---|---|---|
| G1 Schema | Feature has a stable kind/property definition | JSON Schema validates a minimal and full fixture |
| G2 Semantics | Required fields and target references are checked | Semantic validator catches missing fields and broken references |
| G3 Example | Feature appears in example portfolio | At least one sample object exists; two for P0 features |
| G4 Cesium plan | Compiler creates a target plan | Plan reports strong/partial/reserved/unsupported explicitly |
| G5 Cesium render | Runtime adapter creates a native object or reserved diagnostic | Render smoke test passes or expected diagnostic is emitted |
| G6 SIMDIS export | Compiler emits artifact or lossiness diagnostic | Bundle contains object in manifest/entities/GOG/analysis/presentation |
| G7 SOAP export | Compiler emits artifact or lossiness diagnostic | Bundle contains object in scenario/views/analysis/presentation |
| G8 Inspector | Workbench explains the mapping | Selected object shows per-backend status, artifact paths, diagnostics |
| G9 Regression | Test fixture is automated | Smoke test covers validation, compile, export, inspect |
| G10 Documentation | Feature appears in survey | Portfolio row includes notes, priority, and implementation status |

## Coverage score

- 10/10: feature is production-covered.
- 7–9/10: feature is usable with caveats.
- 4–6/10: feature is represented but adapter work remains.
- 1–3/10: feature is only named/reserved.
- 0/10: feature is not in SDJ.
