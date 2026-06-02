import { getCesium, type CesiumRuntime, type ViewerInstance } from "./helpers.ts";

type ViewerState = {
  viewer?: unknown;
  lastLoad?: { entities?: Map<string, unknown>; primitives?: Map<string, unknown> };
  selectedObjectId?: string;
};

type ViewerElements = {
  ionTokenInput: HTMLInputElement;
  selectedObject: HTMLElement;
};

type CesiumPicked = {
  id?: string | { id?: string };
  primitive?: { id?: string };
};

export function initializeViewer(deps: { state: ViewerState; elements: ViewerElements; selectObject: (objectId: string, options?: { focusCesium?: boolean }) => void }): void {
  const Cesium: CesiumRuntime = getCesium();
  const storedToken = localStorage.getItem("sdj.cesiumIonToken") || "";
  deps.elements.ionTokenInput.value = storedToken;
  if (storedToken) {
    Cesium.Ion.defaultAccessToken = storedToken;
  }

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

  deps.state.viewer = new Cesium.Viewer("cesiumContainer", viewerOptions);
  const viewer = deps.state.viewer as ViewerInstance | undefined;
  if (!viewer) {
    throw new Error("Cesium viewer could not be initialized.");
  }
  viewer.scene.globe.depthTestAgainstTerrain = false;
  viewer.scene.debugShowFramesPerSecond = false;

  const handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);
  handler.setInputAction((movement: { position: unknown }) => {
    const picked = viewer.scene.pick(movement.position);
    if (Cesium.defined(picked)) {
      const objectId = objectIdFromPicked(picked);
      if (objectId) {
        deps.selectObject(objectId, { focusCesium: false });
      } else {
        deps.elements.selectedObject.textContent = describePickedObject(picked);
      }
    } else {
      deps.elements.selectedObject.textContent = "No object selected";
    }
  }, Cesium.ScreenSpaceEventType.LEFT_CLICK);
}

export async function zoomToSelectedObject(deps: { state: ViewerState; setStatus: (message: string, kind: "ok" | "warning" | "error" | "neutral") => void }): Promise<void> {
  if (!deps.state.selectedObjectId) {
    deps.setStatus("No object selected.", "warning");
    return;
  }
  const viewer = deps.state.viewer as ViewerInstance | undefined;
  if (!viewer || !deps.state.lastLoad) {
    deps.setStatus("Render the scene before zooming to a selected object.", "warning");
    return;
  }

  const entity = deps.state.lastLoad.entities && deps.state.lastLoad.entities.get(deps.state.selectedObjectId);
  if (entity) {
    await viewer.zoomTo(entity);
    viewer.selectedEntity = entity;
    deps.setStatus(`Zoomed to ${deps.state.selectedObjectId}.`, "ok");
    return;
  }

  const primitive = deps.state.lastLoad.primitives && deps.state.lastLoad.primitives.get(deps.state.selectedObjectId);
  if (primitive) {
    try {
      await viewer.zoomTo(primitive);
      deps.setStatus(`Zoomed to primitive ${deps.state.selectedObjectId}.`, "ok");
    } catch {
      deps.setStatus(`Selected primitive ${deps.state.selectedObjectId}; Cesium cannot always auto-zoom primitive-only objects.`, "warning");
    }
    return;
  }

  deps.setStatus(`Selected object '${deps.state.selectedObjectId}' is not in the current Cesium load result.`, "warning");
}

export function focusCesiumObject(deps: { state: ViewerState; elements: ViewerElements }, objectId: string): void {
  const viewer = deps.state.viewer as ViewerInstance | undefined;
  if (!viewer || !deps.state.lastLoad) {
    return;
  }
  const entity = deps.state.lastLoad.entities && deps.state.lastLoad.entities.get(objectId);
  if (entity) {
    viewer.selectedEntity = entity;
    return;
  }
  const primitive = deps.state.lastLoad.primitives && deps.state.lastLoad.primitives.get(objectId);
  if (primitive) {
    deps.elements.selectedObject.textContent = `Selected SDJ primitive: ${objectId}`;
  }
}

export function countRenderableObjects(scene: { objects?: unknown[] }, flattenObjects: (value: unknown[]) => { show?: unknown }[], isShown: (value: unknown) => boolean): number {
  return flattenObjects(Array.isArray(scene.objects) ? scene.objects : []).filter((object) => isShown(object.show) !== false).length;
}

export function objectIdFromPicked(picked: unknown): string | undefined {
  const object = picked as CesiumPicked;
  if (object.id && typeof object.id === "object" && typeof object.id.id === "string") {
    return object.id.id;
  }
  if (object.primitive && typeof object.primitive.id === "string") {
    return object.primitive.id;
  }
  if (typeof object.id === "string") {
    return object.id;
  }
  return undefined;
}

export function describePickedObject(picked: unknown): string {
  const object = picked as CesiumPicked;
  if (object.id && typeof object.id === "object" && object.id.id) {
    return `Entity: ${object.id.id}`;
  }
  if (object.primitive && object.primitive.id) {
    return `Primitive: ${object.primitive.id}`;
  }
  return "Cesium object selected";
}
