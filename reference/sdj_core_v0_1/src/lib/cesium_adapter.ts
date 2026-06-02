import type { JsonObject } from "./json.ts";

export interface CesiumSpatialDisplayLoader {
  loadSpatialDisplayScene: (viewer: unknown, scene: JsonObject, options: { zoomToFirstView: boolean }) => Promise<{ warnings?: unknown[] }>;
  compileSpatialDisplaySceneToCesiumPlan: (scene: JsonObject) => JsonObject;
  validateSpatialDisplaySceneSemantics: (scene: JsonObject) => { errors: string[]; warnings: string[] };
  getCesiumKindTargets: () => Record<string, { backend: string; target: string; status: string }>;
}

export function resolveCesiumSpatialDisplayLoader(loader: CesiumSpatialDisplayLoader | undefined = (globalThis as any).SpatialDisplayJson): CesiumSpatialDisplayLoader {
  if (!loader) {
    throw new Error("SpatialDisplayJson loader is not loaded.");
  }
  return loader;
}

export function getCesiumKindTargets(loader?: CesiumSpatialDisplayLoader): Record<string, { backend: string; target: string; status: string }> {
  return resolveCesiumSpatialDisplayLoader(loader).getCesiumKindTargets();
}

export function compileSpatialDisplaySceneToCesiumPlan(scene: JsonObject, loader?: CesiumSpatialDisplayLoader): JsonObject {
  return resolveCesiumSpatialDisplayLoader(loader).compileSpatialDisplaySceneToCesiumPlan(scene);
}

export function validateSpatialDisplaySceneSemantics(scene: JsonObject, loader?: CesiumSpatialDisplayLoader): { errors: string[]; warnings: string[] } {
  return resolveCesiumSpatialDisplayLoader(loader).validateSpatialDisplaySceneSemantics(scene);
}

export function loadSpatialDisplayScene(
  viewer: unknown,
  scene: JsonObject,
  options: { zoomToFirstView: boolean },
  loader?: CesiumSpatialDisplayLoader
): Promise<{ warnings?: unknown[] }> {
  return resolveCesiumSpatialDisplayLoader(loader).loadSpatialDisplayScene(viewer, scene, options);
}
