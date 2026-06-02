import { test } from "node:test";
import assert from "node:assert/strict";
import { collectRuntimeObjects } from "../../sdj_core_v0_1/src/index.ts";

test("collectRuntimeObjects merges scene.runtimeObjects with typed runtime families and dedupes by id+kind", () => {
  const scene = {
    runtimeObjects: [
      { id: "runtime-1", kind: "runtime", runtimeType: "runtime", payload: { source: "legacy" } },
      { id: "terrain", kind: "terrainSurface", payload: { note: "scene field" } }
    ],
    objects: [
      { id: "terrain", kind: "terrainSurface", name: "Terrain" },
      { id: "mesh", kind: "customMesh", name: "Mesh" },
      { id: "clip", kind: "clippingPlane", name: "Clip" }
    ]
  };

  const collected = collectRuntimeObjects(scene);

  assert.deepEqual(
    collected.map((item) => `${item.id}:${item.kind}`),
    ["runtime-1:runtime", "terrain:terrainSurface", "mesh:customMesh", "clip:clippingPlane"]
  );
});
