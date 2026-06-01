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


class SceneEntity(SceneObjectBase):
    objectType: Literal["entity"] = "entity"
    category: EntityCategory | None = None
    position: Wgs84Position
    orientation: Orientation | None = None


class SceneOverlay(SceneObjectBase):
    objectType: Literal["overlay"] = "overlay"
    position: Wgs84Position
    geometryType: Literal["polyline", "polygon", "rectangle", "corridor", "ellipse", "circle", "wall", "box"] = "polyline"
    polyline: ScenePolyline | None = None
    polygon: ScenePolygon | None = None
    rectangle: SceneRectangle | None = None
    corridor: SceneCorridor | None = None
    ellipse: SceneEllipse | None = None
    circle: SceneCircle | None = None
    wall: SceneWall | None = None
    box: SceneBox | None = None


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


SceneObject = Annotated[SceneEntity | SceneOverlay | ScenePath | SceneTrack, Field(discriminator="objectType")]


class VssScene(VssModel):
    schemaVersion: Literal["1.0.0-scene"]
    document: SceneDocument
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
