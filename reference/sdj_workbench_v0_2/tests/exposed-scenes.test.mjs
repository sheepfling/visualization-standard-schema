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

  assert.equal(manifest.totalCount, 131);
  assert.equal(manifest.featured.length, 12);
  assert.equal(manifest.defaultPath, "../../../examples/orb-corpus/sdj/orb_format_collection/soap15/scenarios/air_route_simple.sdj.json");
  assert.equal(manifest.scenes[0].name, "air_route_simple");
  assert.equal(manifest.scenes[0].objectCount, 12);
});
