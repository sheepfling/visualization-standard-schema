import { loadSpatialDisplayScene, normalizeSceneForWorkbench, toJson, type JsonObject } from "../../../sdj_core_v0_1/src/index.ts";
import { errorMessage, getCesium, getSdjLoader } from "./helpers.ts";
import type {
  ClearRenderedSceneDeps,
  ExportAllTargetsDeps,
  ExportNormalizedSdjDeps,
  ExportTargetDeps,
  FormatEditorJsonDeps,
  LoadDroppedFileDeps,
  LoadFileDeps,
  LoadFileInputDeps,
  RenderEditorSceneDeps,
  SaveIonTokenDeps,
  ValidateEditorSceneDeps
} from "./scene_shared.ts";

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

export function exportNormalizedSdj(deps: ExportNormalizedSdjDeps): void {
  try {
    const scene = deps.parseEditorScene();
    deps.downloadText("scene.sdj.json", toJson(scene), "application/json");
    deps.setStatus("Exported normalized SDJ JSON.", "ok");
  } catch (error) {
    deps.setStatus(`SDJ export failed: ${errorMessage(error)}`, "error");
  }
}

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

export async function loadFileInput(deps: LoadFileInputDeps): Promise<void> {
  const file = deps.elements.fileInput.files ? deps.elements.fileInput.files[0] : undefined;
  if (!file) {
    return;
  }
  await deps.loadFile(file);
  deps.elements.fileInput.value = "";
}

export async function loadDroppedFile(deps: LoadDroppedFileDeps, event: DragEvent): Promise<void> {
  const file = event.dataTransfer && event.dataTransfer.files.length > 0 ? event.dataTransfer.files[0] : undefined;
  if (!file) {
    return;
  }
  await deps.loadFile(file);
}

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
