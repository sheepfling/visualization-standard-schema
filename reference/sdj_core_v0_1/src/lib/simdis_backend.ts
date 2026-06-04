import { asArray, asNumber, asObject, asString, toJson, type JsonObject } from "./json.ts";
import type { Diagnostic } from "./scene.ts";
import {
  buildAssetManifest,
  buildSceneDiagnostics,
  buildSceneObjectList,
  defaultPlatformIcon,
  extractPosition,
  extractTrajectory,
  formatFloat,
  formatHeading,
  formatIsoTimestamp,
  normalizeOverlayStyle,
  referenceYearForScene,
  sensorHost,
  styleRgba,
  toLonLatAlt
} from "./backend_utils.ts";
import { collectRuntimeObjects } from "./runtime_objects.ts";
import { isShown } from "./scene.ts";

export type BackendBundle = {
  files: Record<string, string>;
  manifest: JsonObject;
  compilePlan: JsonObject;
  diagnostics: Diagnostic[];
};

export function compileSimdis(scene: JsonObject, compilePlan: JsonObject): BackendBundle {
  const objects = buildSceneObjectList(scene);
  const tracks = objects.filter((object) => object.kind === "track");
  const overlayObjects = objects.filter((object) => ["polyline", "polygon", "rectangle", "ellipse", "circle", "rangeRing", "wall", "corridor"].includes(String(object.kind)));
  const customObjects = asArray(scene.customObjects).map(asObject);
  const runtimeObjects = collectRuntimeObjects(scene);
  const scenarioAsi = buildSimdisScenarioAsi(scene, objects);
  const overlayGog = buildSimdisOverlayGog(objects);
  const entities = {
    platforms: tracks.map((object) => toPlatformState(object)),
    annotations: objects.filter((object) => ["point", "billboard", "label"].includes(String(object.kind))).map((object) => toAnnotation(object)),
    sensors: objects.filter((object) => ["sectorVolume", "keyhole", "hemisphere", "sphericalCap", "frustum", "conicSensor", "rectangularSensor", "customPatternSensor", "fan", "bearingFan"].includes(String(object.kind))).map((object) => toSensorState(object)),
    beams: [],
    gates: [],
    projectors: [],
    vectors: [
      ...objects.filter((object) => ["vector", "velocityVector", "accelerationVector", "bodyAxes", "principalAxes", "lineOfSight", "relativeLine", "interceptLine"].includes(String(object.kind))).map((object) => toVectorState(object)),
      ...overlayObjects.map((object) => toVectorStateFromOverlay(object))
    ],
    overlays: overlayObjects.map((object) => toOverlayState(object))
  };
  const diagnostics = buildSceneDiagnostics(objects, "simdis");
  const manifest = {
    target: "simdis",
    source: asObject(scene.document).id,
    mode: "scene-to-gog+scene-to-entities+scene-to-presentation",
    profiles: asArray(scene.profiles),
    artifacts: [
      { kind: "manifest", path: "simdis/manifest.json" },
      { kind: "entityState", path: "simdis/entities.json" },
      { kind: "entityStateNormalized", path: "simdis/entities.normalized.json" },
      { kind: "gog", path: "simdis/overlays.gog" },
      { kind: "gogNormalized", path: "simdis/overlays.normalized.json" },
      { kind: "asi", path: "simdis/scenario.asi" },
      { kind: "analysis", path: "simdis/analysis.json" },
      { kind: "presentation", path: "simdis/presentation.json" },
      { kind: "assetManifest", path: "simdis/assets.json" },
      { kind: "diagnostics", path: "simdis/diagnostics.json" },
      { kind: "customObjects", path: "simdis/custom-objects.json" },
      { kind: "runtimeObjects", path: "simdis/runtime-objects.json" }
    ],
    totals: {
      platforms: entities.platforms.length,
      sensors: entities.sensors.length,
      annotations: entities.annotations.length,
      beams: 0,
      gates: 0,
      projectors: 0,
      vectors: entities.vectors.length,
      overlays: entities.overlays.length,
      customObjects: customObjects.length,
      runtimeObjects: runtimeObjects.length
    }
  };
  const analysis = { results: asArray(scene.analysis).map(asObject) };
  const presentation = buildSimdisPresentation(scene);
  const assets = buildAssetManifest(scene);
  const bundle = { target: "simdis", source: asObject(scene.document).id, manifest, entities, scenarioAsi, overlaysGog: overlayGog, analysis, presentation, assets, diagnostics, customObjects, runtimeObjects };
  return {
    manifest,
    compilePlan,
    diagnostics,
    files: {
      "simdis/manifest.json": toJson(manifest),
      "simdis/entities.json": toJson(entities),
      "simdis/entities.normalized.json": toJson(entities),
      "simdis/overlays.gog": overlayGog,
      "simdis/overlays.normalized.json": toJson({ overlays: entities.overlays }),
      "simdis/scenario.asi": scenarioAsi,
      "simdis/analysis.json": toJson(analysis),
      "simdis/presentation.json": toJson(presentation),
      "simdis/assets.json": toJson(assets),
      "simdis/diagnostics.json": toJson({ diagnostics }),
      "simdis/custom-objects.json": toJson({ customObjects }),
      "simdis/runtime-objects.json": toJson({ runtimeObjects }),
      "simdis/generated/simdis-example-bundle.json": toJson(bundle)
    }
  };
}

function buildSimdisScenarioAsi(scene: JsonObject, objects: JsonObject[]): string {
  const lines = [`ReferenceYear ${referenceYearForScene(scene, objects)}`, "DegreeAngles 1", ""];
  for (const object of objects) {
    if (object.kind !== "track") {
      continue;
    }
    lines.push(...buildSimdisPlatformLines(object));
    lines.push("");
  }
  return `${lines.join("\n").trimEnd()}\n`;
}

function toPlatformState(object: JsonObject): JsonObject {
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
    properties: {
      ...asObject(object.properties),
      ...(object.kind ? { bridgeKind: object.kind } : {}),
      ...(object.path ? { path: asObject(object.path) } : {})
    }
  };
}

function toAnnotation(object: JsonObject): JsonObject {
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

function toSensorState(object: JsonObject): JsonObject {
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

function toVectorState(object: JsonObject): JsonObject {
  return {
    id: object.id,
    kind: object.kind,
    name: object.name,
    geometry: asObject(object.geometry),
    style: asObject(object.style),
    show: isShown(object.show)
  };
}

function toVectorStateFromOverlay(object: JsonObject): JsonObject {
  const geometry = asObject(object.geometry);
  const positions = String(object.kind || geometry.type || "") === "polygon"
    ? asArray(asArray(geometry.rings)[0]).map(asObject)
    : asArray(geometry.positions).map(asObject);
  return {
    id: object.id,
    kind: "vector",
    name: object.name,
    geometry: {
      type: String(geometry.type || object.kind || "polyline"),
      clampToGround: Boolean(geometry.clampToGround ?? false),
      widthPx: geometry.widthPx,
      positions: positions.map((position) => {
        const lla = toLonLatAlt(position);
        return lla ? { lon: lla.lon, lat: lla.lat, alt: lla.alt } : position;
      })
    },
    style: normalizeOverlayStyle(asObject(object.style)),
    show: isShown(object.show)
  };
}

function toOverlayState(object: JsonObject): JsonObject {
  const geometry = asObject(object.geometry);
  const positions = String(object.kind || geometry.type || "") === "polygon"
    ? asArray(asArray(geometry.rings)[0]).map(asObject)
    : asArray(geometry.positions).map(asObject);
  return {
    id: object.id,
    kind: "overlay",
    name: object.name,
    geometry: {
      type: String(object.kind || "polyline"),
      clampToGround: Boolean(geometry.clampToGround ?? false),
      widthPx: geometry.widthPx,
      positions: positions.map((position) => {
        const lla = toLonLatAlt(position);
        return lla ? { lon: lla.lon, lat: lla.lat, alt: lla.alt } : position;
      })
    },
    style: {},
    show: isShown(object.show)
  };
}

function buildSimdisOverlayGog(objects: JsonObject[]): string {
  const lines = ["# VSS SIMDIS export scene bundle"];
  for (const object of objects) {
    const kind = String(object.kind || "");
    if (kind === "track") {
      lines.push(...buildSimdisOverlayPlatformLines(object));
      continue;
    }
    if (kind === "point" || kind === "billboard" || kind === "label") {
      lines.push(...buildSimdisAnnotationGog(object));
      continue;
    }
    if (kind === "polyline" || kind === "groundPolyline") {
      lines.push(...buildSimdisPolylineGog(object));
    } else if (kind === "polygon") {
      lines.push(...buildSimdisPolygonGog(object));
    } else if (kind === "circle" || kind === "rangeRing") {
      lines.push(...buildSimdisCircleGog(object));
    } else if (kind === "ellipse" || kind === "covarianceEllipse") {
      lines.push(...buildSimdisEllipseGog(object));
    } else if (kind === "rectangle") {
      lines.push(...buildSimdisRectangleGog(object));
    } else if (kind === "sector2d" || kind === "bearingFan" || kind === "fan") {
      lines.push(...buildSimdisSectorComments(object));
    } else if (["sectorVolume", "keyhole", "hemisphere", "sphericalCap", "frustum", "conicSensor", "rectangularSensor", "customPatternSensor"].includes(kind)) {
      lines.push(...buildSimdisSensorComments(object));
    }
  }
  return `${lines.join("\n")}\n`;
}

function buildSimdisPlatformLines(object: JsonObject): string[] {
  const properties = asObject(object.properties);
  const pose = asObject(object.pose);
  const position = asObject(pose.position);
  const cartographic = asArray(position.cartographicDegrees);
  const orientation = asObject(pose.orientation);
  const samples = asObject(position.samples);
  const values = asArray(samples.values);
  const timestamp = values.length > 0 && Array.isArray(values[0]) && typeof values[0][0] === "string"
    ? formatIsoTimestamp(values[0][0])
    : formatIsoTimestamp(samples.epoch);
  const entityId = String(object.id || "");
  const name = String(object.name || entityId);
  const category = String(properties.platformType || "platform");
  const heading = formatHeading(orientation.headingDeg ?? 0);
  const pitch = formatFloat(orientation.pitchDeg ?? 0);
  const roll = formatFloat(orientation.rollDeg ?? 0);
  const icon = defaultPlatformIcon(category);
  const lines = [
    `PlatformID ${entityId}`,
    `PlatformName ${entityId} "${name}"`,
    `PLATFORM ${entityId} NAME "${name}" CATEGORY ${category}`,
    `PlatformIcon ${entityId} "${icon}"`
  ];
  const labelObject = asObject(object.label);
  const label = asString(labelObject.text ?? labelObject.label ?? object.label);
  if (label) {
    lines.push(`PLATFORM_LABEL ${entityId} "${label}"`);
  }
  lines.push(
    "PLATFORM_UPDATE "
    + `${entityId} ${timestamp} `
    + `${Number(cartographic[1] ?? 0).toFixed(4)} `
    + `${Number(cartographic[0] ?? 0).toFixed(4)} `
    + `${Number(cartographic[2] ?? 0).toFixed(3)} `
    + `${heading} ${pitch} ${roll} 0 0 0`
  );
  return lines;
}

function buildSimdisOverlayPlatformLines(object: JsonObject): string[] {
  const properties = asObject(object.properties);
  const pose = asObject(object.pose);
  const position = asObject(pose.position);
  const cartographic = asArray(position.cartographicDegrees);
  const orientation = asObject(pose.orientation);
  const samples = asObject(position.samples);
  const values = asArray(samples.values);
  const timestamp = values.length > 0 && Array.isArray(values[0]) && typeof values[0][0] === "string"
    ? formatIsoTimestamp(values[0][0])
    : formatIsoTimestamp(samples.epoch);
  const entityId = String(object.id || "");
  const name = String(object.name || entityId);
  const category = String(properties.platformType || "platform");
  return [
    `PLATFORM ${entityId} NAME "${name}" CATEGORY ${category}`,
    "PLATFORM_UPDATE "
      + `${entityId} ${timestamp} `
      + `${Number(cartographic[1] ?? 0).toFixed(8)} `
      + `${Number(cartographic[0] ?? 0).toFixed(8)} `
      + `${Number(cartographic[2] ?? 0).toFixed(3)} `
      + `${Number(orientation.headingDeg ?? 0).toFixed(3)} ${Number(orientation.pitchDeg ?? 0).toFixed(3)} ${Number(orientation.rollDeg ?? 0).toFixed(3)}`
  ];
}

function simdisSensorTarget(kind: string): string {
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

function buildSimdisPresentation(scene: JsonObject): JsonObject {
  const items = asArray(scene.presentation).map(asObject);
  return {
    views: items.filter((item) => ["view", "reportView", "plotView", "dataView"].includes(String(item.kind))).map((item) => ({ id: item.id, kind: item.kind, name: item.name || item.title, target: item.target })),
    slides: items.filter((item) => item.kind === "slide").map((item) => ({ id: item.id, title: item.title, startTime: item.startTime, stopTime: item.stopTime, views: item.views || [] })),
    cameraActions: items.filter((item) => item.kind === "cameraAction").map((item) => ({ id: item.id, target: item.target, camera: item.camera || {}, durationSeconds: item.durationSeconds })),
    popups: items.filter((item) => ["popup", "banner", "annotation"].includes(String(item.kind))).map((item) => ({ id: item.id, kind: item.kind, title: item.title, target: item.target }))
  };
}

function buildSimdisAnnotationGog(object: JsonObject): string[] {
  const labelObject = asObject(object.label);
  const label = asString(labelObject.text ?? labelObject.label ?? object.label);
  const posePoint = asObject(object.pose).position;
  const lla = toLonLatAlt(asObject(posePoint));
  const lines = [`start_annotation ${object.id}`, `  name "${object.name || object.id}"`];
  if (label) {
    lines.push(`  label "${label}"`);
  }
  const billboard = asObject(object.billboard);
  if (billboard.image) {
    lines.push(`  billboard "${billboard.image}"`);
  }
  const pointStyle = asObject(object.point);
  const pointColor = asArray(pointStyle.color);
  if (pointColor.length >= 3) {
    lines.push(`  pointcolor ${pointColor[0]} ${pointColor[1]} ${pointColor[2]}`);
  }
  if (lla) {
    lines.push(`  position ${lla.lat.toFixed(8)} ${lla.lon.toFixed(8)} ${lla.alt.toFixed(3)}`);
  }
  lines.push("end_annotation");
  return lines;
}

function buildSimdisPolylineGog(object: JsonObject): string[] {
  const geometry = asObject(object.geometry);
  const positions = asArray(geometry.positions).map(asObject);
  if (positions.length < 2) {
    return [];
  }
  const style = asObject(object.style);
  const rgba = styleRgba(style, [255, 255, 255, 255]);
  const lines = [`start_gog ${object.id}`, "polyline", `  linecolor ${rgba[0]} ${rgba[1]} ${rgba[2]}`, `  linewidth ${(Number(asNumber(geometry.widthPx) ?? 2)).toFixed(1)}`];
  if (style.label) {
    lines.push(`  label "${style.label}"`);
  }
  for (const position of positions) {
    const lla = toLonLatAlt(position);
    if (lla) {
      lines.push(`  point ${lla.lat.toFixed(8)} ${lla.lon.toFixed(8)} ${lla.alt.toFixed(3)}`);
    }
  }
  lines.push("end_gog");
  return lines;
}

function buildSimdisPolygonGog(object: JsonObject): string[] {
  const geometry = asObject(object.geometry);
  const rings = asArray(geometry.rings);
  const positions = asArray(rings[0]).map(asObject);
  if (positions.length < 3) {
    return [];
  }
  const style = asObject(object.style);
  const rgba = styleRgba(style, [255, 255, 255, 255]);
  const lines = [`start_gog ${object.id}`, "polygon", `  linecolor ${rgba[0]} ${rgba[1]} ${rgba[2]}`, `  fillcolor ${rgba[0]} ${rgba[1]} ${rgba[2]}`];
  if (style.label) {
    lines.push(`  label "${style.label}"`);
  }
  for (const position of positions) {
    const lla = toLonLatAlt(position);
    if (lla) {
      lines.push(`  point ${lla.lat.toFixed(8)} ${lla.lon.toFixed(8)} ${lla.alt.toFixed(3)}`);
    }
  }
  lines.push("end_gog");
  return lines;
}

function buildSimdisCircleGog(object: JsonObject): string[] {
  const geometry = asObject(object.geometry);
  const lla = objectCenterLla(object);
  if (!lla) {
    return [];
  }
  const radius = asNumber(geometry.radiusMeters) || asNumber(geometry.outerRadiusMeters) || 1000;
  return [`# begin circle ${object.id}`, `# center ${lla.lat} ${lla.lon} ${lla.alt}`, `# radius ${radius}`, `# end circle ${object.id}`];
}

function buildSimdisEllipseGog(object: JsonObject): string[] {
  const geometry = asObject(object.geometry);
  const lla = objectCenterLla(object);
  if (!lla) {
    return [];
  }
  return [`# begin ellipse ${object.id}`, `# center ${lla.lat} ${lla.lon} ${lla.alt}`, `# majoraxis ${asNumber(geometry.semiMajorAxisMeters) || 1000}`, `# minoraxis ${asNumber(geometry.semiMinorAxisMeters) || 500}`, `# end ellipse ${object.id}`];
}

function buildSimdisRectangleGog(object: JsonObject): string[] {
  const geometry = asObject(object.geometry);
  const bounds = asArray(geometry.westSouthEastNorthDegrees);
  if (bounds.length !== 4) {
    return [];
  }
  const west = Number(bounds[0]);
  const south = Number(bounds[1]);
  const east = Number(bounds[2]);
  const north = Number(bounds[3]);
  return [`# begin rectangle ${object.id}`, `# bounds ${west} ${south} ${east} ${north}`, `# end rectangle ${object.id}`];
}

function buildSimdisSectorComments(object: JsonObject): string[] {
  const geometry = asObject(object.geometry);
  const lla = objectCenterLla(object);
  return [`# begin sector ${object.id}`, `# center ${lla ? `${lla.lat} ${lla.lon} ${lla.alt}` : "reference-or-derived"}`, `# radius ${geometry.outerRadiusMeters ?? geometry.radiusMeters ?? "unknown"}`, `# azimuth ${geometry.azimuthStartDegrees ?? "unknown"} ${geometry.azimuthStopDegrees ?? "unknown"}`, `# end sector ${object.id}`];
}

function buildSimdisSensorComments(object: JsonObject): string[] {
  return [`# sensor-volume ${object.id} kind=${object.kind} geometry=${JSON.stringify(asObject(object.geometry))}`];
}

function objectCenterLla(object: JsonObject): { lon: number; lat: number; alt: number } | undefined {
  return toLonLatAlt(asObject(asObject(object.pose).position));
}
