import { buildCompilePlan } from "./plan.ts";
import { toJson, type JsonObject } from "./json.ts";
import { compileCesium, type BackendBundle as CesiumBackendBundle } from "./cesium_backend.ts";
import { compileSimdis, type BackendBundle as SimdisBackendBundle } from "./simdis_backend.ts";
import { compileSoap, type BackendBundle as SoapBackendBundle } from "./soap_backend.ts";

export type BackendBundle = CesiumBackendBundle | SimdisBackendBundle | SoapBackendBundle;

export function compileBackend(scene: JsonObject, target: string): BackendBundle {
  const compilePlan = buildCompilePlan(scene);
  if (target === "cesium") {
    return compileCesium(scene, compilePlan);
  }
  if (target === "simdis") {
    return compileSimdis(scene, compilePlan);
  }
  if (target === "soap") {
    return compileSoap(scene, compilePlan);
  }
  throw new Error(`Unsupported SDJ export target '${target}'.`);
}

export function compileAllBackends(scene: JsonObject): Record<string, BackendBundle> {
  return {
    cesium: compileBackend(scene, "cesium"),
    simdis: compileBackend(scene, "simdis"),
    soap: compileBackend(scene, "soap")
  };
}

export function compileAllBackendsToFiles(scene: JsonObject): Record<string, string> {
  const bundles = compileAllBackends(scene);
  const files: Record<string, string> = {
    "compile-plan-all-targets.json": toJson(buildCompilePlan(scene))
  };
  for (const [target, bundle] of Object.entries(bundles)) {
    for (const [path, content] of Object.entries(bundle.files)) {
      files[path] = content;
    }
    files[`${target}/bundle-summary.json`] = toJson({
      target,
      manifest: bundle.manifest,
      diagnostics: bundle.diagnostics
    });
  }
  return files;
}
