import { asArray, asObject, type JsonObject } from "./json.ts";
import { flattenObjects } from "./scene.ts";

export const RUNTIME_OBJECT_KINDS = new Set([
  "terrainSurface",
  "customMesh",
  "clippingPlane",
  "clippingPolygon",
  "classificationVolume",
  "customShader",
  "postProcessStage",
  "customPrimitive",
  "primitiveMesh",
  "composite",
  "atmosphere",
  "czmlDataSource",
  "dataSource",
  "geoJsonDataSource",
  "kmlDataSource",
  "skyBox",
  "videoPlane",
  "voxel"
]);

export function collectRuntimeObjects(scene: JsonObject): JsonObject[] {
  const objects = flattenObjects(asArray(scene.objects).map(asObject));
  return dedupeByIdAndKind([
    ...asArray(scene.runtimeObjects).map(asObject),
    ...objects.filter((object) => RUNTIME_OBJECT_KINDS.has(String(object.kind)))
  ]);
}

export function dedupeByIdAndKind(objects: JsonObject[]): JsonObject[] {
  const seen = new Set<string>();
  const result: JsonObject[] = [];
  for (const object of objects) {
    const id = String(object.id || "");
    const kind = String(object.kind || "");
    const key = `${id}::${kind}`;
    if (!id || !kind || seen.has(key)) {
      continue;
    }
    seen.add(key);
    result.push(object);
  }
  return result;
}
