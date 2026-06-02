import { asArray, asObject, createZipBlob, normalizeSceneForWorkbench, toJson, type JsonObject, loadSpatialDisplayScene, type CesiumSpatialDisplayLoader } from "../../../sdj_core_v0_1/src/index.ts";
import { errorMessage, escapeHtml, getCesium, getSdjLoader } from "./helpers.ts";
import type { WorkbenchElements } from "../types/sdj";
import type {
  ExposedSceneManifest,
  LoadDefaultCapabilitiesDeps,
  LoadDroppedFileDeps,
  LoadExampleSceneDeps,
  LoadExposedSceneCatalogDeps,
  LoadFeaturedExposedSceneDeps,
  LoadFileDeps,
  LoadFileInputDeps,
  LoadInitialSceneDeps,
  LoadSceneByPathDeps,
  LoadSelectedExposedSceneDeps,
  ParseEditorSceneDeps,
  RenderEditorSceneDeps,
  RenderExposedSceneCatalogDeps,
  SceneWorkbenchDeps,
  SceneWorkbenchState,
  SaveIonTokenDeps,
  SetEditorSceneDeps,
  StatusDeps,
  UpdateSelectedCatalogSceneSummaryDeps,
  ValidateEditorSceneDeps,
  ClearRenderedSceneDeps,
  FormatEditorJsonDeps,
  ExportAllTargetsDeps,
  ExportNormalizedSdjDeps,
  ExportTargetDeps,
  SyncCatalogSelectionDeps,
  StatusKind
} from "./scene_shared.ts";

export { EXAMPLE_SCENES, EXPOSED_SCENE_MANIFEST, type ExposedSceneManifest, type SceneCatalogEntry, type SceneWorkbenchState } from "./scene_shared.ts";

/**
 * Loads default backend capability metadata used when a scene omits it.
 *
 * @param {{ state: { defaultCapabilities?: JsonObject }, setStatus: (message: string, kind: "ok" | "warning" | "error" | "neutral") => void }} deps
 * @returns {Promise<void>}
 */
export async function loadDefaultCapabilities(deps: LoadDefaultCapabilitiesDeps): Promise<void> {
  try {
    const response = await fetch(new URL("../data/sdj_backend_capabilities_v0_4.json", import.meta.url));
    deps.state.defaultCapabilities = await response.json();
  } catch (error) {
    deps.state.defaultCapabilities = {};
    deps.setStatus(`Capability metadata could not be loaded: ${errorMessage(error)}`, "warning");
  }
}

/**
 * Loads a built-in example scene into the editor.
 *
 * @param {{
 *   state: { defaultCapabilities?: JsonObject },
 *   setEditorScene: (scene: JsonObject) => void,
 *   updatePanels: (scene: JsonObject) => void,
 *   setStatus: (message: string, kind: "ok" | "warning" | "error" | "neutral") => void
 * }} deps
 * @param {"minimal" | "full"} key
 * @returns {Promise<void>}
 */
export async function loadExampleScene(deps: LoadExampleSceneDeps, key: "minimal" | "full"): Promise<void> {
  try {
    const response = await fetch(new URL(EXAMPLE_SCENES[key], import.meta.url));
    const scene = await response.json();
    const normalized = normalizeSceneForWorkbench(scene as JsonObject, deps.state.defaultCapabilities) as JsonObject;
    deps.setEditorScene(normalized);
    deps.updatePanels(normalized);
    deps.setStatus(`Loaded ${key} example scene.`, "ok");
  } catch (error) {
    deps.setStatus(`Failed to load ${key} example: ${errorMessage(error)}`, "error");
  }
}

/**
 * Loads the manifest of exposed SDJ scenes that should be available to default users.
 *
 * @param {{
 *   state: { exposedSceneCatalog?: JsonObject[], exposedSceneFeatured?: JsonObject[], exposedSceneDefaultPath?: string },
 *   elements: { sceneCatalogSummary: HTMLElement },
 *   renderExposedSceneCatalog: () => void,
 *   updateSelectedCatalogSceneSummary: () => void,
 *   setStatus: (message: string, kind: "ok" | "warning" | "error" | "neutral") => void
 * }} deps
 * @returns {Promise<void>}
 */
export async function loadExposedSceneCatalog(deps: LoadExposedSceneCatalogDeps): Promise<void> {
  try {
    const response = await fetch(new URL(EXPOSED_SCENE_MANIFEST, import.meta.url));
    const manifest = await response.json() as ExposedSceneManifest;
    deps.state.exposedSceneCatalog = Array.isArray(manifest.scenes) ? manifest.scenes : [];
    deps.state.exposedSceneFeatured = Array.isArray(manifest.featured) ? manifest.featured : [];
    deps.state.exposedSceneDefaultPath = String(manifest.defaultPath || deps.state.exposedSceneFeatured?.[0]?.path || "");
    deps.renderExposedSceneCatalog();
    deps.updateSelectedCatalogSceneSummary();
  } catch (error) {
    deps.state.exposedSceneCatalog = [];
    deps.state.exposedSceneFeatured = [];
    deps.state.exposedSceneDefaultPath = undefined;
    deps.elements.sceneCatalogSummary.textContent = "Exposed SDJ scenes could not be loaded; falling back to the built-in examples.";
    deps.setStatus(`Exposed SDJ catalog could not be loaded: ${errorMessage(error)}`, "warning");
  }
}

/**
 * Loads the most representative exposed SDJ scene on startup.
 *
 * @param {{ state: { exposedSceneDefaultPath?: string }, loadSceneByPath: (relativePath: string) => Promise<boolean>, loadExampleScene: (key: "minimal" | "full") => Promise<void> }} deps
 * @returns {Promise<void>}
 */
export async function loadInitialScene(deps: LoadInitialSceneDeps): Promise<void> {
  if (deps.state.exposedSceneDefaultPath) {
    const loaded = await deps.loadSceneByPath(deps.state.exposedSceneDefaultPath);
    if (loaded) {
      return;
    }
  }
  await deps.loadExampleScene("minimal");
}

/**
 * Loads the scene selected in the exposed-scene picker.
 *
 * @param {{ elements: { sceneCatalogSelect: HTMLSelectElement }, loadSceneByPath: (relativePath: string) => Promise<boolean> }} deps
 * @returns {Promise<void>}
 */
export async function loadSelectedExposedScene(deps: LoadSelectedExposedSceneDeps): Promise<void> {
  const selectedPath = deps.elements.sceneCatalogSelect.value;
  if (!selectedPath) {
    return;
  }
  await deps.loadSceneByPath(selectedPath);
}

/**
 * Loads the featured exposed scene.
 *
 * @param {{ state: { exposedSceneFeatured?: JsonObject[], exposedSceneDefaultPath?: string }, loadSceneByPath: (relativePath: string) => Promise<boolean> }} deps
 * @returns {Promise<void>}
 */
export async function loadFeaturedExposedScene(deps: LoadFeaturedExposedSceneDeps): Promise<void> {
  const featured = deps.state.exposedSceneFeatured || [];
  const defaultPath = String(featured[0]?.path || deps.state.exposedSceneDefaultPath || "");
  if (!defaultPath) {
    return;
  }
  await deps.loadSceneByPath(defaultPath);
}

/**
 * Loads a scene by a path relative to this module.
 *
 * @param {{
 *   state: { defaultCapabilities?: JsonObject },
 *   setEditorScene: (scene: JsonObject) => void,
 *   updatePanels: (scene: JsonObject) => void,
 *   syncCatalogSelection: (relativePath: string) => void,
 *   setStatus: (message: string, kind: "ok" | "warning" | "error" | "neutral") => void
 * }} deps
 * @param {string} relativePath
 * @returns {Promise<boolean>}
 */
export async function loadSceneByPath(deps: LoadSceneByPathDeps, relativePath: string): Promise<boolean> {
  try {
    const response = await fetch(new URL(relativePath, import.meta.url));
    const scene = await response.json();
    const normalized = normalizeSceneForWorkbench(scene as JsonObject, deps.state.defaultCapabilities);
    deps.setEditorScene(normalized);
    deps.updatePanels(normalized);
    deps.syncCatalogSelection(relativePath);
    const document = normalized.document as JsonObject | undefined;
    const loadedName = String(document?.name || document?.id || relativePath);
    deps.setStatus(`Loaded exposed scene: ${loadedName}.`, "ok");
    return true;
  } catch (error) {
    deps.setStatus(`Failed to load scene ${relativePath}: ${errorMessage(error)}`, "error");
    return false;
  }
}

/**
 * Renders the exposed-scene picker.
 *
 * @param {{
 *   state: { exposedSceneCatalog?: JsonObject[], exposedSceneFeatured?: JsonObject[], exposedSceneDefaultPath?: string },
 *   elements: { sceneCatalogFilter: HTMLInputElement, sceneCatalogSelect: HTMLSelectElement },
 *   updateSelectedCatalogSceneSummary: () => void
 * }} deps
 * @returns {void}
 */
export function renderExposedSceneCatalog(deps: RenderExposedSceneCatalogDeps): void {
  const catalog = (Array.isArray(deps.state.exposedSceneCatalog) ? deps.state.exposedSceneCatalog : []) as JsonObject[];
  const filter = deps.elements.sceneCatalogFilter.value.trim().toLowerCase();
  const featured = (deps.state.exposedSceneFeatured || []) as JsonObject[];
  const featuredPaths = new Set(featured.map((item) => String(asObject(item).path || "")));
  const scenes = catalog.filter((scene) => {
    if (!filter) {
      return true;
    }
    const haystack = `${String(scene.name || "")} ${String(scene.id || "")} ${String(scene.group || "")} ${String(scene.source || "")} ${String(scene.objectCount || "")}`.toLowerCase();
    return haystack.includes(filter);
  });
  const featuredScenes = scenes.filter((scene) => featuredPaths.has(String(scene.path || "")));
  const remaining = scenes.filter((scene) => !featuredPaths.has(String(scene.path || "")));
  const optionHtml = (items: JsonObject[], label: string) => {
    if (items.length === 0) {
      return "";
    }
    return `<optgroup label="${escapeHtml(label)}">${items.map((scene) => {
      const path = String(scene.path || "");
      const title = `${String(scene.name || path)} [${Number(scene.objectCount || 0)}]`;
      const group = String(scene.group || "");
      const source = String(scene.source || "");
      return `<option value="${escapeHtml(path)}" title="${escapeHtml(source)}">${escapeHtml(`${title} - ${group}`)}</option>`;
    }).join("")}</optgroup>`;
  };
  deps.elements.sceneCatalogSelect.innerHTML = [
    optionHtml(featuredScenes, "Featured exposed scenes"),
    optionHtml(remaining, "All exposed scenes")
  ].join("") || `<option value="" disabled selected>No exposed scenes available</option>`;

  if (!deps.elements.sceneCatalogSelect.value) {
    const initialPath = deps.state.exposedSceneDefaultPath || String(featuredScenes[0]?.path || remaining[0]?.path || "");
    if (initialPath) {
      deps.elements.sceneCatalogSelect.value = initialPath;
    }
  }

  deps.updateSelectedCatalogSceneSummary();
}

/**
 * Keeps the catalog summary aligned with the selected exposed scene.
 *
 * @param {{ state: { exposedSceneCatalog?: JsonObject[] }, elements: { sceneCatalogSelect: HTMLSelectElement, sceneCatalogSummary: HTMLElement } }} deps
 * @returns {void}
 */
export function updateSelectedCatalogSceneSummary(deps: UpdateSelectedCatalogSceneSummaryDeps): void {
  const catalog = (Array.isArray(deps.state.exposedSceneCatalog) ? deps.state.exposedSceneCatalog : []) as JsonObject[];
  const selectedPath = deps.elements.sceneCatalogSelect.value;
  if (!selectedPath) {
    deps.elements.sceneCatalogSummary.textContent = `${catalog.length} exposed SDJ scenes available from the imported corpus.`;
    return;
  }
  const selected = catalog.find((scene) => String(scene.path || "") === selectedPath);
  if (!selected) {
    deps.elements.sceneCatalogSummary.textContent = `${catalog.length} exposed SDJ scenes available from the imported corpus.`;
    return;
  }
  deps.elements.sceneCatalogSummary.textContent = `${catalog.length} exposed SDJ scenes available. Selected: ${String(selected.name || selected.path)} · ${Number(selected.objectCount || 0)} object(s) · ${String(selected.group || "")}`;
}

/**
 * Keeps the picker selection in sync after the user loads a scene.
 *
 * @param {{ elements: { sceneCatalogSelect: HTMLSelectElement } }} deps
 * @param {string} relativePath
 * @returns {void}
 */
export function syncCatalogSelection(deps: SyncCatalogSelectionDeps, relativePath: string): void {
  if (deps.elements.sceneCatalogSelect.value === relativePath) {
    return;
  }
  deps.elements.sceneCatalogSelect.value = relativePath;
}

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

/**
 * Validates the scene currently in the editor.
 *
 * @param {{ parseEditorScene: () => JsonObject, updatePanels: (scene: JsonObject) => void, setStatus: (message: string, kind: "ok" | "warning" | "error" | "neutral") => void, clearPanels: () => void, validateSemantics: (scene: JsonObject) => { errors: unknown[], warnings: unknown[] }, errorMessage: (error: unknown) => string }} deps
 * @returns {void}
 */
export function validateEditorScene(deps: ValidateEditorSceneDeps): void {
  try {
    const scene = deps.parseEditorScene();
    const semantic = deps.validateSemantics(scene);
    deps.updatePanels(scene);
    if (semantic.errors.length > 0) {
      deps.setStatus(`Validation failed with ${semantic.errors.length} error(s).`, "error");
      return;
    }
    deps.setStatus(`Validation passed with ${semantic.warnings.length} warning(s).`, semantic.warnings.length > 0 ? "warning" : "ok");
  } catch (error) {
    deps.setStatus(`Invalid JSON: ${errorMessage(error)}`, "error");
    deps.clearPanels();
  }
}

/**
 * Parses and renders the editor scene into Cesium.
 *
 * @param {{
 *   parseEditorScene: () => JsonObject,
 *   validateSemantics: (scene: JsonObject) => { errors: unknown[], warnings: unknown[] },
 *   updatePanels: (scene: JsonObject) => void,
 *   clearRenderedScene: () => void,
 *   getSdjLoader?: () => { loadSpatialDisplayScene: (viewer: unknown, scene: JsonObject, options: { zoomToFirstView: boolean }) => Promise<{ warnings?: unknown[] }> },
 *   state: { viewer?: unknown, lastLoad?: { warnings?: unknown[] }, currentScene?: JsonObject },
 *   setStatus: (message: string, kind: "ok" | "warning" | "error" | "neutral") => void,
 *   countRenderableObjects: (scene: JsonObject) => number,
 *   errorMessage: (error: unknown) => string
 * }} deps
 * @returns {Promise<void>}
 */
export async function renderEditorScene(deps: RenderEditorSceneDeps): Promise<void> {
  try {
    const scene = deps.parseEditorScene();
    const semantic = deps.validateSemantics(scene);
    deps.updatePanels(scene);
    if (semantic.errors.length > 0) {
      deps.setStatus(`Not rendering; scene has ${semantic.errors.length} semantic error(s).`, "error");
      return;
    }
    deps.clearRenderedScene();
    const loader = deps.getSdjLoader ? deps.getSdjLoader() : getSdjLoader();
    const loadResult = await loadSpatialDisplayScene(deps.state.viewer, scene, { zoomToFirstView: true }, loader) as {
      warnings?: unknown[];
      entities?: Map<string, unknown>;
      primitives?: Map<string, unknown>;
    };
    deps.state.lastLoad = {
      ...loadResult,
      warnings: (loadResult.warnings || []).map((warning) => String(warning))
    };
    deps.state.currentScene = scene;
    const warningCount = (deps.state.lastLoad?.warnings || []).length + semantic.warnings.length;
    deps.setStatus(`Rendered ${deps.countRenderableObjects(scene)} object(s) into Cesium. Warnings: ${warningCount}.`, warningCount > 0 ? "warning" : "ok");
  } catch (error) {
    deps.setStatus(`Render failed: ${errorMessage(error)}`, "error");
  }
}

/**
 * Removes the most recent SDJ render pass from Cesium.
 *
 * @param {{ state: { viewer?: unknown, lastLoad?: { entities?: Map<string, unknown>, primitives?: Map<string, unknown> } }, elements: { selectedObject: HTMLElement }, setStatus: (message: string, kind: "ok" | "warning" | "error" | "neutral") => void }} deps
 * @returns {void}
 */
export function clearRenderedScene(deps: ClearRenderedSceneDeps): void {
  const lastLoad = deps.state.lastLoad;
  if (!deps.state.viewer || !lastLoad) {
    return;
  }
  const viewer = deps.state.viewer as { entities: { remove: (entity: unknown) => void }; scene: { primitives: { remove: (primitive: unknown) => void } } } | undefined;
  if (lastLoad.entities) {
    for (const entity of lastLoad.entities.values()) {
      viewer?.entities.remove(entity);
    }
  }
  if (lastLoad.primitives) {
    for (const primitive of lastLoad.primitives.values()) {
      try {
        viewer?.scene.primitives.remove(primitive);
      } catch (error) {
        console.warn("Unable to remove primitive", primitive, error);
      }
    }
  }
  deps.state.lastLoad = undefined;
  deps.elements.selectedObject.textContent = "No object selected";
  deps.setStatus("Cleared rendered SDJ objects.", "neutral");
}

/**
 * Formats editor JSON.
 *
 * @param {{ parseEditorScene: () => JsonObject, setEditorScene: (scene: JsonObject) => void, updatePanels: (scene: JsonObject) => void, setStatus: (message: string, kind: "ok" | "warning" | "error" | "neutral") => void, errorMessage: (error: unknown) => string }} deps
 * @returns {void}
 */
export function formatEditorJson(deps: FormatEditorJsonDeps): void {
  try {
    const scene = deps.parseEditorScene();
    deps.setEditorScene(scene);
    deps.updatePanels(scene);
    deps.setStatus("Formatted and normalized editor JSON.", "ok");
  } catch (error) {
    deps.setStatus(`Cannot format invalid JSON: ${errorMessage(error)}`, "error");
  }
}

/**
 * Downloads normalized SDJ JSON.
 *
 * @param {{ parseEditorScene: () => JsonObject, downloadText: (filename: string, content: string, mimeType: string) => void, setStatus: (message: string, kind: "ok" | "warning" | "error" | "neutral") => void, errorMessage: (error: unknown) => string }} deps
 * @returns {void}
 */
export function exportNormalizedSdj(deps: ExportNormalizedSdjDeps): void {
  try {
    const scene = deps.parseEditorScene();
    deps.downloadText("scene.sdj.json", toJson(scene), "application/json");
    deps.setStatus("Exported normalized SDJ JSON.", "ok");
  } catch (error) {
    deps.setStatus(`SDJ export failed: ${errorMessage(error)}`, "error");
  }
}

/**
 * Exports a single backend bundle as a ZIP.
 *
 * @param {{
 *   parseEditorScene: () => JsonObject,
 *   compileBackend: (scene: JsonObject, target: "cesium" | "simdis" | "soap") => { files: Record<string, string> },
 *   createZipBlob: (files: Record<string, string>) => Blob,
 *   downloadBlob: (blob: Blob, filename: string) => void,
 *   setStatus: (message: string, kind: "ok" | "warning" | "error" | "neutral") => void,
 *   errorMessage: (error: unknown) => string
 * }} deps
 * @param {"cesium" | "simdis" | "soap"} target
 * @returns {void}
 */
export function exportTarget(deps: ExportTargetDeps, target: "cesium" | "simdis" | "soap"): void {
  try {
    const scene = deps.parseEditorScene();
    const bundle = deps.compileBackend(scene, target);
    const blob = deps.createZipBlob(bundle.files);
    deps.downloadBlob(blob, `sdj-${target}-export.zip`);
    deps.setStatus(`Exported ${target.toUpperCase()} bundle with ${Object.keys(bundle.files).length} file(s).`, "ok");
  } catch (error) {
    deps.setStatus(`${target.toUpperCase()} export failed: ${errorMessage(error)}`, "error");
  }
}

/**
 * Exports all backend bundles as one ZIP.
 *
 * @param {{
 *   parseEditorScene: () => JsonObject,
 *   compileAllBackendsToFiles: (scene: JsonObject) => Record<string, string>,
 *   createZipBlob: (files: Record<string, string>) => Blob,
 *   downloadBlob: (blob: Blob, filename: string) => void,
 *   setStatus: (message: string, kind: "ok" | "warning" | "error" | "neutral") => void,
 *   errorMessage: (error: unknown) => string
 * }} deps
 * @returns {void}
 */
export function exportAllTargets(deps: ExportAllTargetsDeps): void {
  try {
    const scene = deps.parseEditorScene();
    const files = deps.compileAllBackendsToFiles(scene);
    const blob = deps.createZipBlob(files);
    deps.downloadBlob(blob, "sdj-all-backends-export.zip");
    deps.setStatus(`Exported all backend bundles with ${Object.keys(files).length} file(s).`, "ok");
  } catch (error) {
    deps.setStatus(`All-target export failed: ${errorMessage(error)}`, "error");
  }
}

/**
 * Loads a scene from the file input control.
 *
 * @param {{ elements: { fileInput: HTMLInputElement }, loadFile: (file: File) => Promise<void> }} deps
 * @returns {Promise<void>}
 */
export async function loadFileInput(deps: LoadFileInputDeps): Promise<void> {
  const file = deps.elements.fileInput.files ? deps.elements.fileInput.files[0] : undefined;
  if (!file) {
    return;
  }
  await deps.loadFile(file);
  deps.elements.fileInput.value = "";
}

/**
 * Loads a dropped scene file.
 *
 * @param {{ loadFile: (file: File) => Promise<void> }} deps
 * @param {DragEvent} event
 * @returns {Promise<void>}
 */
export async function loadDroppedFile(deps: LoadDroppedFileDeps, event: DragEvent): Promise<void> {
  const file = event.dataTransfer && event.dataTransfer.files.length > 0 ? event.dataTransfer.files[0] : undefined;
  if (!file) {
    return;
  }
  await deps.loadFile(file);
}

/**
 * Loads a JSON file into the editor.
 *
 * @param {{
 *   state: { defaultCapabilities?: JsonObject },
 *   setEditorScene: (scene: JsonObject) => void,
 *   updatePanels: (scene: JsonObject) => void,
 *   setStatus: (message: string, kind: "ok" | "warning" | "error" | "neutral") => void
 * }} deps
 * @param {File} file
 * @returns {Promise<void>}
 */
export async function loadFile(deps: LoadFileDeps, file: File): Promise<void> {
  try {
    const text = await file.text();
    const parsed = JSON.parse(text) as JsonObject;
    const normalized = normalizeSceneForWorkbench(parsed, deps.state.defaultCapabilities);
    deps.setEditorScene(normalized);
    deps.updatePanels(normalized);
    deps.setStatus(`Loaded ${file.name}.`, "ok");
  } catch (error) {
    deps.setStatus(`Could not load ${file.name}: ${errorMessage(error)}`, "error");
  }
}

/**
 * Saves the current Cesium ion token to local storage.
 *
 * @param {{ elements: { ionTokenInput: HTMLInputElement }, setStatus: (message: string, kind: "ok" | "warning" | "error" | "neutral") => void }} deps
 * @returns {void}
 */
export function saveIonToken(deps: SaveIonTokenDeps): void {
  const token = deps.elements.ionTokenInput.value.trim();
  const Cesium = getCesium();
  if (token) {
    localStorage.setItem("sdj.cesiumIonToken", token);
    Cesium.Ion.defaultAccessToken = token;
    deps.setStatus("Saved Cesium ion token for this browser.", "ok");
  } else {
    localStorage.removeItem("sdj.cesiumIonToken");
    deps.setStatus("Cleared Cesium ion token from this browser.", "neutral");
  }
}
