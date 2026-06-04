import { asArray, asNumber, asObject, asString, type JsonObject } from "./json.ts";
import type { Diagnostic } from "./scene.ts";
import { flattenObjects, isShown } from "./scene.ts";

export function dedupeByIdAndKind(objects: JsonObject[]): JsonObject[] {
  const seen = new Set<string>();
  const result: JsonObject[] = [];
  for (const object of objects) {
    const id = String(object.id || "");
    const kind = String(object.kind || "");
    const key = `${id}::${kind}`;
    if (!id || !kind || seen.has(key)) {
      continue;
    }
    seen.add(key);
    result.push(object);
  }
  return result;
}

export function buildAssetManifest(scene: JsonObject): JsonObject {
  const assets = asObject(scene.assets);
  return {
    assets: Object.entries(assets).map(([id, value]) => ({ id, ...asObject(value) }))
  };
}

export function formatIsoTimestamp(value: any): string {
  if (value == null) {
    return "-1";
  }
  const text = String(value).trim();
  if (!text) {
    return "-1";
  }
  return text.endsWith("Z") ? text.slice(0, -1) + "+00:00" : text;
}

export function formatFloat(value: any): string {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return "0";
  }
  if (Number.isInteger(number)) {
    return String(number);
  }
  return number.toFixed(3).replace(/0+$/, "").replace(/\.$/, "");
}

export function formatHeading(value: any): string {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return "000";
  }
  if (Number.isInteger(number)) {
    return String(number).padStart(3, "0");
  }
  return number.toFixed(3).replace(/0+$/, "").replace(/\.$/, "");
}

export function defaultPlatformIcon(category: string): string {
  return {
    air: "aircraft",
    ground: "site",
    surface: "ship",
    subsurface: "subsurface",
    space: "satellite",
    sensor: "sensor",
    overlay: "site",
    other: "platform"
  }[category] || "platform";
}

export function styleRgba(style: JsonObject, fallback: [number, number, number, number]): [number, number, number, number] {
  const rgba = asArray(style?.colorRgba);
  if (rgba.length >= 4) {
    return [Number(rgba[0]), Number(rgba[1]), Number(rgba[2]), Number(rgba[3])];
  }
  return fallback;
}

export function normalizeOverlayStyle(style: JsonObject): JsonObject {
  const normalized: JsonObject = {};
  const label = asString(style?.label);
  if (label) {
    normalized.label = label;
  }
  const colorRgba = asArray(style?.colorRgba);
  if (colorRgba.length >= 4) {
    normalized.colorRgba = colorRgba.map((component) => Number(component));
  }
  return normalized;
}

export function normalizeSoapOverlayStyle(style: JsonObject, geometry: JsonObject): JsonObject {
  const normalized: JsonObject = { colorRgba: [] };
  const label = asString(style?.label);
  if (label) {
    normalized.label = label;
  }
  const colorRgba = asArray(style?.colorRgba);
  if (colorRgba.length >= 4) {
    normalized.colorRgba = colorRgba.map((component) => Number(component));
  }
  if (geometry?.widthPx != null) {
    normalized.widthPx = Number(geometry.widthPx);
  }
  normalized.clampToGround = Boolean(geometry?.clampToGround ?? false);
  return normalized;
}

export function toLonLatAlt(position: JsonObject): { lon: number; lat: number; alt: number } | undefined {
  const value = asArray(position.cartographicDegrees);
  if (value.length >= 3) {
    return { lon: Number(value[0]), lat: Number(value[1]), alt: Number(value[2]) };
  }
  return undefined;
}

export function sensorHost(object: JsonObject): string | undefined {
  const pose = asObject(object.pose);
  const position = asObject(pose.position);
  const reference = asString(position.reference);
  if (reference) {
    return reference.split("#")[0];
  }
  return undefined;
}

export function buildSceneDiagnostics(objects: JsonObject[], target: "simdis" | "soap"): Diagnostic[] {
  const diagnostics: Diagnostic[] = [];
  for (const object of objects) {
    if (object.kind === "track" && !object.timestamp) {
      const code = target === "simdis" ? "SIMDIS-SCENE-MISSING-TIMESTAMP" : "SOAP-SCENE-MISSING-TIMESTAMP";
      const message = target === "simdis"
        ? `Entity '${String(object.id || "")}' has no timestamp; scene or fallback time was used for SIMDIS export.`
        : `Entity '${String(object.id || "")}' has no timestamp; SOAP trajectory export was omitted.`;
      diagnostics.push({ severity: "warning", code, path: `entities/${String(object.id || "")}`, message });
    }
  }
  return diagnostics;
}

export function referenceYearForScene(scene: JsonObject, objects: JsonObject[]): number {
  const candidates: number[] = [];
  const created = asObject(scene.document).created;
  if (typeof created === "string" && created.length >= 4) {
    const year = Number(created.slice(0, 4));
    if (Number.isFinite(year)) {
      candidates.push(year);
    }
  }
  for (const object of objects) {
    if (typeof object.timestamp === "string" && object.timestamp.length >= 4) {
      const year = Number(String(object.timestamp).slice(0, 4));
      if (Number.isFinite(year)) {
        candidates.push(year);
      }
    }
  }
  return candidates.length > 0 ? Math.max(...candidates) : 1970;
}

export function buildSceneObjectList(scene: JsonObject): JsonObject[] {
  return flattenObjects(asArray(scene.objects).map(asObject));
}

export function extractPosition(positionProperty: JsonObject): JsonObject | null {
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

export function extractTrajectory(object: JsonObject): JsonObject[] {
  const position = asObject(asObject(object.pose).position);
  const samples = asObject(position.samples);
  const values = asArray(samples.values);
  return values.map((sample) => {
    const row = asArray(sample);
    return {
      t: formatIsoTimestamp(row[0]),
      valueFormat: "cartesianMeters",
      referenceFrame: samples.referenceFrame || "FIXED",
      value: row.slice(1)
    };
  });
}

export function extractSoapTrajectory(object: JsonObject): JsonObject[] {
  const position = asObject(asObject(object.pose).position);
  const samples = asObject(position.samples);
  const values = asArray(samples.values);
  return values.map((sample) => {
    const row = asArray(sample);
    return {
      t: formatIsoTimestamp(row[0]),
      valueFormat: "cartographicDegrees",
      value: row.slice(1)
    };
  });
}
