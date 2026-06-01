import {
  asArray,
  asObject,
  buildCompilePlan,
  compileAllBackendsToFiles,
  compileBackend,
  createZipBlob,
  flattenObjects,
  inspectObject,
  normalizeSceneForWorkbench,
  toJson,
  validateSemantics
} from "./lib/index.js";
import {
  byId,
  downloadBlob,
  downloadText,
  errorMessage,
  escapeHtml,
  getCesium,
  getSdjLoader
} from "./workbench/helpers.js";

/**
 * @typedef {Record<string, unknown>} JsonObject
 */

const EXAMPLE_SCENES = {
  minimal: "../examples/sdj_minimal_scene.json",
  full: "../examples/sdj_full_coverage_scene_v0_4.json"
};

const EXPOSED_SCENE_MANIFEST = "../data/sdj_exposed_scenes_manifest.json";

/** @type {{viewer: any, defaultCapabilities?: JsonObject, exposedSceneCatalog?: JsonObject[], exposedSceneFeatured?: JsonObject[], exposedSceneDefaultPath?: string, lastLoad?: {entities?: Map<string, unknown>, primitives?: Map<string, unknown>, warnings?: string[]}, currentScene?: JsonObject, currentPlan?: JsonObject, selectedObjectId?: string}} */
const state = {
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

const elements = {
  drawer: byId("drawer"),
  drawerToggle: byId("drawerToggle"),
  renderButton: byId("renderButton"),
  validateButton: byId("validateButton"),
  clearButton: byId("clearButton"),
  loadFeaturedSceneButton: byId("loadFeaturedSceneButton"),
  loadSelectedSceneButton: byId("loadSelectedSceneButton"),
  sceneCatalogFilter: /** @type {HTMLInputElement} */ (byId("sceneCatalogFilter")),
  sceneCatalogSelect: /** @type {HTMLSelectElement} */ (byId("sceneCatalogSelect")),
  sceneCatalogSummary: byId("sceneCatalogSummary"),
  loadMinimalButton: byId("loadMinimalButton"),
  loadFullButton: byId("loadFullButton"),
  exportSdjButton: byId("exportSdjButton"),
  exportCesiumButton: byId("exportCesiumButton"),
  exportSimdisButton: byId("exportSimdisButton"),
  exportSoapButton: byId("exportSoapButton"),
  exportAllButton: byId("exportAllButton"),
  formatButton: byId("formatButton"),
  fileInput: /** @type {HTMLInputElement} */ (byId("fileInput")),
  dropZone: byId("dropZone"),
  editor: /** @type {HTMLTextAreaElement} */ (byId("jsonEditor")),
  statusText: byId("statusText"),
  diagnosticsPanel: byId("diagnosticsPanel"),
  totalsPanel: byId("totalsPanel"),
  objectTableBody: byId("objectTableBody"),
  objectFilter: /** @type {HTMLInputElement} */ (byId("objectFilter")),
  inspectorPanel: byId("inspectorPanel"),
  copyInspectorButton: byId("copyInspectorButton"),
  downloadInspectorButton: byId("downloadInspectorButton"),
  zoomSelectedButton: byId("zoomSelectedButton"),
  selectedObject: byId("selectedObject"),
  ionTokenInput: /** @type {HTMLInputElement} */ (byId("ionTokenInput")),
  saveTokenButton: byId("saveTokenButton")
};

await initialize();

/**
 * Initializes the Cesium viewer, UI event handlers, and default scene.
 *
 * @returns {Promise<void>}
 */
async function initialize() {
  await loadDefaultCapabilities();
  await loadExposedSceneCatalog();
  initializeViewer();
  bindUi();
  await loadInitialScene();
  validateEditorScene();
}

/**
 * Loads default backend capability metadata used when a scene omits it.
 *
 * @returns {Promise<void>}
 */
async function loadDefaultCapabilities() {
  try {
    const response = await fetch(new URL("../data/sdj_backend_capabilities_v0_4.json", import.meta.url));
    state.defaultCapabilities = await response.json();
  } catch (error) {
    state.defaultCapabilities = {};
    setStatus(`Capability metadata could not be loaded: ${errorMessage(error)}`, "warning");
  }
}

/**
 * Creates the Cesium viewer.
 *
 * @returns {void}
 */
function initializeViewer() {
  const Cesium = getCesium();
  const storedToken = localStorage.getItem("sdj.cesiumIonToken") || "";
  elements.ionTokenInput.value = storedToken;
  if (storedToken) {
    Cesium.Ion.defaultAccessToken = storedToken;
  }

  /** @type {JsonObject} */
  const viewerOptions = {
    animation: true,
    timeline: true,
    shouldAnimate: true,
    baseLayerPicker: true,
    sceneModePicker: true,
    infoBox: true,
    selectionIndicator: true,
    geocoder: false
  };

  state.viewer = new Cesium.Viewer("cesiumContainer", viewerOptions);
  state.viewer.scene.globe.depthTestAgainstTerrain = false;
  state.viewer.scene.debugShowFramesPerSecond = false;

  const handler = new Cesium.ScreenSpaceEventHandler(state.viewer.scene.canvas);
  handler.setInputAction((movement) => {
    const picked = state.viewer.scene.pick(movement.position);
    if (Cesium.defined(picked)) {
      const objectId = objectIdFromPicked(picked);
      if (objectId) {
        selectObject(objectId, { focusCesium: false });
      } else {
        elements.selectedObject.textContent = describePickedObject(picked);
      }
    } else {
      elements.selectedObject.textContent = "No object selected";
    }
  }, Cesium.ScreenSpaceEventType.LEFT_CLICK);
}

/**
 * Connects UI event handlers.
 *
 * @returns {void}
 */
function bindUi() {
  elements.drawerToggle.addEventListener("click", () => {
    document.body.classList.toggle("drawer-collapsed");
  });
  elements.loadSelectedSceneButton.addEventListener("click", () => {
    void loadSelectedExposedScene();
  });
  elements.loadFeaturedSceneButton.addEventListener("click", () => {
    void loadFeaturedExposedScene();
  });
  elements.sceneCatalogFilter.addEventListener("input", () => {
    renderExposedSceneCatalog();
  });
  elements.sceneCatalogSelect.addEventListener("change", () => {
    updateSelectedCatalogSceneSummary();
  });
  elements.renderButton.addEventListener("click", () => {
    void renderEditorScene();
  });
  elements.validateButton.addEventListener("click", () => {
    validateEditorScene();
  });
  elements.clearButton.addEventListener("click", () => {
    clearRenderedScene();
  });
  elements.loadMinimalButton.addEventListener("click", () => {
    void loadExampleScene("minimal");
  });
  elements.loadFullButton.addEventListener("click", () => {
    void loadExampleScene("full");
  });
  elements.exportSdjButton.addEventListener("click", () => {
    exportNormalizedSdj();
  });
  elements.exportCesiumButton.addEventListener("click", () => {
    exportTarget("cesium");
  });
  elements.exportSimdisButton.addEventListener("click", () => {
    exportTarget("simdis");
  });
  elements.exportSoapButton.addEventListener("click", () => {
    exportTarget("soap");
  });
  elements.exportAllButton.addEventListener("click", () => {
    exportAllTargets();
  });
  elements.formatButton.addEventListener("click", () => {
    formatEditorJson();
  });
  elements.fileInput.addEventListener("change", () => {
    void loadFileInput();
  });
  elements.objectFilter.addEventListener("input", () => {
    updatePanelsFromEditor();
  });
  elements.objectTableBody.addEventListener("click", (event) => {
    handleObjectTableClick(event);
  });
  elements.copyInspectorButton.addEventListener("click", () => {
    void copySelectedObjectReport();
  });
  elements.downloadInspectorButton.addEventListener("click", () => {
    downloadSelectedObjectReport();
  });
  elements.zoomSelectedButton.addEventListener("click", () => {
    void zoomToSelectedObject();
  });
  elements.saveTokenButton.addEventListener("click", () => {
    saveIonToken();
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
    void loadDroppedFile(event);
  });
}

/**
 * Loads a built-in example scene into the editor.
 *
 * @param {"minimal" | "full"} key
 * @returns {Promise<void>}
 */
async function loadExampleScene(key) {
  try {
    const response = await fetch(new URL(EXAMPLE_SCENES[key], import.meta.url));
    const scene = await response.json();
    const normalized = normalizeSceneForWorkbench(scene, state.defaultCapabilities);
    setEditorScene(normalized);
    updatePanels(normalized);
    setStatus(`Loaded ${key} example scene.`, "ok");
  } catch (error) {
    setStatus(`Failed to load ${key} example: ${errorMessage(error)}`, "error");
  }
}

/**
 * Loads the manifest of exposed SDJ scenes that should be available to default users.
 *
 * @returns {Promise<void>}
 */
async function loadExposedSceneCatalog() {
  try {
    const response = await fetch(new URL(EXPOSED_SCENE_MANIFEST, import.meta.url));
    const manifest = await response.json();
    state.exposedSceneCatalog = Array.isArray(manifest.scenes) ? manifest.scenes : [];
    state.exposedSceneFeatured = Array.isArray(manifest.featured) ? manifest.featured : [];
    state.exposedSceneDefaultPath = String(manifest.defaultPath || state.exposedSceneFeatured?.[0]?.path || "");
    renderExposedSceneCatalog();
    updateSelectedCatalogSceneSummary();
  } catch (error) {
    state.exposedSceneCatalog = [];
    state.exposedSceneFeatured = [];
    state.exposedSceneDefaultPath = undefined;
    elements.sceneCatalogSummary.textContent = "Exposed SDJ scenes could not be loaded; falling back to the built-in examples.";
    setStatus(`Exposed SDJ catalog could not be loaded: ${errorMessage(error)}`, "warning");
  }
}

/**
 * Loads the most representative exposed SDJ scene on startup.
 *
 * @returns {Promise<void>}
 */
async function loadInitialScene() {
  if (state.exposedSceneDefaultPath) {
    const loaded = await loadSceneByPath(state.exposedSceneDefaultPath);
    if (loaded) {
      return;
    }
  }
  await loadExampleScene("minimal");
}

/**
 * Loads the scene selected in the exposed-scene picker.
 *
 * @returns {Promise<void>}
 */
async function loadSelectedExposedScene() {
  const selectedPath = elements.sceneCatalogSelect.value;
  if (!selectedPath) {
    return;
  }
  await loadSceneByPath(selectedPath);
}

/**
 * Loads the featured exposed scene.
 *
 * @returns {Promise<void>}
 */
async function loadFeaturedExposedScene() {
  const featured = state.exposedSceneFeatured || [];
  const defaultPath = String(featured[0]?.path || state.exposedSceneDefaultPath || "");
  if (!defaultPath) {
    return;
  }
  await loadSceneByPath(defaultPath);
}

/**
 * Loads a scene by a path relative to this module.
 *
 * @param {string} relativePath
 * @returns {Promise<void>}
 */
async function loadSceneByPath(relativePath) {
  try {
    const response = await fetch(new URL(relativePath, import.meta.url));
    const scene = await response.json();
    const normalized = normalizeSceneForWorkbench(scene, state.defaultCapabilities);
    setEditorScene(normalized);
    updatePanels(normalized);
    syncCatalogSelection(relativePath);
    const loadedName = String(normalized.document?.name || normalized.document?.id || relativePath);
    setStatus(`Loaded exposed scene: ${loadedName}.`, "ok");
    return true;
  } catch (error) {
    setStatus(`Failed to load scene ${relativePath}: ${errorMessage(error)}`, "error");
    return false;
  }
}

/**
 * Renders the exposed-scene picker.
 *
 * @returns {void}
 */
function renderExposedSceneCatalog() {
  const catalog = Array.isArray(state.exposedSceneCatalog) ? state.exposedSceneCatalog : [];
  const filter = elements.sceneCatalogFilter.value.trim().toLowerCase();
  const featuredPaths = new Set((state.exposedSceneFeatured || []).map((item) => String(asObject(item).path || "")));
  const scenes = catalog.filter((scene) => {
    if (!filter) {
      return true;
    }
    const haystack = `${String(scene.name || "")} ${String(scene.id || "")} ${String(scene.group || "")} ${String(scene.source || "")} ${String(scene.objectCount || "")}`.toLowerCase();
    return haystack.includes(filter);
  });
  const featured = scenes.filter((scene) => featuredPaths.has(String(scene.path || "")));
  const remaining = scenes.filter((scene) => !featuredPaths.has(String(scene.path || "")));
  const optionHtml = (items, label) => {
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
  elements.sceneCatalogSelect.innerHTML = [
    optionHtml(featured, "Featured exposed scenes"),
    optionHtml(remaining, "All exposed scenes")
  ].join("") || `<option value="" disabled selected>No exposed scenes available</option>`;

  if (!elements.sceneCatalogSelect.value) {
    const initialPath = state.exposedSceneDefaultPath || String(featured[0]?.path || remaining[0]?.path || "");
    if (initialPath) {
      elements.sceneCatalogSelect.value = initialPath;
    }
  }

  updateSelectedCatalogSceneSummary();
}

/**
 * Keeps the catalog summary aligned with the selected exposed scene.
 *
 * @returns {void}
 */
function updateSelectedCatalogSceneSummary() {
  const catalog = Array.isArray(state.exposedSceneCatalog) ? state.exposedSceneCatalog : [];
  const selectedPath = elements.sceneCatalogSelect.value;
  if (!selectedPath) {
    elements.sceneCatalogSummary.textContent = `${catalog.length} exposed SDJ scenes available from the imported corpus.`;
    return;
  }
  const selected = catalog.find((scene) => String(scene.path || "") === selectedPath);
  if (!selected) {
    elements.sceneCatalogSummary.textContent = `${catalog.length} exposed SDJ scenes available from the imported corpus.`;
    return;
  }
  elements.sceneCatalogSummary.textContent = `${catalog.length} exposed SDJ scenes available. Selected: ${String(selected.name || selected.path)} · ${Number(selected.objectCount || 0)} object(s) · ${String(selected.group || "")}`;
}

/**
 * Keeps the picker selection in sync after the user loads a scene.
 *
 * @param {string} relativePath
 * @returns {void}
 */
function syncCatalogSelection(relativePath) {
  if (elements.sceneCatalogSelect.value === relativePath) {
    return;
  }
  elements.sceneCatalogSelect.value = relativePath;
  updateSelectedCatalogSceneSummary();
}

/**
 * Parses and normalizes the editor JSON.
 *
 * @returns {JsonObject}
 */
function parseEditorScene() {
  const parsed = JSON.parse(elements.editor.value);
  return normalizeSceneForWorkbench(parsed, state.defaultCapabilities);
}

/**
 * Sets the editor text from a scene object.
 *
 * @param {JsonObject} scene
 * @returns {void}
 */
function setEditorScene(scene) {
  elements.editor.value = toJson(scene);
  state.currentScene = scene;
  if (state.selectedObjectId && !findSceneObject(scene, state.selectedObjectId)) {
    state.selectedObjectId = undefined;
  }
}

/**
 * Validates the scene currently in the editor.
 *
 * @returns {void}
 */
function validateEditorScene() {
  try {
    const scene = parseEditorScene();
    const semantic = validateSemantics(scene);
    updatePanels(scene);
    if (semantic.errors.length > 0) {
      setStatus(`Validation failed with ${semantic.errors.length} error(s).`, "error");
      return;
    }
    setStatus(`Validation passed with ${semantic.warnings.length} warning(s).`, semantic.warnings.length > 0 ? "warning" : "ok");
  } catch (error) {
    setStatus(`Invalid JSON: ${errorMessage(error)}`, "error");
    clearPanels();
  }
}

/**
 * Parses and renders the editor scene into Cesium.
 *
 * @returns {Promise<void>}
 */
async function renderEditorScene() {
  try {
    const scene = parseEditorScene();
    const semantic = validateSemantics(scene);
    updatePanels(scene);
    if (semantic.errors.length > 0) {
      setStatus(`Not rendering; scene has ${semantic.errors.length} semantic error(s).`, "error");
      return;
    }
    clearRenderedScene();
    const loader = getSdjLoader();
    state.lastLoad = await loader.loadSpatialDisplayScene(state.viewer, scene, { zoomToFirstView: true });
    state.currentScene = scene;
    const warningCount = (state.lastLoad.warnings || []).length + semantic.warnings.length;
    setStatus(`Rendered ${countRenderableObjects(scene)} object(s) into Cesium. Warnings: ${warningCount}.`, warningCount > 0 ? "warning" : "ok");
  } catch (error) {
    setStatus(`Render failed: ${errorMessage(error)}`, "error");
  }
}

/**
 * Removes the most recent SDJ render pass from Cesium.
 *
 * @returns {void}
 */
function clearRenderedScene() {
  if (!state.viewer || !state.lastLoad) {
    return;
  }
  if (state.lastLoad.entities) {
    for (const entity of state.lastLoad.entities.values()) {
      state.viewer.entities.remove(entity);
    }
  }
  if (state.lastLoad.primitives) {
    for (const primitive of state.lastLoad.primitives.values()) {
      try {
        state.viewer.scene.primitives.remove(primitive);
      } catch (error) {
        console.warn("Unable to remove primitive", primitive, error);
      }
    }
  }
  state.lastLoad = undefined;
  elements.selectedObject.textContent = "No object selected";
  setStatus("Cleared rendered SDJ objects.", "neutral");
}

/**
 * Formats editor JSON.
 *
 * @returns {void}
 */
function formatEditorJson() {
  try {
    const scene = parseEditorScene();
    setEditorScene(scene);
    updatePanels(scene);
    setStatus("Formatted and normalized editor JSON.", "ok");
  } catch (error) {
    setStatus(`Cannot format invalid JSON: ${errorMessage(error)}`, "error");
  }
}

/**
 * Downloads normalized SDJ JSON.
 *
 * @returns {void}
 */
function exportNormalizedSdj() {
  try {
    const scene = parseEditorScene();
    downloadText("scene.sdj.json", toJson(scene), "application/json");
    setStatus("Exported normalized SDJ JSON.", "ok");
  } catch (error) {
    setStatus(`SDJ export failed: ${errorMessage(error)}`, "error");
  }
}

/**
 * Exports a single backend bundle as a ZIP.
 *
 * @param {"cesium" | "simdis" | "soap"} target
 * @returns {void}
 */
function exportTarget(target) {
  try {
    const scene = parseEditorScene();
    const bundle = compileBackend(scene, target);
    const blob = createZipBlob(bundle.files);
    downloadBlob(blob, `sdj-${target}-export.zip`);
    setStatus(`Exported ${target.toUpperCase()} bundle with ${Object.keys(bundle.files).length} file(s).`, "ok");
  } catch (error) {
    setStatus(`${target.toUpperCase()} export failed: ${errorMessage(error)}`, "error");
  }
}

/**
 * Exports all backend bundles as one ZIP.
 *
 * @returns {void}
 */
function exportAllTargets() {
  try {
    const scene = parseEditorScene();
    const files = compileAllBackendsToFiles(scene);
    const blob = createZipBlob(files);
    downloadBlob(blob, "sdj-all-backends-export.zip");
    setStatus(`Exported all backend bundles with ${Object.keys(files).length} file(s).`, "ok");
  } catch (error) {
    setStatus(`All-target export failed: ${errorMessage(error)}`, "error");
  }
}

/**
 * Loads a scene from the file input control.
 *
 * @returns {Promise<void>}
 */
async function loadFileInput() {
  const file = elements.fileInput.files ? elements.fileInput.files[0] : undefined;
  if (!file) {
    return;
  }
  await loadFile(file);
  elements.fileInput.value = "";
}

/**
 * Loads a dropped scene file.
 *
 * @param {DragEvent} event
 * @returns {Promise<void>}
 */
async function loadDroppedFile(event) {
  const file = event.dataTransfer && event.dataTransfer.files.length > 0 ? event.dataTransfer.files[0] : undefined;
  if (!file) {
    return;
  }
  await loadFile(file);
}

/**
 * Loads a JSON file into the editor.
 *
 * @param {File} file
 * @returns {Promise<void>}
 */
async function loadFile(file) {
  try {
    const text = await file.text();
    const parsed = JSON.parse(text);
    const normalized = normalizeSceneForWorkbench(parsed, state.defaultCapabilities);
    setEditorScene(normalized);
    updatePanels(normalized);
    setStatus(`Loaded ${file.name}.`, "ok");
  } catch (error) {
    setStatus(`Could not load ${file.name}: ${errorMessage(error)}`, "error");
  }
}

/**
 * Saves the current Cesium ion token to local storage.
 *
 * @returns {void}
 */
function saveIonToken() {
  const token = elements.ionTokenInput.value.trim();
  const Cesium = getCesium();
  if (token) {
    localStorage.setItem("sdj.cesiumIonToken", token);
    Cesium.Ion.defaultAccessToken = token;
    setStatus("Saved Cesium ion token for this browser.", "ok");
  } else {
    localStorage.removeItem("sdj.cesiumIonToken");
    setStatus("Cleared Cesium ion token from this browser.", "neutral");
  }
}

/**
 * Updates panels from the editor, swallowing parse failures.
 *
 * @returns {void}
 */
function updatePanelsFromEditor() {
  try {
    updatePanels(parseEditorScene());
  } catch (_error) {
    clearPanels();
  }
}

/**
 * Updates diagnostics and support panels for a scene.
 *
 * @param {JsonObject} scene
 * @returns {void}
 */
function updatePanels(scene) {
  const plan = buildCompilePlan(scene);
  state.currentScene = scene;
  state.currentPlan = plan;
  if (state.selectedObjectId && !findSceneObject(scene, state.selectedObjectId)) {
    state.selectedObjectId = undefined;
  }
  renderDiagnostics(plan);
  renderTotals(plan);
  renderObjectTable(scene, plan);
  renderInspector(scene, plan);
}

/**
 * Clears diagnostics panels.
 *
 * @returns {void}
 */
function clearPanels() {
  elements.diagnosticsPanel.innerHTML = "";
  elements.totalsPanel.innerHTML = "";
  elements.objectTableBody.innerHTML = "";
  elements.inspectorPanel.innerHTML = `<div class="empty-state">Select an object from the table or click a rendered Cesium object.</div>`;
  state.currentPlan = undefined;
}

/**
 * Renders semantic diagnostics.
 *
 * @param {JsonObject} plan
 * @returns {void}
 */
function renderDiagnostics(plan) {
  const semantic = /** @type {{errors?: unknown[], warnings?: unknown[]}} */ (plan.semantic || {});
  const errors = Array.isArray(semantic.errors) ? semantic.errors : [];
  const warnings = Array.isArray(semantic.warnings) ? semantic.warnings : [];
  const items = [...errors, ...warnings].slice(0, 60);
  if (items.length === 0) {
    elements.diagnosticsPanel.innerHTML = `<div class="empty-state">No semantic diagnostics.</div>`;
    return;
  }
  elements.diagnosticsPanel.innerHTML = items.map((item) => {
    const diagnostic = /** @type {JsonObject} */ (item);
    const severity = String(diagnostic.severity || "warning");
    return `<div class="diagnostic ${escapeHtml(severity)}"><strong>${escapeHtml(String(diagnostic.code || severity))}</strong><span>${escapeHtml(String(diagnostic.message || ""))}</span><small>${escapeHtml(String(diagnostic.path || ""))}</small></div>`;
  }).join("");
}

/**
 * Renders backend compile totals.
 *
 * @param {JsonObject} plan
 * @returns {void}
 */
function renderTotals(plan) {
  const targetTotals = /** @type {JsonObject} */ (plan.targetTotals || {});
  const html = ["cesium", "simdis", "soap"].map((target) => {
    const totals = /** @type {JsonObject} */ (targetTotals[target] || {});
    return `<article class="target-card"><h3>${target.toUpperCase()}</h3><dl><div><dt>Strong</dt><dd>${Number(totals.strong || 0)}</dd></div><div><dt>Partial</dt><dd>${Number(totals.partial || 0)}</dd></div><div><dt>Reserved</dt><dd>${Number(totals.reserved || 0)}</dd></div><div><dt>Unsupported</dt><dd>${Number(totals.unsupported || 0)}</dd></div><div><dt>Hidden</dt><dd>${Number(totals.hidden || 0)}</dd></div></dl></article>`;
  }).join("");
  elements.totalsPanel.innerHTML = html;
}

/**
 * Renders the object coverage table.
 *
 * @param {JsonObject} scene
 * @param {JsonObject} plan
 * @returns {void}
 */
function renderObjectTable(scene, plan) {
  const filter = elements.objectFilter.value.trim().toLowerCase();
  const objects = flattenObjects(asArray(scene.objects).map(asObject));
  const plans = new Map(asArray(plan.objects).map((item) => {
    const objectPlan = /** @type {JsonObject} */ (item);
    return [String(objectPlan.id), objectPlan];
  }));
  const rows = objects.filter((object) => {
    if (!filter) {
      return true;
    }
    return `${object.id || ""} ${object.kind || ""} ${object.name || ""}`.toLowerCase().includes(filter);
  }).slice(0, 250).map((object) => {
    const objectId = String(object.id || "");
    const objectPlan = /** @type {JsonObject} */ (plans.get(objectId) || {});
    const targetBadges = asArray(objectPlan.targets).map((targetPlan) => {
      const target = /** @type {JsonObject} */ (targetPlan);
      const support = String(target.support || "unknown");
      const title = `${String(target.targetNative || "")} / ${String(target.lossiness || "unknown")} lossiness`;
      return `<span class="support-badge ${escapeHtml(support)}" title="${escapeHtml(title)}">${escapeHtml(String(target.target || "?"))}: ${escapeHtml(support)}</span>`;
    }).join(" ");
    const selected = state.selectedObjectId === objectId ? " selected" : "";
    const shown = object.show === false ? " hidden-object" : "";
    return `<tr class="object-row${selected}${shown}" data-object-id="${escapeHtml(objectId)}"><td>${escapeHtml(objectId)}</td><td>${escapeHtml(String(object.kind || ""))}</td><td>${escapeHtml(String(object.name || ""))}</td><td>${targetBadges}</td></tr>`;
  }).join("");
  elements.objectTableBody.innerHTML = rows || `<tr><td colspan="4" class="empty-state">No matching objects.</td></tr>`;
}

/**
 * Handles row clicks in the object coverage table.
 *
 * @param {Event} event
 * @returns {void}
 */
function handleObjectTableClick(event) {
  const target = /** @type {Element | null} */ (event.target instanceof Element ? event.target : null);
  const row = target ? target.closest("tr[data-object-id]") : null;
  if (!row) {
    return;
  }
  const objectId = row.getAttribute("data-object-id");
  if (!objectId) {
    return;
  }
  selectObject(objectId, { focusCesium: true });
}

/**
 * Updates the current object selection and inspector.
 *
 * @param {string} objectId
 * @param {{focusCesium?: boolean}} options
 * @returns {void}
 */
function selectObject(objectId, options = {}) {
  state.selectedObjectId = objectId;
  elements.selectedObject.textContent = `Selected SDJ object: ${objectId}`;
  if (options.focusCesium) {
    focusCesiumObject(objectId);
  }
  if (state.currentScene && state.currentPlan) {
    renderObjectTable(state.currentScene, state.currentPlan);
    renderInspector(state.currentScene, state.currentPlan);
  } else {
    updatePanelsFromEditor();
  }
}

/**
 * Renders the backend inspector for the selected object.
 *
 * @param {JsonObject} scene
 * @param {JsonObject} plan
 * @returns {void}
 */
function renderInspector(scene, plan) {
  if (!state.selectedObjectId) {
    elements.inspectorPanel.innerHTML = `<div class="empty-state">Select an object from the table or click a rendered Cesium object.</div>`;
    return;
  }
  const inspection = inspectObject(scene, state.selectedObjectId, plan);
  if (!inspection) {
    elements.inspectorPanel.innerHTML = `<div class="empty-state">Selected object '${escapeHtml(state.selectedObjectId)}' is not present in the current editor scene.</div>`;
    return;
  }

  const object = asObject(inspection.object);
  const targets = asArray(inspection.targets).map(asObject);
  const semanticDiagnostics = asArray(inspection.semanticDiagnostics).map(asObject);
  const targetHtml = targets.map((target) => renderTargetInspectorCard(target)).join("");
  const semanticHtml = renderDiagnosticList(semanticDiagnostics, "No object-specific semantic diagnostics.");
  const rendererHints = asObject(inspection.rendererHints);
  const hintsHtml = Object.keys(rendererHints).length > 0
    ? `<details><summary>Renderer hints</summary><pre>${escapeHtml(toJson(rendererHints))}</pre></details>`
    : `<p class="inspector-muted">No rendererHints block on this object.</p>`;

  elements.inspectorPanel.innerHTML = `
    <article class="inspector-object-card">
      <div class="inspector-heading">
        <div>
          <strong>${escapeHtml(String(inspection.id || ""))}</strong>
          <span>${escapeHtml(String(inspection.kind || "unknown"))}${inspection.name ? ` · ${escapeHtml(String(inspection.name))}` : ""}</span>
        </div>
        <span class="support-badge ${inspection.visible ? "strong" : "reserved"}">${inspection.visible ? "visible" : "hidden"}</span>
      </div>
      <dl class="inspector-meta">
        <div><dt>SDJ path</dt><dd>${escapeHtml(String(inspection.path || ""))}</dd></div>
        <div><dt>Layer</dt><dd>${escapeHtml(String(object.layer || "—"))}</dd></div>
      </dl>
      <div class="inspector-targets">${targetHtml}</div>
      <section class="inspector-subsection">
        <h3>Object diagnostics</h3>
        ${semanticHtml}
      </section>
      <section class="inspector-subsection">
        <h3>Renderer hints</h3>
        ${hintsHtml}
      </section>
      <section class="inspector-subsection">
        <h3>Source object JSON</h3>
        <details open><summary>Normalized object payload</summary><pre>${escapeHtml(toJson(object))}</pre></details>
      </section>
    </article>`;
}

/**
 * Renders one target mapping card.
 *
 * @param {JsonObject} target
 * @returns {string}
 */
function renderTargetInspectorCard(target) {
  const support = String(target.support || "unknown");
  const diagnostics = asArray(target.diagnostics).map(asObject);
  const artifactPaths = asArray(target.artifactPaths).map(String);
  const fileList = artifactPaths.length > 0
    ? artifactPaths.map((path) => `<li>${escapeHtml(path)}</li>`).join("")
    : `<li>${escapeHtml(String(target.artifactPath || target.artifact || "diagnostics"))}</li>`;
  return `
    <article class="inspector-target-card ${escapeHtml(support)}">
      <header>
        <strong>${escapeHtml(String(target.target || "unknown").toUpperCase())}</strong>
        <span class="support-badge ${escapeHtml(support)}">${escapeHtml(support)}</span>
      </header>
      <dl>
        <div><dt>Native target</dt><dd>${escapeHtml(String(target.targetNative || "—"))}</dd></div>
        <div><dt>Lossiness</dt><dd>${escapeHtml(String(target.lossiness || "unknown"))}</dd></div>
        <div><dt>Object artifact</dt><dd>${escapeHtml(String(target.artifactPath || target.artifact || "diagnostics"))}</dd></div>
      </dl>
      <p>${escapeHtml(String(target.action || "No action guidance."))}</p>
      <details>
        <summary>Generated files</summary>
        <ul>${fileList}</ul>
      </details>
      ${renderDiagnosticList(diagnostics, "No target-specific diagnostics.")}
    </article>`;
}

/**
 * Renders diagnostics in a compact form.
 *
 * @param {JsonObject[]} diagnostics
 * @param {string} emptyMessage
 * @returns {string}
 */
function renderDiagnosticList(diagnostics, emptyMessage) {
  if (diagnostics.length === 0) {
    return `<div class="empty-state compact">${escapeHtml(emptyMessage)}</div>`;
  }
  return `<div class="inspector-diagnostics">${diagnostics.map((diagnostic) => {
    const severity = String(diagnostic.severity || "warning");
    return `<div class="diagnostic ${escapeHtml(severity)}"><strong>${escapeHtml(String(diagnostic.code || severity))}</strong><span>${escapeHtml(String(diagnostic.message || ""))}</span><small>${escapeHtml(String(diagnostic.path || ""))}</small></div>`;
  }).join("")}</div>`;
}

/**
 * Builds the selected object mapping payload for copy/download actions.
 *
 * @returns {JsonObject}
 */
function buildSelectedObjectReport() {
  if (!state.selectedObjectId) {
    throw new Error("No object selected.");
  }
  const scene = parseEditorScene();
  const plan = buildCompilePlan(scene);
  const report = inspectObject(scene, state.selectedObjectId, plan);
  if (!report) {
    throw new Error(`Selected object '${state.selectedObjectId}' is not in the current scene.`);
  }
  return report;
}

/**
 * Copies the selected object mapping report to the clipboard.
 *
 * @returns {Promise<void>}
 */
async function copySelectedObjectReport() {
  try {
    const report = buildSelectedObjectReport();
    await navigator.clipboard.writeText(toJson(report));
    setStatus(`Copied mapping report for ${state.selectedObjectId}.`, "ok");
  } catch (error) {
    setStatus(`Copy failed: ${errorMessage(error)}`, "error");
  }
}

/**
 * Downloads the selected object mapping report.
 *
 * @returns {void}
 */
function downloadSelectedObjectReport() {
  try {
    const report = buildSelectedObjectReport();
    downloadText(`sdj-object-mapping-${state.selectedObjectId || "object"}.json`, toJson(report), "application/json");
    setStatus(`Downloaded mapping report for ${state.selectedObjectId}.`, "ok");
  } catch (error) {
    setStatus(`Report download failed: ${errorMessage(error)}`, "error");
  }
}

/**
 * Zooms to the selected rendered object when possible.
 *
 * @returns {Promise<void>}
 */
async function zoomToSelectedObject() {
  if (!state.selectedObjectId) {
    setStatus("No object selected.", "warning");
    return;
  }
  if (!state.viewer || !state.lastLoad) {
    setStatus("Render the scene before zooming to a selected object.", "warning");
    return;
  }

  const entity = state.lastLoad.entities && state.lastLoad.entities.get(state.selectedObjectId);
  if (entity) {
    await state.viewer.zoomTo(entity);
    state.viewer.selectedEntity = entity;
    setStatus(`Zoomed to ${state.selectedObjectId}.`, "ok");
    return;
  }

  const primitive = state.lastLoad.primitives && state.lastLoad.primitives.get(state.selectedObjectId);
  if (primitive) {
    try {
      await state.viewer.zoomTo(primitive);
      setStatus(`Zoomed to primitive ${state.selectedObjectId}.`, "ok");
    } catch (_error) {
      setStatus(`Selected primitive ${state.selectedObjectId}; Cesium cannot always auto-zoom primitive-only objects.`, "warning");
    }
    return;
  }

  setStatus(`Selected object '${state.selectedObjectId}' is not in the current Cesium load result.`, "warning");
}

/**
 * Counts objects that are not explicitly hidden.
 *
 * @param {JsonObject} scene
 * @returns {number}
 */
function countRenderableObjects(scene) {
  return flattenObjects(asArray(scene.objects).map(asObject)).filter((object) => object.show !== false).length;
}

/**
 * Updates the status pill.
 *
 * @param {string} message
 * @param {"ok" | "warning" | "error" | "neutral"} kind
 * @returns {void}
 */
function setStatus(message, kind) {
  elements.statusText.textContent = message;
  elements.statusText.className = `status-pill ${kind}`;
}

function findSceneObject(scene, objectId) {
  return flattenObjects(asArray(scene.objects).map(asObject)).find((object) => String(object.id || "") === objectId);
}

/**
 * Attempts to select the corresponding rendered Cesium object.
 *
 * @param {string} objectId
 * @returns {void}
 */
function focusCesiumObject(objectId) {
  if (!state.viewer || !state.lastLoad) {
    return;
  }
  const entity = state.lastLoad.entities && state.lastLoad.entities.get(objectId);
  if (entity) {
    state.viewer.selectedEntity = entity;
    return;
  }
  const primitive = state.lastLoad.primitives && state.lastLoad.primitives.get(objectId);
  if (primitive) {
    elements.selectedObject.textContent = `Selected SDJ primitive: ${objectId}`;
  }
}

/**
 * Extracts an SDJ object id from a Cesium pick result when possible.
 *
 * @param {unknown} picked
 * @returns {string | undefined}
 */
function objectIdFromPicked(picked) {
  const object = /** @type {any} */ (picked);
  if (object.id && typeof object.id.id === "string") {
    return object.id.id;
  }
  if (object.primitive && typeof object.primitive.id === "string") {
    return object.primitive.id;
  }
  if (object.id && typeof object.id === "string") {
    return object.id;
  }
  return undefined;
}

/**
 * Produces a useful label for a picked Cesium object.
 *
 * @param {unknown} picked
 * @returns {string}
 */
function describePickedObject(picked) {
  const object = /** @type {any} */ (picked);
  if (object.id && object.id.id) {
    return `Entity: ${object.id.id}`;
  }
  if (object.primitive && object.primitive.id) {
    return `Primitive: ${object.primitive.id}`;
  }
  return "Cesium object selected";
}
