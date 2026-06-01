# SDJ v0.5 Coverage Backlog

## P0 — must close to claim modern Cesium profile

- Add explicit `gaussianSplatTileset` object alias and splat-specific capability diagnostics.
- Implement target attachment resolver: an advanced object can target a tileset, model, globe, data source, or primitive.
- Implement `tilesetStyle -> Cesium.Cesium3DTileStyle`.
- Implement `customShader -> Cesium.CustomShader` for model/tileset where supported.
- Implement `clippingPlane` and `clippingPolygon` target attachments.
- Implement `classificationPrimitive` and `classificationVolume` adapters.
- Add `terrain` and `imageryLayer` provider specs and runtime adapters.
- Implement data-source bridge objects for CZML, GeoJSON, KML.
- Expand material schema to cover Cesium material properties and polyline materials.

## P1 — tactical/backend completeness

- Implement ion SDK direct sensor path where available.
- Add dynamic model-matrix update support for custom primitives.
- Add antenna pattern, RF volume, gate, laser, LOB, and projector schemas as backend-aware tactical objects.
- Add SOAP/SIMDIS stronger native exports for sensor swaths, RF links, access intervals, and coverage grids.
- Add coverage scene generator with one visible and one hidden sample per feature.

## P2 — presentation/effects completeness

- Implement post-process stages.
- Implement cloud collection and atmosphere/skybox settings.
- Add video plane and panorama adapters.
- Add presentation timeline/camera scripting that works in Cesium and exports to SOAP/SIMDIS presentation bundles.

## P3 — future renderers

- Add Unreal rendererHints/profile.
- Add TGx rendererHints/profile.
- Add renderer-neutral material downsampling rules.
- Add conformance tests for target capability negotiation.
