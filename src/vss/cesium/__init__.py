from __future__ import annotations

from pathlib import Path
from typing import Any

from ..capabilities import assess_cesium_scene_support, get_cesium_capabilities
from ..models import (
    EntityUpsertMessage,
    SceneBox,
    SceneCircle,
    SceneEntity,
    SceneEllipse,
    SceneOverlay,
    ScenePath,
    SceneTrack,
    SceneWall,
    VssScene,
    scene_entity_from_message,
)
from ..util import dumps_json, write_text_file


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
    packets: list[dict[str, Any]] = [
        {
            "id": "document",
            "name": document_name or scene.document.name,
            "version": "1.0",
            **({"clock": clock} if clock else {}),
        }
    ]
    for obj in scene.objects:
        if isinstance(obj, SceneEntity):
            packets.append(_build_scene_entity_packet(obj))
        elif isinstance(obj, ScenePath):
            packets.append(_build_scene_path_packet(obj))
        elif isinstance(obj, SceneTrack):
            packets.append(_build_scene_track_packet(obj))
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
) -> str:
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
      .overlay code {{
        font-size: 12px;
      }}
    </style>
  </head>
  <body>
    <div class="overlay">
      <h1>{title}</h1>
      <p>Load this page through a local web server so Cesium can fetch <code>{czml_path}</code>.</p>
    </div>
    <div id="cesiumContainer"></div>
    <script>
      const viewer = new Cesium.Viewer("cesiumContainer", {{
        animation: false,
        timeline: false,
        shouldAnimate: false
      }});

      Cesium.CzmlDataSource.load("{czml_path}")
        .then((dataSource) => viewer.dataSources.add(dataSource))
        .then((dataSource) => viewer.zoomTo(dataSource))
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
) -> Path:
    return write_text_file(
        path,
        render_cesium_viewer_html(czml_path=czml_path, title=title),
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

    return packet


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


__all__ = [
    "assess_cesium_scene_support",
    "compile_cesium_document",
    "compile_cesium_scene",
    "dump_cesium_document_json",
    "dump_cesium_scene_json",
    "get_cesium_capabilities",
    "render_cesium_viewer_html",
    "write_cesium_document",
    "write_cesium_scene",
    "write_cesium_viewer",
]
