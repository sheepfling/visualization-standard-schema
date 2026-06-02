export type JsonValue = string | number | boolean | null | JsonObject | JsonValue[];
export interface JsonObject {
  [key: string]: unknown;
}

export interface Diagnostic {
  severity: "error" | "warning" | "info" | string;
  code: string;
  path: string;
  message: string;
}

export interface TargetPlan {
  target: string;
  support: string;
  targetNative: string;
  lossiness: string;
  artifact: string;
  artifactPath: string;
  action: string;
  diagnostics?: Diagnostic[];
  artifactPaths?: string[];
}

export interface ObjectPlan {
  id: string;
  kind: string;
  name?: string;
  layer?: string;
  path: string;
  shown: boolean;
  targets: TargetPlan[];
}

export interface CompilePlan extends JsonObject {
  schemaVersion?: string;
  document: JsonObject;
  generatedAt: string;
  objectCount: number;
  analysisCount: number;
  presentationCount: number;
  kindCounts: Record<string, number>;
  targetTotals: Record<string, Record<string, number>>;
  semantic: {
    errors: Diagnostic[];
    warnings: Diagnostic[];
  };
  objects: ObjectPlan[];
  analysis: JsonObject[];
  presentation: JsonObject[];
}

export interface BackendBundle {
  files: Record<string, string>;
  manifest: JsonObject;
  compilePlan: CompilePlan;
  diagnostics: Diagnostic[];
}

export interface WorkbenchState {
  viewer?: unknown;
  defaultCapabilities?: JsonObject;
  exposedSceneCatalog?: JsonObject[];
  exposedSceneFeatured?: JsonObject[];
  exposedSceneDefaultPath?: string;
  lastLoad?: {
    entities?: Map<string, unknown>;
    primitives?: Map<string, unknown>;
    warnings?: string[];
  };
  currentScene?: JsonObject;
  currentPlan?: CompilePlan;
  selectedObjectId?: string;
}

export interface WorkbenchElements {
  drawer: HTMLElement;
  drawerToggle: HTMLElement;
  renderButton: HTMLElement;
  validateButton: HTMLElement;
  clearButton: HTMLElement;
  loadFeaturedSceneButton: HTMLElement;
  loadSelectedSceneButton: HTMLElement;
  sceneCatalogFilter: HTMLInputElement;
  sceneCatalogSelect: HTMLSelectElement;
  sceneCatalogSummary: HTMLElement;
  loadMinimalButton: HTMLElement;
  loadFullButton: HTMLElement;
  exportSdjButton: HTMLElement;
  exportCesiumButton: HTMLElement;
  exportSimdisButton: HTMLElement;
  exportSoapButton: HTMLElement;
  exportAllButton: HTMLElement;
  formatButton: HTMLElement;
  fileInput: HTMLInputElement;
  dropZone: HTMLElement;
  editor: HTMLTextAreaElement;
  statusText: HTMLElement;
  diagnosticsPanel: HTMLElement;
  totalsPanel: HTMLElement;
  objectTableBody: HTMLElement;
  objectFilter: HTMLInputElement;
  inspectorPanel: HTMLElement;
  copyInspectorButton: HTMLElement;
  downloadInspectorButton: HTMLElement;
  zoomSelectedButton: HTMLElement;
  selectedObject: HTMLElement;
  ionTokenInput: HTMLInputElement;
  saveTokenButton: HTMLElement;
}
