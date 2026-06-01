import { analyzeWorkbenchShell, readWorkbenchIndexHtml } from "./smoke-support.mjs";

const baseUrl = process.env.SDJ_WORKBENCH_URL || "file://index.html";
const html = readWorkbenchIndexHtml();
const analysis = analyzeWorkbenchShell(html);

if (!analysis.ok) {
  throw new Error(`Workbench shell is missing required markup: ${analysis.missing.join(", ")}`);
}

console.log(JSON.stringify({
  ok: true,
  mode: "shell",
  url: baseUrl,
  statusText: "Shell markup verified",
  missing: analysis.missing
}, null, 2));
