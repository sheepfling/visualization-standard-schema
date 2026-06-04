import fs from "node:fs";
const report = JSON.parse(fs.readFileSync(new URL("./reports/acceptance-report.json", import.meta.url), "utf8"));
if (report.diagnostics.semanticErrors.length) process.exit(1);
console.log(`acceptance ${report.sceneId}: ${report.records.length} records`);
