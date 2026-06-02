import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";
import assert from "node:assert/strict";
import { CESIUM_KIND_TARGETS, compileSpatialDisplaySceneToCesiumPlan } from "../../sdj_core_v0_1/src/index.ts";
import "../vendor/sdj_cesium_loader_v0_4.js";

const projectDir = dirname(dirname(fileURLToPath(import.meta.url)));

function readJson(relativePath) {
  return JSON.parse(readFileSync(join(projectDir, relativePath), "utf8"));
}

test("shared Cesium kind targets are total and implemented", () => {
  const entries = Object.entries(CESIUM_KIND_TARGETS);
  assert.ok(entries.length > 0, "expected a non-empty Cesium kind target table");
  assert.deepEqual(
    new Set(entries.map(([, value]) => value.status)),
    new Set(["implemented"])
  );
});

test("vendor loader publishes the shared Cesium kind targets table", () => {
  assert.deepEqual(globalThis.SpatialDisplayJsonKindTargets, CESIUM_KIND_TARGETS);
  assert.deepEqual(globalThis.SpatialDisplayJson.getCesiumKindTargets(), CESIUM_KIND_TARGETS);
});

test("vendor loader falls back to its local Cesium kind targets table when the global override is absent", () => {
  const original = globalThis.SpatialDisplayJsonKindTargets;
  delete globalThis.SpatialDisplayJsonKindTargets;
  try {
    assert.equal(globalThis.SpatialDisplayJsonKindTargets, undefined);
    assert.deepEqual(globalThis.SpatialDisplayJson.getCesiumKindTargets(), CESIUM_KIND_TARGETS);
  } finally {
    globalThis.SpatialDisplayJsonKindTargets = original;
  }
});

test("full coverage scene compiles with no non-implemented Cesium kinds", () => {
  const scene = readJson("examples/sdj_full_coverage_scene_v0_4.json");
  const plan = compileSpatialDisplaySceneToCesiumPlan(scene);
  const nonImplemented = plan.items.filter((item) => item.status !== "implemented");
  assert.deepEqual(nonImplemented, []);
});
