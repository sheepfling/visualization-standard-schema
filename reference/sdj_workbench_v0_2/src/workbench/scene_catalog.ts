import { asObject, normalizeSceneForWorkbench, type JsonObject } from "../../../sdj_core_v0_1/src/index.ts";
import { errorMessage, escapeHtml } from "./helpers.ts";
import type { LoadDefaultCapabilitiesDeps, LoadExampleSceneDeps, LoadExposedSceneCatalogDeps, LoadFeaturedExposedSceneDeps, LoadInitialSceneDeps, LoadSceneByPathDeps, LoadSelectedExposedSceneDeps, RenderExposedSceneCatalogDeps, SyncCatalogSelectionDeps, UpdateSelectedCatalogSceneSummaryDeps } from "./scene_shared.ts";
import { EXAMPLE_SCENES, EXPOSED_SCENE_MANIFEST, type ExposedSceneManifest } from "./scene_shared.ts";

export async function loadDefaultCapabilities(deps: LoadDefaultCapabilitiesDeps): Promise<void> {
  try {
    const response = await fetch(new URL("../data/sdj_backend_capabilities_v0_4.json", import.meta.url));
    deps.state.defaultCapabilities = await response.json();
  } catch (error) {
    deps.state.defaultCapabilities = {};
    deps.setStatus(`Capability metadata could not be loaded: ${errorMessage(error)}`, "warning");
  }
}

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

export async function loadInitialScene(deps: LoadInitialSceneDeps): Promise<void> {
  if (deps.state.exposedSceneDefaultPath) {
    const loaded = await deps.loadSceneByPath(deps.state.exposedSceneDefaultPath);
    if (loaded) {
      return;
    }
  }
  await deps.loadExampleScene("minimal");
}

export async function loadSelectedExposedScene(deps: LoadSelectedExposedSceneDeps): Promise<void> {
  const selectedPath = deps.elements.sceneCatalogSelect.value;
  if (!selectedPath) {
    return;
  }
  await deps.loadSceneByPath(selectedPath);
}

export async function loadFeaturedExposedScene(deps: LoadFeaturedExposedSceneDeps): Promise<void> {
  const featured = deps.state.exposedSceneFeatured || [];
  const defaultPath = String(featured[0]?.path || deps.state.exposedSceneDefaultPath || "");
  if (!defaultPath) {
    return;
  }
  await deps.loadSceneByPath(defaultPath);
}

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

export function syncCatalogSelection(deps: SyncCatalogSelectionDeps, relativePath: string): void {
  if (deps.elements.sceneCatalogSelect.value === relativePath) {
    return;
  }
  deps.elements.sceneCatalogSelect.value = relativePath;
}
