import { test } from "node:test";
import assert from "node:assert/strict";
import {
  compileSpatialDisplaySceneToCesiumPlan,
  getCesiumKindTargets,
  loadSpatialDisplayScene,
  resolveCesiumSpatialDisplayLoader,
  validateSpatialDisplaySceneSemantics
} from "../../sdj_core_v0_1/src/index.ts";
import "../vendor/sdj_cesium_loader_v0_4.js";

test("resolveCesiumSpatialDisplayLoader prefers explicit loaders", () => {
  const loader = { loadSpatialDisplayScene() {}, compileSpatialDisplaySceneToCesiumPlan() {}, validateSpatialDisplaySceneSemantics() {}, getCesiumKindTargets() {} };
  assert.equal(resolveCesiumSpatialDisplayLoader(loader), loader);
});

test("adapter helpers delegate to the injected loader", async () => {
  const scene = { id: "scene" };
  const calls = [];
  const loader = {
    loadSpatialDisplayScene(viewer, loadedScene, options) {
      calls.push(["load", viewer, loadedScene, options]);
      return Promise.resolve({ warnings: ["warn"] });
    },
    compileSpatialDisplaySceneToCesiumPlan(loadedScene) {
      calls.push(["plan", loadedScene]);
      return { plan: loadedScene };
    },
    validateSpatialDisplaySceneSemantics(loadedScene) {
      calls.push(["validate", loadedScene]);
      return { errors: ["error"], warnings: ["warn"] };
    },
    getCesiumKindTargets() {
      calls.push(["targets"]);
      return { point: { backend: "entity", target: "PointGraphics", status: "implemented" } };
    }
  };

  assert.deepEqual(getCesiumKindTargets(loader), {
    point: { backend: "entity", target: "PointGraphics", status: "implemented" }
  });
  assert.deepEqual(compileSpatialDisplaySceneToCesiumPlan(scene, loader), { plan: scene });
  assert.deepEqual(validateSpatialDisplaySceneSemantics(scene, loader), { errors: ["error"], warnings: ["warn"] });
  await assert.doesNotReject(() => loadSpatialDisplayScene("viewer", scene, { zoomToFirstView: true }, loader));

  assert.deepEqual(calls, [
    ["targets"],
    ["plan", scene],
    ["validate", scene],
    ["load", "viewer", scene, { zoomToFirstView: true }]
  ]);
});

test("cesium compile plan classifies imported runtime families as total support", () => {
  const scene = {
    objects: [
      { id: "terrain", kind: "terrainSurface" },
      { id: "mesh", kind: "customMesh" },
      { id: "clip-plane", kind: "clippingPlane" },
      { id: "shader", kind: "customShader" },
      { id: "stage", kind: "postProcessStage" },
      { id: "geojson", kind: "geoJsonDataSource" },
      { id: "sky", kind: "skyBox" },
      { id: "video", kind: "videoPlane" }
    ]
  };
  const plan = compileSpatialDisplaySceneToCesiumPlan(scene);
  const byKind = new Map(plan.items.map((item) => [item.kind, item]));

  for (const kind of ["terrainSurface", "customMesh", "clippingPlane", "customShader", "postProcessStage", "geoJsonDataSource", "skyBox", "videoPlane"]) {
    assert.ok(byKind.has(kind), `missing ${kind} from compile plan`);
    assert.equal(byKind.get(kind).status, "implemented", `${kind} should compile as implemented`);
  }
});

test("cesium loader preserves imported runtime families as opaque scene objects", async () => {
  const viewer = {
    clock: {},
    timeline: { zoomTo() {} },
    entities: {
      items: [],
      add(entity) {
        this.items.push(entity);
        return entity;
      }
    },
    scene: { primitives: { add(value) { return value; } } },
    imageryLayers: { addImageryProvider() { return {}; } }
  };
  const originalCesium = globalThis.Cesium;
  globalThis.Cesium = {};
  try {
    const result = await loadSpatialDisplayScene(viewer, {
      objects: [
        { id: "terrain", kind: "terrainSurface", name: "Terrain surface" },
        { id: "shader", kind: "customShader", name: "Custom shader" },
        { id: "geojson", kind: "geoJsonDataSource", name: "GeoJSON source" }
      ]
    }, { zoomToFirstView: false });

    assert.equal(result.warnings.length, 0);
    assert.equal(result.entities.size, 3);
    assert.equal(viewer.entities.items.length, 3);
    assert.equal(viewer.entities.items[0].properties.importedKind, "terrainSurface");
    assert.equal(viewer.entities.items[1].properties.importedKind, "customShader");
    assert.equal(viewer.entities.items[2].properties.importedKind, "geoJsonDataSource");
  } finally {
    globalThis.Cesium = originalCesium;
  }
});

test("resolveCesiumSpatialDisplayLoader falls back to globalThis", () => {
  const original = globalThis.SpatialDisplayJson;
  const loader = { loadSpatialDisplayScene() {}, compileSpatialDisplaySceneToCesiumPlan() {}, validateSpatialDisplaySceneSemantics() {}, getCesiumKindTargets() {} };
  globalThis.SpatialDisplayJson = loader;
  try {
    assert.equal(resolveCesiumSpatialDisplayLoader(), loader);
  } finally {
    globalThis.SpatialDisplayJson = original;
  }
});
