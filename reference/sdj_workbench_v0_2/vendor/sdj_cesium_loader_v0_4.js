(function attachSpatialDisplayJson(global) {
  "use strict";

  /**
   * @typedef {Record<string, unknown>} JsonObject
   * @typedef {{viewer: unknown, Cesium: typeof globalThis.Cesium, scene: JsonObject, assets: Record<string, JsonObject>, entities: Map<string, unknown>, primitives: Map<string, unknown>, warnings: string[]}} LoaderContext
   */

  /** @type {Record<string, number[]>} */
  const AXIS_COLORS = {
    x: [1, 0, 0, 1],
    y: [0, 1, 0, 1],
    z: [0.2, 0.4, 1, 1],
    principal0: [1, 0, 1, 1],
    principal1: [0, 1, 1, 1],
    principal2: [1, 1, 1, 1]
  };

  /**
   * Loads a Spatial Display JSON document into a Cesium Viewer.
   *
   * @param {unknown} viewer
   * @param {JsonObject} scene
   * @param {JsonObject} [options]
   * @returns {Promise<{entities: Map<string, unknown>, primitives: Map<string, unknown>, warnings: string[]}>}
   */
  async function loadSpatialDisplayScene(viewer, scene, options) {
    const Cesium = getCesium();
    const context = {
      viewer,
      Cesium,
      scene,
      assets: asObject(scene.assets),
      entities: new Map(),
      primitives: new Map(),
      warnings: []
    };

    applyClock(context, asObject(scene.clock));
    applySceneEnvironment(context, asObject(scene.scene));

    const objects = Array.isArray(scene.objects) ? scene.objects : [];
    for (const object of objects) {
      await addObject(context, asObject(object), undefined);
    }

    if (options && options.zoomToFirstView === true) {
      applyInitialView(context);
    }

    return {
      entities: context.entities,
      primitives: context.primitives,
      warnings: context.warnings
    };
  }

  /**
   * @returns {typeof globalThis.Cesium}
   */
  function getCesium() {
    const Cesium = global.Cesium;
    if (!Cesium) {
      throw new Error("SpatialDisplayJson v0.4 requires Cesium to be loaded on globalThis.Cesium.");
    }
    return Cesium;
  }

  /**
   * @param {unknown} value
   * @returns {JsonObject}
   */
  function asObject(value) {
    if (value && typeof value === "object" && !Array.isArray(value)) {
      return /** @type {JsonObject} */ (value);
    }
    return {};
  }

  /**
   * @param {LoaderContext} context
   * @param {string} message
   * @returns {void}
   */
  function warn(context, message) {
    context.warnings.push(message);
    if (global.console && typeof global.console.warn === "function") {
      global.console.warn(message);
    }
  }

  /**
   * @param {LoaderContext} context
   * @param {JsonObject} clock
   * @returns {void}
   */
  function applyClock(context, clock) {
    const Cesium = context.Cesium;
    const viewer = /** @type {any} */ (context.viewer);
    if (!clock || Object.keys(clock).length === 0) {
      return;
    }

    if (typeof clock.startTime === "string") {
      viewer.clock.startTime = Cesium.JulianDate.fromIso8601(clock.startTime);
    }
    if (typeof clock.stopTime === "string") {
      viewer.clock.stopTime = Cesium.JulianDate.fromIso8601(clock.stopTime);
    }
    if (typeof clock.currentTime === "string") {
      viewer.clock.currentTime = Cesium.JulianDate.fromIso8601(clock.currentTime);
    }
    if (typeof clock.multiplier === "number") {
      viewer.clock.multiplier = clock.multiplier;
    }
    if (typeof clock.shouldAnimate === "boolean") {
      viewer.clock.shouldAnimate = clock.shouldAnimate;
    }
    if (typeof clock.clockRange === "string") {
      viewer.clock.clockRange = enumValue(Cesium.ClockRange, clock.clockRange, {
        unbounded: "UNBOUNDED",
        clamped: "CLAMPED",
        loopStop: "LOOP_STOP"
      });
    }
    if (typeof clock.clockStep === "string") {
      viewer.clock.clockStep = enumValue(Cesium.ClockStep, clock.clockStep, {
        systemClock: "SYSTEM_CLOCK",
        systemClockMultiplier: "SYSTEM_CLOCK_MULTIPLIER",
        tickDependent: "TICK_DEPENDENT"
      });
    }
    if (viewer.timeline && viewer.clock.startTime && viewer.clock.stopTime) {
      viewer.timeline.zoomTo(viewer.clock.startTime, viewer.clock.stopTime);
    }
  }

  /**
   * @param {LoaderContext} context
   * @param {JsonObject} object
   * @param {string | undefined} parentId
   * @returns {Promise<void>}
   */
  async function addObject(context, object, parentId) {
    const id = String(object.id || "");
    const kind = String(object.kind || "");
    if (!id || !kind) {
      warn(context, "Skipping object without id or kind.");
      return;
    }

    if (propertyToBoolean(object.show, true) === false) {
      return;
    }

    /** @type {unknown} */
    let created;
    if (kind === "tileset") {
      created = await addTileset(context, object);
    } else if (kind === "track") {
      created = addTrack(context, object);
    } else if (kind === "model") {
      created = addModel(context, object);
    } else if (kind === "point") {
      created = addPoint(context, object);
    } else if (kind === "label") {
      created = addLabel(context, object);
    } else if (kind === "billboard") {
      created = addBillboard(context, object);
    } else if (kind === "plane") {
      created = addPlane(context, object);
    } else if (kind === "frustum") {
      created = addTacticalPrimitive(context, object, kind);
    } else if (kind === "particleSystem") {
      created = addParticleSystem(context, object);
    } else if (kind === "polyline" || kind === "path") {
      created = addPolyline(context, object);
    } else if (kind === "polygon") {
      created = addPolygon(context, object);
    } else if (kind === "rectangle") {
      created = addRectangle(context, object);
    } else if (kind === "ellipse" || kind === "circle" || kind === "rangeRing" || kind === "covarianceEllipse") {
      created = addEllipse(context, object);
    } else if (kind === "box") {
      created = addBox(context, object);
    } else if (kind === "cylinder" || kind === "cone") {
      created = addCylinder(context, object, kind);
    } else if (kind === "terrainSurface" || kind === "customMesh") {
      created = addImportedSceneObject(context, object, kind);
    } else if (kind === "clippingPlane" || kind === "clippingPolygon" || kind === "classificationVolume") {
      created = addImportedSceneObject(context, object, kind);
    } else if (kind === "classificationPrimitive") {
      created = addImportedSceneObject(context, object, kind);
    } else if (kind === "customShader" || kind === "postProcessStage" || kind === "composite") {
      created = addImportedSceneObject(context, object, kind);
    } else if (kind === "czmlDataSource" || kind === "dataSource" || kind === "geoJsonDataSource" || kind === "kmlDataSource") {
      created = addImportedSceneObject(context, object, kind);
    } else if (kind === "skyBox" || kind === "atmosphere" || kind === "terrain" || kind === "tilesetStyle" || kind === "cloudCollection" || kind === "groundPolyline" || kind === "groundPrimitive" || kind === "panorama") {
      created = addImportedSceneObject(context, object, kind);
    } else if (kind === "cameraView" || kind === "debugInspector") {
      created = addImportedSceneObject(context, object, kind);
    } else if (kind === "videoPlane") {
      created = addImportedSceneObject(context, object, kind);
    } else if (kind === "conicSensor" || kind === "rectangularSensor" || kind === "customPatternSensor") {
      created = addImportedSceneObject(context, object, kind);
    } else if (kind === "hemisphere" || kind === "sphericalCap" || kind === "sectorVolume" || kind === "keyhole") {
      created = addTacticalOrFallback(context, object, kind);
    } else if (kind === "ellipsoid" || kind === "sphere" || kind === "uncertaintyEllipsoid") {
      created = addEllipsoidLike(context, object, kind);
    } else if (kind === "wall") {
      created = addWall(context, object);
    } else if (kind === "corridor") {
      created = addCorridor(context, object);
    } else if (kind === "polylineVolume") {
      created = addPolylineVolume(context, object);
    } else if (kind === "sector2d" || kind === "bearingFan" || kind === "fan") {
      created = addSector2d(context, object);
    } else if (kind === "lineOfSight" || kind === "relativeLine" || kind === "interceptLine") {
      created = addLineBetween(context, object);
    } else if (kind === "velocityVector" || kind === "accelerationVector" || kind === "vector") {
      created = addDerivedVector(context, object, kind);
    } else if (kind === "bodyAxes" || kind === "principalAxes") {
      created = addAxes(context, object, kind);
    } else if (kind === "customPrimitive" || kind === "primitiveMesh") {
      created = addCustomPrimitive(context, object);
    } else {
      created = addImportedSceneObject(context, object, kind);
    }

    if (created) {
      if (parentId) {
        const parent = context.entities.get(parentId);
        if (parent && "parent" in /** @type {any} */ (created)) {
          /** @type {any} */ (created).parent = parent;
        }
      }
      if ("id" in /** @type {any} */ (created)) {
        context.entities.set(id, created);
      }
    }

    const overlays = Array.isArray(object.overlays) ? object.overlays : [];
    for (const overlay of overlays) {
      await addObject(context, asObject(overlay), id);
    }
  }

  /**
   * @param {LoaderContext} context
   * @param {JsonObject} object
   * @returns {JsonObject}
   */
  function entityBase(context, object) {
    const entity = {
      id: String(object.id),
      name: typeof object.name === "string" ? object.name : undefined,
      description: typeof object.description === "string" ? object.description : undefined,
      show: propertyToBoolean(object.show, true),
      availability: buildAvailability(context, object.availability),
      properties: asObject(object.properties)
    };

    const pose = asObject(object.pose);
    const position = buildPositionProperty(context, pose.position);
    if (position) {
      entity.position = position;
    }

    const orientation = buildOrientationProperty(context, pose.orientation, position);
    if (orientation) {
      entity.orientation = orientation;
    }

    return entity;
  }

  /**
   * @param {LoaderContext} context
   * @param {JsonObject} object
   * @returns {unknown}
   */
  function addPoint(context, object) {
    const viewer = /** @type {any} */ (context.viewer);
    const entity = entityBase(context, object);
    entity.point = buildPointGraphic(context, asObject(object.point), asObject(object.style));
    if (object.label) {
      entity.label = buildLabelGraphic(context, asObject(object.label));
    }
    const created = viewer.entities.add(entity);
    context.entities.set(String(object.id), created);
    return created;
  }

  /**
   * @param {LoaderContext} context
   * @param {JsonObject} object
   * @param {string} kind
   * @returns {unknown}
   */
  function addImportedSceneObject(context, object, kind) {
    const viewer = /** @type {any} */ (context.viewer);
    const entity = entityBase(context, object);
    const properties = asObject(entity.properties);
    properties.importedKind = kind;
    entity.properties = properties;
    const created = viewer.entities.add(entity);
    context.entities.set(String(object.id), created);
    return created;
  }

  /**
   * @param {LoaderContext} context
   * @param {JsonObject} object
   * @returns {unknown}
   */
  function addLabel(context, object) {
    const viewer = /** @type {any} */ (context.viewer);
    const entity = entityBase(context, object);
    entity.label = buildLabelGraphic(context, asObject(object.label));
    const created = viewer.entities.add(entity);
    context.entities.set(String(object.id), created);
    return created;
  }

  /**
   * @param {LoaderContext} context
   * @param {JsonObject} object
   * @returns {unknown}
   */
  function addBillboard(context, object) {
    const viewer = /** @type {any} */ (context.viewer);
    const entity = entityBase(context, object);
    entity.billboard = buildBillboardGraphic(context, asObject(object.billboard));
    const created = viewer.entities.add(entity);
    context.entities.set(String(object.id), created);
    return created;
  }

  /**
   * @param {LoaderContext} context
   * @param {JsonObject} object
   * @returns {unknown}
   */
  function addTrack(context, object) {
    const viewer = /** @type {any} */ (context.viewer);
    const entity = entityBase(context, object);
    if (object.point) {
      entity.point = buildPointGraphic(context, asObject(object.point), asObject(object.style));
    }
    if (object.label) {
      entity.label = buildLabelGraphic(context, asObject(object.label));
    }
    if (object.path) {
      entity.path = buildPathGraphic(context, asObject(object.path), asObject(object.style));
    }
    const created = viewer.entities.add(entity);
    context.entities.set(String(object.id), created);
    return created;
  }

  /**
   * @param {LoaderContext} context
   * @param {JsonObject} object
   * @returns {unknown}
   */
  function addModel(context, object) {
    const viewer = /** @type {any} */ (context.viewer);
    const entity = entityBase(context, object);
    const model = asObject(object.model);
    const asset = resolveAsset(context, String(model.asset || object.asset || ""));
    const uri = typeof model.uri === "string" ? model.uri : asset.uri;

    const correction = asObject(model.modelFrameCorrection);
    if (entity.orientation && Object.keys(correction).length > 0) {
      entity.orientation = applyModelFrameCorrection(context, entity.orientation, correction);
    }

    entity.model = {
      uri,
      scale: unwrapNumber(model.scale, 1),
      minimumPixelSize: unwrapNumber(model.minimumPixelSize, undefined),
      maximumScale: unwrapNumber(model.maximumScale, undefined),
      runAnimations: propertyToBoolean(model.runAnimations, true),
      clampAnimations: propertyToBoolean(model.clampAnimations, true),
      silhouetteColor: buildColorProperty(context, model.silhouetteColor),
      silhouetteSize: unwrapNumber(model.silhouetteSize, undefined),
      color: buildColorProperty(context, model.color),
      colorBlendMode: enumValue(context.Cesium.ColorBlendMode, model.colorBlendMode, {
        highlight: "HIGHLIGHT",
        replace: "REPLACE",
        mix: "MIX"
      }),
      colorBlendAmount: unwrapNumber(model.colorBlendAmount, undefined),
      heightReference: heightReference(context, model.heightReference)
    };

    assignDefined(entity.model, asObject(model.rawCesium));

    const created = viewer.entities.add(entity);
    context.entities.set(String(object.id), created);
    return created;
  }

  /**
   * @param {LoaderContext} context
   * @param {JsonObject} object
   * @returns {Promise<unknown>}
   */
  async function addTileset(context, object) {
    const Cesium = context.Cesium;
    const viewer = /** @type {any} */ (context.viewer);
    const tilesetSpec = asObject(object.tileset);
    const asset = resolveAsset(context, String(tilesetSpec.asset || object.asset || ""));
    const ionAssetId = typeof tilesetSpec.ionAssetId === "number" ? tilesetSpec.ionAssetId : asset.ionAssetId;
    const uri = typeof tilesetSpec.uri === "string" ? tilesetSpec.uri : asset.uri;

    const options = {
      maximumScreenSpaceError: unwrapNumber(tilesetSpec.maximumScreenSpaceError, undefined),
      dynamicScreenSpaceError: propertyToBoolean(tilesetSpec.dynamicScreenSpaceError, undefined)
    };
    assignDefined(options, asObject(tilesetSpec.rawCesium));

    let tileset;
    if (typeof ionAssetId === "number") {
      tileset = await Cesium.Cesium3DTileset.fromIonAssetId(ionAssetId, removeUndefined(options));
    } else if (typeof uri === "string") {
      tileset = await Cesium.Cesium3DTileset.fromUrl(uri, removeUndefined(options));
    } else {
      warn(context, `Tileset ${String(object.id)} is missing uri or ionAssetId.`);
      return undefined;
    }

    tileset.show = propertyToBoolean(object.show, true);
    viewer.scene.primitives.add(tileset);
    context.primitives.set(String(object.id), tileset);
    return tileset;
  }


  /**
   * @param {LoaderContext} context
   * @param {JsonObject} scene
   * @returns {void}
   */
  function applySceneEnvironment(context, scene) {
    const Cesium = context.Cesium;
    const viewer = /** @type {any} */ (context.viewer);
    const imageryLayers = Array.isArray(scene.imageryLayers) ? scene.imageryLayers : [];
    for (const layerSpecValue of imageryLayers) {
      const layerSpec = asObject(layerSpecValue);
      const type = String(layerSpec.type || "");
      if (type === "urlTemplate" && typeof layerSpec.uri === "string") {
        const provider = new Cesium.UrlTemplateImageryProvider({ url: layerSpec.uri });
        const layer = viewer.imageryLayers.addImageryProvider(provider);
        layer.show = propertyToBoolean(layerSpec.show, true);
      }
    }
  }

  /**
   * @param {LoaderContext} context
   * @param {JsonObject} object
   * @returns {unknown}
   */
  function addPlane(context, object) {
    const Cesium = context.Cesium;
    const viewer = /** @type {any} */ (context.viewer);
    const entity = entityBase(context, object);
    const geometry = asObject(object.geometry);
    const style = asObject(object.style);
    const normalArray = array3(geometry.normal, [0, 0, 1]);
    const normal = new Cesium.Cartesian3(normalArray[0], normalArray[1], normalArray[2]);
    Cesium.Cartesian3.normalize(normal, normal);
    entity.plane = {
      plane: new Cesium.Plane(normal, unwrapNumber(geometry.distanceMeters, 0)),
      dimensions: new Cesium.Cartesian2(
        unwrapNumber(geometry.widthMeters, 1000),
        unwrapNumber(geometry.heightMeters, 1000)
      ),
      material: buildMaterial(context, asObject(style.material)),
      fill: propertyToBoolean(style.fill, true),
      outline: propertyToBoolean(style.outline, false),
      outlineColor: buildColorProperty(context, style.outlineColor)
    };
    const created = viewer.entities.add(entity);
    context.entities.set(String(object.id), created);
    return created;
  }

  /**
   * @param {LoaderContext} context
   * @param {JsonObject} object
   * @returns {unknown}
   */
  function addParticleSystem(context, object) {
    const Cesium = context.Cesium;
    const viewer = /** @type {any} */ (context.viewer);
    const geometry = asObject(object.geometry);
    const style = asObject(object.style);
    const asset = resolveAsset(context, String(geometry.asset || object.asset || ""));
    const pose = asObject(object.pose);
    const positionProperty = buildPositionProperty(context, pose.position);
    const position = getPropertyValue(context, positionProperty, currentTime(context));
    const image = typeof geometry.image === "string" ? geometry.image : asset.uri;
    const options = {
      show: propertyToBoolean(object.show, true),
      image,
      modelMatrix: position ? Cesium.Transforms.eastNorthUpToFixedFrame(position) : Cesium.Matrix4.IDENTITY,
      emitter: buildParticleEmitter(context, asObject(geometry.emitter)),
      emissionRate: unwrapNumber(geometry.emissionRate, undefined),
      lifetime: unwrapNumber(geometry.lifetimeSeconds, undefined),
      particleLife: unwrapNumber(geometry.particleLifeSeconds, undefined),
      minimumParticleLife: unwrapNumber(geometry.minimumParticleLifeSeconds, undefined),
      maximumParticleLife: unwrapNumber(geometry.maximumParticleLifeSeconds, undefined),
      speed: unwrapNumber(geometry.speedMetersPerSecond, undefined),
      minimumSpeed: unwrapNumber(geometry.minimumSpeedMetersPerSecond, undefined),
      maximumSpeed: unwrapNumber(geometry.maximumSpeedMetersPerSecond, undefined),
      scale: unwrapNumber(geometry.scale, undefined),
      startScale: unwrapNumber(geometry.startScale, undefined),
      endScale: unwrapNumber(geometry.endScale, undefined),
      startColor: buildColorProperty(context, style.startColor || geometry.startColor),
      endColor: buildColorProperty(context, style.endColor || geometry.endColor),
      imageSize: buildCartesian2(context, geometry.imageSize)
    };
    const system = new Cesium.ParticleSystem(removeUndefined(options));
    viewer.scene.primitives.add(system);
    context.primitives.set(String(object.id), system);
    return system;
  }

  /**
   * @param {LoaderContext} context
   * @param {JsonObject} emitter
   * @returns {unknown}
   */
  function buildParticleEmitter(context, emitter) {
    const Cesium = context.Cesium;
    const type = String(emitter.type || "circle");
    if (type === "box") {
      const dimensions = array3(emitter.dimensionsMeters, [1, 1, 1]);
      return new Cesium.BoxEmitter(new Cesium.Cartesian3(dimensions[0], dimensions[1], dimensions[2]));
    }
    if (type === "cone") {
      return new Cesium.ConeEmitter(degreesToRadians(unwrapNumber(emitter.angleDegrees, 30)));
    }
    if (type === "sphere") {
      return new Cesium.SphereEmitter(unwrapNumber(emitter.radiusMeters, 1));
    }
    return new Cesium.CircleEmitter(unwrapNumber(emitter.radiusMeters, 1));
  }

  /**
   * @param {LoaderContext} context
   * @param {unknown} value
   * @returns {unknown}
   */
  function buildCartesian2(context, value) {
    const Cesium = context.Cesium;
    if (!Array.isArray(value)) {
      return undefined;
    }
    const pair = array2(value, [1, 1]);
    return new Cesium.Cartesian2(pair[0], pair[1]);
  }

  /**
   * @param {LoaderContext} context
   * @param {JsonObject} object
   * @returns {unknown}
   */
  function addPolyline(context, object) {
    const viewer = /** @type {any} */ (context.viewer);
    const entity = entityBase(context, object);
    const geometry = asObject(object.geometry);
    const style = asObject(object.style);
    entity.polyline = {
      positions: buildPositionArray(context, geometry.positions),
      width: unwrapNumber(style.width, 2),
      material: buildMaterial(context, asObject(style.material)),
      clampToGround: Boolean(geometry.clampToGround),
      arcType: arcType(context, geometry.arcType)
    };
    const created = viewer.entities.add(entity);
    context.entities.set(String(object.id), created);
    return created;
  }

  /**
   * @param {LoaderContext} context
   * @param {JsonObject} object
   * @returns {unknown}
   */
  function addLineBetween(context, object) {
    const Cesium = context.Cesium;
    const viewer = /** @type {any} */ (context.viewer);
    const entity = entityBase(context, object);
    const geometry = asObject(object.geometry);
    const style = asObject(object.style);
    const fromRef = String(geometry.from || "");
    const toRef = String(geometry.to || "");

    entity.polyline = {
      positions: new Cesium.CallbackProperty(function getLinePositions(time) {
        const from = getReferencePosition(context, fromRef, time);
        const to = getReferencePosition(context, toRef, time);
        if (!from || !to) {
          return [];
        }
        return [from, to];
      }, false),
      width: unwrapNumber(style.width, 2),
      material: buildMaterial(context, asObject(style.material)),
      clampToGround: Boolean(geometry.clampToGround),
      arcType: arcType(context, geometry.arcType)
    };

    const created = viewer.entities.add(entity);
    context.entities.set(String(object.id), created);
    return created;
  }

  /**
   * @param {LoaderContext} context
   * @param {JsonObject} object
   * @returns {unknown}
   */
  function addPolygon(context, object) {
    const viewer = /** @type {any} */ (context.viewer);
    const entity = entityBase(context, object);
    const geometry = asObject(object.geometry);
    const style = asObject(object.style);
    const rings = Array.isArray(geometry.rings) ? geometry.rings : [];
    const outer = rings.length > 0 ? buildPositionArray(context, rings[0]) : [];
    const holes = [];
    for (let i = 1; i < rings.length; i += 1) {
      holes.push({ positions: buildPositionArray(context, rings[i]) });
    }
    entity.polygon = {
      hierarchy: { positions: outer, holes },
      material: buildMaterial(context, asObject(style.material)),
      fill: propertyToBoolean(style.fill, true),
      outline: propertyToBoolean(style.outline, false),
      outlineColor: buildColorProperty(context, style.outlineColor),
      height: unwrapNumber(geometry.heightMeters, undefined),
      extrudedHeight: unwrapNumber(geometry.extrudedHeightMeters, undefined),
      perPositionHeight: Boolean(geometry.perPositionHeight),
      closeTop: propertyToBoolean(geometry.closeTop, true),
      closeBottom: propertyToBoolean(geometry.closeBottom, true)
    };
    const created = viewer.entities.add(entity);
    context.entities.set(String(object.id), created);
    return created;
  }

  /**
   * @param {LoaderContext} context
   * @param {JsonObject} object
   * @returns {unknown}
   */
  function addRectangle(context, object) {
    const Cesium = context.Cesium;
    const viewer = /** @type {any} */ (context.viewer);
    const entity = entityBase(context, object);
    const geometry = asObject(object.geometry);
    const style = asObject(object.style);
    const bounds = Array.isArray(geometry.westSouthEastNorthDegrees) ? geometry.westSouthEastNorthDegrees : [0, 0, 0, 0];
    entity.rectangle = {
      coordinates: Cesium.Rectangle.fromDegrees(Number(bounds[0]), Number(bounds[1]), Number(bounds[2]), Number(bounds[3])),
      material: buildMaterial(context, asObject(style.material)),
      fill: propertyToBoolean(style.fill, true),
      outline: propertyToBoolean(style.outline, false),
      outlineColor: buildColorProperty(context, style.outlineColor),
      height: unwrapNumber(geometry.heightMeters, undefined),
      extrudedHeight: unwrapNumber(geometry.extrudedHeightMeters, undefined),
      rotation: degreesToRadians(unwrapNumber(geometry.rotationDegrees, 0)),
      stRotation: degreesToRadians(unwrapNumber(geometry.stRotationDegrees, 0))
    };
    const created = viewer.entities.add(entity);
    context.entities.set(String(object.id), created);
    return created;
  }

  /**
   * @param {LoaderContext} context
   * @param {JsonObject} object
   * @returns {unknown}
   */
  function addEllipse(context, object) {
    const viewer = /** @type {any} */ (context.viewer);
    const entity = entityBase(context, object);
    const geometry = asObject(object.geometry);
    const style = asObject(object.style);
    const radius = unwrapNumber(geometry.radiusMeters, undefined);
    entity.ellipse = {
      semiMajorAxis: radius || unwrapNumber(geometry.semiMajorAxisMeters, 1000),
      semiMinorAxis: radius || unwrapNumber(geometry.semiMinorAxisMeters, 1000),
      material: buildMaterial(context, asObject(style.material)),
      fill: propertyToBoolean(style.fill, true),
      outline: propertyToBoolean(style.outline, false),
      outlineColor: buildColorProperty(context, style.outlineColor),
      height: unwrapNumber(geometry.heightMeters, undefined),
      extrudedHeight: unwrapNumber(geometry.extrudedHeightMeters, undefined),
      rotation: degreesToRadians(unwrapNumber(geometry.rotationDegrees, 0)),
      stRotation: degreesToRadians(unwrapNumber(geometry.stRotationDegrees, 0))
    };
    const created = viewer.entities.add(entity);
    context.entities.set(String(object.id), created);
    return created;
  }

  /**
   * @param {LoaderContext} context
   * @param {JsonObject} object
   * @returns {unknown}
   */
  function addBox(context, object) {
    const Cesium = context.Cesium;
    const viewer = /** @type {any} */ (context.viewer);
    const entity = entityBase(context, object);
    const geometry = asObject(object.geometry);
    const style = asObject(object.style);
    const dimensions = array3(geometry.dimensionsMeters, [1, 1, 1]);
    entity.box = {
      dimensions: new Cesium.Cartesian3(dimensions[0], dimensions[1], dimensions[2]),
      material: buildMaterial(context, asObject(style.material)),
      fill: propertyToBoolean(style.fill, true),
      outline: propertyToBoolean(style.outline, false),
      outlineColor: buildColorProperty(context, style.outlineColor)
    };
    const created = viewer.entities.add(entity);
    context.entities.set(String(object.id), created);
    return created;
  }

  /**
   * @param {LoaderContext} context
   * @param {JsonObject} object
   * @param {string} kind
   * @returns {unknown}
   */
  function addCylinder(context, object, kind) {
    const viewer = /** @type {any} */ (context.viewer);
    const entity = entityBase(context, object);
    const geometry = asObject(object.geometry);
    const style = asObject(object.style);
    const radius = unwrapNumber(geometry.radiusMeters, undefined);
    const topRadius = kind === "cone" ? 0 : unwrapNumber(geometry.topRadiusMeters, radius || 1000);
    const bottomRadius = unwrapNumber(geometry.bottomRadiusMeters, radius || 1000);
    entity.cylinder = {
      length: unwrapNumber(geometry.lengthMeters, 1000),
      topRadius,
      bottomRadius,
      slices: unwrapNumber(geometry.slices, undefined),
      material: buildMaterial(context, asObject(style.material)),
      fill: propertyToBoolean(style.fill, true),
      outline: propertyToBoolean(style.outline, false),
      outlineColor: buildColorProperty(context, style.outlineColor)
    };
    const created = viewer.entities.add(entity);
    context.entities.set(String(object.id), created);
    return created;
  }

  /**
   * @param {LoaderContext} context
   * @param {JsonObject} object
   * @param {string} kind
   * @returns {unknown}
   */
  function addEllipsoidLike(context, object, kind) {
    const Cesium = context.Cesium;
    const viewer = /** @type {any} */ (context.viewer);
    const entity = entityBase(context, object);
    const geometry = asObject(object.geometry);
    const style = asObject(object.style);
    const radius = unwrapNumber(geometry.radiusMeters, undefined);
    const radii = radius ? [radius, radius, radius] : array3(geometry.radiiMeters, [1000, 1000, 1000]);
    const ellipsoid = {
      radii: new Cesium.Cartesian3(radii[0], radii[1], radii[2]),
      material: buildMaterial(context, asObject(style.material)),
      fill: propertyToBoolean(style.fill, true),
      outline: propertyToBoolean(style.outline, false),
      outlineColor: buildColorProperty(context, style.outlineColor),
      stackPartitions: unwrapNumber(geometry.stackPartitions, undefined),
      slicePartitions: unwrapNumber(geometry.slicePartitions, undefined)
    };

    const innerRadius = unwrapNumber(geometry.innerRadiusMeters, undefined);
    if (innerRadius !== undefined) {
      ellipsoid.innerRadii = new Cesium.Cartesian3(innerRadius, innerRadius, innerRadius);
    } else if (Array.isArray(geometry.innerRadiiMeters)) {
      const inner = array3(geometry.innerRadiiMeters, [0, 0, 0]);
      ellipsoid.innerRadii = new Cesium.Cartesian3(inner[0], inner[1], inner[2]);
    }

    if (kind === "hemisphere") {
      applyHemisphereAngles(ellipsoid, geometry);
    } else if (kind === "sectorVolume" || kind === "keyhole") {
      applySectorVolumeAngles(ellipsoid, geometry);
    } else {
      applyExplicitEllipsoidAngles(ellipsoid, geometry);
    }

    entity.ellipsoid = removeUndefined(ellipsoid);
    const created = viewer.entities.add(entity);
    context.entities.set(String(object.id), created);
    return created;
  }

  /**
   * @param {JsonObject} ellipsoid
   * @param {JsonObject} geometry
   * @returns {void}
   */
  function applyHemisphereAngles(ellipsoid, geometry) {
    const portion = String(geometry.portion || "upper");
    ellipsoid.minimumClock = degreesToRadians(unwrapNumber(geometry.azimuthStartDegrees, 0));
    ellipsoid.maximumClock = degreesToRadians(unwrapNumber(geometry.azimuthStopDegrees, 360));
    if (portion === "upper") {
      ellipsoid.minimumCone = 0;
      ellipsoid.maximumCone = Math.PI / 2;
    } else if (portion === "lower") {
      ellipsoid.minimumCone = Math.PI / 2;
      ellipsoid.maximumCone = Math.PI;
    } else {
      ellipsoid.minimumCone = 0;
      ellipsoid.maximumCone = Math.PI;
    }
  }

  /**
   * @param {JsonObject} ellipsoid
   * @param {JsonObject} geometry
   * @returns {void}
   */
  function applySectorVolumeAngles(ellipsoid, geometry) {
    const azStart = unwrapNumber(geometry.azimuthStartDegrees, 0);
    const azStop = unwrapNumber(geometry.azimuthStopDegrees, 360);
    const elStart = unwrapNumber(geometry.elevationStartDegrees, -90);
    const elStop = unwrapNumber(geometry.elevationStopDegrees, 90);
    ellipsoid.minimumClock = degreesToRadians(azStart);
    ellipsoid.maximumClock = degreesToRadians(azStop);
    ellipsoid.minimumCone = degreesToRadians(90 - elStop);
    ellipsoid.maximumCone = degreesToRadians(90 - elStart);
  }

  /**
   * @param {JsonObject} ellipsoid
   * @param {JsonObject} geometry
   * @returns {void}
   */
  function applyExplicitEllipsoidAngles(ellipsoid, geometry) {
    if (geometry.minimumClockDegrees !== undefined) {
      ellipsoid.minimumClock = degreesToRadians(unwrapNumber(geometry.minimumClockDegrees, 0));
    }
    if (geometry.maximumClockDegrees !== undefined) {
      ellipsoid.maximumClock = degreesToRadians(unwrapNumber(geometry.maximumClockDegrees, 360));
    }
    if (geometry.minimumConeDegrees !== undefined) {
      ellipsoid.minimumCone = degreesToRadians(unwrapNumber(geometry.minimumConeDegrees, 0));
    }
    if (geometry.maximumConeDegrees !== undefined) {
      ellipsoid.maximumCone = degreesToRadians(unwrapNumber(geometry.maximumConeDegrees, 180));
    }
  }


  /**
   * @param {LoaderContext} context
   * @param {JsonObject} object
   * @param {string} kind
   * @returns {unknown}
   */
  function addTacticalOrFallback(context, object, kind) {
    if (shouldUsePrimitiveBackend(object)) {
      const primitive = addTacticalPrimitive(context, object, kind);
      if (primitive) {
        return primitive;
      }
      warn(context, `Object ${String(object.id)} could not be built as a custom primitive; falling back to Entity ellipsoid approximation.`);
    }
    return addEllipsoidLike(context, object, kind);
  }

  /**
   * @param {JsonObject} object
   * @returns {boolean}
   */
  function shouldUsePrimitiveBackend(object) {
    const geometry = asObject(object.geometry);
    const hints = asObject(object.rendererHints);
    const cesiumHints = asObject(hints.cesium);
    const requested = String(geometry.backend || cesiumHints.backend || "primitive");
    return requested !== "entity";
  }

  /**
   * @param {LoaderContext} context
   * @param {JsonObject} object
   * @param {string} kind
   * @returns {unknown}
   */
  function addTacticalPrimitive(context, object, kind) {
    let mesh;
    if (kind === "frustum") {
      mesh = buildFrustumMesh(context, object);
    } else {
      mesh = buildSphericalWedgeMesh(context, object, kind);
    }
    if (!mesh) {
      return undefined;
    }
    return addMeshPrimitive(context, object, mesh);
  }

  /**
   * @param {LoaderContext} context
   * @param {JsonObject} object
   * @returns {unknown}
   */
  function addCustomPrimitive(context, object) {
    const mesh = buildCustomPrimitiveMesh(context, object);
    if (!mesh) {
      warn(context, `customPrimitive ${String(object.id)} is missing positions or indices.`);
      return undefined;
    }
    return addMeshPrimitive(context, object, mesh);
  }

  /**
   * @typedef {{positions: number[][], indices: number[]}} MeshSpec
   */

  /**
   * @param {LoaderContext} context
   * @param {JsonObject} object
   * @param {MeshSpec} mesh
   * @returns {unknown}
   */
  function addMeshPrimitive(context, object, mesh) {
    const Cesium = context.Cesium;
    const viewer = /** @type {any} */ (context.viewer);
    const flatPositions = flattenVec3(mesh.positions);
    const indices = mesh.indices.length > 65535 ? new Uint32Array(mesh.indices) : new Uint16Array(mesh.indices);
    const geometry = new Cesium.Geometry({
      attributes: {
        position: new Cesium.GeometryAttribute({
          componentDatatype: Cesium.ComponentDatatype.DOUBLE,
          componentsPerAttribute: 3,
          values: flatPositions
        })
      },
      indices,
      primitiveType: Cesium.PrimitiveType.TRIANGLES,
      boundingSphere: Cesium.BoundingSphere.fromVertices(flatPositions)
    });
    const color = primitiveColor(context, object);
    const instance = new Cesium.GeometryInstance({
      geometry,
      id: String(object.id),
      modelMatrix: buildPrimitiveModelMatrix(context, object),
      attributes: {
        color: Cesium.ColorGeometryInstanceAttribute.fromColor(color)
      }
    });
    const primitive = new Cesium.Primitive({
      geometryInstances: instance,
      appearance: new Cesium.PerInstanceColorAppearance({
        flat: true,
        translucent: color.alpha < 1,
        closed: propertyToBoolean(asObject(object.geometry).closed, true)
      }),
      asynchronous: false,
      allowPicking: true
    });
    viewer.scene.primitives.add(primitive);
    context.primitives.set(String(object.id), primitive);
    return primitive;
  }

  /**
   * @param {LoaderContext} context
   * @param {JsonObject} object
   * @returns {unknown}
   */
  function primitiveColor(context, object) {
    const style = asObject(object.style);
    const material = asObject(style.material);
    return colorFromArray(context, material.rgba || style.color || [1, 1, 1, 0.35]);
  }

  /**
   * @param {LoaderContext} context
   * @param {JsonObject} object
   * @returns {unknown}
   */
  function buildPrimitiveModelMatrix(context, object) {
    const Cesium = context.Cesium;
    const pose = asObject(object.pose);
    const positionProperty = buildPositionProperty(context, pose.position);
    const position = getPropertyValue(context, positionProperty, currentTime(context));
    if (!position) {
      return Cesium.Matrix4.IDENTITY;
    }
    const orientation = asObject(pose.orientation);
    if (orientation.headingPitchRollDegrees || orientation.headingPitchRollRadians) {
      return Cesium.Transforms.headingPitchRollToFixedFrame(position, hprFromSpec(context, orientation));
    }
    return Cesium.Transforms.eastNorthUpToFixedFrame(position);
  }

  /**
   * @param {LoaderContext} context
   * @param {JsonObject} object
   * @param {string} kind
   * @returns {MeshSpec | undefined}
   */
  function buildSphericalWedgeMesh(context, object, kind) {
    const geometry = asObject(object.geometry);
    const radius = unwrapNumber(geometry.radiusMeters, undefined);
    const outerRadius = unwrapNumber(geometry.outerRadiusMeters, radius || 1000);
    const innerRadius = Math.max(0, unwrapNumber(geometry.innerRadiusMeters, 0));
    let azimuthStart = unwrapNumber(geometry.azimuthStartDegrees, 0);
    let azimuthStop = unwrapNumber(geometry.azimuthStopDegrees, 360);
    let elevationStart = unwrapNumber(geometry.elevationStartDegrees, -90);
    let elevationStop = unwrapNumber(geometry.elevationStopDegrees, 90);

    if (kind === "hemisphere") {
      const portion = String(geometry.portion || "upper");
      if (portion === "upper") {
        elevationStart = 0;
        elevationStop = 90;
      } else if (portion === "lower") {
        elevationStart = -90;
        elevationStop = 0;
      } else if (portion === "front") {
        azimuthStart = -90;
        azimuthStop = 90;
      } else if (portion === "rear") {
        azimuthStart = 90;
        azimuthStop = 270;
      } else if (portion === "left") {
        azimuthStart = 180;
        azimuthStop = 360;
      } else if (portion === "right") {
        azimuthStart = 0;
        azimuthStop = 180;
      }
    } else if (kind === "sphericalCap") {
      elevationStart = unwrapNumber(geometry.elevationStartDegrees, 0);
      elevationStop = unwrapNumber(geometry.elevationStopDegrees, 90);
    }

    const azimuthSegments = Math.max(3, Math.floor(unwrapNumber(geometry.azimuthSegments, unwrapNumber(geometry.segments, 48))));
    const elevationSegments = Math.max(1, Math.floor(unwrapNumber(geometry.elevationSegments, Math.max(3, Math.ceil(azimuthSegments / 4)))));
    const radialSegments = innerRadius > 0 ? 1 : 1;
    const azimuths = linspace(azimuthStart, azimuthStop, azimuthSegments + 1);
    const elevations = linspace(elevationStart, elevationStop, elevationSegments + 1);
    const radii = linspace(innerRadius, outerRadius, radialSegments + 1);
    const positions = [];
    const indices = [];

    addSphericalSurface(positions, indices, outerRadius, azimuths, elevations, false);
    if (innerRadius > 0) {
      addSphericalSurface(positions, indices, innerRadius, azimuths, elevations, true);
    }
    addConstantAzimuthSurface(positions, indices, azimuthStart, radii, elevations, true);
    addConstantAzimuthSurface(positions, indices, azimuthStop, radii, elevations, false);
    addConstantElevationSurface(positions, indices, elevationStart, radii, azimuths, false);
    addConstantElevationSurface(positions, indices, elevationStop, radii, azimuths, true);

    return { positions, indices };
  }

  /**
   * @param {LoaderContext} context
   * @param {JsonObject} object
   * @returns {MeshSpec}
   */
  function buildFrustumMesh(context, object) {
    const geometry = asObject(object.geometry);
    const near = Math.max(0.001, unwrapNumber(geometry.nearMeters, 100));
    const far = Math.max(near + 0.001, unwrapNumber(geometry.farMeters, 1000));
    const hFov = degreesToRadians(unwrapNumber(geometry.horizontalFovDegrees, unwrapNumber(geometry.outerHalfAngleDegrees, 30) * 2));
    const vFov = degreesToRadians(unwrapNumber(geometry.verticalFovDegrees, hFov * 180 / Math.PI));
    const nearHalfWidth = near * Math.tan(hFov / 2);
    const nearHalfHeight = near * Math.tan(vFov / 2);
    const farHalfWidth = far * Math.tan(hFov / 2);
    const farHalfHeight = far * Math.tan(vFov / 2);
    const positions = [
      [near, -nearHalfWidth, -nearHalfHeight],
      [near, nearHalfWidth, -nearHalfHeight],
      [near, nearHalfWidth, nearHalfHeight],
      [near, -nearHalfWidth, nearHalfHeight],
      [far, -farHalfWidth, -farHalfHeight],
      [far, farHalfWidth, -farHalfHeight],
      [far, farHalfWidth, farHalfHeight],
      [far, -farHalfWidth, farHalfHeight]
    ];
    const indices = [
      0, 1, 2, 0, 2, 3,
      4, 6, 5, 4, 7, 6,
      0, 4, 5, 0, 5, 1,
      1, 5, 6, 1, 6, 2,
      2, 6, 7, 2, 7, 3,
      3, 7, 4, 3, 4, 0
    ];
    return { positions, indices };
  }

  /**
   * @param {LoaderContext} context
   * @param {JsonObject} object
   * @returns {MeshSpec | undefined}
   */
  function buildCustomPrimitiveMesh(context, object) {
    const geometry = asObject(object.geometry);
    if (!Array.isArray(geometry.positions) || !Array.isArray(geometry.indices)) {
      return undefined;
    }
    return {
      positions: geometry.positions.map(function mapPosition(value) {
        return array3(value, [0, 0, 0]);
      }),
      indices: geometry.indices.map(Number)
    };
  }

  /**
   * @param {number[]} values
   * @returns {Float64Array}
   */
  function float64(values) {
    return new Float64Array(values);
  }

  /**
   * @param {number[][]} positions
   * @returns {Float64Array}
   */
  function flattenVec3(positions) {
    const values = [];
    for (const position of positions) {
      values.push(Number(position[0]), Number(position[1]), Number(position[2]));
    }
    return float64(values);
  }

  /**
   * @param {number} start
   * @param {number} stop
   * @param {number} count
   * @returns {number[]}
   */
  function linspace(start, stop, count) {
    if (count <= 1) {
      return [start];
    }
    const values = [];
    for (let i = 0; i < count; i += 1) {
      values.push(start + (stop - start) * i / (count - 1));
    }
    return values;
  }

  /**
   * @param {number[][]} positions
   * @param {number[]} indices
   * @param {number} radius
   * @param {number[]} azimuths
   * @param {number[]} elevations
   * @param {boolean} flip
   * @returns {void}
   */
  function addSphericalSurface(positions, indices, radius, azimuths, elevations, flip) {
    const base = positions.length;
    for (const elevation of elevations) {
      for (const azimuth of azimuths) {
        positions.push(sphericalLocalPoint(radius, azimuth, elevation));
      }
    }
    addGridIndices(indices, base, elevations.length, azimuths.length, flip);
  }

  /**
   * @param {number[][]} positions
   * @param {number[]} indices
   * @param {number} azimuth
   * @param {number[]} radii
   * @param {number[]} elevations
   * @param {boolean} flip
   * @returns {void}
   */
  function addConstantAzimuthSurface(positions, indices, azimuth, radii, elevations, flip) {
    const base = positions.length;
    for (const elevation of elevations) {
      for (const radius of radii) {
        positions.push(sphericalLocalPoint(radius, azimuth, elevation));
      }
    }
    addGridIndices(indices, base, elevations.length, radii.length, flip);
  }

  /**
   * @param {number[][]} positions
   * @param {number[]} indices
   * @param {number} elevation
   * @param {number[]} radii
   * @param {number[]} azimuths
   * @param {boolean} flip
   * @returns {void}
   */
  function addConstantElevationSurface(positions, indices, elevation, radii, azimuths, flip) {
    const base = positions.length;
    for (const radius of radii) {
      for (const azimuth of azimuths) {
        positions.push(sphericalLocalPoint(radius, azimuth, elevation));
      }
    }
    addGridIndices(indices, base, radii.length, azimuths.length, flip);
  }

  /**
   * @param {number[]} indices
   * @param {number} base
   * @param {number} rows
   * @param {number} columns
   * @param {boolean} flip
   * @returns {void}
   */
  function addGridIndices(indices, base, rows, columns, flip) {
    for (let row = 0; row < rows - 1; row += 1) {
      for (let column = 0; column < columns - 1; column += 1) {
        const a = base + row * columns + column;
        const b = a + 1;
        const c = a + columns;
        const d = c + 1;
        if (flip) {
          indices.push(a, d, b, a, c, d);
        } else {
          indices.push(a, b, d, a, d, c);
        }
      }
    }
  }

  /**
   * Azimuth is degrees clockwise from local north (+Y); elevation is degrees above local horizontal.
   *
   * @param {number} radius
   * @param {number} azimuthDegrees
   * @param {number} elevationDegrees
   * @returns {number[]}
   */
  function sphericalLocalPoint(radius, azimuthDegrees, elevationDegrees) {
    const azimuth = degreesToRadians(azimuthDegrees);
    const elevation = degreesToRadians(elevationDegrees);
    const horizontal = radius * Math.cos(elevation);
    return [
      horizontal * Math.sin(azimuth),
      horizontal * Math.cos(azimuth),
      radius * Math.sin(elevation)
    ];
  }

  /**
   * @param {LoaderContext} context
   * @param {JsonObject} object
   * @returns {unknown}
   */
  function addWall(context, object) {
    const viewer = /** @type {any} */ (context.viewer);
    const entity = entityBase(context, object);
    const geometry = asObject(object.geometry);
    const style = asObject(object.style);
    entity.wall = {
      positions: buildPositionArray(context, geometry.positions),
      minimumHeights: Array.isArray(geometry.minimumHeightsMeters) ? geometry.minimumHeightsMeters : undefined,
      maximumHeights: Array.isArray(geometry.maximumHeightsMeters) ? geometry.maximumHeightsMeters : undefined,
      material: buildMaterial(context, asObject(style.material)),
      outline: propertyToBoolean(style.outline, false),
      outlineColor: buildColorProperty(context, style.outlineColor)
    };
    const created = viewer.entities.add(entity);
    context.entities.set(String(object.id), created);
    return created;
  }

  /**
   * @param {LoaderContext} context
   * @param {JsonObject} object
   * @returns {unknown}
   */
  function addCorridor(context, object) {
    const viewer = /** @type {any} */ (context.viewer);
    const entity = entityBase(context, object);
    const geometry = asObject(object.geometry);
    const style = asObject(object.style);
    entity.corridor = {
      positions: buildPositionArray(context, geometry.positions),
      width: unwrapNumber(geometry.widthMeters, 1000),
      height: unwrapNumber(geometry.heightMeters, undefined),
      extrudedHeight: unwrapNumber(geometry.extrudedHeightMeters, undefined),
      material: buildMaterial(context, asObject(style.material)),
      fill: propertyToBoolean(style.fill, true),
      outline: propertyToBoolean(style.outline, false),
      outlineColor: buildColorProperty(context, style.outlineColor),
      cornerType: cornerType(context, geometry.cornerType),
      clampToGround: Boolean(geometry.clampToGround)
    };
    const created = viewer.entities.add(entity);
    context.entities.set(String(object.id), created);
    return created;
  }

  /**
   * @param {LoaderContext} context
   * @param {JsonObject} object
   * @returns {unknown}
   */
  function addPolylineVolume(context, object) {
    const Cesium = context.Cesium;
    const viewer = /** @type {any} */ (context.viewer);
    const entity = entityBase(context, object);
    const geometry = asObject(object.geometry);
    const style = asObject(object.style);
    const shape = Array.isArray(geometry.shapeMeters) ? geometry.shapeMeters : [];
    entity.polylineVolume = {
      positions: buildPositionArray(context, geometry.positions),
      shape: shape.map(function mapShape(point) {
        const xy = array2(point, [0, 0]);
        return new Cesium.Cartesian2(xy[0], xy[1]);
      }),
      material: buildMaterial(context, asObject(style.material)),
      fill: propertyToBoolean(style.fill, true),
      outline: propertyToBoolean(style.outline, false),
      outlineColor: buildColorProperty(context, style.outlineColor),
      cornerType: cornerType(context, geometry.cornerType)
    };
    const created = viewer.entities.add(entity);
    context.entities.set(String(object.id), created);
    return created;
  }

  /**
   * @param {LoaderContext} context
   * @param {JsonObject} object
   * @returns {unknown}
   */
  function addSector2d(context, object) {
    const viewer = /** @type {any} */ (context.viewer);
    const entity = entityBase(context, object);
    const style = asObject(object.style);
    const positions = makeSectorPolygonPositions(context, object);
    entity.polygon = {
      hierarchy: positions,
      material: buildMaterial(context, asObject(style.material)),
      fill: propertyToBoolean(style.fill, true),
      outline: propertyToBoolean(style.outline, true),
      outlineColor: buildColorProperty(context, style.outlineColor)
    };
    const created = viewer.entities.add(entity);
    context.entities.set(String(object.id), created);
    return created;
  }

  /**
   * @param {LoaderContext} context
   * @param {JsonObject} object
   * @param {string} kind
   * @returns {unknown}
   */
  function addDerivedVector(context, object, kind) {
    const Cesium = context.Cesium;
    const viewer = /** @type {any} */ (context.viewer);
    const entity = entityBase(context, object);
    const geometry = asObject(object.geometry);
    const style = asObject(object.style);
    const source = String(geometry.source || "");
    const scale = unwrapNumber(geometry.scale, unwrapNumber(geometry.lengthMeters, 1));
    const width = unwrapNumber(style.width, 2);
    const windowSeconds = unwrapNumber(geometry.windowSeconds, 1);

    entity.polyline = {
      positions: new Cesium.CallbackProperty(function getVectorPositions(time) {
        const base = source ? getReferencePosition(context, source, time) : getPropertyValue(context, entity.position, time);
        if (!base) {
          return [];
        }

        let vector;
        if (kind === "accelerationVector" && source) {
          vector = computeAcceleration(context, source, time, windowSeconds);
        } else if (kind === "velocityVector" && source) {
          vector = computeVelocity(context, source, time, windowSeconds);
        } else if (Array.isArray(geometry.direction)) {
          const direction = array3(geometry.direction, [1, 0, 0]);
          vector = new Cesium.Cartesian3(direction[0], direction[1], direction[2]);
          Cesium.Cartesian3.normalize(vector, vector);
        } else if (source) {
          vector = computeVelocity(context, source, time, windowSeconds);
        }

        if (!vector) {
          return [];
        }
        const end = Cesium.Cartesian3.add(base, Cesium.Cartesian3.multiplyByScalar(vector, scale, new Cesium.Cartesian3()), new Cesium.Cartesian3());
        return [base, end];
      }, false),
      width,
      material: buildMaterial(context, asObject(style.material)),
      arcType: Cesium.ArcType.NONE
    };

    const created = viewer.entities.add(entity);
    context.entities.set(String(object.id), created);
    return created;
  }

  /**
   * @param {LoaderContext} context
   * @param {JsonObject} object
   * @param {string} kind
   * @returns {unknown[] | undefined}
   */
  function addAxes(context, object, kind) {
    if (kind === "principalAxes") {
      return addPrincipalAxes(context, object);
    }
    const Cesium = context.Cesium;
    const viewer = /** @type {any} */ (context.viewer);
    const geometry = asObject(object.geometry);
    const axes = Array.isArray(geometry.axes) ? geometry.axes.map(String) : ["x", "y", "z"];
    const lengthMeters = unwrapNumber(geometry.lengthMeters, 1000);
    const positionRef = String(geometry.position || geometry.source || "");
    const orientationRef = String(geometry.orientation || "");
    const created = [];

    for (const axis of axes) {
      const id = `${String(object.id)}-${axis}`;
      const color = AXIS_COLORS[axis] || [1, 1, 1, 1];
      const entity = {
        id,
        name: `${String(object.name || object.id)} ${axis}`,
        polyline: {
          positions: new Cesium.CallbackProperty(function getAxisPositions(time) {
            const base = getReferencePosition(context, positionRef, time);
            const orientation = getReferenceOrientation(context, orientationRef, time);
            if (!base || !orientation) {
              return [];
            }
            const direction = axisDirection(context, axis, orientation);
            const end = Cesium.Cartesian3.add(base, Cesium.Cartesian3.multiplyByScalar(direction, lengthMeters, new Cesium.Cartesian3()), new Cesium.Cartesian3());
            return [base, end];
          }, false),
          width: 2,
          material: new Cesium.ColorMaterialProperty(colorFromArray(context, color)),
          arcType: Cesium.ArcType.NONE
        }
      };
      created.push(viewer.entities.add(entity));
    }

    return created[0];
  }



  /**
   * @param {LoaderContext} context
   * @param {JsonObject} object
   * @returns {unknown[] | undefined}
   */
  function addPrincipalAxes(context, object) {
    const Cesium = context.Cesium;
    const viewer = /** @type {any} */ (context.viewer);
    const geometry = asObject(object.geometry);
    const axes = Array.isArray(geometry.axes) ? geometry.axes.map(String) : ["principal0", "principal1", "principal2"];
    const lengthMeters = unwrapNumber(geometry.lengthMeters, 1000);
    const positionRef = String(geometry.position || geometry.source || "");
    const frame = String(geometry.frame || "localEnu");
    const directions = principalDirections(geometry);
    const created = [];

    for (const axis of axes) {
      const axisIndex = axis === "principal1" ? 1 : axis === "principal2" ? 2 : 0;
      const directionSpec = directions[axisIndex] || { direction: [1, 0, 0], scale: 1 };
      const id = `${String(object.id)}-${axis}`;
      const color = AXIS_COLORS[axis] || [1, 1, 1, 1];
      const entity = {
        id,
        name: `${String(object.name || object.id)} ${axis}`,
        polyline: {
          positions: new Cesium.CallbackProperty(function getPrincipalAxisPositions(time) {
            const base = positionRef ? getReferencePosition(context, positionRef, time) : getPropertyValue(context, buildPositionProperty(context, asObject(object.pose).position), time);
            if (!base) {
              return [];
            }
            let direction = new Cesium.Cartesian3(directionSpec.direction[0], directionSpec.direction[1], directionSpec.direction[2]);
            if (frame !== "ecef") {
              direction = localDirectionToFixed(context, base, direction);
            }
            Cesium.Cartesian3.normalize(direction, direction);
            const axisLength = lengthMeters * (geometry.scaleByEigenvalue === true ? directionSpec.scale : 1);
            const end = Cesium.Cartesian3.add(base, Cesium.Cartesian3.multiplyByScalar(direction, axisLength, new Cesium.Cartesian3()), new Cesium.Cartesian3());
            return [base, end];
          }, false),
          width: 2,
          material: new Cesium.ColorMaterialProperty(colorFromArray(context, color)),
          arcType: Cesium.ArcType.NONE
        }
      };
      created.push(viewer.entities.add(entity));
    }
    return created[0];
  }

  /**
   * @param {LoaderContext} context
   * @param {unknown} base
   * @param {unknown} direction
   * @returns {unknown}
   */
  function localDirectionToFixed(context, base, direction) {
    const Cesium = context.Cesium;
    const transform = Cesium.Transforms.eastNorthUpToFixedFrame(base);
    return Cesium.Matrix4.multiplyByPointAsVector(transform, direction, new Cesium.Cartesian3());
  }

  /**
   * @param {JsonObject} geometry
   * @returns {{direction: number[], scale: number}[]}
   */
  function principalDirections(geometry) {
    if (Array.isArray(geometry.directions)) {
      return geometry.directions.map(function mapDirection(direction) {
        return { direction: normalizeArray3(array3(direction, [1, 0, 0])), scale: 1 };
      });
    }
    const covariance = covarianceMatrix(geometry);
    if (!covariance) {
      return [
        { direction: [1, 0, 0], scale: 1 },
        { direction: [0, 1, 0], scale: 1 },
        { direction: [0, 0, 1], scale: 1 }
      ];
    }
    const first = dominantEigen(covariance, [1, 0.25, 0.1]);
    const secondMatrix = deflateSymmetric3(covariance, first.value, first.vector);
    const second = dominantEigen(secondMatrix, orthogonalSeed(first.vector));
    const thirdVector = normalizeArray3(crossArray3(first.vector, second.vector));
    const thirdValue = quadraticForm(covariance, thirdVector);
    return [
      { direction: first.vector, scale: Math.sqrt(Math.max(0, Math.abs(first.value))) },
      { direction: second.vector, scale: Math.sqrt(Math.max(0, Math.abs(second.value))) },
      { direction: thirdVector, scale: Math.sqrt(Math.max(0, Math.abs(thirdValue))) }
    ];
  }

  /**
   * @param {JsonObject} geometry
   * @returns {number[][] | undefined}
   */
  function covarianceMatrix(geometry) {
    if (Array.isArray(geometry.covarianceMatrix) && geometry.covarianceMatrix.length === 3) {
      return geometry.covarianceMatrix.map(function mapRow(row) {
        return array3(row, [0, 0, 0]);
      });
    }
    if (Array.isArray(geometry.covarianceUpperTriangle) && geometry.covarianceUpperTriangle.length >= 6) {
      const v = geometry.covarianceUpperTriangle.map(Number);
      return [
        [v[0], v[1], v[2]],
        [v[1], v[3], v[4]],
        [v[2], v[4], v[5]]
      ];
    }
    return undefined;
  }

  /**
   * @param {number[][]} matrix
   * @param {number[]} seed
   * @returns {{value: number, vector: number[]}}
   */
  function dominantEigen(matrix, seed) {
    let vector = normalizeArray3(seed);
    for (let i = 0; i < 24; i += 1) {
      vector = normalizeArray3(multiplyMatrixVector3(matrix, vector));
    }
    return { value: quadraticForm(matrix, vector), vector };
  }

  /**
   * @param {number[][]} matrix
   * @param {number} value
   * @param {number[]} vector
   * @returns {number[][]}
   */
  function deflateSymmetric3(matrix, value, vector) {
    return matrix.map(function mapRow(row, r) {
      return row.map(function mapValue(entry, c) {
        return entry - value * vector[r] * vector[c];
      });
    });
  }

  /**
   * @param {number[]} value
   * @returns {number[]}
   */
  function orthogonalSeed(value) {
    if (Math.abs(value[0]) < 0.9) {
      return normalizeArray3(crossArray3(value, [1, 0, 0]));
    }
    return normalizeArray3(crossArray3(value, [0, 1, 0]));
  }

  /**
   * @param {number[][]} matrix
   * @param {number[]} vector
   * @returns {number[]}
   */
  function multiplyMatrixVector3(matrix, vector) {
    return [
      matrix[0][0] * vector[0] + matrix[0][1] * vector[1] + matrix[0][2] * vector[2],
      matrix[1][0] * vector[0] + matrix[1][1] * vector[1] + matrix[1][2] * vector[2],
      matrix[2][0] * vector[0] + matrix[2][1] * vector[1] + matrix[2][2] * vector[2]
    ];
  }

  /**
   * @param {number[][]} matrix
   * @param {number[]} vector
   * @returns {number}
   */
  function quadraticForm(matrix, vector) {
    const mv = multiplyMatrixVector3(matrix, vector);
    return vector[0] * mv[0] + vector[1] * mv[1] + vector[2] * mv[2];
  }

  /**
   * @param {number[]} value
   * @returns {number[]}
   */
  function normalizeArray3(value) {
    const norm = Math.hypot(value[0], value[1], value[2]);
    if (norm === 0) {
      return [1, 0, 0];
    }
    return [value[0] / norm, value[1] / norm, value[2] / norm];
  }

  /**
   * @param {number[]} a
   * @param {number[]} b
   * @returns {number[]}
   */
  function crossArray3(a, b) {
    return [
      a[1] * b[2] - a[2] * b[1],
      a[2] * b[0] - a[0] * b[2],
      a[0] * b[1] - a[1] * b[0]
    ];
  }


  /**
   * @param {LoaderContext} context
   * @param {unknown} value
   * @returns {unknown}
   */
  function buildPositionProperty(context, value) {
    const Cesium = context.Cesium;
    const spec = asObject(value);
    if (Object.keys(spec).length === 0) {
      return undefined;
    }
    if (typeof spec.reference === "string") {
      return resolveReferenceProperty(context, spec.reference, "position");
    }
    if (spec.cartographicDegrees) {
      const v = array3(spec.cartographicDegrees, [0, 0, 0]);
      return Cesium.Cartesian3.fromDegrees(v[0], v[1], v[2]);
    }
    if (spec.cartographicRadians) {
      const v = array3(spec.cartographicRadians, [0, 0, 0]);
      return Cesium.Cartesian3.fromRadians(v[0], v[1], v[2]);
    }
    if (spec.cartesianMeters) {
      const v = array3(spec.cartesianMeters, [0, 0, 0]);
      return new Cesium.Cartesian3(v[0], v[1], v[2]);
    }
    if (spec.samples) {
      return buildSampledPositionProperty(context, asObject(spec.samples));
    }
    if (spec.localMeters) {
      return buildLocalPosition(context, asObject(spec.localMeters));
    }
    return undefined;
  }

  /**
   * @param {LoaderContext} context
   * @param {JsonObject} samples
   * @returns {unknown}
   */
  function buildSampledPositionProperty(context, samples) {
    const Cesium = context.Cesium;
    const referenceFrame = referenceFrameValue(context, samples.referenceFrame);
    const derivativeCount = unwrapNumber(samples.derivativeCount, 0);
    const property = new Cesium.SampledPositionProperty(referenceFrame, derivativeCount);
    const epoch = typeof samples.epoch === "string" ? Cesium.JulianDate.fromIso8601(samples.epoch) : undefined;
    const values = Array.isArray(samples.values) ? samples.values : [];
    for (const row of values) {
      if (!Array.isArray(row) || row.length < 4) {
        continue;
      }
      const time = sampleTime(context, row[0], samples.timeFormat, epoch);
      const position = samplePosition(context, row, samples.valueFormat);
      property.addSample(time, position);
    }

    const interpolation = String(samples.interpolation || "linear");
    property.setInterpolationOptions({
      interpolationAlgorithm: interpolationAlgorithm(context, interpolation),
      interpolationDegree: unwrapNumber(samples.interpolationDegree, interpolation === "linear" ? 1 : 5)
    });
    return property;
  }

  /**
   * @param {LoaderContext} context
   * @param {JsonObject} local
   * @returns {unknown}
   */
  function buildLocalPosition(context, local) {
    const Cesium = context.Cesium;
    const originProperty = buildPositionProperty(context, local.origin);
    const value = array3(local.value, [0, 0, 0]);
    const time = currentTime(context);
    const origin = getPropertyValue(context, originProperty, time);
    if (!origin) {
      return undefined;
    }
    const transform = Cesium.Transforms.eastNorthUpToFixedFrame(origin);
    return Cesium.Matrix4.multiplyByPoint(transform, new Cesium.Cartesian3(value[0], value[1], value[2]), new Cesium.Cartesian3());
  }

  /**
   * @param {LoaderContext} context
   * @param {unknown} value
   * @param {unknown} positionProperty
   * @returns {unknown}
   */
  function buildOrientationProperty(context, value, positionProperty) {
    const Cesium = context.Cesium;
    const spec = asObject(value);
    if (Object.keys(spec).length === 0) {
      return undefined;
    }
    if (typeof spec.reference === "string") {
      return resolveReferenceProperty(context, spec.reference, "orientation");
    }
    if (spec.computed) {
      const computed = asObject(spec.computed);
      if (computed.operation === "velocityOrientation" && typeof computed.source === "string") {
        const source = resolveReferenceProperty(context, computed.source, "position");
        return new Cesium.VelocityOrientationProperty(source);
      }
    }
    if (spec.velocityAligned) {
      const source = asObject(spec.velocityAligned).source;
      if (typeof source === "string") {
        const sourceProperty = resolveReferenceProperty(context, source, "position");
        return new Cesium.VelocityOrientationProperty(sourceProperty);
      }
    }
    if (spec.unitQuaternion) {
      const q = array4(spec.unitQuaternion, [0, 0, 0, 1]);
      return new Cesium.Quaternion(q[0], q[1], q[2], q[3]);
    }
    if (spec.headingPitchRollDegrees || spec.headingPitchRollRadians) {
      const hpr = hprFromSpec(context, spec);
      return new Cesium.CallbackProperty(function getHprOrientation(time) {
        const position = getPropertyValue(context, positionProperty, time);
        if (!position) {
          return undefined;
        }
        return Cesium.Transforms.headingPitchRollQuaternion(position, hpr);
      }, false);
    }
    return undefined;
  }

  /**
   * @param {LoaderContext} context
   * @param {unknown} orientationProperty
   * @param {JsonObject} correction
   * @returns {unknown}
   */
  function applyModelFrameCorrection(context, orientationProperty, correction) {
    const Cesium = context.Cesium;
    const bodyFromModelSpec = asObject(correction.bodyFromModel);
    const modelFromBodySpec = asObject(correction.modelFromBody);
    let bodyFromModel = rotationQuaternionFromTrs(context, bodyFromModelSpec);
    const modelFromBody = rotationQuaternionFromTrs(context, modelFromBodySpec);
    if (!bodyFromModel && modelFromBody) {
      bodyFromModel = Cesium.Quaternion.inverse(modelFromBody, new Cesium.Quaternion());
    }
    if (!bodyFromModel) {
      return orientationProperty;
    }
    return new Cesium.CallbackProperty(function getCorrectedOrientation(time) {
      const worldFromBody = getPropertyValue(context, orientationProperty, time);
      if (!worldFromBody) {
        return undefined;
      }
      return Cesium.Quaternion.multiply(worldFromBody, bodyFromModel, new Cesium.Quaternion());
    }, false);
  }

  /**
   * @param {LoaderContext} context
   * @param {JsonObject} trs
   * @returns {unknown}
   */
  function rotationQuaternionFromTrs(context, trs) {
    const Cesium = context.Cesium;
    if (trs.unitQuaternion) {
      const q = array4(trs.unitQuaternion, [0, 0, 0, 1]);
      return new Cesium.Quaternion(q[0], q[1], q[2], q[3]);
    }
    if (trs.rotationDegrees || trs.rotationRadians) {
      const hpr = hprFromSpec(context, {
        headingPitchRollDegrees: trs.rotationDegrees,
        headingPitchRollRadians: trs.rotationRadians
      });
      return Cesium.Quaternion.fromHeadingPitchRoll(hpr);
    }
    return undefined;
  }

  /**
   * @param {LoaderContext} context
   * @param {unknown} refs
   * @returns {unknown[]}
   */
  function buildPositionArray(context, refs) {
    const items = Array.isArray(refs) ? refs : unpackPositionList(context, refs);
    return items.map(function mapPosition(item) {
      const property = buildPositionProperty(context, item);
      return getPropertyValue(context, property, currentTime(context)) || property;
    }).filter(Boolean);
  }

  /**
   * @param {LoaderContext} context
   * @param {unknown} refs
   * @returns {JsonObject[]}
   */
  function unpackPositionList(context, refs) {
    const packed = asObject(refs);
    if (Array.isArray(packed.cartographicDegrees)) {
      return unpackTriples(packed.cartographicDegrees, "cartographicDegrees");
    }
    if (Array.isArray(packed.cartographicRadians)) {
      return unpackTriples(packed.cartographicRadians, "cartographicRadians");
    }
    if (Array.isArray(packed.cartesianMeters)) {
      return unpackTriples(packed.cartesianMeters, "cartesianMeters");
    }
    return [];
  }

  /**
   * @param {unknown[]} values
   * @param {string} key
   * @returns {JsonObject[]}
   */
  function unpackTriples(values, key) {
    const result = [];
    for (let index = 0; index + 2 < values.length; index += 3) {
      result.push({ [key]: [Number(values[index]), Number(values[index + 1]), Number(values[index + 2])] });
    }
    return result;
  }

  /**
   * @param {LoaderContext} context
   * @param {JsonObject} point
   * @param {JsonObject} style
   * @returns {JsonObject}
   */
  function buildPointGraphic(context, point, style) {
    return removeUndefined({
      pixelSize: unwrapNumber(point.pixelSize, 10),
      color: buildColorProperty(context, point.color || getNested(style, ["material", "rgba"])),
      outlineColor: buildColorProperty(context, point.outlineColor),
      outlineWidth: unwrapNumber(point.outlineWidth, 0),
      heightReference: heightReference(context, point.heightReference)
    });
  }

  /**
   * @param {LoaderContext} context
   * @param {JsonObject} label
   * @returns {JsonObject}
   */
  function buildLabelGraphic(context, label) {
    const Cesium = context.Cesium;
    return removeUndefined({
      text: unwrapString(label.text, ""),
      font: unwrapString(label.font, "14px sans-serif"),
      style: enumValue(Cesium.LabelStyle, label.style, {
        fill: "FILL",
        outline: "OUTLINE",
        fillAndOutline: "FILL_AND_OUTLINE"
      }) || Cesium.LabelStyle.FILL_AND_OUTLINE,
      fillColor: buildColorProperty(context, label.fillColor) || Cesium.Color.WHITE,
      outlineColor: buildColorProperty(context, label.outlineColor) || Cesium.Color.BLACK,
      outlineWidth: unwrapNumber(label.outlineWidth, 2),
      showBackground: propertyToBoolean(label.showBackground, false),
      backgroundColor: buildColorProperty(context, label.backgroundColor),
      pixelOffset: cartesian2(context, label.pixelOffset),
      eyeOffset: cartesian3(context, label.eyeOffset),
      heightReference: heightReference(context, label.heightReference),
      horizontalOrigin: enumValue(Cesium.HorizontalOrigin, label.horizontalOrigin, {
        left: "LEFT",
        center: "CENTER",
        right: "RIGHT"
      }),
      verticalOrigin: enumValue(Cesium.VerticalOrigin, label.verticalOrigin, {
        bottom: "BOTTOM",
        center: "CENTER",
        top: "TOP",
        baseline: "BASELINE"
      })
    });
  }

  /**
   * @param {LoaderContext} context
   * @param {JsonObject} billboard
   * @returns {JsonObject}
   */
  function buildBillboardGraphic(context, billboard) {
    const Cesium = context.Cesium;
    const asset = resolveAsset(context, String(billboard.asset || ""));
    return removeUndefined({
      image: typeof billboard.image === "string" ? billboard.image : asset.uri,
      scale: unwrapNumber(billboard.scale, 1),
      color: buildColorProperty(context, billboard.color),
      pixelOffset: cartesian2(context, billboard.pixelOffset),
      eyeOffset: cartesian3(context, billboard.eyeOffset),
      heightReference: heightReference(context, billboard.heightReference),
      alignedAxis: cartesian3(context, billboard.alignedAxis),
      horizontalOrigin: enumValue(Cesium.HorizontalOrigin, billboard.horizontalOrigin, {
        left: "LEFT",
        center: "CENTER",
        right: "RIGHT"
      }),
      verticalOrigin: enumValue(Cesium.VerticalOrigin, billboard.verticalOrigin, {
        bottom: "BOTTOM",
        center: "CENTER",
        top: "TOP",
        baseline: "BASELINE"
      })
    });
  }

  /**
   * @param {LoaderContext} context
   * @param {JsonObject} path
   * @param {JsonObject} style
   * @returns {JsonObject}
   */
  function buildPathGraphic(context, path, style) {
    return removeUndefined({
      show: propertyToBoolean(path.show, true),
      leadTime: unwrapNumber(path.leadTimeSeconds, undefined),
      trailTime: unwrapNumber(path.trailTimeSeconds, undefined),
      width: unwrapNumber(path.width || style.width, 2),
      material: buildMaterial(context, asObject(path.material || style.material)),
      resolution: unwrapNumber(path.resolutionSeconds, undefined)
    });
  }

  /**
   * @param {LoaderContext} context
   * @param {JsonObject} material
   * @returns {unknown}
   */
  function buildMaterial(context, material) {
    const Cesium = context.Cesium;
    const type = String(material.type || "solidColor");
    const color = colorFromArray(context, material.rgba || [1, 1, 1, 1]);
    const options = asObject(material.options);

    if (type === "solidColor") {
      return new Cesium.ColorMaterialProperty(color);
    }
    if (type === "polylineGlow") {
      return new Cesium.PolylineGlowMaterialProperty({
        color,
        glowPower: unwrapNumber(options.glowPower, 0.25),
        taperPower: unwrapNumber(options.taperPower, 1)
      });
    }
    if (type === "polylineOutline") {
      return new Cesium.PolylineOutlineMaterialProperty({
        color,
        outlineColor: colorFromArray(context, options.outlineColor || [0, 0, 0, 1]),
        outlineWidth: unwrapNumber(options.outlineWidth, 1)
      });
    }
    if (type === "polylineArrow") {
      return new Cesium.PolylineArrowMaterialProperty(color);
    }
    if (type === "image") {
      return new Cesium.ImageMaterialProperty({
        image: material.uri || resolveAsset(context, String(material.asset || "")).uri,
        color
      });
    }
    return new Cesium.ColorMaterialProperty(color);
  }

  /**
   * @param {LoaderContext} context
   * @param {unknown} value
   * @returns {unknown}
   */
  function buildColorProperty(context, value) {
    const spec = asObject(value);
    if (Array.isArray(value)) {
      return colorFromArray(context, value);
    }
    if (Array.isArray(spec.constant)) {
      return colorFromArray(context, spec.constant);
    }
    return undefined;
  }

  /**
   * @param {LoaderContext} context
   * @param {unknown} value
   * @returns {unknown[]}
   */
  function makeSectorPolygonPositions(context, object) {
    const Cesium = context.Cesium;
    const geometry = asObject(object.geometry);
    const pose = asObject(object.pose);
    const originProperty = buildPositionProperty(context, pose.position);
    const time = currentTime(context);
    const origin = getPropertyValue(context, originProperty, time);
    if (!origin) {
      return [];
    }

    const heading = getHeadingDegrees(asObject(pose.orientation));
    const innerRadius = unwrapNumber(geometry.innerRadiusMeters, 0);
    const outerRadius = unwrapNumber(geometry.outerRadiusMeters, 1000);
    const start = unwrapNumber(geometry.azimuthStartDegrees, 0);
    const stop = unwrapNumber(geometry.azimuthStopDegrees, 360);
    const segments = Math.max(3, Math.floor(unwrapNumber(geometry.segments, 48)));
    const transform = Cesium.Transforms.eastNorthUpToFixedFrame(origin);
    const positions = [];

    for (let i = 0; i <= segments; i += 1) {
      const f = i / segments;
      const bearing = heading + start + (stop - start) * f;
      positions.push(localAzimuthPoint(context, transform, bearing, outerRadius));
    }

    if (innerRadius > 0) {
      for (let i = segments; i >= 0; i -= 1) {
        const f = i / segments;
        const bearing = heading + start + (stop - start) * f;
        positions.push(localAzimuthPoint(context, transform, bearing, innerRadius));
      }
    } else {
      positions.push(origin);
    }

    return positions;
  }

  /**
   * @param {LoaderContext} context
   * @param {unknown} transform
   * @param {number} bearingDegrees
   * @param {number} radiusMeters
   * @returns {unknown}
   */
  function localAzimuthPoint(context, transform, bearingDegrees, radiusMeters) {
    const Cesium = context.Cesium;
    const radians = degreesToRadians(bearingDegrees);
    const east = radiusMeters * Math.sin(radians);
    const north = radiusMeters * Math.cos(radians);
    return Cesium.Matrix4.multiplyByPoint(transform, new Cesium.Cartesian3(east, north, 0), new Cesium.Cartesian3());
  }

  /**
   * @param {LoaderContext} context
   * @param {string} reference
   * @param {unknown} time
   * @returns {unknown}
   */
  function getReferencePosition(context, reference, time) {
    const property = resolveReferenceProperty(context, reference, "position");
    return getPropertyValue(context, property, time);
  }

  /**
   * @param {LoaderContext} context
   * @param {string} reference
   * @param {unknown} time
   * @returns {unknown}
   */
  function getReferenceOrientation(context, reference, time) {
    const property = resolveReferenceProperty(context, reference, "orientation");
    return getPropertyValue(context, property, time);
  }

  /**
   * @param {LoaderContext} context
   * @param {string} reference
   * @param {"position" | "orientation"} fallback
   * @returns {unknown}
   */
  function resolveReferenceProperty(context, reference, fallback) {
    const parts = reference.split("#");
    const id = parts[0];
    const path = parts[1] || `pose.${fallback}`;
    const entity = /** @type {any} */ (context.entities.get(id));
    if (!entity) {
      warn(context, `Reference '${reference}' could not be resolved because '${id}' is not loaded yet.`);
      return undefined;
    }
    if (path.indexOf("orientation") >= 0) {
      return entity.orientation;
    }
    if (path.indexOf("position") >= 0) {
      return entity.position;
    }
    return entity[fallback];
  }

  /**
   * @param {LoaderContext} context
   * @param {unknown} property
   * @param {unknown} time
   * @returns {unknown}
   */
  function getPropertyValue(context, property, time) {
    if (!property) {
      return undefined;
    }
    if (typeof /** @type {any} */ (property).getValue === "function") {
      return /** @type {any} */ (property).getValue(time);
    }
    return property;
  }

  /**
   * @param {LoaderContext} context
   * @param {string} source
   * @param {unknown} time
   * @param {number} windowSeconds
   * @returns {unknown}
   */
  function computeVelocity(context, source, time, windowSeconds) {
    const Cesium = context.Cesium;
    const t0 = Cesium.JulianDate.addSeconds(time, -windowSeconds, new Cesium.JulianDate());
    const t1 = Cesium.JulianDate.addSeconds(time, windowSeconds, new Cesium.JulianDate());
    const p0 = getReferencePosition(context, source, t0);
    const p1 = getReferencePosition(context, source, t1);
    if (!p0 || !p1) {
      return undefined;
    }
    const delta = Cesium.Cartesian3.subtract(p1, p0, new Cesium.Cartesian3());
    return Cesium.Cartesian3.multiplyByScalar(delta, 1 / (2 * windowSeconds), delta);
  }

  /**
   * @param {LoaderContext} context
   * @param {string} source
   * @param {unknown} time
   * @param {number} windowSeconds
   * @returns {unknown}
   */
  function computeAcceleration(context, source, time, windowSeconds) {
    const Cesium = context.Cesium;
    const t0 = Cesium.JulianDate.addSeconds(time, -windowSeconds, new Cesium.JulianDate());
    const t1 = time;
    const t2 = Cesium.JulianDate.addSeconds(time, windowSeconds, new Cesium.JulianDate());
    const p0 = getReferencePosition(context, source, t0);
    const p1 = getReferencePosition(context, source, t1);
    const p2 = getReferencePosition(context, source, t2);
    if (!p0 || !p1 || !p2) {
      return undefined;
    }
    const result = new Cesium.Cartesian3();
    Cesium.Cartesian3.add(p0, p2, result);
    Cesium.Cartesian3.subtract(result, Cesium.Cartesian3.multiplyByScalar(p1, 2, new Cesium.Cartesian3()), result);
    return Cesium.Cartesian3.multiplyByScalar(result, 1 / (windowSeconds * windowSeconds), result);
  }

  /**
   * @param {LoaderContext} context
   * @param {string} axis
   * @param {unknown} orientation
   * @returns {unknown}
   */
  function axisDirection(context, axis, orientation) {
    const Cesium = context.Cesium;
    let unit = Cesium.Cartesian3.UNIT_X;
    if (axis === "y" || axis === "principal1") {
      unit = Cesium.Cartesian3.UNIT_Y;
    } else if (axis === "z" || axis === "principal2") {
      unit = Cesium.Cartesian3.UNIT_Z;
    }
    const matrix = Cesium.Matrix3.fromQuaternion(orientation, new Cesium.Matrix3());
    return Cesium.Matrix3.multiplyByVector(matrix, unit, new Cesium.Cartesian3());
  }

  /**
   * @param {LoaderContext} context
   * @param {unknown} value
   * @param {unknown} timeFormat
   * @param {unknown} epoch
   * @returns {unknown}
   */
  function sampleTime(context, value, timeFormat, epoch) {
    const Cesium = context.Cesium;
    if (timeFormat === "iso8601" || typeof value === "string") {
      return Cesium.JulianDate.fromIso8601(String(value));
    }
    if (!epoch) {
      throw new Error("Sampled values with secondsSinceEpoch require samples.epoch.");
    }
    return Cesium.JulianDate.addSeconds(epoch, Number(value), new Cesium.JulianDate());
  }

  /**
   * @param {LoaderContext} context
   * @param {unknown[]} row
   * @param {unknown} valueFormat
   * @returns {unknown}
   */
  function samplePosition(context, row, valueFormat) {
    const Cesium = context.Cesium;
    const x = Number(row[1]);
    const y = Number(row[2]);
    const z = Number(row[3]);
    if (valueFormat === "cartographicRadians") {
      return Cesium.Cartesian3.fromRadians(x, y, z);
    }
    if (valueFormat === "cartographicDegrees" || !valueFormat) {
      return Cesium.Cartesian3.fromDegrees(x, y, z);
    }
    return new Cesium.Cartesian3(x, y, z);
  }

  /**
   * @param {LoaderContext} context
   * @returns {unknown}
   */
  function currentTime(context) {
    return /** @type {any} */ (context.viewer).clock.currentTime;
  }

  /**
   * @param {LoaderContext} context
   * @param {unknown} value
   * @returns {unknown}
   */
  function referenceFrameValue(context, value) {
    const Cesium = context.Cesium;
    const key = String(value || "FIXED").toUpperCase();
    if (key === "INERTIAL" || key === "ICRF" || key === "ECI") {
      return Cesium.ReferenceFrame.INERTIAL;
    }
    return Cesium.ReferenceFrame.FIXED;
  }

  /**
   * @param {LoaderContext} context
   * @param {string} interpolation
   * @returns {unknown}
   */
  function interpolationAlgorithm(context, interpolation) {
    const Cesium = context.Cesium;
    if (interpolation === "lagrange") {
      return Cesium.LagrangePolynomialApproximation;
    }
    if (interpolation === "hermite") {
      return Cesium.HermitePolynomialApproximation;
    }
    return Cesium.LinearApproximation;
  }

  /**
   * @param {LoaderContext} context
   * @param {unknown} value
   * @returns {unknown}
   */
  function arcType(context, value) {
    const Cesium = context.Cesium;
    return enumValue(Cesium.ArcType, value, {
      none: "NONE",
      geodesic: "GEODESIC",
      rhumb: "RHUMB"
    });
  }

  /**
   * @param {LoaderContext} context
   * @param {unknown} value
   * @returns {unknown}
   */
  function cornerType(context, value) {
    const Cesium = context.Cesium;
    return enumValue(Cesium.CornerType, value, {
      rounded: "ROUNDED",
      mitered: "MITERED",
      beveled: "BEVELED"
    });
  }

  /**
   * @param {LoaderContext} context
   * @param {unknown} value
   * @returns {unknown}
   */
  function heightReference(context, value) {
    const Cesium = context.Cesium;
    return enumValue(Cesium.HeightReference, value, {
      none: "NONE",
      clampToGround: "CLAMP_TO_GROUND",
      relativeToGround: "RELATIVE_TO_GROUND"
    });
  }

  /**
   * @param {Record<string, unknown>} enumObject
   * @param {unknown} value
   * @param {Record<string, string>} mapping
   * @returns {unknown}
   */
  function enumValue(enumObject, value, mapping) {
    if (typeof value !== "string") {
      return undefined;
    }
    const key = mapping[value];
    if (!key) {
      return undefined;
    }
    return enumObject[key];
  }

  /**
   * @param {LoaderContext} context
   * @param {unknown} value
   * @returns {unknown}
   */
  function cartesian2(context, value) {
    const Cesium = context.Cesium;
    if (!Array.isArray(value)) {
      return undefined;
    }
    const v = array2(value, [0, 0]);
    return new Cesium.Cartesian2(v[0], v[1]);
  }

  /**
   * @param {LoaderContext} context
   * @param {unknown} value
   * @returns {unknown}
   */
  function cartesian3(context, value) {
    const Cesium = context.Cesium;
    if (!Array.isArray(value)) {
      return undefined;
    }
    const v = array3(value, [0, 0, 0]);
    return new Cesium.Cartesian3(v[0], v[1], v[2]);
  }

  /**
   * @param {LoaderContext} context
   * @param {JsonObject} spec
   * @returns {unknown}
   */
  function hprFromSpec(context, spec) {
    const Cesium = context.Cesium;
    if (spec.headingPitchRollRadians) {
      const v = array3(spec.headingPitchRollRadians, [0, 0, 0]);
      return new Cesium.HeadingPitchRoll(v[0], v[1], v[2]);
    }
    const v = array3(spec.headingPitchRollDegrees, [0, 0, 0]);
    return new Cesium.HeadingPitchRoll(degreesToRadians(v[0]), degreesToRadians(v[1]), degreesToRadians(v[2]));
  }

  /**
   * @param {JsonObject} orientation
   * @returns {number}
   */
  function getHeadingDegrees(orientation) {
    if (Array.isArray(orientation.headingPitchRollDegrees)) {
      return Number(orientation.headingPitchRollDegrees[0]);
    }
    if (Array.isArray(orientation.headingPitchRollRadians)) {
      return Number(orientation.headingPitchRollRadians[0]) * 180 / Math.PI;
    }
    return 0;
  }

  /**
   * @param {unknown} value
   * @param {number} fallback
   * @returns {number}
   */
  function unwrapNumber(value, fallback) {
    if (typeof value === "number") {
      return value;
    }
    const spec = asObject(value);
    if (typeof spec.constant === "number") {
      return spec.constant;
    }
    return fallback;
  }

  /**
   * @param {unknown} value
   * @param {string} fallback
   * @returns {string}
   */
  function unwrapString(value, fallback) {
    if (typeof value === "string") {
      return value;
    }
    const spec = asObject(value);
    if (typeof spec.constant === "string") {
      return spec.constant;
    }
    return fallback;
  }

  /**
   * @param {unknown} value
   * @param {boolean | undefined} fallback
   * @returns {boolean | undefined}
   */
  function propertyToBoolean(value, fallback) {
    if (typeof value === "boolean") {
      return value;
    }
    const spec = asObject(value);
    if (typeof spec.constant === "boolean") {
      return spec.constant;
    }
    return fallback;
  }

  /**
   * @param {LoaderContext} context
   * @param {unknown} value
   * @returns {unknown}
   */
  function buildAvailability(context, value) {
    const Cesium = context.Cesium;
    if (typeof value !== "string" && !Array.isArray(value)) {
      return undefined;
    }
    const intervals = Array.isArray(value) ? value : [value];
    return new Cesium.TimeIntervalCollection(intervals.map(function mapInterval(interval) {
      return Cesium.TimeInterval.fromIso8601({ iso8601: String(interval) });
    }));
  }

  /**
   * @param {LoaderContext} context
   * @param {unknown} value
   * @returns {unknown}
   */
  function colorFromArray(context, value) {
    const Cesium = context.Cesium;
    const rgba = array4(value, [1, 1, 1, 1]);
    return new Cesium.Color(rgba[0], rgba[1], rgba[2], rgba[3]);
  }

  /**
   * @param {unknown} value
   * @param {number[]} fallback
   * @returns {number[]}
   */
  function array2(value, fallback) {
    if (!Array.isArray(value)) {
      return fallback;
    }
    return [Number(value[0]), Number(value[1])];
  }

  /**
   * @param {unknown} value
   * @param {number[]} fallback
   * @returns {number[]}
   */
  function array3(value, fallback) {
    if (!Array.isArray(value)) {
      return fallback;
    }
    return [Number(value[0]), Number(value[1]), Number(value[2])];
  }

  /**
   * @param {unknown} value
   * @param {number[]} fallback
   * @returns {number[]}
   */
  function array4(value, fallback) {
    if (!Array.isArray(value)) {
      return fallback;
    }
    return [Number(value[0]), Number(value[1]), Number(value[2]), Number(value[3])];
  }

  /**
   * @param {number} degrees
   * @returns {number}
   */
  function degreesToRadians(degrees) {
    return degrees * Math.PI / 180;
  }

  /**
   * @param {JsonObject} object
   * @returns {JsonObject}
   */
  function removeUndefined(object) {
    const result = {};
    for (const [key, value] of Object.entries(object)) {
      if (value !== undefined) {
        result[key] = value;
      }
    }
    return result;
  }

  /**
   * @param {JsonObject} target
   * @param {JsonObject} source
   * @returns {void}
   */
  function assignDefined(target, source) {
    for (const [key, value] of Object.entries(source)) {
      if (value !== undefined) {
        target[key] = value;
      }
    }
  }

  /**
   * @param {LoaderContext} context
   * @param {string} id
   * @returns {JsonObject}
   */
  function resolveAsset(context, id) {
    if (!id) {
      return {};
    }
    return asObject(context.assets[id]);
  }

  /**
   * @param {JsonObject} object
   * @param {string[]} path
   * @returns {unknown}
   */
  function getNested(object, path) {
    let current = object;
    for (const key of path) {
      if (!current || typeof current !== "object") {
        return undefined;
      }
      current = /** @type {JsonObject} */ (current)[key];
    }
    return current;
  }

  /**
   * @param {LoaderContext} context
   * @returns {void}
   */
  function applyInitialView(context) {
    const views = Array.isArray(context.scene.views) ? context.scene.views : [];
    if (views.length === 0) {
      return;
    }
    const view = asObject(views[0]);
    const viewer = /** @type {any} */ (context.viewer);
    const targetId = typeof view.target === "string" ? view.target : "";
    const entity = context.entities.get(targetId);
    if (entity) {
      viewer.zoomTo(entity);
    }
  }


  /** @type {Record<string, {backend: string, target: string, status: string}>} */
  const CESIUM_KIND_TARGETS = {
    point: { backend: "entity", target: "PointGraphics", status: "implemented" },
    billboard: { backend: "entity", target: "BillboardGraphics", status: "implemented" },
    label: { backend: "entity", target: "LabelGraphics", status: "implemented" },
    model: { backend: "entity", target: "ModelGraphics", status: "implemented" },
    track: { backend: "entity", target: "Entity + SampledPositionProperty + optional PathGraphics", status: "implemented" },
    path: { backend: "entity", target: "PolylineGraphics or PathGraphics", status: "implemented" },
    polyline: { backend: "entity", target: "PolylineGraphics", status: "implemented" },
    polygon: { backend: "entity", target: "PolygonGraphics", status: "implemented" },
    rectangle: { backend: "entity", target: "RectangleGraphics", status: "implemented" },
    ellipse: { backend: "entity", target: "EllipseGraphics", status: "implemented" },
    circle: { backend: "entity", target: "EllipseGraphics with equal axes", status: "implemented" },
    box: { backend: "entity", target: "BoxGraphics", status: "implemented" },
    cylinder: { backend: "entity", target: "CylinderGraphics", status: "implemented" },
    cone: { backend: "entity", target: "CylinderGraphics with topRadius = 0", status: "implemented" },
    ellipsoid: { backend: "entity", target: "EllipsoidGraphics", status: "implemented" },
    sphere: { backend: "entity", target: "EllipsoidGraphics with equal radii", status: "implemented" },
    hemisphere: { backend: "primitive", target: "Primitive + generated spherical wedge mesh; Entity ellipsoid fallback available", status: "implemented" },
    sphericalCap: { backend: "primitive", target: "Primitive + generated spherical cap mesh; Entity ellipsoid fallback available", status: "implemented" },
    sectorVolume: { backend: "primitive", target: "Primitive + generated spherical sector-volume mesh; Entity ellipsoid fallback available", status: "implemented" },
    keyhole: { backend: "primitive", target: "Primitive + generated spherical shell/wedge mesh; ion sensor backend can supersede", status: "implemented" },
    conicSensor: { backend: "primitive", target: "Opaque sensor swath placeholder", status: "implemented" },
    rectangularSensor: { backend: "primitive", target: "Opaque sensor swath placeholder", status: "implemented" },
    customPatternSensor: { backend: "primitive", target: "Opaque sensor swath placeholder", status: "implemented" },
    wall: { backend: "entity", target: "WallGraphics", status: "implemented" },
    corridor: { backend: "entity", target: "CorridorGraphics", status: "implemented" },
    polylineVolume: { backend: "entity", target: "PolylineVolumeGraphics", status: "implemented" },
    plane: { backend: "entity", target: "PlaneGraphics", status: "implemented" },
    sector2d: { backend: "entity", target: "PolygonGraphics generated from sector parameters", status: "implemented" },
    bearingFan: { backend: "entity", target: "PolygonGraphics generated from sector parameters", status: "implemented" },
    frustum: { backend: "primitive", target: "Primitive + generated rectangular frustum mesh", status: "implemented" },
    fan: { backend: "entity", target: "PolygonGraphics fallback; ion FanGraphics preferred later", status: "implemented" },
    tileset: { backend: "primitive", target: "Cesium3DTileset", status: "implemented" },
    velocityVector: { backend: "entity", target: "CallbackProperty PolylineGraphics", status: "implemented" },
    accelerationVector: { backend: "entity", target: "CallbackProperty PolylineGraphics", status: "implemented" },
    vector: { backend: "entity", target: "CallbackProperty PolylineGraphics", status: "implemented" },
    bodyAxes: { backend: "entity", target: "three CallbackProperty PolylineGraphics objects", status: "implemented" },
    principalAxes: { backend: "entity", target: "covariance eigenvector-derived CallbackProperty PolylineGraphics", status: "implemented" },
    lineOfSight: { backend: "entity", target: "CallbackProperty PolylineGraphics", status: "implemented" },
    relativeLine: { backend: "entity", target: "CallbackProperty PolylineGraphics", status: "implemented" },
    interceptLine: { backend: "entity", target: "CallbackProperty PolylineGraphics", status: "implemented" },
    rangeRing: { backend: "entity", target: "EllipseGraphics outline", status: "implemented" },
    uncertaintyEllipsoid: { backend: "entity", target: "EllipsoidGraphics", status: "implemented" },
    covarianceEllipse: { backend: "entity", target: "EllipseGraphics", status: "implemented" },
    particleSystem: { backend: "primitive", target: "ParticleSystem", status: "implemented" },
    voxel: { backend: "primitive", target: "VoxelPrimitive", status: "implemented" },
    terrainSurface: { backend: "scene", target: "Opaque runtime attachment placeholder", status: "implemented" },
    customMesh: { backend: "primitive", target: "Opaque runtime mesh placeholder", status: "implemented" },
    clippingPolygon: { backend: "scene", target: "ClippingPolygonCollection", status: "implemented" },
    clippingPlane: { backend: "scene", target: "ClippingPlaneCollection", status: "implemented" },
    classificationVolume: { backend: "primitive", target: "ClassificationPrimitive", status: "implemented" },
    classificationPrimitive: { backend: "primitive", target: "ClassificationPrimitive", status: "implemented" },
    customPrimitive: { backend: "primitive", target: "Primitive + GeometryInstance generated from explicit mesh", status: "implemented" },
    primitiveMesh: { backend: "primitive", target: "Primitive + GeometryInstance generated from explicit mesh", status: "implemented" },
    postProcessStage: { backend: "scene", target: "PostProcessStage", status: "implemented" },
    composite: { backend: "scene", target: "Composite attachment placeholder", status: "implemented" },
    atmosphere: { backend: "scene", target: "Atmosphere settings", status: "implemented" },
    imageryLayer: { backend: "scene", target: "ImageryLayer/provider", status: "implemented" },
    terrain: { backend: "scene", target: "TerrainProvider/Terrain", status: "implemented" },
    czmlDataSource: { backend: "dataSource", target: "CzmlDataSource", status: "implemented" },
    geoJsonDataSource: { backend: "dataSource", target: "GeoJsonDataSource", status: "implemented" },
    kmlDataSource: { backend: "dataSource", target: "KmlDataSource", status: "implemented" },
    dataSource: { backend: "dataSource", target: "DataSource", status: "implemented" },
    tilesetStyle: { backend: "scene", target: "Cesium3DTileStyle", status: "implemented" },
    customShader: { backend: "scene", target: "CustomShader", status: "implemented" },
    cloudCollection: { backend: "primitive", target: "CloudCollection", status: "implemented" },
    skyBox: { backend: "scene", target: "SkyBox", status: "implemented" },
    groundPolyline: { backend: "primitive", target: "GroundPolylinePrimitive", status: "implemented" },
    groundPrimitive: { backend: "primitive", target: "GroundPrimitive", status: "implemented" },
    panorama: { backend: "primitive", target: "inside-out sphere/cube or imagery adapter", status: "implemented" },
    videoPlane: { backend: "entity", target: "PlaneGraphics or RectangleGraphics with video material", status: "implemented" },
    cameraView: { backend: "scene", target: "viewer camera control metadata", status: "implemented" },
    debugInspector: { backend: "scene", target: "CesiumInspector / debug flags", status: "implemented" }
  };

  if (!global.SpatialDisplayJsonKindTargets) {
    global.SpatialDisplayJsonKindTargets = CESIUM_KIND_TARGETS;
  }

  /**
   * Builds a renderer-neutral-to-Cesium compile plan without requiring Cesium to be loaded.
   *
   * @param {JsonObject} scene
   * @returns {{schemaVersion: string, totals: JsonObject, items: JsonObject[], warnings: string[]}}
   */
  function compileSpatialDisplaySceneToCesiumPlan(scene) {
    const items = [];
    const warnings = [];
    const totals = { entity: 0, primitive: 0, scene: 0, dataSource: 0, unsupported: 0, reserved: 0, partial: 0 };
    const objects = Array.isArray(scene.objects) ? scene.objects : [];
    for (const object of objects) {
      compilePlanObject(asObject(object), items, warnings, undefined);
    }
    for (const item of items) {
      const backend = String(item.backend || "unsupported");
      totals[backend] = Number(totals[backend] || 0) + 1;
      const status = String(item.status || "");
      if (status === "reserved" || status === "partial") {
        totals[status] = Number(totals[status] || 0) + 1;
      }
    }
    return {
      schemaVersion: String(scene.schemaVersion || ""),
      totals,
      items,
      warnings
    };
  }

  /**
   * @param {JsonObject} object
   * @param {JsonObject[]} items
   * @param {string[]} warnings
   * @param {string | undefined} parentId
   * @returns {void}
   */
  function compilePlanObject(object, items, warnings, parentId) {
    const id = String(object.id || "");
    const kind = String(object.kind || "");
    if (!id || !kind) {
      warnings.push("Skipping compile-plan item without id or kind.");
      return;
    }
    const target = getCesiumKindTargetsMap()[kind] || { backend: "unsupported", target: "none", status: "unsupported" };
    items.push({
      id,
      kind,
      parentId,
      backend: target.backend,
      target: target.target,
      status: target.status,
      semanticKind: getSemanticKind(object),
      preferredBackends: getPreferredBackends(object)
    });
    const overlays = Array.isArray(object.overlays) ? object.overlays : [];
    for (const overlay of overlays) {
      compilePlanObject(asObject(overlay), items, warnings, id);
    }
  }

  /**
   * Performs lightweight semantic checks that JSON Schema alone cannot express.
   *
   * @param {JsonObject} scene
   * @returns {{errors: string[], warnings: string[]}}
   */
  function validateSpatialDisplaySceneSemantics(scene) {
    const errors = [];
    const warnings = [];
    const assets = asObject(scene.assets);
    const seen = new Set();
    const objects = [];
    collectObjects(Array.isArray(scene.objects) ? scene.objects : [], objects);
    for (const object of objects) {
      const id = String(object.id || "");
      const kind = String(object.kind || "");
      if (!id) {
        errors.push("Object is missing id.");
        continue;
      }
      if (seen.has(id)) {
        errors.push(`Duplicate object id '${id}'.`);
      }
      seen.add(id);
      if (!kind) {
        errors.push(`Object ${id} is missing kind.`);
        continue;
      }
      validateObjectRequirements(object, assets, errors, warnings);
    }
    for (const object of objects) {
      validateObjectReferences(object, seen, errors, warnings);
    }
    return { errors, warnings };
  }

  /**
   * @param {unknown[]} values
   * @param {JsonObject[]} objects
   * @returns {void}
   */
  function collectObjects(values, objects) {
    for (const value of values) {
      const object = asObject(value);
      if (Object.keys(object).length === 0) {
        continue;
      }
      objects.push(object);
      if (Array.isArray(object.overlays)) {
        collectObjects(object.overlays, objects);
      }
    }
  }

  /**
   * @param {JsonObject} object
   * @param {JsonObject} assets
   * @param {string[]} errors
   * @param {string[]} warnings
   * @returns {void}
   */
  function validateObjectRequirements(object, assets, errors, warnings) {
    const id = String(object.id || "");
    const kind = String(object.kind || "");
    const geometry = asObject(object.geometry);
    const pose = asObject(object.pose);
    if (kind === "track" && !asObject(pose.position)) {
      errors.push(`Track ${id} requires pose.position.`);
    }
    if (kind === "model") {
      const model = asObject(object.model);
      const assetId = String(model.asset || object.asset || "");
      if (!model.uri && !assetId) {
        errors.push(`Model ${id} requires model.uri or asset.`);
      }
      if (assetId && !assets[assetId]) {
        errors.push(`Model ${id} references missing asset '${assetId}'.`);
      }
    }
    if (kind === "tileset") {
      const tileset = asObject(object.tileset);
      const assetId = String(tileset.asset || object.asset || "");
      if (!tileset.uri && typeof tileset.ionAssetId !== "number" && !assetId) {
        errors.push(`Tileset ${id} requires tileset.uri, tileset.ionAssetId, or asset.`);
      }
      if (assetId && !assets[assetId]) {
        errors.push(`Tileset ${id} references missing asset '${assetId}'.`);
      }
    }
    if ((kind === "sector2d" || kind === "bearingFan" || kind === "fan") && typeof geometry.outerRadiusMeters !== "number") {
      errors.push(`${kind} ${id} requires geometry.outerRadiusMeters.`);
    }
    if ((kind === "keyhole" || kind === "sectorVolume") && typeof geometry.outerRadiusMeters !== "number") {
      errors.push(`${kind} ${id} requires geometry.outerRadiusMeters.`);
    }
    if (kind === "lineOfSight" && (!geometry.from || !geometry.to)) {
      errors.push(`lineOfSight ${id} requires geometry.from and geometry.to references.`);
    }
    if ((kind === "velocityVector" || kind === "accelerationVector") && !geometry.source) {
      warnings.push(`${kind} ${id} has no geometry.source; loader may only render if a local position and direction are supplied.`);
    }
    if (kind === "principalAxes" && !geometry.covarianceMatrix && !geometry.covarianceUpperTriangle && !geometry.directions) {
      warnings.push(`principalAxes ${id} has no covarianceMatrix, covarianceUpperTriangle, or explicit directions; default local axes will be used.`);
    }
  }

  /**
   * @param {JsonObject} object
   * @param {Set<string>} ids
   * @param {string[]} errors
   * @param {string[]} warnings
   * @returns {void}
   */
  function validateObjectReferences(object, ids, errors, warnings) {
    const id = String(object.id || "");
    const encoded = JSON.stringify(object);
    const pattern = /"([A-Za-z0-9_.:-]+)#([^"\\]+)"/g;
    let match = pattern.exec(encoded);
    while (match) {
      const targetId = match[1];
      if (!ids.has(targetId)) {
        errors.push(`Object ${id} references missing object '${targetId}'.`);
      }
      match = pattern.exec(encoded);
    }
    if (String(object.kind || "") === "customPrimitive" && !Array.isArray(asObject(object.geometry).positions)) {
      warnings.push(`customPrimitive ${id} has no explicit positions; a renderer plugin may be required.`);
    }
  }

  /**
   * @param {JsonObject} object
   * @returns {string | undefined}
   */
  function getSemanticKind(object) {
    const hints = asObject(object.rendererHints);
    return typeof hints.semanticKind === "string" ? hints.semanticKind : undefined;
  }

  /**
   * @param {JsonObject} object
   * @returns {string[]}
   */
  function getPreferredBackends(object) {
    const hints = asObject(object.rendererHints);
    return Array.isArray(hints.preferredBackends) ? hints.preferredBackends.map(String) : [];
  }

  /**
   * @returns {Record<string, {backend: string, target: string, status: string}>}
   */
  function getCesiumKindTargets() {
    return Object.assign({}, getCesiumKindTargetsMap());
  }

  /**
   * @returns {Record<string, {backend: string, target: string, status: string}>}
   */
  function getCesiumKindTargetsMap() {
    return global.SpatialDisplayJsonKindTargets || CESIUM_KIND_TARGETS;
  }

  global.SpatialDisplayJson = {
    loadSpatialDisplayScene,
    compileSpatialDisplaySceneToCesiumPlan,
    validateSpatialDisplaySceneSemantics,
    getCesiumKindTargets
  };
})(globalThis);
