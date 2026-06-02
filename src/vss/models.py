from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, HttpUrl


class VssModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EntityCategory(str, Enum):
    AIR = "air"
    GROUND = "ground"
    SURFACE = "surface"
    SUBSURFACE = "subsurface"
    SPACE = "space"
    SENSOR = "sensor"
    OVERLAY = "overlay"
    OTHER = "other"


class Wgs84Position(VssModel):
    longitudeDeg: float = Field(ge=-180, le=180)
    latitudeDeg: float = Field(ge=-90, le=90)
    altitudeM: float


class Orientation(VssModel):
    headingDeg: float | None = None
    pitchDeg: float | None = None
    rollDeg: float | None = None


class Style(VssModel):
    label: str | None = None
    iconUri: HttpUrl | None = None
    modelUri: HttpUrl | None = None
    colorRgba: tuple[int, int, int, int] | None = None


class ScenePolyline(VssModel):
    positions: list[Wgs84Position] = Field(min_length=2)
    widthPx: float = Field(default=2.0, gt=0)
    clampToGround: bool = False


class ScenePolygon(VssModel):
    positions: list[Wgs84Position] = Field(min_length=3)
    clampToGround: bool = False


class SceneRectangle(VssModel):
    westSouthEastNorthDegrees: tuple[float, float, float, float]
    heightMeters: float | None = None
    extrudedHeightMeters: float | None = None
    rotationDegrees: float | None = None
    stRotationDegrees: float | None = None


class SceneEllipse(VssModel):
    semiMajorAxisMeters: float = Field(gt=0)
    semiMinorAxisMeters: float = Field(gt=0)
    heightMeters: float | None = None
    extrudedHeightMeters: float | None = None
    rotationDegrees: float | None = None
    stRotationDegrees: float | None = None
    clampToGround: bool = False


class SceneCircle(VssModel):
    radiusMeters: float = Field(gt=0)
    heightMeters: float | None = None
    extrudedHeightMeters: float | None = None
    rotationDegrees: float | None = None
    stRotationDegrees: float | None = None
    clampToGround: bool = False


class SceneRangeRing(VssModel):
    radiusMeters: float = Field(gt=0)
    heightMeters: float | None = None
    extrudedHeightMeters: float | None = None
    rotationDegrees: float | None = None
    stRotationDegrees: float | None = None
    clampToGround: bool = False
    outlineWidthPx: float = Field(default=1.0, gt=0)


class SceneCorridor(VssModel):
    positions: list[Wgs84Position] = Field(min_length=2)
    widthMeters: float = Field(gt=0)
    heightMeters: float | None = None
    extrudedHeightMeters: float | None = None
    cornerType: Literal["rounded", "mitered", "beveled"] | None = None
    clampToGround: bool = False


class SceneWall(VssModel):
    positions: list[Wgs84Position] = Field(min_length=2)
    minimumHeightsMeters: list[float] | None = None
    maximumHeightsMeters: list[float] | None = None
    clampToGround: bool = False


class SceneBox(VssModel):
    dimensionsMeters: tuple[float, float, float]


class SceneCylinder(VssModel):
    lengthMeters: float = Field(gt=0)
    topRadiusMeters: float = Field(ge=0)
    bottomRadiusMeters: float = Field(ge=0)
    numberOfSides: int | None = Field(default=None, ge=3)
    slope: float | None = None


class SceneCone(VssModel):
    radiusMeters: float = Field(gt=0)
    innerHalfAngleDegrees: float = Field(ge=0, le=90)
    outerHalfAngleDegrees: float = Field(ge=0, le=90)
    minimumClockAngleDegrees: float | None = Field(default=None, ge=0, le=360)
    maximumClockAngleDegrees: float | None = Field(default=None, ge=0, le=360)
    showIntersection: bool | None = None
    intersectionWidthPx: float | None = Field(default=None, gt=0)


class SceneConicSensor(VssModel):
    radiusMeters: float = Field(gt=0)
    innerHalfAngleDegrees: float = Field(ge=0, le=90)
    outerHalfAngleDegrees: float = Field(ge=0, le=90)
    minimumClockAngleDegrees: float | None = Field(default=None, ge=0, le=360)
    maximumClockAngleDegrees: float | None = Field(default=None, ge=0, le=360)
    showIntersection: bool | None = None
    intersectionWidthPx: float | None = Field(default=None, gt=0)


class SceneRectangularSensor(VssModel):
    radiusMeters: float = Field(gt=0)
    xHalfAngleDegrees: float = Field(ge=0, le=90)
    yHalfAngleDegrees: float = Field(ge=0, le=90)
    showIntersection: bool | None = None
    intersectionWidthPx: float | None = Field(default=None, gt=0)
    showLateralSurfaces: bool | None = None
    showDomeSurfaces: bool | None = None


class SceneFrustum(VssModel):
    nearMeters: float = Field(gt=0)
    farMeters: float = Field(gt=0)
    horizontalFovDegrees: float | None = Field(default=None, gt=0, le=180)
    verticalFovDegrees: float | None = Field(default=None, gt=0, le=180)
    innerHalfAngleDegrees: float | None = Field(default=None, ge=0, le=90)
    outerHalfAngleDegrees: float | None = Field(default=None, ge=0, le=90)
    aspectRatio: float | None = Field(default=None, gt=0)
    windingOrder: Literal["counterClockwise", "clockwise"] | None = None
    closed: bool | None = None


class SceneSector2D(VssModel):
    innerRadiusMeters: float | None = Field(default=None, ge=0)
    outerRadiusMeters: float = Field(gt=0)
    azimuthStartDegrees: float
    azimuthStopDegrees: float
    elevationStartDegrees: float | None = None
    elevationStopDegrees: float | None = None
    heightMeters: float | None = None
    segments: int = Field(default=32, ge=3)
    mode: Literal["surface", "flatLocal", "volume"] | None = None
    windingOrder: Literal["counterClockwise", "clockwise"] | None = None
    closed: bool | None = None


class SceneBearingFan(VssModel):
    innerRadiusMeters: float | None = Field(default=None, ge=0)
    outerRadiusMeters: float = Field(gt=0)
    azimuthStartDegrees: float
    azimuthStopDegrees: float
    elevationStartDegrees: float | None = None
    elevationStopDegrees: float | None = None
    heightMeters: float | None = None
    segments: int = Field(default=24, ge=3)
    mode: Literal["surface", "flatLocal", "volume"] | None = None
    windingOrder: Literal["counterClockwise", "clockwise"] | None = None
    closed: bool | None = None


class SceneCustomPatternSensor(VssModel):
    innerRadiusMeters: float | None = Field(default=None, ge=0)
    outerRadiusMeters: float = Field(gt=0)
    azimuthStartDegrees: float
    azimuthStopDegrees: float
    elevationStartDegrees: float | None = None
    elevationStopDegrees: float | None = None
    patternAzimuthElevationDegrees: list[tuple[float, float]] = Field(default_factory=list)
    heightMeters: float | None = None
    segments: int = Field(default=24, ge=3)
    mode: Literal["surface", "flatLocal", "volume"] | None = None
    windingOrder: Literal["counterClockwise", "clockwise"] | None = None
    closed: bool | None = None


class SceneFan(VssModel):
    innerRadiusMeters: float | None = Field(default=None, ge=0)
    outerRadiusMeters: float = Field(gt=0)
    azimuthStartDegrees: float
    azimuthStopDegrees: float
    elevationStartDegrees: float | None = None
    elevationStopDegrees: float | None = None
    heightMeters: float | None = None
    segments: int = Field(default=24, ge=3)
    mode: Literal["surface", "flatLocal", "volume"] | None = None
    windingOrder: Literal["counterClockwise", "clockwise"] | None = None
    closed: bool | None = None


class SceneSectorVolume(VssModel):
    innerRadiusMeters: float | None = Field(default=None, ge=0)
    outerRadiusMeters: float = Field(gt=0)
    azimuthStartDegrees: float
    azimuthStopDegrees: float
    elevationStartDegrees: float | None = None
    elevationStopDegrees: float | None = None
    heightMeters: float | None = None
    segments: int = Field(default=32, ge=3)
    mode: Literal["surface", "flatLocal", "volume"] | None = None
    windingOrder: Literal["counterClockwise", "clockwise"] | None = None
    closed: bool | None = None


class SceneKeyhole(VssModel):
    innerRadiusMeters: float = Field(ge=0)
    outerRadiusMeters: float = Field(gt=0)
    azimuthStartDegrees: float
    azimuthStopDegrees: float
    elevationStartDegrees: float | None = None
    elevationStopDegrees: float | None = None
    segments: int = Field(default=32, ge=3)
    mode: Literal["surface", "flatLocal", "volume"] | None = None
    windingOrder: Literal["counterClockwise", "clockwise"] | None = None
    closed: bool | None = None


class SceneHemisphere(VssModel):
    radiusMeters: float = Field(gt=0)


class SceneSphericalCap(VssModel):
    radiusMeters: float = Field(gt=0)
    innerRadiusMeters: float | None = Field(default=None, ge=0)
    portion: Literal["upper", "lower", "front", "rear", "left", "right"] | None = None
    azimuthStartDegrees: float | None = None
    azimuthStopDegrees: float | None = None
    segments: int | None = Field(default=None, ge=3)
    windingOrder: Literal["counterClockwise", "clockwise"] | None = None
    closed: bool | None = None
    azimuthSegments: int | None = Field(default=None, ge=3)
    elevationSegments: int | None = Field(default=None, ge=1)
    elevationStartDegrees: float | None = None
    elevationStopDegrees: float | None = None


class SceneParticleSystem(VssModel):
    asset: str | None = None
    image: str | None = None
    emitter: dict[str, Any] | None = None
    emissionRate: float | None = Field(default=None, ge=0)
    lifetimeSeconds: float | None = Field(default=None, ge=0)
    particleLifeSeconds: float | None = Field(default=None, ge=0)
    minimumParticleLifeSeconds: float | None = Field(default=None, ge=0)
    maximumParticleLifeSeconds: float | None = Field(default=None, ge=0)
    speedMetersPerSecond: float | None = None
    minimumSpeedMetersPerSecond: float | None = None
    maximumSpeedMetersPerSecond: float | None = None
    scale: float | None = Field(default=None, gt=0)
    startScale: float | None = Field(default=None, gt=0)
    endScale: float | None = Field(default=None, gt=0)
    imageSize: tuple[float, float] | None = None
    startColor: tuple[float, float, float, float] | None = None
    endColor: tuple[float, float, float, float] | None = None


class SceneVoxel(VssModel):
    semanticKind: str | None = None
    grid: dict[str, Any] = Field(default_factory=dict)
    dimensionsMeters: tuple[float, float, float] | None = None
    note: str | None = None
    extensions: dict[str, Any] = Field(default_factory=dict)


class ScenePolylineVolume(VssModel):
    positions: list[Wgs84Position] = Field(min_length=2)
    shapePositions: list[tuple[float, float]] = Field(min_length=3)
    cornerType: Literal["rounded", "mitered", "beveled"] | None = None


class ScenePlane(VssModel):
    normal: tuple[float, float, float]
    distanceMeters: float
    widthMeters: float = Field(gt=0)
    heightMeters: float = Field(gt=0)


class SceneTileset(VssModel):
    uri: str = Field(min_length=1)


class SceneEllipsoid(VssModel):
    radiiMeters: tuple[float, float, float]


class SceneSphere(VssModel):
    radiusMeters: float = Field(gt=0)


class SceneUncertaintyEllipsoid(VssModel):
    radiiMeters: tuple[float, float, float]
    slicePartitions: int | None = Field(default=None, ge=1)
    stackPartitions: int | None = Field(default=None, ge=1)


class SceneCovarianceEllipse(VssModel):
    semiMajorAxisMeters: float = Field(gt=0)
    semiMinorAxisMeters: float = Field(gt=0)
    heightMeters: float | None = None
    extrudedHeightMeters: float | None = None
    rotationDegrees: float | None = None
    stRotationDegrees: float | None = None
    clampToGround: bool = False


class SceneVector(VssModel):
    objectType: Literal["vector"] = "vector"
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    startPosition: Wgs84Position
    endPosition: Wgs84Position
    widthPx: float = Field(default=2.0, gt=0)
    clampToGround: bool = False
    style: Style | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    source: str | None = None
    timestamp: datetime | None = None


class SceneVelocityVector(VssModel):
    objectType: Literal["velocityVector"] = "velocityVector"
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    startPosition: Wgs84Position
    endPosition: Wgs84Position
    widthPx: float = Field(default=2.0, gt=0)
    clampToGround: bool = False
    style: Style | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    source: str | None = None
    timestamp: datetime | None = None


class SceneAccelerationVector(VssModel):
    objectType: Literal["accelerationVector"] = "accelerationVector"
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    startPosition: Wgs84Position
    endPosition: Wgs84Position
    widthPx: float = Field(default=2.0, gt=0)
    clampToGround: bool = False
    style: Style | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    source: str | None = None
    timestamp: datetime | None = None


class SceneLineOfSight(VssModel):
    objectType: Literal["lineOfSight"] = "lineOfSight"
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    startPosition: Wgs84Position
    endPosition: Wgs84Position
    widthPx: float = Field(default=2.0, gt=0)
    clampToGround: bool = False
    style: Style | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    source: str | None = None
    timestamp: datetime | None = None


class SceneBodyAxes(VssModel):
    objectType: Literal["bodyAxes"] = "bodyAxes"
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    originPosition: Wgs84Position
    axisLengthsMeters: tuple[float, float, float]
    orientation: Orientation | None = None
    style: Style | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    source: str | None = None
    timestamp: datetime | None = None


class ScenePrincipalAxes(VssModel):
    objectType: Literal["principalAxes"] = "principalAxes"
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    originPosition: Wgs84Position
    axisLengthsMeters: tuple[float, float, float]
    orientation: Orientation | None = None
    style: Style | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    source: str | None = None
    timestamp: datetime | None = None


class SceneRelativeLine(VssModel):
    objectType: Literal["relativeLine"] = "relativeLine"
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    startPosition: Wgs84Position
    endPosition: Wgs84Position
    widthPx: float = Field(default=2.0, gt=0)
    clampToGround: bool = False
    style: Style | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    source: str | None = None
    timestamp: datetime | None = None


class SceneInterceptLine(VssModel):
    objectType: Literal["interceptLine"] = "interceptLine"
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    startPosition: Wgs84Position
    endPosition: Wgs84Position
    widthPx: float = Field(default=2.0, gt=0)
    clampToGround: bool = False
    style: Style | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    source: str | None = None
    timestamp: datetime | None = None


class SceneView(VssModel):
    id: str = Field(min_length=1)
    name: str | None = None
    target: str | None = None
    position: Wgs84Position | None = None
    orientation: Orientation | None = None
    rangeMeters: float | None = Field(default=None, gt=0)
    durationSeconds: float | None = Field(default=None, gt=0)
    rendererHints: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime | None = None


class SceneCameraView(SceneView):
    objectType: Literal["cameraView"] = "cameraView"
    style: Style | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    source: str | None = None


class EntityUpsertPayload(VssModel):
    entityId: str = Field(min_length=1)
    name: str = Field(min_length=1)
    category: EntityCategory | None = None
    position: Wgs84Position
    orientation: Orientation | None = None
    style: Style | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)


class EntityUpsertMessage(VssModel):
    schemaVersion: Literal["1.0.0"]
    messageType: Literal["entity.upsert"]
    messageId: str = Field(min_length=1)
    timestamp: datetime
    source: str = Field(min_length=1)
    payload: EntityUpsertPayload

    @classmethod
    def export_json_schema(cls) -> dict[str, Any]:
        return cls.model_json_schema()


class SceneDocument(VssModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str | None = None
    created: datetime | None = None
    generator: str | None = None
    source: str | None = None


class SceneObjectBase(VssModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    style: Style | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    source: str | None = None
    timestamp: datetime | None = None


class SceneImportedObjectBase(SceneObjectBase):
    show: bool | None = None
    layer: str | None = None
    extensions: dict[str, Any] = Field(default_factory=dict)
    rendererHints: dict[str, Any] = Field(default_factory=dict)
    payload: dict[str, Any] = Field(default_factory=dict)
    position: Wgs84Position | None = None
    orientation: Orientation | None = None


class SceneCustomObject(SceneImportedObjectBase):
    objectType: Literal["custom"] = "custom"
    customType: str = Field(min_length=1)


class SceneRuntimeObject(SceneImportedObjectBase):
    objectType: Literal["runtime"] = "runtime"
    runtimeType: str = Field(min_length=1)


class SceneTerrainSurface(SceneImportedObjectBase):
    objectType: Literal["terrainSurface"] = "terrainSurface"


class SceneCustomMesh(SceneImportedObjectBase):
    objectType: Literal["customMesh"] = "customMesh"


class SceneClippingPlane(SceneImportedObjectBase):
    objectType: Literal["clippingPlane"] = "clippingPlane"
    clippingPlane: dict[str, Any] = Field(default_factory=dict)


class SceneClippingPolygon(SceneImportedObjectBase):
    objectType: Literal["clippingPolygon"] = "clippingPolygon"
    clippingPolygon: dict[str, Any] = Field(default_factory=dict)


class SceneClassificationVolume(SceneImportedObjectBase):
    objectType: Literal["classificationVolume"] = "classificationVolume"
    classificationVolume: dict[str, Any] = Field(default_factory=dict)


class SceneCustomShader(SceneImportedObjectBase):
    objectType: Literal["customShader"] = "customShader"
    customShader: dict[str, Any] = Field(default_factory=dict)


class ScenePostProcessStage(SceneImportedObjectBase):
    objectType: Literal["postProcessStage"] = "postProcessStage"
    postProcessStage: dict[str, Any] = Field(default_factory=dict)


class SceneEntity(SceneObjectBase):
    objectType: Literal["entity"] = "entity"
    category: EntityCategory | None = None
    position: Wgs84Position
    orientation: Orientation | None = None


class SceneOverlay(SceneObjectBase):
    objectType: Literal["overlay"] = "overlay"
    position: Wgs84Position
    orientation: Orientation | None = None
    geometryType: Literal["polyline", "polygon", "rectangle", "corridor", "ellipse", "circle", "rangeRing", "wall", "box", "cylinder", "cone", "conicSensor", "rectangularSensor", "frustum", "sector2d", "bearingFan", "customPatternSensor", "fan", "sectorVolume", "hemisphere", "sphericalCap", "keyhole", "polylineVolume", "plane", "tileset", "ellipsoid", "sphere", "uncertaintyEllipsoid", "covarianceEllipse", "particleSystem", "voxel", "custom"] = "polyline"
    customGeometryType: str | None = None
    polyline: ScenePolyline | None = None
    polygon: ScenePolygon | None = None
    rectangle: SceneRectangle | None = None
    corridor: SceneCorridor | None = None
    ellipse: SceneEllipse | None = None
    circle: SceneCircle | None = None
    rangeRing: SceneRangeRing | None = None
    wall: SceneWall | None = None
    box: SceneBox | None = None
    cylinder: SceneCylinder | None = None
    cone: SceneCone | None = None
    conicSensor: SceneConicSensor | None = None
    rectangularSensor: SceneRectangularSensor | None = None
    frustum: SceneFrustum | None = None
    sector2d: SceneSector2D | None = None
    bearingFan: SceneBearingFan | None = None
    customPatternSensor: SceneCustomPatternSensor | None = None
    fan: SceneFan | None = None
    sectorVolume: SceneSectorVolume | None = None
    hemisphere: SceneHemisphere | None = None
    sphericalCap: SceneSphericalCap | None = None
    keyhole: SceneKeyhole | None = None
    polylineVolume: ScenePolylineVolume | None = None
    plane: ScenePlane | None = None
    tileset: SceneTileset | None = None
    ellipsoid: SceneEllipsoid | None = None
    sphere: SceneSphere | None = None
    uncertaintyEllipsoid: SceneUncertaintyEllipsoid | None = None
    covarianceEllipse: SceneCovarianceEllipse | None = None
    particleSystem: SceneParticleSystem | None = None
    voxel: SceneVoxel | None = None


class ScenePathSample(VssModel):
    timestamp: datetime
    position: Wgs84Position


class ScenePath(SceneObjectBase):
    objectType: Literal["path"] = "path"
    samples: list[ScenePathSample] = Field(min_length=2)
    widthPx: float = Field(default=2.0, gt=0)
    clampToGround: bool = False


class SceneTrack(SceneObjectBase):
    objectType: Literal["track"] = "track"
    samples: list[ScenePathSample] = Field(min_length=2)
    widthPx: float = Field(default=2.0, gt=0)
    clampToGround: bool = False
    orientation: Orientation | None = None


SceneObject = Annotated[SceneEntity | SceneOverlay | ScenePath | SceneTrack | SceneVector | SceneVelocityVector | SceneAccelerationVector | SceneLineOfSight | SceneBodyAxes | ScenePrincipalAxes | SceneRelativeLine | SceneInterceptLine | SceneCameraView | SceneCustomObject | SceneRuntimeObject | SceneTerrainSurface | SceneCustomMesh | SceneClippingPlane | SceneClippingPolygon | SceneClassificationVolume | SceneCustomShader | ScenePostProcessStage, Field(discriminator="objectType")]


class VssScene(VssModel):
    schemaVersion: Literal["1.0.0-scene"]
    document: SceneDocument
    views: list[SceneView] = Field(default_factory=list)
    analysis: dict[str, Any] = Field(default_factory=dict)
    presentation: dict[str, Any] = Field(default_factory=dict)
    objects: list[SceneObject] = Field(
        default_factory=list,
        validation_alias=AliasChoices("objects", "entities"),
        serialization_alias="objects",
    )

    @property
    def entities(self) -> list[SceneEntity]:
        return [obj for obj in self.objects if isinstance(obj, SceneEntity)]

    @property
    def overlays(self) -> list[SceneOverlay]:
        return [obj for obj in self.objects if isinstance(obj, SceneOverlay)]

    @property
    def paths(self) -> list[ScenePath]:
        return [obj for obj in self.objects if isinstance(obj, ScenePath)]

    @property
    def tracks(self) -> list[SceneTrack]:
        return [obj for obj in self.objects if isinstance(obj, SceneTrack)]

    @property
    def vectors(self) -> list[SceneVector]:
        return [obj for obj in self.objects if isinstance(obj, SceneVector)]

    @property
    def velocityVectors(self) -> list[SceneVelocityVector]:
        return [obj for obj in self.objects if isinstance(obj, SceneVelocityVector)]

    @property
    def accelerationVectors(self) -> list[SceneAccelerationVector]:
        return [obj for obj in self.objects if isinstance(obj, SceneAccelerationVector)]

    @property
    def cameraViews(self) -> list[SceneCameraView]:
        return [obj for obj in self.objects if isinstance(obj, SceneCameraView)]

    @property
    def customObjects(self) -> list[SceneCustomObject]:
        return [obj for obj in self.objects if isinstance(obj, SceneCustomObject)]

    @property
    def runtimeObjects(self) -> list[SceneRuntimeObject]:
        return [obj for obj in self.objects if isinstance(obj, SceneRuntimeObject)]

    @property
    def terrainSurfaces(self) -> list[SceneTerrainSurface]:
        return [obj for obj in self.objects if isinstance(obj, SceneTerrainSurface)]

    @property
    def customMeshes(self) -> list[SceneCustomMesh]:
        return [obj for obj in self.objects if isinstance(obj, SceneCustomMesh)]

    @property
    def clippingPlanes(self) -> list[SceneClippingPlane]:
        return [obj for obj in self.objects if isinstance(obj, SceneClippingPlane)]

    @property
    def clippingPolygons(self) -> list[SceneClippingPolygon]:
        return [obj for obj in self.objects if isinstance(obj, SceneClippingPolygon)]

    @property
    def classificationVolumes(self) -> list[SceneClassificationVolume]:
        return [obj for obj in self.objects if isinstance(obj, SceneClassificationVolume)]

    @property
    def customShaders(self) -> list[SceneCustomShader]:
        return [obj for obj in self.objects if isinstance(obj, SceneCustomShader)]

    @property
    def postProcessStages(self) -> list[ScenePostProcessStage]:
        return [obj for obj in self.objects if isinstance(obj, ScenePostProcessStage)]

    @property
    def lineOfSights(self) -> list[SceneLineOfSight]:
        return [obj for obj in self.objects if isinstance(obj, SceneLineOfSight)]

    @property
    def bodyAxes(self) -> list[SceneBodyAxes]:
        return [obj for obj in self.objects if isinstance(obj, SceneBodyAxes)]

    @property
    def principalAxes(self) -> list[ScenePrincipalAxes]:
        return [obj for obj in self.objects if isinstance(obj, ScenePrincipalAxes)]

    @property
    def relativeLines(self) -> list[SceneRelativeLine]:
        return [obj for obj in self.objects if isinstance(obj, SceneRelativeLine)]

    @property
    def interceptLines(self) -> list[SceneInterceptLine]:
        return [obj for obj in self.objects if isinstance(obj, SceneInterceptLine)]

    @classmethod
    def from_messages(
        cls,
        messages: list[EntityUpsertMessage],
        *,
        scene_id: str = "scene-001",
        scene_name: str = "VSS Scene",
        description: str | None = None,
        generator: str = "visualization-standard-schema",
    ) -> "VssScene":
        created = max((message.timestamp for message in messages), default=None)
        sources = sorted({message.source for message in messages})
        source = ", ".join(sources) if sources else None
        return cls(
            schemaVersion="1.0.0-scene",
            document=SceneDocument(
                id=scene_id,
                name=scene_name,
                description=description,
                created=created,
                generator=generator,
                source=source,
            ),
            objects=[scene_entity_from_message(message) for message in messages],
        )


def scene_entity_from_message(message: EntityUpsertMessage) -> SceneEntity:
    payload = message.payload
    return SceneEntity(
        objectType="entity",
        id=payload.entityId,
        name=payload.name,
        category=payload.category,
        position=payload.position,
        orientation=payload.orientation,
        style=payload.style,
        attributes=payload.attributes,
        source=message.source,
        timestamp=message.timestamp,
    )
