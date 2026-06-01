/**
 * Shared JSON helpers for the SDJ workbench library layer.
 *
 * @typedef {Record<string, unknown>} JsonObject
 */

/**
 * @param {unknown} value
 * @returns {JsonObject}
 */
export function asObject(value) {
  if (value && typeof value === "object" && !Array.isArray(value)) {
    return /** @type {JsonObject} */ (value);
  }
  return {};
}

/**
 * @param {unknown} value
 * @returns {unknown[]}
 */
export function asArray(value) {
  if (Array.isArray(value)) {
    return value;
  }
  return [];
}

/**
 * @param {unknown} value
 * @returns {number | undefined}
 */
export function asNumber(value) {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  return undefined;
}

/**
 * @param {unknown} value
 * @returns {string | undefined}
 */
export function asString(value) {
  if (typeof value === "string") {
    return value;
  }
  return undefined;
}

/**
 * @template T
 * @param {T} value
 * @returns {T}
 */
export function cloneJson(value) {
  return /** @type {T} */ (JSON.parse(JSON.stringify(value)));
}

/**
 * @param {unknown} value
 * @returns {string}
 */
export function toJson(value) {
  return `${JSON.stringify(value, null, 2)}\n`;
}
