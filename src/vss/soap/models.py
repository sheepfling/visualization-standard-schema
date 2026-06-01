from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from ..models import VssModel


class SoapArtifact(VssModel):
    kind: str = Field(min_length=1)
    path: str = Field(min_length=1)


class SoapManifest(VssModel):
    target: Literal["soap"] = "soap"
    source: str = Field(min_length=1)
    mode: str = Field(min_length=1)
    profiles: list[str] = Field(default_factory=list)
    artifacts: list[SoapArtifact] = Field(default_factory=list)
    totals: dict[str, Any] = Field(default_factory=dict)


class SoapPlatform(VssModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    kind: Literal["Platform"] = "Platform"
    initialState: dict[str, Any] = Field(default_factory=dict)
    properties: dict[str, Any] = Field(default_factory=dict)


class SoapTrajectory(VssModel):
    id: str = Field(min_length=1)
    platformId: str = Field(min_length=1)
    source: str = Field(min_length=1)
    samples: list[dict[str, Any]] = Field(default_factory=list)


class SoapOverlayStyle(VssModel):
    label: str | None = None
    colorRgba: list[int] = Field(default_factory=list)
    widthPx: float | None = None
    clampToGround: bool = False


class SoapOverlayPoint(VssModel):
    longitudeDeg: float
    latitudeDeg: float
    altitudeM: float


class SoapOverlay(VssModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    kind: Literal["polyline", "polygon"]
    style: SoapOverlayStyle = Field(default_factory=SoapOverlayStyle)
    positions: list[SoapOverlayPoint] = Field(default_factory=list)
    properties: dict[str, Any] = Field(default_factory=dict)


class SoapModel(VssModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    kind: Literal["Model"] = "Model"
    uri: str = Field(min_length=1)
    position: dict[str, Any] = Field(default_factory=dict)
    properties: dict[str, Any] = Field(default_factory=dict)


class SoapSensorSwath(VssModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    kind: Literal["SensorSwath"] = "SensorSwath"
    hostId: str | None = None
    position: dict[str, Any] = Field(default_factory=dict)
    style: SoapOverlayStyle = Field(default_factory=SoapOverlayStyle)
    properties: dict[str, Any] = Field(default_factory=dict)


class SoapView(VssModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    kind: Literal["View"] = "View"
    target: str | None = None
    camera: dict[str, Any] = Field(default_factory=dict)


class SoapPalette(VssModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    entries: list[dict[str, Any]] = Field(default_factory=list)


class SoapScenario(VssModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    clock: dict[str, Any] = Field(default_factory=dict)
    units: dict[str, Any] = Field(default_factory=dict)
    platforms: list[SoapPlatform] = Field(default_factory=list)
    trajectories: list[SoapTrajectory] = Field(default_factory=list)
    models: list[SoapModel] = Field(default_factory=list)
    sensorSwaths: list[SoapSensorSwath] = Field(default_factory=list)
    overlays: list[SoapOverlay] = Field(default_factory=list)
    extensions: dict[str, Any] = Field(default_factory=dict)


class SoapViews(VssModel):
    views: list[SoapView] = Field(default_factory=list)
    palettes: list[SoapPalette] = Field(default_factory=list)


class SoapAnalysis(VssModel):
    results: list[dict[str, Any]] = Field(default_factory=list)


class SoapPresentation(VssModel):
    presentation: dict[str, Any] | None = None
    slides: list[dict[str, Any]] = Field(default_factory=list)
    actions: list[dict[str, Any]] = Field(default_factory=list)


class SoapAsset(VssModel):
    id: str = Field(min_length=1)
    path: str | None = None
    kind: str | None = None
    uri: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SoapAssets(VssModel):
    assets: list[SoapAsset] = Field(default_factory=list)


class SoapDiagnostic(VssModel):
    severity: str = Field(min_length=1)
    code: str = Field(min_length=1)
    path: str = Field(min_length=1)
    message: str = Field(min_length=1)


class SoapBundle(VssModel):
    target: Literal["soap"] = "soap"
    source: str = Field(min_length=1)
    manifest: SoapManifest
    scenario: SoapScenario
    views: SoapViews = Field(default_factory=SoapViews)
    analysis: SoapAnalysis = Field(default_factory=SoapAnalysis)
    presentation: SoapPresentation = Field(default_factory=SoapPresentation)
    assets: SoapAssets = Field(default_factory=SoapAssets)
    diagnostics: list[SoapDiagnostic] = Field(default_factory=list)
    overlays: list[str] = Field(default_factory=list)
