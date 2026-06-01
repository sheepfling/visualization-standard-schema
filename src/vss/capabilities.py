from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Callable, Literal

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
_SceneFeatureCounter = Callable[[VssScene], int]


def _count_object_attr(scene: VssScene, attr_name: str) -> int:
    return sum(1 for obj in scene.objects if getattr(obj, attr_name) is not None)


def _count_overlay_geometry(scene: VssScene, geometry_type: str, attr_name: str) -> int:
    return sum(
        1
        for overlay in scene.overlays
        if overlay.geometryType == geometry_type and getattr(overlay, attr_name) is not None
    )


def _count_style_attr(scene: VssScene, attr_name: str) -> int:
    return sum(1 for obj in scene.objects if obj.style is not None and getattr(obj.style, attr_name) is not None)


_SCENE_FEATURE_COUNTERS: dict[str, _SceneFeatureCounter] = {
    "document.metadata": lambda scene: 1,
    "clock.timestamps": lambda scene: _count_object_attr(scene, "timestamp"),
    "object.entity.position": lambda scene: len(scene.entities),
    "object.entity.orientation": lambda scene: sum(1 for entity in scene.entities if entity.orientation is not None),
    "style.label": lambda scene: _count_style_attr(scene, "label"),
    "style.icon": lambda scene: _count_style_attr(scene, "iconUri"),
    "style.model": lambda scene: _count_style_attr(scene, "modelUri"),
    "style.color": lambda scene: _count_style_attr(scene, "colorRgba"),
    "object.path.sampledMotion": lambda scene: len(scene.paths),
    "object.track.sampledMotion": lambda scene: len(scene.tracks),
    "object.rectangle.geometry": lambda scene: _count_overlay_geometry(scene, "rectangle", "rectangle"),
    "object.overlay.polyline": lambda scene: _count_overlay_geometry(scene, "polyline", "polyline"),
    "object.overlay.polygon": lambda scene: _count_overlay_geometry(scene, "polygon", "polygon"),
    "object.corridor.geometry": lambda scene: _count_overlay_geometry(scene, "corridor", "corridor"),
    "object.ellipse.geometry": lambda scene: _count_overlay_geometry(scene, "ellipse", "ellipse"),
    "object.circle.geometry": lambda scene: _count_overlay_geometry(scene, "circle", "circle"),
    "object.wall.geometry": lambda scene: _count_overlay_geometry(scene, "wall", "wall"),
    "object.box.geometry": lambda scene: _count_overlay_geometry(scene, "box", "box"),
    "object.sensor": lambda scene: sum(1 for entity in scene.entities if entity.category is not None and entity.category.value == "sensor"),
    "views": lambda scene: 0,
    "analysis": lambda scene: 0,
    "presentation": lambda scene: 0,
}


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
    return {feature_id: counter(scene) for feature_id, counter in _SCENE_FEATURE_COUNTERS.items()}


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
