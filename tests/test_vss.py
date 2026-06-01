import sys
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vss import (
    assess_cesium_scene_support as assess_cesium_scene_support_root,
)
from vss import (
    assess_scene_for_target,
    dump_message,
    dump_message_json,
    dump_scene,
    dump_scene_json,
    load_message_file,
    load_scene_file,
    load_simdis_bundle,
    load_soap_bundle,
    write_message_file,
    write_scene_file,
)
from vss import (
    assess_simdis_scene_support as assess_simdis_scene_support_root,
)
from vss import (
    assess_soap_scene_support as assess_soap_scene_support_root,
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
    get_cesium_capabilities as get_cesium_capabilities_root,
)
from vss import (
    get_simdis_capabilities as get_simdis_capabilities_root,
)
from vss import (
    get_soap_capabilities as get_soap_capabilities_root,
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
from vss.convert import parse_simdis_bundle_to_scene
from vss.convert import parse_czml_to_scene
from vss.cesium import (
    compile_cesium_document,
    compile_cesium_scene,
    dump_cesium_document_json,
    dump_cesium_scene_json,
    render_cesium_viewer_html,
    write_cesium_document,
    write_cesium_scene,
    write_cesium_viewer,
)
from vss.models import (
    EntityCategory,
    EntityUpsertMessage,
    SceneDocument,
    SceneEntity,
    Style,
    VssScene,
    Wgs84Position,
)
from vss.orb import (
    AnalysisSpec,
    AnalysisTemplateSpec,
    ContourGridSpec,
    CoordinateSystemSpec,
    DerivedVariableSpec,
    DisplayDefaultsSpec,
    FixedSiteSpec,
    ObserverPlatformSpec,
    OrbDefineBlock,
    OrbPackageSpec,
    OrbStabilization,
    SiteBundleSpec,
    WorldViewSpec,
    add_contour_grid,
    add_coordinate_system,
    add_fixed_site,
    add_observer_platform,
    add_site_bundle,
    add_world_view_from_spec,
    build_orb_package,
    dump_orb_text,
    edit_orb_scenario_text,
    load_orb_package,
    normalize_analysis_template,
    parse_orb_scenario_text,
    parse_orb_text,
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
from vss.targets import (
    assess_cesium_scene_support as assess_cesium_scene_support_facade,
)
from vss.targets import (
    assess_simdis_scene_support as assess_simdis_scene_support_facade,
)
from vss.targets import (
    assess_soap_scene_support as assess_soap_scene_support_facade,
)
from vss.targets import (
    compile_cesium_document as compile_cesium_document_facade,
)
from vss.targets import (
    compile_cesium_scene as compile_cesium_scene_facade,
)
from vss.targets import (
    compile_simdis_asi as compile_simdis_asi_facade,
)
from vss.targets import (
    compile_simdis_asi_message as compile_simdis_asi_message_facade,
)
from vss.targets import (
    compile_simdis_bundle as compile_simdis_bundle_facade,
)
from vss.targets import (
    compile_simdis_lines as compile_simdis_lines_facade,
)
from vss.targets import (
    compile_simdis_scene as compile_simdis_scene_facade,
)
from vss.targets import (
    compile_soap_envelope as compile_soap_envelope_facade,
)
from vss.targets import (
    compile_soap_scene as compile_soap_scene_facade,
)
from vss.targets import (
    dump_cesium_document_json as dump_cesium_document_json_facade,
)
from vss.targets import (
    dump_cesium_scene_json as dump_cesium_scene_json_facade,
)
from vss.targets import (
    get_cesium_capabilities as get_cesium_capabilities_facade,
)
from vss.targets import (
    get_simdis_capabilities as get_simdis_capabilities_facade,
)
from vss.targets import (
    get_soap_capabilities as get_soap_capabilities_facade,
)
from vss.targets import (
    render_cesium_viewer_html as render_cesium_viewer_html_facade,
)
from vss.targets import (
    write_cesium_document as write_cesium_document_facade,
)
from vss.targets import (
    write_cesium_scene as write_cesium_scene_facade,
)
from vss.targets import (
    write_cesium_viewer as write_cesium_viewer_facade,
)

EXAMPLE_PATH = Path("examples/cesium/air-track.json")
SCENE_EXAMPLE_PATH = Path("examples/scenes/air-pair.scene.json")
MIXED_SCENE_EXAMPLE_PATH = Path("examples/scenes/mixed-ops.scene.json")
CORRIDOR_SCENE_EXAMPLE_PATH = Path("examples/scenes/corridor-demo.scene.json")
ELLIPSE_CIRCLE_SCENE_EXAMPLE_PATH = Path("examples/scenes/ellipse-circle-demo.scene.json")
WALL_SCENE_EXAMPLE_PATH = Path("examples/scenes/wall-demo.scene.json")
BOX_SCENE_EXAMPLE_PATH = Path("examples/scenes/box-demo.scene.json")
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


@pytest.fixture
def example_message() -> EntityUpsertMessage:
    return load_message_file(EXAMPLE_PATH)


@pytest.fixture
def example_scene(example_message: EntityUpsertMessage) -> VssScene:
    return VssScene.from_messages(
        [example_message],
        scene_id="demo-scene",
        scene_name="Demo Scene",
    )


def test_target_packages_are_canonical_compile_entrypoints() -> None:
    assert assess_cesium_scene_support_facade is assess_cesium_scene_support_root
    assert assess_simdis_scene_support_facade is assess_simdis_scene_support_root
    assert assess_soap_scene_support_facade is assess_soap_scene_support_root
    assert compile_cesium_document_facade is compile_cesium_document
    assert compile_cesium_scene_facade is compile_cesium_scene
    assert dump_cesium_document_json_facade is dump_cesium_document_json
    assert dump_cesium_scene_json_facade is dump_cesium_scene_json
    assert render_cesium_viewer_html_facade is render_cesium_viewer_html
    assert write_cesium_document_facade is write_cesium_document
    assert write_cesium_scene_facade is write_cesium_scene
    assert write_cesium_viewer_facade is write_cesium_viewer
    assert compile_simdis_asi_facade is compile_simdis_asi
    assert compile_simdis_asi_message_facade is compile_simdis_asi_message
    assert compile_simdis_lines_facade is compile_simdis_lines
    assert compile_simdis_bundle_facade is compile_simdis_bundle
    assert compile_simdis_scene_facade is compile_simdis_scene
    assert compile_soap_envelope_facade is compile_soap_envelope
    assert compile_soap_scene_facade is compile_soap_scene
    assert get_cesium_capabilities_facade is get_cesium_capabilities_root
    assert get_simdis_capabilities_facade is get_simdis_capabilities_root
    assert get_soap_capabilities_facade is get_soap_capabilities_root


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
    assert get_cesium_capabilities_root() == get_cesium_capabilities_facade()
    assert get_simdis_capabilities_root() == get_simdis_capabilities_facade()
    assert get_soap_capabilities_root() == get_soap_capabilities_facade()
    assert load_orb_package_root is load_orb_package
    assert write_orb_package_root is write_orb_package


def test_static_target_capability_reports_describe_current_surfaces() -> None:
    cesium = get_cesium_capabilities_root()
    simdis = get_simdis_capabilities_root()
    soap = get_soap_capabilities_root()

    assert [surface.id for surface in cesium.surfaces] == ["czml", "cesium-js-viewer", "cesium-js-loader"]
    assert [surface.id for surface in simdis.surfaces] == ["simdis-asi", "simdis-gog", "simdis-bundle"]
    assert [surface.id for surface in soap.surfaces] == ["soap-envelope", "soap-bundle", "orb-related"]
    assert any(feature.featureId == "object.entity.orientation" and feature.support == "partial" for feature in cesium.schemaFeatures)
    assert any(feature.featureId == "object.path.sampledMotion" and feature.support == "partial" for feature in cesium.schemaFeatures)
    assert any(feature.featureId == "object.track.sampledMotion" and feature.support == "strong" for feature in cesium.schemaFeatures)
    assert any(feature.featureId == "object.rectangle.geometry" and feature.support == "strong" for feature in cesium.schemaFeatures)
    assert any(feature.featureId == "object.corridor.geometry" and feature.support == "strong" for feature in cesium.schemaFeatures)
    assert any(feature.featureId == "object.ellipse.geometry" and feature.support == "strong" for feature in cesium.schemaFeatures)
    assert any(feature.featureId == "object.circle.geometry" and feature.support == "strong" for feature in cesium.schemaFeatures)
    assert any(feature.featureId == "object.wall.geometry" and feature.support == "strong" for feature in cesium.schemaFeatures)
    assert any(feature.featureId == "object.box.geometry" and feature.support == "strong" for feature in cesium.schemaFeatures)
    assert any(feature.featureId == "style.model" and feature.support == "unsupported" for feature in simdis.schemaFeatures)
    assert any(feature.featureId == "views" and feature.support == "partial" for feature in soap.schemaFeatures)


def test_scene_target_assessment_reports_supported_and_unsupported_features() -> None:
    scene = load_scene_file(MIXED_SCENE_EXAMPLE_PATH)

    cesium = assess_scene_for_target(scene, "cesium")
    simdis = assess_scene_for_target(scene, "simdis")
    soap = assess_scene_for_target(scene, "soap")

    assert cesium.objectCount == 5
    assert any(feature.featureId == "object.overlay.polygon" and feature.support == "strong" for feature in cesium.features)
    assert any(feature.featureId == "object.entity.orientation" and feature.support == "partial" for feature in cesium.features)

    assert simdis.objectCount == 5
    assert any(feature.featureId == "style.model" and feature.support == "unsupported" for feature in simdis.features)
    assert any(feature.featureId == "object.overlay.polyline" and feature.support == "strong" for feature in simdis.features)

    assert soap.objectCount == 5
    assert any(feature.featureId == "style.icon" and feature.support == "unsupported" for feature in soap.features)
    assert any(feature.featureId == "object.sensor" and feature.support == "partial" for feature in soap.features)


def test_path_scene_assessment_reports_path_support() -> None:
    scene = load_scene_file(Path("examples/scenes/path-demo.scene.json"))
    assessment = assess_scene_for_target(scene, "cesium")
    assert assessment.objectCount == 1
    assert any(feature.featureId == "object.path.sampledMotion" and feature.support == "partial" for feature in assessment.features)


def test_track_scene_assessment_reports_track_support() -> None:
    scene = load_scene_file(Path("examples/scenes/track-demo.scene.json"))
    assessment = assess_scene_for_target(scene, "cesium")
    assert assessment.objectCount == 1
    assert any(feature.featureId == "object.track.sampledMotion" and feature.support == "strong" for feature in assessment.features)


def test_rectangle_scene_assessment_reports_rectangle_support() -> None:
    scene = load_scene_file(Path("examples/scenes/rectangle-demo.scene.json"))
    assessment = assess_scene_for_target(scene, "cesium")
    assert assessment.objectCount == 1
    assert any(feature.featureId == "object.rectangle.geometry" and feature.support == "strong" for feature in assessment.features)


def test_corridor_scene_assessment_reports_corridor_support() -> None:
    scene = load_scene_file(CORRIDOR_SCENE_EXAMPLE_PATH)
    assessment = assess_scene_for_target(scene, "cesium")
    assert assessment.objectCount == 1
    assert any(feature.featureId == "object.corridor.geometry" and feature.support == "strong" for feature in assessment.features)


def test_ellipse_circle_scene_assessment_reports_ellipse_and_circle_support() -> None:
    scene = load_scene_file(ELLIPSE_CIRCLE_SCENE_EXAMPLE_PATH)
    assessment = assess_scene_for_target(scene, "cesium")
    assert assessment.objectCount == 2
    assert any(feature.featureId == "object.ellipse.geometry" and feature.support == "strong" for feature in assessment.features)
    assert any(feature.featureId == "object.circle.geometry" and feature.support == "strong" for feature in assessment.features)


def test_wall_scene_assessment_reports_wall_support() -> None:
    scene = load_scene_file(WALL_SCENE_EXAMPLE_PATH)
    assessment = assess_scene_for_target(scene, "cesium")
    assert assessment.objectCount == 1
    assert any(feature.featureId == "object.wall.geometry" and feature.support == "strong" for feature in assessment.features)


def test_box_scene_assessment_reports_box_support() -> None:
    scene = load_scene_file(BOX_SCENE_EXAMPLE_PATH)
    assessment = assess_scene_for_target(scene, "cesium")
    assert assessment.objectCount == 1
    assert any(feature.featureId == "object.box.geometry" and feature.support == "strong" for feature in assessment.features)


def test_example_loads(example_message: EntityUpsertMessage) -> None:
    assert isinstance(example_message, EntityUpsertMessage)
    assert example_message.payload.entityId == "aircraft-001"


def test_scene_example_loads() -> None:
    scene = load_scene_file(SCENE_EXAMPLE_PATH)
    assert scene.document.id == "air-pair-demo"
    assert len(scene.objects) == 2
    assert len(scene.entities) == 2
    assert scene.entities[1].id == "aircraft-002"


def test_mixed_scene_example_loads() -> None:
    scene = load_scene_file(MIXED_SCENE_EXAMPLE_PATH)
    assert scene.document.id == "mixed-ops-demo"
    assert len(scene.objects) == 5
    assert len(scene.entities) == 3
    assert len(scene.overlays) == 2
    assert scene.entities[0].category is not None
    assert scene.entities[1].category is not None
    assert scene.entities[2].category is not None
    assert scene.entities[0].category.value == "air"
    assert scene.entities[1].category.value == "sensor"
    assert scene.entities[2].category.value == "ground"
    assert scene.overlays[0].id == "flight-corridor-a"
    assert scene.overlays[0].polyline is not None
    assert len(scene.overlays[0].polyline.positions) == 3
    assert scene.overlays[1].id == "coverage-zone-b"
    assert scene.overlays[1].geometryType == "polygon"
    assert scene.overlays[1].polygon is not None
    assert len(scene.overlays[1].polygon.positions) == 4


def test_path_scene_example_loads() -> None:
    scene = load_scene_file(Path("examples/scenes/path-demo.scene.json"))
    assert scene.document.id == "path-demo"
    assert len(scene.objects) == 1
    assert len(scene.paths) == 1
    path = scene.paths[0]
    assert path.id == "track-001-path"
    assert len(path.samples) == 3
    assert path.samples[0].position.longitudeDeg == -97.74


def test_track_scene_example_loads() -> None:
    scene = load_scene_file(Path("examples/scenes/track-demo.scene.json"))
    assert scene.document.id == "track-demo"
    assert len(scene.objects) == 1
    assert len(scene.tracks) == 1
    track = scene.tracks[0]
    assert track.id == "track-001"
    assert len(track.samples) == 3
    assert track.orientation is not None
    assert track.orientation.headingDeg == 72.0


def test_rectangle_scene_example_loads() -> None:
    scene = load_scene_file(Path("examples/scenes/rectangle-demo.scene.json"))
    assert scene.document.id == "rectangle-demo"
    assert len(scene.objects) == 1
    assert len(scene.overlays) == 1
    overlay = scene.overlays[0]
    assert overlay.geometryType == "rectangle"
    assert overlay.rectangle is not None
    assert overlay.rectangle.westSouthEastNorthDegrees == (-97.78, 30.24, -97.62, 30.36)


def test_corridor_scene_example_loads() -> None:
    scene = load_scene_file(CORRIDOR_SCENE_EXAMPLE_PATH)
    assert scene.document.id == "corridor-demo"
    assert len(scene.objects) == 1
    assert len(scene.overlays) == 1
    overlay = scene.overlays[0]
    assert overlay.geometryType == "corridor"
    assert overlay.corridor is not None
    assert overlay.corridor.widthMeters == 75000.0
    assert len(overlay.corridor.positions) == 3


def test_ellipse_circle_scene_example_loads() -> None:
    scene = load_scene_file(ELLIPSE_CIRCLE_SCENE_EXAMPLE_PATH)
    assert scene.document.id == "ellipse-circle-demo"
    assert len(scene.objects) == 2
    assert len(scene.overlays) == 2
    ellipse, circle = scene.overlays
    assert ellipse.geometryType == "ellipse"
    assert ellipse.ellipse is not None
    assert ellipse.ellipse.semiMajorAxisMeters == 120000.0
    assert ellipse.ellipse.semiMinorAxisMeters == 60000.0
    assert circle.geometryType == "circle"
    assert circle.circle is not None
    assert circle.circle.radiusMeters == 80000.0


def test_wall_scene_example_loads() -> None:
    scene = load_scene_file(WALL_SCENE_EXAMPLE_PATH)
    assert scene.document.id == "wall-demo"
    assert len(scene.objects) == 1
    assert len(scene.overlays) == 1
    wall = scene.overlays[0]
    assert wall.geometryType == "wall"
    assert wall.wall is not None
    assert wall.wall.positions[0].longitudeDeg == -97.66
    assert wall.wall.maximumHeightsMeters == [2500.0, 3000.0, 2800.0]


def test_box_scene_example_loads() -> None:
    scene = load_scene_file(BOX_SCENE_EXAMPLE_PATH)
    assert scene.document.id == "box-demo"
    assert len(scene.objects) == 1
    assert len(scene.overlays) == 1
    box = scene.overlays[0]
    assert box.geometryType == "box"
    assert box.box is not None
    assert box.box.dimensionsMeters == (50000.0, 30000.0, 12000.0)


def test_cesium_output_contains_entity_packet(example_message: EntityUpsertMessage) -> None:
    packets = compile_cesium_document(example_message)
    assert packets[1]["id"] == "aircraft-001"
    assert packets[1]["position"]["cartographicDegrees"] == [-97.7431, 30.2672, 9450.0]
    assert packets[1]["properties"]["category"] == "air"
    assert packets[1]["properties"]["orientationDegrees"] == {
        "heading": 72.0,
        "pitch": 1.5,
        "roll": 0.2,
    }
    assert packets[1]["model"]["uri"] == "https://example.org/assets/aircraft.glb"
    assert packets[1]["point"]["color"]["rgba"] == [64, 145, 255, 255]


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


def test_scene_round_trip_and_cesium_scene_output(example_scene: VssScene) -> None:
    dumped = dump_scene(example_scene)
    assert dumped["document"]["id"] == "demo-scene"
    assert dumped["objects"][0]["id"] == "aircraft-001"

    packets = compile_cesium_scene(example_scene)
    assert packets[0]["name"] == "Demo Scene"
    assert packets[1]["id"] == "aircraft-001"
    assert packets[1]["properties"]["category"] == "air"
    assert "clock" in packets[0]

    dumped_scene_json = dump_scene_json(example_scene)
    assert '"schemaVersion": "1.0.0-scene"' in dumped_scene_json
    dumped_czml = dump_cesium_scene_json(example_scene)
    assert '"name": "Demo Scene"' in dumped_czml
    assert '"id": "aircraft-001"' in dumped_czml


def test_scene_example_compiles_to_multi_entity_czml() -> None:
    scene = load_scene_file(SCENE_EXAMPLE_PATH)
    packets = compile_cesium_scene(scene)
    assert packets[0]["name"] == "Air Pair Demo"
    assert len(packets) == 3
    assert packets[1]["id"] == "aircraft-001"
    assert packets[2]["id"] == "aircraft-002"


def test_mixed_scene_compiles_to_multiple_visual_paths() -> None:
    scene = load_scene_file(MIXED_SCENE_EXAMPLE_PATH)
    packets = compile_cesium_scene(scene)
    assert packets[0]["name"] == "Mixed Ops Demo"
    assert len(packets) == 6
    assert packets[1]["model"]["uri"] == "https://example.org/assets/aircraft.glb"
    assert packets[2]["billboard"]["image"] == "https://example.org/assets/sensor.png"
    assert packets[3]["properties"]["category"] == "ground"
    assert packets[4]["properties"]["category"] == "overlay"
    assert packets[4]["polyline"]["width"] == 4.0
    assert packets[4]["polyline"]["positions"]["cartographicDegrees"] == [
        -96.88,
        32.70,
        5500.0,
        -96.79,
        32.76,
        6000.0,
        -96.69,
        32.82,
        6400.0,
    ]
    assert packets[5]["properties"]["category"] == "overlay"
    assert packets[5]["polygon"]["positions"]["cartographicDegrees"] == [
        -96.76,
        32.77,
        1500.0,
        -96.72,
        32.76,
        1500.0,
        -96.7,
        32.79,
        1800.0,
        -96.74,
        32.81,
        1800.0,
    ]
    assert packets[5]["polygon"]["positions"]["cartographicDegrees"] == [
        -96.760,
        32.770,
        1500.0,
        -96.720,
        32.760,
        1500.0,
        -96.700,
        32.790,
        1800.0,
        -96.740,
        32.810,
        1800.0,
    ]


def test_path_scene_compiles_to_czml_path_graphics() -> None:
    scene = load_scene_file(Path("examples/scenes/path-demo.scene.json"))
    packets = compile_cesium_scene(scene)
    assert packets[0]["name"] == "Path Demo"
    assert len(packets) == 2
    assert packets[1]["id"] == "track-001-path"
    assert packets[1]["properties"]["objectType"] == "path"
    assert packets[1]["path"]["width"] == 3.5
    assert packets[1]["path"]["material"]["solidColor"]["color"]["rgba"] == [69, 142, 255, 255]
    assert packets[1]["position"]["epoch"] == "2026-06-01T12:00:00+00:00"
    assert packets[1]["position"]["cartographicDegrees"] == [
        0.0,
        -97.74,
        30.26,
        9000.0,
        180.0,
        -97.62,
        30.34,
        9200.0,
        360.0,
        -97.51,
        30.41,
        9600.0,
    ]


def test_track_scene_compiles_to_czml_track_graphics() -> None:
    scene = load_scene_file(Path("examples/scenes/track-demo.scene.json"))
    packets = compile_cesium_scene(scene)
    assert packets[0]["name"] == "Track Demo"
    assert len(packets) == 2
    assert packets[1]["id"] == "track-001"
    assert packets[1]["properties"]["objectType"] == "track"
    assert packets[1]["properties"]["category"] == "track"
    assert packets[1]["properties"]["orientationDegrees"] == {
        "heading": 72.0,
        "pitch": 1.5,
        "roll": 0.2,
    }
    assert packets[1]["path"]["width"] == 4.0
    assert packets[1]["path"]["material"]["solidColor"]["color"]["rgba"] == [235, 99, 52, 255]
    assert packets[1]["position"]["cartographicDegrees"] == [
        0.0,
        -97.85,
        30.25,
        9100.0,
        120.0,
        -97.74,
        30.3,
        9300.0,
        300.0,
        -97.61,
        30.38,
        9700.0,
    ]


def test_rectangle_scene_compiles_to_czml_rectangle_graphics() -> None:
    scene = load_scene_file(Path("examples/scenes/rectangle-demo.scene.json"))
    packets = compile_cesium_scene(scene)
    assert packets[0]["name"] == "Rectangle Demo"
    assert len(packets) == 2
    assert packets[1]["id"] == "rect-001"
    assert packets[1]["properties"]["objectType"] == "overlay"
    assert packets[1]["rectangle"]["coordinates"]["wsenDegrees"] == [-97.78, 30.24, -97.62, 30.36]
    assert packets[1]["rectangle"]["height"] == 0.0
    assert packets[1]["rectangle"]["rotation"] == 0.0
    assert packets[1]["rectangle"]["material"]["solidColor"]["color"]["rgba"] == [52, 199, 89, 180]


def test_corridor_scene_compiles_to_czml_corridor_graphics() -> None:
    scene = load_scene_file(CORRIDOR_SCENE_EXAMPLE_PATH)
    packets = compile_cesium_scene(scene)
    assert packets[0]["name"] == "Corridor Demo"
    assert len(packets) == 2
    assert packets[1]["id"] == "corridor-001"
    assert packets[1]["properties"]["objectType"] == "overlay"
    assert packets[1]["corridor"]["width"] == 75000.0
    assert packets[1]["corridor"]["cornerType"] == "ROUNDED"
    assert packets[1]["corridor"]["material"]["solidColor"]["color"]["rgba"] == [173, 114, 255, 220]


def test_ellipse_circle_scene_compiles_to_czml_ellipse_graphics() -> None:
    scene = load_scene_file(ELLIPSE_CIRCLE_SCENE_EXAMPLE_PATH)
    packets = compile_cesium_scene(scene)
    assert packets[0]["name"] == "Ellipse Circle Demo"
    assert len(packets) == 3
    assert packets[1]["id"] == "ellipse-001"
    assert packets[1]["ellipse"]["semiMajorAxis"] == 120000.0
    assert packets[1]["ellipse"]["semiMinorAxis"] == 60000.0
    assert packets[2]["id"] == "circle-001"
    assert packets[2]["ellipse"]["semiMajorAxis"] == 80000.0
    assert packets[2]["ellipse"]["semiMinorAxis"] == 80000.0


def test_wall_scene_compiles_to_czml_wall_graphics() -> None:
    scene = load_scene_file(WALL_SCENE_EXAMPLE_PATH)
    packets = compile_cesium_scene(scene)
    assert packets[0]["name"] == "Wall Demo"
    assert len(packets) == 2
    assert packets[1]["id"] == "wall-001"
    assert packets[1]["wall"]["positions"]["cartographicDegrees"] == [
        -97.66,
        30.3,
        0.0,
        -97.59,
        30.35,
        0.0,
        -97.52,
        30.39,
        0.0,
    ]
    assert packets[1]["wall"]["maximumHeights"] == [2500.0, 3000.0, 2800.0]
    assert packets[1]["wall"]["minimumHeights"] == [0.0, 0.0, 0.0]


def test_corridor_scene_round_trip_through_czml_parser() -> None:
    scene = load_scene_file(CORRIDOR_SCENE_EXAMPLE_PATH)
    rebuilt = parse_czml_to_scene(dump_cesium_scene_json(scene), source="czml")
    assert len(rebuilt.overlays) == 1
    overlay = rebuilt.overlays[0]
    assert overlay.geometryType == "corridor"
    assert overlay.corridor is not None
    assert overlay.corridor.widthMeters == 75000.0
    assert overlay.corridor.cornerType == "rounded"


def test_ellipse_circle_scene_round_trip_through_czml_parser() -> None:
    scene = load_scene_file(ELLIPSE_CIRCLE_SCENE_EXAMPLE_PATH)
    rebuilt = parse_czml_to_scene(dump_cesium_scene_json(scene), source="czml")
    assert len(rebuilt.overlays) == 2
    assert rebuilt.overlays[0].geometryType == "ellipse"
    assert rebuilt.overlays[0].ellipse is not None
    assert rebuilt.overlays[0].ellipse.semiMajorAxisMeters == 120000.0
    assert rebuilt.overlays[1].geometryType == "circle"
    assert rebuilt.overlays[1].circle is not None
    assert rebuilt.overlays[1].circle.radiusMeters == 80000.0


def test_wall_scene_round_trip_through_czml_parser() -> None:
    scene = load_scene_file(WALL_SCENE_EXAMPLE_PATH)
    rebuilt = parse_czml_to_scene(dump_cesium_scene_json(scene), source="czml")
    assert len(rebuilt.overlays) == 1
    wall = rebuilt.overlays[0]
    assert wall.geometryType == "wall"
    assert wall.wall is not None
    assert wall.wall.maximumHeightsMeters == [2500.0, 3000.0, 2800.0]


def test_scene_files_can_be_written(example_scene: VssScene, tmp_path: Path) -> None:
    scene_path = write_scene_file(example_scene, tmp_path / "scene.json")
    czml_path = write_cesium_scene(example_scene, tmp_path / "scene.czml.json")

    loaded_scene = load_scene_file(scene_path)
    assert loaded_scene.document.name == "Demo Scene"
    assert '"id": "aircraft-001"' in czml_path.read_text(encoding="utf-8")


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
    rebuilt = load_simdis_bundle_files(files)
    assert rebuilt.entities.platforms[0].id == "aircraft-001"
    assert rebuilt.scenarioAsi.startswith("ReferenceYear 2026")
    assert "PLATFORM aircraft-001" in rebuilt.overlaysGog


def test_simdis_bundle_round_trip_from_directory(example_message: EntityUpsertMessage, tmp_path: Path) -> None:
    bundle = compile_simdis_bundle(example_message)
    write_simdis_bundle(bundle, tmp_path)
    rebuilt = load_simdis_bundle(tmp_path)
    assert rebuilt.manifest.target == "simdis"
    initial_position = rebuilt.entities.platforms[0].initialPosition
    assert initial_position is not None
    assert initial_position.lon == -97.7431


def test_simdis_scene_bundle_round_trip_from_directory(tmp_path: Path) -> None:
    scene = load_scene_file(MIXED_SCENE_EXAMPLE_PATH)
    bundle = compile_simdis_scene(scene)
    write_simdis_bundle(bundle, tmp_path)
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


def test_message_and_cesium_files_can_be_written(example_message: EntityUpsertMessage, tmp_path: Path) -> None:
    message_path = write_message_file(example_message, tmp_path / "message.json")
    cesium_path = write_cesium_document(example_message, tmp_path / "scene.czml")

    assert (
        EntityUpsertMessage.model_validate_json(message_path.read_text(encoding="utf-8")).messageId
        == example_message.messageId
    )
    assert '"id": "aircraft-001"' in cesium_path.read_text(encoding="utf-8")


def test_cesium_document_json_is_serializable(example_message: EntityUpsertMessage) -> None:
    dumped = dump_cesium_document_json(example_message)
    assert '"id": "document"' in dumped
    assert '"id": "aircraft-001"' in dumped


def test_cesium_viewer_html_references_czml() -> None:
    html = render_cesium_viewer_html(
        czml_path="./air-track.czml.json",
        title="VSS Air Track Viewer",
    )
    assert "Cesium.Viewer" in html
    assert 'CzmlDataSource.load("./air-track.czml.json")' in html
    assert "VSS Air Track Viewer" in html


def test_cesium_viewer_file_can_be_written(tmp_path: Path) -> None:
    viewer_path = write_cesium_viewer(
        tmp_path / "air-track.viewer.html",
        czml_path="./air-track.czml.json",
        title="VSS Air Track Viewer",
    )
    html = viewer_path.read_text(encoding="utf-8")
    assert "air-track.czml.json" in html


def test_orb_parser_preserves_round_trip_text() -> None:
    document = parse_orb_text(ORB_SNIPPET)
    assert dump_orb_text(document) == ORB_SNIPPET


def test_orb_parser_extracts_define_blocks() -> None:
    document = parse_orb_text(ORB_SNIPPET)
    assert [block.block_kind for block in document.define_blocks] == ["UNITS", "GROUP", "VIEW"]
    assert isinstance(document.define_blocks[0], OrbDefineBlock)
    assert document.entries[0].tokens == ("56", "revision")
    assert document.entries[1].tokens == ("SOAP_SCENARIO_FILE",)


def test_orb_parser_builds_indented_child_lists() -> None:
    document = parse_orb_text(ORB_SNIPPET)
    group_block = document.define_blocks[1]
    assert group_block.define_tokens == ("GROUP", "PLATFORM_GROUP", "{New}")
    platlist = group_block.children[0]
    assert platlist.keyword == "PLATLIST"
    assert [child.tokens[0] for child in platlist.children] == [".Earth CI Observer", "Air", "END_OF_INPUT"]

    view_block = document.define_blocks[2]
    icons = view_block.children[1]
    assert icons.keyword == "ICONS"
    icon_list = icons.children[0]
    assert icon_list.keyword == "ICON_LIST"
    assert [child.tokens[0] for child in icon_list.children] == ["ABQ", "Air(Smooth)", "END_OF_INPUT"]


def test_orb_parser_closes_sentinel_sections() -> None:
    document = parse_orb_text(ORB_TYPED_SNIPPET)
    config_block = document.define_blocks[2]
    assert [child.keyword for child in config_block.children[-2:]] == ["DRIVER", "AUTO_LOAD"]
    driver = config_block.children[-2]
    assert [child.keyword for child in driver.children] == ["BORDER", "DRIVER_END"]


def test_orb_typed_scenario_extracts_units_clock_and_config() -> None:
    scenario = parse_orb_scenario_text(ORB_TYPED_SNIPPET)
    assert scenario.revision == 56
    assert scenario.file_type == "SOAP_SCENARIO_FILE"
    assert scenario.units is not None
    assert scenario.clock is not None
    assert scenario.config is not None

    assert scenario.units.distance == "KILOMETERS"
    assert scenario.units.time == "SECONDS"
    assert scenario.units.angle_shift is False

    assert scenario.clock.epoch == (1994, 11, 1, 0, 0, 0)
    assert scenario.clock.simulation_time == 9840
    assert scenario.clock.pause is True
    assert scenario.clock.real_time is False
    assert scenario.clock.time_step == 60

    assert scenario.config.properties["VERSION"] == "Version 15.3.2"
    assert scenario.config.properties["CLOCK_FONT_COLOR"] == "Gray"
    assert scenario.config.properties["TRANSCTL"] == -637813.7
    assert scenario.config.clock_cone_grid["CLOCK_COUNT"] == 12
    assert scenario.config.clock_cone_grid["GRID_COLOR"] == "Magenta"
    assert scenario.config.driver["BORDER"] is False
    assert scenario.config.properties["AUTO_LOAD"] is False


def test_orb_typed_scenario_extracts_group_platform_trajectory_and_view() -> None:
    scenario = parse_orb_scenario_text(ORB_EXPANDED_SNIPPET)
    assert len(scenario.groups) == 1
    assert len(scenario.platforms) == 1
    assert len(scenario.trajectories) == 1
    assert len(scenario.views) == 1

    group = scenario.groups[0]
    assert group.group_type == "PLATFORM_GROUP"
    assert group.name == "{New}"
    assert group.properties["PLATLIST"] is True
    assert group.lists["PLATLIST"] == [".Earth CI Observer", "Air", "END_OF_INPUT"]

    platform = scenario.platforms[0]
    assert platform.platform_type == "AIRROUTE"
    assert platform.name == "Air"
    assert platform.properties["PLAT"] == "Earth"
    assert platform.properties["WAYPOINT_TYPE"] == "BY_SPEED"
    assert platform.repeated["WAYPOINT"][0] == (33.93, -118.4, 1, 0, 0.205778)
    assert platform.properties["SMOOTH"] is False

    trajectory = scenario.trajectories[0]
    assert trajectory.name == "Air Trajectory"
    assert trajectory.properties["CS"] == "ECR"
    assert trajectory.properties["TRAJECTORY_CHOICE"] == ("RELATIVE", "FORWARD", 49000)
    assert trajectory.trajectory_rows[1] == (2001, 4, 10, 1, 1, 1)

    view = scenario.views[0]
    assert view.view_type == "WORLD"
    assert view.name == ".Moon CI Observer View"
    assert view.observer == ".Moon CI Observer"
    assert view.coordinate_system == ".Moon Pointing"
    assert view.sets["CONES"] is True
    assert view.lists["ICON_LIST"] == ["ABQ", "Air(Smooth)", "END_OF_INPUT"]
    assert view.properties["ICON_LIST"] is True
    assert view.properties["VIEWANGLES"] == (-90, 90)


@pytest.mark.parametrize(
    "sample_path",
    [
        ORB_SAMPLE_DIR / "air_route_simple.orb",
        ORB_SAMPLE_DIR / "demo.orb",
    ],
)
def test_real_orb_files_round_trip_exactly(sample_path: Path) -> None:
    raw = sample_path.read_text(encoding="utf-8")
    assert dump_orb_text(parse_orb_text(raw)) == raw


def test_orb_typed_scenario_extracts_mapcenter_spice_cs_analysis_and_grid() -> None:
    scenario = parse_orb_scenario_text(ORB_REMAINDER_SNIPPET)
    assert len(scenario.map_centers) == 1
    assert len(scenario.spices) == 1
    assert len(scenario.coordinate_systems) == 1
    assert len(scenario.analyses) == 1
    assert len(scenario.grids) == 1

    assert scenario.map_centers[0].properties["MAPFILE"] == "wmedium.wld"
    assert scenario.spices[0].repeated["SPICEFILE"] == ["leap.tls", "constant.tpc"]

    cs = scenario.coordinate_systems[0]
    assert cs.cs_type == "CSBASIS"
    assert cs.name == "ECR"
    assert cs.properties["AXES"] is False
    assert cs.properties["TRACK"] == ("Z", "LONLAT", 0, 90)

    analysis = scenario.analyses[0]
    assert analysis.name == ".GM Earth"
    assert analysis.properties["VARIABLE"] == ("CONSTANT", 398600.5)
    assert analysis.variable_details["DISTANCEU"] == ("KILOMETERS", 3)
    assert analysis.variable_details["COMMENT"] == "Earth GM"

    grid = scenario.grids[0]
    assert grid.grid_type == "CONTOUR"
    assert grid.name == ".Earth Lat/Lon Grid"
    assert grid.properties["DIMENSION"] == (8, 8, 10)
    assert grid.properties["PLANE"] == "XY"


def test_orb_editor_updates_existing_lines_and_round_trips() -> None:
    editor = edit_orb_scenario_text(ORB_TYPED_SNIPPET)
    editor.set_config_property("AUTO_LOAD", True)
    editor.set_units_property("TIME", "HOURS")
    updated = editor.refresh()

    assert updated.config is not None
    assert updated.units is not None
    assert updated.config.properties["AUTO_LOAD"] is True
    assert updated.units.time == "HOURS"

    rendered = editor.to_text()
    assert "\tAUTO_LOAD ON\n" in rendered
    assert "\tTIME HOURS\n" in rendered
    assert dump_orb_text(parse_orb_text(rendered)) == rendered


def test_orb_editor_updates_named_blocks() -> None:
    editor = edit_orb_scenario_text(ORB_EXPANDED_SNIPPET)
    editor.set_platform_property("Air", "SMOOTH", True)
    editor.set_view_property(".Moon CI Observer View", "VIEWANGLES", (-45, 45))
    updated = editor.refresh()

    assert updated.platforms[0].properties["SMOOTH"] is True
    assert updated.views[0].properties["VIEWANGLES"] == (-45, 45)
    rendered = editor.to_text()
    assert "SMOOTH ON" in rendered
    assert "VIEWANGLES -45 45" in rendered


def test_orb_editor_deletes_singleton_statements() -> None:
    editor = edit_orb_scenario_text(ORB_TYPED_SNIPPET)
    editor.delete_config_property("AUTO_LOAD")
    editor.delete_units_property("ANGLE_SHIFT")
    editor.delete_clock_property("REAL_TIME")
    updated = editor.refresh()

    assert updated.config is not None
    assert updated.units is not None
    assert updated.clock is not None
    assert "AUTO_LOAD" not in updated.config.properties
    assert updated.units.angle_shift is None
    assert updated.clock.real_time is None

    rendered = editor.to_text()
    assert "AUTO_LOAD" not in rendered
    assert "ANGLE_SHIFT" not in rendered
    assert "REAL_TIME" not in rendered
    assert dump_orb_text(parse_orb_text(rendered)) == rendered


def test_orb_editor_creates_new_named_blocks() -> None:
    editor = edit_orb_scenario_text(ORB_SNIPPET)
    editor.create_platform(
        "ECR_FIXED",
        "New Site",
        properties={
            "STATE": (35.0, -97.0, 0),
            "PLAT": "Earth",
            "SHAPE": "STATION",
            "ICON": True,
        },
    )
    editor.create_view(
        "WORLD",
        "New View",
        "New Site",
        "ECR",
        properties={
            "ICONS": True,
            "VIEWANGLES": (-30, 60),
        },
    )
    updated = editor.refresh()

    created_platform = next(platform for platform in updated.platforms if platform.name == "New Site")
    assert created_platform.platform_type == "ECR_FIXED"
    assert created_platform.state == (35.0, -97.0, 0)
    assert created_platform.properties["ICON"] is True

    created_view = next(view for view in updated.views if view.name == "New View")
    assert created_view.view_type == "WORLD"
    assert created_view.observer == "New Site"
    assert created_view.coordinate_system == "ECR"
    assert created_view.properties["VIEWANGLES"] == (-30, 60)

    rendered = editor.to_text()
    assert 'DEFINE PLATFORM ECR_FIXED "New Site"' in rendered
    assert 'DEFINE VIEW WORLD "New View" "New Site" ECR' in rendered
    assert dump_orb_text(parse_orb_text(rendered)) == rendered


def test_orb_editor_deletes_named_blocks() -> None:
    editor = edit_orb_scenario_text(ORB_EXPANDED_SNIPPET)
    editor.delete_platform("Air")
    editor.delete_view(".Moon CI Observer View")
    updated = editor.refresh()

    assert not updated.platforms
    assert not updated.views

    rendered = editor.to_text()
    assert 'DEFINE PLATFORM AIRROUTE  "Air"' not in rendered
    assert 'DEFINE VIEW WORLD  ".Moon CI Observer View"' not in rendered
    assert dump_orb_text(parse_orb_text(rendered)) == rendered


def test_orb_editor_updates_group_and_view_list_items() -> None:
    editor = edit_orb_scenario_text(ORB_SNIPPET)
    editor.set_group_list_items("{New}", "PLATLIST", ["Alpha", "Bravo", "END_OF_INPUT"])
    editor.set_view_list_items(".Moon CI Observer View", "ICON_LIST", ["One", "Two", "END_OF_INPUT"])
    updated = editor.refresh()

    assert updated.groups[0].lists["PLATLIST"] == ["Alpha", "Bravo", "END_OF_INPUT"]
    assert updated.views[0].lists["ICON_LIST"] == ["One", "Two", "END_OF_INPUT"]

    rendered = editor.to_text()
    assert '"Alpha"' in rendered
    assert '"Bravo"' in rendered
    assert '"One"' in rendered
    assert '"Two"' in rendered
    assert dump_orb_text(parse_orb_text(rendered)) == rendered


def test_orb_editor_updates_spice_files_and_platform_repeated_rows() -> None:
    editor = edit_orb_scenario_text(f"{ORB_REMAINDER_SNIPPET}{ORB_EXPANDED_SNIPPET}")
    editor.set_spice_files(["alpha.tls", "beta.tpc"])
    editor.set_platform_repeated(
        "Air",
        "WAYPOINT",
        [
            (10.0, 20.0, 1, 0, 0.1),
            (30.0, 40.0, 2, 0, 0.2),
        ],
    )
    updated = editor.refresh()

    assert updated.spices[0].repeated["SPICEFILE"] == ["alpha.tls", "beta.tpc"]
    assert updated.platforms[0].repeated["WAYPOINT"] == [
        (10.0, 20.0, 1, 0, 0.1),
        (30.0, 40.0, 2, 0, 0.2),
    ]

    rendered = editor.to_text()
    assert 'SPICEFILE "alpha.tls"' in rendered
    assert 'SPICEFILE "beta.tpc"' in rendered
    assert "WAYPOINT 10.0 20.0 1 0 0.1" in rendered
    assert "WAYPOINT 30.0 40.0 2 0 0.2" in rendered
    assert dump_orb_text(parse_orb_text(rendered)) == rendered


def test_orb_editor_updates_trajectory_rows() -> None:
    editor = edit_orb_scenario_text(ORB_EXPANDED_SNIPPET)
    editor.set_trajectory_rows(
        "Air Trajectory",
        [
            (2020, 1, 1, 0, 0, 0),
            (2020, 1, 1, 1, 2, 3),
        ],
    )
    updated = editor.refresh()

    assert updated.trajectories[0].trajectory_rows == [
        (2020, 1, 1, 0, 0, 0),
        (2020, 1, 1, 1, 2, 3),
    ]

    rendered = editor.to_text()
    assert "\t\t2020 1 1 0 0 0\n" in rendered
    assert "\t\t2020 1 1 1 2 3\n" in rendered
    assert dump_orb_text(parse_orb_text(rendered)) == rendered


def test_orb_editor_authors_airroute_platform() -> None:
    editor = edit_orb_scenario_text(ORB_SNIPPET)
    editor.add_airroute_platform(
        "Route One",
        start_state=(2004, 2, 1, 0, 0, 0, 2004, 2, 2, 0, 0, 0),
        waypoints=[
            (33.9, -118.4, 1, 0, 0.2),
            (35.0, -97.0, 1, 0, 0.3),
        ],
        color="Cyan",
        smooth=True,
    )
    updated = editor.refresh()

    platform = next(item for item in updated.platforms if item.name == "Route One")
    assert platform.platform_type == "AIRROUTE"
    assert platform.properties["PLAT"] == "Earth"
    assert platform.properties["WAYPOINT_TYPE"] == "BY_SPEED"
    assert platform.properties["SMOOTH"] is True
    assert platform.repeated["WAYPOINT"][1] == (35.0, -97.0, 1, 0, 0.3)


def test_orb_editor_authors_trajectory_and_world_view() -> None:
    editor = edit_orb_scenario_text(ORB_SNIPPET)
    editor.create_trajectory(
        "Route One Trajectory",
        coordinate_system="ECR",
        platform_name="Route One",
        trajectory_choice=("RELATIVE", "FORWARD", 1200),
        rows=[
            (2024, 1, 1, 0, 0, 0),
            (2024, 1, 1, 0, 5, 0),
        ],
        properties={"REFRESH_CHOICE": "GENERATE"},
    )
    editor.add_world_view(
        "Route One View",
        observer="Route One",
        coordinate_system="ECR",
        icon_list=["Route One", "END_OF_INPUT"],
        label_list=["Route One", "END_OF_INPUT"],
        viewangles=(-10, 70),
    )
    updated = editor.refresh()

    trajectory = next(item for item in updated.trajectories if item.name == "Route One Trajectory")
    assert trajectory.properties["CS"] == "ECR"
    assert trajectory.trajectory_rows[0] == (2024, 1, 1, 0, 0, 0)

    view = next(item for item in updated.views if item.name == "Route One View")
    assert view.observer == "Route One"
    assert view.coordinate_system == "ECR"
    assert view.lists["ICON_LIST"] == ["Route One", "END_OF_INPUT"]
    assert view.lists["LABEL_LIST"] == ["Route One", "END_OF_INPUT"]
    assert view.properties["VIEWANGLES"] == (-10, 70)


def test_orb_editor_clones_named_block() -> None:
    editor = edit_orb_scenario_text(ORB_EXPANDED_SNIPPET)
    editor.clone_named_block("PLATFORM", "Air", "Air Copy")
    updated = editor.refresh()

    clone = next(item for item in updated.platforms if item.name == "Air Copy")
    assert clone.platform_type == "AIRROUTE"
    assert clone.repeated["WAYPOINT"] == updated.platforms[0].repeated["WAYPOINT"]

    rendered = editor.to_text()
    assert 'DEFINE PLATFORM AIRROUTE "Air Copy"' in rendered
    assert dump_orb_text(parse_orb_text(rendered)) == rendered


def test_orb_authoring_helpers_add_fixed_site_view_and_grid() -> None:
    editor = edit_orb_scenario_text(ORB_SNIPPET)
    add_fixed_site(
        editor,
        FixedSiteSpec(
            name="Site Alpha",
            latitude_deg=35.0,
            longitude_deg=-97.0,
            color="Orange",
        ),
    )
    add_world_view_from_spec(
        editor,
        WorldViewSpec(
            name="Site Alpha View",
            observer="Site Alpha",
            coordinate_system="ECR",
            icon_list=["Site Alpha", "END_OF_INPUT"],
            label_list=["Site Alpha", "END_OF_INPUT"],
            viewangles=(-20, 50),
        ),
    )
    add_contour_grid(
        editor,
        ContourGridSpec(
            name="Site Alpha Grid",
            dimension=(8, 8, 10),
            altitude=0.0,
            domain=(0, 3600),
            domdlt=60.0,
            output_format="TEXTUREMAP_FORMAT",
            contour_enabled=True,
        ),
    )
    updated = editor.refresh()

    site = next(item for item in updated.platforms if item.name == "Site Alpha")
    assert site.platform_type == "ECR_FIXED"
    assert site.state == (35.0, -97.0, 0.0)
    assert site.properties["PLAT"] == "Earth"
    assert site.properties["COLOR"] == "Orange"

    view = next(item for item in updated.views if item.name == "Site Alpha View")
    assert view.observer == "Site Alpha"
    assert view.lists["ICON_LIST"] == ["Site Alpha", "END_OF_INPUT"]
    assert view.properties["VIEWANGLES"] == (-20, 50)

    grid = next(item for item in updated.grids if item.name == "Site Alpha Grid")
    assert grid.grid_type == "CONTOUR"
    assert grid.properties["DIMENSION"] == (8, 8, 10)
    assert grid.properties["OUTPUT_FORMAT"] == "TEXTUREMAP_FORMAT"
    assert grid.properties["CONTOUR_ENABLED"] is True

    rendered = editor.to_text()
    assert 'DEFINE PLATFORM ECR_FIXED "Site Alpha"' in rendered
    assert 'DEFINE VIEW WORLD "Site Alpha View" "Site Alpha" ECR' in rendered
    assert 'DEFINE GRID CONTOUR "Site Alpha Grid"' in rendered
    assert dump_orb_text(parse_orb_text(rendered)) == rendered


def test_orb_authoring_helpers_add_coordinate_system_observer_and_site_bundle() -> None:
    editor = edit_orb_scenario_text(ORB_SNIPPET)
    add_coordinate_system(
        editor,
        CoordinateSystemSpec(
            name="Site Alpha CS",
            track=("Z", "LONLAT", 0, 90),
            align=("RESULTANT", "Y", "LONLAT", 0, 0),
            sweep=("Z", "NOSWEEP"),
            origin=(".Host Platform", ".Host Platform"),
        ),
    )
    add_observer_platform(
        editor,
        ObserverPlatformSpec(
            name="Site Alpha Observer",
            state=(35.0, -97.0, 1000.0),
            coordinate_system="Site Alpha CS",
        ),
    )
    add_site_bundle(
        editor,
        SiteBundleSpec(
            site=FixedSiteSpec(name="Bundle Site", latitude_deg=34.0, longitude_deg=-96.0),
            coordinate_system=CoordinateSystemSpec(
                name="Bundle CS",
                track=("Z", "LONLAT", 0, 90),
                align=("RESULTANT", "Y", "LONLAT", 0, 0),
                sweep=("Z", "NOSWEEP"),
                origin=(".Host Platform", ".Host Platform"),
            ),
            observer=ObserverPlatformSpec(
                name="Bundle Observer",
                state=(34.0, -96.0, 500.0),
                coordinate_system="Bundle CS",
            ),
            view=WorldViewSpec(
                name="Bundle View",
                observer="Bundle Observer",
                coordinate_system="Bundle CS",
                icon_list=["Bundle Site", "END_OF_INPUT"],
                viewangles=(-15, 45),
            ),
            grid=ContourGridSpec(
                name="Bundle Grid",
                dimension=(4, 4, 4),
                altitude=0.0,
                domain=(0, 600),
                domdlt=30.0,
            ),
        ),
    )
    updated = editor.refresh()

    assert any(cs.name == "Site Alpha CS" for cs in updated.coordinate_systems)
    observer = next(item for item in updated.platforms if item.name == "Site Alpha Observer")
    assert observer.properties["CS"] == "Site Alpha CS"
    assert observer.properties["SHAPE"] == "VIEW_ONLY"

    assert any(site.name == "Bundle Site" for site in updated.platforms)
    bundle_view = next(item for item in updated.views if item.name == "Bundle View")
    assert bundle_view.observer == "Bundle Observer"
    assert bundle_view.coordinate_system == "Bundle CS"
    bundle_grid = next(item for item in updated.grids if item.name == "Bundle Grid")
    assert bundle_grid.properties["DIMENSION"] == (4, 4, 4)

    rendered = editor.to_text()
    assert 'DEFINE CS CSBASIS "Site Alpha CS"' in rendered
    assert 'DEFINE PLATFORM ECR_FIXED "Site Alpha Observer"' in rendered
    assert 'DEFINE VIEW WORLD "Bundle View" "Bundle Observer" "Bundle CS"' in rendered
    assert dump_orb_text(parse_orb_text(rendered)) == rendered


def test_orb_package_build_write_and_load_round_trip(tmp_path: Path) -> None:
    spec = OrbPackageSpec(
        site_bundle=SiteBundleSpec(
            site=FixedSiteSpec(name="Pkg Site", latitude_deg=36.0, longitude_deg=-98.0, color="Blue"),
            coordinate_system=CoordinateSystemSpec(
                name="Pkg CS",
                track=("Z", "LONLAT", 0, 90),
                align=("RESULTANT", "Y", "LONLAT", 0, 0),
                sweep=("Z", "NOSWEEP"),
                origin=(".Host Platform", ".Host Platform"),
            ),
            observer=ObserverPlatformSpec(
                name="Pkg Observer",
                state=(36.0, -98.0, 900.0),
                coordinate_system="Pkg CS",
            ),
            view=WorldViewSpec(
                name="Pkg View",
                observer="Pkg Observer",
                coordinate_system="Pkg CS",
                icon_list=["Pkg Site", "END_OF_INPUT"],
                label_list=["Pkg Site", "END_OF_INPUT"],
                viewangles=(-25, 55),
            ),
            grid=ContourGridSpec(
                name="Pkg Grid",
                dimension=(6, 6, 6),
                altitude=0.0,
                domain=(0, 3600),
                domdlt=120.0,
                contour_enabled=False,
            ),
        ),
        extra_fixed_sites=[
            FixedSiteSpec(name="Pkg Site 2", latitude_deg=37.0, longitude_deg=-99.0),
        ],
    )

    editor = build_orb_package(spec)
    text = editor.to_text()
    assert "SOAP_SCENARIO_FILE" in text
    assert 'DEFINE PLATFORM ECR_FIXED "Pkg Site"' in text
    assert 'DEFINE GRID CONTOUR "Pkg Grid"' in text

    output_path = write_orb_package(spec, tmp_path / "pkg.orb")
    assert output_path.read_text(encoding="utf-8") == text

    scenario = load_orb_package(output_path)
    assert scenario.revision == 56
    assert scenario.file_type == "SOAP_SCENARIO_FILE"
    assert any(platform.name == "Pkg Site" for platform in scenario.platforms)
    assert any(platform.name == "Pkg Site 2" for platform in scenario.platforms)
    assert any(view.name == "Pkg View" for view in scenario.views)
    assert any(grid.name == "Pkg Grid" for grid in scenario.grids)
    assert scenario.document.to_text() == text
    assert dump_orb_text(parse_orb_text(text)) == text


def test_orb_package_supports_analysis_templates_stabilization_and_display_defaults(tmp_path: Path) -> None:
    spec = OrbPackageSpec(
        site_bundle=SiteBundleSpec(
            site=FixedSiteSpec(name="Template Site", latitude_deg=35.0, longitude_deg=-97.0),
            coordinate_system=CoordinateSystemSpec(
                name="Template CS",
                track=("Z", "LONLAT", 0, 90),
                align=("RESULTANT", "Y", "LONLAT", 0, 0),
                sweep=("Z", "NOSWEEP"),
                origin=(".Host Platform", ".Host Platform"),
            ),
            observer=ObserverPlatformSpec(
                name="Template Observer",
                state=(35.0, -97.0, 1000.0),
                coordinate_system="Template CS",
            ),
            view=WorldViewSpec(
                name="Template View",
                observer="Template Observer",
                coordinate_system="Template CS",
                icon_list=["Template Site", "END_OF_INPUT"],
            ),
        ),
        display_defaults=DisplayDefaultsSpec(
            map_color="Black",
            world_pcolor="White",
            data_pcolor="White",
            text_pcolor="White",
            world_scolor="Gray",
            icon_scale=1.5,
            line_thickness=2.0,
            map_line_thickness=2.0,
            limb=True,
            worldmap=False,
            lighting=True,
        ),
        analyses=[
            AnalysisSpec(
                name="Template Derived",
                variable=("CONSTANT", 1),
                variable_details={
                    "DISTANCEU": ("KILOMETERS", 1.0),
                    "TIMEU": ("SECONDS", 0.0),
                    "COMMENT": "Template derived variable",
                },
                bounds=(0, 10),
            )
        ],
        stabilizations=["Inertial"],
    )

    editor = build_orb_package(spec)
    output_path = write_orb_package(spec, tmp_path / "template.orb")
    scenario = load_orb_package(output_path)

    assert scenario.config is not None
    assert scenario.config.properties["MAP_COLOR"] == "Black"
    assert scenario.config.properties["ICON_SCALE"] == 1.5
    assert scenario.config.properties["LIMB"] is True
    assert scenario.config.properties["WORLDMAP"] is False
    assert scenario.config.properties["LIGHTING"] is True

    analysis = next(item for item in scenario.analyses if item.name == "Template Derived")
    assert analysis.properties["VARIABLE"] == ("CONSTANT", 1)
    assert analysis.properties["BOUNDS"] == (0, 10)
    assert analysis.variable_details["COMMENT"] == "Template derived variable"

    stabilization = next(item for item in scenario.stabilizations if item.name == "Inertial")
    assert isinstance(stabilization, OrbStabilization)

    rendered = editor.to_text()
    assert 'DEFINE ANALYSIS "Template Derived"' in rendered
    assert 'DEFINE STABILIZATION "Inertial"' in rendered
    assert dump_orb_text(parse_orb_text(rendered)) == rendered


def test_orb_package_analysis_template_normalization_round_trip(tmp_path: Path) -> None:
    template = AnalysisTemplateSpec(
        name="Normalized Derived",
        derived_variable=DerivedVariableSpec(
            value=("CONSTANT", 1),
            distanceu=("KILOMETERS", 1.0),
            timeu=("SECONDS", 0.0),
            comment="Normalized derived variable",
            extra_details={"SOURCE": "Template"},
        ),
        bounds=(0, 10),
        color="Blue",
        marker="o",
        link=True,
        cue=True,
    )

    analysis = normalize_analysis_template(template)
    assert analysis.name == "Normalized Derived"
    assert analysis.variable == ("CONSTANT", 1)
    assert analysis.variable_details["DISTANCEU"] == ("KILOMETERS", 1.0)
    assert analysis.variable_details["TIMEU"] == ("SECONDS", 0.0)
    assert analysis.variable_details["COMMENT"] == "Normalized derived variable"
    assert analysis.variable_details["SOURCE"] == "Template"

    spec = OrbPackageSpec(analysis_templates=[template])
    editor = build_orb_package(spec)
    output_path = write_orb_package(spec, tmp_path / "normalized.orb")
    scenario = load_orb_package(output_path)

    assert output_path.read_text(encoding="utf-8") == editor.to_text()
    analysis_block = next(item for item in scenario.analyses if item.name == "Normalized Derived")
    assert analysis_block.properties["VARIABLE"] == ("CONSTANT", 1)
    assert analysis_block.properties["BOUNDS"] == (0, 10)
    assert analysis_block.properties["COLOR"] == "Blue"
    assert analysis_block.variable_details["COMMENT"] == "Normalized derived variable"
    assert dump_orb_text(parse_orb_text(editor.to_text())) == editor.to_text()
