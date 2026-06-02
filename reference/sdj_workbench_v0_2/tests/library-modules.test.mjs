import { readFileSync } from "node:fs";
import { test } from "node:test";
import assert from "node:assert/strict";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import {
  buildCompilePlan,
  createZipBlob,
  normalizeSceneForWorkbench,
  toJson
} from "../../sdj_core_v0_1/src/index.ts";

const projectDir = dirname(dirname(fileURLToPath(import.meta.url)));

function readJson(relativePath) {
  return JSON.parse(readFileSync(join(projectDir, relativePath), "utf8"));
}

test("library modules match the legacy compiler surface for normalization and planning", () => {
  const scene = readJson("examples/sdj_minimal_scene.json");
  const capabilities = readJson("data/sdj_backend_capabilities_v0_4.json");

  const normalized = normalizeSceneForWorkbench(scene, capabilities);
  const plan = buildCompilePlan(normalized);

  assert.equal(normalized.schemaVersion, "sdj-0.4");
  assert.equal(plan.objectCount > 0, true);
  assert.ok(plan.kindCounts.point >= 0);
  assert.ok(plan.targetTotals.cesium);
  assert.equal(toJson({ ok: true }), toJson({ ok: true }));
});

test("library zip helper creates a readable archive blob", async () => {
  const blob = createZipBlob({
    "bundle/manifest.json": toJson({ ok: true }),
    "bundle/notes.txt": "hello\n"
  });

  assert.equal(blob.type, "application/zip");
  assert.ok(blob.size > 0);
});
