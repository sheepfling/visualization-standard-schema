/**
 * Browser-side SDJ compiler helpers for Cesium, SIMDIS, and SOAP export bundles.
 *
 * @typedef {Record<string, unknown>} JsonObject
 * @typedef {{severity: string, code: string, path: string, message: string}} Diagnostic
 * @typedef {{target: string, support: string, targetNative: string, lossiness: string, artifact: string, artifactPath: string, action: string}} TargetPlan
 * @typedef {{id: string, kind: string, name?: string, layer?: string, path: string, shown: boolean, targets: TargetPlan[]}} ObjectPlan
 * @typedef {{files: Record<string, string>, manifest: JsonObject, compilePlan: JsonObject, diagnostics: Diagnostic[]}} BackendBundle
 */

const TARGETS = ["cesium", "simdis", "soap"];
const TEXT_ENCODER = new TextEncoder();

/** @type {number[] | undefined} */
let crcTable;

/**
 * Converts an unknown value into a JSON object or an empty object.
 *
 * @param {unknown} value
 * @returns {JsonObject}
 */
export function asObject(value) {
  if (value && typeof value === "object" && !Array.isArray(value)) {
    return /** @type {JsonObject} */ (value);
  }
  return {};
}

/**
 * Converts an unknown value into an array or an empty array.
 *
 * @param {unknown} value
 * @returns {unknown[]}
 */
export function asArray(value) {
  if (Array.isArray(value)) {
    return value;
  }
  return [];
}

/**
 * Converts an unknown value into a finite number when possible.
 *
 * @param {unknown} value
 * @returns {number | undefined}
 */
export function asNumber(value) {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  return undefined;
}

/**
 * Converts an unknown value into a string when possible.
 *
 * @param {unknown} value
 * @returns {string | undefined}
 */
export function asString(value) {
  if (typeof value === "string") {
    return value;
  }
  return undefined;
}

/**
 * Makes a browser-safe deep clone of a JSON-compatible value.
 *
 * @template T
 * @param {T} value
 * @returns {T}
 */
export function cloneJson(value) {
  return /** @type {T} */ (JSON.parse(JSON.stringify(value)));
}

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
 * Builds the multi-backend compile plan used by the UI and exporters.
 *
 * @param {JsonObject} scene
 * @returns {JsonObject}
 */
export function buildCompilePlan(scene) {
  const objectPlans = buildObjectPlans(scene);
  const semantic = validateSemantics(scene);
  /** @type {JsonObject} */
  const targetTotals = {};

  for (const objectPlan of objectPlans) {
    for (const targetPlan of objectPlan.targets) {
      const target = targetPlan.target;
      if (!targetTotals[target]) {
        targetTotals[target] = {
          strong: 0,
          partial: 0,
          weak: 0,
          reserved: 0,
          unsupported: 0,
          unknown: 0,
          hidden: 0
        };
      }
      const totals = asObject(targetTotals[target]);
      const support = String(targetPlan.support || "unknown");
      if (typeof totals[support] === "number") {
        totals[support] = Number(totals[support]) + 1;
      } else {
        totals.unknown = Number(totals.unknown || 0) + 1;
      }
      const object = findObject(scene, objectPlan.id);
      if (object && !isShown(object.show)) {
        totals.hidden = Number(totals.hidden || 0) + 1;
      }
    }
  }

  /** @type {JsonObject} */
  const kindCounts = {};
  for (const objectPlan of objectPlans) {
    kindCounts[objectPlan.kind] = Number(kindCounts[objectPlan.kind] || 0) + 1;
  }

  return {
    schemaVersion: scene.schemaVersion,
    document: asObject(scene.document),
    generatedAt: new Date().toISOString(),
    objectCount: objectPlans.length,
    analysisCount: asArray(scene.analysis).length,
    presentationCount: asArray(scene.presentation).length,
    kindCounts,
    targetTotals,
    semantic,
    objects: objectPlans,
    analysis: buildAnalysisPlans(scene),
    presentation: buildPresentationPlans(scene)
  };
}

/**
 * Compatibility wrapper for callers that use the earlier inspector function name.
 *
 * @param {JsonObject} scene
 * @param {string} objectId
 * @returns {JsonObject}
 */
export function inspectObjectMapping(scene, objectId) {
  const inspection = inspectObject(scene, objectId);
  const diagnostics = inspection
    ? [...asArray(inspection.semanticDiagnostics), ...asArray(inspection.targets).map(asObject).flatMap((target) => asArray(target.diagnostics))]
    : [];
  return {
    id: objectId,
    found: Boolean(inspection),
    object: inspection ? inspection.object : null,
    objectPlan: inspection ? inspection.plan : {},
    targetDetails: inspection ? inspection.targets : [],
    diagnostics,
    generatedAt: new Date().toISOString()
  };
}

/**
 * Builds a focused inspection record for one object and all configured targets.
 *
 * @param {JsonObject} scene
 * @param {string} objectId
 * @param {JsonObject | undefined} compilePlan
 * @returns {JsonObject | undefined}
 */
export function inspectObject(scene, objectId, compilePlan = undefined) {
  const plan = compilePlan || buildCompilePlan(scene);
  const objects = flattenObjects(asArray(scene.objects).map(asObject));
  const object = objects.find((candidate) => String(candidate.id || "") === objectId);
  if (!object) {
    return undefined;
  }

  const objectPlan = asObject(asArray(plan.objects).map(asObject).find((candidate) => String(candidate.id || "") === objectId));
  const semantic = asObject(plan.semantic);
  const semanticDiagnostics = [...asArray(semantic.errors), ...asArray(semantic.warnings)]
    .map(asObject)
    .filter((diagnostic) => diagnosticMatchesObject(diagnostic, object, objectPlan));
  const targets = asArray(objectPlan.targets).map(asObject).map((targetPlan) => {
    const target = String(targetPlan.target || "unknown");
    const targetDiagnostics = buildTargetDiagnostics(plan, target)
      .filter((diagnostic) => diagnosticMatchesObject(diagnostic, object, objectPlan));
    return {
      target,
      support: String(targetPlan.support || "unknown"),
      targetNative: String(targetPlan.targetNative || ""),
      lossiness: String(targetPlan.lossiness || "unknown"),
      artifact: String(targetPlan.artifact || "diagnostics"),
      artifactPath: String(targetPlan.artifactPath || artifactPathForKind(target, String(object.kind || "unknown"), objectId)),
      artifactPaths: artifactPathsForInspection(target, String(targetPlan.artifact || "")),
      action: String(targetPlan.action || actionForSupport(target, String(object.kind || "unknown"), String(targetPlan.support || "unknown"), isShown(object.show))),
      diagnostics: targetDiagnostics
    };
  });

  const cleanObject = cloneJson(object);
  delete cleanObject.__path;
  return {
    id: objectId,
    kind: String(object.kind || "unknown"),
    name: String(object.name || ""),
    path: String(objectPlan.path || object.__path || "objects/?"),
    visible: isShown(object.show),
    object: cleanObject,
    plan: objectPlan,
    targets,
    semanticDiagnostics,
    rendererHints: asObject(object.rendererHints)
  };
}

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
 * Creates a no-compression ZIP Blob from text files.
 *
 * @param {Record<string, string>} files
 * @returns {Blob}
 */
export function createZipBlob(files) {
  const entries = Object.entries(files).map(([rawName, content]) => {
    const name = rawName.replace(/\\/g, "/").replace(/^\/+/, "");
    const nameBytes = TEXT_ENCODER.encode(name);
    const data = TEXT_ENCODER.encode(content);
    return {
      name,
      nameBytes,
      data,
      crc: crc32(data),
      localOffset: 0
    };
  });

  /** @type {(Uint8Array | BlobPart)[]} */
  const localParts = [];
  /** @type {Uint8Array[]} */
  const centralParts = [];
  let offset = 0;
  const now = new Date();
  const dosTime = toDosTime(now);
  const dosDate = toDosDate(now);

  for (const entry of entries) {
    entry.localOffset = offset;
    const header = new Uint8Array(30 + entry.nameBytes.length);
    const view = new DataView(header.buffer);
    view.setUint32(0, 0x04034b50, true);
    view.setUint16(4, 20, true);
    view.setUint16(6, 0x0800, true);
    view.setUint16(8, 0, true);
    view.setUint16(10, dosTime, true);
    view.setUint16(12, dosDate, true);
    view.setUint32(14, entry.crc, true);
    view.setUint32(18, entry.data.length, true);
    view.setUint32(22, entry.data.length, true);
    view.setUint16(26, entry.nameBytes.length, true);
    view.setUint16(28, 0, true);
    header.set(entry.nameBytes, 30);
    localParts.push(header, entry.data);
    offset += header.length + entry.data.length;
  }

  const centralStart = offset;
  for (const entry of entries) {
    const central = new Uint8Array(46 + entry.nameBytes.length);
    const view = new DataView(central.buffer);
    view.setUint32(0, 0x02014b50, true);
    view.setUint16(4, 20, true);
    view.setUint16(6, 20, true);
    view.setUint16(8, 0x0800, true);
    view.setUint16(10, 0, true);
    view.setUint16(12, dosTime, true);
    view.setUint16(14, dosDate, true);
    view.setUint32(16, entry.crc, true);
    view.setUint32(20, entry.data.length, true);
    view.setUint32(24, entry.data.length, true);
    view.setUint16(28, entry.nameBytes.length, true);
    view.setUint16(30, 0, true);
    view.setUint16(32, 0, true);
    view.setUint16(34, 0, true);
    view.setUint16(36, 0, true);
    view.setUint32(38, 0, true);
    view.setUint32(42, entry.localOffset, true);
    central.set(entry.nameBytes, 46);
    centralParts.push(central);
    offset += central.length;
  }

  const centralSize = offset - centralStart;
  const end = new Uint8Array(22);
  const endView = new DataView(end.buffer);
  endView.setUint32(0, 0x06054b50, true);
  endView.setUint16(4, 0, true);
  endView.setUint16(6, 0, true);
  endView.setUint16(8, entries.length, true);
  endView.setUint16(10, entries.length, true);
  endView.setUint32(12, centralSize, true);
  endView.setUint32(16, centralStart, true);
  endView.setUint16(20, 0, true);

  return new Blob([...localParts, ...centralParts, end], { type: "application/zip" });
}

/**
 * Converts a value to formatted JSON text.
 *
 * @param {unknown} value
 * @returns {string}
 */
export function toJson(value) {
  return `${JSON.stringify(value, null, 2)}\n`;
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
 * @param {JsonObject} scene
 * @returns {ObjectPlan[]}
 */
function buildObjectPlans(scene) {
  const capabilities = asObject(scene.backendCapabilities);
  const targets = Object.keys(capabilities).filter((target) => TARGETS.includes(target));
  const resolvedTargets = targets.length > 0 ? targets : TARGETS;
  const objects = flattenObjects(asArray(scene.objects).map(asObject));
  return objects.map((object, index) => {
    const id = String(object.id || `object-${index + 1}`);
    const kind = String(object.kind || "unknown");
    const path = String(object.__path || `objects/${index}`);
    const shown = isShown(object.show);
    return {
      id,
      kind,
      name: asString(object.name),
      layer: asString(object.layer),
      path,
      shown,
      targets: resolvedTargets.map((target) => {
        const targetCapabilities = asObject(capabilities[target]);
        const objectSupport = asObject(targetCapabilities.objectSupport);
        const support = asObject(objectSupport[kind]);
        const supportValue = String(support.support || fallbackSupport(target, kind));
        const artifact = artifactForKind(target, kind);
        return {
          target,
          support: supportValue,
          targetNative: String(support.target || artifact),
          lossiness: String(support.lossiness || "unknown"),
          artifact,
          artifactPath: artifactPathForKind(target, kind, id),
          action: actionForSupport(target, kind, supportValue, shown)
        };
      })
    };
  });
}

/**
 * @param {string} target
 * @param {string} kind
 * @returns {string}
 */
function fallbackSupport(target, kind) {
  if (target === "cesium") {
    if (["point", "label", "billboard", "track", "model", "polyline", "polygon", "rectangle", "ellipse", "circle", "box", "cylinder", "cone", "ellipsoid", "sphere", "wall", "corridor", "polylineVolume", "plane"].includes(kind)) {
      return "strong";
    }
    if (["sectorVolume", "keyhole", "hemisphere", "sphericalCap", "frustum", "customPrimitive"].includes(kind)) {
      return "partial";
    }
  }
  if (target === "simdis") {
    if (["track", "point", "label", "polyline", "polygon", "circle", "ellipse", "rectangle", "sector2d", "rangeRing"].includes(kind)) {
      return "strong";
    }
    return "partial";
  }
  if (target === "soap") {
    if (["track", "model", "lineOfSight", "sectorVolume", "conicSensor"].includes(kind)) {
      return "strong";
    }
    return "partial";
  }
  return "unknown";
}

/**
 * @param {string} target
 * @param {string} kind
 * @returns {string}
 */
function artifactForKind(target, kind) {
  if (target === "cesium") {
    if (kind === "tileset") {
      return "scene.primitives/Cesium3DTileset";
    }
    if (["sectorVolume", "keyhole", "hemisphere", "sphericalCap", "frustum", "customPrimitive", "primitiveMesh", "customMesh"].includes(kind)) {
      return "scene.primitives/Primitive";
    }
    if (kind === "particleSystem") {
      return "scene.primitives/ParticleSystem";
    }
    return "viewer.entities/Entity";
  }

  if (target === "simdis") {
    if (["polyline", "polygon", "circle", "ellipse", "rectangle", "sector2d", "rangeRing", "bearingFan", "wall", "corridor"].includes(kind)) {
      return "overlays.gog";
    }
    if (["track", "model", "point", "billboard", "label"].includes(kind)) {
      return "entities.json";
    }
    if (["conicSensor", "rectangularSensor", "customPatternSensor", "sectorVolume", "keyhole", "frustum", "fan"].includes(kind)) {
      return "entities.json/sensors";
    }
    return "manifest.json/extensions";
  }

  if (target === "soap") {
    if (["track", "model"].includes(kind)) {
      return "scenario.json/platforms";
    }
    if (["conicSensor", "rectangularSensor", "customPatternSensor", "sectorVolume", "keyhole", "frustum", "fan"].includes(kind)) {
      return "scenario.json/sensorSwaths";
    }
    if (["polyline", "polygon", "circle", "ellipse", "rectangle", "rangeRing", "lineOfSight"].includes(kind)) {
      return "scenario.json/overlays";
    }
    return "scenario.json/extensions";
  }

  return "diagnostics";
}

/**
 * @param {JsonObject} diagnostic
 * @param {JsonObject} object
 * @param {JsonObject} objectPlan
 * @returns {boolean}
 */
function diagnosticMatchesObject(diagnostic, object, objectPlan) {
  const id = String(object.id || "");
  const path = String(objectPlan.path || object.__path || "");
  const diagnosticPath = String(diagnostic.path || "");
  const message = String(diagnostic.message || "");
  return Boolean(id) && (diagnosticPath === path || diagnosticPath.includes(id) || message.includes(`'${id}'`) || message.includes(id));
}

/**
 * @param {string} target
 * @param {string} artifact
 * @returns {string[]}
 */
function artifactPathsForInspection(target, artifact) {
  if (target === "cesium") {
    if (artifact.includes("Cesium3DTileset") || artifact.includes("Primitive") || artifact.includes("Entity") || artifact.includes("ParticleSystem")) {
      return ["cesium/scene.sdj.json", "cesium/compile-plan.json"];
    }
    return ["cesium/diagnostics.json"];
  }
  if (target === "simdis") {
    if (artifact.includes("overlays.gog")) {
      return ["simdis/overlays.gog"];
    }
    if (artifact.includes("entities.json")) {
      return ["simdis/entities.json"];
    }
    if (artifact.includes("presentation")) {
      return ["simdis/presentation.json"];
    }
    return ["simdis/manifest.json", "simdis/diagnostics.json"];
  }
  if (target === "soap") {
    if (artifact.includes("scenario.json")) {
      return ["soap/scenario.json"];
    }
    if (artifact.includes("views.json")) {
      return ["soap/views.json"];
    }
    if (artifact.includes("presentation")) {
      return ["soap/presentation.json"];
    }
    return ["soap/manifest.json", "soap/diagnostics.json"];
  }
  return ["diagnostics.json"];
}

/**
 * Resolves the object-specific path inside a generated backend bundle.
 *
 * @param {string} target
 * @param {string} kind
 * @param {string} id
 * @returns {string}
 */
function artifactPathForKind(target, kind, id) {
  const encodedId = encodeArtifactId(id);
  if (target === "cesium") {
    return `cesium/scene.sdj.json#objects/${encodedId}`;
  }

  if (target === "simdis") {
    if (["polyline", "polygon", "circle", "ellipse", "rectangle", "sector2d", "rangeRing", "bearingFan", "wall", "corridor"].includes(kind)) {
      return `simdis/overlays.gog#${encodedId}`;
    }
    if (["track", "model"].includes(kind)) {
      return `simdis/entities.json#platforms/${encodedId}`;
    }
    if (["point", "billboard", "label"].includes(kind)) {
      return `simdis/entities.json#annotations/${encodedId}`;
    }
    if (["vector", "velocityVector", "accelerationVector", "bodyAxes", "principalAxes", "lineOfSight", "relativeLine", "interceptLine"].includes(kind)) {
      return `simdis/entities.json#vectors/${encodedId}`;
    }
    if (["conicSensor", "rectangularSensor", "customPatternSensor", "sectorVolume", "keyhole", "frustum", "hemisphere", "sphericalCap", "fan"].includes(kind)) {
      return `simdis/entities.json#sensors/${encodedId}`;
    }
    return `simdis/manifest.json#extensions/${encodedId}`;
  }

  if (target === "soap") {
    if (["track"].includes(kind)) {
      return `soap/scenario.json#platforms/${encodedId}`;
    }
    if (["model"].includes(kind)) {
      return `soap/scenario.json#models/${encodedId}`;
    }
    if (["conicSensor", "rectangularSensor", "customPatternSensor", "sectorVolume", "keyhole", "frustum", "hemisphere", "sphericalCap", "fan"].includes(kind)) {
      return `soap/scenario.json#sensorSwaths/${encodedId}`;
    }
    if (["polyline", "polygon", "circle", "ellipse", "rectangle", "rangeRing", "lineOfSight", "relativeLine", "interceptLine"].includes(kind)) {
      return `soap/scenario.json#overlays/${encodedId}`;
    }
    return `soap/scenario.json#extensions/${encodedId}`;
  }

  return `diagnostics#${encodedId}`;
}

/**
 * Produces a short human-readable action for the inspector.
 *
 * @param {string} target
 * @param {string} kind
 * @param {string} support
 * @param {boolean} shown
 * @returns {string}
 */
function actionForSupport(target, kind, support, shown) {
  if (!shown) {
    return "Object is hidden in the source scene; export keeps it as metadata or disabled output where possible.";
  }
  if (support === "strong") {
    return `${target} can represent ${kind} directly or with low-loss native constructs.`;
  }
  if (support === "partial" || support === "weak") {
    return `${target} receives an approximate or normalized ${kind} representation; inspect diagnostics for lossiness.`;
  }
  if (support === "reserved") {
    return `${kind} is reserved for ${target}; the object is retained for future adapter support.`;
  }
  if (support === "unsupported") {
    return `${target} cannot currently emit ${kind}; the compiler records diagnostics instead of dropping the object silently.`;
  }
  return `${target} has no explicit capability entry for ${kind}; fallback planning is used.`;
}

/**
 * Encodes an object id for artifact-fragment display.
 *
 * @param {string} id
 * @returns {string}
 */
function encodeArtifactId(id) {
  return encodeURIComponent(id).replace(/%2F/gi, "/");
}

/**
 * @param {JsonObject} scene
 * @returns {JsonObject[]}
 */
function buildAnalysisPlans(scene) {
  const capabilities = asObject(scene.backendCapabilities);
  return asArray(scene.analysis).map(asObject).map((analysis) => {
    const kind = String(analysis.kind || analysis.analysisType || "analysisResult");
    return {
      id: analysis.id,
      kind,
      analysisType: analysis.analysisType || kind,
      targets: TARGETS.map((target) => {
        const support = asObject(asObject(asObject(capabilities[target]).analysisSupport)[kind]);
        return {
          target,
          support: String(support.support || "partial"),
          targetNative: String(support.target || `${target}/analysis`),
          lossiness: String(support.lossiness || "unknown")
        };
      })
    };
  });
}

/**
 * @param {JsonObject} scene
 * @returns {JsonObject[]}
 */
function buildPresentationPlans(scene) {
  return asArray(scene.presentation).map(asObject).map((item) => ({
    id: item.id,
    kind: item.kind,
    title: item.title || item.name,
    targets: [
      { target: "cesium", support: "partial", targetNative: "camera/viewer controls or external UI" },
      { target: "simdis", support: "strong", targetNative: "view / presentation / popup / banner" },
      { target: "soap", support: "strong", targetNative: "Presentation -> Slide -> Palette -> Viewport -> View" }
    ]
  }));
}

/**
 * @param {JsonObject} scene
 * @param {string} id
 * @returns {JsonObject | undefined}
 */
function findObject(scene, id) {
  return flattenObjects(asArray(scene.objects).map(asObject)).find((object) => object.id === id);
}

/**
 * @param {unknown} value
 * @returns {boolean}
 */
function isShown(value) {
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
 * @param {JsonObject} object
 * @param {Set<string>} ids
 * @param {Diagnostic[]} errors
 * @param {Diagnostic[]} warnings
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
      errors.push({ severity: "error", code: "SDJ-REFERENCE-MISSING", path: String(object.__path || id), message: `Object '${id}' references missing object '${targetId}'.` });
    }
    match = pattern.exec(encoded);
  }
  if (String(object.kind || "") === "customPrimitive" && !Array.isArray(asObject(object.geometry).positions)) {
    warnings.push({ severity: "warning", code: "SDJ-CUSTOM-PRIMITIVE-NO-POSITIONS", path: String(object.__path || id), message: `customPrimitive '${id}' has no explicit positions; a renderer plugin may be required.` });
  }
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

/**
 * @param {string[]} lines
 * @param {JsonObject} object
 * @param {unknown[]} positions
 * @returns {void}
 */
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

/**
 * @param {string[]} lines
 * @param {JsonObject} object
 * @param {unknown[]} positions
 * @returns {void}
 */
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

/**
 * @param {string[]} lines
 * @param {JsonObject} object
 * @param {JsonObject} geometry
 * @returns {void}
 */
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

/**
 * @param {string[]} lines
 * @param {JsonObject} object
 * @param {JsonObject} geometry
 * @returns {void}
 */
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

/**
 * @param {string[]} lines
 * @param {JsonObject} object
 * @param {JsonObject} geometry
 * @returns {void}
 */
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

/**
 * @param {string[]} lines
 * @param {JsonObject} object
 * @param {JsonObject} geometry
 * @returns {void}
 */
function emitGogSectorComment(lines, object, geometry) {
  const lla = objectCenterLla(object);
  lines.push(`# begin sector ${object.id}`);
  lines.push(`# center ${lla ? `${lla.lat} ${lla.lon} ${lla.alt}` : "reference-or-derived"}`);
  lines.push(`# radius ${geometry.outerRadiusMeters ?? geometry.radiusMeters ?? "unknown"}`);
  lines.push(`# azimuth ${geometry.azimuthStartDegrees ?? "unknown"} ${geometry.azimuthStopDegrees ?? "unknown"}`);
  lines.push(`# end sector ${object.id}`);
}

/**
 * @param {string[]} lines
 * @param {JsonObject} object
 * @param {JsonObject} geometry
 * @returns {void}
 */
function emitGogSensorComment(lines, object, geometry) {
  lines.push(`# sensor-volume ${object.id} kind=${object.kind} geometry=${JSON.stringify(geometry)}`);
}

/**
 * @param {JsonObject} object
 * @returns {{lon: number, lat: number, alt: number} | undefined}
 */
function objectCenterLla(object) {
  return toLonLatAlt(asObject(asObject(object.pose).position));
}

/**
 * @param {JsonObject} position
 * @returns {{lon: number, lat: number, alt: number} | undefined}
 */
function toLonLatAlt(position) {
  const value = asArray(position.cartographicDegrees);
  if (value.length >= 3) {
    return { lon: Number(value[0]), lat: Number(value[1]), alt: Number(value[2]) };
  }
  return undefined;
}

/**
 * @param {JsonObject} object
 * @returns {string | undefined}
 */
function sensorHost(object) {
  const pose = asObject(object.pose);
  const position = asObject(pose.position);
  const reference = asString(position.reference);
  if (reference) {
    return reference.split("#")[0];
  }
  return undefined;
}

/**
 * @param {string} kind
 * @returns {string}
 */
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

/**
 * @param {JsonObject} scene
 * @returns {JsonObject}
 */
function buildSimdisPresentation(scene) {
  const items = asArray(scene.presentation).map(asObject);
  return {
    views: items.filter((item) => ["view", "reportView", "plotView", "dataView"].includes(String(item.kind))).map((item) => ({ id: item.id, kind: item.kind, name: item.name || item.title, target: item.target })),
    slides: items.filter((item) => item.kind === "slide").map((item) => ({ id: item.id, title: item.title, startTime: item.startTime, stopTime: item.stopTime, views: item.views || [] })),
    cameraActions: items.filter((item) => item.kind === "cameraAction").map((item) => ({ id: item.id, target: item.target, camera: item.camera || {}, durationSeconds: item.durationSeconds })),
    popups: items.filter((item) => ["popup", "banner", "annotation"].includes(String(item.kind))).map((item) => ({ id: item.id, kind: item.kind, title: item.title, target: item.target }))
  };
}

/**
 * @param {JsonObject} object
 * @returns {JsonObject}
 */
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

/**
 * @param {string} platformId
 * @returns {string | undefined}
 */
function modelForPlatform(platformId) {
  if (platformId === "air-track-17") {
    return "air-track-17-model";
  }
  if (platformId === "air-track-42") {
    return "track-42-model";
  }
  return undefined;
}

/**
 * @param {JsonObject} object
 * @returns {JsonObject}
 */
function toSoapTrajectory(object) {
  return {
    id: `${object.id}-trajectory`,
    platformId: object.id,
    source: "sdj.sampledPosition",
    samples: extractTrajectory(object)
  };
}

/**
 * @param {JsonObject} object
 * @returns {JsonObject}
 */
function toSoapModel(object) {
  return {
    id: object.id,
    name: object.name,
    asset: object.asset || asObject(object.model).asset || asObject(object.model).uri,
    pose: asObject(object.pose),
    model: asObject(object.model)
  };
}

/**
 * @param {JsonObject} object
 * @returns {JsonObject}
 */
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

/**
 * @param {string} kind
 * @returns {string}
 */
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

/**
 * @param {JsonObject} object
 * @returns {JsonObject}
 */
function toSoapOverlay(object) {
  return {
    id: object.id,
    kind: object.kind,
    name: object.name,
    geometry: asObject(object.geometry),
    style: asObject(object.style)
  };
}

/**
 * @param {JsonObject} scene
 * @returns {JsonObject}
 */
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

/**
 * @param {string} kind
 * @returns {string}
 */
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

/**
 * @param {JsonObject} scene
 * @returns {JsonObject}
 */
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

/**
 * @param {JsonObject} scene
 * @returns {Record<string, string>}
 */
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

/**
 * @param {JsonObject} object
 * @returns {JsonObject | null}
 */
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

/**
 * @param {JsonObject} object
 * @returns {JsonObject[]}
 */
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

/**
 * @param {JsonObject} compilePlan
 * @param {string} target
 * @returns {Diagnostic[]}
 */
function buildTargetDiagnostics(compilePlan, target) {
  /** @type {Diagnostic[]} */
  const diagnostics = [];
  for (const object of asArray(compilePlan.objects).map(asObject)) {
    const targetPlan = asArray(object.targets).map(asObject).find((candidate) => candidate.target === target);
    if (!targetPlan) {
      continue;
    }
    const support = String(targetPlan.support || "unknown");
    if (["partial", "weak", "reserved", "unsupported", "unknown"].includes(support)) {
      diagnostics.push({
        severity: support === "unsupported" ? "error" : "warning",
        code: `${target.toUpperCase()}-${support.toUpperCase()}-SUPPORT`,
        path: String(object.path || object.id || "objects/?"),
        message: `${target} support for ${object.kind} '${object.id}' is ${support}; target is ${targetPlan.targetNative || "diagnostic"}; artifact path is ${targetPlan.artifactPath || targetPlan.artifact || "diagnostics"}.`
      });
    }
  }
  return diagnostics;
}

/**
 * Builds object-specific diagnostics for the inspector panel.
 *
 * @param {JsonObject} compilePlan
 * @param {string} objectId
 * @returns {Diagnostic[]}
 */
function buildObjectDiagnostics(compilePlan, objectId) {
  /** @type {Diagnostic[]} */
  const diagnostics = [];
  const objectPlan = asArray(compilePlan.objects).map(asObject).find((object) => object.id === objectId);
  if (!objectPlan) {
    return [{
      severity: "error",
      code: "SDJ-INSPECTOR-NOT-FOUND",
      path: `objects/${objectId}`,
      message: `No object plan exists for '${objectId}'.`
    }];
  }

  for (const targetPlan of asArray(objectPlan.targets).map(asObject)) {
    const support = String(targetPlan.support || "unknown");
    if (["partial", "weak", "reserved", "unsupported", "unknown"].includes(support)) {
      diagnostics.push({
        severity: support === "unsupported" ? "error" : "warning",
        code: `${String(targetPlan.target || "TARGET").toUpperCase()}-${support.toUpperCase()}-MAPPING`,
        path: String(targetPlan.artifactPath || objectPlan.path || objectId),
        message: String(targetPlan.action || `${targetPlan.target || "target"} support for '${objectId}' is ${support}.`)
      });
    }
  }
  return diagnostics;
}

/**
 * @returns {string}
 */
function renderCesiumReadme() {
  return [
    "# Cesium bundle",
    "",
    "This bundle contains the normalized SDJ scene and compile plan for the Cesium runtime adapter.",
    "Load `scene.sdj.json` with `SpatialDisplayJson.loadSpatialDisplayScene(viewer, scene, options)`.",
    ""
  ].join("\n");
}

/**
 * @param {Uint8Array} data
 * @returns {number}
 */
function crc32(data) {
  const table = getCrcTable();
  let crc = 0xffffffff;
  for (const byte of data) {
    crc = (crc >>> 8) ^ table[(crc ^ byte) & 0xff];
  }
  return (crc ^ 0xffffffff) >>> 0;
}

/**
 * @returns {number[]}
 */
function getCrcTable() {
  if (crcTable) {
    return crcTable;
  }
  crcTable = [];
  for (let n = 0; n < 256; n += 1) {
    let c = n;
    for (let k = 0; k < 8; k += 1) {
      if ((c & 1) !== 0) {
        c = 0xedb88320 ^ (c >>> 1);
      } else {
        c >>>= 1;
      }
    }
    crcTable[n] = c >>> 0;
  }
  return crcTable;
}

/**
 * @param {Date} date
 * @returns {number}
 */
function toDosTime(date) {
  return (date.getHours() << 11) | (date.getMinutes() << 5) | Math.floor(date.getSeconds() / 2);
}

/**
 * @param {Date} date
 * @returns {number}
 */
function toDosDate(date) {
  const year = Math.max(1980, date.getFullYear());
  return ((year - 1980) << 9) | ((date.getMonth() + 1) << 5) | date.getDate();
}
