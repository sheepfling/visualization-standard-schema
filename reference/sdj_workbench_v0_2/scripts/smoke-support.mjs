import { existsSync } from "node:fs";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

export const DEFAULT_BROWSER_PATHS = [
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  "/Applications/Google Chrome Beta.app/Contents/MacOS/Google Chrome Beta",
  "/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary",
  "/Applications/Chromium.app/Contents/MacOS/Chromium",
  "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"
];

/**
 * @param {Record<string, string | undefined>} [env]
 * @param {(path: string) => boolean} [fileExists]
 * @returns {{ headless: boolean, executablePath?: string, channel?: string }}
 */
export function resolveBrowserLaunchOptions(env = process.env, fileExists = existsSync) {
  const headless = readBooleanEnv(env.SDJ_BROWSER_HEADLESS, true);
  const channel = normalizeChannel(env.SDJ_BROWSER_CHANNEL);

  if (channel) {
    return { headless, channel };
  }

  const explicitExecutablePath = env.SDJ_BROWSER_EXECUTABLE_PATH?.trim();
  if (explicitExecutablePath) {
    return { headless, executablePath: explicitExecutablePath };
  }

  for (const candidate of DEFAULT_BROWSER_PATHS) {
    if (fileExists(candidate)) {
      return { headless, executablePath: candidate };
    }
  }

  return { headless };
}

/**
 * @param {Record<string, string | undefined>} [env]
 * @returns {"shell" | "none"}
 */
export function resolveBrowserFallbackMode(env = process.env) {
  const value = env.SDJ_BROWSER_SMOKE_FALLBACK?.trim().toLowerCase();
  return value === "none" ? "none" : "shell";
}

/**
 * @param {string | undefined} value
 * @param {boolean} defaultValue
 * @returns {boolean}
 */
export function readBooleanEnv(value, defaultValue) {
  if (value === undefined) {
    return defaultValue;
  }
  const normalized = value.trim().toLowerCase();
  if (["0", "false", "no", "off"].includes(normalized)) {
    return false;
  }
  if (["1", "true", "yes", "on"].includes(normalized)) {
    return true;
  }
  return defaultValue;
}

/**
 * @param {string | undefined} value
 * @returns {string | undefined}
 */
export function normalizeChannel(value) {
  const channel = value?.trim();
  return channel ? channel : undefined;
}

/**
 * @param {string} html
 * @returns {{ ok: boolean, missing: string[] }}
 */
export function analyzeWorkbenchShell(html) {
  const requirements = [
    { name: "Cesium container", needle: 'id="cesiumContainer"' },
    { name: "App script", needle: 'type="module" src="./src/app.js"' },
    { name: "Cesium loader", needle: 'src="./vendor/sdj_cesium_loader_v0_4.js"' },
    { name: "Render button", needle: 'id="renderButton"' },
    { name: "Load example", needle: 'id="loadMinimalButton"' }
  ];

  const missing = requirements.filter((requirement) => !html.includes(requirement.needle)).map((requirement) => requirement.name);
  return { ok: missing.length === 0, missing };
}

/**
 * @returns {string}
 */
export function readWorkbenchIndexHtml() {
  const projectDir = dirname(dirname(fileURLToPath(import.meta.url)));
  return readFileSync(join(projectDir, "index.html"), "utf8");
}
