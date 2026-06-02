import type { WorkbenchElements, WorkbenchState } from "./sdj";

export interface CesiumSpatialDisplayLoader {
  loadSpatialDisplayScene(viewer: unknown, scene: Record<string, unknown>, options: { zoomToFirstView: boolean }): Promise<{ warnings?: unknown[] }>;
  compileSpatialDisplaySceneToCesiumPlan(scene: Record<string, unknown>): Record<string, unknown>;
  validateSpatialDisplaySceneSemantics(scene: Record<string, unknown>): { errors: string[]; warnings: string[] };
  getCesiumKindTargets(): Record<string, { backend: string; target: string; status: string }>;
}

export interface WorkbenchSmokeApi {
  getRenderSummary(): {
    viewerReady: boolean;
    currentSceneId: string;
    selectedObjectId: string | null;
    entityCount: number;
    primitiveCount: number;
    renderedObjectCount: number;
    warningCount: number;
    statusText: string;
  };
}

export interface AppDeps {
  state: WorkbenchState;
  elements: WorkbenchElements;
}

declare global {
  interface Window {
    Cesium?: unknown;
    SpatialDisplayJson?: CesiumSpatialDisplayLoader;
    SpatialDisplayJsonKindTargets?: Record<string, { backend: string; target: string; status: string }>;
    __sdjWorkbenchSmoke?: WorkbenchSmokeApi;
  }

  var Cesium: unknown;
  var SpatialDisplayJson: CesiumSpatialDisplayLoader | undefined;
  var SpatialDisplayJsonKindTargets: Record<string, { backend: string; target: string; status: string }> | undefined;
  var __sdjWorkbenchSmoke: WorkbenchSmokeApi | undefined;
}
