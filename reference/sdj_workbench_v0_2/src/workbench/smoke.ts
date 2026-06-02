import type { WorkbenchElements } from "../types/sdj";

type WorkbenchSmokeState = {
  viewer?: unknown;
  lastLoad?: {
    entities?: Map<string, unknown>;
    primitives?: Map<string, unknown>;
    warnings?: string[];
  };
  currentScene?: {
    document?: {
      id?: string;
      name?: string;
    };
  };
  selectedObjectId?: string;
};

type WorkbenchSmokeApi = {
  getRenderSummary: () => {
    viewerReady: boolean;
    currentSceneId: string;
    selectedObjectId: string | null;
    entityCount: number;
    primitiveCount: number;
    renderedObjectCount: number;
    warningCount: number;
    statusText: string;
  };
};

/**
 * Returns the current rendered-state summary for browser smoke checks.
 *
 * @param {{ state: WorkbenchSmokeState, elements: Pick<WorkbenchElements, "statusText"> }} deps
 */
export function getRenderSummary(deps: { state: WorkbenchSmokeState; elements: Pick<WorkbenchElements, "statusText"> }) {
  const entityCount = deps.state.lastLoad?.entities ? deps.state.lastLoad.entities.size : 0;
  const primitiveCount = deps.state.lastLoad?.primitives ? deps.state.lastLoad.primitives.size : 0;
  const warningCount = deps.state.lastLoad?.warnings ? deps.state.lastLoad.warnings.length : 0;
  return {
    viewerReady: Boolean(deps.state.viewer),
    currentSceneId: String(deps.state.currentScene?.document?.id || deps.state.currentScene?.document?.name || ""),
    selectedObjectId: deps.state.selectedObjectId || null,
    entityCount,
    primitiveCount,
    renderedObjectCount: entityCount + primitiveCount,
    warningCount,
    statusText: String(deps.elements.statusText.textContent || "")
  };
}

/**
 * Installs the smoke API on the global object for external browser harnesses.
 *
 * @param {{ state: WorkbenchSmokeState, elements: Pick<WorkbenchElements, "statusText"> }} deps
 * @returns {WorkbenchSmokeApi}
 */
export function installWorkbenchSmokeApi(deps: { state: WorkbenchSmokeState; elements: Pick<WorkbenchElements, "statusText"> }): WorkbenchSmokeApi {
  const api = {
    getRenderSummary: () => getRenderSummary(deps)
  };
  globalThis.__sdjWorkbenchSmoke = api;
  return api;
}
