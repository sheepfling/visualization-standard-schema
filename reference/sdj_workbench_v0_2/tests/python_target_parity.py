from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from vss.cesium import dump_cesium_scene_json  # noqa: E402
from vss.io import dump_scene_json  # noqa: E402
from vss.models import (  # noqa: E402
    EntityCategory,
    Orientation,
    SceneDocument,
    SceneEntity,
    SceneOverlay,
    SceneRuntimeObject,
    ScenePolygon,
    ScenePolyline,
    Style,
    VssScene,
    Wgs84Position,
)
from vss.simdis import compile_simdis_scene, dump_simdis_bundle_json  # noqa: E402
from vss.soap import compile_soap_scene, dump_soap_bundle_json  # noqa: E402


def _load_scene(path: Path) -> VssScene:
    return VssScene.model_validate_json(path.read_text(encoding="utf-8"))


def _bridge_to_scene(payload: dict[str, object]) -> VssScene:
    document = payload["document"]
    assert isinstance(document, dict)
    objects = payload.get("objects", [])
    assert isinstance(objects, list)

    scene_objects: list[SceneEntity | SceneOverlay] = []
    for item in objects:
        assert isinstance(item, dict)
        kind = str(item.get("kind") or "")
        if kind == "track":
            scene_objects.append(_track_to_entity(item))
        elif kind == "polyline":
            scene_objects.append(_polyline_to_overlay(item))
        elif kind == "polygon":
            scene_objects.append(_polygon_to_overlay(item))
        elif kind in {
            "terrainSurface",
            "customMesh",
            "clippingPlane",
            "clippingPolygon",
            "classificationVolume",
            "customShader",
            "postProcessStage",
            "customPrimitive",
            "primitiveMesh",
            "composite",
            "atmosphere",
            "czmlDataSource",
            "dataSource",
            "geoJsonDataSource",
            "kmlDataSource",
            "skyBox",
            "videoPlane",
            "voxel",
        }:
            scene_objects.append(_runtime_to_object(item, kind))

    return VssScene(
        schemaVersion="1.0.0-scene",
        document=SceneDocument(
            id=str(document["id"]),
            name=str(document["name"]),
            description=document.get("description") if isinstance(document, dict) else None,
            created=document.get("created") if isinstance(document, dict) else None,
            generator=document.get("generator") if isinstance(document, dict) else None,
            source=document.get("source") if isinstance(document, dict) else None,
        ),
        objects=scene_objects,
    )


def _track_to_entity(item: dict[str, object]) -> SceneEntity:
    pose = item.get("pose")
    assert isinstance(pose, dict)
    position = pose.get("position")
    assert isinstance(position, dict)
    cartographic = position.get("cartographicDegrees")
    assert isinstance(cartographic, list) and len(cartographic) >= 3
    timestamp = None
    samples = position.get("samples")
    if isinstance(samples, dict):
        values = samples.get("values")
        epoch = samples.get("epoch")
        if isinstance(values, list) and values:
            first = values[0]
            if isinstance(first, list) and first:
                sample_time = first[0]
                if isinstance(sample_time, str) and sample_time:
                    timestamp = sample_time
                elif isinstance(epoch, str) and epoch:
                    timestamp = epoch
    orientation = pose.get("orientation")
    if isinstance(orientation, dict):
        orientation_model = Orientation.model_validate(
            {
                key: value
                for key, value in {
                    "headingDeg": orientation.get("headingDeg"),
                    "pitchDeg": orientation.get("pitchDeg"),
                    "rollDeg": orientation.get("rollDeg"),
                }.items()
                if value is not None
            }
        )
    else:
        orientation_model = None
    properties = item.get("properties")
    if not isinstance(properties, dict):
        properties = {}
    path = item.get("path")
    style = item.get("style")
    label = None
    color = None
    if isinstance(style, dict):
        label = style.get("label")
        if isinstance(style.get("material"), dict):
            rgba = style["material"].get("rgba")
            if isinstance(rgba, list) and len(rgba) == 4:
                color = tuple(int(component) for component in rgba)

    style_model = None
    if label or color:
        style_model = Style(
            label=str(label) if label is not None else None,
            colorRgba=color,
        )

    return SceneEntity(
        objectType="entity",
        id=str(item["id"]),
        name=str(item.get("name") or item["id"]),
        category=EntityCategory.AIR if str(properties.get("platformType") or "air") == "air" else EntityCategory.OTHER,
        position=Wgs84Position(
            longitudeDeg=float(cartographic[0]),
            latitudeDeg=float(cartographic[1]),
            altitudeM=float(cartographic[2]),
        ),
        orientation=orientation_model,
        style=style_model,
        attributes={
            **properties,
            **({"path": path} if path is not None else {}),
            "bridgeKind": str(item.get("kind") or ""),
        },
        source="parity.bridge.fixture",
        timestamp=timestamp,
    )


def _polyline_to_overlay(item: dict[str, object]) -> SceneOverlay:
    pose = item.get("pose")
    assert isinstance(pose, dict)
    position = pose.get("position")
    assert isinstance(position, dict)
    cartographic = position.get("cartographicDegrees")
    assert isinstance(cartographic, list) and len(cartographic) >= 3
    geometry = item.get("geometry")
    assert isinstance(geometry, dict)
    positions = geometry.get("positions")
    assert isinstance(positions, list)
    return SceneOverlay(
        objectType="overlay",
        id=str(item["id"]),
        name=str(item.get("name") or item["id"]),
        position=Wgs84Position(
            longitudeDeg=float(cartographic[0]),
            latitudeDeg=float(cartographic[1]),
            altitudeM=float(cartographic[2]),
        ),
        geometryType="polyline",
        polyline=ScenePolyline(
            positions=[
                Wgs84Position(
                    longitudeDeg=float(point["cartographicDegrees"][0]),
                    latitudeDeg=float(point["cartographicDegrees"][1]),
                    altitudeM=float(point["cartographicDegrees"][2]),
                )
                for point in positions
            ],
            widthPx=3.0,
        ),
    )


def _runtime_to_object(item: dict[str, object], kind: str) -> SceneRuntimeObject:
    position = None
    raw_position = item.get("position")
    if isinstance(raw_position, dict):
        cartographic = raw_position.get("cartographicDegrees")
        if isinstance(cartographic, list) and len(cartographic) >= 3:
            position = Wgs84Position(
                longitudeDeg=float(cartographic[0]),
                latitudeDeg=float(cartographic[1]),
                altitudeM=float(cartographic[2]),
            )
    return SceneRuntimeObject(
        objectType="runtime",
        id=str(item["id"]),
        name=str(item.get("name") or item["id"]),
        runtimeType=kind,
        show=item.get("show") if isinstance(item.get("show"), bool) else None,
        layer=str(item["layer"]) if isinstance(item.get("layer"), str) else None,
        extensions=item["extensions"] if isinstance(item.get("extensions"), dict) else {},
        rendererHints=item["rendererHints"] if isinstance(item.get("rendererHints"), dict) else {},
        payload=item["payload"] if isinstance(item.get("payload"), dict) else {},
        position=position,
        source=str(item["source"]) if isinstance(item.get("source"), str) else None,
    )


def _polygon_to_overlay(item: dict[str, object]) -> SceneOverlay:
    pose = item.get("pose")
    assert isinstance(pose, dict)
    position = pose.get("position")
    assert isinstance(position, dict)
    cartographic = position.get("cartographicDegrees")
    assert isinstance(cartographic, list) and len(cartographic) >= 3
    geometry = item.get("geometry")
    assert isinstance(geometry, dict)
    rings = geometry.get("rings")
    assert isinstance(rings, list) and rings
    ring = rings[0]
    assert isinstance(ring, list)
    return SceneOverlay(
        objectType="overlay",
        id=str(item["id"]),
        name=str(item.get("name") or item["id"]),
        position=Wgs84Position(
            longitudeDeg=float(cartographic[0]),
            latitudeDeg=float(cartographic[1]),
            altitudeM=float(cartographic[2]),
        ),
        geometryType="polygon",
        polygon=ScenePolygon(
            positions=[
                Wgs84Position(
                    longitudeDeg=float(point["cartographicDegrees"][0]),
                    latitudeDeg=float(point["cartographicDegrees"][1]),
                    altitudeM=float(point["cartographicDegrees"][2]),
                )
                for point in ring
            ]
        ),
    )


def main() -> None:
    fixture_path = Path(sys.argv[1])
    mode = sys.argv[2] if len(sys.argv) > 2 else "bridge"
    if mode == "scene":
        scene = _load_scene(fixture_path)
    else:
        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
        scene = _bridge_to_scene(payload)

    cesium_packets = json.loads(dump_cesium_scene_json(scene))
    simdis_bundle = compile_simdis_scene(scene)
    soap_bundle = compile_soap_scene(scene)

    result = {
        "cesium": {
            "packets": [packet for packet in cesium_packets if isinstance(packet, dict)],
            "packetIds": [packet.get("id") for packet in cesium_packets if isinstance(packet, dict)],
            "packetCount": len([packet for packet in cesium_packets if isinstance(packet, dict)]),
        },
        "simdis": json.loads(dump_simdis_bundle_json(simdis_bundle)),
        "soap": json.loads(dump_soap_bundle_json(soap_bundle)),
        "scene": json.loads(dump_scene_json(scene)),
    }
    json.dump(result, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
