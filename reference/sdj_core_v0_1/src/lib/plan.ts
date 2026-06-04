import { asArray, asObject, asString, type JsonObject } from "./json.ts";
import type { Diagnostic } from "./scene.ts";
import { CESIUM_KIND_TARGETS } from "./cesium_kind_targets.ts";
import { findObject, flattenObjects, isShown, validateSemantics } from "./scene.ts";


const TARGETS = ["cesium", "simdis", "soap"];

export function buildCompilePlan(scene: JsonObject): JsonObject {
  const objectPlans = buildObjectPlans(scene);
  const semantic = validateSemantics(scene);
  const targetTotals: JsonObject = {};

  for (const objectPlan of objectPlans) {
    for (const targetPlan of asArray((objectPlan as JsonObject).targets).map(asObject)) {
      const target = String(targetPlan.target || "");
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
      const object = findObject(scene, String((objectPlan as JsonObject).id || ""));
      if (object && !isShown(object.show)) {
        totals.hidden = Number(totals.hidden || 0) + 1;
      }
    }
  }

  const kindCounts: JsonObject = {};
  for (const objectPlan of objectPlans) {
    const kind = String((objectPlan as JsonObject).kind || "");
    kindCounts[kind] = Number(kindCounts[kind] || 0) + 1;
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

export function buildAnalysisPlans(scene: JsonObject): JsonObject[] {
  const capabilities = asObject(scene.backendCapabilities);
  return asArray(scene.analysis).map(asObject).map((analysis) => {
    const kind = String(analysis.kind || analysis.analysisType || "analysisResult");
    return {
      id: analysis.id,
      kind,
      analysisType: analysis.analysisType || kind,
      targets: TARGETS.map((target) => {
        const support = asObject(asObject(asObject((capabilities as JsonObject)[target]).analysisSupport)[kind]);
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

export function buildPresentationPlans(scene: JsonObject): JsonObject[] {
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

export function buildObjectPlans(scene: JsonObject): JsonObject[] {
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
        const targetCapabilities = asObject((capabilities as JsonObject)[target]);
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

export function fallbackSupport(target: string, kind: string): string {
  if (target === "cesium") {
    const targetSpec = CESIUM_KIND_TARGETS[kind];
    if (targetSpec) {
      return targetSpec.status;
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

export function artifactForKind(target: string, kind: string): string {
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
    if (["clippingPlane", "clippingPolygon", "classificationVolume", "postProcessStage", "customShader"].includes(kind)) {
      return "viewer.scene/opaque-attachment";
    }
    if (["czmlDataSource", "dataSource", "geoJsonDataSource", "kmlDataSource"].includes(kind)) {
      return "viewer.dataSources/DataSource";
    }
    if (["skyBox", "atmosphere"].includes(kind)) {
      return "viewer.scene/environment";
    }
    if (kind === "videoPlane") {
      return "viewer.entities/PlaneGraphics";
    }
    if (kind === "composite") {
      return "scene.runtime/Composite";
    }
    if (["terrainSurface", "customMesh", "voxel"].includes(kind)) {
      return "scene.runtime/opaque";
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

export function artifactPathForKind(target: string, kind: string, id: string): string {
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

export function buildTargetDiagnostics(compilePlan: JsonObject, target: string): Diagnostic[] {
  const diagnostics: Diagnostic[] = [];
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

export function buildObjectDiagnostics(compilePlan: JsonObject, objectId: string): Diagnostic[] {
  const diagnostics: Diagnostic[] = [];
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

export function inspectObject(scene: JsonObject, objectId: string): JsonObject | undefined {
  const compilePlan = buildCompilePlan(scene);
  const object = flattenObjects(asArray(scene.objects).map(asObject)).find((candidate) => String(candidate.id || "") === objectId);
  if (!object) {
    return undefined;
  }
  const plan = asObject(asArray(compilePlan.objects).map(asObject).find((candidate) => String(candidate.id || "") === objectId));
  return {
    id: objectId,
    kind: String(object.kind || "unknown"),
    name: String(object.name || ""),
    path: String(object.__path || "objects/?"),
    visible: isShown(object.show),
    object,
    plan,
    targets: asArray(plan.targets).map(asObject),
    semanticDiagnostics: [
      ...asArray(asObject(compilePlan.semantic).errors),
      ...asArray(asObject(compilePlan.semantic).warnings)
    ],
    rendererHints: asObject(object.rendererHints)
  };
}

export function inspectObjectMapping(scene: JsonObject, objectId: string): JsonObject {
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

export function artifactPathsForInspection(target: string, artifact: string): string[] {
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

export function actionForSupport(target: string, kind: string, support: string, shown: boolean): string {
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

export function encodeArtifactId(id: string): string {
  return encodeURIComponent(id).replace(/%2F/gi, "/");
}
