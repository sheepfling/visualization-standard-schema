import { asArray, asObject, toJson, type JsonObject } from "./json.ts";
import {
  buildAssetManifest,
  buildSceneDiagnostics,
  buildSceneObjectList,
  extractPosition,
  extractSoapTrajectory,
  formatIsoTimestamp,
  normalizeSoapOverlayStyle,
  sensorHost,
  toLonLatAlt
} from "./backend_utils.ts";
import { collectRuntimeObjects } from "./runtime_objects.ts";

export type BackendBundle = {
  files: Record<string, string>;
  manifest: JsonObject;
  compilePlan: JsonObject;
  diagnostics: JsonObject[];
};

export function compileSoap(scene: JsonObject, compilePlan: JsonObject): BackendBundle {
  const objects = buildSceneObjectList(scene);
  const tracks = objects.filter((object) => object.kind === "track");
  const scenario = {
    id: asObject(scene.document).id,
    name: asObject(scene.document).name,
    clock: buildSoapClock(objects),
    units: asObject(scene.units),
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
  const customObjects = asArray(scene.customObjects).map(asObject);
  const runtimeObjects = collectRuntimeObjects(scene);
  const diagnostics = buildSceneDiagnostics(objects, "soap");
  const overlayFiles = buildSoapAnalysisOverlayFiles(scene);
  const manifest = {
    target: "soap",
    source: asObject(scene.document).id,
    mode: "scene-to-scenario+scene-to-analysis+scene-to-presentation",
    profiles: asArray(scene.profiles),
    artifacts: [
      { kind: "manifest", path: "soap/manifest.json" },
      { kind: "scenario", path: "soap/scenario.json" },
      { kind: "views", path: "soap/views.json" },
      { kind: "analysis", path: "soap/analysis.json" },
      { kind: "presentation", path: "soap/presentation.json" },
      { kind: "assetManifest", path: "soap/assets.json" },
      { kind: "diagnostics", path: "soap/diagnostics.json" },
      { kind: "customObjects", path: "soap/custom-objects.json" },
      { kind: "runtimeObjects", path: "soap/runtime-objects.json" },
      ...Object.keys(overlayFiles).map((path) => ({ kind: "overlay", path }))
    ],
    totals: {
      platforms: scenario.platforms.length,
      trajectories: scenario.trajectories.length,
      models: scenario.models.length,
      sensorSwaths: scenario.sensorSwaths.length,
      overlays: scenario.overlays.length,
      customObjects: customObjects.length,
      runtimeObjects: runtimeObjects.length
    }
  };
  const bundle = { target: "soap", source: asObject(scene.document).id, manifest, scenario, views, analysis, presentation, assets, diagnostics, overlays: Object.keys(overlayFiles), customObjects, runtimeObjects };
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
      "soap/custom-objects.json": toJson({ customObjects }),
      "soap/runtime-objects.json": toJson({ runtimeObjects }),
      "soap/generated/soap-example-bundle.json": toJson(bundle),
      ...overlayFiles
    }
  };
}

function toSoapPlatform(object: JsonObject): JsonObject {
  return {
    id: object.id,
    name: object.name,
    kind: "Platform",
    initialState: extractPosition(asObject(asObject(object.pose).position)),
    properties: {
      ...asObject(object.properties),
      ...(object.kind ? { bridgeKind: object.kind } : {}),
      ...(object.path ? { path: asObject(object.path) } : {}),
      ...(asObject(object.properties).platformType ? { category: asObject(object.properties).platformType } : {}),
      ...(asObject(object.properties).source ? { source: asObject(object.properties).source } : {})
    }
  };
}

function toSoapTrajectory(object: JsonObject): JsonObject {
  return { id: `${object.id}-trajectory`, platformId: object.id, source: "vss.scene.entity", samples: extractSoapTrajectory(object) };
}

function toSoapModel(object: JsonObject): JsonObject {
  return {
    id: object.id,
    name: object.name,
    asset: object.asset || asObject(object.model).asset || asObject(object.model).uri,
    pose: asObject(object.pose),
    model: asObject(object.model)
  };
}

function toSoapSensorSwath(object: JsonObject): JsonObject {
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

function soapSensorTarget(kind: string): string {
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

function toSoapOverlay(object: JsonObject): JsonObject {
  const geometry = asObject(object.geometry);
  const positions = String(object.kind || geometry.type || "") === "polygon"
    ? asArray(asArray(geometry.rings)[0]).map(asObject)
    : asArray(geometry.positions).map(asObject);
  return {
    id: object.id,
    name: object.name,
    kind: object.kind,
    style: normalizeSoapOverlayStyle(object.style, geometry),
    positions: positions.map((position) => {
      const lla = toLonLatAlt(position);
      return lla ? { longitudeDeg: lla.lon, latitudeDeg: lla.lat, altitudeM: lla.alt } : position;
    }),
    properties: {}
  };
}

function buildSoapViews(scene: JsonObject): JsonObject {
  const objects = asArray(scene.objects).map(asObject);
  const firstEntity = objects.find((item) => ["track", "model", "point", "billboard", "label"].includes(String(item.kind)));
  const sceneId = String(asObject(scene.document).id || "scene");
  const sceneName = String(asObject(scene.document).name || sceneId);
  return {
    views: firstEntity
      ? [
          {
            id: `${sceneId}-overview`,
            kind: "View",
            name: `${sceneName} Overview`,
            target: firstEntity.id,
            camera: extractPosition(asObject(asObject(firstEntity.pose).position)) || {}
          }
        ]
      : [],
    palettes: [
      {
        id: `${sceneId}-default-palette`,
        name: "Default Palette",
        entries: [
          { kind: "entity-count", value: objects.filter((item) => item.kind === "track" || item.kind === "model" || item.kind === "point" || item.kind === "billboard" || item.kind === "label").length },
          { kind: "overlay-count", value: objects.filter((item) => ["polyline", "polygon", "rectangle", "ellipse", "circle", "rangeRing", "lineOfSight", "relativeLine", "interceptLine"].includes(String(item.kind))).length }
        ]
      }
    ]
  };
}

function buildSoapPresentation(scene: JsonObject): JsonObject {
  return { slides: [], actions: [] };
}

function buildSoapAnalysisOverlayFiles(scene: JsonObject): Record<string, string> {
  const files: Record<string, string> = {};
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

function buildSoapClock(objects: JsonObject[]): JsonObject {
  const timestamps = objects
    .map((object) => asObject(object).timestamp)
    .filter((timestamp): timestamp is string => typeof timestamp === "string" && timestamp.length > 0);
  if (timestamps.length === 0) {
    return {};
  }
  const sorted = [...timestamps].sort();
  const start = sorted[0];
  const stop = sorted[sorted.length - 1];
  return { startTime: formatIsoTimestamp(start), stopTime: formatIsoTimestamp(stop), currentTime: formatIsoTimestamp(stop) };
}
