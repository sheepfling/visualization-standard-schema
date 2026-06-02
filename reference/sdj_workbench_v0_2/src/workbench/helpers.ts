import type { CesiumSpatialDisplayLoader } from "../types/runtime";

export interface CesiumRuntime {
  Ion: {
    defaultAccessToken: string;
  };
  Viewer: new (containerId: string, options: Record<string, unknown>) => ViewerInstance;
  ScreenSpaceEventHandler: new (canvas: HTMLCanvasElement) => ScreenSpaceEventHandlerInstance;
  ScreenSpaceEventType: {
    LEFT_CLICK: unknown;
  };
  defined(value: unknown): boolean;
}

export interface ViewerInstance {
  scene: {
    globe: {
      depthTestAgainstTerrain: boolean;
    };
    debugShowFramesPerSecond: boolean;
    canvas: HTMLCanvasElement;
    pick(position: unknown): unknown;
    primitives: {
      remove(primitive: unknown): void;
    };
  };
  entities: {
    remove(entity: unknown): void;
  };
  zoomTo(target: unknown): Promise<void>;
  selectedEntity?: unknown;
}

export interface ScreenSpaceEventHandlerInstance {
  setInputAction(callback: (movement: { position: unknown }) => void, type: unknown): void;
}

type BrowserGlobals = Window & typeof globalThis & {
  Cesium?: CesiumRuntime;
  SpatialDisplayJson?: CesiumSpatialDisplayLoader;
  SpatialDisplayJsonKindTargets?: Record<string, { backend: string; target: string; status: string }>;
};

export function byId(id: string): HTMLElement {
  const element = document.getElementById(id);
  if (!element) {
    throw new Error(`Missing element #${id}.`);
  }
  return element;
}

export function escapeHtml(value: string): string {
  return value.replace(/[&<>'"]/g, (character) => {
    const entities: Record<string, string> = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      "'": "&#39;",
      "\"": "&quot;"
    };
    return entities[character] || character;
  });
}

export function errorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  return String(error);
}

export function downloadText(filename: string, content: string, mimeType: string): void {
  const blob = new Blob([content], { type: mimeType });
  downloadBlob(blob, filename);
}

export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => {
    URL.revokeObjectURL(url);
  }, 1000);
}

export function getCesium(): CesiumRuntime {
  const globals = globalThis as BrowserGlobals;
  if (!globals.Cesium) {
    throw new Error("Cesium is not loaded. Check the Cesium CDN script in index.html.");
  }
  return globals.Cesium;
}

export function getSdjLoader(): CesiumSpatialDisplayLoader {
  const globals = globalThis as BrowserGlobals;
  if (!globals.SpatialDisplayJson) {
    throw new Error("SpatialDisplayJson loader is not loaded.");
  }
  return globals.SpatialDisplayJson;
}

export function getSdjCesiumKindTargets(): Record<string, { backend: string; target: string; status: string }> | undefined {
  const globals = globalThis as BrowserGlobals;
  return globals.SpatialDisplayJsonKindTargets;
}
