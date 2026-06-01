from __future__ import annotations

from typing import Any

from ..models import (
    EntityUpsertMessage,
    Orientation,
    SceneEntity,
    SceneOverlay,
    VssScene,
    Wgs84Position,
)
from ..util import (
    isoformat_or_default,
    normalize_configs,
    simdis_fallback_timestamp_iso,
    to_bool,
    to_float,
)
from .asi import _simdis_config, compile_simdis_asi, compile_simdis_asi_message
from .models import (
    SimdisAnalysis,
    SimdisAnnotationState,
    SimdisArtifact,
    SimdisAssets,
    SimdisBeamSample,
    SimdisBeamState,
    SimdisBundle,
    SimdisDiagnostic,
    SimdisEntities,
    SimdisGateSample,
    SimdisGateState,
    SimdisManifest,
    SimdisOverlayGeometry,
    SimdisOverlayPoint,
    SimdisOverlayState,
    SimdisPlatformState,
    SimdisPosition,
    SimdisPresentation,
    SimdisProjectorSample,
    SimdisProjectorState,
    SimdisSensorState,
    SimdisVectorState,
)


def compile_simdis_lines(message: EntityUpsertMessage) -> list[str]:
    payload = message.payload
    return _compile_platform_lines(
        entity_id=payload.entityId,
        name=payload.name,
        category=payload.category.value if payload.category else "other",
        position=payload.position,
        orientation=payload.orientation,
        timestamp=message.timestamp.isoformat(),
        label=payload.style.label if payload.style and payload.style.label else None,
        comment=f"# VSS SIMDIS export messageId={message.messageId}",
    )


def compile_simdis_bundle(message: EntityUpsertMessage) -> SimdisBundle:
    payload = message.payload
    platform = _platform_from_scene_entity(
        SceneEntity(
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
    )
    return _build_simdis_bundle(
        source=message.messageId,
        mode="entity.upsert-to-simdis-platform",
        platforms=[platform],
        sensors=[],
        annotations=[],
        beams=[],
        gates=[],
        projectors=[],
        vectors=[],
        overlays=[],
        overlays_gog="\n".join(compile_simdis_lines(message)) + "\n",
        scenario_asi=compile_simdis_asi_message(message),
    )


def compile_simdis_scene(scene: VssScene) -> SimdisBundle:
    platforms: list[SimdisPlatformState] = []
    sensors: list[SimdisSensorState] = []
    annotations: list[SimdisAnnotationState] = []
    beams: list[SimdisBeamState] = []
    gates: list[SimdisGateState] = []
    projectors: list[SimdisProjectorState] = []
    vectors: list[SimdisVectorState] = []
    overlays: list[SimdisOverlayState] = []

    for entity in scene.entities:
        if _is_annotation_candidate(entity):
            annotations.append(_annotation_from_scene_entity(entity))
            continue
        if entity.category is not None and entity.category.value == "sensor":
            sensors.append(_sensor_from_scene_entity(entity))
        else:
            platforms.append(_platform_from_scene_entity(entity))
        beams.extend(_beams_from_scene_entity(entity))
        gates.extend(_gates_from_scene_entity(entity))
        projectors.extend(_projectors_from_scene_entity(entity))

    overlay_lines = ["# VSS SIMDIS export scene bundle"]
    for entity in scene.entities:
        if _is_annotation_candidate(entity):
            overlay_lines.extend(_compile_annotation_gog(_annotation_from_scene_entity(entity)))
            continue
        if entity.category is not None and entity.category.value == "sensor":
            continue
        overlay_lines.extend(
            _compile_platform_lines(
                entity_id=entity.id,
                name=entity.name,
                category=entity.category.value if entity.category else "other",
                position=entity.position,
                orientation=entity.orientation,
                timestamp=isoformat_or_default(
                    entity.timestamp or scene.document.created,
                    fallback_iso=simdis_fallback_timestamp_iso,
                ),
                label=entity.style.label if entity.style and entity.style.label else None,
                comment=None,
            )
        )
    for overlay in scene.overlays:
        overlays.append(_overlay_from_scene_overlay(overlay))
        vectors.append(_vector_from_scene_overlay(overlay))
        overlay_lines.extend(_compile_overlay_gog(overlay))
    diagnostics = _build_scene_diagnostics(scene)
    return _build_simdis_bundle(
        source=scene.document.id,
        mode="scene-to-gog+scene-to-entities+scene-to-presentation",
        platforms=platforms,
        sensors=sensors,
        annotations=annotations,
        beams=beams,
        gates=gates,
        projectors=projectors,
        vectors=vectors,
        overlays=overlays,
        overlays_gog="\n".join(overlay_lines) + "\n",
        scenario_asi=compile_simdis_asi(scene),
        diagnostics=diagnostics,
    )


def _build_simdis_bundle(
    *,
    source: str,
    mode: str,
    platforms: list[SimdisPlatformState],
    sensors: list[SimdisSensorState],
    annotations: list[SimdisAnnotationState],
    beams: list[SimdisBeamState],
    gates: list[SimdisGateState],
    projectors: list[SimdisProjectorState],
    vectors: list[SimdisVectorState],
    overlays: list[SimdisOverlayState],
    overlays_gog: str,
    scenario_asi: str,
    diagnostics: list[SimdisDiagnostic] | None = None,
) -> SimdisBundle:
    manifest = SimdisManifest(
        source=source,
        mode=mode,
        artifacts=[
            SimdisArtifact(kind="manifest", path="simdis/manifest.json"),
            SimdisArtifact(kind="entityState", path="simdis/entities.json"),
            SimdisArtifact(kind="gog", path="simdis/overlays.gog"),
            SimdisArtifact(kind="asi", path="simdis/scenario.asi"),
            SimdisArtifact(kind="analysis", path="simdis/analysis.json"),
            SimdisArtifact(kind="presentation", path="simdis/presentation.json"),
            SimdisArtifact(kind="assetManifest", path="simdis/assets.json"),
            SimdisArtifact(kind="diagnostics", path="simdis/diagnostics.json"),
        ],
        totals={
            "platforms": len(platforms),
            "sensors": len(sensors),
            "annotations": len(annotations),
            "beams": len(beams),
            "gates": len(gates),
            "projectors": len(projectors),
            "vectors": len(vectors),
            "overlays": len(overlays),
        },
    )
    return SimdisBundle(
        source=source,
        manifest=manifest,
        entities=SimdisEntities(
            platforms=platforms,
            sensors=sensors,
            annotations=annotations,
            beams=beams,
            gates=gates,
            projectors=projectors,
            vectors=vectors,
            overlays=overlays,
        ),
        overlaysGog=overlays_gog,
        scenarioAsi=scenario_asi,
        analysis=SimdisAnalysis(),
        presentation=SimdisPresentation(),
        assets=SimdisAssets(),
        diagnostics=diagnostics or [],
    )


def _platform_from_scene_entity(entity: SceneEntity) -> SimdisPlatformState:
    return SimdisPlatformState(
        id=entity.id,
        name=entity.name,
        category=entity.category.value if entity.category else "platform",
        initialPosition=SimdisPosition(
            frame="cartographicDegrees",
            lon=entity.position.longitudeDeg,
            lat=entity.position.latitudeDeg,
            alt=entity.position.altitudeM,
        ),
        orientation=entity.orientation.model_dump(exclude_none=True) if entity.orientation else {},
        label={"text": entity.style.label} if entity.style and entity.style.label else {},
        properties=entity.attributes,
    )


def _sensor_from_scene_entity(entity: SceneEntity) -> SimdisSensorState:
    return SimdisSensorState(
        id=entity.id,
        kind=entity.category.value if entity.category else "sensor",
        name=entity.name,
        hostId=entity.source,
        pose={
            "position": {
                "frame": "cartographicDegrees",
                "lon": entity.position.longitudeDeg,
                "lat": entity.position.latitudeDeg,
                "alt": entity.position.altitudeM,
            },
            **(
                {"orientation": entity.orientation.model_dump(exclude_none=True)}
                if entity.orientation
                else {}
            ),
        },
        geometry={
            "type": "sensor-point",
            "positionMode": "cartographicDegrees",
        },
        style=entity.style.model_dump(exclude_none=True) if entity.style else {},
        show=True,
        simdisTarget="beam / LOB / projector",
    )


def _annotation_from_scene_entity(entity: SceneEntity) -> SimdisAnnotationState:
    style = entity.style
    return SimdisAnnotationState(
        id=entity.id,
        kind="annotation",
        name=entity.name,
        position=SimdisPosition(
            frame="cartographicDegrees",
            lon=entity.position.longitudeDeg,
            lat=entity.position.latitudeDeg,
            alt=entity.position.altitudeM,
        ),
        label={"text": style.label} if style and style.label else {},
        billboard={"image": str(style.iconUri)} if style and style.iconUri else {},
        point={
            "color": list(style.colorRgba) if style and style.colorRgba else [255, 255, 255, 255],
        },
        show=True,
    )


def _beams_from_scene_entity(entity: SceneEntity) -> list[SimdisBeamState]:
    simdis = _simdis_config(entity)
    beam_configs = _normalize_configs(simdis.get("beams") or simdis.get("beam"))
    beams: list[SimdisBeamState] = []
    for index, config in enumerate(beam_configs, start=1):
        beams.append(
            SimdisBeamState(
                id=_string_or_default(config.get("beamId"), f"{entity.id}-beam-{index}"),
                hostPlatformId=_string_or_default(config.get("hostPlatformId"), entity.id),
                type=_string_or_default(config.get("type"), "BODY"),
                horzBW=to_float(config.get("horzBwDeg")),
                vertBW=to_float(config.get("vertBwDeg")),
                samples=[
                    SimdisBeamSample(
                        time=_string_or_default(
                            sample.get("time"),
                            isoformat_or_default(entity.timestamp, fallback_iso=simdis_fallback_timestamp_iso),
                        ),
                        on=_to_bool(sample.get("on")),
                        color=_string_or_none(sample.get("color")),
                        az=to_float(sample.get("az")),
                        el=to_float(sample.get("el")),
                        rangeMeters=to_float(sample.get("rangeMeters")),
                        targetPlatformId=_string_or_none(sample.get("targetPlatformId")),
                    )
                    for sample in _normalize_configs(config.get("samples"))
                ],
            )
        )
    return beams


def _gates_from_scene_entity(entity: SceneEntity) -> list[SimdisGateState]:
    simdis = _simdis_config(entity)
    gate_configs = _normalize_configs(simdis.get("gates") or simdis.get("gate"))
    gates: list[SimdisGateState] = []
    for index, config in enumerate(gate_configs, start=1):
        gates.append(
            SimdisGateState(
                id=_string_or_default(config.get("gateId"), f"{entity.id}-gate-{index}"),
                hostBeamId=_string_or_default(config.get("hostBeamId"), f"{entity.id}-beam-{index}"),
                type=_string_or_default(config.get("type"), "BODY"),
                samples=[
                    SimdisGateSample(
                        time=_string_or_default(
                            sample.get("time"),
                            isoformat_or_default(entity.timestamp, fallback_iso=simdis_fallback_timestamp_iso),
                        ),
                        on=_to_bool(sample.get("on")),
                        color=_string_or_none(sample.get("color")),
                        az=to_float(sample.get("az")),
                        el=to_float(sample.get("el")),
                        width=to_float(sample.get("width")),
                        height=to_float(sample.get("height")),
                        minRangeMeters=to_float(sample.get("minRangeMeters")),
                        maxRangeMeters=to_float(sample.get("maxRangeMeters")),
                        centroidMeters=to_float(sample.get("centroidMeters")),
                    )
                    for sample in _normalize_configs(config.get("samples"))
                ],
            )
        )
    return gates


def _projectors_from_scene_entity(entity: SceneEntity) -> list[SimdisProjectorState]:
    simdis = _simdis_config(entity)
    projector_configs = _normalize_configs(simdis.get("projectors") or simdis.get("projector"))
    projectors: list[SimdisProjectorState] = []
    for index, config in enumerate(projector_configs, start=1):
        projectors.append(
            SimdisProjectorState(
                id=_string_or_default(config.get("projectorId"), f"{entity.id}-projector-{index}"),
                hostPlatformId=_string_or_default(config.get("hostPlatformId"), entity.id),
                rasterFile=_string_or_none(config.get("rasterFile")),
                interpolateFov=bool(config.get("interpolateFov", True)),
                samples=[
                    SimdisProjectorSample(
                        time=_string_or_default(
                            sample.get("time"),
                            isoformat_or_default(entity.timestamp, fallback_iso=simdis_fallback_timestamp_iso),
                        ),
                        on=_to_bool(sample.get("on")),
                        fovDegrees=to_float(sample.get("fovDegrees")),
                    )
                    for sample in _normalize_configs(config.get("samples"))
                ],
            )
        )
    return projectors


def _compile_platform_lines(
    *,
    entity_id: str,
    name: str,
    category: str,
    position: Wgs84Position,
    orientation: Orientation | None,
    timestamp: str,
    label: str | None,
    comment: str | None,
) -> list[str]:
    heading = orientation.headingDeg if orientation and orientation.headingDeg is not None else 0.0
    pitch = orientation.pitchDeg if orientation and orientation.pitchDeg is not None else 0.0
    roll = orientation.rollDeg if orientation and orientation.rollDeg is not None else 0.0
    lines: list[str] = []
    if comment:
        lines.append(comment)
    lines.extend(
        [
            f'PLATFORM {entity_id} NAME "{name}" CATEGORY {category}',
            (
                "PLATFORM_UPDATE "
                f"{entity_id} "
                f"{timestamp} "
                f"{position.latitudeDeg:.8f} "
                f"{position.longitudeDeg:.8f} "
                f"{position.altitudeM:.3f} "
                f"{heading:.3f} "
                f"{pitch:.3f} "
                f"{roll:.3f}"
            ),
        ]
    )
    if label:
        lines.append(f'PLATFORM_LABEL {entity_id} "{label}"')
    return lines


def _build_scene_diagnostics(scene: VssScene) -> list[SimdisDiagnostic]:
    diagnostics: list[SimdisDiagnostic] = []
    for entity in scene.entities:
        if entity.timestamp is None:
            diagnostics.append(
                SimdisDiagnostic(
                    severity="warning",
                    code="SIMDIS-SCENE-MISSING-TIMESTAMP",
                    path=f"entities/{entity.id}",
                    message=f"Entity '{entity.id}' has no timestamp; scene or fallback time was used for SIMDIS export.",
                )
            )
    return diagnostics


def _is_annotation_candidate(entity: SceneEntity) -> bool:
    style = entity.style
    if entity.category is not None and entity.category.value == "sensor":
        return False
    if entity.category is None or entity.category.value != "ground":
        return False
    if style is None:
        return False
    if style.modelUri is not None:
        return False
    return bool(style.label or style.iconUri)


def _compile_overlay_gog(overlay: SceneOverlay) -> list[str]:
    rgba = overlay.style.colorRgba if overlay.style and overlay.style.colorRgba else (255, 255, 255, 255)
    rgb = f"{rgba[0]} {rgba[1]} {rgba[2]}"
    lines = [f"start_gog {overlay.id}"]
    if overlay.geometryType == "polyline" and overlay.polyline:
        lines.extend(
            [
                "polyline",
                f"  linecolor {rgb}",
                f"  linewidth {overlay.polyline.widthPx:.1f}",
            ]
        )
        positions = overlay.polyline.positions
    elif overlay.geometryType == "polygon" and overlay.polygon:
        lines.extend(
            [
                "polygon",
                f"  linecolor {rgb}",
                f"  fillcolor {rgb}",
            ]
        )
        positions = overlay.polygon.positions
    else:
        return []
    if overlay.style and overlay.style.label:
        lines.append(f'  label "{overlay.style.label}"')
    for position in positions:
        lines.append(
            "  point "
            f"{position.latitudeDeg:.8f} "
            f"{position.longitudeDeg:.8f} "
            f"{position.altitudeM:.3f}"
        )
    lines.append("end_gog")
    return lines


def _compile_annotation_gog(annotation: SimdisAnnotationState) -> list[str]:
    lines = [
        f"start_annotation {annotation.id}",
        f'  name "{annotation.name}"',
    ]
    if annotation.label and annotation.label.get("text"):
        lines.append(f'  label "{annotation.label["text"]}"')
    if annotation.billboard and annotation.billboard.get("image"):
        lines.append(f'  billboard "{annotation.billboard["image"]}"')
    if annotation.point and annotation.point.get("color"):
        color = annotation.point["color"]
        if len(color) >= 3:
            lines.append(f"  pointcolor {color[0]} {color[1]} {color[2]}")
    if annotation.position:
        lines.append(
            "  position "
            f"{annotation.position.lat:.8f} "
            f"{annotation.position.lon:.8f} "
            f"{annotation.position.alt:.3f}"
        )
    lines.append("end_annotation")
    return lines


_normalize_configs = normalize_configs


def _string_or_default(value: Any, default: str) -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


_to_bool = to_bool


def _vector_from_scene_overlay(overlay: SceneOverlay) -> SimdisVectorState:
    if overlay.geometryType == "polyline" and overlay.polyline:
        geometry = {
            "type": "polyline",
            "widthPx": overlay.polyline.widthPx,
            "clampToGround": overlay.polyline.clampToGround,
            "positions": [
                {
                    "lon": position.longitudeDeg,
                    "lat": position.latitudeDeg,
                    "alt": position.altitudeM,
                }
                for position in overlay.polyline.positions
            ],
        }
    elif overlay.geometryType == "polygon" and overlay.polygon:
        geometry = {
            "type": "polygon",
            "clampToGround": overlay.polygon.clampToGround,
            "positions": [
                {
                    "lon": position.longitudeDeg,
                    "lat": position.latitudeDeg,
                    "alt": position.altitudeM,
                }
                for position in overlay.polygon.positions
            ],
        }
    else:
        geometry = {}
    return SimdisVectorState(
        id=overlay.id,
        kind="vector",
        name=overlay.name,
        geometry=geometry,
        style=overlay.style.model_dump(exclude_none=True) if overlay.style else {},
        show=True,
    )


def _overlay_from_scene_overlay(overlay: SceneOverlay) -> SimdisOverlayState:
    if overlay.geometryType == "polyline" and overlay.polyline:
        geometry = SimdisOverlayGeometry(
            type="polyline",
            clampToGround=overlay.polyline.clampToGround,
            widthPx=overlay.polyline.widthPx,
            positions=[
                SimdisOverlayPoint(
                    lon=position.longitudeDeg,
                    lat=position.latitudeDeg,
                    alt=position.altitudeM,
                )
                for position in overlay.polyline.positions
            ],
        )
    else:
        geometry = SimdisOverlayGeometry(
            type="polygon",
            clampToGround=overlay.polygon.clampToGround if overlay.polygon else False,
            positions=[
                SimdisOverlayPoint(
                    lon=position.longitudeDeg,
                    lat=position.latitudeDeg,
                    alt=position.altitudeM,
                )
                for position in (overlay.polygon.positions if overlay.polygon else [])
            ],
        )
    return SimdisOverlayState(
        id=overlay.id,
        name=overlay.name,
        geometry=geometry,
        style=overlay.style.model_dump(exclude_none=True) if overlay.style else {},
        show=True,
    )


__all__ = ["compile_simdis_bundle", "compile_simdis_lines", "compile_simdis_scene"]
