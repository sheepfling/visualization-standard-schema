import type { JsonObject } from "../../../sdj_core_v0_1/src/index.ts";
import type { WorkbenchElements, WorkbenchState } from "../types/sdj";

export type StatusKind = "ok" | "warning" | "error" | "neutral";

export interface SceneCatalogEntry {
  name?: string;
  id?: string;
  group?: string;
  source?: string;
  objectCount?: number;
  path?: string;
}

export interface ExposedSceneManifest {
  scenes?: SceneCatalogEntry[];
  featured?: SceneCatalogEntry[];
  defaultPath?: string;
}

export type SceneWorkbenchState = Omit<WorkbenchState, "exposedSceneCatalog" | "exposedSceneFeatured" | "exposedSceneDefaultPath"> & {
  exposedSceneCatalog?: SceneCatalogEntry[];
  exposedSceneFeatured?: SceneCatalogEntry[];
  exposedSceneDefaultPath?: string;
};

export interface SceneWorkbenchDeps {
  state: SceneWorkbenchState;
  elements: WorkbenchElements;
  setStatus: (message: string, kind: StatusKind) => void;
  setEditorScene: (scene: JsonObject) => void;
  updatePanels: (scene: JsonObject) => void;
  syncCatalogSelection: (relativePath: string) => void;
  renderExposedSceneCatalog: () => void;
  updateSelectedCatalogSceneSummary: () => void;
  loadSceneByPath: (relativePath: string) => Promise<boolean>;
  loadExampleScene: (key: "minimal" | "full") => Promise<void>;
  validateSemantics: (scene: JsonObject) => { errors: unknown[]; warnings: unknown[] };
  clearPanels: () => void;
  clearRenderedScene: () => void;
  countRenderableObjects: (scene: JsonObject) => number;
  parseEditorScene: () => JsonObject;
  loadFile: (file: File) => Promise<void>;
  downloadText: (filename: string, content: string, mimeType: string) => void;
  downloadBlob: (blob: Blob, filename: string) => void;
  createZipBlob: (files: Record<string, string>) => Blob;
  compileBackend: (scene: JsonObject, target: "cesium" | "simdis" | "soap") => { files: Record<string, string> };
  compileAllBackendsToFiles: (scene: JsonObject) => Record<string, string>;
  getSdjLoader: () => CesiumSpatialDisplayLoader;
  findSceneObject: (scene: JsonObject, objectId: string) => JsonObject | undefined;
  inspectObject: (scene: JsonObject, objectId: string, plan?: JsonObject) => JsonObject | undefined;
}

export type LoadDefaultCapabilitiesDeps = { state: Pick<SceneWorkbenchState, "defaultCapabilities"> } & StatusDeps;
export type LoadExampleSceneDeps = {
  state: Pick<SceneWorkbenchState, "defaultCapabilities">;
  setEditorScene: (scene: JsonObject) => void;
  updatePanels: (scene: JsonObject) => void;
} & StatusDeps;
export type LoadExposedSceneCatalogDeps = {
  state: Pick<SceneWorkbenchState, "defaultCapabilities" | "exposedSceneCatalog" | "exposedSceneFeatured" | "exposedSceneDefaultPath">;
  elements: Pick<WorkbenchElements, "sceneCatalogSummary">;
  renderExposedSceneCatalog: () => void;
  updateSelectedCatalogSceneSummary: () => void;
} & StatusDeps;
export type LoadInitialSceneDeps = {
  state: Pick<SceneWorkbenchState, "exposedSceneDefaultPath">;
  loadSceneByPath: (relativePath: string) => Promise<boolean>;
  loadExampleScene: (key: "minimal" | "full") => Promise<void>;
};
export type LoadSelectedExposedSceneDeps = {
  elements: Pick<WorkbenchElements, "sceneCatalogSelect">;
  loadSceneByPath: (relativePath: string) => Promise<boolean>;
};
export type LoadFeaturedExposedSceneDeps = {
  state: Pick<SceneWorkbenchState, "exposedSceneFeatured" | "exposedSceneDefaultPath">;
  loadSceneByPath: (relativePath: string) => Promise<boolean>;
};
export type LoadSceneByPathDeps = {
  state: Pick<SceneWorkbenchState, "defaultCapabilities">;
  setEditorScene: (scene: JsonObject) => void;
  updatePanels: (scene: JsonObject) => void;
  syncCatalogSelection: (relativePath: string) => void;
} & StatusDeps;
export type RenderExposedSceneCatalogDeps = {
  state: Pick<SceneWorkbenchState, "exposedSceneCatalog" | "exposedSceneFeatured" | "exposedSceneDefaultPath">;
  elements: Pick<WorkbenchElements, "sceneCatalogFilter" | "sceneCatalogSelect">;
  updateSelectedCatalogSceneSummary: () => void;
};
export type UpdateSelectedCatalogSceneSummaryDeps = {
  state: Pick<SceneWorkbenchState, "exposedSceneCatalog">;
  elements: Pick<WorkbenchElements, "sceneCatalogSelect" | "sceneCatalogSummary">;
};
export type SyncCatalogSelectionDeps = { elements: Pick<WorkbenchElements, "sceneCatalogSelect"> };
export type ParseEditorSceneDeps = { elements: Pick<WorkbenchElements, "editor">; state: Pick<SceneWorkbenchState, "defaultCapabilities"> };
export type SetEditorSceneDeps = {
  elements: Pick<WorkbenchElements, "editor">;
  state: Pick<SceneWorkbenchState, "currentScene" | "selectedObjectId">;
  findSceneObject: (scene: JsonObject, objectId: string) => JsonObject | undefined;
};
export type ValidateEditorSceneDeps = {
  parseEditorScene: () => JsonObject;
  updatePanels: (scene: JsonObject) => void;
  clearPanels: () => void;
  validateSemantics: (scene: JsonObject) => { errors: unknown[]; warnings: unknown[] };
} & StatusDeps;
export type RenderEditorSceneDeps = {
  parseEditorScene: () => JsonObject;
  validateSemantics: (scene: JsonObject) => { errors: unknown[]; warnings: unknown[] };
  updatePanels: (scene: JsonObject) => void;
  clearRenderedScene: () => void;
  getSdjLoader?: () => CesiumSpatialDisplayLoader;
  state: Pick<SceneWorkbenchState, "viewer" | "lastLoad" | "currentScene">;
  countRenderableObjects: (scene: JsonObject) => number;
} & StatusDeps;
export type ClearRenderedSceneDeps = {
  state: Pick<SceneWorkbenchState, "viewer" | "lastLoad">;
  elements: Pick<WorkbenchElements, "selectedObject">;
} & StatusDeps;
export type FormatEditorJsonDeps = {
  parseEditorScene: () => JsonObject;
  setEditorScene: (scene: JsonObject) => void;
  updatePanels: (scene: JsonObject) => void;
} & StatusDeps;
export type ExportNormalizedSdjDeps = { parseEditorScene: () => JsonObject; downloadText: (filename: string, content: string, mimeType: string) => void } & StatusDeps;
export type ExportTargetDeps = {
  parseEditorScene: () => JsonObject;
  compileBackend: (scene: JsonObject, target: "cesium" | "simdis" | "soap") => { files: Record<string, string> };
  createZipBlob: (files: Record<string, string>) => Blob;
  downloadBlob: (blob: Blob, filename: string) => void;
} & StatusDeps;
export type ExportAllTargetsDeps = {
  parseEditorScene: () => JsonObject;
  compileAllBackendsToFiles: (scene: JsonObject) => Record<string, string>;
  createZipBlob: (files: Record<string, string>) => Blob;
  downloadBlob: (blob: Blob, filename: string) => void;
} & StatusDeps;
export type LoadFileInputDeps = { elements: Pick<WorkbenchElements, "fileInput">; loadFile: (file: File) => Promise<void> };
export type LoadDroppedFileDeps = { loadFile: (file: File) => Promise<void> };
export type LoadFileDeps = { state: Pick<SceneWorkbenchState, "defaultCapabilities">; setEditorScene: (scene: JsonObject) => void; updatePanels: (scene: JsonObject) => void } & StatusDeps;
export type SaveIonTokenDeps = { elements: Pick<WorkbenchElements, "ionTokenInput"> } & StatusDeps;

export type StatusDeps = {
  setStatus: (message: string, kind: StatusKind) => void;
  errorMessage?: (error: unknown) => string;
};

export const EXAMPLE_SCENES = {
  minimal: "../examples/sdj_minimal_scene.json",
  full: "../examples/sdj_full_coverage_scene_v0_4.json"
};

export const EXPOSED_SCENE_MANIFEST = "../data/sdj_exposed_scenes_manifest.json";
