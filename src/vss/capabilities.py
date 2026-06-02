from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import Field

from .models import VssModel, VssScene

TargetName = Literal["cesium", "simdis", "soap"]
SupportLevel = Literal["strong", "partial", "unsupported"]


class TargetSurface(VssModel):
    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    kind: str = Field(min_length=1)
    status: SupportLevel
    description: str = Field(min_length=1)
    artifacts: list[str] = Field(default_factory=list)


class SchemaFeatureSupport(VssModel):
    featureId: str = Field(min_length=1)
    label: str = Field(min_length=1)
    support: SupportLevel
    notes: str = Field(min_length=1)
    surfaces: list[str] = Field(default_factory=list)


class TargetCapabilityReport(VssModel):
    target: TargetName
    adapterVersion: str = Field(min_length=1)
    surfaces: list[TargetSurface] = Field(default_factory=list)
    schemaFeatures: list[SchemaFeatureSupport] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class SceneFeatureAssessment(VssModel):
    featureId: str = Field(min_length=1)
    label: str = Field(min_length=1)
    presentCount: int = Field(ge=0)
    support: SupportLevel
    notes: str = Field(min_length=1)


class SceneTargetAssessment(VssModel):
    target: TargetName
    sceneId: str = Field(min_length=1)
    objectCount: int = Field(ge=0)
    supportedCount: int = Field(ge=0)
    partialCount: int = Field(ge=0)
    unsupportedCount: int = Field(ge=0)
    features: list[SceneFeatureAssessment] = Field(default_factory=list)


_CAPABILITY_CONTRACT_PATH = Path(__file__).resolve().parents[2] / "targets" / "capabilities" / "target-capabilities.json"
_SCENE_FEATURE_COUNT_RULES_PATH = Path(__file__).resolve().parents[2] / "targets" / "capabilities" / "scene-feature-counts.json"


@lru_cache(maxsize=1)
def _load_capability_contracts() -> dict[TargetName, TargetCapabilityReport]:
    payload = json.loads(_CAPABILITY_CONTRACT_PATH.read_text(encoding="utf-8"))
    return {
        key: TargetCapabilityReport.model_validate(value)
        for key, value in payload.items()
    }


def get_target_capabilities(target: TargetName) -> TargetCapabilityReport:
    return _load_capability_contracts()[target]


def assess_scene_for_target(scene: VssScene, target: TargetName) -> SceneTargetAssessment:
    report = get_target_capabilities(target)
    counts = _scene_feature_counts(scene)
    features: list[SceneFeatureAssessment] = []
    supported_count = 0
    partial_count = 0
    unsupported_count = 0
    for item in report.schemaFeatures:
        present_count = counts.get(item.featureId, 0)
        if present_count <= 0:
            continue
        features.append(
            SceneFeatureAssessment(
                featureId=item.featureId,
                label=item.label,
                presentCount=present_count,
                support=item.support,
                notes=item.notes,
            )
        )
        if item.support == "strong":
            supported_count += present_count
        elif item.support == "partial":
            partial_count += present_count
        else:
            unsupported_count += present_count
    return SceneTargetAssessment(
        target=target,
        sceneId=scene.document.id,
        objectCount=len(scene.objects),
        supportedCount=supported_count,
        partialCount=partial_count,
        unsupportedCount=unsupported_count,
        features=features,
    )


def _scene_feature_counts(scene: VssScene) -> dict[str, int]:
    rules = _load_scene_feature_count_rules()
    return {feature_id: _evaluate_scene_feature_count(scene, rule) for feature_id, rule in rules.items()}


@lru_cache(maxsize=1)
def _load_scene_feature_count_rules() -> dict[str, dict[str, Any]]:
    return json.loads(_SCENE_FEATURE_COUNT_RULES_PATH.read_text(encoding="utf-8"))


def _evaluate_scene_feature_count(scene: VssScene, rule: dict[str, Any]) -> int:
    kind = rule["kind"]
    if kind == "constant":
        return int(rule["value"])
    if kind == "object_attr":
        attr = rule["attr"]
        return sum(1 for obj in scene.objects if getattr(obj, attr, None) is not None)
    if kind == "entity_count":
        return len(scene.entities)
    if kind == "entity_attr":
        attr = rule["attr"]
        return sum(1 for entity in scene.entities if getattr(entity, attr, None) is not None)
    if kind == "style_attr":
        attr = rule["attr"]
        return sum(
            1
            for obj in scene.objects
            if (style := getattr(obj, "style", None)) is not None and getattr(style, attr, None) is not None
        )
    if kind == "scene_path_count":
        return len(scene.paths)
    if kind == "scene_track_count":
        return len(scene.tracks)
    if kind == "scene_vector_count":
        return len(scene.vectors)
    if kind == "scene_velocity_vector_count":
        return len(scene.velocityVectors)
    if kind == "scene_acceleration_vector_count":
        return len(scene.accelerationVectors)
    if kind == "scene_line_of_sight_count":
        return len(scene.lineOfSights)
    if kind == "scene_body_axes_count":
        return len(scene.bodyAxes)
    if kind == "scene_principal_axes_count":
        return len(scene.principalAxes)
    if kind == "scene_relative_line_count":
        return len(scene.relativeLines)
    if kind == "scene_intercept_line_count":
        return len(scene.interceptLines)
    if kind == "scene_camera_view_count":
        return len(scene.cameraViews)
    if kind == "scene_view_count":
        return len(scene.views)
    if kind == "scene_custom_object_count":
        return len(scene.customObjects)
    if kind == "scene_runtime_object_count":
        return len(scene.runtimeObjects)
    if kind == "scene_terrain_surface_count":
        return len(scene.terrainSurfaces)
    if kind == "scene_custom_mesh_count":
        return len(scene.customMeshes)
    if kind == "scene_clipping_plane_count":
        return len(scene.clippingPlanes)
    if kind == "scene_clipping_polygon_count":
        return len(scene.clippingPolygons)
    if kind == "scene_classification_volume_count":
        return len(scene.classificationVolumes)
    if kind == "scene_custom_shader_count":
        return len(scene.customShaders)
    if kind == "scene_post_process_stage_count":
        return len(scene.postProcessStages)
    if kind == "overlay_geometry":
        geometry_type = rule["geometryType"]
        attr = rule["attr"]
        return sum(
            1
            for overlay in scene.overlays
            if overlay.geometryType == geometry_type and getattr(overlay, attr, None) is not None
        )
    if kind == "entity_category":
        category = rule["category"]
        return sum(1 for entity in scene.entities if entity.category is not None and entity.category.value == category)
    raise ValueError(f"unknown scene feature count rule kind: {kind}")


def get_cesium_capabilities() -> TargetCapabilityReport:
    return get_target_capabilities("cesium")


def get_simdis_capabilities() -> TargetCapabilityReport:
    return get_target_capabilities("simdis")


def get_soap_capabilities() -> TargetCapabilityReport:
    return get_target_capabilities("soap")


def assess_cesium_scene_support(scene: VssScene) -> SceneTargetAssessment:
    return assess_scene_for_target(scene, "cesium")


def assess_simdis_scene_support(scene: VssScene) -> SceneTargetAssessment:
    return assess_scene_for_target(scene, "simdis")


def assess_soap_scene_support(scene: VssScene) -> SceneTargetAssessment:
    return assess_scene_for_target(scene, "soap")


__all__ = [
    "SceneFeatureAssessment",
    "SceneTargetAssessment",
    "SchemaFeatureSupport",
    "TargetCapabilityReport",
    "TargetSurface",
    "assess_cesium_scene_support",
    "assess_scene_for_target",
    "assess_simdis_scene_support",
    "assess_soap_scene_support",
    "get_cesium_capabilities",
    "get_simdis_capabilities",
    "get_soap_capabilities",
    "get_target_capabilities",
]
