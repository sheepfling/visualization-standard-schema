import {
  asArray,
  asObject,
  compileAllBackendsToFiles,
  compileBackend,
  CESIUM_KIND_TARGETS,
  createZipBlob,
  findObject,
  flattenObjects,
  inspectObject,
  toJson,
  validateSemantics
} from "../../../sdj_core_v0_1/src/index.ts";
import {
  byId,
  downloadBlob,
  downloadText,
  getSdjLoader
} from "./helpers.ts";
import { installWorkbenchSmokeApi } from "./smoke.ts";
import {
  clearRenderedScene,
  exportAllTargets,
  exportNormalizedSdj,
  exportTarget,
  formatEditorJson,
  loadDefaultCapabilities,
  loadDroppedFile,
  loadExampleScene,
  loadExposedSceneCatalog,
  loadFile,
  loadFileInput,
  loadFeaturedExposedScene,
  loadInitialScene,
  loadSceneByPath,
  loadSelectedExposedScene,
  parseEditorScene,
  renderEditorScene,
  renderExposedSceneCatalog,
  saveIonToken,
  setEditorScene,
  syncCatalogSelection,
  updateSelectedCatalogSceneSummary,
  validateEditorScene
} from "./scene.ts";
import {
  countRenderableObjects as countRenderableObjectsViewer,
  focusCesiumObject,
  initializeViewer,
  zoomToSelectedObject
} from "./viewer.ts";
import {
  buildSelectedObjectReport,
  clearPanels,
  copySelectedObjectReport,
  downloadSelectedObjectReport,
  getClickedObjectId,
  renderDiagnostics,
  renderInspector,
  renderObjectTable,
  renderTotals,
  selectObject as selectObjectPanel,
  updatePanels
} from "./panels.ts";
import type { JsonObject, WorkbenchElements, WorkbenchState } from "../types/sdj";

type SceneLoadDeps = {
  state: WorkbenchState;
  elements: WorkbenchElements;
  setStatus: (message: string, kind: "ok" | "warning" | "error" | "neutral") => void;
};

type SelectObjectOptions = {
  focusCesium?: boolean;
};

function createState(): WorkbenchState {
  return {
    viewer: undefined,
    defaultCapabilities: undefined,
    exposedSceneCatalog: undefined,
    exposedSceneFeatured: undefined,
    exposedSceneDefaultPath: undefined,
    lastLoad: undefined,
    currentScene: undefined,
    currentPlan: undefined,
    selectedObjectId: undefined
  };
}

globalThis.SpatialDisplayJsonKindTargets = CESIUM_KIND_TARGETS;

function createElements(): WorkbenchElements {
  return {
    drawer: byId("drawer"),
    drawerToggle: byId("drawerToggle"),
    renderButton: byId("renderButton"),
    validateButton: byId("validateButton"),
    clearButton: byId("clearButton"),
    loadFeaturedSceneButton: byId("loadFeaturedSceneButton"),
    loadSelectedSceneButton: byId("loadSelectedSceneButton"),
    sceneCatalogFilter: byId("sceneCatalogFilter") as HTMLInputElement,
    sceneCatalogSelect: byId("sceneCatalogSelect") as HTMLSelectElement,
    sceneCatalogSummary: byId("sceneCatalogSummary"),
    loadMinimalButton: byId("loadMinimalButton"),
    loadFullButton: byId("loadFullButton"),
    exportSdjButton: byId("exportSdjButton"),
    exportCesiumButton: byId("exportCesiumButton"),
    exportSimdisButton: byId("exportSimdisButton"),
    exportSoapButton: byId("exportSoapButton"),
    exportAllButton: byId("exportAllButton"),
    formatButton: byId("formatButton"),
    fileInput: byId("fileInput") as HTMLInputElement,
    dropZone: byId("dropZone"),
    editor: byId("jsonEditor") as HTMLTextAreaElement,
    statusText: byId("statusText"),
    diagnosticsPanel: byId("diagnosticsPanel"),
    totalsPanel: byId("totalsPanel"),
    objectTableBody: byId("objectTableBody"),
    objectFilter: byId("objectFilter") as HTMLInputElement,
    inspectorPanel: byId("inspectorPanel"),
    copyInspectorButton: byId("copyInspectorButton"),
    downloadInspectorButton: byId("downloadInspectorButton"),
    zoomSelectedButton: byId("zoomSelectedButton"),
    selectedObject: byId("selectedObject"),
    ionTokenInput: byId("ionTokenInput") as HTMLInputElement,
    saveTokenButton: byId("saveTokenButton")
  };
}

function setStatus(elements: WorkbenchElements, message: string, kind: "ok" | "warning" | "error" | "neutral"): void {
  elements.statusText.textContent = message;
  elements.statusText.className = `status-pill ${kind}`;
}

function renderDiagnosticsPanel(elements: WorkbenchElements, plan: JsonObject): void {
  const deps: Parameters<typeof renderDiagnostics>[0] = { elements: { diagnosticsPanel: elements.diagnosticsPanel } };
  renderDiagnostics(deps, plan);
}

function renderTotalsPanel(elements: WorkbenchElements, plan: JsonObject): void {
  const deps: Parameters<typeof renderTotals>[0] = { elements: { totalsPanel: elements.totalsPanel } };
  renderTotals(deps, plan);
}

function renderObjectTablePanel(state: WorkbenchState, elements: WorkbenchElements, scene: JsonObject, plan: JsonObject): void {
  const deps: Parameters<typeof renderObjectTable>[0] = {
    state,
    elements: {
      objectTableBody: elements.objectTableBody,
      objectFilter: elements.objectFilter
    },
    flattenObjects,
    asArray,
    asObject
  };
  renderObjectTable(deps, scene, plan);
}

function renderInspectorPanel(state: WorkbenchState, elements: WorkbenchElements, scene: JsonObject, plan: JsonObject): void {
  const deps: Parameters<typeof renderInspector>[0] = {
    state,
    elements: { inspectorPanel: elements.inspectorPanel },
    inspectObject,
    asArray,
    asObject
  };
  renderInspector(deps, scene, plan);
}

function updateScenePanels(state: WorkbenchState, elements: WorkbenchElements, scene: JsonObject): void {
  const deps: Parameters<typeof updatePanels>[0] = {
    state,
    findSceneObject: findObject,
    renderDiagnostics: (plan: JsonObject) => renderDiagnosticsPanel(elements, plan),
    renderTotals: (plan: JsonObject) => renderTotalsPanel(elements, plan),
    renderObjectTable: (currentScene: JsonObject, plan: JsonObject) => renderObjectTablePanel(state, elements, currentScene, plan),
    renderInspector: (currentScene: JsonObject, plan: JsonObject) => renderInspectorPanel(state, elements, currentScene, plan)
  };
  updatePanels(deps, scene);
}

function clearScenePanels(state: WorkbenchState, elements: WorkbenchElements): void {
  const deps: Parameters<typeof clearPanels>[0] = {
    state,
    elements: {
      diagnosticsPanel: elements.diagnosticsPanel,
      totalsPanel: elements.totalsPanel,
      objectTableBody: elements.objectTableBody,
      inspectorPanel: elements.inspectorPanel
    }
  };
  clearPanels(deps);
}

function parseScene(elements: WorkbenchElements, state: WorkbenchState): JsonObject {
  return parseEditorScene({ elements, state });
}

function setScene(elements: WorkbenchElements, state: WorkbenchState, scene: JsonObject): void {
  const deps: Parameters<typeof setEditorScene>[0] = { elements, state, findSceneObject: findObject };
  setEditorScene(deps, scene);
}

function updatePanelsFromEditor(state: WorkbenchState, elements: WorkbenchElements): void {
  try {
    updateScenePanels(state, elements, parseScene(elements, state));
  } catch {
    clearScenePanels(state, elements);
  }
}

function selectObject(state: WorkbenchState, elements: WorkbenchElements, objectId: string, options: SelectObjectOptions = {}): void {
  const selectDeps: Parameters<typeof selectObjectPanel>[0] = { state, elements };
  selectObjectPanel(selectDeps, objectId);
  if (options.focusCesium) {
    const focusDeps: Parameters<typeof focusCesiumObject>[0] = { state, elements };
    focusCesiumObject(focusDeps, objectId);
  }
  if (state.currentScene && state.currentPlan) {
    renderObjectTablePanel(state, elements, state.currentScene, state.currentPlan as unknown as JsonObject);
    renderInspectorPanel(state, elements, state.currentScene, state.currentPlan as unknown as JsonObject);
  } else {
    updatePanelsFromEditor(state, elements);
  }
}

function createSelectedObjectReportDeps(state: WorkbenchState, elements: WorkbenchElements) {
  return {
    state,
    parseEditorScene: () => parseScene(elements, state),
    inspectObject
  };
}

function buildSelectedObjectReportForSelection(state: WorkbenchState, elements: WorkbenchElements): string {
  return buildSelectedObjectReport(createSelectedObjectReportDeps(state, elements));
}

function copySelectedObjectReportForSelection(state: WorkbenchState, elements: WorkbenchElements): void {
  copySelectedObjectReport({
    ...createSelectedObjectReportDeps(state, elements),
    buildSelectedObjectReport: () => buildSelectedObjectReportForSelection(state, elements)
  });
}

function downloadSelectedObjectReportForSelection(state: WorkbenchState, elements: WorkbenchElements): void {
  downloadSelectedObjectReport({
    ...createSelectedObjectReportDeps(state, elements),
    buildSelectedObjectReport: () => buildSelectedObjectReportForSelection(state, elements),
    downloadText,
    state
  });
}

function zoomSelectedObject(state: WorkbenchState, setStatusFn: (message: string, kind: "ok" | "warning" | "error" | "neutral") => void): void {
  void zoomToSelectedObject({ state, setStatus: setStatusFn });
}

function countRenderableObjects(scene: JsonObject): number {
  return countRenderableObjectsViewer(scene, (objects: unknown[]) => flattenObjects(objects as JsonObject[]), (value) => value !== false);
}

function loadSceneDeps(state: WorkbenchState, elements: WorkbenchElements, setStatusFn: SceneLoadDeps["setStatus"]): SceneLoadDeps {
  return { state, elements, setStatus: setStatusFn };
}

function bindUi(state: WorkbenchState, elements: WorkbenchElements): void {
  const setStatusFn = (message: string, kind: "ok" | "warning" | "error" | "neutral") => setStatus(elements, message, kind);

  elements.drawerToggle.addEventListener("click", () => {
    document.body.classList.toggle("drawer-collapsed");
  });
  elements.loadSelectedSceneButton.addEventListener("click", () => {
    const deps: Parameters<typeof loadSelectedExposedScene>[0] = {
      elements,
      loadSceneByPath: (relativePath: string) => loadSceneByPath({
        ...loadSceneDeps(state, elements, setStatusFn),
        setEditorScene: (scene: JsonObject) => setScene(elements, state, scene),
        updatePanels: (scene: JsonObject) => updateScenePanels(state, elements, scene),
        syncCatalogSelection: (path: string) => {
          syncCatalogSelection({ elements }, path);
          updateSelectedCatalogSceneSummary({ state, elements });
        }
      }, relativePath)
    };
    void loadSelectedExposedScene(deps);
  });
  elements.loadFeaturedSceneButton.addEventListener("click", () => {
    const deps: Parameters<typeof loadFeaturedExposedScene>[0] = {
      state,
      loadSceneByPath: (relativePath: string) => loadSceneByPath({
        ...loadSceneDeps(state, elements, setStatusFn),
        setEditorScene: (scene: JsonObject) => setScene(elements, state, scene),
        updatePanels: (scene: JsonObject) => updateScenePanels(state, elements, scene),
        syncCatalogSelection: (path: string) => syncCatalogSelection({ elements }, path)
      }, relativePath)
    };
    void loadFeaturedExposedScene(deps);
  });
  elements.sceneCatalogFilter.addEventListener("input", () => {
    const deps: Parameters<typeof renderExposedSceneCatalog>[0] = {
      state,
      elements,
      updateSelectedCatalogSceneSummary: () => updateSelectedCatalogSceneSummary({ state, elements })
    };
    renderExposedSceneCatalog(deps);
  });
  elements.sceneCatalogSelect.addEventListener("change", () => {
    updateSelectedCatalogSceneSummary({ state, elements });
  });
  elements.renderButton.addEventListener("click", () => {
    const deps: Parameters<typeof renderEditorScene>[0] = {
      parseEditorScene: () => parseScene(elements, state),
      validateSemantics,
      updatePanels: (scene: JsonObject) => updateScenePanels(state, elements, scene),
      clearRenderedScene: () => clearRenderedScene({ state, elements, setStatus: setStatusFn }),
      getSdjLoader,
      state,
      setStatus: setStatusFn,
      countRenderableObjects
    };
    void renderEditorScene(deps);
  });
  elements.validateButton.addEventListener("click", () => {
    const deps: Parameters<typeof validateEditorScene>[0] = {
      parseEditorScene: () => parseScene(elements, state),
      updatePanels: (scene: JsonObject) => updateScenePanels(state, elements, scene),
      setStatus: setStatusFn,
      clearPanels: () => clearScenePanels(state, elements),
      validateSemantics
    };
    validateEditorScene(deps);
  });
  elements.clearButton.addEventListener("click", () => {
    clearRenderedScene({ state, elements, setStatus: setStatusFn });
  });
  elements.loadMinimalButton.addEventListener("click", () => {
    const deps: Parameters<typeof loadExampleScene>[0] = {
      state,
      setEditorScene: (scene: JsonObject) => setScene(elements, state, scene),
      updatePanels: (scene: JsonObject) => updateScenePanels(state, elements, scene),
      setStatus: setStatusFn
    };
    void loadExampleScene(deps, "minimal");
  });
  elements.loadFullButton.addEventListener("click", () => {
    const deps: Parameters<typeof loadExampleScene>[0] = {
      state,
      setEditorScene: (scene: JsonObject) => setScene(elements, state, scene),
      updatePanels: (scene: JsonObject) => updateScenePanels(state, elements, scene),
      setStatus: setStatusFn
    };
    void loadExampleScene(deps, "full");
  });
  elements.exportSdjButton.addEventListener("click", () => {
    const deps: Parameters<typeof exportNormalizedSdj>[0] = {
      parseEditorScene: () => parseScene(elements, state),
      downloadText,
      setStatus: setStatusFn
    };
    exportNormalizedSdj(deps);
  });
  elements.exportCesiumButton.addEventListener("click", () => {
    const deps: Parameters<typeof exportTarget>[0] = {
      parseEditorScene: () => parseScene(elements, state),
      compileBackend,
      createZipBlob,
      downloadBlob,
      setStatus: setStatusFn
    };
    exportTarget(deps, "cesium");
  });
  elements.exportSimdisButton.addEventListener("click", () => {
    const deps: Parameters<typeof exportTarget>[0] = {
      parseEditorScene: () => parseScene(elements, state),
      compileBackend,
      createZipBlob,
      downloadBlob,
      setStatus: setStatusFn
    };
    exportTarget(deps, "simdis");
  });
  elements.exportSoapButton.addEventListener("click", () => {
    const deps: Parameters<typeof exportTarget>[0] = {
      parseEditorScene: () => parseScene(elements, state),
      compileBackend,
      createZipBlob,
      downloadBlob,
      setStatus: setStatusFn
    };
    exportTarget(deps, "soap");
  });
  elements.exportAllButton.addEventListener("click", () => {
    const deps: Parameters<typeof exportAllTargets>[0] = {
      parseEditorScene: () => parseScene(elements, state),
      compileAllBackendsToFiles,
      createZipBlob,
      downloadBlob,
      setStatus: setStatusFn
    };
    exportAllTargets(deps);
  });
  elements.formatButton.addEventListener("click", () => {
    const deps: Parameters<typeof formatEditorJson>[0] = {
      parseEditorScene: () => parseScene(elements, state),
      setEditorScene: (scene: JsonObject) => setScene(elements, state, scene),
      updatePanels: (scene: JsonObject) => updateScenePanels(state, elements, scene),
      setStatus: setStatusFn
    };
    formatEditorJson(deps);
  });
  elements.fileInput.addEventListener("change", () => {
    const deps: Parameters<typeof loadFileInput>[0] = {
      elements,
      loadFile: (file: File) => loadFile({
        state,
        setEditorScene: (scene: JsonObject) => setScene(elements, state, scene),
        updatePanels: (scene: JsonObject) => updateScenePanels(state, elements, scene),
        setStatus: setStatusFn
      }, file)
    };
    void loadFileInput(deps);
  });
  elements.objectFilter.addEventListener("input", () => {
    updatePanelsFromEditor(state, elements);
  });
  elements.objectTableBody.addEventListener("click", (event) => {
    const objectId = getClickedObjectId(event);
    if (objectId) {
      selectObject(state, elements, objectId, { focusCesium: true });
    }
  });
  elements.copyInspectorButton.addEventListener("click", () => {
    copySelectedObjectReportForSelection(state, elements);
  });
  elements.downloadInspectorButton.addEventListener("click", () => {
    downloadSelectedObjectReportForSelection(state, elements);
  });
  elements.zoomSelectedButton.addEventListener("click", () => {
    zoomSelectedObject(state, setStatusFn);
  });
  elements.saveTokenButton.addEventListener("click", () => {
    const deps: Parameters<typeof saveIonToken>[0] = {
      elements,
      setStatus: setStatusFn
    };
    saveIonToken(deps);
  });

  for (const eventName of ["dragenter", "dragover"]) {
    elements.dropZone.addEventListener(eventName, (event) => {
      event.preventDefault();
      elements.dropZone.classList.add("drag-over");
    });
  }
  for (const eventName of ["dragleave", "drop"]) {
    elements.dropZone.addEventListener(eventName, (event) => {
      event.preventDefault();
      elements.dropZone.classList.remove("drag-over");
    });
  }
  elements.dropZone.addEventListener("drop", (event) => {
    const deps: Parameters<typeof loadDroppedFile>[0] = {
      loadFile: (file: File) => loadFile({
        state,
        setEditorScene: (scene: JsonObject) => setScene(elements, state, scene),
        updatePanels: (scene: JsonObject) => updateScenePanels(state, elements, scene),
        setStatus: setStatusFn
      }, file)
    };
    void loadDroppedFile(deps, event);
  });
}

async function initializeScenes(state: WorkbenchState, elements: WorkbenchElements): Promise<void> {
  const setStatusFn = (message: string, kind: "ok" | "warning" | "error" | "neutral") => setStatus(elements, message, kind);
  await loadDefaultCapabilities({ state, setStatus: setStatusFn });
  await loadExposedSceneCatalog({
    state,
    elements,
    renderExposedSceneCatalog: () => renderExposedSceneCatalog({
      state,
      elements,
      updateSelectedCatalogSceneSummary: () => updateSelectedCatalogSceneSummary({ state, elements })
    }),
    updateSelectedCatalogSceneSummary: () => updateSelectedCatalogSceneSummary({ state, elements }),
    setStatus: setStatusFn
  });
  initializeViewer({
    state,
    elements,
    selectObject: (objectId: string, options?: SelectObjectOptions) => selectObject(state, elements, objectId, options)
  });
  bindUi(state, elements);
  await loadInitialScene({
    state,
    loadSceneByPath: (relativePath: string) => loadSceneByPath({
      state,
      setEditorScene: (scene: JsonObject) => setScene(elements, state, scene),
      updatePanels: (scene: JsonObject) => updateScenePanels(state, elements, scene),
      syncCatalogSelection: (path: string) => {
        syncCatalogSelection({ elements }, path);
        updateSelectedCatalogSceneSummary({ state, elements });
      },
      setStatus: setStatusFn
    }, relativePath),
    loadExampleScene: (key: "minimal" | "full") => loadExampleScene({
      state,
      setEditorScene: (scene: JsonObject) => setScene(elements, state, scene),
      updatePanels: (scene: JsonObject) => updateScenePanels(state, elements, scene),
      setStatus: setStatusFn
    }, key)
  });
  validateEditorScene({
    parseEditorScene: () => parseScene(elements, state),
    updatePanels: (scene: JsonObject) => updateScenePanels(state, elements, scene),
    setStatus: setStatusFn,
    clearPanels: () => clearScenePanels(state, elements),
    validateSemantics
  });
}

export async function initializeWorkbench(): Promise<void> {
  const state = createState();
  const elements = createElements();
  installWorkbenchSmokeApi({ state, elements });
  await initializeScenes(state, elements);
}
