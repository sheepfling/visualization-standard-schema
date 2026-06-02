import { normalizeSceneForWorkbench, toJson, type JsonObject } from "../../../sdj_core_v0_1/src/index.ts";
import type { ParseEditorSceneDeps, SetEditorSceneDeps } from "./scene_shared.ts";

export { EXAMPLE_SCENES, EXPOSED_SCENE_MANIFEST, type ExposedSceneManifest, type SceneCatalogEntry, type SceneWorkbenchState } from "./scene_shared.ts";

/**
 * Loads default backend capability metadata used when a scene omits it.
 *
 * @param {{ state: { defaultCapabilities?: JsonObject }, setStatus: (message: string, kind: "ok" | "warning" | "error" | "neutral") => void }} deps
 * @returns {Promise<void>}
 */
export {
  loadDefaultCapabilities,
  loadExampleScene,
  loadExposedSceneCatalog,
  loadFeaturedExposedScene,
  loadInitialScene,
  loadSceneByPath,
  loadSelectedExposedScene,
  renderExposedSceneCatalog,
  syncCatalogSelection,
  updateSelectedCatalogSceneSummary
} from "./scene_catalog.ts";

/**
 * Parses and normalizes the editor JSON.
 *
 * @param {{ elements: { editor: HTMLTextAreaElement }, state: { defaultCapabilities?: JsonObject } }} deps
 * @returns {JsonObject}
 */
export function parseEditorScene(deps: ParseEditorSceneDeps): JsonObject {
  const parsed = JSON.parse(deps.elements.editor.value) as JsonObject;
  return normalizeSceneForWorkbench(parsed, deps.state.defaultCapabilities);
}

/**
 * Sets the editor text from a scene object.
 *
 * @param {{ elements: { editor: HTMLTextAreaElement }, state: { currentScene?: JsonObject, selectedObjectId?: string }, findSceneObject: (scene: JsonObject, objectId: string) => JsonObject | undefined }} deps
 * @param {JsonObject} scene
 * @returns {void}
 */
export function setEditorScene(deps: SetEditorSceneDeps, scene: JsonObject): void {
  deps.elements.editor.value = toJson(scene);
  deps.state.currentScene = scene;
  if (deps.state.selectedObjectId && !deps.findSceneObject(scene, deps.state.selectedObjectId)) {
    deps.state.selectedObjectId = undefined;
  }
}
