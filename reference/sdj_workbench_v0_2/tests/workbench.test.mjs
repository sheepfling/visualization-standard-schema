import { readFileSync } from "node:fs";
import { test } from "node:test";
import assert from "node:assert/strict";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import {
  buildCompilePlan,
  compileAllBackendsToFiles,
  compileBackend,
  normalizeSceneForWorkbench,
} from "../../sdj_core_v0_1/src/index.ts";

const projectDir = dirname(dirname(fileURLToPath(import.meta.url)));

function readJson(relativePath) {
  return JSON.parse(readFileSync(join(projectDir, relativePath), "utf8"));
}

test("normalizeSceneForWorkbench applies standard defaults", () => {
  const normalized = normalizeSceneForWorkbench(
    { document: { id: "demo" } },
    { cesium: { supported: true } }
  );

  assert.equal(normalized.schemaVersion, "sdj-0.4");
  assert.deepEqual(normalized.backendCapabilities, { cesium: { supported: true } });
  assert.deepEqual(normalized.objects, []);
  assert.deepEqual(normalized.analysis, []);
  assert.deepEqual(normalized.presentation, []);
});

test("compileBackend and compileAllBackendsToFiles produce stable Cesium artifacts", () => {
  const scene = normalizeSceneForWorkbench(readJson("examples/sdj_minimal_scene.json"), readJson("data/sdj_backend_capabilities_v0_4.json"));
  const plan = buildCompilePlan(scene);
  const cesium = compileBackend(scene, "cesium");
  const allFiles = compileAllBackendsToFiles(scene);

  assert.equal(plan.document.id, "sdj-minimal-demo");
  assert.equal(plan.objectCount, 5);
  assert.equal(cesium.manifest.target, "cesium");
  assert.ok(Object.keys(cesium.files).some((name) => name.endsWith("manifest.json")));
  assert.ok(allFiles["compile-plan-all-targets.json"]);
  assert.ok(allFiles["cesium/bundle-summary.json"]);
});

test("compileBackend preserves imported runtime families in SIMDIS and SOAP bundles", () => {
  const scene = normalizeSceneForWorkbench(
    {
      document: { id: "runtime-families-demo" },
      objects: [
        { id: "terrain", kind: "terrainSurface" },
        { id: "mesh", kind: "customMesh" },
        { id: "clip", kind: "clippingPlane" },
        { id: "shader", kind: "customShader" },
        { id: "stage", kind: "postProcessStage" },
        { id: "source", kind: "geoJsonDataSource" },
        { id: "sky", kind: "skyBox" },
        { id: "video", kind: "videoPlane" }
      ]
    },
    readJson("data/sdj_backend_capabilities_v0_4.json")
  );

  const simdis = compileBackend(scene, "simdis");
  const soap = compileBackend(scene, "soap");
  const simdisRuntime = JSON.parse(simdis.files["simdis/runtime-objects.json"]);
  const soapRuntime = JSON.parse(soap.files["soap/runtime-objects.json"]);

  assert.deepEqual(
    simdisRuntime.runtimeObjects.map((object) => object.kind),
    ["terrainSurface", "customMesh", "clippingPlane", "customShader", "postProcessStage", "geoJsonDataSource", "skyBox", "videoPlane"]
  );
  assert.deepEqual(
    soapRuntime.runtimeObjects.map((object) => object.kind),
    ["terrainSurface", "customMesh", "clippingPlane", "customShader", "postProcessStage", "geoJsonDataSource", "skyBox", "videoPlane"]
  );
});

test("index.html wires the Cesium viewer and workbench app", () => {
  const html = readFileSync(join(projectDir, "index.html"), "utf8");

  assert.ok(html.includes('src="./vendor/sdj_cesium_loader_v0_4.js"'));
  assert.ok(html.includes('type="module" src="./src/app.js"'));
  assert.ok(html.includes('id="cesiumContainer"'));
});
