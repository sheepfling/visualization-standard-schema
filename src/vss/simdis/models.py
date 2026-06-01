from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from ..models import VssModel


class SimdisArtifact(VssModel):
    kind: str = Field(min_length=1)
    path: str = Field(min_length=1)


class SimdisManifest(VssModel):
    target: Literal["simdis"] = "simdis"
    source: str = Field(min_length=1)
    mode: str = Field(min_length=1)
    profiles: list[str] = Field(default_factory=list)
    artifacts: list[SimdisArtifact] = Field(default_factory=list)
    totals: dict[str, Any] = Field(default_factory=dict)


class SimdisPosition(VssModel):
    frame: str | None = None
    lon: float | None = None
    lat: float | None = None
    alt: float | None = None
    reference: str | None = None
    sampled: bool | None = None
    epoch: str | None = None
    valueFormat: str | None = None


class SimdisTrajectorySample(VssModel):
    t: float | int | str
    valueFormat: str = "cartesianMeters"
    referenceFrame: str = "FIXED"
    value: list[Any] = Field(default_factory=list)


class SimdisPlatformState(VssModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    kind: Literal["platform"] = "platform"
    category: str = "platform"
    trajectory: list[SimdisTrajectorySample] = Field(default_factory=list)
    initialPosition: SimdisPosition | None = None
    orientation: dict[str, Any] = Field(default_factory=dict)
    label: dict[str, Any] = Field(default_factory=dict)
    trackHistory: bool = True
    properties: dict[str, Any] = Field(default_factory=dict)


class SimdisAnnotationState(VssModel):
    id: str = Field(min_length=1)
    kind: str = Field(min_length=1)
    name: str = Field(min_length=1)
    position: SimdisPosition | None = None
    label: dict[str, Any] = Field(default_factory=dict)
    billboard: dict[str, Any] = Field(default_factory=dict)
    point: dict[str, Any] = Field(default_factory=dict)
    show: bool = True


class SimdisSensorState(VssModel):
    id: str = Field(min_length=1)
    kind: str = Field(min_length=1)
    name: str = Field(min_length=1)
    hostId: str | None = None
    pose: dict[str, Any] = Field(default_factory=dict)
    geometry: dict[str, Any] = Field(default_factory=dict)
    style: dict[str, Any] = Field(default_factory=dict)
    show: bool = True
    simdisTarget: str = Field(min_length=1)


class SimdisBeamSample(VssModel):
    time: str = Field(min_length=1)
    on: bool | None = None
    color: str | None = None
    az: float | None = None
    el: float | None = None
    rangeMeters: float | None = None
    targetPlatformId: str | None = None


class SimdisBeamState(VssModel):
    id: str = Field(min_length=1)
    hostPlatformId: str = Field(min_length=1)
    kind: Literal["beam"] = "beam"
    type: str = "BODY"
    horzBW: float | None = None
    vertBW: float | None = None
    samples: list[SimdisBeamSample] = Field(default_factory=list)


class SimdisGateSample(VssModel):
    time: str = Field(min_length=1)
    on: bool | None = None
    color: str | None = None
    az: float | None = None
    el: float | None = None
    width: float | None = None
    height: float | None = None
    minRangeMeters: float | None = None
    maxRangeMeters: float | None = None
    centroidMeters: float | None = None


class SimdisGateState(VssModel):
    id: str = Field(min_length=1)
    hostBeamId: str = Field(min_length=1)
    kind: Literal["gate"] = "gate"
    type: str = "BODY"
    samples: list[SimdisGateSample] = Field(default_factory=list)


class SimdisProjectorSample(VssModel):
    time: str = Field(min_length=1)
    on: bool | None = None
    fovDegrees: float | None = None


class SimdisProjectorState(VssModel):
    id: str = Field(min_length=1)
    hostPlatformId: str = Field(min_length=1)
    kind: Literal["projector"] = "projector"
    rasterFile: str | None = None
    interpolateFov: bool = True
    samples: list[SimdisProjectorSample] = Field(default_factory=list)


class SimdisGogVertex(VssModel):
    mode: str = Field(min_length=1)
    values: list[float] = Field(default_factory=list)


class SimdisGogShape(VssModel):
    id: str = Field(min_length=1)
    kind: str = Field(min_length=1)
    name: str | None = None
    vertices: list[SimdisGogVertex] = Field(default_factory=list)
    properties: dict[str, Any] = Field(default_factory=dict)
    attachments: dict[str, Any] = Field(default_factory=dict)


class SimdisGogDocument(VssModel):
    source: str | None = None
    shapes: list[SimdisGogShape] = Field(default_factory=list)


class SimdisVectorState(VssModel):
    id: str = Field(min_length=1)
    kind: str = Field(min_length=1)
    name: str = Field(min_length=1)
    geometry: dict[str, Any] = Field(default_factory=dict)
    style: dict[str, Any] = Field(default_factory=dict)
    show: bool = True


class SimdisOverlayPoint(VssModel):
    lon: float
    lat: float
    alt: float


class SimdisOverlayGeometry(VssModel):
    type: Literal["polyline", "polygon"]
    clampToGround: bool = False
    widthPx: float | None = None
    positions: list[SimdisOverlayPoint] = Field(default_factory=list)


class SimdisOverlayState(VssModel):
    id: str = Field(min_length=1)
    kind: Literal["overlay"] = "overlay"
    name: str = Field(min_length=1)
    geometry: SimdisOverlayGeometry
    style: dict[str, Any] = Field(default_factory=dict)
    show: bool = True


class SimdisEntities(VssModel):
    platforms: list[SimdisPlatformState] = Field(default_factory=list)
    annotations: list[SimdisAnnotationState] = Field(default_factory=list)
    sensors: list[SimdisSensorState] = Field(default_factory=list)
    beams: list[SimdisBeamState] = Field(default_factory=list)
    gates: list[SimdisGateState] = Field(default_factory=list)
    projectors: list[SimdisProjectorState] = Field(default_factory=list)
    vectors: list[SimdisVectorState] = Field(default_factory=list)
    overlays: list[SimdisOverlayState] = Field(default_factory=list)


class SimdisAnalysis(VssModel):
    results: list[dict[str, Any]] = Field(default_factory=list)


class SimdisView(VssModel):
    id: str = Field(min_length=1)
    kind: str = Field(min_length=1)
    name: str | None = None
    target: str | None = None


class SimdisSlide(VssModel):
    id: str = Field(min_length=1)
    title: str | None = None
    startTime: str | None = None
    stopTime: str | None = None
    views: list[Any] = Field(default_factory=list)


class SimdisCameraAction(VssModel):
    id: str = Field(min_length=1)
    target: str | None = None
    camera: dict[str, Any] = Field(default_factory=dict)
    durationSeconds: float | int | None = None


class SimdisPopup(VssModel):
    id: str = Field(min_length=1)
    kind: str = Field(min_length=1)
    title: str | None = None
    target: str | None = None


class SimdisPresentation(VssModel):
    views: list[SimdisView] = Field(default_factory=list)
    slides: list[SimdisSlide] = Field(default_factory=list)
    cameraActions: list[SimdisCameraAction] = Field(default_factory=list)
    popups: list[SimdisPopup] = Field(default_factory=list)


class SimdisAsset(VssModel):
    id: str = Field(min_length=1)
    path: str | None = None
    kind: str | None = None
    uri: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SimdisAssets(VssModel):
    assets: list[SimdisAsset] = Field(default_factory=list)


class SimdisDiagnostic(VssModel):
    severity: str = Field(min_length=1)
    code: str = Field(min_length=1)
    path: str = Field(min_length=1)
    message: str = Field(min_length=1)


class SimdisBundle(VssModel):
    target: Literal["simdis"] = "simdis"
    source: str = Field(min_length=1)
    manifest: SimdisManifest
    scenarioAsi: str = ""
    entities: SimdisEntities = Field(default_factory=SimdisEntities)
    overlaysGog: str = "gog version 2\n"
    analysis: SimdisAnalysis = Field(default_factory=SimdisAnalysis)
    presentation: SimdisPresentation = Field(default_factory=SimdisPresentation)
    assets: SimdisAssets = Field(default_factory=SimdisAssets)
    diagnostics: list[SimdisDiagnostic] = Field(default_factory=list)
