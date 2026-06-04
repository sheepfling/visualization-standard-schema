import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vss import (
    assess_scene_for_target,
    dump_message,
    dump_message_json,
    dump_scene_json,
    load_scene_file,
    load_simdis_bundle,
    load_soap_bundle,
    parse_scene_json,
)
from vss import (
    build_orb_package as build_orb_package_root,
)
from vss import (
    compile_cesium_document as compile_cesium_document_root,
)
from vss import (
    compile_cesium_scene as compile_cesium_scene_root,
)
from vss import (
    compile_simdis_asi as compile_simdis_asi_root,
)
from vss import (
    compile_simdis_asi_message as compile_simdis_asi_message_root,
)
from vss import (
    compile_simdis_bundle as compile_simdis_bundle_root,
)
from vss import (
    compile_simdis_lines as compile_simdis_lines_root,
)
from vss import (
    compile_soap_envelope as compile_soap_envelope_root,
)
from vss import (
    compile_soap_scene as compile_soap_scene_root,
)
from vss import (
    dump_cesium_document_json as dump_cesium_document_json_root,
)
from vss import (
    dump_cesium_scene_json as dump_cesium_scene_json_root,
)
from vss import (
    dump_soap_bundle_json as dump_soap_bundle_json_root,
)
from vss import (
    load_orb_package as load_orb_package_root,
)
from vss import (
    render_cesium_viewer_html as render_cesium_viewer_html_root,
)
from vss import (
    write_cesium_document as write_cesium_document_root,
)
from vss import (
    write_cesium_scene as write_cesium_scene_root,
)
from vss import (
    write_cesium_viewer as write_cesium_viewer_root,
)
from vss import (
    write_orb_package as write_orb_package_root,
)
from vss.cesium import (
    compile_cesium_document,
    compile_cesium_scene,
    dump_cesium_document_json,
    dump_cesium_scene_json,
    register_cesium_overlay_emitter,
    render_cesium_viewer_html,
    unregister_cesium_overlay_emitter,
    write_cesium_document,
    write_cesium_scene,
    write_cesium_viewer,
)
from vss.convert.czml import parse_czml_to_scene
from vss.convert.simdis import parse_simdis_bundle_to_scene
from vss.models import (
    EntityCategory,
    EntityUpsertMessage,
    SceneCustomObject,
    SceneDocument,
    SceneEntity,
    SceneOverlay,
    SceneRuntimeObject,
    SceneView,
    Style,
    VssScene,
    Wgs84Position,
)
from vss.orb import (
    build_orb_package,
    load_orb_package,
    write_orb_package,
)
from vss.simdis import (
    compile_simdis_asi,
    compile_simdis_asi_message,
    compile_simdis_bundle,
    compile_simdis_lines,
    compile_simdis_scene,
    load_simdis_bundle_files,
    parse_simdis_gog_text,
    parse_simdis_gog_to_scene,
    serialize_simdis_bundle_files,
    write_simdis_bundle,
)
from vss.soap import (
    compile_soap_envelope,
    compile_soap_scene,
    dump_soap_bundle_json,
    load_soap_bundle_files,
    serialize_soap_bundle_files,
    write_soap_bundle,
)

EXAMPLE_PATH = Path("examples/cesium/air-track.json")
SCENE_EXAMPLE_PATH = Path("examples/scenes/air-pair.scene.json")
MIXED_SCENE_EXAMPLE_PATH = Path("examples/scenes/mixed-ops.scene.json")
CORRIDOR_SCENE_EXAMPLE_PATH = Path("examples/scenes/corridor-demo.scene.json")
ELLIPSE_CIRCLE_SCENE_EXAMPLE_PATH = Path("examples/scenes/ellipse-circle-demo.scene.json")
UNCERTAINTY_COVARIANCE_SCENE_EXAMPLE_PATH = Path("examples/scenes/uncertainty-covariance-demo.scene.json")
PARTICLE_SYSTEM_SCENE_EXAMPLE_PATH = Path("examples/scenes/particle-system-demo.scene.json")
VOXEL_SCENE_EXAMPLE_PATH = Path("examples/scenes/voxel-demo.scene.json")
RUNTIME_SUBCLASSES_SCENE_EXAMPLE_PATH = Path("examples/scenes/runtime-subclasses-demo.scene.json")
ATTACHMENT_RUNTIME_SCENE_EXAMPLE_PATH = Path("examples/scenes/attachment-runtime-demo.scene.json")
SHADER_STAGE_SCENE_EXAMPLE_PATH = Path("examples/scenes/shader-stage-demo.scene.json")
RANGE_RING_SCENE_EXAMPLE_PATH = Path("examples/scenes/range-ring-demo.scene.json")
BEARING_FAN_SCENE_EXAMPLE_PATH = Path("examples/scenes/bearing-fan-demo.scene.json")
FAN_SCENE_EXAMPLE_PATH = Path("examples/scenes/fan-demo.scene.json")
CUSTOM_PATTERN_SENSOR_SCENE_EXAMPLE_PATH = Path("examples/scenes/custom-pattern-sensor-demo.scene.json")
WALL_SCENE_EXAMPLE_PATH = Path("examples/scenes/wall-demo.scene.json")
BOX_SCENE_EXAMPLE_PATH = Path("examples/scenes/box-demo.scene.json")
CYLINDER_SCENE_EXAMPLE_PATH = Path("examples/scenes/cylinder-demo.scene.json")
CONE_SCENE_EXAMPLE_PATH = Path("examples/scenes/cone-demo.scene.json")
FRUSTUM_SCENE_EXAMPLE_PATH = Path("examples/scenes/frustum-demo.scene.json")
RECTANGULAR_SENSOR_SCENE_EXAMPLE_PATH = Path("examples/scenes/rectangular-sensor-demo.scene.json")
SECTOR2D_SCENE_EXAMPLE_PATH = Path("examples/scenes/sector2d-demo.scene.json")
SECTOR_VOLUME_SCENE_EXAMPLE_PATH = Path("examples/scenes/sectorVolume-demo.scene.json")
HEMISPHERE_SCENE_EXAMPLE_PATH = Path("examples/scenes/hemisphere-demo.scene.json")
SPHERICAL_CAP_SCENE_EXAMPLE_PATH = Path("examples/scenes/sphericalcap-demo.scene.json")
KEYHOLE_SCENE_EXAMPLE_PATH = Path("examples/scenes/keyhole-demo.scene.json")
POLYLINE_VOLUME_SCENE_EXAMPLE_PATH = Path("examples/scenes/polyline-volume-demo.scene.json")
PLANE_SCENE_EXAMPLE_PATH = Path("examples/scenes/plane-demo.scene.json")
TILESET_SCENE_EXAMPLE_PATH = Path("examples/scenes/tileset-demo.scene.json")
VECTOR_SCENE_EXAMPLE_PATH = Path("examples/scenes/vector-demo.scene.json")
VELOCITY_VECTOR_SCENE_EXAMPLE_PATH = Path("examples/scenes/velocity-vector-demo.scene.json")
ACCELERATION_VECTOR_SCENE_EXAMPLE_PATH = Path("examples/scenes/acceleration-vector-demo.scene.json")
LINE_OF_SIGHT_SCENE_EXAMPLE_PATH = Path("examples/scenes/line-of-sight-demo.scene.json")
AXES_SCENE_EXAMPLE_PATH = Path("examples/scenes/axes-demo.scene.json")
RELATIVE_INTERCEPT_SCENE_EXAMPLE_PATH = Path("examples/scenes/relative-intercept-demo.scene.json")
VIEW_SCENE_EXAMPLE_PATH = Path("examples/scenes/view-demo.scene.json")
ELLIPSOID_SPHERE_SCENE_EXAMPLE_PATH = Path("examples/scenes/ellipsoid-sphere-demo.scene.json")
ORB_SAMPLE_DIR = Path("reference/orb_samples")
SIMDIS_GOG_SAMPLE = """# Packet-style GOG sample.

start
annotation "SDJ GOG annotation"
lla 33.9200 -117.9200 12000
fontname arial.ttf
fontsize 16
linecolor hex 0xffffffff
textoutlinecolor hex 0xff000000
textoutlinethickness thin
3d name "SDJ annotation"
end

start
line
lla 33.9200 -117.9200 10000
lla 33.9600 -117.8800 10800
linewidth 4
linecolor hex 0x7fff00ff
3d name "SDJ great-circle line"
end

start
polygon
lla 33.9000 -117.9700 1500
lla 33.9000 -117.9300 1500
lla 33.9300 -117.9200 1800
filled
fillcolor hex 0x3f00ff00
outline true
linecolor hex 0x7f00ffff
3d name "SDJ filled coverage polygon"
end
"""

ORB_SNIPPET = """56 revision
SOAP_SCENARIO_FILE
DEFINE UNITS
\tDISTANCE KILOMETERS
\tTIME HOURS
DEFINE GROUP PLATFORM_GROUP  "{New}"
\tPLATLIST "ON"
     ".Earth CI Observer"
     "Air"
     "END_OF_INPUT"
DEFINE VIEW WORLD  ".Moon CI Observer View" ".Moon CI Observer" ".Moon Pointing"
  CONES SET
\tCONE_LIST
     "END_OF_INPUT"
  ICONS ON
\tICON_LIST "ON"
     "ABQ"
     "Air(Smooth)"
     "END_OF_INPUT"
"""
ORB_TYPED_SNIPPET = """56 revision
SOAP_SCENARIO_FILE
DEFINE UNITS
\tDISTANCE KILOMETERS
\tTIME SECONDS
\tANGLE DEGREES
\tANGLE_SHIFT OFF
DEFINE CLOCK
\tEPOCH  1994 11 1 0 0 0
\tSIMULATION_TIME 9840
\tPAUSE ON
\tREAL_TIME OFF
\tTIME_STEP 60
DEFINE CONFIG
\tVERSION "Version 15.3.2"
\tCLOCK_FONT_COLOR Gray
\tTRANSCTL -637813.7
\tCLOCK_CONE_GRID
\tCLOCK_COUNT 12
\tCONE_COUNT 6
\tGRID_COLOR Magenta
\tGRID_END
\tDRIVER
\tBORDER OFF
\tDRIVER_END
\tAUTO_LOAD OFF
"""
ORB_EXPANDED_SNIPPET = """54 revision
SOAP_SCENARIO_FILE
DEFINE GROUP PLATFORM_GROUP  "{New}"
\tPLATLIST "ON"
     ".Earth CI Observer"
     "Air"
     "END_OF_INPUT"
DEFINE PLATFORM AIRROUTE  "Air"
\tSTATE  2004 2 1 0 0 0 2004 2 11 0 0 0
  PLAT  "Earth"
  WAYPOINT_TYPE BY_SPEED
  WAYPOINT 33.93 -118.4 1 0 0.205778
  WAYPOINT 38.82 -104.72 1 0 0.205778
  SHAPE AIRCRAFT
  SMOOTH OFF
DEFINE TRAJECTORY  "Air Trajectory"
\tCS  "ECR"
\tPLATFORM  "Air"
\tTRAJECTORY_CHOICE RELATIVE FORWARD 49000
\t\t2001 4 10 0 0 0
\t\t2001 4 10 1 1 1
\tREFRESH_CHOICE GENERATE
DEFINE VIEW WORLD  ".Moon CI Observer View" ".Moon CI Observer" ".Moon Pointing"
  CONES SET
\tCONE_LIST
     "END_OF_INPUT"
  ICONS ON
\tICON_LIST "ON"
     "ABQ"
     "Air(Smooth)"
     "END_OF_INPUT"
  LABELS ON
\tLABEL_LIST "ON"
     "Air(Smooth)"
     "END_OF_INPUT"
  VIEWANGLES -90 90
"""
ORB_REMAINDER_SNIPPET = """54 revision
SOAP_SCENARIO_FILE
DEFINE MAPCENTER
\tMAPFILE wmedium.wld
DEFINE SPICE
\tSPICEFILE leap.tls
\tSPICEFILE constant.tpc
DEFINE CS CSBASIS  "ECR"
  AXES OFF
  TRACK Z LONLAT 0 90
  ALIGN RESULTANT Y LONLAT 0 0
  SWEEP Z NOSWEEP
  ORIGIN  ".Host Platform" ".Host Platform"
DEFINE ANALYSIS  ".GM Earth"
  VARIABLE CONSTANT 398600.5
    DISTANCEU KILOMETERS 3
    TIMEU SECONDS -2
    ANGLEU DEGREES 0
    COMMENT  "Earth GM"
  BOUNDS 0 10
  COLOR Red
DEFINE GRID CONTOUR  ".Earth Lat/Lon Grid"
  DIMENSION 8 8 10
\tALTITUDE 0
  DOMAIN 0 86400
\tDOMDLT 300
  ANALYSIS  ".None."
  PLANE XY
"""

def test_root_exports_match_target_packages() -> None:
    assert build_orb_package_root is build_orb_package
    assert compile_cesium_document_root is compile_cesium_document
    assert compile_cesium_scene_root is compile_cesium_scene
    assert dump_cesium_document_json_root is dump_cesium_document_json
    assert dump_cesium_scene_json_root is dump_cesium_scene_json
    assert render_cesium_viewer_html_root is render_cesium_viewer_html
    assert write_cesium_document_root is write_cesium_document
    assert write_cesium_scene_root is write_cesium_scene
    assert write_cesium_viewer_root is write_cesium_viewer
    assert compile_simdis_asi_root is compile_simdis_asi
    assert compile_simdis_asi_message_root is compile_simdis_asi_message
    assert compile_simdis_lines_root is compile_simdis_lines
    assert compile_simdis_bundle_root is compile_simdis_bundle
    assert dump_soap_bundle_json_root is dump_soap_bundle_json
    assert compile_soap_scene_root is compile_soap_scene
    assert compile_soap_envelope_root is compile_soap_envelope
    assert load_orb_package_root is load_orb_package
    assert write_orb_package_root is write_orb_package

def test_example_loads(example_message: EntityUpsertMessage) -> None:
    assert isinstance(example_message, EntityUpsertMessage)
    assert example_message.payload.entityId == "aircraft-001"

def test_particle_system_scene_example_loads() -> None:
    scene = load_scene_file(PARTICLE_SYSTEM_SCENE_EXAMPLE_PATH)
    assert scene.document.id == "particle-system-demo"
    assert len(scene.objects) == 1
    assert len(scene.overlays) == 1
    particle = scene.overlays[0]
    assert particle.geometryType == "particleSystem"
    assert particle.particleSystem is not None
    assert particle.particleSystem.asset == "smokeParticle"
    assert particle.particleSystem.emissionRate == 12.0
    assert particle.particleSystem.imageSize == (20.0, 20.0)

def test_voxel_scene_example_loads() -> None:
    scene = load_scene_file(VOXEL_SCENE_EXAMPLE_PATH)
    assert scene.document.id == "voxel-demo"
    assert len(scene.objects) == 1
    assert len(scene.overlays) == 1
    voxel = scene.overlays[0]
    assert voxel.geometryType == "voxel"
    assert voxel.voxel is not None
    assert voxel.voxel.semanticKind == "voxel"
    assert voxel.voxel.grid["x"] == 12
    assert voxel.voxel.dimensionsMeters == (12.0, 8.0, 6.0)


def test_voxel_scene_round_trips_through_czml_metadata() -> None:
    scene = load_scene_file(VOXEL_SCENE_EXAMPLE_PATH)
    czml = dump_cesium_scene_json(scene)
    rebuilt = parse_czml_to_scene(czml, source="voxel-demo")
    assert rebuilt.document.id == "voxel-demo"
    assert len(rebuilt.overlays) == 1
    voxel = rebuilt.overlays[0]
    assert voxel.geometryType == "voxel"
    assert voxel.voxel is not None
    assert voxel.voxel.semanticKind == "voxel"
    assert voxel.voxel.grid["z"] == 6
    assert voxel.voxel.dimensionsMeters == (12.0, 8.0, 6.0)
    assert dump_cesium_scene_json(scene).find('"box"') != -1

def test_view_scene_compiles_to_czml_camera_view_packet() -> None:
    scene = load_scene_file(VIEW_SCENE_EXAMPLE_PATH)
    packets = compile_cesium_scene(scene)
    assert packets[0]["name"] == "View Demo"
    assert len(packets) == 3
    camera_packet = packets[1]
    assert camera_packet["id"] == "aircraft-camera-view"
    assert camera_packet["properties"]["objectType"] == "cameraView"
    assert camera_packet["properties"]["rangeMeters"] == 22000.0
    assert camera_packet["properties"]["orientationDegrees"]["pitch"] == -30.0


def test_cesium_viewer_html_uses_fly_to_for_view_targets() -> None:
    html = render_cesium_viewer_html(
        czml_path="demo.czml",
        views=[
            SceneView(
                id="view-1",
                name="View One",
                target="aircraft-001",
                rangeMeters=1200.0,
                durationSeconds=2.5,
            )
        ],
    )
    assert "viewer.flyTo(entity, options)" in html
    assert "duration: view.durationSeconds ?? 1.5" in html


def test_cesium_overlay_emitter_registry_supports_custom_geometry() -> None:
    def emit_custom(overlay: SceneOverlay) -> dict[str, object] | None:
        return {
            "id": overlay.id,
            "name": overlay.name,
            "properties": {
                "objectType": "overlay",
                "shapeType": "custom",
                "customGeometryType": overlay.customGeometryType,
            },
        }

    register_cesium_overlay_emitter("testCustomGeometry", emit_custom)
    try:
        scene = VssScene(
            schemaVersion="1.0.0-scene",
            document=SceneDocument(id="custom-registry", name="Custom Registry"),
            objects=[
                SceneOverlay(
                    objectType="overlay",
                    id="custom-001",
                    name="Custom 001",
                    position=Wgs84Position(longitudeDeg=-97.0, latitudeDeg=30.0, altitudeM=1000.0),
                    geometryType="custom",
                    customGeometryType="testCustomGeometry",
                )
            ],
        )
        packets = compile_cesium_scene(scene)
        assert packets[1]["properties"]["customGeometryType"] == "testCustomGeometry"
    finally:
        unregister_cesium_overlay_emitter("testCustomGeometry")


def test_custom_scene_object_round_trips_through_scene_json() -> None:
    scene = VssScene(
        schemaVersion="1.0.0-scene",
        document=SceneDocument(id="custom-object-demo", name="Custom Object Demo"),
        objects=[
            SceneCustomObject(
                objectType="custom",
                id="custom-001",
                name="Custom Runtime Object",
                customType="rendererSpecificThing",
                payload={"alpha": 1, "beta": {"gamma": True}},
                rendererHints={"kind": "example"},
            )
        ],
    )
    dumped = dump_scene_json(scene)
    rebuilt = parse_scene_json(dumped)
    assert rebuilt.customObjects[0].customType == "rendererSpecificThing"
    assert rebuilt.customObjects[0].payload["beta"]["gamma"] is True
    assert "\"customType\": \"rendererSpecificThing\"" in dumped

    czml = dump_cesium_scene_json(scene)
    rebuilt_czml = parse_czml_to_scene(czml, source="custom-object-demo")
    assert rebuilt_czml.customObjects[0].customType == "rendererSpecificThing"
    assert rebuilt_czml.customObjects[0].payload["alpha"] == 1


def test_custom_scene_object_assessment_reports_partial_support() -> None:
    scene = VssScene(
        schemaVersion="1.0.0-scene",
        document=SceneDocument(id="custom-object-demo", name="Custom Object Demo"),
        objects=[
            SceneCustomObject(
                objectType="custom",
                id="custom-001",
                name="Custom Runtime Object",
                customType="rendererSpecificThing",
                payload={"alpha": 1},
            )
        ],
    )
    cesium = assess_scene_for_target(scene, "cesium")
    simdis = assess_scene_for_target(scene, "simdis")
    soap = assess_scene_for_target(scene, "soap")
    assert any(feature.featureId == "customObjects" and feature.support == "partial" for feature in cesium.features)
    assert any(feature.featureId == "customObjects" and feature.support == "partial" for feature in simdis.features)
    assert any(feature.featureId == "customObjects" and feature.support == "partial" for feature in soap.features)


def test_custom_scene_object_round_trips_through_simdis_and_soap_bundles(tmp_path: Path) -> None:
    scene = VssScene(
        schemaVersion="1.0.0-scene",
        document=SceneDocument(id="custom-object-demo", name="Custom Object Demo"),
        objects=[
            SceneCustomObject(
                objectType="custom",
                id="custom-001",
                name="Custom Runtime Object",
                customType="rendererSpecificThing",
                payload={"alpha": 1, "beta": {"gamma": True}},
                rendererHints={"kind": "example"},
            )
        ],
    )

    simdis_bundle = compile_simdis_scene(scene)
    simdis_written = write_simdis_bundle(simdis_bundle, tmp_path / "simdis")
    simdis_rebuilt = load_simdis_bundle(tmp_path / "simdis")
    assert simdis_written["simdis/custom-objects.json"].exists()
    assert simdis_rebuilt.customObjects[0]["customType"] == "rendererSpecificThing"
    assert simdis_rebuilt.customObjects[0]["payload"]["beta"]["gamma"] is True

    soap_bundle = compile_soap_scene(scene)
    soap_written = write_soap_bundle(soap_bundle, tmp_path / "soap")
    soap_rebuilt = load_soap_bundle(tmp_path / "soap")
    assert soap_written["soap/custom-objects.json"].exists()
    assert soap_rebuilt.customObjects[0]["customType"] == "rendererSpecificThing"
    assert soap_rebuilt.customObjects[0]["rendererHints"]["kind"] == "example"


def test_runtime_scene_object_round_trips_through_scene_json_and_bundles(tmp_path: Path) -> None:
    scene = VssScene(
        schemaVersion="1.0.0-scene",
        document=SceneDocument(id="runtime-object-demo", name="Runtime Object Demo"),
        objects=[
            SceneRuntimeObject(
                objectType="runtime",
                id="runtime-001",
                name="Runtime Object",
                runtimeType="rendererSpecificRuntimeThing",
                payload={"alpha": 1},
                rendererHints={"kind": "runtime-example"},
            )
        ],
    )
    dumped = dump_scene_json(scene)
    rebuilt = parse_scene_json(dumped)
    assert rebuilt.runtimeObjects[0].runtimeType == "rendererSpecificRuntimeThing"
    assert rebuilt.runtimeObjects[0].payload["alpha"] == 1

    simdis_bundle = compile_simdis_scene(scene)
    simdis_written = write_simdis_bundle(simdis_bundle, tmp_path / "simdis-runtime")
    simdis_rebuilt = load_simdis_bundle(tmp_path / "simdis-runtime")
    assert simdis_written["simdis/runtime-objects.json"].exists()
    assert simdis_rebuilt.runtimeObjects[0]["runtimeType"] == "rendererSpecificRuntimeThing"

    soap_bundle = compile_soap_scene(scene)
    soap_written = write_soap_bundle(soap_bundle, tmp_path / "soap-runtime")
    soap_rebuilt = load_soap_bundle(tmp_path / "soap-runtime")
    assert soap_written["soap/runtime-objects.json"].exists()
    assert soap_rebuilt.runtimeObjects[0]["rendererHints"]["kind"] == "runtime-example"


def test_runtime_subclass_scene_objects_round_trip_through_scene_json_and_bundles(tmp_path: Path) -> None:
    scene = load_scene_file(RUNTIME_SUBCLASSES_SCENE_EXAMPLE_PATH)
    dumped = dump_scene_json(scene)
    rebuilt = parse_scene_json(dumped)

    assert rebuilt.terrainSurfaces[0].rendererHints["semanticKind"] == "terrainSurface"
    assert rebuilt.customMeshes[0].rendererHints["semanticKind"] == "customMesh"
    assert rebuilt.terrainSurfaces[0].show is False
    assert rebuilt.customMeshes[0].payload["note"] == "placeholder"

    cesium = assess_scene_for_target(scene, "cesium")
    simdis = assess_scene_for_target(scene, "simdis")
    soap = assess_scene_for_target(scene, "soap")
    assert cesium.objectCount == 2
    assert any(feature.featureId == "object.terrainSurface.runtime" and feature.support == "partial" for feature in cesium.features)
    assert any(feature.featureId == "object.customMesh.runtime" and feature.support == "partial" for feature in cesium.features)
    assert any(feature.featureId == "object.terrainSurface.runtime" and feature.support == "partial" for feature in simdis.features)
    assert any(feature.featureId == "object.customMesh.runtime" and feature.support == "partial" for feature in soap.features)

    czml = compile_cesium_scene(scene)
    terrain_packet = next(packet for packet in czml if packet.get("id") == "terrain-surface-001")
    custom_mesh_packet = next(packet for packet in czml if packet.get("id") == "custom-mesh-001")
    assert terrain_packet["properties"]["objectType"] == "terrainSurface"
    assert custom_mesh_packet["properties"]["objectType"] == "customMesh"

    simdis_bundle = compile_simdis_scene(scene)
    simdis_written = write_simdis_bundle(simdis_bundle, tmp_path / "simdis-runtime-subclasses")
    simdis_rebuilt = load_simdis_bundle(tmp_path / "simdis-runtime-subclasses")
    assert simdis_written["simdis/runtime-objects.json"].exists()
    assert any(item["objectType"] == "terrainSurface" for item in simdis_rebuilt.runtimeObjects)
    assert any(item["objectType"] == "customMesh" for item in simdis_rebuilt.runtimeObjects)

    soap_bundle = compile_soap_scene(scene)
    soap_written = write_soap_bundle(soap_bundle, tmp_path / "soap-runtime-subclasses")
    soap_rebuilt = load_soap_bundle(tmp_path / "soap-runtime-subclasses")
    assert soap_written["soap/runtime-objects.json"].exists()
    assert any(item["objectType"] == "terrainSurface" for item in soap_rebuilt.runtimeObjects)
    assert any(item["objectType"] == "customMesh" for item in soap_rebuilt.runtimeObjects)


def test_attachment_runtime_scene_objects_round_trip_through_scene_json_and_bundles(tmp_path: Path) -> None:
    scene = load_scene_file(ATTACHMENT_RUNTIME_SCENE_EXAMPLE_PATH)
    dumped = dump_scene_json(scene)
    rebuilt = parse_scene_json(dumped)

    assert rebuilt.clippingPlanes[0].clippingPlane["distanceMeters"] == 250.0
    assert rebuilt.clippingPolygons[0].clippingPolygon["clampToGround"] is True
    assert rebuilt.classificationVolumes[0].classificationVolume["shape"] == "box"

    cesium = assess_scene_for_target(scene, "cesium")
    simdis = assess_scene_for_target(scene, "simdis")
    soap = assess_scene_for_target(scene, "soap")
    assert cesium.objectCount == 3
    assert any(feature.featureId == "object.clippingPlane.runtime" and feature.support == "partial" for feature in cesium.features)
    assert any(feature.featureId == "object.clippingPolygon.runtime" and feature.support == "partial" for feature in cesium.features)
    assert any(feature.featureId == "object.classificationVolume.runtime" and feature.support == "partial" for feature in cesium.features)
    assert any(feature.featureId == "object.clippingPlane.runtime" and feature.support == "partial" for feature in simdis.features)
    assert any(feature.featureId == "object.clippingPolygon.runtime" and feature.support == "partial" for feature in soap.features)

    czml = compile_cesium_scene(scene)
    clipping_plane_packet = next(packet for packet in czml if packet.get("id") == "clipping-plane-001")
    clipping_polygon_packet = next(packet for packet in czml if packet.get("id") == "clipping-polygon-001")
    classification_volume_packet = next(packet for packet in czml if packet.get("id") == "classification-volume-001")
    assert clipping_plane_packet["properties"]["clippingPlane"]["distanceMeters"] == 250.0
    assert clipping_polygon_packet["properties"]["clippingPolygon"]["clampToGround"] is True
    assert classification_volume_packet["properties"]["classificationVolume"]["shape"] == "box"

    simdis_bundle = compile_simdis_scene(scene)
    simdis_written = write_simdis_bundle(simdis_bundle, tmp_path / "simdis-attachments")
    simdis_rebuilt = load_simdis_bundle(tmp_path / "simdis-attachments")
    assert simdis_written["simdis/runtime-objects.json"].exists()
    assert any(item["objectType"] == "clippingPlane" for item in simdis_rebuilt.runtimeObjects)
    assert any(item["objectType"] == "classificationVolume" for item in simdis_rebuilt.runtimeObjects)

    soap_bundle = compile_soap_scene(scene)
    soap_written = write_soap_bundle(soap_bundle, tmp_path / "soap-attachments")
    soap_rebuilt = load_soap_bundle(tmp_path / "soap-attachments")
    assert soap_written["soap/runtime-objects.json"].exists()
    assert any(item["objectType"] == "clippingPolygon" for item in soap_rebuilt.runtimeObjects)
    assert any(item["objectType"] == "clippingPlane" for item in soap_rebuilt.runtimeObjects)


def test_shader_stage_scene_objects_round_trip_through_scene_json_and_bundles(tmp_path: Path) -> None:
    scene = load_scene_file(SHADER_STAGE_SCENE_EXAMPLE_PATH)
    dumped = dump_scene_json(scene)
    rebuilt = parse_scene_json(dumped)

    assert rebuilt.customShaders[0].customShader["language"] == "glsl"
    assert rebuilt.postProcessStages[0].postProcessStage["stageType"] == "bloom"

    cesium = assess_scene_for_target(scene, "cesium")
    simdis = assess_scene_for_target(scene, "simdis")
    soap = assess_scene_for_target(scene, "soap")
    assert cesium.objectCount == 2
    assert any(feature.featureId == "object.customShader.runtime" and feature.support == "partial" for feature in cesium.features)
    assert any(feature.featureId == "object.postProcessStage.runtime" and feature.support == "partial" for feature in cesium.features)
    assert any(feature.featureId == "object.customShader.runtime" and feature.support == "partial" for feature in simdis.features)
    assert any(feature.featureId == "object.postProcessStage.runtime" and feature.support == "partial" for feature in soap.features)

    czml = compile_cesium_scene(scene)
    custom_shader_packet = next(packet for packet in czml if packet.get("id") == "custom-shader-001")
    post_process_stage_packet = next(packet for packet in czml if packet.get("id") == "post-process-stage-001")
    assert custom_shader_packet["properties"]["customShader"]["language"] == "glsl"
    assert post_process_stage_packet["properties"]["postProcessStage"]["stageType"] == "bloom"

    simdis_bundle = compile_simdis_scene(scene)
    simdis_written = write_simdis_bundle(simdis_bundle, tmp_path / "simdis-shader-stage")
    simdis_rebuilt = load_simdis_bundle(tmp_path / "simdis-shader-stage")
    assert simdis_written["simdis/runtime-objects.json"].exists()
    assert any(item["objectType"] == "customShader" for item in simdis_rebuilt.runtimeObjects)
    assert any(item["objectType"] == "postProcessStage" for item in simdis_rebuilt.runtimeObjects)

    soap_bundle = compile_soap_scene(scene)
    soap_written = write_soap_bundle(soap_bundle, tmp_path / "soap-shader-stage")
    soap_rebuilt = load_soap_bundle(tmp_path / "soap-shader-stage")
    assert soap_written["soap/runtime-objects.json"].exists()
    assert any(item["objectType"] == "customShader" for item in soap_rebuilt.runtimeObjects)
    assert any(item["objectType"] == "postProcessStage" for item in soap_rebuilt.runtimeObjects)

def test_scene_can_be_built_from_messages(example_message: EntityUpsertMessage) -> None:
    payload = dump_message(example_message)["payload"]
    second = EntityUpsertMessage.model_validate(
        {
            **dump_message(example_message),
            "messageId": "msg-0002",
            "timestamp": "2026-06-01T12:05:00Z",
            "payload": {
                **payload,
                "entityId": "aircraft-002",
                "name": "Blue Two",
            },
        }
    )
    scene = VssScene.from_messages([example_message, second], scene_id="demo-scene", scene_name="Demo Scene")
    assert scene.document.id == "demo-scene"
    assert len(scene.entities) == 2
    assert scene.entities[1].id == "aircraft-002"

def test_scene_example_assessment_reports_views_support() -> None:
    scene = load_scene_file(SCENE_EXAMPLE_PATH)
    cesium = assess_scene_for_target(scene, "cesium")
    soap = assess_scene_for_target(scene, "soap")
    assert cesium.objectCount == 2
    assert any(feature.featureId == "views" and feature.support == "partial" for feature in cesium.features)
    assert any(feature.featureId == "views" and feature.support == "partial" for feature in soap.features)

def test_particle_system_scene_assessment_reports_support() -> None:
    scene = load_scene_file(PARTICLE_SYSTEM_SCENE_EXAMPLE_PATH)
    cesium = assess_scene_for_target(scene, "cesium")
    simdis = assess_scene_for_target(scene, "simdis")
    soap = assess_scene_for_target(scene, "soap")
    assert cesium.objectCount == 1
    assert any(feature.featureId == "object.particleSystem.geometry" and feature.support == "strong" for feature in cesium.features)
    assert any(feature.featureId == "object.particleSystem.geometry" and feature.support == "unsupported" for feature in simdis.features)
    assert any(feature.featureId == "object.particleSystem.geometry" and feature.support == "unsupported" for feature in soap.features)

def test_voxel_scene_assessment_reports_support() -> None:
    scene = load_scene_file(VOXEL_SCENE_EXAMPLE_PATH)
    cesium = assess_scene_for_target(scene, "cesium")
    simdis = assess_scene_for_target(scene, "simdis")
    soap = assess_scene_for_target(scene, "soap")
    assert cesium.objectCount == 1
    assert any(feature.featureId == "object.voxel.geometry" and feature.support == "partial" for feature in cesium.features)
    assert any(feature.featureId == "object.voxel.geometry" and feature.support == "unsupported" for feature in simdis.features)
    assert any(feature.featureId == "object.voxel.geometry" and feature.support == "unsupported" for feature in soap.features)

def test_simdis_output_contains_platform_update(example_message: EntityUpsertMessage) -> None:
    lines = compile_simdis_lines(example_message)
    assert any(line.startswith("PLATFORM_UPDATE aircraft-001") for line in lines)

def test_simdis_asi_export_includes_beam_gate_and_projector() -> None:
    scene = VssScene(
        schemaVersion="1.0.0-scene",
        document=SceneDocument(
            id="asi-demo",
            name="ASI Demo",
            created=datetime.fromisoformat("2026-01-01T00:00:00+00:00"),
        ),
        objects=[
            SceneEntity(
                objectType="entity",
                id="sensor-alpha",
                name="Sensor Alpha",
                category=EntityCategory.SENSOR,
                position=Wgs84Position(longitudeDeg=-117.97, latitudeDeg=33.9, altitudeM=1250.0),
                style=Style(label="Sensor Alpha"),
                attributes={
                    "simdis": {
                        "platformIcon": "radar",
                        "beam": {
                            "beamId": "301",
                            "hostPlatformId": "sensor-alpha",
                            "type": "BODY",
                            "horzBwDeg": 20,
                            "vertBwDeg": 10,
                            "samples": [
                                {
                                    "time": "2026-01-01T00:00:00Z",
                                    "on": True,
                                    "color": "green",
                                    "az": 35,
                                    "el": 8,
                                    "rangeMeters": 65000,
                                    "targetPlatformId": "target-202",
                                }
                            ],
                        },
                        "gate": {
                            "gateId": "401",
                            "hostBeamId": "301",
                            "type": "BODY",
                            "samples": [
                                {
                                    "time": "2026-01-01T00:00:00Z",
                                    "on": True,
                                    "color": "yellow",
                                    "az": 35,
                                    "el": 8,
                                    "width": 5,
                                    "height": 3,
                                    "minRangeMeters": 15000,
                                    "maxRangeMeters": 35000,
                                    "centroidMeters": 25000,
                                }
                            ],
                        },
                        "projector": {
                            "projectorId": "601",
                            "rasterFile": "media/sample-projector-image.png",
                            "interpolateFov": True,
                            "samples": [
                                {
                                    "time": "2026-01-01T00:00:00Z",
                                    "on": True,
                                    "fovDegrees": 20,
                                }
                            ],
                        },
                    }
                },
                source="sim.example.ops-sim",
                timestamp=datetime.fromisoformat("2026-01-01T00:00:00+00:00"),
            )
        ],
    )
    text = compile_simdis_asi(scene)
    assert "ReferenceYear 2026" in text
    assert 'PlatformIcon sensor-alpha "radar"' in text
    assert "BeamID sensor-alpha 301" in text
    assert 'BeamType 301 "BODY"' in text
    assert "BeamOnOffCmd 301 2026-01-01T00:00:00Z 1" in text
    assert "GateID 301 401" in text
    assert "GateDataRAE 401 2026-01-01T00:00:00Z 35 8 5 3 15000 35000 25000" in text
    assert "Projector sensor-alpha 601" in text
    assert 'ProjectorRasterFile 601 "media/sample-projector-image.png"' in text

def test_simdis_gog_parser_recovers_supported_shapes() -> None:
    document = parse_simdis_gog_text(SIMDIS_GOG_SAMPLE)
    assert [shape.kind for shape in document.shapes] == ["annotation", "line", "polygon"]
    assert document.shapes[0].name == "SDJ annotation"

    scene = parse_simdis_gog_to_scene(SIMDIS_GOG_SAMPLE)
    assert len(scene.entities) == 1
    assert len(scene.overlays) == 2
    assert scene.entities[0].name == "SDJ annotation"
    assert scene.overlays[0].geometryType == "polyline"
    assert scene.overlays[1].geometryType == "polygon"

def test_simdis_bundle_round_trip_from_file_map(example_message: EntityUpsertMessage) -> None:
    bundle = compile_simdis_bundle(example_message)
    files = serialize_simdis_bundle_files(bundle)
    assert "simdis/entities.normalized.json" in files
    assert "simdis/overlays.normalized.json" in files
    rebuilt = load_simdis_bundle_files(files)
    assert rebuilt.entities.platforms[0].id == "aircraft-001"
    assert rebuilt.scenarioAsi.startswith("ReferenceYear 2026")
    assert "PLATFORM aircraft-001" in rebuilt.overlaysGog

def test_simdis_bundle_round_trip_from_directory(example_message: EntityUpsertMessage, tmp_path: Path) -> None:
    bundle = compile_simdis_bundle(example_message)
    written = write_simdis_bundle(bundle, tmp_path)
    assert "simdis/entities.normalized.json" in written
    assert "simdis/overlays.normalized.json" in written
    rebuilt = load_simdis_bundle(tmp_path)
    assert rebuilt.manifest.target == "simdis"
    initial_position = rebuilt.entities.platforms[0].initialPosition
    assert initial_position is not None
    assert initial_position.lon == -97.7431

def test_simdis_scene_bundle_round_trip_from_directory(tmp_path: Path) -> None:
    scene = load_scene_file(MIXED_SCENE_EXAMPLE_PATH)
    bundle = compile_simdis_scene(scene)
    written = write_simdis_bundle(bundle, tmp_path)
    assert "simdis/entities.normalized.json" in written
    assert "simdis/overlays.normalized.json" in written
    rebuilt = load_simdis_bundle(tmp_path)
    assert rebuilt.manifest.source == "mixed-ops-demo"
    assert len(rebuilt.entities.platforms) == 1
    assert len(rebuilt.entities.sensors) == 1
    assert len(rebuilt.entities.annotations) == 1
    assert len(rebuilt.entities.vectors) == 2
    assert len(rebuilt.entities.overlays) == 2
    assert "PlatformID aircraft-003" in rebuilt.scenarioAsi
    assert "PLATFORM aircraft-003" in rebuilt.overlaysGog
    assert "start_annotation ground-site-01" in rebuilt.overlaysGog
    assert 'label "Ground Site 01"' in rebuilt.overlaysGog
    assert "start_gog flight-corridor-a" in rebuilt.overlaysGog
    assert "linecolor 186 104 200" in rebuilt.overlaysGog
    assert "start_gog coverage-zone-b" in rebuilt.overlaysGog
    assert "polygon" in rebuilt.overlaysGog
    assert rebuilt.entities.annotations[0].id == "ground-site-01"
    assert rebuilt.entities.sensors[0].id == "sensor-alpha"
    assert rebuilt.entities.vectors[0].id == "flight-corridor-a"
    assert rebuilt.entities.vectors[1].id == "coverage-zone-b"
    assert rebuilt.entities.overlays[0].geometry.type == "polyline"
    assert rebuilt.entities.overlays[1].geometry.type == "polygon"
    assert rebuilt.diagnostics == []

def test_simdis_bundle_scene_import_recovers_gog_overlays(tmp_path: Path) -> None:
    scene = load_scene_file(MIXED_SCENE_EXAMPLE_PATH)
    bundle = compile_simdis_scene(scene)
    write_simdis_bundle(bundle, tmp_path)
    rebuilt = parse_simdis_bundle_to_scene(tmp_path)
    assert len(rebuilt.entities) == 3
    assert len(rebuilt.overlays) == 2
    assert {overlay.id for overlay in rebuilt.overlays} == {"flight-corridor-a", "coverage-zone-b"}

def test_soap_output_contains_payload(example_message: EntityUpsertMessage) -> None:
    xml = compile_soap_envelope(example_message)
    assert "EntityUpsertMessage" in xml
    assert "aircraft-001" in xml

def test_soap_scene_bundle_round_trip_from_file_map() -> None:
    scene = load_scene_file(SCENE_EXAMPLE_PATH)
    bundle = compile_soap_scene(scene)
    files = serialize_soap_bundle_files(bundle)
    rebuilt = load_soap_bundle_files(files)
    assert rebuilt.scenario.id == "air-pair-demo"
    assert len(rebuilt.scenario.platforms) == 2
    assert rebuilt.scenario.trajectories[0].platformId == "aircraft-001"
    assert len(rebuilt.scenario.models) == 2
    assert rebuilt.scenario.models[0].uri == "https://example.org/assets/aircraft.glb"
    assert len(rebuilt.views.views) == 1
    assert rebuilt.views.views[0].target == "aircraft-001"
    assert len(rebuilt.views.palettes) == 1
    assert rebuilt.views.palettes[0].entries[0]["value"] == 2
    assert '"target": "soap"' in dump_soap_bundle_json(bundle)

def test_soap_scene_bundle_round_trip_from_directory(tmp_path: Path) -> None:
    scene = load_scene_file(MIXED_SCENE_EXAMPLE_PATH)
    bundle = compile_soap_scene(scene)
    write_soap_bundle(bundle, tmp_path)
    rebuilt = load_soap_bundle(tmp_path)
    assert rebuilt.manifest.source == "mixed-ops-demo"
    assert len(rebuilt.scenario.platforms) == 3
    assert rebuilt.scenario.clock["currentTime"] == "2026-06-01T12:07:00+00:00"
    assert len(rebuilt.scenario.models) == 1
    assert rebuilt.scenario.models[0].id == "aircraft-003"
    assert rebuilt.scenario.models[0].uri == "https://example.org/assets/aircraft.glb"
    assert len(rebuilt.scenario.sensorSwaths) == 1
    assert rebuilt.scenario.sensorSwaths[0].id == "sensor-alpha"
    assert rebuilt.scenario.sensorSwaths[0].style.label == "Sensor Alpha"
    assert len(rebuilt.scenario.overlays) == 2
    assert rebuilt.scenario.overlays[0].id == "flight-corridor-a"
    assert rebuilt.scenario.overlays[0].kind == "polyline"
    assert rebuilt.scenario.overlays[1].id == "coverage-zone-b"
    assert rebuilt.scenario.overlays[1].kind == "polygon"
    assert len(rebuilt.views.views) == 1
    assert rebuilt.views.views[0].target == "aircraft-003"
    assert len(rebuilt.views.palettes) == 1
    assert rebuilt.views.palettes[0].entries[0]["value"] == 3
    assert rebuilt.views.palettes[0].entries[1]["value"] == 2
    assert rebuilt.diagnostics == []

def test_round_trip_dump_uses_json_safe_shapes(example_message: EntityUpsertMessage) -> None:
    dumped = dump_message_json(example_message)
    rebuilt = EntityUpsertMessage.model_validate_json(dumped)
    assert rebuilt.messageId == example_message.messageId

def test_dump_message_returns_plain_json_data(example_message: EntityUpsertMessage) -> None:
    dumped = dump_message(example_message)
    assert dumped["payload"]["entityId"] == "aircraft-001"
    assert dumped["payload"]["style"]["colorRgba"] == [64, 145, 255, 255]
