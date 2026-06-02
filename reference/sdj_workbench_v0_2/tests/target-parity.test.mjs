import { existsSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";
import { test } from "node:test";
import assert from "node:assert/strict";
import { compileBackend, buildCompilePlan } from "../../sdj_core_v0_1/src/index.ts";

const projectDir = dirname(dirname(fileURLToPath(import.meta.url)));
const fixturePath = join(projectDir, "tests/fixtures/parity-bridge.scene.json");
const runtimeFixturePath = join(projectDir, "tests/fixtures/runtime-families.bridge.scene.json");
const multiTrackFixturePath = join(projectDir, "tests/fixtures/multi-track.bridge.scene.json");
const pythonParityHelper = join(projectDir, "tests/python_target_parity.py");

function readJson(relativePath) {
  return JSON.parse(readFileSync(join(projectDir, relativePath), "utf8"));
}

function loadPythonParity(path = fixturePath, mode = "bridge") {
  const result = spawnSync("python3", [pythonParityHelper, path, mode], {
    encoding: "utf8",
    cwd: projectDir,
  });
  if (result.status !== 0) {
    throw new Error(`python parity helper failed:\n${result.stderr || result.stdout}`);
  }
  return JSON.parse(result.stdout);
}

function loadBridgeScene() {
  return readJson("tests/fixtures/parity-bridge.scene.json");
}

function loadRuntimeBridgeScene() {
  return readJson("tests/fixtures/runtime-families.bridge.scene.json");
}

function normalizeRuntimeObject(object) {
  return {
    id: object.id,
    kind: object.kind ?? object.runtimeType ?? object.objectType ?? null,
    name: object.name ?? null
  };
}

test("Cesium translation keeps packet identity parity with Python", () => {
  const bridgeScene = loadBridgeScene();
  const python = loadPythonParity();
  const compilePlan = buildCompilePlan(bridgeScene);
  const js = compileBackend(bridgeScene, "cesium");

  assert.equal(compilePlan.objectCount, python.cesium.packetCount - 1);
  assert.deepEqual(
    compilePlan.objects.map((object) => object.id),
    python.cesium.packetIds.filter((id) => id !== "document")
  );
  assert.deepEqual(
    JSON.parse(js.files["cesium/generated/cesium-example-bundle.json"]),
    python.cesium.packets
  );
});

test("SIMDIS bundle output matches the Python bundle on the bridge fixture", () => {
  const bridgeScene = loadBridgeScene();
  const python = loadPythonParity();
  const js = compileBackend(bridgeScene, "simdis");

  assert.deepEqual(JSON.parse(js.files["simdis/generated/simdis-example-bundle.json"]), python.simdis);
});

test("SOAP bundle output matches the Python bundle on the bridge fixture", () => {
  const bridgeScene = loadBridgeScene();
  const python = loadPythonParity();
  const js = compileBackend(bridgeScene, "soap");

  assert.deepEqual(JSON.parse(js.files["soap/generated/soap-example-bundle.json"]), python.soap);
});

test("runtime-family bundles stay parity-aligned between JS and Python", () => {
  const bridgeScene = loadRuntimeBridgeScene();
  const python = loadPythonParity(runtimeFixturePath);
  const jsSimdis = compileBackend(bridgeScene, "simdis");
  const jsSoap = compileBackend(bridgeScene, "soap");
  const pythonSimdisRuntime = python.simdis.runtimeObjects.map(normalizeRuntimeObject);
  const pythonSoapRuntime = python.soap.runtimeObjects.map(normalizeRuntimeObject);
  const jsSimdisRuntime = JSON.parse(jsSimdis.files["simdis/runtime-objects.json"]).runtimeObjects.map(normalizeRuntimeObject);
  const jsSoapRuntime = JSON.parse(jsSoap.files["soap/runtime-objects.json"]).runtimeObjects.map(normalizeRuntimeObject);

  assert.deepEqual(jsSimdisRuntime, pythonSimdisRuntime);
  assert.deepEqual(jsSoapRuntime, pythonSoapRuntime);
  assert.equal(jsSimdis.manifest.totals.runtimeObjects, pythonSimdisRuntime.length);
  assert.equal(jsSoap.manifest.totals.runtimeObjects, pythonSoapRuntime.length);
});

const corpusScenes = [
  { name: "bridge parity", path: fixturePath },
  { name: "multi-track bridge", path: multiTrackFixturePath },
];

for (const scene of corpusScenes) {
  test(`target parity matches Python on corpus scene ${scene.name}`, { skip: !existsSync(scene.path) }, () => {
    const bridgeScene = JSON.parse(readFileSync(scene.path, "utf8"));
    const python = loadPythonParity(scene.path, "bridge");
    const jsCesium = compileBackend(bridgeScene, "cesium");
    const jsSimdis = compileBackend(bridgeScene, "simdis");
    const jsSoap = compileBackend(bridgeScene, "soap");

    assert.deepEqual(JSON.parse(jsCesium.files["cesium/generated/cesium-example-bundle.json"]), python.cesium.packets);
    assert.deepEqual(JSON.parse(jsSimdis.files["simdis/generated/simdis-example-bundle.json"]), python.simdis);
    assert.deepEqual(JSON.parse(jsSoap.files["soap/generated/soap-example-bundle.json"]), python.soap);
  });
}
