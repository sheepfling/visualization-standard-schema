import { asArray, asObject, asString, cloneJson } from "./json.js";

/**
 * @typedef {Record<string, unknown>} JsonObject
 * @typedef {{severity: string, code: string, path: string, message: string}} Diagnostic
 */

/**
 * Ensures the scene has default backend capabilities and standard defaults.
 *
 * @param {JsonObject} scene
 * @param {JsonObject | undefined} defaultCapabilities
 * @returns {JsonObject}
 */
export function normalizeSceneForWorkbench(scene, defaultCapabilities) {
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

/**
 * Flattens top-level objects and nested overlays.
 *
 * @param {JsonObject[]} objects
 * @param {string} prefix
 * @returns {JsonObject[]}
 */
export function flattenObjects(objects, prefix = "objects") {
  /** @type {JsonObject[]} */
  const result = [];
  objects.forEach((object, index) => {
    const cloned = { ...object, __path: `${prefix}/${index}` };
    result.push(cloned);
    const overlays = asArray(object.overlays).map(asObject);
    if (overlays.length > 0) {
      result.push(...flattenObjects(overlays, `${prefix}/${index}/overlays`));
    }
  });
  return result;
}

/**
 * @param {unknown} value
 * @returns {boolean}
 */
export function isShown(value) {
  if (value === false) {
    return false;
  }
  const object = asObject(value);
  if (object.constant === false) {
    return false;
  }
  return true;
}

/**
 * @param {JsonObject} scene
 * @param {string} id
 * @returns {JsonObject | undefined}
 */
export function findObject(scene, id) {
  return flattenObjects(asArray(scene.objects).map(asObject)).find((object) => object.id === id);
}

/**
 * Performs semantic checks that are useful before rendering or exporting.
 *
 * @param {JsonObject} scene
 * @returns {{errors: Diagnostic[], warnings: Diagnostic[]}}
 */
export function validateSemantics(scene) {
  /** @type {Diagnostic[]} */
  const errors = [];
  /** @type {Diagnostic[]} */
  const warnings = [];
  const objects = flattenObjects(asArray(scene.objects).map(asObject));
  const ids = new Set();

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

/**
 * @param {JsonObject} object
 * @param {Set<string>} ids
 * @param {Diagnostic[]} errors
 * @param {Diagnostic[]} warnings
 * @returns {void}
 */
export function validateObjectReferences(object, ids, errors, warnings) {
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
