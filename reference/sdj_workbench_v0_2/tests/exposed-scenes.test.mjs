import { readFileSync } from "node:fs";
import { test } from "node:test";
import assert from "node:assert/strict";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const projectDir = dirname(dirname(fileURLToPath(import.meta.url)));

function readJson(relativePath) {
  return JSON.parse(readFileSync(join(projectDir, relativePath), "utf8"));
}

test("exposed scene manifest includes the full corpus", () => {
  const manifest = readJson("data/sdj_exposed_scenes_manifest.json");

  assert.equal(manifest.totalCount, 134);
  assert.equal(manifest.featured.length, 12);
  assert.equal(manifest.defaultPath, manifest.scenes[0].path);
  assert.equal(manifest.featured[0].path, manifest.scenes[0].path);
  assert.equal(manifest.scenes[0].objectCount, manifest.featured[0].objectCount);
  assert.ok(manifest.scenes[0].objectCount >= manifest.scenes[manifest.scenes.length - 1].objectCount);
});
