import { chromium } from "playwright";
import {
  analyzeWorkbenchShell,
  readWorkbenchIndexHtml,
  resolveBrowserFallbackMode,
  resolveBrowserLaunchOptions
} from "./smoke-support.mjs";

const baseUrl = process.env.SDJ_WORKBENCH_URL || "http://127.0.0.1:5173";
const launchOptions = resolveBrowserLaunchOptions();

async function runBrowserSmoke() {
  let browser;
  try {
    browser = await chromium.launch(launchOptions);
  } catch (error) {
    if (resolveBrowserFallbackMode() === "shell") {
      console.warn(`Browser launch failed; falling back to shell smoke: ${error instanceof Error ? error.message : String(error)}`);
      await runShellFallback();
      return;
    }
    throw error;
  }

  try {
    const page = await browser.newPage({
      viewport: {
        width: 1400,
        height: 900
      }
    });

    const consoleErrors = [];
    page.on("console", (message) => {
      if (message.type() === "error") {
        consoleErrors.push(message.text());
      }
    });

    await page.goto(baseUrl, { waitUntil: "networkidle" });
    await page.getByRole("heading", { name: "Scene JSON" }).waitFor();
    await page.getByRole("button", { name: "Load Minimal Example" }).waitFor();
    await page.getByRole("button", { name: "Render SDJ" }).click();
    await page.getByText("Rendered").waitFor({ timeout: 30000 });

    const statusText = await page.locator("#statusText").textContent();
    const bodyText = await page.locator("body").textContent();

    if (consoleErrors.some((line) => line.includes("Error constructing CesiumWidget"))) {
      throw new Error(`CesiumWidget failed to construct in browser: ${consoleErrors.join("\n")}`);
    }
    if (!bodyText || !bodyText.includes("Rendered")) {
      throw new Error("Expected rendered status text was not found.");
    }

    console.log(JSON.stringify({
      ok: true,
      mode: "browser",
      url: baseUrl,
      browser: launchOptions.channel || launchOptions.executablePath || "playwright-bundled",
      statusText: statusText || null,
      consoleErrors
    }, null, 2));
  } finally {
    await browser.close();
  }
}

async function runShellFallback() {
  const html = readWorkbenchIndexHtml();
  const analysis = analyzeWorkbenchShell(html);
  if (!analysis.ok) {
    throw new Error(`Workbench shell is missing required markup: ${analysis.missing.join(", ")}`);
  }

  console.log(JSON.stringify({
    ok: true,
    mode: "shell",
    url: "file://index.html",
    browser: null,
    statusText: "Shell markup verified",
    consoleErrors: [],
    missing: analysis.missing
  }, null, 2));
}

await runBrowserSmoke();
