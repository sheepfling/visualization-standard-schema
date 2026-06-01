import { asArray, asNumber, asObject, asString, toJson } from "./json.js";
import { buildCompilePlan, buildTargetDiagnostics } from "./plan.js";
import { flattenObjects, isShown } from "./scene.js";
import { createZipBlob } from "./zip.js";

/**
 * @typedef {Record<string, unknown>} JsonObject
 * @typedef {{files: Record<string, string>, manifest: JsonObject, compilePlan: JsonObject, diagnostics: {severity: string, code: string, path: string, message: string}[]}} BackendBundle
 */

/**
 * Builds artifacts for a single backend.
 *
 * @param {JsonObject} scene
 * @param {string} target
 * @returns {BackendBundle}
 */
export function compileBackend(scene, target) {
  const compilePlan = buildCompilePlan(scene);
  if (target === "cesium") {
    return compileCesium(scene, compilePlan);
  }
  if (target === "simdis") {
    return compileSimdis(scene, compilePlan);
  }
  if (target === "soap") {
    return compileSoap(scene, compilePlan);
  }
  throw new Error(`Unsupported SDJ export target '${target}'.`);
}

/**
 * Builds artifacts for all supported backends.
 *
 * @param {JsonObject} scene
 * @returns {Record<string, BackendBundle>}
 */
export function compileAllBackends(scene) {
  return {
    cesium: compileBackend(scene, "cesium"),
    simdis: compileBackend(scene, "simdis"),
    soap: compileBackend(scene, "soap")
  };
}

/**
 * Creates a flat combined ZIP file map for all targets.
 *
 * @param {JsonObject} scene
 * @returns {Record<string, string>}
 */
export function compileAllBackendsToFiles(scene) {
  const bundles = compileAllBackends(scene);
  /** @type {Record<string, string>} */
  const files = {
    "compile-plan-all-targets.json": toJson(buildCompilePlan(scene))
  };
  for (const [target, bundle] of Object.entries(bundles)) {
    for (const [path, content] of Object.entries(bundle.files)) {
      files[path] = content;
    }
    files[`${target}/bundle-summary.json`] = toJson({
      target,
      manifest: bundle.manifest,
      diagnostics: bundle.diagnostics
    });
  }
  return files;
}

/**
 * @param {JsonObject} scene
 * @param {JsonObject} compilePlan
 * @returns {BackendBundle}
 */
function compileCesium(scene, compilePlan) {
  const manifest = {
    target: "cesium",
    source: asObject(scene.document).id,
    mode: "render",
    artifacts: [
      { kind: "sceneJson", path: "cesium/scene.sdj.json" },
      { kind: "compilePlan", path: "cesium/compile-plan.json" },
      { kind: "loader", path: "vendor/sdj_cesium_loader_v0_4.js" }
    ],
    objectCount: compilePlan.objectCount,
    analysisCount: compilePlan.analysisCount,
    presentationCount: compilePlan.presentationCount,
    totals: asObject(asObject(compilePlan.targetTotals).cesium)
  };
  const diagnostics = buildTargetDiagnostics(compilePlan, "cesium");
  return {
    manifest,
    compilePlan,
    diagnostics,
    files: {
      "cesium/manifest.json": toJson(manifest),
      "cesium/scene.sdj.json": toJson(scene),
      "cesium/compile-plan.json": toJson(compilePlan),
      "cesium/diagnostics.json": toJson({ diagnostics }),
      "cesium/README.md": renderCesiumReadme()
    }
  };
}

/**
 * @param {JsonObject} scene
 * @param {JsonObject} compilePlan
 * @returns {BackendBundle}
 */
function compileSimdis(scene, compilePlan) {
  const objects = flattenObjects(asArray(scene.objects).map(asObject));
  const entities = {
    platforms: objects.filter((object) => object.kind === "track").map((object) => toPlatformState(object)),
    annotations: objects.filter((object) => ["point", "billboard", "label"].includes(String(object.kind))).map((object) => toAnnotation(object)),
    sensors: objects.filter((object) => ["sectorVolume", "keyhole", "hemisphere", "sphericalCap", "frustum", "conicSensor", "rectangularSensor", "customPatternSensor", "fan", "bearingFan"].includes(String(object.kind))).map((object) => toSensorState(object)),
    vectors: objects.filter((object) => ["vector", "velocityVector", "accelerationVector", "bodyAxes", "principalAxes", "lineOfSight", "relativeLine", "interceptLine"].includes(String(object.kind))).map((object) => toVectorState(object))
  };
  const diagnostics = buildTargetDiagnostics(compilePlan, "simdis");
  const manifest = {
    target: "simdis",
    source: asObject(scene.document).id,
    mode: "scene-to-gog+scene-to-entities+scene-to-presentation",
    profiles: scene.profiles,
    artifacts: [
      { kind: "manifest", path: "simdis/manifest.json" },
      { kind: "gog", path: "simdis/overlays.gog" },
      { kind: "entityState", path: "simdis/entities.json" },
      { kind: "analysis", path: "simdis/analysis.json" },
      { kind: "presentation", path: "simdis/presentation.json" },
      { kind: "assetManifest", path: "simdis/assets.json" },
      { kind: "diagnostics", path: "simdis/diagnostics.json" }
    ],
    totals: asObject(asObject(compilePlan.targetTotals).simdis)
  };
  const analysis = { results: asArray(scene.analysis).map(asObject) };
  const presentation = buildSimdisPresentation(scene);
  const assets = buildAssetManifest(scene);
  const bundle = {
    target: "simdis",
    source: asObject(scene.document).id,
    manifest,
    entities,
    analysis,
    presentation,
    assets,
    diagnostics
  };
  return {
    manifest,
    compilePlan,
    diagnostics,
    files: {
      "simdis/manifest.json": toJson(manifest),
      "simdis/entities.json": toJson(entities),
      "simdis/overlays.gog": buildGog(objects),
      "simdis/analysis.json": toJson(analysis),
      "simdis/presentation.json": toJson(presentation),
      "simdis/assets.json": toJson(assets),
      "simdis/diagnostics.json": toJson({ diagnostics }),
      "simdis/generated/simdis-example-bundle.json": toJson(bundle)
    }
  };
}

/**
 * @param {JsonObject} scene
 * @param {JsonObject} compilePlan
 * @returns {BackendBundle}
 */
function compileSoap(scene, compilePlan) {
  const objects = flattenObjects(asArray(scene.objects).map(asObject));
  const tracks = objects.filter((object) => object.kind === "track");
  const scenario = {
    id: asObject(scene.document).id,
    name: asObject(scene.document).name,
    clock: scene.clock,
    units: scene.units,
    platforms: tracks.map((object) => toSoapPlatform(object)),
    trajectories: tracks.map((object) => toSoapTrajectory(object)),
    models: objects.filter((object) => object.kind === "model").map((object) => toSoapModel(object)),
    sensorSwaths: objects.filter((object) => ["sectorVolume", "keyhole", "hemisphere", "sphericalCap", "frustum", "conicSensor", "rectangularSensor", "customPatternSensor", "fan"].includes(String(object.kind))).map((object) => toSoapSensorSwath(object)),
    overlays: objects.filter((object) => ["polyline", "polygon", "rectangle", "ellipse", "circle", "rangeRing", "lineOfSight", "relativeLine", "interceptLine"].includes(String(object.kind))).map((object) => toSoapOverlay(object)),
    extensions: asObject(scene.extensions).soap || {}
  };
  const views = buildSoapViews(scene);
  const analysis = { results: asArray(scene.analysis).map(asObject) };
  const presentation = buildSoapPresentation(scene);
  const assets = buildAssetManifest(scene);
  const diagnostics = buildTargetDiagnostics(compilePlan, "soap");
  const overlayFiles = buildSoapAnalysisOverlayFiles(scene);
  const manifest = {
    target: "soap",
    source: asObject(scene.document).id,
    mode: "scene-to-scenario+scene-to-analysis+scene-to-presentation",
    profiles: scene.profiles,
    artifacts: [
      { kind: "manifest", path: "soap/manifest.json" },
      { kind: "scenario", path: "soap/scenario.json" },
      { kind: "views", path: "soap/views.json" },
      { kind: "analysis", path: "soap/analysis.json" },
      { kind: "presentation", path: "soap/presentation.json" },
      { kind: "assetManifest", path: "soap/assets.json" },
      { kind: "diagnostics", path: "soap/diagnostics.json" },
      ...Object.keys(overlayFiles).map((path) => ({ kind: "overlay", path }))
    ],
    totals: asObject(asObject(compilePlan.targetTotals).soap)
  };
  const bundle = {
    target: "soap",
    source: asObject(scene.document).id,
    manifest,
    scenario,
    views,
    analysis,
    presentation,
    assets,
    diagnostics,
    overlays: Object.keys(overlayFiles)
  };
  return {
    manifest,
    compilePlan,
    diagnostics,
    files: {
      "soap/manifest.json": toJson(manifest),
      "soap/scenario.json": toJson(scenario),
      "soap/views.json": toJson(views),
      "soap/analysis.json": toJson(analysis),
      "soap/presentation.json": toJson(presentation),
      "soap/assets.json": toJson(assets),
      "soap/diagnostics.json": toJson({ diagnostics }),
      "soap/generated/soap-example-bundle.json": toJson(bundle),
      ...overlayFiles
    }
  };
}

/**
 * @param {JsonObject} scene
 * @returns {JsonObject}
 */
function buildAssetManifest(scene) {
  const assets = asObject(scene.assets);
  return {
    assets: Object.entries(assets).map(([id, value]) => ({ id, ...asObject(value) }))
  };
}

/**
 * @param {JsonObject} object
 * @returns {JsonObject}
 */
function toPlatformState(object) {
  return {
    id: object.id,
    name: object.name,
    kind: "platform",
    category: asObject(object.properties).platformType || "platform",
    trajectory: extractTrajectory(object),
    initialPosition: extractPosition(asObject(asObject(object.pose).position)),
    orientation: asObject(asObject(object.pose).orientation),
    label: asObject(object.label),
    trackHistory: Boolean(asObject(object.path).show ?? true),
    properties: asObject(object.properties)
  };
}

/**
 * @param {JsonObject} object
 * @returns {JsonObject}
 */
function toAnnotation(object) {
  return {
    id: object.id,
    kind: object.kind,
    name: object.name,
    position: extractPosition(asObject(asObject(object.pose).position)),
    label: asObject(object.label),
    billboard: asObject(object.billboard),
    point: asObject(object.point),
    show: isShown(object.show)
  };
}

/**
 * @param {JsonObject} object
 * @returns {JsonObject}
 */
function toSensorState(object) {
  return {
    id: object.id,
    kind: object.kind,
    name: object.name,
    hostId: sensorHost(object),
    pose: asObject(object.pose),
    geometry: asObject(object.geometry),
    style: asObject(object.style),
    show: isShown(object.show),
    simdisTarget: simdisSensorTarget(String(object.kind || "sensor"))
  };
}

/**
 * @param {JsonObject} object
 * @returns {JsonObject}
 */
function toVectorState(object) {
  return {
    id: object.id,
    kind: object.kind,
    name: object.name,
    geometry: asObject(object.geometry),
    style: asObject(object.style),
    show: isShown(object.show)
  };
}

/**
 * @param {JsonObject[]} objects
 * @returns {string}
 */
function buildGog(objects) {
  const lines = ["gog version 2", "# Generated by SDJ Workbench browser compiler"];
  for (const object of objects) {
    if (!isShown(object.show)) {
      continue;
    }
    const kind = String(object.kind || "");
    const geometry = asObject(object.geometry);
    if (kind === "polyline" || kind === "groundPolyline") {
      emitGogLine(lines, object, asArray(geometry.positions));
    } else if (kind === "polygon") {
      const rings = asArray(geometry.rings);
      emitGogPolygon(lines, object, asArray(rings[0]));
    } else if (kind === "circle" || kind === "rangeRing") {
      emitGogCircle(lines, object, geometry);
    } else if (kind === "ellipse" || kind === "covarianceEllipse") {
      emitGogEllipse(lines, object, geometry);
    } else if (kind === "rectangle") {
      emitGogRectangle(lines, object, geometry);
    } else if (kind === "sector2d" || kind === "bearingFan" || kind === "fan") {
      emitGogSectorComment(lines, object, geometry);
    } else if (["sectorVolume", "keyhole", "hemisphere", "sphericalCap", "frustum", "conicSensor", "rectangularSensor", "customPatternSensor"].includes(kind)) {
      emitGogSensorComment(lines, object, geometry);
    }
  }
  return `${lines.join("\n")}\n`;
}

function emitGogLine(lines, object, positions) {
  if (positions.length < 2) {
    return;
  }
  lines.push(`begin line # ${object.id}`);
  lines.push("  linecolor 255 255 255 255");
  lines.push("  linewidth 2");
  for (const position of positions) {
    const lla = toLonLatAlt(asObject(position));
    if (lla) {
      lines.push(`  ll ${lla.lat.toFixed(8)} ${lla.lon.toFixed(8)} ${lla.alt.toFixed(2)}`);
    }
  }
  lines.push("end");
}

function emitGogPolygon(lines, object, positions) {
  if (positions.length < 3) {
    return;
  }
  lines.push(`begin polygon # ${object.id}`);
  lines.push("  linecolor 0 255 255 255");
  lines.push("  fillcolor 0 255 255 64");
  for (const position of positions) {
    const lla = toLonLatAlt(asObject(position));
    if (lla) {
      lines.push(`  ll ${lla.lat.toFixed(8)} ${lla.lon.toFixed(8)} ${lla.alt.toFixed(2)}`);
    }
  }
  lines.push("end");
}

function emitGogCircle(lines, object, geometry) {
  const lla = objectCenterLla(object);
  const radius = asNumber(geometry.radiusMeters) || asNumber(geometry.outerRadiusMeters) || 1000;
  if (!lla) {
    return;
  }
  lines.push(`begin circle # ${object.id}`);
  lines.push(`  centerll ${lla.lat.toFixed(8)} ${lla.lon.toFixed(8)} ${lla.alt.toFixed(2)}`);
  lines.push(`  radius ${radius}`);
  lines.push("  linecolor 0 255 0 255");
  lines.push("end");
}

function emitGogEllipse(lines, object, geometry) {
  const lla = objectCenterLla(object);
  if (!lla) {
    return;
  }
  lines.push(`begin ellipse # ${object.id}`);
  lines.push(`  centerll ${lla.lat.toFixed(8)} ${lla.lon.toFixed(8)} ${lla.alt.toFixed(2)}`);
  lines.push(`  majoraxis ${asNumber(geometry.semiMajorAxisMeters) || 1000}`);
  lines.push(`  minoraxis ${asNumber(geometry.semiMinorAxisMeters) || 500}`);
  lines.push("  linecolor 255 255 0 255");
  lines.push("end");
}

function emitGogRectangle(lines, object, geometry) {
  const bounds = asArray(geometry.westSouthEastNorthDegrees);
  if (bounds.length !== 4) {
    return;
  }
  const west = Number(bounds[0]);
  const south = Number(bounds[1]);
  const east = Number(bounds[2]);
  const north = Number(bounds[3]);
  lines.push(`begin polygon # ${object.id}`);
  lines.push("  linecolor 255 255 255 255");
  for (const point of [[west, south], [east, south], [east, north], [west, north]]) {
    const lon = Number(point[0]);
    const lat = Number(point[1]);
    lines.push(`  ll ${lat.toFixed(8)} ${lon.toFixed(8)} 0.00`);
  }
  lines.push("end");
}

function emitGogSectorComment(lines, object, geometry) {
  const lla = objectCenterLla(object);
  lines.push(`# begin sector ${object.id}`);
  lines.push(`# center ${lla ? `${lla.lat} ${lla.lon} ${lla.alt}` : "reference-or-derived"}`);
  lines.push(`# radius ${geometry.outerRadiusMeters ?? geometry.radiusMeters ?? "unknown"}`);
  lines.push(`# azimuth ${geometry.azimuthStartDegrees ?? "unknown"} ${geometry.azimuthStopDegrees ?? "unknown"}`);
  lines.push(`# end sector ${object.id}`);
}

function emitGogSensorComment(lines, object, geometry) {
  lines.push(`# sensor-volume ${object.id} kind=${object.kind} geometry=${JSON.stringify(geometry)}`);
}

function objectCenterLla(object) {
  return toLonLatAlt(asObject(asObject(object.pose).position));
}

function toLonLatAlt(position) {
  const value = asArray(position.cartographicDegrees);
  if (value.length >= 3) {
    return { lon: Number(value[0]), lat: Number(value[1]), alt: Number(value[2]) };
  }
  return undefined;
}

function sensorHost(object) {
  const pose = asObject(object.pose);
  const position = asObject(pose.position);
  const reference = asString(position.reference);
  if (reference) {
    return reference.split("#")[0];
  }
  return undefined;
}

function simdisSensorTarget(kind) {
  if (kind === "rectangularSensor" || kind === "frustum") {
    return "gate/projector";
  }
  if (kind === "customPatternSensor") {
    return "antenna pattern / custom beam";
  }
  if (kind === "keyhole" || kind === "sectorVolume") {
    return "GOG wedge + beam semantics";
  }
  return "beam / LOB / projector";
}

function buildSimdisPresentation(scene) {
  const items = asArray(scene.presentation).map(asObject);
  return {
    views: items.filter((item) => ["view", "reportView", "plotView", "dataView"].includes(String(item.kind))).map((item) => ({ id: item.id, kind: item.kind, name: item.name || item.title, target: item.target })),
    slides: items.filter((item) => item.kind === "slide").map((item) => ({ id: item.id, title: item.title, startTime: item.startTime, stopTime: item.stopTime, views: item.views || [] })),
    cameraActions: items.filter((item) => item.kind === "cameraAction").map((item) => ({ id: item.id, target: item.target, camera: item.camera || {}, durationSeconds: item.durationSeconds })),
    popups: items.filter((item) => ["popup", "banner", "annotation"].includes(String(item.kind))).map((item) => ({ id: item.id, kind: item.kind, title: item.title, target: item.target }))
  };
}

function toSoapPlatform(object) {
  return {
    id: object.id,
    name: object.name,
    kind: "Platform",
    modelRef: modelForPlatform(String(object.id || "")),
    initialState: extractPosition(asObject(asObject(object.pose).position)),
    properties: asObject(object.properties)
  };
}

function modelForPlatform(platformId) {
  if (platformId === "air-track-17") {
    return "air-track-17-model";
  }
  if (platformId === "air-track-42") {
    return "track-42-model";
  }
  return undefined;
}

function toSoapTrajectory(object) {
  return {
    id: `${object.id}-trajectory`,
    platformId: object.id,
    source: "sdj.sampledPosition",
    samples: extractTrajectory(object)
  };
}

function toSoapModel(object) {
  return {
    id: object.id,
    name: object.name,
    asset: object.asset || asObject(object.model).asset || asObject(object.model).uri,
    pose: asObject(object.pose),
    model: asObject(object.model)
  };
}

function toSoapSensorSwath(object) {
  return {
    id: object.id,
    kind: object.kind,
    name: object.name,
    hostPlatform: sensorHost(object),
    geometry: asObject(object.geometry),
    pose: asObject(object.pose),
    nativeTarget: soapSensorTarget(String(object.kind || "sensor"))
  };
}

function soapSensorTarget(kind) {
  if (kind === "keyhole" || kind === "sectorVolume") {
    return "Sensor Swath + Contour";
  }
  if (kind === "conicSensor" || kind === "customPatternSensor") {
    return "Sensor Swath / RF Communications object";
  }
  if (kind === "frustum" || kind === "rectangularSensor") {
    return "World View sensor volume";
  }
  return "Sensor Swath";
}

function toSoapOverlay(object) {
  return {
    id: object.id,
    kind: object.kind,
    name: object.name,
    geometry: asObject(object.geometry),
    style: asObject(object.style)
  };
}

function buildSoapViews(scene) {
  const presentation = asArray(scene.presentation).map(asObject);
  const viewItems = presentation.filter((item) => ["view", "reportView", "plotView", "dataView"].includes(String(item.kind)));
  return {
    views: viewItems.map((item) => ({
      id: item.id,
      kind: soapViewKind(String(item.kind)),
      name: item.name || item.title,
      target: item.target,
      rendererHints: item.rendererHints || {}
    })),
    palettes: presentation.filter((item) => item.kind === "palette").map((item) => ({ id: item.id, title: item.title, viewports: item.viewports || [] }))
  };
}

function soapViewKind(kind) {
  if (kind === "reportView") {
    return "Report";
  }
  if (kind === "plotView") {
    return "Plot";
  }
  if (kind === "dataView") {
    return "Data";
  }
  return "World";
}

function buildSoapPresentation(scene) {
  const items = asArray(scene.presentation).map(asObject);
  return {
    presentation: items.find((item) => item.kind === "presentation") || null,
    slides: items.filter((item) => item.kind === "slide"),
    actions: items.filter((item) => ["cameraAction", "bookmark", "popup", "banner", "movie"].includes(String(item.kind))).map((item, index) => ({
      order: index,
      id: item.id,
      kind: item.kind,
      title: item.title,
      target: item.target,
      durationSeconds: item.durationSeconds,
      camera: item.camera || {}
    }))
  };
}

function buildSoapAnalysisOverlayFiles(scene) {
  /** @type {Record<string, string>} */
  const files = {};
  for (const analysis of asArray(scene.analysis).map(asObject)) {
    const fileName = `${analysis.id || analysis.kind || "analysis"}.json`.replace(/[^A-Za-z0-9_.-]/g, "_");
    const relative = `soap/overlays/${fileName}`;
    files[relative] = toJson({
      id: analysis.id,
      kind: analysis.kind,
      analysisType: analysis.analysisType,
      participants: analysis.participants || [],
      intervals: analysis.intervals || [],
      samples: analysis.samples || [],
      metrics: analysis.metrics || {},
      grid: analysis.grid || {}
    });
  }
  return files;
}

function extractPosition(positionProperty) {
  const lla = toLonLatAlt(positionProperty);
  if (lla) {
    return { frame: "cartographicDegrees", ...lla };
  }
  const reference = asString(positionProperty.reference);
  if (reference) {
    return { reference };
  }
  if (positionProperty.samples) {
    const samples = asObject(positionProperty.samples);
    return { sampled: true, epoch: samples.epoch, valueFormat: samples.valueFormat || "cartesianMeters" };
  }
  return null;
}

function extractTrajectory(object) {
  const position = asObject(asObject(object.pose).position);
  const samples = asObject(position.samples);
  const values = asArray(samples.values);
  return values.map((sample) => {
    const row = asArray(sample);
    return {
      t: row[0],
      valueFormat: samples.valueFormat || "cartesianMeters",
      referenceFrame: samples.referenceFrame || "FIXED",
      value: row.slice(1)
    };
  });
}

function renderCesiumReadme() {
  return [
    "# Cesium bundle",
    "",
    "This bundle contains the normalized SDJ scene and compile plan for the Cesium runtime adapter.",
    "Load `scene.sdj.json` with `SpatialDisplayJson.loadSpatialDisplayScene(viewer, scene, options)`.",
    ""
  ].join("\n");
}
