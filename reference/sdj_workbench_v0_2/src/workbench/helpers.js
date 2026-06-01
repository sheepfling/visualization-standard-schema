/**
 * Looks up an element by id.
 *
 * @param {string} id
 * @returns {HTMLElement}
 */
export function byId(id) {
  const element = document.getElementById(id);
  if (!element) {
    throw new Error(`Missing element #${id}.`);
  }
  return element;
}

/**
 * Escapes text for HTML insertion.
 *
 * @param {string} value
 * @returns {string}
 */
export function escapeHtml(value) {
  return value.replace(/[&<>'"]/g, (character) => {
    const entities = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      "'": "&#39;",
      "\"": "&quot;"
    };
    return entities[character] || character;
  });
}

/**
 * Converts an error-like value into text.
 *
 * @param {unknown} error
 * @returns {string}
 */
export function errorMessage(error) {
  if (error instanceof Error) {
    return error.message;
  }
  return String(error);
}

/**
 * Downloads text content.
 *
 * @param {string} filename
 * @param {string} content
 * @param {string} mimeType
 * @returns {void}
 */
export function downloadText(filename, content, mimeType) {
  const blob = new Blob([content], { type: mimeType });
  downloadBlob(blob, filename);
}

/**
 * Downloads a Blob.
 *
 * @param {Blob} blob
 * @param {string} filename
 * @returns {void}
 */
export function downloadBlob(blob, filename) {
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

/**
 * Returns the global Cesium object.
 *
 * @returns {any}
 */
export function getCesium() {
  if (!globalThis.Cesium) {
    throw new Error("Cesium is not loaded. Check the Cesium CDN script in index.html.");
  }
  return globalThis.Cesium;
}

/**
 * Returns the SDJ Cesium loader object.
 *
 * @returns {any}
 */
export function getSdjLoader() {
  if (!globalThis.SpatialDisplayJson) {
    throw new Error("SpatialDisplayJson loader is not loaded.");
  }
  return globalThis.SpatialDisplayJson;
}
