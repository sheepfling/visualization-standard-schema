# Cesium SDJ Gap Map

## Purpose

This document answers two concrete questions for the current Python package:

1. Do we have full connection from the imported SDJ schema into the Cesium renderer?
2. Is the current package shape modular enough to reuse as a library or hook in another project?

Short answer:

- No, we do not have full SDJ-to-Cesium coverage yet.
- Yes, the package shape is reusable for the current narrow subset, but it is not yet a full SDJ rendering library.

## Baseline

Imported SDJ reference:

- `reference/sdj_workbench_v0_2/schemas/sdj_v0_4.schema.json`
- `reference/sdj_workbench_v0_2/src/sdj_browser_compiler.js`

Current Python Cesium path:

- `src/vss/models.py`
- `src/vss/cesium/__init__.py`
- `targets/capabilities/target-capabilities.json`

## Current Python Scene Surface

The current Python scene model is intentionally small.

Supported top-level scene concepts:

- `document`
- `objects`

Supported object families:

- `SceneEntity`
- `SceneOverlay`
- `ScenePath`
- `SceneTrack`

Supported overlay geometries:

- `polyline`
- `polygon`
- `rectangle`
- `corridor`
- `ellipse`
- `circle`

Supported entity styling:

- `label`
- `iconUri`
- `modelUri`
- `colorRgba`

Important omissions relative to imported SDJ:

- `units`
- `clock` as authored scene input
- `scene`
- `assets`
- `materials`
- `layers`
- `views`
- `analysis`
- `presentation`
- `backend`
- `backendCapabilities`
- `extensions`

## Imported SDJ Object Families

The imported SDJ schema advertises a much larger object-kind surface, including:

- marker and entity-like objects:
  `point`, `billboard`, `label`, `model`, `path`, `track`
- geometry objects:
  `polyline`, `polygon`, `rectangle`, `ellipse`, `circle`, `box`, `cylinder`, `cone`, `ellipsoid`, `sphere`, `wall`, `corridor`, `polylineVolume`, `plane`
- terrain and tiles:
  `tileset`, `terrain`, `imageryLayer`
- coverage and sensor objects:
  `sector2d`, `sectorVolume`, `hemisphere`, `sphericalCap`, `keyhole`, `rangeRing`, `bearingFan`, `frustum`, `conicSensor`, `rectangularSensor`, `customPatternSensor`, `fan`
- vectors and derived lines:
  `vector`, `velocityVector`, `accelerationVector`, `bodyAxes`, `principalAxes`, `lineOfSight`, `relativeLine`, `interceptLine`
- uncertainty and effects:
  `uncertaintyEllipsoid`, `covarianceEllipse`, `particleSystem`, `voxel`
- renderer/runtime objects:
  `clippingPolygon`, `clippingPlane`, `classificationVolume`, `postProcessStage`, `customPrimitive`, `composite`, `atmosphere`, `cameraView`, `customShader`, `czmlDataSource`, `dataSource`, `geoJsonDataSource`, `kmlDataSource`, `skyBox`, `videoPlane`, `primitiveMesh`, `terrainSurface`, `customMesh`

The current Python model does not expose most of those at all.

## Current Cesium Emitter Coverage

The current Cesium emitter in `src/vss/cesium/__init__.py` compiles:

- document packet
- scene clock derived from object timestamps
- entity packets with:
  - cartographic position
  - label graphics
  - billboard graphics
  - model graphics
  - point graphics
  - category/source/timestamp properties
- path packets with:
  - sampled cartographic motion
  - path graphics
  - sampled label/color styling
- track packets with:
  - sampled cartographic motion
  - path graphics
  - orientation properties
- overlay packets with:
  - polyline geometry
  - polygon geometry
  - rectangle geometry
  - corridor geometry
  - overlay label styling

Current Cesium target support is already tracked in `targets/capabilities/target-capabilities.json`.

## Gap Matrix

### Fully Wired Today

- `document` metadata -> CZML document packet
- `entity.position` -> CZML `position.cartographicDegrees`
- `style.label` -> CZML `label`
- `style.iconUri` -> CZML `billboard`
- `style.modelUri` -> CZML `model`
- `style.colorRgba` -> CZML point/label/polyline/polygon coloring
- `path.samples` -> CZML sampled `position` plus `path`
- `track.samples` -> CZML sampled `position` plus `path`
- `track.orientation` -> CZML orientation properties
- `overlay.rectangle` -> CZML `rectangle`
- `overlay.polyline` -> CZML `polyline`
- `overlay.polygon` -> CZML `polygon`
- `overlay.corridor` -> CZML `corridor`
- `overlay.ellipse` -> CZML `ellipse`
- `overlay.circle` -> CZML `ellipse`
- timestamps -> CZML document `clock`

### Partially Wired Today

- `entity.orientation`
  Current status: preserved only in `properties.orientationDegrees`
  Missing: native Cesium `orientation` quaternion / frame semantics

- `path` sampled motion
  Current status: typed path objects compile to sampled CZML position plus path graphics
  Missing: richer path semantics, alternate interpolation policies, and first-class track modeling

- `track` sampled motion
  Current status: typed track objects compile to sampled CZML position plus path graphics and orientation metadata
  Missing: richer trajectory schema and full imported-SDJ position/orientation sampling semantics

- `rectangle` overlay geometry
  Current status: typed rectangle overlays compile to CZML rectangle packets with bounds and styling
  Missing: higher-level rectangle authoring helpers and rotation/extrusion ergonomics

- `corridor` overlay geometry
  Current status: typed corridor overlays compile to CZML corridor packets with positions, width, and styling
  Missing: richer corridor ergonomics and imported-SDJ corner-case semantics

- `ellipse` overlay geometry
  Current status: typed ellipse overlays compile to CZML ellipse packets with axes and styling
  Missing: higher-level ellipse authoring helpers and imported-SDJ edge cases

- `circle` overlay geometry
  Current status: typed circle overlays compile to CZML ellipse packets with matching axes and styling
  Missing: higher-level circle authoring helpers and imported-SDJ edge cases

- sensor entities
  Current status: sensor category can render as normal entity, billboard, or model
  Missing: sensor volume geometry such as conic, rectangular, frustum, keyhole, fan

- viewer/runtime integration
  Current status: generated HTML shell loads CZML into CesiumJS
  Missing: authored scene views, camera programs, loader module, richer runtime hooks

### Not Wired Into the Python Scene Model Yet

- `ellipse`
- `circle`
- `box`
- `cylinder`
- `cone`
- `ellipsoid`
- `sphere`
- `wall`
- `polylineVolume`
- `plane`
- `tileset`
- `sector2d`
- `sectorVolume`
- `hemisphere`
- `sphericalCap`
- `keyhole`
- `rangeRing`
- `bearingFan`
- `frustum`
- `conicSensor`
- `rectangularSensor`
- `customPatternSensor`
- `fan`
- `vector`
- `velocityVector`
- `accelerationVector`
- `bodyAxes`
- `principalAxes`
- `lineOfSight`
- `relativeLine`
- `interceptLine`
- `uncertaintyEllipsoid`
- `covarianceEllipse`
- `particleSystem`
- `voxel`
- renderer-specific runtime objects from the imported schema

### Not Wired Into Cesium Output Yet Even If Added To Scene Model

- authored `views`
- authored `analysis`
- authored `presentation`
- imported SDJ backend artifact concepts like `compile-plan` and loader modules

## Comparison With Imported Workbench

The imported browser compiler already reasons about many more SDJ kinds than the
current Python Cesium adapter.

The imported compiler explicitly classifies many kinds as Cesium-native or
Cesium-partial, including:

- entity-like kinds:
  `point`, `billboard`, `label`, `model`, `track`, `path`
- standard geometries:
  `polyline`, `polygon`, `rectangle`, `ellipse`, `circle`, `box`, `cylinder`, `cone`, `ellipsoid`, `sphere`, `wall`, `corridor`, `polylineVolume`, `plane`
- tiles and higher-level primitives:
  `tileset`
- sensor/coverage families:
  `sector2d`, `sectorVolume`, `hemisphere`, `sphericalCap`, `keyhole`, `rangeRing`, `bearingFan`, `frustum`, `conicSensor`, `rectangularSensor`, `customPatternSensor`, `fan`
- vector families:
  `vector`, `velocityVector`, `accelerationVector`, `bodyAxes`, `principalAxes`, `lineOfSight`, `relativeLine`, `interceptLine`
- effects:
  `uncertaintyEllipsoid`, `covarianceEllipse`, `particleSystem`

That means the Python package is not just missing implementation detail. It is
still missing large chunks of the object model that the imported SDJ baseline
already assumes.

## Library Assessment

### What Is Good

The current package shape is reasonably modular for the subset it supports:

- core models are separate from target adapters
- IO helpers are separate from rendering adapters
- target code is target-owned:
  - `vss.cesium`
  - `vss.simdis`
  - `vss.soap`
- `vss.targets` is only a compatibility facade
- capability reporting is now data-driven from `targets/capabilities/target-capabilities.json`

This is a usable library shape for:

- validating the current message and scene subset
- generating current CZML output
- embedding current compile helpers in another Python project

### What Is Not Ready Yet

It is not yet a sufficiently complete SDJ library if another project expects:

- broad imported-SDJ object support
- authored views and camera integration
- analysis or presentation compilation
- plugin-style registration of new object families
- a stable scene IR that cleanly separates generic scene semantics from target-specific renderer semantics

## Reuse Verdict

Use it as a library today if the downstream project only needs the current
subset:

- entity updates
- simple scene documents
- labels, billboards, models
- polyline and polygon overlays
- basic CZML generation

Do not present it as a full SDJ-to-Cesium library yet.

## Recommended Next Steps

1. Promote a broader tracked `vss-scene` schema from the imported SDJ schema.
2. Replace the current `SceneEntity`/`SceneOverlay` split with typed object families that match imported SDJ kinds more closely.
3. Refactor the Cesium target into per-kind emitters instead of one mostly flat packet builder.
4. Add a native Cesium orientation path with explicit frame semantics.
5. Add first-class scene `views` and compile them into runtime camera behavior.
6. Add scene-level fixtures that exercise imported SDJ families incrementally:
   - `track` / `path`
   - `wall`
   - sensor volumes
   - vectors
   - tileset

## Practical Conclusion

The current codebase is modular enough to be reused as a narrow library.
It is not yet complete enough to be the SDJ Cesium library implied by the
imported `sdj_v0_4` schema and workbench.
