import { test } from "node:test";
import assert from "node:assert/strict";
import {
  analyzeWorkbenchShell,
  resolveBrowserFallbackMode,
  resolveBrowserLaunchOptions
} from "../scripts/smoke-support.mjs";

test("resolveBrowserLaunchOptions prefers an explicit executable path", () => {
  const options = resolveBrowserLaunchOptions(
    {
      SDJ_BROWSER_EXECUTABLE_PATH: "/tmp/fake-browser",
      SDJ_BROWSER_CHANNEL: "chrome",
      SDJ_BROWSER_HEADLESS: "false"
    },
    () => false
  );

  assert.deepEqual(options, {
    headless: false,
    executablePath: "/tmp/fake-browser"
  });
});

test("resolveBrowserLaunchOptions falls back through known browser paths", () => {
  const options = resolveBrowserLaunchOptions(
    {
      SDJ_BROWSER_HEADLESS: "true"
    },
    (path) => path === "/Applications/Chromium.app/Contents/MacOS/Chromium"
  );

  assert.deepEqual(options, {
    headless: true,
    executablePath: "/Applications/Chromium.app/Contents/MacOS/Chromium"
  });
});

test("resolveBrowserFallbackMode defaults to shell smoke", () => {
  assert.equal(resolveBrowserFallbackMode({}), "shell");
  assert.equal(resolveBrowserFallbackMode({ SDJ_BROWSER_SMOKE_FALLBACK: "none" }), "none");
});

test("analyzeWorkbenchShell validates the required workbench markup", () => {
  const analysis = analyzeWorkbenchShell(`
    <main id="cesiumContainer"></main>
    <button id="renderButton"></button>
    <button id="loadMinimalButton"></button>
    <script src="./vendor/sdj_cesium_loader_v0_4.js"></script>
    <script type="module" src="./src/app.js"></script>
  `);

  assert.equal(analysis.ok, true);
  assert.deepEqual(analysis.missing, []);
});

test("analyzeWorkbenchShell reports missing markup", () => {
  const analysis = analyzeWorkbenchShell("<main></main>");

  assert.equal(analysis.ok, false);
  assert.deepEqual(analysis.missing, [
    "Cesium container",
    "App script",
    "Cesium loader",
    "Render button",
    "Load example"
  ]);
});
