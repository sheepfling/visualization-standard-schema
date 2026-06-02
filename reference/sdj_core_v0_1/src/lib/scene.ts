import { asArray, asObject, asString, cloneJson, type JsonObject } from "./json.ts";

export interface Diagnostic {
  severity: string;
  code: string;
  path: string;
  message: string;
}

export function normalizeSceneForWorkbench(scene: JsonObject, defaultCapabilities: JsonObject | undefined): JsonObject {
  const normalized = cloneJson(scene);
  if (!normalized.schemaVersion) {
    normalized.schemaVersion = "sdj-0.4";
  }
  if (!normalized.backendCapabilities && defaultCapabilities) {
    normalized.backendCapabilities = cloneJson(defaultCapabilities);
  }
  if (!Array.isArray(normalized.objects)) {
    normalized.objects = [];
  }
  if (!Array.isArray(normalized.analysis)) {
    normalized.analysis = [];
  }
  if (!Array.isArray(normalized.presentation)) {
    normalized.presentation = [];
  }
  return normalized;
}

export function flattenObjects(objects: JsonObject[], prefix = "objects"): JsonObject[] {
  const result: JsonObject[] = [];
  objects.forEach((object, index) => {
    const cloned: JsonObject = { ...object, __path: `${prefix}/${index}` };
    result.push(cloned);
    const overlays = asArray(object.overlays).map(asObject);
    if (overlays.length > 0) {
      result.push(...flattenObjects(overlays, `${prefix}/${index}/overlays`));
    }
  });
  return result;
}

export function isShown(value: unknown): boolean {
  if (value === false) {
    return false;
  }
  const object = asObject(value);
  if (object.constant === false) {
    return false;
  }
  return true;
}

export function findObject(scene: JsonObject, id: string): JsonObject | undefined {
  return flattenObjects(asArray(scene.objects).map(asObject)).find((object) => object.id === id);
}

export function validateSemantics(scene: JsonObject): { errors: Diagnostic[]; warnings: Diagnostic[] } {
  const errors: Diagnostic[] = [];
  const warnings: Diagnostic[] = [];
  const objects = flattenObjects(asArray(scene.objects).map(asObject));
  const ids = new Set<string>();

  for (const object of objects) {
    const id = asString(object.id);
    const kind = asString(object.kind);
    const path = String(object.__path || "objects/?");
    if (!id) {
      errors.push({ severity: "error", code: "SDJ-ID-MISSING", path, message: "Object is missing an id." });
      continue;
    }
    if (ids.has(id)) {
      errors.push({ severity: "error", code: "SDJ-ID-DUPLICATE", path, message: `Duplicate object id '${id}'.` });
    }
    ids.add(id);
    if (!kind) {
      errors.push({ severity: "error", code: "SDJ-KIND-MISSING", path, message: `Object '${id}' is missing kind.` });
    }
    if (kind === "track" && !asObject(object.pose).position) {
      errors.push({ severity: "error", code: "SDJ-TRACK-NO-POSITION", path, message: `Track '${id}' requires pose.position.` });
    }
    if (kind === "model" && !object.asset && !asObject(object.model).uri && !asObject(object.model).asset) {
      warnings.push({ severity: "warning", code: "SDJ-MODEL-NO-ASSET", path, message: `Model '${id}' has no asset or uri.` });
    }
    if (!isShown(object.show)) {
      warnings.push({ severity: "warning", code: "SDJ-HIDDEN-COVERAGE-OBJECT", path, message: `Object '${id}' is hidden and will compile as metadata/placeholder.` });
    }
  }

  for (const object of objects) {
    validateObjectReferences(object, ids, errors, warnings);
  }

  for (const analysis of asArray(scene.analysis).map(asObject)) {
    const id = String(analysis.id || "analysis/?");
    const kind = String(analysis.kind || analysis.analysisType || "");
    if (["accessIntervals", "lineOfSightSamples", "rfLinkBudget", "communicationLink"].includes(kind)) {
      if (asArray(analysis.participants).length < 2) {
        errors.push({ severity: "error", code: "SDJ-ANALYSIS-PARTICIPANTS", path: `analysis/${id}`, message: `Analysis '${id}' requires at least two participants.` });
      }
    }
  }

  return { errors, warnings };
}

export function validateObjectReferences(object: JsonObject, ids: Set<string>, errors: Diagnostic[], warnings: Diagnostic[]): void {
  const id = String(object.id || "");
  const encoded = JSON.stringify(object);
  const pattern = /"([A-Za-z0-9_.:-]+)#([^"\\]+)"/g;
  let match = pattern.exec(encoded);
  while (match) {
    const targetId = match[1];
    if (!ids.has(targetId)) {
      errors.push({ severity: "error", code: "SDJ-REFERENCE-MISSING", path: String(object.__path || id), message: `Object '${id}' references missing object '${targetId}'.` });
    }
    match = pattern.exec(encoded);
  }
  if (String(object.kind || "") === "customPrimitive" && !Array.isArray(asObject(object.geometry).positions)) {
    warnings.push({ severity: "warning", code: "SDJ-CUSTOM-PRIMITIVE-NO-POSITIONS", path: String(object.__path || id), message: `customPrimitive '${id}' has no explicit positions; a renderer plugin may be required.` });
  }
}
