# Visualization Standard Schema

Visualization Standard Schema (VSS) is a standard message set for exchanging
visualization-oriented state between simulation, command-and-control, and
rendering systems.

The initial focus is Cesium-compatible scene and entity updates. Optional
compile targets are reserved for SOAP and SIMDIS integrations.

## Goals

- Define a stable message envelope for transport-agnostic exchange.
- Start with entity state required by geospatial 3D visualization clients.
- Keep source messages simple enough to compile into multiple downstream
  representations.
- Separate core schema from target-specific adapters.

## Repository Layout

- `schemas/` core JSON Schema definitions.
- `examples/` example payloads by consumer target.
- `targets/` notes and adapter contracts for compile targets.
- `docs/` design notes and roadmap material.

## Initial Message Set

The first schema version includes:

- message envelope metadata
- entity add or update messages
- WGS84 position state
- orientation state
- style hints for Cesium-oriented rendering

## Next Steps

1. Expand the core entity model for tracks, sensors, and overlays.
2. Add a validator and code generation workflow.
3. Define SOAP and SIMDIS field mapping rules from the core schema.
