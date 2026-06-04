from __future__ import annotations

import math
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from ..capabilities import assess_cesium_scene_support, get_cesium_capabilities
from ..models import (
    EntityUpsertMessage,
    SceneAccelerationVector,
    SceneBodyAxes,
    SceneCameraView,
    SceneClassificationVolume,
    SceneClippingPlane,
    SceneClippingPolygon,
    SceneCustomMesh,
    SceneCustomObject,
    SceneCustomShader,
    SceneEntity,
    SceneInterceptLine,
    SceneLineOfSight,
    SceneOverlay,
    SceneParticleSystem,
    ScenePath,
    ScenePostProcessStage,
    ScenePrincipalAxes,
    SceneRelativeLine,
    SceneRuntimeObject,
    SceneTerrainSurface,
    SceneTrack,
    SceneVector,
    SceneVelocityVector,
    SceneView,
    VssScene,
    Wgs84Position,
    scene_entity_from_message,
)
from ..util import dumps_json, write_text_file

CesiumOverlayEmitter = Callable[[SceneOverlay], dict[str, Any] | None]
_CESIUM_OVERLAY_EMITTERS: dict[str, CesiumOverlayEmitter] = {}


def register_cesium_overlay_emitter(geometry_type: str, emitter: CesiumOverlayEmitter) -> None:
    _CESIUM_OVERLAY_EMITTERS[geometry_type] = emitter


def unregister_cesium_overlay_emitter(geometry_type: str) -> None:
    _CESIUM_OVERLAY_EMITTERS.pop(geometry_type, None)


def get_cesium_overlay_emitters() -> dict[str, CesiumOverlayEmitter]:
    return dict(_CESIUM_OVERLAY_EMITTERS)


def compile_cesium_document(
    message: EntityUpsertMessage,
    *,
    document_name: str = "VSS CZML",
) -> list[dict[str, Any]]:
    return [
        {
            "id": "document",
            "name": document_name,
            "version": "1.0",
        },
        _build_scene_entity_packet(
            scene_entity_from_message(message),
            attributes={
                "source": message.source,
                "messageId": message.messageId,
                "timestamp": message.timestamp.isoformat(),
                **message.payload.attributes,
            },
        ),
    ]


def compile_cesium_scene(
    scene: VssScene,
    *,
    document_name: str | None = None,
) -> list[dict[str, Any]]:
    clock = _build_clock_packet(scene)
    document_properties: dict[str, Any] = {}
    if scene.analysis:
        document_properties["analysis"] = scene.analysis
    if scene.presentation:
        document_properties["presentation"] = scene.presentation
    packets: list[dict[str, Any]] = [
        {
            "id": "document",
            "name": document_name or scene.document.name,
            "version": "1.0",
            **({"clock": clock} if clock else {}),
            **({"properties": document_properties} if document_properties else {}),
        }
    ]
    for obj in scene.objects:
        if isinstance(obj, SceneEntity):
            packets.append(_build_scene_entity_packet(obj))
        elif isinstance(obj, ScenePath):
            packets.append(_build_scene_path_packet(obj))
        elif isinstance(obj, SceneTrack):
            packets.append(_build_scene_track_packet(obj))
        elif isinstance(obj, SceneVector):
            packets.append(_build_scene_vector_packet(obj))
        elif isinstance(obj, SceneVelocityVector):
            packets.append(_build_scene_velocity_vector_packet(obj))
        elif isinstance(obj, SceneAccelerationVector):
            packets.append(_build_scene_acceleration_vector_packet(obj))
        elif isinstance(obj, SceneLineOfSight):
            packets.append(_build_scene_line_of_sight_packet(obj))
        elif isinstance(obj, SceneBodyAxes):
            packets.extend(_build_scene_axes_packets(obj, family="bodyAxes"))
        elif isinstance(obj, ScenePrincipalAxes):
            packets.extend(_build_scene_axes_packets(obj, family="principalAxes"))
        elif isinstance(obj, SceneRelativeLine):
            packets.append(_build_scene_relative_line_packet(obj))
        elif isinstance(obj, SceneInterceptLine):
            packets.append(_build_scene_intercept_line_packet(obj))
        elif isinstance(obj, SceneCameraView):
            packets.append(_build_scene_camera_view_packet(obj))
        elif isinstance(obj, SceneCustomObject):
            packets.append(_build_scene_custom_object_packet(obj))
        elif isinstance(obj, SceneRuntimeObject):
            packets.append(_build_scene_runtime_object_packet(obj))
        elif isinstance(obj, SceneTerrainSurface):
            packets.append(_build_scene_terrain_surface_packet(obj))
        elif isinstance(obj, SceneCustomMesh):
            packets.append(_build_scene_custom_mesh_packet(obj))
        elif isinstance(obj, SceneClippingPlane):
            packets.append(_build_scene_clipping_plane_packet(obj))
        elif isinstance(obj, SceneClippingPolygon):
            packets.append(_build_scene_clipping_polygon_packet(obj))
        elif isinstance(obj, SceneClassificationVolume):
            packets.append(_build_scene_classification_volume_packet(obj))
        elif isinstance(obj, SceneCustomShader):
            packets.append(_build_scene_custom_shader_packet(obj))
        elif isinstance(obj, ScenePostProcessStage):
            packets.append(_build_scene_post_process_stage_packet(obj))
        else:
            packets.append(_build_scene_overlay_packet(obj))
    return packets


def dump_cesium_document_json(
    message: EntityUpsertMessage,
    *,
    indent: int = 2,
    document_name: str = "VSS CZML",
) -> str:
    return dumps_json(
        compile_cesium_document(message, document_name=document_name),
        indent=indent,
    )


def dump_cesium_scene_json(
    scene: VssScene,
    *,
    indent: int = 2,
    document_name: str | None = None,
) -> str:
    return dumps_json(
        compile_cesium_scene(scene, document_name=document_name),
        indent=indent,
    )


def write_cesium_document(
    message: EntityUpsertMessage,
    path: str | Path,
    *,
    indent: int = 2,
    document_name: str = "VSS CZML",
) -> Path:
    return write_text_file(
        path,
        dump_cesium_document_json(message, indent=indent, document_name=document_name),
        encoding="utf-8",
    )


def write_cesium_scene(
    scene: VssScene,
    path: str | Path,
    *,
    indent: int = 2,
    document_name: str | None = None,
) -> Path:
    return write_text_file(
        path,
        dump_cesium_scene_json(scene, indent=indent, document_name=document_name),
        encoding="utf-8",
    )


def render_cesium_viewer_html(
    *,
    czml_path: str,
    title: str = "VSS Cesium Viewer",
    views: list[SceneView | SceneCameraView] | None = None,
    scene_metadata: dict[str, Any] | None = None,
) -> str:
    view_payload = dumps_json([view.model_dump(mode="json", exclude_none=True) for view in views or []], indent=2)
    metadata_payload = dumps_json(scene_metadata or {}, indent=2)
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title}</title>
    <script src="https://cesium.com/downloads/cesiumjs/releases/1.120/Build/Cesium/Cesium.js"></script>
    <link href="https://cesium.com/downloads/cesiumjs/releases/1.120/Build/Cesium/Widgets/widgets.css" rel="stylesheet">
    <style>
      html, body, #cesiumContainer {{
        margin: 0;
        width: 100%;
        height: 100%;
        overflow: hidden;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }}
      .overlay {{
        position: absolute;
        top: 16px;
        left: 16px;
        z-index: 1;
        max-width: 24rem;
        padding: 12px 14px;
        background: rgba(15, 23, 42, 0.82);
        color: #e2e8f0;
        border-radius: 10px;
        backdrop-filter: blur(10px);
      }}
      .overlay h1 {{
        margin: 0 0 8px;
        font-size: 16px;
      }}
      .overlay p {{
        margin: 0;
        font-size: 13px;
        line-height: 1.45;
      }}
      .overlay .view-controls {{
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 12px;
      }}
      .overlay .view-controls button {{
        border: 0;
        border-radius: 999px;
        padding: 8px 12px;
        background: #2563eb;
        color: white;
        font-size: 12px;
        font-weight: 600;
        cursor: pointer;
      }}
      .overlay .view-controls button:hover {{
        background: #1d4ed8;
      }}
      .overlay code {{
        font-size: 12px;
      }}
      .overlay details {{
        margin-top: 12px;
      }}
      .overlay pre {{
        margin: 8px 0 0;
        max-height: 12rem;
        overflow: auto;
        padding: 10px;
        background: rgba(15, 23, 42, 0.92);
        color: #cbd5e1;
        border-radius: 8px;
        font-size: 11px;
        white-space: pre-wrap;
      }}
    </style>
  </head>
  <body>
    <div class="overlay">
      <h1>{title}</h1>
      <p>Load this page through a local web server so Cesium can fetch <code>{czml_path}</code>.</p>
      <div class="view-controls" id="viewControls"></div>
      <details id="sceneMetadataPanel" hidden>
        <summary>Scene metadata</summary>
        <pre id="sceneMetadataText"></pre>
      </details>
    </div>
    <div id="cesiumContainer"></div>
    <script>
      const sceneViews = {view_payload};
      const sceneMetadata = {metadata_payload};
      const viewer = new Cesium.Viewer("cesiumContainer", {{
        animation: false,
        timeline: false,
        shouldAnimate: false
      }});
      let loadedDataSource = null;

      function activateSceneView(view) {{
        if (!loadedDataSource) {{
          return Promise.resolve();
        }}
        if (view.target) {{
          const entity = loadedDataSource.entities.getById(view.target);
          if (entity) {{
            const options = {{
              duration: view.durationSeconds ?? 1.5
            }};
            if (view.rangeMeters) {{
              options.offset = new Cesium.HeadingPitchRange(0.0, Cesium.Math.toRadians(-25.0), view.rangeMeters);
            }}
            return viewer.flyTo(entity, options);
          }}
        }}
        if (view.position) {{
          const orientation = view.orientation ? {{
            heading: Cesium.Math.toRadians(view.orientation.headingDeg || 0.0),
            pitch: Cesium.Math.toRadians(view.orientation.pitchDeg || 0.0),
            roll: Cesium.Math.toRadians(view.orientation.rollDeg || 0.0)
          }} : undefined;
          return viewer.camera.flyTo({{
            destination: Cesium.Cartesian3.fromDegrees(
              view.position.longitudeDeg,
              view.position.latitudeDeg,
              view.position.altitudeM
            ),
            orientation,
            duration: view.durationSeconds ?? 1.5
          }});
        }}
        return Promise.resolve();
      }}

      function renderViewControls() {{
        const container = document.getElementById("viewControls");
        container.innerHTML = "";
        if (!sceneViews.length) {{
          container.style.display = "none";
          return;
        }}
        sceneViews.forEach((view) => {{
          const button = document.createElement("button");
          button.textContent = view.name || view.id;
          button.title = view.target ? "Focus " + view.target : "Fly to " + button.textContent;
          button.addEventListener("click", () => activateSceneView(view).catch((error) => console.error("Failed to activate view", error)));
          container.appendChild(button);
        }});
      }}

      function renderSceneMetadata() {{
        const panel = document.getElementById("sceneMetadataPanel");
        const text = document.getElementById("sceneMetadataText");
        const hasMetadata = sceneMetadata && Object.keys(sceneMetadata).length > 0;
        if (!panel || !text || !hasMetadata) {{
          if (panel) {{
            panel.hidden = true;
          }}
          return;
        }}
        text.textContent = JSON.stringify(sceneMetadata, null, 2);
        panel.hidden = false;
      }}

      Cesium.CzmlDataSource.load("{czml_path}")
        .then((dataSource) => viewer.dataSources.add(dataSource))
        .then((dataSource) => {{
          loadedDataSource = dataSource;
          renderViewControls();
          renderSceneMetadata();
          return viewer.zoomTo(dataSource);
        }})
        .catch((error) => {{
          console.error("Failed to load CZML", error);
        }});
    </script>
  </body>
</html>
"""


def write_cesium_viewer(
    path: str | Path,
    *,
    czml_path: str,
    title: str = "VSS Cesium Viewer",
    views: list[SceneView | SceneCameraView] | None = None,
    scene_metadata: dict[str, Any] | None = None,
) -> Path:
    return write_text_file(
        path,
        render_cesium_viewer_html(czml_path=czml_path, title=title, views=views, scene_metadata=scene_metadata),
        encoding="utf-8",
    )


def _build_scene_entity_packet(
    entity: SceneEntity,
    *,
    attributes: dict[str, Any] | None = None,
) -> dict[str, Any]:
    packet: dict[str, Any] = {
        "id": entity.id,
        "name": entity.name,
        "position": {
            "cartographicDegrees": [
                entity.position.longitudeDeg,
                entity.position.latitudeDeg,
                entity.position.altitudeM,
            ]
        },
        "properties": dict(attributes or entity.attributes),
    }

    if entity.source and "source" not in packet["properties"]:
        packet["properties"]["source"] = entity.source
    if entity.timestamp and "timestamp" not in packet["properties"]:
        packet["properties"]["timestamp"] = entity.timestamp.isoformat()

    style = entity.style
    rgba = list(style.colorRgba) if style and style.colorRgba else None

    if style and style.label:
        packet["label"] = {
            "text": style.label,
            "horizontalOrigin": "LEFT",
            "pixelOffset": {"cartesian2": [12, 0]},
        }
        if rgba:
            packet["label"]["fillColor"] = {"rgba": rgba}

    if style and style.modelUri:
        packet["model"] = {
            "uri": str(style.modelUri),
            "scale": 1.0,
        }

    if style and style.iconUri:
        packet["billboard"] = {
            "image": str(style.iconUri),
            "scale": 1.0,
            "verticalOrigin": "BOTTOM",
        }

    point_packet: dict[str, Any] = {
        "pixelSize": 10,
        "outlineWidth": 1,
    }
    packet["point"] = point_packet
    if rgba:
        point_packet["color"] = {"rgba": rgba}
        point_packet["outlineColor"] = {"rgba": [255, 255, 255, 255]}

    if entity.orientation:
        packet["properties"]["orientationDegrees"] = {
            "heading": entity.orientation.headingDeg,
            "pitch": entity.orientation.pitchDeg,
            "roll": entity.orientation.rollDeg,
        }

    if entity.category:
        packet["properties"]["category"] = entity.category.value

    return packet


def _build_scene_overlay_packet(overlay: SceneOverlay) -> dict[str, Any]:
    packet: dict[str, Any] = {
        "id": overlay.id,
        "name": overlay.name,
        "position": {
            "cartographicDegrees": [
                overlay.position.longitudeDeg,
                overlay.position.latitudeDeg,
                overlay.position.altitudeM,
            ]
        },
        "properties": {
            **overlay.attributes,
            "objectType": "overlay",
            **({"source": overlay.source} if overlay.source else {}),
            **({"timestamp": overlay.timestamp.isoformat()} if overlay.timestamp else {}),
            "category": "overlay",
        },
    }

    style = overlay.style
    rgba = list(style.colorRgba) if style and style.colorRgba else None

    emitter_key = overlay.customGeometryType or overlay.geometryType
    custom_emitter = _CESIUM_OVERLAY_EMITTERS.get(emitter_key)
    if custom_emitter is not None:
        custom_packet = custom_emitter(overlay)
        if custom_packet is not None:
            return custom_packet

    if style and style.label:
        packet["label"] = {
            "text": style.label,
            "horizontalOrigin": "LEFT",
            "pixelOffset": {"cartesian2": [12, 0]},
        }
        if rgba:
            packet["label"]["fillColor"] = {"rgba": rgba}
    if overlay.geometryType == "polyline" and overlay.polyline:
        packet["polyline"] = {
            "positions": {
                "cartographicDegrees": _flatten_positions(overlay.polyline.positions)
            },
            "width": overlay.polyline.widthPx,
            "clampToGround": overlay.polyline.clampToGround,
        }
        if rgba:
            packet["polyline"]["material"] = {"solidColor": {"color": {"rgba": rgba}}}
    elif overlay.geometryType == "polygon" and overlay.polygon:
        packet["polygon"] = {
            "positions": {
                "cartographicDegrees": _flatten_positions(overlay.polygon.positions)
            },
            "perPositionHeight": not overlay.polygon.clampToGround,
            "arcType": "GEODESIC",
        }
        if rgba:
            packet["polygon"]["material"] = {"solidColor": {"color": {"rgba": rgba}}}
    elif overlay.geometryType == "rectangle" and overlay.rectangle:
        packet["rectangle"] = {
            "coordinates": {
                "wsenDegrees": list(overlay.rectangle.westSouthEastNorthDegrees)
            }
        }
        if overlay.rectangle.heightMeters is not None:
            packet["rectangle"]["height"] = overlay.rectangle.heightMeters
        if overlay.rectangle.extrudedHeightMeters is not None:
            packet["rectangle"]["extrudedHeight"] = overlay.rectangle.extrudedHeightMeters
        if overlay.rectangle.rotationDegrees is not None:
            packet["rectangle"]["rotation"] = overlay.rectangle.rotationDegrees
        if overlay.rectangle.stRotationDegrees is not None:
            packet["rectangle"]["stRotation"] = overlay.rectangle.stRotationDegrees
        if rgba:
            packet["rectangle"]["material"] = {"solidColor": {"color": {"rgba": rgba}}}
    elif overlay.geometryType == "corridor" and overlay.corridor:
        packet["corridor"] = {
            "positions": {
                "cartographicDegrees": _flatten_positions(overlay.corridor.positions)
            },
            "width": overlay.corridor.widthMeters,
            "clampToGround": overlay.corridor.clampToGround,
        }
        if overlay.corridor.heightMeters is not None:
            packet["corridor"]["height"] = overlay.corridor.heightMeters
        if overlay.corridor.extrudedHeightMeters is not None:
            packet["corridor"]["extrudedHeight"] = overlay.corridor.extrudedHeightMeters
        if overlay.corridor.cornerType is not None:
            packet["corridor"]["cornerType"] = overlay.corridor.cornerType.upper()
        if rgba:
            packet["corridor"]["material"] = {"solidColor": {"color": {"rgba": rgba}}}
    elif overlay.geometryType == "ellipse" and overlay.ellipse:
        packet["ellipse"] = {
            "semiMajorAxis": overlay.ellipse.semiMajorAxisMeters,
            "semiMinorAxis": overlay.ellipse.semiMinorAxisMeters,
        }
        if overlay.ellipse.heightMeters is not None:
            packet["ellipse"]["height"] = overlay.ellipse.heightMeters
        if overlay.ellipse.extrudedHeightMeters is not None:
            packet["ellipse"]["extrudedHeight"] = overlay.ellipse.extrudedHeightMeters
        if overlay.ellipse.rotationDegrees is not None:
            packet["ellipse"]["rotation"] = overlay.ellipse.rotationDegrees
        if overlay.ellipse.stRotationDegrees is not None:
            packet["ellipse"]["stRotation"] = overlay.ellipse.stRotationDegrees
        if overlay.ellipse.clampToGround:
            packet["ellipse"]["clampToGround"] = True
        if rgba:
            packet["ellipse"]["material"] = {"solidColor": {"color": {"rgba": rgba}}}
    elif overlay.geometryType == "covarianceEllipse" and overlay.covarianceEllipse:
        ellipse = overlay.covarianceEllipse
        packet["ellipse"] = {
            "semiMajorAxis": ellipse.semiMajorAxisMeters,
            "semiMinorAxis": ellipse.semiMinorAxisMeters,
        }
        if ellipse.heightMeters is not None:
            packet["ellipse"]["height"] = ellipse.heightMeters
        if ellipse.extrudedHeightMeters is not None:
            packet["ellipse"]["extrudedHeight"] = ellipse.extrudedHeightMeters
        if ellipse.rotationDegrees is not None:
            packet["ellipse"]["rotation"] = ellipse.rotationDegrees
        if ellipse.stRotationDegrees is not None:
            packet["ellipse"]["stRotation"] = ellipse.stRotationDegrees
        if ellipse.clampToGround:
            packet["ellipse"]["clampToGround"] = True
        packet["properties"]["shapeType"] = "covarianceEllipse"
        packet["properties"]["covarianceEllipse"] = {
            "semiMajorAxisMeters": ellipse.semiMajorAxisMeters,
            "semiMinorAxisMeters": ellipse.semiMinorAxisMeters,
            "heightMeters": ellipse.heightMeters,
            "extrudedHeightMeters": ellipse.extrudedHeightMeters,
            "rotationDegrees": ellipse.rotationDegrees,
            "stRotationDegrees": ellipse.stRotationDegrees,
            "clampToGround": ellipse.clampToGround,
        }
        if rgba:
            packet["ellipse"]["material"] = {"solidColor": {"color": {"rgba": rgba}}}
    elif overlay.geometryType == "circle" and overlay.circle:
        packet["ellipse"] = {
            "semiMajorAxis": overlay.circle.radiusMeters,
            "semiMinorAxis": overlay.circle.radiusMeters,
        }
        if overlay.circle.heightMeters is not None:
            packet["ellipse"]["height"] = overlay.circle.heightMeters
        if overlay.circle.extrudedHeightMeters is not None:
            packet["ellipse"]["extrudedHeight"] = overlay.circle.extrudedHeightMeters
        if overlay.circle.rotationDegrees is not None:
            packet["ellipse"]["rotation"] = overlay.circle.rotationDegrees
        if overlay.circle.stRotationDegrees is not None:
            packet["ellipse"]["stRotation"] = overlay.circle.stRotationDegrees
        if overlay.circle.clampToGround:
            packet["ellipse"]["clampToGround"] = True
        if rgba:
            packet["ellipse"]["material"] = {"solidColor": {"color": {"rgba": rgba}}}
    elif overlay.geometryType == "rangeRing" and overlay.rangeRing:
        ring = overlay.rangeRing
        packet["ellipse"] = {
            "semiMajorAxis": ring.radiusMeters,
            "semiMinorAxis": ring.radiusMeters,
            "fill": False,
            "outline": True,
        }
        packet["properties"]["shapeType"] = "rangeRing"
        packet["properties"]["rangeRing"] = {
            "radiusMeters": ring.radiusMeters,
            "heightMeters": ring.heightMeters,
            "extrudedHeightMeters": ring.extrudedHeightMeters,
            "rotationDegrees": ring.rotationDegrees,
            "stRotationDegrees": ring.stRotationDegrees,
            "outlineWidthPx": ring.outlineWidthPx,
            "clampToGround": ring.clampToGround,
        }
        if ring.heightMeters is not None:
            packet["ellipse"]["height"] = ring.heightMeters
        if ring.extrudedHeightMeters is not None:
            packet["ellipse"]["extrudedHeight"] = ring.extrudedHeightMeters
        if ring.rotationDegrees is not None:
            packet["ellipse"]["rotation"] = ring.rotationDegrees
        if ring.stRotationDegrees is not None:
            packet["ellipse"]["stRotation"] = ring.stRotationDegrees
        if ring.clampToGround:
            packet["ellipse"]["clampToGround"] = True
        packet["ellipse"]["outlineWidth"] = ring.outlineWidthPx
        if rgba:
            packet["ellipse"]["outlineColor"] = {"rgba": rgba}
    elif overlay.geometryType == "wall" and overlay.wall:
        packet["wall"] = {
            "positions": {
                "cartographicDegrees": _flatten_positions(overlay.wall.positions)
            },
            "maximumHeights": overlay.wall.maximumHeightsMeters
            if overlay.wall.maximumHeightsMeters is not None
            else [pos.altitudeM for pos in overlay.wall.positions],
            "minimumHeights": overlay.wall.minimumHeightsMeters
            if overlay.wall.minimumHeightsMeters is not None
            else [0.0 for _ in overlay.wall.positions],
            "clampToGround": overlay.wall.clampToGround,
        }
        if rgba:
            packet["wall"]["material"] = {"solidColor": {"color": {"rgba": rgba}}}
    elif overlay.geometryType == "box" and overlay.box:
        packet["box"] = {
            "dimensions": {"cartesian": list(overlay.box.dimensionsMeters)}
        }
        if rgba:
            packet["box"]["material"] = {"solidColor": {"color": {"rgba": rgba}}}
    elif overlay.geometryType == "cylinder" and overlay.cylinder:
        packet["cylinder"] = {
            "length": overlay.cylinder.lengthMeters,
            "topRadius": overlay.cylinder.topRadiusMeters,
            "bottomRadius": overlay.cylinder.bottomRadiusMeters,
        }
        if overlay.cylinder.numberOfSides is not None:
            packet["cylinder"]["numberOfVerticalLines"] = overlay.cylinder.numberOfSides
        if overlay.cylinder.slope is not None:
            packet["cylinder"]["slope"] = overlay.cylinder.slope
        if rgba:
            packet["cylinder"]["material"] = {"solidColor": {"color": {"rgba": rgba}}}
    elif overlay.geometryType == "cone" and overlay.cone:
        packet["agi_conicSensor"] = {
            "radius": overlay.cone.radiusMeters,
            "innerHalfAngle": math.radians(overlay.cone.innerHalfAngleDegrees)
            if overlay.cone.innerHalfAngleDegrees is not None
            else 0.0,
            "outerHalfAngle": math.radians(overlay.cone.outerHalfAngleDegrees),
        }
        if overlay.cone.minimumClockAngleDegrees is not None:
            packet["agi_conicSensor"]["minimumClockAngle"] = math.radians(overlay.cone.minimumClockAngleDegrees)
        if overlay.cone.maximumClockAngleDegrees is not None:
            packet["agi_conicSensor"]["maximumClockAngle"] = math.radians(overlay.cone.maximumClockAngleDegrees)
        if overlay.cone.showIntersection is not None:
            packet["agi_conicSensor"]["showIntersection"] = overlay.cone.showIntersection
        if overlay.cone.intersectionWidthPx is not None:
            packet["agi_conicSensor"]["intersectionWidth"] = overlay.cone.intersectionWidthPx
        if overlay.orientation:
            packet["orientation"] = {
                "unitQuaternion": _orientation_to_unit_quaternion(overlay.orientation)
            }
            packet["properties"]["orientationDegrees"] = {
                "heading": overlay.orientation.headingDeg,
                "pitch": overlay.orientation.pitchDeg,
                "roll": overlay.orientation.rollDeg,
            }
        if rgba:
            packet["agi_conicSensor"]["capMaterial"] = {"solidColor": {"color": {"rgba": rgba}}}
            packet["agi_conicSensor"]["outerMaterial"] = {"solidColor": {"color": {"rgba": rgba}}}
            packet["agi_conicSensor"]["innerMaterial"] = {"solidColor": {"color": {"rgba": rgba}}}
    elif overlay.geometryType == "conicSensor" and overlay.conicSensor:
        packet["agi_conicSensor"] = {
            "radius": overlay.conicSensor.radiusMeters,
            "innerHalfAngle": math.radians(overlay.conicSensor.innerHalfAngleDegrees)
            if overlay.conicSensor.innerHalfAngleDegrees is not None
            else 0.0,
            "outerHalfAngle": math.radians(overlay.conicSensor.outerHalfAngleDegrees),
        }
        if overlay.conicSensor.minimumClockAngleDegrees is not None:
            packet["agi_conicSensor"]["minimumClockAngle"] = math.radians(overlay.conicSensor.minimumClockAngleDegrees)
        if overlay.conicSensor.maximumClockAngleDegrees is not None:
            packet["agi_conicSensor"]["maximumClockAngle"] = math.radians(overlay.conicSensor.maximumClockAngleDegrees)
        if overlay.conicSensor.showIntersection is not None:
            packet["agi_conicSensor"]["showIntersection"] = overlay.conicSensor.showIntersection
        if overlay.conicSensor.intersectionWidthPx is not None:
            packet["agi_conicSensor"]["intersectionWidth"] = overlay.conicSensor.intersectionWidthPx
        if overlay.orientation:
            packet["orientation"] = {
                "unitQuaternion": _orientation_to_unit_quaternion(overlay.orientation)
            }
            packet["properties"]["orientationDegrees"] = {
                "heading": overlay.orientation.headingDeg,
                "pitch": overlay.orientation.pitchDeg,
                "roll": overlay.orientation.rollDeg,
            }
        if rgba:
            packet["agi_conicSensor"]["capMaterial"] = {"solidColor": {"color": {"rgba": rgba}}}
            packet["agi_conicSensor"]["outerMaterial"] = {"solidColor": {"color": {"rgba": rgba}}}
            packet["agi_conicSensor"]["innerMaterial"] = {"solidColor": {"color": {"rgba": rgba}}}
    elif overlay.geometryType == "rectangularSensor" and overlay.rectangularSensor:
        packet["agi_rectangularSensor"] = {
            "radius": overlay.rectangularSensor.radiusMeters,
            "xHalfAngle": math.radians(overlay.rectangularSensor.xHalfAngleDegrees),
            "yHalfAngle": math.radians(overlay.rectangularSensor.yHalfAngleDegrees),
        }
        if overlay.rectangularSensor.showIntersection is not None:
            packet["agi_rectangularSensor"]["showIntersection"] = overlay.rectangularSensor.showIntersection
        if overlay.rectangularSensor.intersectionWidthPx is not None:
            packet["agi_rectangularSensor"]["intersectionWidth"] = overlay.rectangularSensor.intersectionWidthPx
        if overlay.rectangularSensor.showLateralSurfaces is not None:
            packet["agi_rectangularSensor"]["showLateralSurfaces"] = overlay.rectangularSensor.showLateralSurfaces
        if overlay.rectangularSensor.showDomeSurfaces is not None:
            packet["agi_rectangularSensor"]["showDomeSurfaces"] = overlay.rectangularSensor.showDomeSurfaces
        if overlay.orientation:
            packet["orientation"] = {
                "unitQuaternion": _orientation_to_unit_quaternion(overlay.orientation)
            }
            packet["properties"]["orientationDegrees"] = {
                "heading": overlay.orientation.headingDeg,
                "pitch": overlay.orientation.pitchDeg,
                "roll": overlay.orientation.rollDeg,
            }
        if rgba:
            packet["agi_rectangularSensor"]["lateralSurfaceMaterial"] = {"solidColor": {"color": {"rgba": rgba}}}
    elif overlay.geometryType == "frustum" and overlay.frustum:
        frustum = overlay.frustum
        h_fov = frustum.horizontalFovDegrees
        if h_fov is None and frustum.outerHalfAngleDegrees is not None:
            h_fov = frustum.outerHalfAngleDegrees * 2.0
        if h_fov is None:
            h_fov = 30.0
        v_fov = frustum.verticalFovDegrees
        if v_fov is None:
            v_fov = h_fov / frustum.aspectRatio if frustum.aspectRatio else h_fov
        width = 2.0 * frustum.farMeters * math.tan(math.radians(h_fov) / 2.0)
        height = 2.0 * frustum.farMeters * math.tan(math.radians(v_fov) / 2.0)
        depth = max(frustum.farMeters - frustum.nearMeters, 0.0)
        packet["box"] = {
            "dimensions": {
                "cartesian": [depth, width, height]
            }
        }
        packet["properties"]["shapeType"] = "frustum"
        packet["properties"]["frustum"] = {
            "nearMeters": frustum.nearMeters,
            "farMeters": frustum.farMeters,
            "horizontalFovDegrees": frustum.horizontalFovDegrees,
            "verticalFovDegrees": frustum.verticalFovDegrees,
            "innerHalfAngleDegrees": frustum.innerHalfAngleDegrees,
            "outerHalfAngleDegrees": frustum.outerHalfAngleDegrees,
            "aspectRatio": frustum.aspectRatio,
            "windingOrder": frustum.windingOrder,
            "closed": frustum.closed,
        }
        if overlay.orientation:
            packet["orientation"] = {
                "unitQuaternion": _orientation_to_unit_quaternion(overlay.orientation)
            }
            packet["properties"]["orientationDegrees"] = {
                "heading": overlay.orientation.headingDeg,
                "pitch": overlay.orientation.pitchDeg,
                "roll": overlay.orientation.rollDeg,
            }
        if rgba:
            packet["box"]["material"] = {"solidColor": {"color": {"rgba": rgba}}}
    elif overlay.geometryType == "sector2d" and overlay.sector2d:
        sector = overlay.sector2d
        packet["polygon"] = {
            "positions": {
                "cartographicDegrees": _sector_polygon_positions(overlay.position, sector)
            },
            "perPositionHeight": True,
            "arcType": "GEODESIC",
        }
        packet["properties"]["shapeType"] = "sector2d"
        packet["properties"]["sector2d"] = {
            "innerRadiusMeters": sector.innerRadiusMeters,
            "outerRadiusMeters": sector.outerRadiusMeters,
            "azimuthStartDegrees": sector.azimuthStartDegrees,
            "azimuthStopDegrees": sector.azimuthStopDegrees,
            "elevationStartDegrees": sector.elevationStartDegrees,
            "elevationStopDegrees": sector.elevationStopDegrees,
            "heightMeters": sector.heightMeters,
            "segments": sector.segments,
            "mode": sector.mode,
            "windingOrder": sector.windingOrder,
            "closed": sector.closed,
        }
        if rgba:
            packet["polygon"]["material"] = {"solidColor": {"color": {"rgba": rgba}}}
    elif overlay.geometryType == "customPatternSensor" and overlay.customPatternSensor:
        sector = overlay.customPatternSensor
        packet["polygon"] = {
            "positions": {
                "cartographicDegrees": _sector_polygon_positions(overlay.position, sector)
            },
            "perPositionHeight": True,
            "arcType": "GEODESIC",
        }
        packet["properties"]["shapeType"] = "customPatternSensor"
        packet["properties"]["customPatternSensor"] = {
            "innerRadiusMeters": sector.innerRadiusMeters,
            "outerRadiusMeters": sector.outerRadiusMeters,
            "azimuthStartDegrees": sector.azimuthStartDegrees,
            "azimuthStopDegrees": sector.azimuthStopDegrees,
            "elevationStartDegrees": sector.elevationStartDegrees,
            "elevationStopDegrees": sector.elevationStopDegrees,
            "patternAzimuthElevationDegrees": sector.patternAzimuthElevationDegrees,
            "heightMeters": sector.heightMeters,
            "segments": sector.segments,
            "mode": sector.mode,
            "windingOrder": sector.windingOrder,
            "closed": sector.closed,
        }
        if overlay.orientation:
            packet["orientation"] = {
                "unitQuaternion": _orientation_to_unit_quaternion(overlay.orientation)
            }
            packet["properties"]["orientationDegrees"] = {
                "heading": overlay.orientation.headingDeg,
                "pitch": overlay.orientation.pitchDeg,
                "roll": overlay.orientation.rollDeg,
            }
        if rgba:
            packet["polygon"]["material"] = {"solidColor": {"color": {"rgba": rgba}}}
    elif overlay.geometryType == "bearingFan" and overlay.bearingFan:
        sector = overlay.bearingFan
        packet["polygon"] = {
            "positions": {
                "cartographicDegrees": _sector_polygon_positions(overlay.position, sector)
            },
            "perPositionHeight": True,
            "arcType": "GEODESIC",
        }
        packet["properties"]["shapeType"] = "bearingFan"
        packet["properties"]["bearingFan"] = {
            "innerRadiusMeters": sector.innerRadiusMeters,
            "outerRadiusMeters": sector.outerRadiusMeters,
            "azimuthStartDegrees": sector.azimuthStartDegrees,
            "azimuthStopDegrees": sector.azimuthStopDegrees,
            "elevationStartDegrees": sector.elevationStartDegrees,
            "elevationStopDegrees": sector.elevationStopDegrees,
            "heightMeters": sector.heightMeters,
            "segments": sector.segments,
            "mode": sector.mode,
            "windingOrder": sector.windingOrder,
            "closed": sector.closed,
        }
        if overlay.orientation:
            packet["orientation"] = {
                "unitQuaternion": _orientation_to_unit_quaternion(overlay.orientation)
            }
            packet["properties"]["orientationDegrees"] = {
                "heading": overlay.orientation.headingDeg,
                "pitch": overlay.orientation.pitchDeg,
                "roll": overlay.orientation.rollDeg,
            }
        if rgba:
            packet["polygon"]["material"] = {"solidColor": {"color": {"rgba": rgba}}}
    elif overlay.geometryType == "fan" and overlay.fan:
        sector = overlay.fan
        packet["polygon"] = {
            "positions": {
                "cartographicDegrees": _sector_polygon_positions(overlay.position, sector)
            },
            "perPositionHeight": True,
            "arcType": "GEODESIC",
        }
        packet["properties"]["shapeType"] = "fan"
        packet["properties"]["fan"] = {
            "innerRadiusMeters": sector.innerRadiusMeters,
            "outerRadiusMeters": sector.outerRadiusMeters,
            "azimuthStartDegrees": sector.azimuthStartDegrees,
            "azimuthStopDegrees": sector.azimuthStopDegrees,
            "elevationStartDegrees": sector.elevationStartDegrees,
            "elevationStopDegrees": sector.elevationStopDegrees,
            "heightMeters": sector.heightMeters,
            "segments": sector.segments,
            "mode": sector.mode,
            "windingOrder": sector.windingOrder,
            "closed": sector.closed,
        }
        if overlay.orientation:
            packet["orientation"] = {
                "unitQuaternion": _orientation_to_unit_quaternion(overlay.orientation)
            }
            packet["properties"]["orientationDegrees"] = {
                "heading": overlay.orientation.headingDeg,
                "pitch": overlay.orientation.pitchDeg,
                "roll": overlay.orientation.rollDeg,
            }
        if rgba:
            packet["polygon"]["material"] = {"solidColor": {"color": {"rgba": rgba}}}
    elif overlay.geometryType == "sectorVolume" and overlay.sectorVolume:
        sector = overlay.sectorVolume
        packet["polygon"] = {
            "positions": {
                "cartographicDegrees": _sector_polygon_positions(overlay.position, sector)
            },
            "perPositionHeight": True,
            "arcType": "GEODESIC",
        }
        packet["properties"]["shapeType"] = "sectorVolume"
        packet["properties"]["sectorVolume"] = {
            "innerRadiusMeters": sector.innerRadiusMeters,
            "outerRadiusMeters": sector.outerRadiusMeters,
            "azimuthStartDegrees": sector.azimuthStartDegrees,
            "azimuthStopDegrees": sector.azimuthStopDegrees,
            "elevationStartDegrees": sector.elevationStartDegrees,
            "elevationStopDegrees": sector.elevationStopDegrees,
            "heightMeters": sector.heightMeters,
            "segments": sector.segments,
            "mode": sector.mode,
            "windingOrder": sector.windingOrder,
            "closed": sector.closed,
        }
        if sector.heightMeters is not None:
            packet["polygon"]["extrudedHeight"] = overlay.position.altitudeM + sector.heightMeters
        if rgba:
            packet["polygon"]["material"] = {"solidColor": {"color": {"rgba": rgba}}}
    elif overlay.geometryType == "hemisphere" and overlay.hemisphere:
        radius = overlay.hemisphere.radiusMeters
        packet["ellipsoid"] = {
            "radii": {"cartesian": [radius, radius, radius]}
        }
        packet["properties"]["shapeType"] = "hemisphere"
        packet["properties"]["hemisphere"] = {
            "radiusMeters": radius,
        }
        if rgba:
            packet["ellipsoid"]["material"] = {"solidColor": {"color": {"rgba": rgba}}}
    elif overlay.geometryType == "sphericalCap" and overlay.sphericalCap:
        cap = overlay.sphericalCap
        packet["ellipsoid"] = {
            "radii": {"cartesian": [cap.radiusMeters, cap.radiusMeters, cap.radiusMeters]}
        }
        packet["properties"]["shapeType"] = "sphericalCap"
        packet["properties"]["sphericalCap"] = {
            "radiusMeters": cap.radiusMeters,
            "innerRadiusMeters": cap.innerRadiusMeters,
            "portion": cap.portion,
            "azimuthStartDegrees": cap.azimuthStartDegrees,
            "azimuthStopDegrees": cap.azimuthStopDegrees,
            "segments": cap.segments,
            "windingOrder": cap.windingOrder,
            "closed": cap.closed,
            "azimuthSegments": cap.azimuthSegments,
            "elevationSegments": cap.elevationSegments,
            "elevationStartDegrees": cap.elevationStartDegrees,
            "elevationStopDegrees": cap.elevationStopDegrees,
        }
        if rgba:
            packet["ellipsoid"]["material"] = {"solidColor": {"color": {"rgba": rgba}}}
    elif overlay.geometryType == "keyhole" and overlay.keyhole:
        sector = overlay.keyhole
        packet["polygon"] = {
            "positions": {
                "cartographicDegrees": _sector_polygon_positions(overlay.position, sector)
            },
            "perPositionHeight": True,
            "arcType": "GEODESIC",
        }
        packet["properties"]["shapeType"] = "keyhole"
        packet["properties"]["keyhole"] = {
            "innerRadiusMeters": sector.innerRadiusMeters,
            "outerRadiusMeters": sector.outerRadiusMeters,
            "azimuthStartDegrees": sector.azimuthStartDegrees,
            "azimuthStopDegrees": sector.azimuthStopDegrees,
            "elevationStartDegrees": sector.elevationStartDegrees,
            "elevationStopDegrees": sector.elevationStopDegrees,
            "segments": sector.segments,
            "mode": sector.mode,
            "windingOrder": sector.windingOrder,
            "closed": sector.closed,
        }
        if rgba:
            packet["polygon"]["material"] = {"solidColor": {"color": {"rgba": rgba}}}
    elif overlay.geometryType == "polylineVolume" and overlay.polylineVolume:
        packet["polylineVolume"] = {
            "positions": {
                "cartographicDegrees": _flatten_positions(overlay.polylineVolume.positions)
            },
            "shape": {
                "cartesian": _flatten_shape_positions(overlay.polylineVolume.shapePositions)
            },
        }
        if overlay.polylineVolume.cornerType is not None:
            packet["polylineVolume"]["cornerType"] = overlay.polylineVolume.cornerType.upper()
        if rgba:
            packet["polylineVolume"]["material"] = {"solidColor": {"color": {"rgba": rgba}}}
    elif overlay.geometryType == "plane" and overlay.plane:
        packet["plane"] = {
            "plane": {
                "normal": {"cartesian": list(overlay.plane.normal)},
                "distance": overlay.plane.distanceMeters,
            },
            "dimensions": {
                "cartesian": [overlay.plane.widthMeters, overlay.plane.heightMeters]
            },
            "fill": True,
            "outline": False,
        }
        if rgba:
            packet["plane"]["material"] = {"solidColor": {"color": {"rgba": rgba}}}
    elif overlay.geometryType == "tileset" and overlay.tileset:
        packet["tileset"] = {
            "uri": overlay.tileset.uri,
        }
    elif overlay.geometryType == "ellipsoid" and overlay.ellipsoid:
        packet["ellipsoid"] = {
            "radii": {"cartesian": list(overlay.ellipsoid.radiiMeters)}
        }
        if rgba:
            packet["ellipsoid"]["material"] = {"solidColor": {"color": {"rgba": rgba}}}
    elif overlay.geometryType == "uncertaintyEllipsoid" and overlay.uncertaintyEllipsoid:
        ellipsoid = overlay.uncertaintyEllipsoid
        packet["ellipsoid"] = {
            "radii": {"cartesian": list(ellipsoid.radiiMeters)}
        }
        packet["properties"]["shapeType"] = "uncertaintyEllipsoid"
        packet["properties"]["uncertaintyEllipsoid"] = {
            "radiiMeters": list(ellipsoid.radiiMeters),
            "slicePartitions": ellipsoid.slicePartitions,
            "stackPartitions": ellipsoid.stackPartitions,
        }
        if rgba:
            packet["ellipsoid"]["material"] = {"solidColor": {"color": {"rgba": rgba}}}
    elif overlay.geometryType == "sphere" and overlay.sphere:
        packet["ellipsoid"] = {
            "radii": {"cartesian": [overlay.sphere.radiusMeters] * 3}
        }
        if rgba:
            packet["ellipsoid"]["material"] = {"solidColor": {"color": {"rgba": rgba}}}
    elif overlay.geometryType == "particleSystem" and overlay.particleSystem:
        particle = overlay.particleSystem
        packet["particleSystem"] = _build_particle_system_packet(particle)
        packet["properties"]["shapeType"] = "particleSystem"
        packet["properties"]["particleSystem"] = {
            "asset": particle.asset,
            "image": particle.image,
            "emitter": particle.emitter,
            "emissionRate": particle.emissionRate,
            "lifetimeSeconds": particle.lifetimeSeconds,
            "particleLifeSeconds": particle.particleLifeSeconds,
            "minimumParticleLifeSeconds": particle.minimumParticleLifeSeconds,
            "maximumParticleLifeSeconds": particle.maximumParticleLifeSeconds,
            "speedMetersPerSecond": particle.speedMetersPerSecond,
            "minimumSpeedMetersPerSecond": particle.minimumSpeedMetersPerSecond,
            "maximumSpeedMetersPerSecond": particle.maximumSpeedMetersPerSecond,
            "scale": particle.scale,
            "startScale": particle.startScale,
            "endScale": particle.endScale,
            "imageSize": list(particle.imageSize) if particle.imageSize is not None else None,
            "startColor": list(particle.startColor) if particle.startColor is not None else None,
            "endColor": list(particle.endColor) if particle.endColor is not None else None,
        }
    elif overlay.geometryType == "custom":
        packet["properties"]["shapeType"] = "custom"
        if overlay.customGeometryType is not None:
            packet["properties"]["customGeometryType"] = overlay.customGeometryType
    elif overlay.geometryType == "voxel" and overlay.voxel:
        voxel = overlay.voxel
        if voxel.dimensionsMeters is not None:
            packet["box"] = {
                "dimensions": {"cartesian": list(voxel.dimensionsMeters)},
                "fill": True,
                "outline": False,
            }
            if rgba:
                packet["box"]["material"] = {"solidColor": {"color": {"rgba": rgba}}}
        packet["properties"]["shapeType"] = "voxel"
        packet["properties"]["voxel"] = {
            "semanticKind": voxel.semanticKind,
            "grid": voxel.grid,
            "dimensionsMeters": list(voxel.dimensionsMeters) if voxel.dimensionsMeters is not None else None,
            "note": voxel.note,
            "extensions": voxel.extensions,
        }

    return packet


def _build_particle_system_packet(particle: SceneParticleSystem) -> dict[str, Any]:
    packet: dict[str, Any] = {}
    if particle.image is not None:
        packet["image"] = particle.image
    if particle.emitter is not None:
        packet["emitter"] = particle.emitter
    if particle.emissionRate is not None:
        packet["emissionRate"] = particle.emissionRate
    if particle.lifetimeSeconds is not None:
        packet["lifetime"] = particle.lifetimeSeconds
    if particle.particleLifeSeconds is not None:
        packet["particleLife"] = particle.particleLifeSeconds
    if particle.minimumParticleLifeSeconds is not None:
        packet["minimumParticleLife"] = particle.minimumParticleLifeSeconds
    if particle.maximumParticleLifeSeconds is not None:
        packet["maximumParticleLife"] = particle.maximumParticleLifeSeconds
    if particle.speedMetersPerSecond is not None:
        packet["speed"] = particle.speedMetersPerSecond
    if particle.minimumSpeedMetersPerSecond is not None:
        packet["minimumSpeed"] = particle.minimumSpeedMetersPerSecond
    if particle.maximumSpeedMetersPerSecond is not None:
        packet["maximumSpeed"] = particle.maximumSpeedMetersPerSecond
    if particle.scale is not None:
        packet["scale"] = particle.scale
    if particle.startScale is not None:
        packet["startScale"] = particle.startScale
    if particle.endScale is not None:
        packet["endScale"] = particle.endScale
    if particle.imageSize is not None:
        packet["imageSize"] = {"cartesian2": list(particle.imageSize)}
    if particle.startColor is not None:
        packet["startColor"] = {"rgba": _float_color_to_rgba(particle.startColor)}
    if particle.endColor is not None:
        packet["endColor"] = {"rgba": _float_color_to_rgba(particle.endColor)}
    return packet


def _float_color_to_rgba(color: tuple[float, float, float, float]) -> list[int]:
    return [max(0, min(255, round(component * 255.0))) for component in color]


def _orientation_to_unit_quaternion(orientation: Any) -> list[float]:
    heading = math.radians(orientation.headingDeg or 0.0)
    pitch = math.radians(orientation.pitchDeg or 0.0)
    roll = math.radians(orientation.rollDeg or 0.0)
    cy = math.cos(heading * 0.5)
    sy = math.sin(heading * 0.5)
    cp = math.cos(pitch * 0.5)
    sp = math.sin(pitch * 0.5)
    cr = math.cos(roll * 0.5)
    sr = math.sin(roll * 0.5)
    x = sr * cp * cy - cr * sp * sy
    y = cr * sp * cy + sr * cp * sy
    z = cr * cp * sy - sr * sp * cy
    w = cr * cp * cy + sr * sp * sy
    return [x, y, z, w]


def _build_scene_path_packet(path: ScenePath) -> dict[str, Any]:
    ordered_samples = sorted(path.samples, key=lambda sample: sample.timestamp)
    epoch = ordered_samples[0].timestamp.isoformat()
    packet: dict[str, Any] = {
        "id": path.id,
        "name": path.name,
        "availability": f"{ordered_samples[0].timestamp.isoformat()}/{ordered_samples[-1].timestamp.isoformat()}",
        "position": {
            "epoch": epoch,
            "cartographicDegrees": _flatten_sampled_positions(ordered_samples, epoch=ordered_samples[0].timestamp),
        },
        "path": {
            "leadTime": 0,
            "trailTime": 300,
            "width": path.widthPx,
            "show": True,
            "resolution": 60,
            "material": {"solidColor": {"color": {"rgba": [255, 255, 255, 255]}}},
            "clampToGround": path.clampToGround,
        },
        "point": {
            "pixelSize": 8,
            "outlineWidth": 1,
        },
        "properties": {
            **path.attributes,
            "objectType": "path",
            "category": "path",
            **({"source": path.source} if path.source else {}),
            **({"timestamp": path.timestamp.isoformat()} if path.timestamp else {}),
        },
    }
    if path.style and path.style.label:
        packet["label"] = {
            "text": path.style.label,
            "horizontalOrigin": "LEFT",
            "pixelOffset": {"cartesian2": [12, 0]},
        }
    rgba = list(path.style.colorRgba) if path.style and path.style.colorRgba else None
    if rgba:
        packet["path"]["material"] = {"solidColor": {"color": {"rgba": rgba}}}
        packet["point"]["color"] = {"rgba": rgba}
        packet["point"]["outlineColor"] = {"rgba": [255, 255, 255, 255]}
        if "label" in packet:
            packet["label"]["fillColor"] = {"rgba": rgba}
    packet["position"] = {
        "epoch": epoch,
        "cartographicDegrees": _flatten_sampled_positions(ordered_samples, epoch=ordered_samples[0].timestamp),
    }
    return packet


def _flatten_shape_positions(points: list[tuple[float, float]]) -> list[float]:
    values: list[float] = []
    for x, y in points:
        values.extend([x, y])
    return values


def _destination_point(lon_deg: float, lat_deg: float, distance_m: float, bearing_deg: float) -> tuple[float, float]:
    radius_m = 6378137.0
    angular_distance = distance_m / radius_m
    bearing = math.radians(bearing_deg)
    lat1 = math.radians(lat_deg)
    lon1 = math.radians(lon_deg)
    sin_lat1 = math.sin(lat1)
    cos_lat1 = math.cos(lat1)
    sin_ang = math.sin(angular_distance)
    cos_ang = math.cos(angular_distance)
    lat2 = math.asin(sin_lat1 * cos_ang + cos_lat1 * sin_ang * math.cos(bearing))
    lon2 = lon1 + math.atan2(
        math.sin(bearing) * sin_ang * cos_lat1,
        cos_ang - sin_lat1 * math.sin(lat2),
    )
    return math.degrees(lon2), math.degrees(lat2)


def _sector_polygon_positions(center: Wgs84Position, sector: Any) -> list[float]:
    start = sector.azimuthStartDegrees
    stop = sector.azimuthStopDegrees
    if stop <= start:
        stop += 360.0
    segments = max(sector.segments, 3)
    altitude = center.altitudeM + (getattr(sector, "heightMeters", None) or 0.0)
    outer_bearings = [start + (stop - start) * index / segments for index in range(segments + 1)]
    positions: list[float] = []
    if sector.innerRadiusMeters and sector.innerRadiusMeters > 0:
        for bearing in outer_bearings:
            lon, lat = _destination_point(center.longitudeDeg, center.latitudeDeg, sector.outerRadiusMeters, bearing)
            positions.extend([lon, lat, altitude])
        for bearing in reversed(outer_bearings):
            lon, lat = _destination_point(center.longitudeDeg, center.latitudeDeg, sector.innerRadiusMeters, bearing)
            positions.extend([lon, lat, altitude])
    else:
        positions.extend([center.longitudeDeg, center.latitudeDeg, altitude])
        for bearing in outer_bearings:
            lon, lat = _destination_point(center.longitudeDeg, center.latitudeDeg, sector.outerRadiusMeters, bearing)
            positions.extend([lon, lat, altitude])
    return positions


def _build_scene_track_packet(track: SceneTrack) -> dict[str, Any]:
    ordered_samples = sorted(track.samples, key=lambda sample: sample.timestamp)
    epoch = ordered_samples[0].timestamp.isoformat()
    packet: dict[str, Any] = {
        "id": track.id,
        "name": track.name,
        "availability": f"{ordered_samples[0].timestamp.isoformat()}/{ordered_samples[-1].timestamp.isoformat()}",
        "position": {
            "epoch": epoch,
            "cartographicDegrees": _flatten_sampled_positions(ordered_samples, epoch=ordered_samples[0].timestamp),
        },
        "path": {
            "leadTime": 0,
            "trailTime": 300,
            "width": track.widthPx,
            "show": True,
            "resolution": 60,
            "clampToGround": track.clampToGround,
        },
        "point": {
            "pixelSize": 8,
            "outlineWidth": 1,
        },
        "properties": {
            **track.attributes,
            "objectType": "track",
            "category": "track",
            **({"source": track.source} if track.source else {}),
            **({"timestamp": track.timestamp.isoformat()} if track.timestamp else {}),
        },
    }
    rgba = list(track.style.colorRgba) if track.style and track.style.colorRgba else None
    if track.style and track.style.label:
        packet["label"] = {
            "text": track.style.label,
            "horizontalOrigin": "LEFT",
            "pixelOffset": {"cartesian2": [12, 0]},
        }
    if rgba:
        packet["path"]["material"] = {"solidColor": {"color": {"rgba": rgba}}}
        packet["point"]["color"] = {"rgba": rgba}
        packet["point"]["outlineColor"] = {"rgba": [255, 255, 255, 255]}
        if "label" in packet:
            packet["label"]["fillColor"] = {"rgba": rgba}
    if track.orientation:
        packet["properties"]["orientationDegrees"] = {
            "heading": track.orientation.headingDeg,
            "pitch": track.orientation.pitchDeg,
            "roll": track.orientation.rollDeg,
        }
    return packet


def _build_scene_vector_packet(vector: SceneVector) -> dict[str, Any]:
    packet: dict[str, Any] = {
        "id": vector.id,
        "name": vector.name,
        "position": {
            "cartographicDegrees": [
                vector.startPosition.longitudeDeg,
                vector.startPosition.latitudeDeg,
                vector.startPosition.altitudeM,
            ]
        },
        "polyline": {
            "positions": {
                "cartographicDegrees": [
                    vector.startPosition.longitudeDeg,
                    vector.startPosition.latitudeDeg,
                    vector.startPosition.altitudeM,
                    vector.endPosition.longitudeDeg,
                    vector.endPosition.latitudeDeg,
                    vector.endPosition.altitudeM,
                ]
            },
            "width": vector.widthPx,
            "clampToGround": vector.clampToGround,
        },
        "properties": {
            **vector.attributes,
            "objectType": "vector",
            "category": "vector",
            **({"source": vector.source} if vector.source else {}),
            **({"timestamp": vector.timestamp.isoformat()} if vector.timestamp else {}),
        },
    }
    if vector.style and vector.style.label:
        packet["label"] = {
            "text": vector.style.label,
            "horizontalOrigin": "LEFT",
            "pixelOffset": {"cartesian2": [12, 0]},
        }
    rgba = list(vector.style.colorRgba) if vector.style and vector.style.colorRgba else None
    if rgba:
        packet["polyline"]["material"] = {"solidColor": {"color": {"rgba": rgba}}}
        if "label" in packet:
            packet["label"]["fillColor"] = {"rgba": rgba}
    return packet


def _build_scene_velocity_vector_packet(vector: SceneVelocityVector) -> dict[str, Any]:
    packet = _build_scene_vector_packet(
        SceneVector(
            objectType="vector",
            id=vector.id,
            name=vector.name,
            startPosition=vector.startPosition,
            endPosition=vector.endPosition,
            widthPx=vector.widthPx,
            clampToGround=vector.clampToGround,
            style=vector.style,
            attributes=vector.attributes,
            source=vector.source,
            timestamp=vector.timestamp,
        )
    )
    packet["properties"]["objectType"] = "velocityVector"
    packet["properties"]["category"] = "velocityVector"
    return packet


def _build_scene_acceleration_vector_packet(vector: SceneAccelerationVector) -> dict[str, Any]:
    packet = _build_scene_vector_packet(
        SceneVector(
            objectType="vector",
            id=vector.id,
            name=vector.name,
            startPosition=vector.startPosition,
            endPosition=vector.endPosition,
            widthPx=vector.widthPx,
            clampToGround=vector.clampToGround,
            style=vector.style,
            attributes=vector.attributes,
            source=vector.source,
            timestamp=vector.timestamp,
        )
    )
    packet["properties"]["objectType"] = "accelerationVector"
    packet["properties"]["category"] = "accelerationVector"
    return packet


def _build_scene_line_of_sight_packet(line_of_sight: SceneLineOfSight) -> dict[str, Any]:
    packet = _build_scene_vector_packet(
        SceneVector(
            objectType="vector",
            id=line_of_sight.id,
            name=line_of_sight.name,
            startPosition=line_of_sight.startPosition,
            endPosition=line_of_sight.endPosition,
            widthPx=line_of_sight.widthPx,
            clampToGround=line_of_sight.clampToGround,
            style=line_of_sight.style,
            attributes=line_of_sight.attributes,
            source=line_of_sight.source,
            timestamp=line_of_sight.timestamp,
        )
    )
    packet["properties"]["objectType"] = "lineOfSight"
    packet["properties"]["category"] = "lineOfSight"
    return packet


def _build_scene_axes_packets(axes: SceneBodyAxes | ScenePrincipalAxes, *, family: str) -> list[dict[str, Any]]:
    axis_roles = ("x", "y", "z")
    axis_colors = {
        "x": [255, 99, 71, 220],
        "y": [46, 204, 113, 220],
        "z": [52, 152, 219, 220],
    }
    if axes.style and axes.style.colorRgba is not None:
        axis_colors = {role: list(axes.style.colorRgba) for role in axis_roles}

    origin = axes.originPosition
    orientation = axes.orientation
    packets: list[dict[str, Any]] = []
    for index, (axis_role, length_m) in enumerate(zip(axis_roles, axes.axisLengthsMeters, strict=True)):
        end_position = _offset_position(origin, axis_role=axis_role, length_m=length_m, orientation=orientation)
        packet: dict[str, Any] = {
            "id": f"{axes.id}-{axis_role}",
            "name": f"{axes.name} {axis_role.upper()}",
            "position": {
                "cartographicDegrees": [
                    origin.longitudeDeg,
                    origin.latitudeDeg,
                    origin.altitudeM,
                ]
            },
            "polyline": {
                "positions": {
                    "cartographicDegrees": [
                        origin.longitudeDeg,
                        origin.latitudeDeg,
                        origin.altitudeM,
                        end_position.longitudeDeg,
                        end_position.latitudeDeg,
                        end_position.altitudeM,
                    ]
                },
                "width": 2.5,
                "clampToGround": False,
            },
            "properties": {
                **axes.attributes,
                "objectType": family,
                "category": family,
                "axisRole": axis_role,
                "axisIndex": index,
                "axisGroupId": axes.id,
                "axisLengthMeters": length_m,
                **({"source": axes.source} if axes.source else {}),
                **({"timestamp": axes.timestamp.isoformat()} if axes.timestamp else {}),
            },
        }
        if orientation is not None:
            packet["properties"]["orientationDegrees"] = {
                "heading": orientation.headingDeg,
                "pitch": orientation.pitchDeg,
                "roll": orientation.rollDeg,
            }
        packet["polyline"]["material"] = {"solidColor": {"color": {"rgba": axis_colors[axis_role]}}}
        packet["label"] = {
            "text": f"{axes.name} {axis_role.upper()}",
            "horizontalOrigin": "LEFT",
            "pixelOffset": {"cartesian2": [12, 0]},
            "fillColor": {"rgba": axis_colors[axis_role]},
        }
        packets.append(packet)
    return packets


def _build_scene_relative_line_packet(relative_line: SceneRelativeLine) -> dict[str, Any]:
    packet = _build_scene_vector_packet(
        SceneVector(
            objectType="vector",
            id=relative_line.id,
            name=relative_line.name,
            startPosition=relative_line.startPosition,
            endPosition=relative_line.endPosition,
            widthPx=relative_line.widthPx,
            clampToGround=relative_line.clampToGround,
            style=relative_line.style,
            attributes=relative_line.attributes,
            source=relative_line.source,
            timestamp=relative_line.timestamp,
        )
    )
    packet["properties"]["objectType"] = "relativeLine"
    packet["properties"]["category"] = "relativeLine"
    return packet


def _build_scene_intercept_line_packet(intercept_line: SceneInterceptLine) -> dict[str, Any]:
    packet = _build_scene_vector_packet(
        SceneVector(
            objectType="vector",
            id=intercept_line.id,
            name=intercept_line.name,
            startPosition=intercept_line.startPosition,
            endPosition=intercept_line.endPosition,
            widthPx=intercept_line.widthPx,
            clampToGround=intercept_line.clampToGround,
            style=intercept_line.style,
            attributes=intercept_line.attributes,
            source=intercept_line.source,
            timestamp=intercept_line.timestamp,
        )
    )
    packet["properties"]["objectType"] = "interceptLine"
    packet["properties"]["category"] = "interceptLine"
    return packet


def _build_scene_camera_view_packet(camera_view: SceneCameraView) -> dict[str, Any]:
    packet: dict[str, Any] = {
        "id": camera_view.id,
        "name": camera_view.name,
        "properties": {
            **camera_view.attributes,
            "objectType": "cameraView",
            **({"source": camera_view.source} if camera_view.source else {}),
            **({"timestamp": camera_view.timestamp.isoformat()} if camera_view.timestamp else {}),
            **({"target": camera_view.target} if camera_view.target else {}),
            **({"rangeMeters": camera_view.rangeMeters} if camera_view.rangeMeters is not None else {}),
            **({"durationSeconds": camera_view.durationSeconds} if camera_view.durationSeconds is not None else {}),
            **({"rendererHints": camera_view.rendererHints} if camera_view.rendererHints else {}),
        },
    }
    if camera_view.position is not None:
        packet["position"] = {
            "cartographicDegrees": [
                camera_view.position.longitudeDeg,
                camera_view.position.latitudeDeg,
                camera_view.position.altitudeM,
            ]
        }
    if camera_view.orientation is not None:
        packet["properties"]["orientationDegrees"] = {
            "heading": camera_view.orientation.headingDeg,
            "pitch": camera_view.orientation.pitchDeg,
            "roll": camera_view.orientation.rollDeg,
        }
    return packet


def _build_scene_imported_object_packet(
    imported_object: Any,
    *,
    object_type: str,
    type_field: str | None = None,
    type_value: str | None = None,
) -> dict[str, Any]:
    packet: dict[str, Any] = {
        "id": imported_object.id,
        "name": imported_object.name,
        "properties": {
            **imported_object.attributes,
            "objectType": object_type,
            **({type_field: type_value} if type_field and type_value is not None else {}),
            **({"source": imported_object.source} if imported_object.source else {}),
            **({"timestamp": imported_object.timestamp.isoformat()} if imported_object.timestamp else {}),
            **({"show": imported_object.show} if getattr(imported_object, "show", None) is not None else {}),
            **({"layer": imported_object.layer} if getattr(imported_object, "layer", None) else {}),
            **({"extensions": imported_object.extensions} if getattr(imported_object, "extensions", None) else {}),
            **({"rendererHints": imported_object.rendererHints} if getattr(imported_object, "rendererHints", None) else {}),
            **({"payload": imported_object.payload} if getattr(imported_object, "payload", None) else {}),
        },
    }
    if getattr(imported_object, "position", None) is not None:
        packet["position"] = {
            "cartographicDegrees": [
                imported_object.position.longitudeDeg,
                imported_object.position.latitudeDeg,
                imported_object.position.altitudeM,
            ]
        }
    if getattr(imported_object, "orientation", None) is not None:
        packet["properties"]["orientationDegrees"] = {
            "heading": imported_object.orientation.headingDeg,
            "pitch": imported_object.orientation.pitchDeg,
            "roll": imported_object.orientation.rollDeg,
        }
    return packet


def _build_scene_custom_object_packet(custom_object: SceneCustomObject) -> dict[str, Any]:
    return _build_scene_imported_object_packet(
        custom_object,
        object_type="custom",
        type_field="customType",
        type_value=custom_object.customType,
    )


def _build_scene_runtime_object_packet(runtime_object: SceneRuntimeObject) -> dict[str, Any]:
    return _build_scene_imported_object_packet(
        runtime_object,
        object_type="runtime",
        type_field="runtimeType",
        type_value=runtime_object.runtimeType,
    )


def _build_scene_terrain_surface_packet(terrain_surface: SceneTerrainSurface) -> dict[str, Any]:
    return _build_scene_imported_object_packet(terrain_surface, object_type="terrainSurface")


def _build_scene_custom_mesh_packet(custom_mesh: SceneCustomMesh) -> dict[str, Any]:
    return _build_scene_imported_object_packet(custom_mesh, object_type="customMesh")


def _build_scene_clipping_plane_packet(clipping_plane: SceneClippingPlane) -> dict[str, Any]:
    packet = _build_scene_imported_object_packet(clipping_plane, object_type="clippingPlane")
    packet["properties"]["clippingPlane"] = clipping_plane.clippingPlane
    return packet


def _build_scene_clipping_polygon_packet(clipping_polygon: SceneClippingPolygon) -> dict[str, Any]:
    packet = _build_scene_imported_object_packet(clipping_polygon, object_type="clippingPolygon")
    packet["properties"]["clippingPolygon"] = clipping_polygon.clippingPolygon
    return packet


def _build_scene_classification_volume_packet(classification_volume: SceneClassificationVolume) -> dict[str, Any]:
    packet = _build_scene_imported_object_packet(classification_volume, object_type="classificationVolume")
    packet["properties"]["classificationVolume"] = classification_volume.classificationVolume
    return packet


def _build_scene_custom_shader_packet(custom_shader: SceneCustomShader) -> dict[str, Any]:
    packet = _build_scene_imported_object_packet(custom_shader, object_type="customShader")
    packet["properties"]["customShader"] = custom_shader.customShader
    return packet


def _build_scene_post_process_stage_packet(post_process_stage: ScenePostProcessStage) -> dict[str, Any]:
    packet = _build_scene_imported_object_packet(post_process_stage, object_type="postProcessStage")
    packet["properties"]["postProcessStage"] = post_process_stage.postProcessStage
    return packet


def _build_clock_packet(scene: VssScene) -> dict[str, Any] | None:
    timestamps = [obj.timestamp for obj in scene.objects if obj.timestamp is not None]
    if not timestamps:
        return None
    start = min(timestamps).isoformat()
    stop = max(timestamps).isoformat()
    return {
        "interval": f"{start}/{stop}",
        "currentTime": stop,
        "multiplier": 1,
        "range": "CLAMPED",
        "step": "SYSTEM_CLOCK_MULTIPLIER",
    }


def _flatten_positions(positions: list[Any]) -> list[float]:
    values: list[float] = []
    for position in positions:
        values.extend(
            [
                position.longitudeDeg,
                position.latitudeDeg,
                position.altitudeM,
            ]
        )
    return values


def _flatten_sampled_positions(samples: list[Any], *, epoch: datetime) -> list[float]:
    values: list[float] = []
    for sample in samples:
        offset = (sample.timestamp - epoch).total_seconds()
        values.extend(
            [
                offset,
                sample.position.longitudeDeg,
                sample.position.latitudeDeg,
                sample.position.altitudeM,
            ]
        )
    return values


def _offset_position(origin: Any, *, axis_role: str, length_m: float, orientation: Any | None) -> Any:
    east_m, north_m, up_m = 0.0, 0.0, 0.0
    if axis_role == "x":
        east_m = length_m
    elif axis_role == "y":
        north_m = length_m
    else:
        up_m = length_m

    if orientation is not None:
        quaternion = _orientation_to_unit_quaternion(orientation)
        east_m, north_m, up_m = _rotate_vector_by_quaternion((east_m, north_m, up_m), quaternion)

    lat_rad = math.radians(origin.latitudeDeg)
    meters_per_degree_lat = 111_320.0
    meters_per_degree_lon = max(1e-9, meters_per_degree_lat * math.cos(lat_rad))
    return type(origin)(
        longitudeDeg=origin.longitudeDeg + (east_m / meters_per_degree_lon),
        latitudeDeg=origin.latitudeDeg + (north_m / meters_per_degree_lat),
        altitudeM=origin.altitudeM + up_m,
    )


def _rotate_vector_by_quaternion(vector: tuple[float, float, float], quaternion: list[float]) -> tuple[float, float, float]:
    x, y, z = vector
    qx, qy, qz, qw = quaternion
    # Quaternion-vector rotation using q * v * q^-1.
    ix = qw * x + qy * z - qz * y
    iy = qw * y + qz * x - qx * z
    iz = qw * z + qx * y - qy * x
    iw = -qx * x - qy * y - qz * z
    rx = ix * qw + iw * -qx + iy * -qz - iz * -qy
    ry = iy * qw + iw * -qy + iz * -qx - ix * -qz
    rz = iz * qw + iw * -qz + ix * -qy - iy * -qx
    return rx, ry, rz


__all__ = [
    "assess_cesium_scene_support",
    "compile_cesium_document",
    "compile_cesium_scene",
    "dump_cesium_document_json",
    "dump_cesium_scene_json",
    "get_cesium_capabilities",
    "get_cesium_overlay_emitters",
    "render_cesium_viewer_html",
    "register_cesium_overlay_emitter",
    "unregister_cesium_overlay_emitter",
    "write_cesium_document",
    "write_cesium_scene",
    "write_cesium_viewer",
]
