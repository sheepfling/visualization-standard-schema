# SDJ Survey / Exposé / Portfolio v0.5

This document is the coverage portfolio for Spatial Display JSON. It is intended to drive schema design, example generation, compiler implementation, and regression testing across Cesium, SIMDIS, SOAP, and future renderers.

## Coverage legend

- `strong`: native or near-native target exists and should be first-class.
- `partial`: supported with fallback, caveat, semantic conversion, or lossy export.
- `reserved`: represented in schema/profile but runtime adapter is not done.
- `weak`: approximate or metadata-only export.
- `unsupported`: intentionally out of scope or blocked until backend extension exists.

## Top-level SDJ profiles

### `sdj-core`
Document identity, units, clock, layers, assets, materials, common object envelope, extension policy.

### `sdj-temporal-properties`
Constant, interval, sampled, reference, computed, and callback-like property descriptions.

### `sdj-frames-and-pose`
Coordinate frames and transform conventions for Earth-fixed, inertial, ENU, body, model, and platform-relative data.

### `sdj-czml-parity`
Entity-like objects corresponding to historical CZML and Cesium Entity API coverage.
Object kinds: `point`, `billboard`, `label`, `polyline`, `polygon`, `rectangle`, `ellipse`, `circle`, `box`, `cylinder`, `cone`, `ellipsoid`, `sphere`, `wall`, `corridor`, `polylineVolume`, `plane`, `model`, `path`, `track`

### `sdj-cesium-advanced`
Modern CesiumJS scene, tileset, model, primitive, clipping, shader, voxel, and effect features not covered by old CZML.
Object kinds: `tileset`, `gaussianSplatTileset`, `pointCloudTileset`, `photogrammetryTileset`, `tilesetStyle`, `customShader`, `voxel`, `particleSystem`, `postProcessStage`, `clippingPlane`, `clippingPolygon`, `classificationPrimitive`, `classificationVolume`, `groundPrimitive`, `groundPolyline`, `cloudCollection`, `atmosphere`, `skyBox`, `imageryLayer`, `terrain`, `dataSource`

### `sdj-tactical-geometry`
Mission/tactical volumes, sectors, fans, keyholes, coverage and uncertainty geometry.
Object kinds: `sector2d`, `sectorVolume`, `keyhole`, `rangeRing`, `bearingFan`, `hemisphere`, `sphericalCap`, `frustum`, `fan`, `conicSensor`, `rectangularSensor`, `customPatternSensor`, `sensorSwath`, `footprint`, `antennaPattern`, `uncertaintyEllipsoid`, `covarianceEllipse`

### `sdj-trajectory-diagnostics`
Tracks plus derived or authored vector/line diagnostics.
Object kinds: `velocityVector`, `accelerationVector`, `bodyAxes`, `principalAxes`, `lineOfSight`, `relativeLine`, `interceptLine`, `tetherLine`, `formationLine`, `predictionPath`, `trackHistory`

### `sdj-analysis-products`
Analysis results that may render as overlays, reports, plots, tables, swaths, access intervals, or backend-native analysis objects.
Analysis kinds: `accessIntervals`, `lineOfSightSamples`, `rfLinkBudget`, `coverageGrid`, `sensorSwath`, `closeApproach`, `rangeReport`, `rangePlot`, `platformDataTable`, `communicationLink`, `parametricStudy`, `deltaV`, `isochrones`, `contours`

### `sdj-presentation`
View, viewport, palette, slide, presentation, camera action, popups, banners, HUDs, movies, and reports.
Presentation kinds: `view`, `viewport`, `palette`, `slide`, `presentation`, `cameraAction`, `bookmark`, `popup`, `banner`, `hudOverlay`, `movie`, `reportView`, `plotView`, `dataView`

### `sdj-backend-bindings`
Capability matrix, rendererHints, native escape hatches, diagnostics, artifact manifests, and target compiler options for Cesium, SIMDIS, SOAP, Unreal, TGx, and future renderers.

## Feature portfolio
### CZML parity / Entity core
| Feature | SDJ kind | Schema | Example | Cesium | SIMDIS | SOAP | Priority |
|---|---|---:|---:|---:|---:|---:|---:|
| Point marker / pixel marker | `point` | existing | existing | strong | strong | partial | P0 |
| Screen-facing image/icon | `billboard` | existing | existing | strong | partial | partial | P0 |
| Screen-facing text label | `label` | existing | existing | strong | strong | partial | P0 |
| 3D line string | `polyline` | existing | existing | strong | strong | strong | P0 |
| Time-dynamic trail/lead path | `path` | existing | existing | strong | partial | partial | P0 |
| Surface or extruded polygon | `polygon` | existing | existing | strong | strong | strong | P0 |
| Cartographic rectangle | `rectangle` | existing | existing | strong | partial | partial | P0 |
| Ellipse on ellipsoid or at height | `ellipse` | existing | existing | strong | strong | strong | P0 |
| Circle as ellipse specialization | `circle` | existing | existing | strong | strong | strong | P0 |
| Oriented box volume | `box` | existing | existing | strong | partial | partial | P0 |
| Cylinder volume | `cylinder` | existing | existing | strong | partial | partial | P0 |
| Cone as cylinder specialization | `cone` | existing | existing | strong | partial | partial | P0 |
| Ellipsoid/sphere/cap shell | `ellipsoid` | existing | existing | strong | partial | partial | P0 |
| Sphere specialization | `sphere` | existing | existing | strong | partial | partial | P0 |
| Vertical wall surface | `wall` | existing | existing | strong | partial | partial | P0 |
| Corridor / buffered path | `corridor` | existing | existing | strong | partial | partial | P0 |
| Swept cross-section tube/volume | `polylineVolume` | existing | existing | strong | partial | partial | P0 |
| Plane graphic | `plane` | existing | existing | strong | partial | partial | P0 |
| GLB/glTF model entity | `model` | existing | existing | strong | strong | strong | P0 |
| Moving platform / sampled object | `track` | existing | existing | strong | strong | strong | P0 |

### Temporal/frames/properties
| Feature | SDJ kind | Schema | Example | Cesium | SIMDIS | SOAP | Priority |
|---|---|---:|---:|---:|---:|---:|---:|
| Constant property value | `constantProperty` | proposed | mixed | strong | strong | strong | P0 |
| Interval-bounded values | `intervalProperty` | proposed | mixed | strong | strong | strong | P0 |
| Sampled scalar/vector/color/property | `sampledProperty` | existing | mixed | strong | strong | strong | P0 |
| Property reference to another SDJ object | `referenceProperty` | existing | mixed | strong | strong | strong | P0 |
| Derived properties such as velocity/acceleration/orientation | `computedProperty` | existing | mixed | strong | strong | strong | P0 |
| Time interval visibility/existence | `availability` | proposed | mixed | strong | strong | strong | P0 |
| lon/lat/height position | `cartographicDegrees` | existing | mixed | strong | strong | strong | P0 |
| Earth-fixed Cartesian position | `ecefMeters` | existing | mixed | strong | strong | strong | P0 |
| Local tangent-plane coordinate | `enuMeters` | proposed | mixed | strong | strong | strong | P0 |
| Inertial/reference-frame state | `inertialFrame` | proposed | mixed | partial | strong | strong | P0 |
| Body axes and body-relative transforms | `bodyFrame` | proposed | mixed | strong | strong | strong | P0 |
| GLB/glTF orientation and origin correction | `modelFrameCorrection` | existing | mixed | strong | strong | strong | P0 |

### Modern assets / tiles / models
| Feature | SDJ kind | Schema | Example | Cesium | SIMDIS | SOAP | Priority |
|---|---|---:|---:|---:|---:|---:|---:|
| 3D Tileset asset | `tileset` | existing | existing | strong | partial | partial | P0 |
| Gaussian splat tileset asset/object | `gaussianSplatTileset` | partial | existing-hidden | partial | weak | weak | P0 |
| 3D Tiles point cloud | `pointCloudTileset` | existing | existing-hidden | strong | partial | partial | P1 |
| Photogrammetry / reality mesh tileset | `photogrammetryTileset` | proposed | needed | strong | partial | partial | P1 |
| Feature styling/filtering for 3D Tiles | `cesium3DTileStyle` | proposed | needed | reserved | weak | weak | P0 |
| 3D Tiles feature metadata/picking | `featureMetadata` | proposed | needed | reserved | weak | partial | P1 |
| Custom shader attached to model/tileset | `customShader` | proposed | needed | reserved | unsupported | partial | P0 |
| PBR material via glTF/GLB | `pbrAsset` | partial | needed | strong | partial | strong | P1 |
| Model animations | `modelAnimation` | partial | needed | partial | partial | strong | P1 |
| Model articulations/node transforms | `modelArticulation` | partial | needed | reserved | partial | strong | P1 |
| IBL/environment map model controls | `imageBasedLighting` | proposed | needed | reserved | unsupported | partial | P2 |

### Primitive / clipping / classification
| Feature | SDJ kind | Schema | Example | Cesium | SIMDIS | SOAP | Priority |
|---|---|---:|---:|---:|---:|---:|---:|
| Explicit geometry primitive with vertices/indices | `customPrimitive` | existing | existing-hidden | strong | partial | partial | P1 |
| Generated or explicit custom mesh | `primitiveMesh` | existing | needed | strong | partial | partial | P1 |
| Terrain-draped primitive | `groundPrimitive` | proposed | needed | reserved | partial | partial | P0 |
| Terrain/tiles draped polyline | `groundPolyline` | proposed | needed | reserved | strong | partial | P0 |
| Classifies terrain/3D Tiles | `classificationPrimitive` | existing | needed | reserved | partial | weak | P0 |
| Semantic classification volume | `classificationVolume` | existing | needed | reserved | partial | weak | P1 |
| Planar clipping attachment | `clippingPlane` | existing | existing-hidden | reserved | weak | partial | P0 |
| Cartographic clipping region | `clippingPolygon` | existing | existing-hidden | reserved | weak | partial | P0 |
| Primitive appearance/material definitions | `appearanceMaterial` | proposed | needed | partial | partial | partial | P1 |
| Batched geometry instances | `geometryInstanceBatching` | proposed | needed | reserved | partial | weak | P1 |

### Tactical geometry / sensors
| Feature | SDJ kind | Schema | Example | Cesium | SIMDIS | SOAP | Priority |
|---|---|---:|---:|---:|---:|---:|---:|
| 2D sector/fan polygon | `sector2d` | existing | existing | strong | strong | partial | P1 |
| 3D spherical sector volume | `sectorVolume` | existing | existing | strong | partial | partial | P1 |
| Inner/outer keyhole wedge | `keyhole` | existing | existing | strong | partial | partial | P1 |
| Range ring/circle | `rangeRing` | existing | existing | strong | strong | partial | P1 |
| Bearing fan | `bearingFan` | existing | existing | strong | strong | partial | P1 |
| Hemisphere/dome | `hemisphere` | existing | existing | strong | partial | partial | P1 |
| Spherical cap/shell | `sphericalCap` | existing | existing | strong | partial | partial | P1 |
| Rectangular frustum/FOV | `frustum` | existing | existing | strong | partial | strong | P1 |
| Generic fan | `fan` | existing | existing-hidden | partial | strong | partial | P0 |
| Conic sensor/FOV | `conicSensor` | existing | existing-hidden | partial | strong | strong | P0 |
| Rectangular sensor/FOV | `rectangularSensor` | existing | existing-hidden | partial | strong | strong | P0 |
| Pattern/antenna sensor | `customPatternSensor` | existing | existing-hidden | partial | strong | partial | P0 |
| Sensor swath footprint | `sensorSwath` | proposed | needed | reserved | strong | strong | P0 |
| Ground footprint | `footprint` | proposed | needed | reserved | partial | strong | P1 |
| Antenna pattern/lobes | `antennaPattern` | proposed | needed | reserved | strong | strong | P0 |
| RF propagation/result volume | `rfPropagationVolume` | proposed | needed | reserved | strong | strong | P0 |
| SIMDIS-like gate | `gate` | proposed | needed | reserved | strong | partial | P0 |
| Laser/ray sensor | `laser` | proposed | needed | reserved | strong | partial | P0 |
| Line of bearing | `lob` | proposed | needed | reserved | strong | partial | P0 |
| Image/video projector | `projector` | proposed | needed | reserved | strong | partial | P0 |
| 3D uncertainty | `uncertaintyEllipsoid` | existing | existing | strong | partial | partial | P1 |
| 2D covariance ellipse | `covarianceEllipse` | existing | existing | strong | partial | partial | P1 |

### Trajectory diagnostics
| Feature | SDJ kind | Schema | Example | Cesium | SIMDIS | SOAP | Priority |
|---|---|---:|---:|---:|---:|---:|---:|
| Velocity vector overlay | `velocityVector` | existing | existing | strong | strong | strong | P1 |
| Acceleration vector overlay | `accelerationVector` | existing | existing | strong | strong | strong | P1 |
| Jerk vector overlay | `jerkVector` | proposed | needed | reserved | strong | strong | P1 |
| Body-frame x/y/z axes | `bodyAxes` | existing | existing | strong | strong | partial | P1 |
| Covariance/principal component axes | `principalAxes` | existing | existing | strong | strong | partial | P1 |
| Line of sight link | `lineOfSight` | existing | existing | strong | strong | strong | P1 |
| Relative/reference line | `relativeLine` | existing | existing | strong | strong | strong | P1 |
| Predicted intercept/closure line | `interceptLine` | existing | existing | strong | strong | strong | P1 |
| Tether/attachment line | `tetherLine` | proposed | needed | reserved | strong | strong | P1 |
| Formation geometry | `formationLine` | proposed | needed | reserved | strong | strong | P1 |
| Predicted future path | `predictionPath` | proposed | needed | reserved | strong | strong | P1 |
| Historical track trail | `trackHistory` | existing | existing | strong | strong | strong | P1 |
| Time tick marks along path | `timeTicks` | proposed | needed | reserved | strong | strong | P1 |
| Burn/maneuver event marker | `maneuverMarker` | proposed | needed | reserved | strong | strong | P1 |

### Scene environment / effects
| Feature | SDJ kind | Schema | Example | Cesium | SIMDIS | SOAP | Priority |
|---|---|---:|---:|---:|---:|---:|---:|
| Terrain provider/reference | `terrain` | existing | needed | reserved | partial | partial | P0 |
| Imagery provider/layer | `imageryLayer` | existing | needed | reserved | partial | partial | P0 |
| Globe options | `globe` | proposed | needed | reserved | partial | partial | P2 |
| Skybox | `skyBox` | existing | needed | reserved | partial | partial | P2 |
| Atmosphere/sky atmosphere | `atmosphere` | existing | needed | reserved | partial | partial | P2 |
| Fog | `fog` | proposed | needed | reserved | partial | partial | P2 |
| Sun/light/shadows | `lighting` | proposed | needed | reserved | partial | partial | P2 |
| Shadow modes | `shadows` | proposed | needed | reserved | partial | partial | P2 |
| Clouds | `cloudCollection` | existing | needed | reserved | partial | partial | P0 |
| Particle effects | `particleSystem` | existing | existing-hidden | strong | partial | partial | P2 |
| Post-process shader stage | `postProcessStage` | existing | needed | reserved | partial | partial | P0 |
| Debug inspector/helpers | `debugInspector` | existing | needed | reserved | partial | partial | P2 |
| Video textured plane | `videoPlane` | existing | needed | reserved | partial | partial | P2 |
| Panorama/cube map panorama | `panorama` | existing | needed | reserved | partial | partial | P2 |

### External data sources / interop
| Feature | SDJ kind | Schema | Example | Cesium | SIMDIS | SOAP | Priority |
|---|---|---:|---:|---:|---:|---:|---:|
| Import/load external CZML | `czmlDataSource` | existing | needed | reserved | partial | partial | P1 |
| Import/load GeoJSON | `geoJsonDataSource` | existing | needed | reserved | partial | partial | P1 |
| Import/load KML/KMZ | `kmlDataSource` | existing | needed | reserved | partial | partial | P1 |
| Custom entity data source | `customDataSource` | existing | needed | reserved | partial | partial | P1 |
| Collection of data source references | `dataSourceCollection` | existing | needed | reserved | partial | partial | P1 |
| Asset manifests for backend bundles | `assetManifest` | existing | needed | reserved | partial | partial | P1 |

### Analysis products
| Feature | SDJ kind | Schema | Example | Cesium | SIMDIS | SOAP | Priority |
|---|---|---:|---:|---:|---:|---:|---:|
| Visibility/access intervals | `accessIntervals` | existing | mixed | partial | strong | strong | P1 |
| LOS sampled results | `lineOfSightSamples` | existing | mixed | partial | strong | strong | P1 |
| RF link budget result | `rfLinkBudget` | existing | mixed | partial | strong | strong | P1 |
| Coverage grid/raster/vector result | `coverageGrid` | existing | mixed | partial | strong | strong | P1 |
| Sensor swath analysis | `sensorSwath` | existing | mixed | partial | strong | strong | P1 |
| Closest approach report | `closeApproach` | existing | mixed | partial | strong | strong | P1 |
| Range report | `rangeReport` | existing | mixed | partial | strong | strong | P1 |
| Range plot | `rangePlot` | existing | mixed | partial | strong | strong | P1 |
| Platform/state data table | `platformDataTable` | existing | mixed | partial | strong | strong | P1 |
| Comms link | `communicationLink` | existing | mixed | partial | strong | strong | P1 |
| Parametric study | `parametricStudy` | existing | mixed | partial | strong | strong | P1 |
| Delta-v/maneuver output | `deltaV` | proposed | mixed | partial | strong | strong | P1 |
| Isochrone regions | `isochrones` | proposed | mixed | partial | strong | strong | P1 |
| Contour output | `contours` | proposed | mixed | partial | strong | strong | P1 |

### Presentation / debrief UI
| Feature | SDJ kind | Schema | Example | Cesium | SIMDIS | SOAP | Priority |
|---|---|---:|---:|---:|---:|---:|---:|
| World/camera view | `view` | existing | mixed | partial | strong | strong | P1 |
| Viewport inside a UI/palette | `viewport` | proposed | mixed | partial | strong | strong | P1 |
| Multi-view layout | `palette` | proposed | mixed | partial | strong | strong | P1 |
| Time-bounded presentation slide | `slide` | existing | mixed | partial | strong | strong | P1 |
| Presentation sequence | `presentation` | existing | mixed | partial | strong | strong | P1 |
| Scripted camera action | `cameraAction` | existing | mixed | partial | strong | strong | P1 |
| Named camera/time bookmark | `bookmark` | existing | mixed | partial | strong | strong | P1 |
| Popup/hover details | `popup` | existing | mixed | partial | strong | strong | P1 |
| Classification/banner overlay | `banner` | existing | mixed | partial | strong | strong | P1 |
| Screen-space HUD overlay | `hudOverlay` | proposed | mixed | partial | strong | strong | P1 |
| Movie/render export | `movie` | proposed | mixed | partial | strong | strong | P1 |
| Report view | `reportView` | existing | mixed | partial | strong | strong | P1 |
| Plot view | `plotView` | existing | mixed | partial | strong | strong | P1 |
| Data table view | `dataView` | existing | mixed | partial | strong | strong | P1 |

### Backend bindings / compiler contracts
| Feature | SDJ kind | Schema | Example | Cesium | SIMDIS | SOAP | Priority |
|---|---|---:|---:|---:|---:|---:|---:|
| Preferred backends and fallbacks | `rendererHints` | existing | mixed | strong | strong | strong | P0 |
| Raw native per-backend escape hatch | `backendNative` | proposed | mixed | strong | strong | strong | P0 |
| Backend support matrix | `capabilityMatrix` | existing | mixed | strong | strong | strong | P0 |
| Lossiness/error/warning diagnostics | `compileDiagnostics` | existing | mixed | strong | strong | strong | P0 |
| Output bundle manifest | `artifactManifest` | existing | mixed | strong | strong | strong | P0 |
| Future Unreal binding | `unrealBinding` | proposed | mixed | strong | strong | strong | P3 |
| Future TGx binding | `tgxBinding` | proposed | mixed | strong | strong | strong | P3 |

## Definition of done per feature

A feature is considered covered only when it has all of the following:

1. Schema definition or module entry.
2. One minimal example object.
3. One full example object with style/time/pose/asset variation when relevant.
4. Semantic validator rule for required fields and target attachments.
5. Cesium compiler target or explicit reserved diagnostic.
6. Cesium runtime smoke test if the target is renderable.
7. SIMDIS artifact mapping with lossiness status.
8. SOAP artifact mapping with lossiness status.
9. Workbench inspector display.
10. Round-trip/export fixture when applicable.

## Immediate v0.5 implementation priorities

1. Promote `gaussianSplatTileset` from asset-only to asset + object alias with splat-specific diagnostics.
2. Implement target attachment graph: `tilesetStyle`, `customShader`, `clippingPlane`, `clippingPolygon`, `classificationPrimitive`.
3. Implement scene provider adapters: `terrain`, `imageryLayer`, `skyBox`, `atmosphere`, `cloudCollection`.
4. Implement data-source bridge: `czmlDataSource`, `geoJsonDataSource`, `kmlDataSource`.
5. Expand material/property parity: polyline glow/outline/arrow, grid/stripe/checker/image materials, distance display, clamp/height reference, classification type.
6. Expand moving primitive support: dynamic model matrices for sector volumes, keyholes, frustums, domes, and meshes.
