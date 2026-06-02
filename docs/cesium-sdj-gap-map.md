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
- `reference/sdj_core_v0_1/src/index.ts`

Current Python Cesium path:

- `src/vss/models.py`
- `src/vss/cesium/__init__.py`
- `targets/capabilities/target-capabilities.json`

## Current Python Scene Surface

The current Python scene model is intentionally small.

Supported top-level scene concepts:

- `document`
- `objects`
- `views`
- `analysis`
- `presentation`

Supported object families:

- `SceneEntity`
- `SceneOverlay`
- `ScenePath`
- `SceneTrack`
- `SceneVector`
- `SceneVelocityVector`
- `SceneAccelerationVector`
- `SceneView`
- `SceneLineOfSight`
- `SceneBodyAxes`
- `ScenePrincipalAxes`
- `SceneRelativeLine`
- `SceneInterceptLine`
- `SceneCameraView`
- `SceneCustomObject`
- `SceneRuntimeObject`
- `SceneTerrainSurface`
- `SceneCustomMesh`
- `SceneClippingPlane`
- `SceneClippingPolygon`
- `SceneClassificationVolume`
- `SceneCustomShader`
- `ScenePostProcessStage`

Supported overlay geometries:

- `polyline`
- `polygon`
- `rectangle`
- `corridor`
- `ellipse`
- `circle`
- `rangeRing`
- `wall`
- `box`
- `cylinder`
- `cone`
- `conicSensor`
- `rectangularSensor`
- `sector2d`
- `bearingFan`
- `fan`
- `sectorVolume`
- `hemisphere`
- `sphericalCap`
- `keyhole`
- `frustum`
- `customPatternSensor`
- `polylineVolume`
- `plane`
- `ellipsoid`
- `sphere`
- `uncertaintyEllipsoid`
- `covarianceEllipse`
- `particleSystem`
- `voxel`
- `custom`
- `runtime`

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
- `backend`
- `backendCapabilities`
- `extensions`

## Imported SDJ Object Families

The imported SDJ schema advertises a much larger object-kind surface, including:

- marker and entity-like objects:
  `point`, `billboard`, `label`, `model`, `path`, `track`
- geometry objects:
  `polyline`, `polygon`, `rectangle`, `ellipse`, `circle`, `box`, `cylinder`, `cone`, `ellipsoid`, `sphere`, `wall`, `corridor`, `polylineVolume`, `plane`, `tileset`
- terrain and tiles:
  `tileset`, `terrain`, `imageryLayer`
- coverage and sensor objects:
  `sector2d`, `sectorVolume`, `hemisphere`, `sphericalCap`, `keyhole`, `bearingFan`, `frustum`, `conicSensor`, `rectangularSensor`, `customPatternSensor`, `fan`
- vectors and derived lines:
  `vector`, `velocityVector`, `accelerationVector`, `bodyAxes`, `principalAxes`, `lineOfSight`, `relativeLine`, `interceptLine`
- uncertainty and effects:
  `uncertaintyEllipsoid`, `covarianceEllipse`, `particleSystem`, `voxel`
- renderer/runtime objects:
  `clippingPolygon`, `clippingPlane`, `classificationVolume`, `postProcessStage`, `customPrimitive`, `composite`, `atmosphere`, `cameraView`, `customShader`, `czmlDataSource`, `dataSource`, `geoJsonDataSource`, `kmlDataSource`, `skyBox`, `videoPlane`, `primitiveMesh`

The current Python model still does not expose most of those at all, but it now has typed `SceneTerrainSurface` and `SceneCustomMesh` subclasses for the imported runtime surface placeholders.

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
- axes packets with:
  - body or principal frame axes
  - three polyline packets with per-axis styling
- scene-view controls with:
  - button-driven camera actions
  - target or position-based navigation
- custom/runtime packets with:
  - typed payload preservation
  - position and orientation preservation
  - emitter registry dispatch for custom geometry families
  - explicit terrainSurface/customMesh typed subclass preservation
  - explicit clippingPlane/clippingPolygon/classificationVolume typed subclass preservation
  - explicit customShader/postProcessStage typed subclass preservation
- overlay packets with:
  - polyline geometry
  - polygon geometry
  - rectangle geometry
  - corridor geometry
  - ellipse geometry
  - circle geometry
  - rangeRing geometry
  - wall geometry
  - overlay label styling
  - box geometry
  - cylinder geometry
  - cone geometry
  - conicSensor geometry
  - rectangularSensor geometry
  - sector2d geometry
  - sectorVolume geometry
  - hemisphere geometry
  - polylineVolume geometry
  - ellipsoid geometry
  - sphere geometry
  - uncertainty ellipsoid geometry
  - covariance ellipse geometry
  - particle system geometry
  - voxel box approximation plus metadata
  - custom object packet preservation / emitter dispatch

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
- `overlay.wall` -> CZML `wall`
- `overlay.box` -> CZML `box`
- `overlay.cylinder` -> CZML `cylinder`
- `overlay.cone` -> CZML `agi_conicSensor`
- `overlay.conicSensor` -> CZML `agi_conicSensor`
- `overlay.rectangularSensor` -> CZML `agi_rectangularSensor`
- `overlay.polylineVolume` -> CZML `polylineVolume`
- `overlay.plane` -> CZML `plane`
- `overlay.tileset` -> CZML `tileset`
- `overlay.ellipsoid` -> CZML `ellipsoid`
- `overlay.sphere` -> CZML `ellipsoid`
- `overlay.uncertaintyEllipsoid` -> CZML `ellipsoid`
- `overlay.covarianceEllipse` -> CZML `ellipse`
- `overlay.particleSystem` -> CZML `particleSystem`
- `overlay.voxel` -> CZML `box` approximation plus voxel metadata
- `vector` -> CZML `polyline`
- `velocityVector` -> CZML `polyline`
- `accelerationVector` -> CZML `polyline`
- `lineOfSight` -> CZML `polyline`
- `bodyAxes` -> three CZML `polyline` packets
- `principalAxes` -> three CZML `polyline` packets
- `relativeLine` -> CZML `polyline`
- `interceptLine` -> CZML `polyline`
- `views` -> CesiumJS viewer buttons and target/position camera actions
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

- `rangeRing` overlay geometry
  Current status: typed range ring overlays compile to outlined CZML ellipse packets with radius and outline styling
  Missing: richer range ring authoring helpers and imported-SDJ edge cases

- `wall` overlay geometry
  Current status: typed wall overlays compile to CZML wall packets with positions and height arrays
  Missing: richer wall authoring helpers and imported-SDJ edge cases

- `box` overlay geometry
  Current status: typed box overlays compile to CZML box packets with dimensions and styling
  Missing: richer box authoring helpers and imported-SDJ edge cases

- `cylinder` overlay geometry
  Current status: typed cylinder overlays compile to CZML cylinder packets with length, radii, and styling
  Missing: richer cylinder authoring helpers and imported-SDJ edge cases

- `cone` overlay geometry
  Current status: typed cone overlays compile to Cesium `agi_conicSensor` packets with radius, angular limits, and styling
  Missing: richer cone authoring helpers, native intersection/cap materials, and imported-SDJ edge cases

- `rectangularSensor` overlay geometry
  Current status: typed rectangular sensor overlays compile to Cesium `agi_rectangularSensor` packets with radius, half angles, orientation, and styling
  Missing: richer rectangular sensor authoring helpers and imported-SDJ edge cases

- `sector2d` overlay geometry
  Current status: typed sector2d overlays compile to CZML polygon wedge approximations with sector metadata preserved in packet properties
  Missing: richer sector2d authoring helpers and imported-SDJ edge cases

- `bearingFan` overlay geometry
  Current status: typed bearingFan overlays compile to CZML polygon wedge approximations with sector metadata preserved in packet properties
  Missing: richer bearingFan authoring helpers and imported-SDJ edge cases

- `fan` overlay geometry
  Current status: typed fan overlays compile to CZML polygon wedge approximations with sector metadata preserved in packet properties
  Missing: richer fan authoring helpers and imported-SDJ edge cases

- `customPatternSensor` overlay geometry
  Current status: typed customPatternSensor overlays compile to CZML polygon wedge approximations with pattern metadata preserved in packet properties
  Missing: richer customPatternSensor authoring helpers and imported-SDJ edge cases

- `sectorVolume` overlay geometry
  Current status: typed sectorVolume overlays compile to CZML polygon wedge approximations with sector-volume metadata preserved in packet properties
  Missing: richer sectorVolume authoring helpers and imported-SDJ edge cases

- `hemisphere` overlay geometry
  Current status: typed hemisphere overlays compile to CZML ellipsoid packets with hemisphere metadata preserved in packet properties
  Missing: richer hemisphere authoring helpers and imported-SDJ edge cases

- `sphericalCap` overlay geometry
  Current status: typed sphericalCap overlays compile to CZML ellipsoid packets with spherical-cap metadata preserved in packet properties
  Missing: richer sphericalCap authoring helpers and imported-SDJ edge cases

- `keyhole` overlay geometry
  Current status: typed keyhole overlays compile to CZML polygon wedge approximations with keyhole metadata preserved in packet properties
  Missing: richer keyhole authoring helpers and imported-SDJ edge cases

- `frustum` overlay geometry
  Current status: typed frustum overlays compile to approximate CZML box packets with frustum metadata preserved in packet properties
  Missing: richer frustum authoring helpers and imported-SDJ edge cases

- `polylineVolume` overlay geometry
  Current status: typed polyline volume overlays compile to native CZML polylineVolume packets with positions, shape points, and styling
  Missing: richer polyline volume authoring helpers and imported-SDJ edge cases

- `plane` overlay geometry
  Current status: typed plane overlays compile to native CZML plane packets with normal vectors, distances, dimensions, and styling
  Missing: richer plane authoring helpers and imported-SDJ edge cases

- `tileset` overlay geometry
  Current status: typed tileset overlays compile to native CZML tileset packets with URIs and styling metadata
  Missing: richer tileset authoring helpers and imported-SDJ edge cases

- `vector` object
  Current status: typed vector objects compile to native CZML polyline packets with explicit start and end positions plus styling
  Missing: richer vector families such as axes

- `velocityVector` object
  Current status: typed velocity vector objects compile to native CZML polyline packets with explicit start and end positions plus styling
  Missing: richer derived-vector semantics and imported-SDJ edge cases

- `accelerationVector` object
  Current status: typed acceleration vector objects compile to native CZML polyline packets with explicit start and end positions plus styling
  Missing: richer derived-vector semantics and imported-SDJ edge cases

- `lineOfSight` object
  Current status: typed line-of-sight objects compile to native CZML polyline packets with explicit start and end positions plus styling
  Missing: richer line-of-sight semantics and imported-SDJ edge cases

- `bodyAxes` object
  Current status: typed body-axes objects compile to three native CZML polyline packets representing the body frame axes
  Missing: richer axis semantics and imported-SDJ edge cases

- `principalAxes` object
  Current status: typed principal-axes objects compile to three native CZML polyline packets representing the principal frame axes
  Missing: richer axis semantics and imported-SDJ edge cases

- `relativeLine` object
  Current status: typed relative-line objects compile to native CZML polyline packets with explicit start and end positions plus styling
  Missing: richer relative-line semantics and imported-SDJ edge cases

- `interceptLine` object
  Current status: typed intercept-line objects compile to native CZML polyline packets with explicit start and end positions plus styling
  Missing: richer intercept-line semantics and imported-SDJ edge cases

- `views`
  Current status: scene views compile into CesiumJS viewer buttons and target/position camera actions with basic range/duration support
  Missing: full camera program semantics and richer runtime hooks

- `cameraView`
  Current status: camera-view objects compile into CesiumJS viewer buttons and target/position/orientation camera actions with basic range/duration support
  Missing: full SDJ camera program semantics and richer runtime hooks

- `ellipsoid` overlay geometry
  Current status: typed ellipsoid overlays compile to CZML ellipsoid packets with radii and styling
  Missing: richer ellipsoid authoring helpers and imported-SDJ edge cases

- `sphere` overlay geometry
  Current status: typed sphere overlays compile to CZML ellipsoid packets with equal radii and styling
  Missing: richer sphere authoring helpers and imported-SDJ edge cases

- `uncertaintyEllipsoid` overlay geometry
  Current status: typed uncertainty ellipsoid overlays compile to CZML ellipsoid packets with radii, partitions, and styling
  Missing: richer uncertainty ellipsoid authoring helpers and imported-SDJ edge cases

- `covarianceEllipse` overlay geometry
  Current status: typed covariance ellipse overlays compile to CZML ellipse packets with ellipse geometry metadata preserved in packet properties
  Missing: richer covariance ellipse authoring helpers and imported-SDJ edge cases

- `particleSystem` overlay geometry
  Current status: typed particle system overlays compile to CZML particleSystem packets with emitter, rate, image, size, and color metadata preserved
  Missing: richer particle system authoring helpers and imported-SDJ edge cases

- `voxel`
  Current status: voxel overlays compile to a CZML box approximation with voxel metadata preserved in packet properties and round-trip back into the typed scene model
  Missing: Cesium primitive generation and runtime wiring

- `custom`
  Current status: custom objects preserve arbitrary payloads, round-trip through scene JSON/CZML, and can dispatch through the Cesium overlay emitter registry
  Current status in SIMDIS/SOAP: custom objects are preserved in the bundle files as typed opaque records
  Missing: standardized imported-SDJ custom type mapping and renderer/runtime contracts

- `runtime`
  Current status: runtime objects preserve arbitrary payloads, round-trip through scene JSON/CZML, and are preserved in SIMDIS/SOAP bundle files as opaque records
  Missing: standardized imported-SDJ runtime object mapping and renderer/runtime contracts

- `terrainSurface`
  Current status: terrain surface objects are explicit typed scene objects, preserve renderer/runtime payloads, and round-trip through scene JSON/CZML and SIMDIS/SOAP bundle files as opaque records
  Missing: native Cesium terrain surface primitive and standardized imported-SDJ attachment contract

- `customMesh`
  Current status: custom mesh objects are explicit typed scene objects, preserve renderer/runtime payloads, and round-trip through scene JSON/CZML and SIMDIS/SOAP bundle files as opaque records
  Missing: native Cesium custom mesh primitive and standardized imported-SDJ attachment contract

- `clippingPlane`
  Current status: clipping plane objects are explicit typed scene objects, preserve renderer/runtime payloads, and round-trip through scene JSON/CZML and SIMDIS/SOAP bundle files as opaque records
  Missing: native Cesium clipping-plane collection and standardized imported-SDJ attachment contract

- `clippingPolygon`
  Current status: clipping polygon objects are explicit typed scene objects, preserve renderer/runtime payloads, and round-trip through scene JSON/CZML and SIMDIS/SOAP bundle files as opaque records
  Missing: native Cesium clipping-polygon collection and standardized imported-SDJ attachment contract

- `classificationVolume`
  Current status: classification volume objects are explicit typed scene objects, preserve renderer/runtime payloads, and round-trip through scene JSON/CZML and SIMDIS/SOAP bundle files as opaque records
  Missing: native Cesium classification-volume primitive and standardized imported-SDJ attachment contract

- `customShader`
  Current status: custom shader objects are explicit typed scene objects, preserve renderer/runtime payloads, and round-trip through scene JSON/CZML and SIMDIS/SOAP bundle files as opaque records
  Missing: native Cesium custom shader execution and standardized imported-SDJ attachment contract

- `postProcessStage`
  Current status: post-process stage objects are explicit typed scene objects, preserve renderer/runtime payloads, and round-trip through scene JSON/CZML and SIMDIS/SOAP bundle files as opaque records
  Missing: native Cesium post-process stage execution and standardized imported-SDJ attachment contract

- sensor entities
  Current status: sensor category can render as normal entity, billboard, or model
  Missing: richer sensor entity semantics and runtime hooks

- viewer/runtime integration
  Current status: generated HTML shell loads CZML into CesiumJS and can render scene-view and camera-view controls
  Missing: loader module and richer runtime hooks

### Not Wired Into the Python Scene Model Yet

- specialized imported renderer/attachment subclasses such as `customPrimitive`, `composite`, `atmosphere`, `czmlDataSource`, `dataSource`, `geoJsonDataSource`, `kmlDataSource`, `skyBox`, `videoPlane`, and `primitiveMesh`

### Not Wired Into Cesium Output Yet Even If Added To Scene Model

- authored `analysis`
  Current status: analysis metadata is preserved on the CZML document packet and surfaced in the Cesium viewer metadata panel
  Missing: richer Cesium-side runtime use of the analysis payload
- authored `presentation`
  Current status: presentation metadata is preserved on the CZML document packet and surfaced in the Cesium viewer metadata panel
  Missing: richer Cesium-side runtime use of the presentation payload
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
  `sector2d`, `sectorVolume`, `hemisphere`, `sphericalCap`, `keyhole`, `bearingFan`, `frustum`, `conicSensor`, `rectangularSensor`, `customPatternSensor`
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
- Cesium overlay emitters can be registered for custom geometry families without editing the core dispatch path
- custom scene objects preserve renderer-specific payloads as a typed escape hatch
- runtime scene objects preserve imported renderer-specific payloads as a typed escape hatch
- custom scene objects survive SIMDIS/SOAP bundle serialization as opaque records
- runtime scene objects survive SIMDIS/SOAP bundle serialization as opaque records

This is a usable library shape for:

- validating the current message and scene subset
- generating current CZML output
- embedding current compile helpers in another Python project

### What Is Not Ready Yet

It is not yet a sufficiently complete SDJ library if another project expects:

- broad imported-SDJ object support
- richer cameraView programs and camera integration
- analysis or presentation runtime use beyond metadata passthrough
- voxel primitive generation and runtime wiring
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
5. Add richer scene `cameraView` programs and compile them into runtime camera behavior.
6. Add scene-level fixtures that exercise imported SDJ families incrementally:
   - `track` / `path`
   - sensor volumes
   - vectors

## Practical Conclusion

The current codebase is modular enough to be reused as a narrow library.
It is not yet complete enough to be the SDJ Cesium library implied by the
imported `sdj_v0_4` schema and workbench.
