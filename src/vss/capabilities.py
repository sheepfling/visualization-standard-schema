from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Literal

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
    entity_count = len(scene.entities)
    overlay_polyline_count = sum(1 for overlay in scene.overlays if overlay.geometryType == "polyline" and overlay.polyline is not None)
    overlay_polygon_count = sum(1 for overlay in scene.overlays if overlay.geometryType == "polygon" and overlay.polygon is not None)
    overlay_corridor_count = sum(1 for overlay in scene.overlays if overlay.geometryType == "corridor" and overlay.corridor is not None)
    overlay_ellipse_count = sum(1 for overlay in scene.overlays if overlay.geometryType == "ellipse" and overlay.ellipse is not None)
    overlay_circle_count = sum(1 for overlay in scene.overlays if overlay.geometryType == "circle" and overlay.circle is not None)
    counts = {
        "document.metadata": 1,
        "clock.timestamps": sum(1 for obj in scene.objects if obj.timestamp is not None),
        "object.entity.position": entity_count,
        "object.entity.orientation": sum(1 for entity in scene.entities if entity.orientation is not None),
        "style.label": sum(1 for obj in scene.objects if obj.style is not None and obj.style.label is not None),
        "style.icon": sum(1 for obj in scene.objects if obj.style is not None and obj.style.iconUri is not None),
        "style.model": sum(1 for obj in scene.objects if obj.style is not None and obj.style.modelUri is not None),
        "style.color": sum(1 for obj in scene.objects if obj.style is not None and obj.style.colorRgba is not None),
        "object.path.sampledMotion": len(scene.paths),
        "object.track.sampledMotion": len(scene.tracks),
        "object.rectangle.geometry": sum(1 for overlay in scene.overlays if overlay.geometryType == "rectangle" and overlay.rectangle is not None),
        "object.overlay.polyline": overlay_polyline_count,
        "object.overlay.polygon": overlay_polygon_count,
        "object.corridor.geometry": overlay_corridor_count,
        "object.ellipse.geometry": overlay_ellipse_count,
        "object.circle.geometry": overlay_circle_count,
        "object.sensor": sum(1 for entity in scene.entities if entity.category is not None and entity.category.value == "sensor"),
        "views": 0,
        "analysis": 0,
        "presentation": 0,
    }
    return counts


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
