from __future__ import annotations

from xml.etree.ElementTree import Element, SubElement, tostring

from ..capabilities import assess_soap_scene_support, get_soap_capabilities
from ..models import EntityUpsertMessage, SceneEntity, SceneOverlay, VssScene
from ..util import utc_now_isoformat
from .io import (
    dump_soap_bundle_json,
    load_soap_bundle,
    load_soap_bundle_files,
    parse_soap_bundle_json,
    serialize_soap_bundle_files,
    write_soap_bundle,
)
from .models import (
    SoapAnalysis,
    SoapArtifact,
    SoapAsset,
    SoapAssets,
    SoapBundle,
    SoapDiagnostic,
    SoapManifest,
    SoapModel,
    SoapOverlay,
    SoapOverlayPoint,
    SoapOverlayStyle,
    SoapPalette,
    SoapPlatform,
    SoapPresentation,
    SoapScenario,
    SoapSensorSwath,
    SoapTrajectory,
    SoapView,
    SoapViews,
)

SOAP_ENV_NS = "http://schemas.xmlsoap.org/soap/envelope/"
VSS_NS = "https://example.org/vss/soap/v1"


def compile_soap_envelope(message: EntityUpsertMessage) -> str:
    envelope = Element(f"{{{SOAP_ENV_NS}}}Envelope")
    body = SubElement(envelope, f"{{{SOAP_ENV_NS}}}Body")
    upsert = SubElement(body, f"{{{VSS_NS}}}EntityUpsertMessage")

    _text(upsert, "schemaVersion", message.schemaVersion)
    _text(upsert, "messageType", message.messageType)
    _text(upsert, "messageId", message.messageId)
    _text(upsert, "timestamp", message.timestamp.isoformat())
    _text(upsert, "source", message.source)

    payload = SubElement(upsert, f"{{{VSS_NS}}}payload")
    _text(payload, "entityId", message.payload.entityId)
    _text(payload, "name", message.payload.name)

    if message.payload.category:
        _text(payload, "category", message.payload.category.value)

    position = SubElement(payload, f"{{{VSS_NS}}}position")
    _text(position, "longitudeDeg", message.payload.position.longitudeDeg)
    _text(position, "latitudeDeg", message.payload.position.latitudeDeg)
    _text(position, "altitudeM", message.payload.position.altitudeM)

    if message.payload.orientation:
        orientation = SubElement(payload, f"{{{VSS_NS}}}orientation")
        _optional_text(orientation, "headingDeg", message.payload.orientation.headingDeg)
        _optional_text(orientation, "pitchDeg", message.payload.orientation.pitchDeg)
        _optional_text(orientation, "rollDeg", message.payload.orientation.rollDeg)

    if message.payload.style:
        style = SubElement(payload, f"{{{VSS_NS}}}style")
        _optional_text(style, "label", message.payload.style.label)
        if message.payload.style.iconUri:
            _text(style, "iconUri", str(message.payload.style.iconUri))
        if message.payload.style.modelUri:
            _text(style, "modelUri", str(message.payload.style.modelUri))
        if message.payload.style.colorRgba:
            color = SubElement(style, f"{{{VSS_NS}}}colorRgba")
            for component in message.payload.style.colorRgba:
                _text(color, "value", component)

    if message.payload.attributes:
        attributes = SubElement(payload, f"{{{VSS_NS}}}attributes")
        for key, value in sorted(message.payload.attributes.items()):
            attribute = SubElement(attributes, f"{{{VSS_NS}}}attribute", name=key)
            attribute.text = str(value)

    return tostring(envelope, encoding="unicode", xml_declaration=True)


def compile_soap_scene(scene: VssScene) -> SoapBundle:
    platforms = [_to_soap_platform(entity) for entity in scene.entities]
    trajectories = [_to_soap_trajectory(entity) for entity in scene.entities if entity.timestamp is not None]
    models = [_to_soap_model(entity) for entity in scene.entities if entity.style and entity.style.modelUri]
    sensor_swaths = [_to_soap_sensor_swath(entity) for entity in scene.entities if entity.category and entity.category.value == "sensor"]
    overlays = [_to_soap_overlay(overlay) for overlay in scene.overlays]
    diagnostics = _build_scene_diagnostics(scene)
    scenario = SoapScenario(
        id=scene.document.id,
        name=scene.document.name,
        clock=_clock_from_scene(scene),
        platforms=platforms,
        trajectories=trajectories,
        models=models,
        sensorSwaths=sensor_swaths,
        overlays=overlays,
    )
    views = _build_soap_views(scene)
    manifest = SoapManifest(
        source=scene.document.id,
        mode="scene-to-scenario+scene-to-analysis+scene-to-presentation",
        artifacts=[
            SoapArtifact(kind="manifest", path="soap/manifest.json"),
            SoapArtifact(kind="scenario", path="soap/scenario.json"),
            SoapArtifact(kind="views", path="soap/views.json"),
            SoapArtifact(kind="analysis", path="soap/analysis.json"),
            SoapArtifact(kind="presentation", path="soap/presentation.json"),
            SoapArtifact(kind="assetManifest", path="soap/assets.json"),
            SoapArtifact(kind="diagnostics", path="soap/diagnostics.json"),
        ],
        totals={
            "platforms": len(platforms),
            "trajectories": len(trajectories),
            "models": len(models),
            "sensorSwaths": len(sensor_swaths),
            "overlays": len(overlays),
        },
    )
    return SoapBundle(
        source=scene.document.id,
        manifest=manifest,
        scenario=scenario,
        views=views,
        analysis=SoapAnalysis(),
        presentation=SoapPresentation(),
        assets=SoapAssets(),
        diagnostics=diagnostics,
    )


def _to_soap_platform(entity: SceneEntity) -> SoapPlatform:
    return SoapPlatform(
        id=entity.id,
        name=entity.name,
        initialState={
            "frame": "cartographicDegrees",
            "lon": entity.position.longitudeDeg,
            "lat": entity.position.latitudeDeg,
            "alt": entity.position.altitudeM,
        },
        properties={
            **entity.attributes,
            **({"category": entity.category.value} if entity.category else {}),
            **({"source": entity.source} if entity.source else {}),
        },
    )


def _to_soap_trajectory(entity: SceneEntity) -> SoapTrajectory:
    if entity.timestamp is None:
        timestamp = utc_now_isoformat()
    else:
        timestamp = entity.timestamp.isoformat()
    return SoapTrajectory(
        id=f"{entity.id}-trajectory",
        platformId=entity.id,
        source="vss.scene.entity",
        samples=[
            {
                "t": timestamp,
                "valueFormat": "cartographicDegrees",
                "value": [
                    entity.position.longitudeDeg,
                    entity.position.latitudeDeg,
                    entity.position.altitudeM,
                ],
            }
        ],
    )


def _to_soap_model(entity: SceneEntity) -> SoapModel:
    model_uri = entity.style.modelUri if entity.style is not None else None
    if model_uri is None:
        raise ValueError(f"entity {entity.id} is missing modelUri")
    return SoapModel(
        id=entity.id,
        name=entity.name,
        uri=str(model_uri),
        position={
            "frame": "cartographicDegrees",
            "lon": entity.position.longitudeDeg,
            "lat": entity.position.latitudeDeg,
            "alt": entity.position.altitudeM,
        },
        properties={
            **entity.attributes,
            **({"category": entity.category.value} if entity.category else {}),
            **({"source": entity.source} if entity.source else {}),
        },
    )


def _to_soap_sensor_swath(entity: SceneEntity) -> SoapSensorSwath:
    return SoapSensorSwath(
        id=entity.id,
        name=entity.name,
        hostId=entity.source,
        position={
            "frame": "cartographicDegrees",
            "lon": entity.position.longitudeDeg,
            "lat": entity.position.latitudeDeg,
            "alt": entity.position.altitudeM,
        },
        style=SoapOverlayStyle(
            label=entity.style.label if entity.style else None,
            colorRgba=list(entity.style.colorRgba) if entity.style and entity.style.colorRgba else [],
        ),
        properties=entity.attributes,
    )


def _to_soap_overlay(overlay: SceneOverlay) -> SoapOverlay:
    if overlay.geometryType == "polyline" and overlay.polyline:
        geometry_type = "polyline"
        positions = overlay.polyline.positions
        geometry_style = {
            "widthPx": overlay.polyline.widthPx,
            "clampToGround": overlay.polyline.clampToGround,
        }
    elif overlay.geometryType == "polygon" and overlay.polygon:
        geometry_type = "polygon"
        positions = overlay.polygon.positions
        geometry_style = {
            "clampToGround": overlay.polygon.clampToGround,
        }
    else:
        geometry_type = overlay.geometryType
        positions = []
        geometry_style = {}
    return SoapOverlay(
        id=overlay.id,
        name=overlay.name,
        kind=geometry_type,
        style=SoapOverlayStyle(
            label=overlay.style.label if overlay.style else None,
            colorRgba=list(overlay.style.colorRgba) if overlay.style and overlay.style.colorRgba else [],
            widthPx=geometry_style.get("widthPx"),
            clampToGround=bool(geometry_style.get("clampToGround", False)),
        ),
        positions=[
            SoapOverlayPoint(
                longitudeDeg=position.longitudeDeg,
                latitudeDeg=position.latitudeDeg,
                altitudeM=position.altitudeM,
            )
            for position in positions
        ],
        properties={
            **overlay.attributes,
            **({"source": overlay.source} if overlay.source else {}),
        },
    )


def _clock_from_scene(scene: VssScene) -> dict[str, str]:
    timestamps = [obj.timestamp for obj in scene.objects if obj.timestamp is not None]
    if not timestamps:
        return {}
    start = min(timestamps).isoformat()
    stop = max(timestamps).isoformat()
    return {"startTime": start, "stopTime": stop, "currentTime": stop}


def _build_soap_views(scene: VssScene) -> SoapViews:
    first_entity = scene.entities[0] if scene.entities else None
    target_id = first_entity.id if first_entity is not None else None
    camera = {}
    if first_entity is not None:
        camera = {
            "frame": "cartographicDegrees",
            "lon": first_entity.position.longitudeDeg,
            "lat": first_entity.position.latitudeDeg,
            "alt": first_entity.position.altitudeM,
        }
    return SoapViews(
        views=[
            SoapView(
                id=f"{scene.document.id}-overview",
                name=f"{scene.document.name} Overview",
                target=target_id,
                camera=camera,
            )
        ] if first_entity is not None else [],
        palettes=[
            SoapPalette(
                id=f"{scene.document.id}-default-palette",
                name="Default Palette",
                entries=[
                    {"kind": "entity-count", "value": len(scene.entities)},
                    {"kind": "overlay-count", "value": len(scene.overlays)},
                ],
            )
        ],
    )


def _build_scene_diagnostics(scene: VssScene) -> list[SoapDiagnostic]:
    diagnostics: list[SoapDiagnostic] = []
    for entity in scene.entities:
        if entity.timestamp is None:
            diagnostics.append(
                SoapDiagnostic(
                    severity="warning",
                    code="SOAP-SCENE-MISSING-TIMESTAMP",
                    path=f"entities/{entity.id}",
                    message=f"Entity '{entity.id}' has no timestamp; SOAP trajectory export was omitted.",
                )
            )
    return diagnostics


def _text(parent: Element, name: str, value: object) -> Element:
    node = SubElement(parent, f"{{{VSS_NS}}}{name}")
    node.text = str(value)
    return node


def _optional_text(parent: Element, name: str, value: object | None) -> Element | None:
    if value is None:
        return None
    return _text(parent, name, value)


__all__ = [
    "SoapAnalysis",
    "SoapArtifact",
    "SoapAsset",
    "SoapAssets",
    "SoapBundle",
    "SoapDiagnostic",
    "SoapManifest",
    "SoapModel",
    "SoapPlatform",
    "SoapPalette",
    "SoapPresentation",
    "SoapScenario",
    "SoapSensorSwath",
    "SoapTrajectory",
    "SoapView",
    "SoapViews",
    "assess_soap_scene_support",
    "compile_soap_envelope",
    "compile_soap_scene",
    "dump_soap_bundle_json",
    "get_soap_capabilities",
    "load_soap_bundle",
    "load_soap_bundle_files",
    "parse_soap_bundle_json",
    "serialize_soap_bundle_files",
    "write_soap_bundle",
]
