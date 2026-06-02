import { asArray, asObject, toJson, type JsonObject } from "./json.ts";
import { buildTargetDiagnostics } from "./plan.ts";
import { buildSceneObjectList, formatIsoTimestamp } from "./backend_utils.ts";

export type BackendBundle = {
  files: Record<string, string>;
  manifest: JsonObject;
  compilePlan: JsonObject;
  diagnostics: { severity: string; code: string; path: string; message: string }[];
};

export function compileCesium(scene: JsonObject, compilePlan: JsonObject): BackendBundle {
  const packets = buildCesiumPackets(scene);
  const manifest = {
    target: "cesium",
    source: asObject(scene.document).id,
    mode: "render",
    artifacts: [
      { kind: "sceneJson", path: "cesium/scene.sdj.json" },
      { kind: "compilePlan", path: "cesium/compile-plan.json" },
      { kind: "packetArray", path: "cesium/generated/cesium-example-bundle.json" },
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
      "cesium/generated/cesium-example-bundle.json": toJson(packets),
      "cesium/diagnostics.json": toJson({ diagnostics }),
      "cesium/README.md": renderCesiumReadme()
    }
  };
}

function buildCesiumPackets(scene: JsonObject): JsonObject[] {
  const objects = buildSceneObjectList(scene);
  const clock = buildCesiumClock(objects);
  const packets: JsonObject[] = [
    {
      id: "document",
      name: asObject(scene.document).name,
      version: "1.0",
      ...(clock ? { clock } : {})
    }
  ];
  for (const object of objects) {
    if (object.kind === "track") {
      packets.push(buildCesiumEntityPacket(object));
    } else if (["polyline", "polygon", "rectangle", "ellipse", "circle", "rangeRing", "wall", "corridor", "sector2d", "bearingFan", "fan", "sectorVolume", "keyhole", "hemisphere", "sphericalCap", "frustum", "conicSensor", "rectangularSensor", "customPatternSensor"].includes(String(object.kind))) {
      packets.push(buildCesiumOverlayPacket(object));
    }
  }
  return packets;
}

function buildCesiumClock(objects: JsonObject[]): JsonObject | null {
  const timestamps = objects
    .map((object) => asObject(object).timestamp)
    .filter((timestamp): timestamp is string => typeof timestamp === "string" && timestamp.length > 0)
    .map((timestamp) => formatIsoTimestamp(timestamp));
  if (timestamps.length === 0) {
    return null;
  }
  const sorted = [...timestamps].sort();
  const start = sorted[0];
  const stop = sorted[sorted.length - 1];
  return {
    interval: `${start}/${stop}`,
    currentTime: stop,
    multiplier: 1,
    range: "CLAMPED",
    step: "SYSTEM_CLOCK_MULTIPLIER"
  };
}

function buildCesiumEntityPacket(object: JsonObject): JsonObject {
  const position = asObject(asObject(object.pose).position);
  const cartographic = asArray(position.cartographicDegrees);
  const properties = {
    ...asObject(object.properties),
    ...(object.kind ? { bridgeKind: object.kind } : {}),
    ...(asObject(object.properties).platformType ? { category: asObject(object.properties).platformType } : {}),
    ...(object.properties?.source ? { source: object.properties.source } : {}),
    ...(object.path ? { path: asObject(object.path) } : {}),
    ...(object.timestamp ? { timestamp: formatIsoTimestamp(object.timestamp) } : {})
  };
  if (asObject(object.pose).orientation) {
    properties.orientationDegrees = {
      heading: Number(asObject(object.pose).orientation.headingDeg ?? 0),
      pitch: Number(asObject(object.pose).orientation.pitchDeg ?? 0),
      roll: Number(asObject(object.pose).orientation.rollDeg ?? 0)
    };
  }
  const packet: JsonObject = {
    id: object.id,
    name: object.name,
    position: {
      cartographicDegrees: [
        Number(cartographic[0] ?? 0),
        Number(cartographic[1] ?? 0),
        Number(cartographic[2] ?? 0)
      ]
    },
    properties,
    point: {
      pixelSize: 10,
      outlineWidth: 1
    }
  };
  const style = asObject(object.style);
  const rgba = asArray(style.colorRgba);
  if (style.label) {
    packet.label = {
      text: style.label,
      horizontalOrigin: "LEFT",
      pixelOffset: { cartesian2: [12, 0] }
    };
    if (rgba.length >= 4) {
      packet.label.fillColor = { rgba: rgba.map((component) => Number(component)) };
    }
  }
  if (rgba.length >= 4) {
    packet.point.color = { rgba: rgba.map((component) => Number(component)) };
    packet.point.outlineColor = { rgba: [255, 255, 255, 255] };
  }
  return packet;
}

function buildCesiumOverlayPacket(object: JsonObject): JsonObject {
  const position = asObject(asObject(object.pose).position);
  const cartographic = asArray(position.cartographicDegrees);
  const geometry = asObject(object.geometry);
  const style = asObject(object.style);
  const rgba = asArray(style.colorRgba);
  const packet: JsonObject = {
    id: object.id,
    name: object.name,
    position: {
      cartographicDegrees: [
        Number(cartographic[0] ?? 0),
        Number(cartographic[1] ?? 0),
        Number(cartographic[2] ?? 0)
      ]
    },
    properties: {
      objectType: "overlay",
      category: "overlay"
    }
  };
  if (style.label) {
    packet.label = {
      text: style.label,
      horizontalOrigin: "LEFT",
      pixelOffset: { cartesian2: [12, 0] }
    };
    if (rgba.length >= 4) {
      packet.label.fillColor = { rgba: rgba.map((component) => Number(component)) };
    }
  }
  if (String(object.kind || "") === "polyline") {
    packet.polyline = {
      positions: {
        cartographicDegrees: flattenCesiumPositions(asArray(geometry.positions).map(asObject))
      },
      width: Number(geometry.widthPx ?? 2),
      clampToGround: Boolean(geometry.clampToGround ?? false)
    };
    if (rgba.length >= 4) {
      packet.polyline.material = { solidColor: { color: { rgba: rgba.map((component) => Number(component)) } } };
    }
  } else if (String(object.kind || "") === "polygon") {
    packet.polygon = {
      positions: {
        cartographicDegrees: flattenCesiumPositions(asArray(asArray(geometry.rings)[0]).map(asObject))
      },
      perPositionHeight: !Boolean(geometry.clampToGround ?? false),
      arcType: "GEODESIC"
    };
    if (rgba.length >= 4) {
      packet.polygon.material = { solidColor: { color: { rgba: rgba.map((component) => Number(component)) } } };
    }
  }
  return packet;
}

function flattenCesiumPositions(positions: JsonObject[]): number[] {
  const flat: number[] = [];
  for (const position of positions) {
    const cartographic = asArray(position.cartographicDegrees);
    flat.push(Number(cartographic[0] ?? 0), Number(cartographic[1] ?? 0), Number(cartographic[2] ?? 0));
  }
  return flat;
}

function renderCesiumReadme(): string {
  return [
    "# Cesium bundle",
    "",
    "This bundle contains the normalized SDJ scene and compile plan for the Cesium runtime adapter.",
    "Load `scene.sdj.json` with `SpatialDisplayJson.loadSpatialDisplayScene(viewer, scene, options)`.",
    ""
  ].join("\n");
}
