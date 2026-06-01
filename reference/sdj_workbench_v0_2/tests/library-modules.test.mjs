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
} from "../src/lib/index.js";
import {
  buildCompilePlan as buildCompilePlanLegacy,
  createZipBlob as createZipBlobLegacy,
  normalizeSceneForWorkbench as normalizeSceneForWorkbenchLegacy,
  toJson as toJsonLegacy
} from "../src/sdj_browser_compiler.js";

const projectDir = dirname(dirname(fileURLToPath(import.meta.url)));

function readJson(relativePath) {
  return JSON.parse(readFileSync(join(projectDir, relativePath), "utf8"));
}

test("library modules match the legacy compiler surface for normalization and planning", () => {
  const scene = readJson("examples/sdj_minimal_scene.json");
  const capabilities = readJson("data/sdj_backend_capabilities_v0_4.json");

  const normalized = normalizeSceneForWorkbench(scene, capabilities);
  const normalizedLegacy = normalizeSceneForWorkbenchLegacy(scene, capabilities);
  const plan = buildCompilePlan(normalized);
  const planLegacy = buildCompilePlanLegacy(normalizedLegacy);

  assert.deepEqual(normalized, normalizedLegacy);
  assert.deepEqual(plan.kindCounts, planLegacy.kindCounts);
  assert.deepEqual(plan.objectCount, planLegacy.objectCount);
  assert.deepEqual(plan.targetTotals, planLegacy.targetTotals);
  assert.equal(toJson({ ok: true }), toJsonLegacy({ ok: true }));
});

test("library zip helper creates a readable archive blob", async () => {
  const blob = createZipBlob({
    "bundle/manifest.json": toJson({ ok: true }),
    "bundle/notes.txt": "hello\n"
  });

  assert.equal(blob.type, "application/zip");
  assert.ok(blob.size > 0);

  // The legacy wrapper should stay compatible as the library surface evolves.
  const legacyBlob = createZipBlobLegacy({
    "bundle/manifest.json": toJson({ ok: true }),
    "bundle/notes.txt": "hello\n"
  });
  assert.equal(legacyBlob.type, "application/zip");
  assert.equal(legacyBlob.size, blob.size);
});
