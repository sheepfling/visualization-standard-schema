import { mkdirSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, relative, sep } from "node:path";
import { fileURLToPath } from "node:url";

/**
 * @param {string} dir
 * @returns {string[]}
 */
function walk(dir) {
  /** @type {string[]} */
  const files = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const entryPath = join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...walk(entryPath));
    } else if (entry.isFile() && entry.name.endsWith(".sdj.json")) {
      files.push(entryPath);
    }
  }
  return files;
}

/**
 * @param {string} text
 * @returns {string}
 */
function titleCaseFromSlug(text) {
  return text
    .split(/[\s_-]+/g)
    .filter(Boolean)
    .map((part) => `${part.charAt(0).toUpperCase()}${part.slice(1)}`)
    .join(" ");
}

const projectDir = dirname(dirname(fileURLToPath(import.meta.url)));
const repoRoot = join(projectDir, "..", "..");
const sourceRoot = join(repoRoot, "examples", "orb-corpus", "sdj");
const srcDir = join(projectDir, "src");
const files = walk(sourceRoot);

const scenes = files.map((filePath) => {
  const scene = JSON.parse(readFileSync(filePath, "utf8"));
  const parts = relative(sourceRoot, filePath).split(sep);
  const group = parts.slice(0, -1).join("/") || "root";
  const fileBase = parts.at(-1)?.replace(/\.sdj\.json$/, "") || "scene";
  const document = scene.document || {};
  const pathForApp = relative(srcDir, filePath).split(sep).join("/");
  return {
    path: pathForApp,
    id: String(document.id || fileBase),
    name: String(document.name || fileBase),
    objectCount: Array.isArray(scene.objects) ? scene.objects.length : 0,
    group,
    schemaVersion: String(scene.schemaVersion || ""),
    source: String(document.source || "")
  };
}).sort((left, right) => {
  if (right.objectCount !== left.objectCount) {
    return right.objectCount - left.objectCount;
  }
  return left.name.localeCompare(right.name);
});

const manifest = {
  generatedAt: new Date().toISOString(),
  sourceRoot: "examples/orb-corpus/sdj",
  totalCount: scenes.length,
  defaultPath: scenes[0]?.path || null,
  featured: scenes.slice(0, 12),
  scenes
};

const outputPath = join(projectDir, "data", "sdj_exposed_scenes_manifest.json");
mkdirSync(dirname(outputPath), { recursive: true });
writeFileSync(outputPath, `${JSON.stringify(manifest, null, 2)}\n`, "utf8");
console.log(JSON.stringify({ ok: true, outputPath, totalCount: scenes.length }, null, 2));
