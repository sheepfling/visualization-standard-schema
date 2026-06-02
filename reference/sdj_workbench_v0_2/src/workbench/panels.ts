import { asArray, asObject, buildCompilePlan, inspectObject, toJson } from "../../../sdj_core_v0_1/src/index.ts";
import { escapeHtml } from "./helpers.ts";

type JsonObject = Record<string, unknown>;
type DiagnosticLike = {
  severity?: string;
  code?: string;
  message?: string;
  path?: string;
};
type PanelsState = {
  currentScene?: JsonObject;
  currentPlan?: JsonObject;
  selectedObjectId?: string;
};
type PanelsUpdateDeps = {
  state: PanelsState;
  findSceneObject: (scene: JsonObject, objectId: string) => JsonObject | undefined;
  renderDiagnostics: (plan: JsonObject) => void;
  renderTotals: (plan: JsonObject) => void;
  renderObjectTable: (scene: JsonObject, plan: JsonObject) => void;
  renderInspector: (scene: JsonObject, plan: JsonObject) => void;
};
type PanelsClearDeps = {
  state: { currentPlan?: JsonObject };
  elements: {
    diagnosticsPanel: HTMLElement;
    totalsPanel: HTMLElement;
    objectTableBody: HTMLElement;
    inspectorPanel: HTMLElement;
  };
};
type DiagnosticsDeps = {
  elements: { diagnosticsPanel: HTMLElement };
};
type TotalsDeps = {
  elements: { totalsPanel: HTMLElement };
};
type ObjectTableDeps = {
  state: { selectedObjectId?: string };
  elements: { objectTableBody: HTMLElement; objectFilter: HTMLInputElement };
  flattenObjects: (objects: JsonObject[]) => JsonObject[];
  asArray: (value: unknown) => unknown[];
  asObject: (value: unknown) => JsonObject;
};
type ClickEvent = {
  target: EventTarget | null;
};
type SelectObjectDeps = {
  state: { selectedObjectId?: string };
  elements: { selectedObject: HTMLElement };
};
type InspectorDeps = {
  state: { selectedObjectId?: string };
  elements: { inspectorPanel: HTMLElement };
  inspectObject: (scene: JsonObject, objectId: string, plan?: JsonObject) => JsonObject | undefined;
  asArray: (value: unknown) => unknown[];
  asObject: (value: unknown) => JsonObject;
};
type InspectionLike = {
  id?: string;
  kind?: string;
  name?: string;
  path?: string;
  visible?: boolean;
  object?: JsonObject;
  targets?: unknown[];
  semanticDiagnostics?: unknown[];
  rendererHints?: JsonObject;
  plan?: JsonObject;
};
type DiagnosticListItem = {
  severity?: string;
  code?: string;
  message?: string;
  path?: string;
};
type SelectedObjectReportDeps = {
  state: { selectedObjectId?: string };
  parseEditorScene: () => JsonObject;
  inspectObject: (scene: JsonObject, objectId: string, plan?: JsonObject) => JsonObject | undefined;
};
type CopyReportDeps = {
  state: { selectedObjectId?: string };
  parseEditorScene: () => JsonObject;
  inspectObject: (scene: JsonObject, objectId: string, plan?: JsonObject) => JsonObject | undefined;
  buildSelectedObjectReport: () => string;
};
type DownloadReportDeps = {
  state: { selectedObjectId?: string };
  parseEditorScene: () => JsonObject;
  inspectObject: (scene: JsonObject, objectId: string, plan?: JsonObject) => JsonObject | undefined;
  buildSelectedObjectReport: () => string;
  downloadText: (filename: string, content: string, mimeType: string) => void;
};

/**
 * Updates diagnostics and support panels for a scene.
 *
 * @param {{
 *   state: { currentScene?: JsonObject, currentPlan?: JsonObject, selectedObjectId?: string },
 *   elements: { diagnosticsPanel: HTMLElement, totalsPanel: HTMLElement, objectTableBody: HTMLElement, inspectorPanel: HTMLElement, objectFilter: HTMLInputElement, selectedObject: HTMLElement },
 *   findSceneObject: (scene: JsonObject, objectId: string) => JsonObject | undefined,
 *   renderDiagnostics: (plan: JsonObject) => void,
 *   renderTotals: (plan: JsonObject) => void,
 *   renderObjectTable: (scene: JsonObject, plan: JsonObject) => void,
 *   renderInspector: (scene: JsonObject, plan: JsonObject) => void
 * }} deps
 * @param {JsonObject} scene
 * @returns {void}
 */
export function updatePanels(deps: PanelsUpdateDeps, scene: JsonObject): void {
  const plan = buildCompilePlan(scene);
  deps.state.currentScene = scene;
  deps.state.currentPlan = plan;
  if (deps.state.selectedObjectId && !deps.findSceneObject(scene, deps.state.selectedObjectId)) {
    deps.state.selectedObjectId = undefined;
  }
  deps.renderDiagnostics(plan);
  deps.renderTotals(plan);
  deps.renderObjectTable(scene, plan);
  deps.renderInspector(scene, plan);
}

/**
 * Clears diagnostics panels.
 *
 * @param {{ state: { currentPlan?: JsonObject }, elements: { diagnosticsPanel: HTMLElement, totalsPanel: HTMLElement, objectTableBody: HTMLElement, inspectorPanel: HTMLElement } }} deps
 * @returns {void}
 */
export function clearPanels(deps: PanelsClearDeps): void {
  deps.elements.diagnosticsPanel.innerHTML = "";
  deps.elements.totalsPanel.innerHTML = "";
  deps.elements.objectTableBody.innerHTML = "";
  deps.elements.inspectorPanel.innerHTML = `<div class="empty-state">Select an object from the table or click a rendered Cesium object.</div>`;
  deps.state.currentPlan = undefined;
}

/**
 * Renders semantic diagnostics.
 *
 * @param {{ elements: { diagnosticsPanel: HTMLElement } }} deps
 * @param {JsonObject} plan
 * @returns {void}
 */
export function renderDiagnostics(deps: DiagnosticsDeps, plan: JsonObject): void {
  const semantic = (plan.semantic as { errors?: unknown[]; warnings?: unknown[] } | undefined) || {};
  const errors = Array.isArray(semantic.errors) ? semantic.errors : [];
  const warnings = Array.isArray(semantic.warnings) ? semantic.warnings : [];
  const items = [...errors, ...warnings].slice(0, 60);
  if (items.length === 0) {
    deps.elements.diagnosticsPanel.innerHTML = `<div class="empty-state">No semantic diagnostics.</div>`;
    return;
  }
  deps.elements.diagnosticsPanel.innerHTML = items.map((item) => {
    const diagnostic = item as DiagnosticLike;
    const severity = String(diagnostic.severity || "warning");
    return `<div class="diagnostic ${escapeHtml(severity)}"><strong>${escapeHtml(String(diagnostic.code || severity))}</strong><span>${escapeHtml(String(diagnostic.message || ""))}</span><small>${escapeHtml(String(diagnostic.path || ""))}</small></div>`;
  }).join("");
}

/**
 * Renders backend compile totals.
 *
 * @param {{ elements: { totalsPanel: HTMLElement } }} deps
 * @param {JsonObject} plan
 * @returns {void}
 */
export function renderTotals(deps: TotalsDeps, plan: JsonObject): void {
  const targetTotals = (plan.targetTotals || {}) as Record<string, Record<string, number>>;
  const html = ["cesium", "simdis", "soap"].map((target) => {
    const totals = targetTotals[target] || {};
    return `<article class="target-card"><h3>${target.toUpperCase()}</h3><dl><div><dt>Strong</dt><dd>${Number(totals.strong || 0)}</dd></div><div><dt>Partial</dt><dd>${Number(totals.partial || 0)}</dd></div><div><dt>Reserved</dt><dd>${Number(totals.reserved || 0)}</dd></div><div><dt>Unsupported</dt><dd>${Number(totals.unsupported || 0)}</dd></div><div><dt>Hidden</dt><dd>${Number(totals.hidden || 0)}</dd></div></dl></article>`;
  }).join("");
  deps.elements.totalsPanel.innerHTML = html;
}

/**
 * Renders the object coverage table.
 *
 * @param {{
 *   state: { selectedObjectId?: string },
 *   elements: { objectTableBody: HTMLElement, objectFilter: HTMLInputElement },
 *   flattenObjects: (objects: JsonObject[]) => JsonObject[],
 *   asArray: (value: unknown) => unknown[],
 *   asObject: (value: unknown) => JsonObject
 * }} deps
 * @param {JsonObject} scene
 * @param {JsonObject} plan
 * @returns {void}
 */
export function renderObjectTable(deps: ObjectTableDeps, scene: JsonObject, plan: JsonObject): void {
  const filter = deps.elements.objectFilter.value.trim().toLowerCase();
  const objects = deps.flattenObjects(deps.asArray(scene.objects).map(deps.asObject));
  const plans = new Map(deps.asArray(plan.objects).map((item) => {
    const objectPlan = item as JsonObject;
    return [String(objectPlan.id), objectPlan];
  }));
  const rows = objects.filter((object) => {
    if (!filter) {
      return true;
    }
    return `${object.id || ""} ${object.kind || ""} ${object.name || ""}`.toLowerCase().includes(filter);
  }).slice(0, 250).map((object) => {
    const objectId = String(object.id || "");
    const objectPlan = (plans.get(objectId) || {}) as JsonObject;
    const targetBadges = deps.asArray(objectPlan.targets).map((targetPlan) => {
      const target = targetPlan as JsonObject;
      const support = String(target.support || "unknown");
      const title = `${String(target.targetNative || "")} / ${String(target.lossiness || "unknown")} lossiness`;
      return `<span class="support-badge ${escapeHtml(support)}" title="${escapeHtml(title)}">${escapeHtml(String(target.target || "?"))}: ${escapeHtml(support)}</span>`;
    }).join(" ");
    const selected = deps.state.selectedObjectId === objectId ? " selected" : "";
    const shown = object.show === false ? " hidden-object" : "";
    return `<tr class="object-row${selected}${shown}" data-object-id="${escapeHtml(objectId)}"><td>${escapeHtml(objectId)}</td><td>${escapeHtml(String(object.kind || ""))}</td><td>${escapeHtml(String(object.name || ""))}</td><td>${targetBadges}</td></tr>`;
  }).join("");
  deps.elements.objectTableBody.innerHTML = rows || `<tr><td colspan="4" class="empty-state">No matching objects.</td></tr>`;
}

export function getClickedObjectId(event: ClickEvent): string | undefined {
  const target = event.target instanceof Element ? event.target : null;
  const row = target ? target.closest("tr[data-object-id]") : null;
  if (!row) {
    return undefined;
  }
  const objectId = row.getAttribute("data-object-id");
  return objectId || undefined;
}

export function selectObject(deps: SelectObjectDeps, objectId: string): void {
  deps.state.selectedObjectId = objectId;
  deps.elements.selectedObject.textContent = `Selected SDJ object: ${objectId}`;
}

export function renderInspector(deps: InspectorDeps, scene: JsonObject, plan: JsonObject): void {
  if (!deps.state.selectedObjectId) {
    deps.elements.inspectorPanel.innerHTML = `<div class="empty-state">Select an object from the table or click a rendered Cesium object.</div>`;
    return;
  }
  const inspection = deps.inspectObject(scene, deps.state.selectedObjectId, plan) as InspectionLike | undefined;
  if (!inspection) {
    deps.elements.inspectorPanel.innerHTML = `<div class="empty-state">Selected object '${escapeHtml(deps.state.selectedObjectId)}' is not present in the current editor scene.</div>`;
    return;
  }

  const object = deps.asObject(inspection.object);
  const targets = deps.asArray(inspection.targets).map((target: unknown) => deps.asObject(target));
  const semanticDiagnostics = deps.asArray(inspection.semanticDiagnostics).map((diagnostic: unknown) => deps.asObject(diagnostic));
  const targetHtml = targets.map((target) => renderTargetInspectorCard(target)).join("");
  const semanticHtml = renderDiagnosticList(semanticDiagnostics as DiagnosticListItem[], "No object-specific semantic diagnostics.");
  const rendererHints = deps.asObject(inspection.rendererHints);
  const hintsHtml = Object.keys(rendererHints).length > 0
    ? `<details><summary>Renderer hints</summary><pre>${escapeHtml(toJson(rendererHints))}</pre></details>`
    : `<p class="inspector-muted">No rendererHints block on this object.</p>`;

  deps.elements.inspectorPanel.innerHTML = `
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
      <section class="inspector-subsection">
        <h3>Plan JSON</h3>
        <details><summary>Compiled plan entry</summary><pre>${escapeHtml(toJson(inspection.plan || {}))}</pre></details>
      </section>
    </article>
  `;
}

export function renderTargetInspectorCard(target: JsonObject): string {
  const support = String(target.support || "unknown");
  const action = String(target.action || "");
  const artifact = target.artifact ? `Artifact: ${String(target.artifact)}<br>` : "";
  const artifactPath = target.artifactPath ? `Artifact path: ${String(target.artifactPath)}<br>` : "";
  return `
    <article class="target-inspector-card">
      <div class="target-inspector-heading">
        <strong>${escapeHtml(String(target.target || "?"))}</strong>
        <span class="support-badge ${escapeHtml(support)}">${escapeHtml(support)}</span>
      </div>
      <p>${escapeHtml(String(target.targetNative || "n/a"))}</p>
      <p class="target-inspector-lossiness">${escapeHtml(String(target.lossiness || "unknown"))} lossiness</p>
      <p class="inspector-muted">${escapeHtml(action)}</p>
      <p class="inspector-muted">${artifact}${artifactPath}</p>
    </article>
  `;
}

export function renderDiagnosticList(diagnostics: DiagnosticListItem[] | undefined, emptyMessage: string): string {
  if (!diagnostics || diagnostics.length === 0) {
    return `<div class="empty-state">${escapeHtml(emptyMessage)}</div>`;
  }
  return diagnostics.map((diagnostic) => {
    const severity = String(diagnostic.severity || "warning");
    return `<div class="diagnostic ${escapeHtml(severity)}"><strong>${escapeHtml(String(diagnostic.code || severity))}</strong><span>${escapeHtml(String(diagnostic.message || ""))}</span><small>${escapeHtml(String(diagnostic.path || ""))}</small></div>`;
  }).join("");
}

export function buildSelectedObjectReport(deps: SelectedObjectReportDeps): string {
  if (!deps.state.selectedObjectId) {
    return "No object selected.";
  }
  const scene = deps.parseEditorScene();
  const inspection = inspectObject(scene, deps.state.selectedObjectId) as InspectionLike | undefined;
  if (!inspection) {
    return `Selected object '${deps.state.selectedObjectId}' is not present in the current editor scene.`;
  }
  return [
    `Selected object: ${inspection.id}`,
    `Kind: ${inspection.kind}`,
    `Name: ${inspection.name || "(unnamed)"}`,
    `Path: ${inspection.path}`,
    `Visible: ${inspection.visible ? "yes" : "no"}`,
    "",
    "Targets:",
    ...((inspection.targets || []) as JsonObject[]).map((target) => {
      const entry = target as { target?: string; support?: string; targetNative?: string; lossiness?: string };
      return `- ${entry.target}: ${entry.support} -> ${entry.targetNative} (${entry.lossiness} lossiness)`;
    }),
    "",
    "Semantic diagnostics:",
    ...((inspection.semanticDiagnostics || []) as JsonObject[]).map((diagnostic) => {
      const entry = diagnostic as DiagnosticLike;
      return `- ${entry.severity}: ${entry.code} :: ${entry.message} (${entry.path})`;
    })
  ].join("\n");
}

export function copySelectedObjectReport(deps: CopyReportDeps): void {
  const report = buildSelectedObjectReport(deps);
  navigator.clipboard.writeText(report);
}

export function downloadSelectedObjectReport(deps: DownloadReportDeps): void {
  const report = buildSelectedObjectReport(deps);
  deps.downloadText("selected-object-report.txt", `${report}\n`, "text/plain");
}
