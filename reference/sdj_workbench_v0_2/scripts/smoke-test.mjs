import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import {
  buildCompilePlan,
  compileAllBackendsToFiles,
  compileBackend,
  inspectObject,
  normalizeSceneForWorkbench,
  validateSemantics
} from "../src/sdj_browser_compiler.js";

/**
 * @param {string} path
 * @returns {Record<string, unknown>}
 */
function readJson(path) {
  return JSON.parse(readFileSync(path, "utf8"));
}

/**
 * @param {string} path
 * @param {unknown} value
 * @returns {void}
 */
function writeJson(path, value) {
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

const projectDir = join(dirname(fileURLToPath(import.meta.url)), "..");
const scenePath = join(projectDir, "examples", "sdj_full_coverage_scene_v0_4.json");
const capabilityPath = join(projectDir, "data", "sdj_backend_capabilities_v0_4.json");
const scene = normalizeSceneForWorkbench(readJson(scenePath), readJson(capabilityPath));
const semantic = validateSemantics(scene);
const compilePlan = buildCompilePlan(scene);
const cesium = compileBackend(scene, "cesium");
const simdis = compileBackend(scene, "simdis");
const soap = compileBackend(scene, "soap");
const allFiles = compileAllBackendsToFiles(scene);
const firstPlannedObject = String(compilePlan.objects[0]?.id || "");
const firstInspection = firstPlannedObject ? inspectObject(scene, firstPlannedObject, compilePlan) : undefined;
const hiddenKeyholeInspection = inspectObject(scene, "coverage-keyhole-hidden", compilePlan) || inspectObject(scene, "sensor-a-keyhole", compilePlan);
const report = {
  ok: semantic.errors.length === 0,
  semanticErrors: semantic.errors.length,
  semanticWarnings: semantic.warnings.length,
  objectCount: compilePlan.objectCount,
  analysisCount: compilePlan.analysisCount,
  presentationCount: compilePlan.presentationCount,
  targetTotals: compilePlan.targetTotals,
  cesiumFiles: Object.keys(cesium.files).length,
  simdisFiles: Object.keys(simdis.files).length,
  soapFiles: Object.keys(soap.files).length,
  allFiles: Object.keys(allFiles).length,
  inspector: {
    firstObject: firstInspection ? {
      id: firstInspection.id,
      kind: firstInspection.kind,
      targets: firstInspection.targets
    } : null,
    sampleObject: hiddenKeyholeInspection ? {
      id: hiddenKeyholeInspection.id,
      kind: hiddenKeyholeInspection.kind,
      visible: hiddenKeyholeInspection.visible,
      targetCount: hiddenKeyholeInspection.targets.length
    } : null
  },
  sampleFiles: Object.keys(allFiles).slice(0, 20)
};
writeJson(join(projectDir, "generated-smoke", "smoke-report.json"), report);
console.log(JSON.stringify(report, null, 2));
