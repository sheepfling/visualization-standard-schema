import math
from datetime import datetime
from pathlib import Path

import pytest

from vss import dump_message
from vss import dump_message_json
from vss import dump_scene
from vss import dump_scene_json
from vss import load_scene_file
from vss import write_message_file
from vss import write_scene_file
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
from vss.convert.czml import parse_czml_to_scene
from vss.models import (
    EntityCategory,
    EntityUpsertMessage,
    SceneDocument,
    SceneEntity,
    Style,
    VssScene,
    Wgs84Position,
)

EXAMPLE_PATH = Path("examples/cesium/air-track.json")
SCENE_EXAMPLE_PATH = Path("examples/scenes/air-pair.scene.json")
MIXED_SCENE_EXAMPLE_PATH = Path("examples/scenes/mixed-ops.scene.json")
CORRIDOR_SCENE_EXAMPLE_PATH = Path("examples/scenes/corridor-demo.scene.json")
ELLIPSE_CIRCLE_SCENE_EXAMPLE_PATH = Path("examples/scenes/ellipse-circle-demo.scene.json")
RANGE_RING_SCENE_EXAMPLE_PATH = Path("examples/scenes/range-ring-demo.scene.json")
BEARING_FAN_SCENE_EXAMPLE_PATH = Path("examples/scenes/bearing-fan-demo.scene.json")
FAN_SCENE_EXAMPLE_PATH = Path("examples/scenes/fan-demo.scene.json")
CUSTOM_PATTERN_SENSOR_SCENE_EXAMPLE_PATH = Path("examples/scenes/custom-pattern-sensor-demo.scene.json")
WALL_SCENE_EXAMPLE_PATH = Path("examples/scenes/wall-demo.scene.json")
BOX_SCENE_EXAMPLE_PATH = Path("examples/scenes/box-demo.scene.json")
CYLINDER_SCENE_EXAMPLE_PATH = Path("examples/scenes/cylinder-demo.scene.json")
CONE_SCENE_EXAMPLE_PATH = Path("examples/scenes/cone-demo.scene.json")
FRUSTUM_SCENE_EXAMPLE_PATH = Path("examples/scenes/frustum-demo.scene.json")
UNCERTAINTY_COVARIANCE_SCENE_EXAMPLE_PATH = Path("examples/scenes/uncertainty-covariance-demo.scene.json")
RECTANGULAR_SENSOR_SCENE_EXAMPLE_PATH = Path("examples/scenes/rectangular-sensor-demo.scene.json")
SECTOR2D_SCENE_EXAMPLE_PATH = Path("examples/scenes/sector2d-demo.scene.json")
SECTOR_VOLUME_SCENE_EXAMPLE_PATH = Path("examples/scenes/sectorVolume-demo.scene.json")
HEMISPHERE_SCENE_EXAMPLE_PATH = Path("examples/scenes/hemisphere-demo.scene.json")
SPHERICAL_CAP_SCENE_EXAMPLE_PATH = Path("examples/scenes/sphericalcap-demo.scene.json")
KEYHOLE_SCENE_EXAMPLE_PATH = Path("examples/scenes/keyhole-demo.scene.json")
POLYLINE_VOLUME_SCENE_EXAMPLE_PATH = Path("examples/scenes/polyline-volume-demo.scene.json")
PLANE_SCENE_EXAMPLE_PATH = Path("examples/scenes/plane-demo.scene.json")
TILESET_SCENE_EXAMPLE_PATH = Path("examples/scenes/tileset-demo.scene.json")
VIEW_SCENE_EXAMPLE_PATH = Path("examples/scenes/view-demo.scene.json")
VECTOR_SCENE_EXAMPLE_PATH = Path("examples/scenes/vector-demo.scene.json")
VELOCITY_VECTOR_SCENE_EXAMPLE_PATH = Path("examples/scenes/velocity-vector-demo.scene.json")
ACCELERATION_VECTOR_SCENE_EXAMPLE_PATH = Path("examples/scenes/acceleration-vector-demo.scene.json")
LINE_OF_SIGHT_SCENE_EXAMPLE_PATH = Path("examples/scenes/line-of-sight-demo.scene.json")
AXES_SCENE_EXAMPLE_PATH = Path("examples/scenes/axes-demo.scene.json")
RELATIVE_INTERCEPT_SCENE_EXAMPLE_PATH = Path("examples/scenes/relative-intercept-demo.scene.json")
ELLIPSOID_SPHERE_SCENE_EXAMPLE_PATH = Path("examples/scenes/ellipsoid-sphere-demo.scene.json")
PARTICLE_SYSTEM_SCENE_EXAMPLE_PATH = Path("examples/scenes/particle-system-demo.scene.json")
VOXEL_SCENE_EXAMPLE_PATH = Path("examples/scenes/voxel-demo.scene.json")

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

def test_scene_example_loads() -> None:
    scene = load_scene_file(SCENE_EXAMPLE_PATH)
    assert scene.document.id == "air-pair-demo"
    assert len(scene.views) == 2
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

def test_uncertainty_covariance_scene_example_loads() -> None:
    scene = load_scene_file(UNCERTAINTY_COVARIANCE_SCENE_EXAMPLE_PATH)
    assert scene.document.id == "uncertainty-covariance-demo"
    assert len(scene.objects) == 2
    assert len(scene.overlays) == 2
    ellipsoid, ellipse = scene.overlays
    assert ellipsoid.geometryType == "uncertaintyEllipsoid"
    assert ellipsoid.uncertaintyEllipsoid is not None
    assert ellipsoid.uncertaintyEllipsoid.radiiMeters == (2200.0, 1200.0, 800.0)
    assert ellipse.geometryType == "covarianceEllipse"
    assert ellipse.covarianceEllipse is not None
    assert ellipse.covarianceEllipse.semiMajorAxisMeters == 6000.0
    assert ellipse.covarianceEllipse.rotationDegrees == 30.0

def test_range_ring_scene_example_loads() -> None:
    scene = load_scene_file(RANGE_RING_SCENE_EXAMPLE_PATH)
    assert scene.document.id == "range-ring-demo"
    assert len(scene.objects) == 1
    assert len(scene.overlays) == 1
    ring = scene.overlays[0]
    assert ring.geometryType == "rangeRing"
    assert ring.rangeRing is not None
    assert ring.rangeRing.radiusMeters == 25000.0
    assert ring.rangeRing.outlineWidthPx == 2.0

def test_bearing_fan_scene_example_loads() -> None:
    scene = load_scene_file(BEARING_FAN_SCENE_EXAMPLE_PATH)
    assert scene.document.id == "bearing-fan-demo"
    assert len(scene.objects) == 1
    assert len(scene.overlays) == 1
    fan = scene.overlays[0]
    assert fan.geometryType == "bearingFan"
    assert fan.bearingFan is not None
    assert fan.bearingFan.outerRadiusMeters == 46000.0
    assert fan.bearingFan.azimuthStartDegrees == -12.0
    assert fan.orientation is not None
    assert fan.orientation.headingDeg == 15.0

def test_fan_scene_example_loads() -> None:
    scene = load_scene_file(FAN_SCENE_EXAMPLE_PATH)
    assert scene.document.id == "fan-demo"
    assert len(scene.objects) == 1
    assert len(scene.overlays) == 1
    fan = scene.overlays[0]
    assert fan.geometryType == "fan"
    assert fan.fan is not None
    assert fan.fan.outerRadiusMeters == 38000.0
    assert fan.fan.azimuthStartDegrees == -20.0
    assert fan.orientation is not None
    assert fan.orientation.headingDeg == 5.0

def test_custom_pattern_sensor_scene_example_loads() -> None:
    scene = load_scene_file(CUSTOM_PATTERN_SENSOR_SCENE_EXAMPLE_PATH)
    assert scene.document.id == "custom-pattern-sensor-demo"
    assert len(scene.objects) == 1
    assert len(scene.overlays) == 1
    sensor = scene.overlays[0]
    assert sensor.geometryType == "customPatternSensor"
    assert sensor.customPatternSensor is not None
    assert sensor.customPatternSensor.outerRadiusMeters == 70000.0
    assert sensor.customPatternSensor.patternAzimuthElevationDegrees[2] == (0.0, 55.0)
    assert sensor.orientation is not None
    assert sensor.orientation.headingDeg == 155.0

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

def test_cylinder_scene_example_loads() -> None:
    scene = load_scene_file(CYLINDER_SCENE_EXAMPLE_PATH)
    assert scene.document.id == "cylinder-demo"
    assert len(scene.objects) == 1
    assert len(scene.overlays) == 1
    cylinder = scene.overlays[0]
    assert cylinder.geometryType == "cylinder"
    assert cylinder.cylinder is not None
    assert cylinder.cylinder.lengthMeters == 6000.0
    assert cylinder.cylinder.topRadiusMeters == 1500.0
    assert cylinder.cylinder.bottomRadiusMeters == 2500.0

def test_cone_scene_example_loads() -> None:
    scene = load_scene_file(CONE_SCENE_EXAMPLE_PATH)
    assert scene.document.id == "cone-demo"
    assert len(scene.objects) == 1
    assert len(scene.overlays) == 1
    cone = scene.overlays[0]
    assert cone.geometryType == "cone"
    assert cone.orientation is not None
    assert cone.orientation.headingDeg == 35.0
    assert cone.cone is not None
    assert cone.cone.radiusMeters == 14000.0
    assert cone.cone.outerHalfAngleDegrees == 18.0

def test_conic_sensor_scene_example_loads() -> None:
    scene = load_scene_file(Path("examples/scenes/conic-sensor-demo.scene.json"))
    assert scene.document.id == "conic-sensor-demo"
    assert len(scene.objects) == 1
    assert len(scene.overlays) == 1
    sensor = scene.overlays[0]
    assert sensor.geometryType == "conicSensor"
    assert sensor.conicSensor is not None
    assert sensor.conicSensor.radiusMeters == 14000.0
    assert sensor.conicSensor.outerHalfAngleDegrees == 18.0

def test_rectangular_sensor_scene_example_loads() -> None:
    scene = load_scene_file(RECTANGULAR_SENSOR_SCENE_EXAMPLE_PATH)
    assert scene.document.id == "rectangular-sensor-demo"
    assert len(scene.objects) == 1
    assert len(scene.overlays) == 1
    sensor = scene.overlays[0]
    assert sensor.geometryType == "rectangularSensor"
    assert sensor.rectangularSensor is not None
    assert sensor.rectangularSensor.radiusMeters == 22000.0
    assert sensor.rectangularSensor.xHalfAngleDegrees == 16.0
    assert sensor.rectangularSensor.yHalfAngleDegrees == 28.0

def test_sector2d_scene_example_loads() -> None:
    scene = load_scene_file(SECTOR2D_SCENE_EXAMPLE_PATH)
    assert scene.document.id == "sector2d-demo"
    assert len(scene.objects) == 1
    assert len(scene.overlays) == 1
    sector = scene.overlays[0]
    assert sector.geometryType == "sector2d"
    assert sector.sector2d is not None
    assert sector.sector2d.outerRadiusMeters == 14000.0
    assert sector.sector2d.azimuthStartDegrees == 25.0
    assert sector.sector2d.azimuthStopDegrees == 105.0

def test_sector_volume_scene_example_loads() -> None:
    scene = load_scene_file(SECTOR_VOLUME_SCENE_EXAMPLE_PATH)
    assert scene.document.id == "sectorVolume-demo"
    assert len(scene.objects) == 1
    assert len(scene.overlays) == 1
    volume = scene.overlays[0]
    assert volume.geometryType == "sectorVolume"
    assert volume.sectorVolume is not None
    assert volume.sectorVolume.outerRadiusMeters == 18000.0
    assert volume.sectorVolume.azimuthStartDegrees == 30.0
    assert volume.sectorVolume.azimuthStopDegrees == 120.0

def test_hemisphere_scene_example_loads() -> None:
    scene = load_scene_file(HEMISPHERE_SCENE_EXAMPLE_PATH)
    assert scene.document.id == "hemisphere-demo"
    assert len(scene.objects) == 1
    assert len(scene.overlays) == 1
    hemi = scene.overlays[0]
    assert hemi.geometryType == "hemisphere"
    assert hemi.hemisphere is not None
    assert hemi.hemisphere.radiusMeters == 9000.0

def test_spherical_cap_scene_example_loads() -> None:
    scene = load_scene_file(SPHERICAL_CAP_SCENE_EXAMPLE_PATH)
    assert scene.document.id == "sphericalcap-demo"
    assert len(scene.objects) == 1
    assert len(scene.overlays) == 1
    cap = scene.overlays[0]
    assert cap.geometryType == "sphericalCap"
    assert cap.sphericalCap is not None
    assert cap.sphericalCap.radiusMeters == 11000.0
    assert cap.sphericalCap.portion == "upper"

def test_keyhole_scene_example_loads() -> None:
    scene = load_scene_file(KEYHOLE_SCENE_EXAMPLE_PATH)
    assert scene.document.id == "keyhole-demo"
    assert len(scene.objects) == 1
    assert len(scene.overlays) == 1
    keyhole = scene.overlays[0]
    assert keyhole.geometryType == "keyhole"
    assert keyhole.keyhole is not None
    assert keyhole.keyhole.innerRadiusMeters == 3500.0
    assert keyhole.keyhole.outerRadiusMeters == 12500.0
    assert keyhole.keyhole.azimuthStartDegrees == 45.0
    assert keyhole.keyhole.azimuthStopDegrees == 135.0

def test_frustum_scene_example_loads() -> None:
    scene = load_scene_file(FRUSTUM_SCENE_EXAMPLE_PATH)
    assert scene.document.id == "frustum-demo"
    assert len(scene.objects) == 1
    assert len(scene.overlays) == 1
    frustum = scene.overlays[0]
    assert frustum.geometryType == "frustum"
    assert frustum.frustum is not None
    assert frustum.frustum.nearMeters == 2000.0
    assert frustum.frustum.farMeters == 12000.0
    assert frustum.frustum.horizontalFovDegrees == 40.0

def test_polyline_volume_scene_example_loads() -> None:
    scene = load_scene_file(POLYLINE_VOLUME_SCENE_EXAMPLE_PATH)
    assert scene.document.id == "polyline-volume-demo"
    assert len(scene.objects) == 1
    assert len(scene.overlays) == 1
    volume = scene.overlays[0]
    assert volume.geometryType == "polylineVolume"
    assert volume.polylineVolume is not None
    assert len(volume.polylineVolume.positions) == 3
    assert len(volume.polylineVolume.shapePositions) == 4
    assert volume.polylineVolume.cornerType == "mitered"

def test_plane_scene_example_loads() -> None:
    scene = load_scene_file(PLANE_SCENE_EXAMPLE_PATH)
    assert scene.document.id == "plane-demo"
    assert len(scene.objects) == 1
    assert len(scene.overlays) == 1
    plane = scene.overlays[0]
    assert plane.geometryType == "plane"
    assert plane.plane is not None
    assert plane.plane.normal == (0.0, 0.0, 1.0)
    assert plane.plane.widthMeters == 45000.0
    assert plane.plane.heightMeters == 28000.0

def test_tileset_scene_example_loads() -> None:
    scene = load_scene_file(TILESET_SCENE_EXAMPLE_PATH)
    assert scene.document.id == "tileset-demo"
    assert len(scene.objects) == 1
    assert len(scene.overlays) == 1
    tileset = scene.overlays[0]
    assert tileset.geometryType == "tileset"
    assert tileset.tileset is not None
    assert tileset.tileset.uri == "https://example.org/tilesets/demo/tileset.json"

def test_vector_scene_example_loads() -> None:
    scene = load_scene_file(VECTOR_SCENE_EXAMPLE_PATH)
    assert scene.document.id == "vector-demo"
    assert len(scene.objects) == 1
    assert len(scene.vectors) == 1
    vector = scene.vectors[0]
    assert vector.id == "vector-001"
    assert vector.startPosition.longitudeDeg == -97.74
    assert vector.endPosition.altitudeM == 11000.0
    assert vector.widthPx == 4.0

def test_velocity_vector_scene_example_loads() -> None:
    scene = load_scene_file(VELOCITY_VECTOR_SCENE_EXAMPLE_PATH)
    assert scene.document.id == "velocity-vector-demo"
    assert len(scene.objects) == 1
    assert len(scene.velocityVectors) == 1
    velocity_vector = scene.velocityVectors[0]
    assert velocity_vector.id == "velocity-vector-001"
    assert velocity_vector.startPosition.longitudeDeg == -97.72
    assert velocity_vector.endPosition.altitudeM == 9500.0
    assert velocity_vector.widthPx == 3.5

def test_acceleration_vector_scene_example_loads() -> None:
    scene = load_scene_file(ACCELERATION_VECTOR_SCENE_EXAMPLE_PATH)
    assert scene.document.id == "acceleration-vector-demo"
    assert len(scene.objects) == 1
    assert len(scene.accelerationVectors) == 1
    acceleration_vector = scene.accelerationVectors[0]
    assert acceleration_vector.id == "acceleration-vector-001"
    assert acceleration_vector.startPosition.longitudeDeg == -97.70
    assert acceleration_vector.endPosition.altitudeM == 8800.0
    assert acceleration_vector.widthPx == 3.0

def test_line_of_sight_scene_example_loads() -> None:
    scene = load_scene_file(LINE_OF_SIGHT_SCENE_EXAMPLE_PATH)
    assert scene.document.id == "line-of-sight-demo"
    assert len(scene.objects) == 1
    assert len(scene.lineOfSights) == 1
    line_of_sight = scene.lineOfSights[0]
    assert line_of_sight.id == "los-001"
    assert line_of_sight.startPosition.longitudeDeg == -97.74
    assert line_of_sight.endPosition.altitudeM == 1000.0
    assert line_of_sight.widthPx == 2.5

def test_axes_scene_example_loads() -> None:
    scene = load_scene_file(AXES_SCENE_EXAMPLE_PATH)
    assert scene.document.id == "axes-demo"
    assert len(scene.objects) == 2
    assert len(scene.bodyAxes) == 1
    assert len(scene.principalAxes) == 1
    body_axes = scene.bodyAxes[0]
    assert body_axes.id == "body-axes-001"
    assert body_axes.axisLengthsMeters == (4500.0, 3000.0, 1800.0)
    assert body_axes.orientation is not None
    assert body_axes.orientation.headingDeg == 42.0
    principal_axes = scene.principalAxes[0]
    assert principal_axes.id == "principal-axes-001"
    assert principal_axes.axisLengthsMeters == (3800.0, 2200.0, 2600.0)

def test_relative_intercept_scene_example_loads() -> None:
    scene = load_scene_file(RELATIVE_INTERCEPT_SCENE_EXAMPLE_PATH)
    assert scene.document.id == "relative-intercept-demo"
    assert len(scene.objects) == 2
    assert len(scene.relativeLines) == 1
    assert len(scene.interceptLines) == 1
    relative_line = scene.relativeLines[0]
    assert relative_line.id == "relative-line-001"
    assert relative_line.startPosition.longitudeDeg == -97.74
    assert relative_line.endPosition.altitudeM == 9400.0
    intercept_line = scene.interceptLines[0]
    assert intercept_line.id == "intercept-line-001"
    assert intercept_line.startPosition.latitudeDeg == 30.29
    assert intercept_line.endPosition.longitudeDeg == -97.66

def test_view_scene_example_loads() -> None:
    scene = load_scene_file(VIEW_SCENE_EXAMPLE_PATH)
    assert scene.document.id == "view-demo"
    assert len(scene.objects) == 2
    assert len(scene.views) == 1
    assert len(scene.cameraViews) == 1
    view = scene.views[0]
    assert view.id == "aircraft-overview"
    assert view.target == "aircraft-001"
    assert view.position is not None
    assert view.position.longitudeDeg == -97.7431
    assert view.position.latitudeDeg == 30.2672
    camera_view = scene.cameraViews[0]
    assert camera_view.id == "aircraft-camera-view"
    assert camera_view.rangeMeters == 22000.0
    assert camera_view.orientation is not None
    assert camera_view.orientation.pitchDeg == -30.0

def test_ellipsoid_sphere_scene_example_loads() -> None:
    scene = load_scene_file(ELLIPSOID_SPHERE_SCENE_EXAMPLE_PATH)
    assert scene.document.id == "ellipsoid-sphere-demo"
    assert len(scene.objects) == 2
    assert len(scene.overlays) == 2
    ellipsoid, sphere = scene.overlays
    assert ellipsoid.geometryType == "ellipsoid"
    assert ellipsoid.ellipsoid is not None
    assert ellipsoid.ellipsoid.radiiMeters == (8000.0, 12000.0, 6000.0)
    assert sphere.geometryType == "sphere"
    assert sphere.sphere is not None
    assert sphere.sphere.radiusMeters == 10000.0

def test_scene_example_compiles_to_multi_entity_czml() -> None:
    scene = load_scene_file(SCENE_EXAMPLE_PATH)
    packets = compile_cesium_scene(scene)
    assert packets[0]["name"] == "Air Pair Demo"
    assert len(packets) == 3
    assert packets[1]["id"] == "aircraft-001"
    assert packets[2]["id"] == "aircraft-002"

def test_scene_analysis_and_presentation_are_preserved_on_czml_document() -> None:
    scene = VssScene(
        schemaVersion="1.0.0-scene",
        document=SceneDocument(id="meta-demo", name="Meta Demo"),
        objects=[
            SceneEntity(
                id="aircraft-001",
                name="Aircraft 001",
                category=EntityCategory.AIR,
                position=Wgs84Position(longitudeDeg=-97.74, latitudeDeg=30.27, altitudeM=1000.0),
                style=Style(label="Aircraft 001"),
            )
        ],
        analysis={"results": [{"id": "analysis-1", "value": 42}]},
        presentation={"slides": [{"id": "slide-1", "title": "Overview"}]},
    )
    packets = compile_cesium_scene(scene)
    assert packets[0]["properties"]["analysis"] == {"results": [{"id": "analysis-1", "value": 42}]}
    assert packets[0]["properties"]["presentation"] == {"slides": [{"id": "slide-1", "title": "Overview"}]}
    html = render_cesium_viewer_html(
        czml_path="./meta-demo.czml.json",
        title="Meta Demo",
        scene_metadata={"analysis": scene.analysis, "presentation": scene.presentation},
    )
    assert "Scene metadata" in html
    assert '"analysis": {' in html
    assert '"presentation": {' in html

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

def test_uncertainty_covariance_scene_compiles_to_czml_effect_graphics() -> None:
    scene = load_scene_file(UNCERTAINTY_COVARIANCE_SCENE_EXAMPLE_PATH)
    packets = compile_cesium_scene(scene)
    assert packets[0]["name"] == "Uncertainty Covariance Demo"
    assert len(packets) == 3
    assert packets[1]["id"] == "uncertainty-ellipsoid-track-42"
    assert packets[1]["ellipsoid"]["radii"]["cartesian"] == [2200.0, 1200.0, 800.0]
    assert packets[1]["properties"]["shapeType"] == "uncertaintyEllipsoid"
    assert packets[1]["properties"]["uncertaintyEllipsoid"]["slicePartitions"] == 24
    assert packets[2]["id"] == "covariance-ellipse-track-42"
    assert packets[2]["ellipse"]["semiMajorAxis"] == 6000.0
    assert packets[2]["ellipse"]["semiMinorAxis"] == 2200.0
    assert packets[2]["properties"]["shapeType"] == "covarianceEllipse"
    assert packets[2]["properties"]["covarianceEllipse"]["rotationDegrees"] == 30.0

def test_particle_system_scene_compiles_to_czml_particle_system_graphics() -> None:
    scene = load_scene_file(PARTICLE_SYSTEM_SCENE_EXAMPLE_PATH)
    packets = compile_cesium_scene(scene)
    assert packets[0]["name"] == "Particle System Demo"
    assert len(packets) == 2
    assert packets[1]["id"] == "particle-system-001"
    assert packets[1]["properties"]["shapeType"] == "particleSystem"
    assert packets[1]["particleSystem"]["image"] == "smokeParticle.png"
    assert packets[1]["particleSystem"]["emissionRate"] == 12.0
    assert packets[1]["particleSystem"]["imageSize"]["cartesian2"] == [20.0, 20.0]
    assert packets[1]["particleSystem"]["startColor"]["rgba"] == [255, 255, 255, 178]
    assert packets[1]["particleSystem"]["endColor"]["rgba"] == [102, 102, 102, 0]

def test_range_ring_scene_compiles_to_czml_range_ring_graphics() -> None:
    scene = load_scene_file(RANGE_RING_SCENE_EXAMPLE_PATH)
    packets = compile_cesium_scene(scene)
    assert packets[0]["name"] == "Range Ring Demo"
    assert len(packets) == 2
    assert packets[1]["id"] == "range-ring-001"
    assert packets[1]["ellipse"]["fill"] is False
    assert packets[1]["ellipse"]["outline"] is True
    assert packets[1]["ellipse"]["outlineWidth"] == 2.0
    assert packets[1]["properties"]["shapeType"] == "rangeRing"
    assert packets[1]["properties"]["rangeRing"]["radiusMeters"] == 25000.0

def test_bearing_fan_scene_compiles_to_czml_bearing_fan_graphics() -> None:
    scene = load_scene_file(BEARING_FAN_SCENE_EXAMPLE_PATH)
    packets = compile_cesium_scene(scene)
    assert packets[0]["name"] == "Bearing Fan Demo"
    assert len(packets) == 2
    assert packets[1]["id"] == "bearing-fan-001"
    assert packets[1]["properties"]["shapeType"] == "bearingFan"
    assert packets[1]["properties"]["bearingFan"]["outerRadiusMeters"] == 46000.0
    assert packets[1]["properties"]["orientationDegrees"]["heading"] == 15.0

def test_fan_scene_compiles_to_czml_fan_graphics() -> None:
    scene = load_scene_file(FAN_SCENE_EXAMPLE_PATH)
    packets = compile_cesium_scene(scene)
    assert packets[0]["name"] == "Fan Demo"
    assert len(packets) == 2
    assert packets[1]["id"] == "fan-001"
    assert packets[1]["properties"]["shapeType"] == "fan"
    assert packets[1]["properties"]["fan"]["outerRadiusMeters"] == 38000.0
    assert packets[1]["properties"]["orientationDegrees"]["heading"] == 5.0

def test_custom_pattern_sensor_scene_compiles_to_czml_custom_pattern_sensor_graphics() -> None:
    scene = load_scene_file(CUSTOM_PATTERN_SENSOR_SCENE_EXAMPLE_PATH)
    packets = compile_cesium_scene(scene)
    assert packets[0]["name"] == "Custom Pattern Sensor Demo"
    assert len(packets) == 2
    assert packets[1]["id"] == "custom-pattern-sensor-001"
    assert packets[1]["polygon"]["arcType"] == "GEODESIC"
    assert packets[1]["polygon"]["perPositionHeight"] is True
    assert packets[1]["properties"]["shapeType"] == "customPatternSensor"
    assert packets[1]["properties"]["customPatternSensor"]["outerRadiusMeters"] == 70000.0
    assert list(packets[1]["properties"]["customPatternSensor"]["patternAzimuthElevationDegrees"][2]) == [0.0, 55.0]
    assert packets[1]["orientation"]["unitQuaternion"]
    assert packets[1]["properties"]["orientationDegrees"] == {
        "heading": 155.0,
        "pitch": -8.0,
        "roll": 0.0,
    }

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

def test_cylinder_scene_compiles_to_czml_cylinder_graphics() -> None:
    scene = load_scene_file(CYLINDER_SCENE_EXAMPLE_PATH)
    packets = compile_cesium_scene(scene)
    assert packets[0]["name"] == "Cylinder Demo"
    assert len(packets) == 2
    assert packets[1]["id"] == "cyl-001"
    assert packets[1]["cylinder"]["length"] == 6000.0
    assert packets[1]["cylinder"]["topRadius"] == 1500.0
    assert packets[1]["cylinder"]["bottomRadius"] == 2500.0
    assert packets[1]["cylinder"]["numberOfVerticalLines"] == 48
    assert packets[1]["cylinder"]["slope"] == 0.0

def test_cone_scene_compiles_to_czml_cone_graphics() -> None:
    scene = load_scene_file(CONE_SCENE_EXAMPLE_PATH)
    packets = compile_cesium_scene(scene)
    assert packets[0]["name"] == "Cone Demo"
    assert len(packets) == 2
    assert packets[1]["id"] == "cone-001"
    assert packets[1]["agi_conicSensor"]["radius"] == 14000.0
    assert packets[1]["agi_conicSensor"]["outerHalfAngle"] == pytest.approx(math.radians(18.0))
    assert packets[1]["agi_conicSensor"]["innerHalfAngle"] == pytest.approx(math.radians(4.5))
    assert packets[1]["agi_conicSensor"]["minimumClockAngle"] == pytest.approx(math.radians(25.0))
    assert packets[1]["agi_conicSensor"]["maximumClockAngle"] == pytest.approx(math.radians(325.0))
    assert packets[1]["agi_conicSensor"]["showIntersection"] is True
    assert packets[1]["agi_conicSensor"]["intersectionWidth"] == 3.0
    assert packets[1]["orientation"]["unitQuaternion"] == pytest.approx(
        [0.07277505546949486, -0.08655093529432578, 0.3031223057132924, 0.9462185765879608]
    )
    assert packets[1]["properties"]["orientationDegrees"] == {
        "heading": 35.0,
        "pitch": -12.0,
        "roll": 5.0,
    }

def test_conic_sensor_scene_compiles_to_czml_conic_sensor_graphics() -> None:
    scene = load_scene_file(Path("examples/scenes/conic-sensor-demo.scene.json"))
    packets = compile_cesium_scene(scene)
    assert packets[0]["name"] == "Conic Sensor Demo"
    assert len(packets) == 2
    assert packets[1]["id"] == "conic-sensor-001"
    assert packets[1]["agi_conicSensor"]["radius"] == 14000.0
    assert packets[1]["agi_conicSensor"]["outerHalfAngle"] == pytest.approx(math.radians(18.0))
    assert packets[1]["agi_conicSensor"]["innerHalfAngle"] == pytest.approx(math.radians(4.5))
    assert packets[1]["agi_conicSensor"]["minimumClockAngle"] == pytest.approx(math.radians(25.0))
    assert packets[1]["agi_conicSensor"]["maximumClockAngle"] == pytest.approx(math.radians(325.0))
    assert packets[1]["agi_conicSensor"]["showIntersection"] is True
    assert packets[1]["agi_conicSensor"]["intersectionWidth"] == 3.0
    assert packets[1]["orientation"]["unitQuaternion"] == pytest.approx(
        [0.07277505546949486, -0.08655093529432578, 0.3031223057132924, 0.9462185765879608]
    )

def test_rectangular_sensor_scene_compiles_to_czml_rectangular_sensor_graphics() -> None:
    scene = load_scene_file(RECTANGULAR_SENSOR_SCENE_EXAMPLE_PATH)
    packets = compile_cesium_scene(scene)
    assert packets[0]["name"] == "Rectangular Sensor Demo"
    assert len(packets) == 2
    assert packets[1]["id"] == "rect-sensor-001"
    assert packets[1]["agi_rectangularSensor"]["radius"] == 22000.0
    assert packets[1]["agi_rectangularSensor"]["xHalfAngle"] == pytest.approx(math.radians(16.0))
    assert packets[1]["agi_rectangularSensor"]["yHalfAngle"] == pytest.approx(math.radians(28.0))
    assert packets[1]["agi_rectangularSensor"]["showIntersection"] is True
    assert packets[1]["agi_rectangularSensor"]["intersectionWidth"] == 2.5
    assert packets[1]["orientation"]["unitQuaternion"] == pytest.approx(
        [0.029456238098177573, -0.07475958978523743, 0.15728091918369064, 0.9842794553545146]
    )

def test_sector2d_scene_compiles_to_czml_sector_polygon_graphics() -> None:
    scene = load_scene_file(SECTOR2D_SCENE_EXAMPLE_PATH)
    packets = compile_cesium_scene(scene)
    assert packets[0]["name"] == "Sector 2D Demo"
    assert len(packets) == 2
    assert packets[1]["id"] == "sector2d-001"
    assert packets[1]["polygon"]["arcType"] == "GEODESIC"
    assert packets[1]["polygon"]["perPositionHeight"] is True
    assert packets[1]["properties"]["shapeType"] == "sector2d"
    assert packets[1]["properties"]["sector2d"]["outerRadiusMeters"] == 14000.0
    assert packets[1]["properties"]["sector2d"]["azimuthStartDegrees"] == 25.0
    assert packets[1]["properties"]["sector2d"]["azimuthStopDegrees"] == 105.0

def test_sector2d_scene_round_trip_through_czml_parser() -> None:
    scene = load_scene_file(SECTOR2D_SCENE_EXAMPLE_PATH)
    rebuilt = parse_czml_to_scene(dump_cesium_scene_json(scene), source="czml")
    assert len(rebuilt.overlays) == 1
    sector = rebuilt.overlays[0]
    assert sector.geometryType == "sector2d"
    assert sector.sector2d is not None
    assert sector.sector2d.outerRadiusMeters == 14000.0
    assert sector.sector2d.azimuthStartDegrees == 25.0
    assert sector.sector2d.azimuthStopDegrees == 105.0

def test_sector_volume_scene_round_trip_through_czml_parser() -> None:
    scene = load_scene_file(SECTOR_VOLUME_SCENE_EXAMPLE_PATH)
    rebuilt = parse_czml_to_scene(dump_cesium_scene_json(scene), source="czml")
    assert len(rebuilt.overlays) == 1
    volume = rebuilt.overlays[0]
    assert volume.geometryType == "sectorVolume"
    assert volume.sectorVolume is not None
    assert volume.sectorVolume.outerRadiusMeters == 18000.0
    assert volume.sectorVolume.azimuthStartDegrees == 30.0
    assert volume.sectorVolume.azimuthStopDegrees == 120.0

def test_hemisphere_scene_round_trip_through_czml_parser() -> None:
    scene = load_scene_file(HEMISPHERE_SCENE_EXAMPLE_PATH)
    rebuilt = parse_czml_to_scene(dump_cesium_scene_json(scene), source="czml")
    assert len(rebuilt.overlays) == 1
    hemi = rebuilt.overlays[0]
    assert hemi.geometryType == "hemisphere"
    assert hemi.hemisphere is not None
    assert hemi.hemisphere.radiusMeters == 9000.0

def test_hemisphere_scene_compiles_to_czml_ellipsoid_graphics() -> None:
    scene = load_scene_file(HEMISPHERE_SCENE_EXAMPLE_PATH)
    packets = compile_cesium_scene(scene)
    assert packets[0]["name"] == "Hemisphere Demo"
    assert len(packets) == 2
    assert packets[1]["id"] == "hemisphere-001"
    assert packets[1]["ellipsoid"]["radii"]["cartesian"] == [9000.0, 9000.0, 9000.0]
    assert packets[1]["properties"]["shapeType"] == "hemisphere"
    assert packets[1]["properties"]["hemisphere"]["radiusMeters"] == 9000.0

def test_spherical_cap_scene_compiles_to_czml_spherical_cap_graphics() -> None:
    scene = load_scene_file(SPHERICAL_CAP_SCENE_EXAMPLE_PATH)
    packets = compile_cesium_scene(scene)
    assert packets[0]["name"] == "Spherical Cap Demo"
    assert len(packets) == 2
    assert packets[1]["id"] == "sphericalcap-001"
    assert packets[1]["ellipsoid"]["radii"]["cartesian"] == [11000.0, 11000.0, 11000.0]
    assert packets[1]["properties"]["shapeType"] == "sphericalCap"
    assert packets[1]["properties"]["sphericalCap"]["radiusMeters"] == 11000.0
    assert packets[1]["properties"]["sphericalCap"]["portion"] == "upper"

def test_keyhole_scene_compiles_to_czml_keyhole_polygon_graphics() -> None:
    scene = load_scene_file(KEYHOLE_SCENE_EXAMPLE_PATH)
    packets = compile_cesium_scene(scene)
    assert packets[0]["name"] == "Keyhole Demo"
    assert len(packets) == 2
    assert packets[1]["id"] == "keyhole-001"
    assert packets[1]["polygon"]["arcType"] == "GEODESIC"
    assert packets[1]["properties"]["shapeType"] == "keyhole"
    assert packets[1]["properties"]["keyhole"]["innerRadiusMeters"] == 3500.0
    assert packets[1]["properties"]["keyhole"]["outerRadiusMeters"] == 12500.0

def test_keyhole_scene_round_trip_through_czml_parser() -> None:
    scene = load_scene_file(KEYHOLE_SCENE_EXAMPLE_PATH)
    rebuilt = parse_czml_to_scene(dump_cesium_scene_json(scene), source="czml")
    assert len(rebuilt.overlays) == 1
    keyhole = rebuilt.overlays[0]
    assert keyhole.geometryType == "keyhole"
    assert keyhole.keyhole is not None
    assert keyhole.keyhole.innerRadiusMeters == 3500.0
    assert keyhole.keyhole.outerRadiusMeters == 12500.0
    assert keyhole.keyhole.azimuthStartDegrees == 45.0
    assert keyhole.keyhole.azimuthStopDegrees == 135.0

def test_frustum_scene_compiles_to_czml_frustum_graphics() -> None:
    scene = load_scene_file(FRUSTUM_SCENE_EXAMPLE_PATH)
    packets = compile_cesium_scene(scene)
    assert packets[0]["name"] == "Frustum Demo"
    assert len(packets) == 2
    assert packets[1]["id"] == "frustum-001"
    assert packets[1]["box"]["dimensions"]["cartesian"][0] == 10000.0
    assert packets[1]["box"]["dimensions"]["cartesian"][1] == pytest.approx(8735.285622388856)
    assert packets[1]["box"]["dimensions"]["cartesian"][2] == pytest.approx(6430.780618346945)
    assert packets[1]["properties"]["shapeType"] == "frustum"
    assert packets[1]["properties"]["frustum"]["nearMeters"] == 2000.0
    assert packets[1]["properties"]["frustum"]["farMeters"] == 12000.0

def test_frustum_scene_round_trip_through_czml_parser() -> None:
    scene = load_scene_file(FRUSTUM_SCENE_EXAMPLE_PATH)
    rebuilt = parse_czml_to_scene(dump_cesium_scene_json(scene), source="czml")
    assert len(rebuilt.overlays) == 1
    frustum = rebuilt.overlays[0]
    assert frustum.geometryType == "frustum"
    assert frustum.frustum is not None
    assert frustum.frustum.nearMeters == 2000.0
    assert frustum.frustum.farMeters == 12000.0
    assert frustum.frustum.horizontalFovDegrees == 40.0
    assert frustum.frustum.verticalFovDegrees == 30.0

def test_spherical_cap_scene_round_trip_through_czml_parser() -> None:
    scene = load_scene_file(SPHERICAL_CAP_SCENE_EXAMPLE_PATH)
    rebuilt = parse_czml_to_scene(dump_cesium_scene_json(scene), source="czml")
    assert len(rebuilt.overlays) == 1
    cap = rebuilt.overlays[0]
    assert cap.geometryType == "sphericalCap"
    assert cap.sphericalCap is not None
    assert cap.sphericalCap.radiusMeters == 11000.0
    assert cap.sphericalCap.portion == "upper"
    assert cap.sphericalCap.azimuthStartDegrees == 15.0
    assert cap.sphericalCap.azimuthStopDegrees == 165.0

def test_polyline_volume_scene_compiles_to_czml_polyline_volume_graphics() -> None:
    scene = load_scene_file(POLYLINE_VOLUME_SCENE_EXAMPLE_PATH)
    packets = compile_cesium_scene(scene)
    assert packets[0]["name"] == "Polyline Volume Demo"
    assert len(packets) == 2
    assert packets[1]["id"] == "pv-001"
    assert packets[1]["polylineVolume"]["positions"]["cartographicDegrees"] == [
        -97.78,
        30.22,
        1200.0,
        -97.73,
        30.25,
        1800.0,
        -97.69,
        30.27,
        2200.0,
    ]
    assert packets[1]["polylineVolume"]["shape"]["cartesian"] == [
        -1000.0,
        -1000.0,
        1000.0,
        -1000.0,
        1000.0,
        1000.0,
        -1000.0,
        1000.0,
    ]
    assert packets[1]["polylineVolume"]["cornerType"] == "MITERED"

def test_plane_scene_compiles_to_czml_plane_graphics() -> None:
    scene = load_scene_file(PLANE_SCENE_EXAMPLE_PATH)
    packets = compile_cesium_scene(scene)
    assert packets[0]["name"] == "Plane Demo"
    assert len(packets) == 2
    assert packets[1]["id"] == "plane-001"
    assert packets[1]["plane"]["plane"]["normal"]["cartesian"] == [0.0, 0.0, 1.0]
    assert packets[1]["plane"]["plane"]["distance"] == 0.0
    assert packets[1]["plane"]["dimensions"]["cartesian"] == [45000.0, 28000.0]
    assert packets[1]["plane"]["fill"] is True
    assert packets[1]["plane"]["outline"] is False

def test_tileset_scene_compiles_to_czml_tileset_graphics() -> None:
    scene = load_scene_file(TILESET_SCENE_EXAMPLE_PATH)
    packets = compile_cesium_scene(scene)
    assert packets[0]["name"] == "Tileset Demo"
    assert len(packets) == 2
    assert packets[1]["id"] == "tileset-001"
    assert packets[1]["tileset"]["uri"] == "https://example.org/tilesets/demo/tileset.json"

def test_vector_scene_compiles_to_czml_vector_graphics() -> None:
    scene = load_scene_file(VECTOR_SCENE_EXAMPLE_PATH)
    packets = compile_cesium_scene(scene)
    assert packets[0]["name"] == "Vector Demo"
    assert len(packets) == 2
    assert packets[1]["id"] == "vector-001"
    assert packets[1]["polyline"]["positions"]["cartographicDegrees"] == [
        -97.74,
        30.27,
        9000.0,
        -97.68,
        30.33,
        11000.0,
    ]
    assert packets[1]["polyline"]["width"] == 4.0
    assert packets[1]["polyline"]["material"]["solidColor"]["color"]["rgba"] == [255, 153, 0, 255]

def test_velocity_vector_scene_compiles_to_czml_velocity_vector_graphics() -> None:
    scene = load_scene_file(VELOCITY_VECTOR_SCENE_EXAMPLE_PATH)
    packets = compile_cesium_scene(scene)
    assert packets[0]["name"] == "Velocity Vector Demo"
    assert len(packets) == 2
    assert packets[1]["id"] == "velocity-vector-001"
    assert packets[1]["properties"]["objectType"] == "velocityVector"
    assert packets[1]["polyline"]["positions"]["cartographicDegrees"] == [
        -97.72,
        30.26,
        8000.0,
        -97.65,
        30.31,
        9500.0,
    ]
    assert packets[1]["polyline"]["width"] == 3.5
    assert packets[1]["polyline"]["material"]["solidColor"]["color"]["rgba"] == [0, 170, 255, 255]

def test_acceleration_vector_scene_compiles_to_czml_acceleration_vector_graphics() -> None:
    scene = load_scene_file(ACCELERATION_VECTOR_SCENE_EXAMPLE_PATH)
    packets = compile_cesium_scene(scene)
    assert packets[0]["name"] == "Acceleration Vector Demo"
    assert len(packets) == 2
    assert packets[1]["id"] == "acceleration-vector-001"
    assert packets[1]["properties"]["objectType"] == "accelerationVector"
    assert packets[1]["polyline"]["positions"]["cartographicDegrees"] == [
        -97.70,
        30.25,
        7800.0,
        -97.62,
        30.29,
        8800.0,
    ]
    assert packets[1]["polyline"]["width"] == 3.0
    assert packets[1]["polyline"]["material"]["solidColor"]["color"]["rgba"] == [220, 90, 70, 255]

def test_line_of_sight_scene_compiles_to_czml_line_of_sight_graphics() -> None:
    scene = load_scene_file(LINE_OF_SIGHT_SCENE_EXAMPLE_PATH)
    packets = compile_cesium_scene(scene)
    assert packets[0]["name"] == "Line of Sight Demo"
    assert len(packets) == 2
    assert packets[1]["id"] == "los-001"
    assert packets[1]["properties"]["objectType"] == "lineOfSight"
    assert packets[1]["polyline"]["positions"]["cartographicDegrees"] == [
        -97.74,
        30.27,
        1000.0,
        -97.66,
        30.31,
        1000.0,
    ]
    assert packets[1]["polyline"]["width"] == 2.5
    assert packets[1]["polyline"]["material"]["solidColor"]["color"]["rgba"] == [255, 255, 255, 255]

def test_ellipsoid_sphere_scene_compiles_to_czml_ellipsoid_graphics() -> None:
    scene = load_scene_file(ELLIPSOID_SPHERE_SCENE_EXAMPLE_PATH)
    packets = compile_cesium_scene(scene)
    assert packets[0]["name"] == "Ellipsoid Sphere Demo"
    assert len(packets) == 3
    assert packets[1]["id"] == "ellipsoid-001"
    assert packets[1]["ellipsoid"]["radii"]["cartesian"] == [8000.0, 12000.0, 6000.0]
    assert packets[2]["id"] == "sphere-001"
    assert packets[2]["ellipsoid"]["radii"]["cartesian"] == [10000.0, 10000.0, 10000.0]

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

def test_uncertainty_covariance_scene_round_trip_through_czml_parser() -> None:
    scene = load_scene_file(UNCERTAINTY_COVARIANCE_SCENE_EXAMPLE_PATH)
    rebuilt = parse_czml_to_scene(dump_cesium_scene_json(scene), source="czml")
    assert len(rebuilt.overlays) == 2
    ellipsoid, ellipse = rebuilt.overlays
    assert ellipsoid.geometryType == "uncertaintyEllipsoid"
    assert ellipsoid.uncertaintyEllipsoid is not None
    assert ellipsoid.uncertaintyEllipsoid.radiiMeters == (2200.0, 1200.0, 800.0)
    assert ellipsoid.uncertaintyEllipsoid.slicePartitions == 24
    assert ellipse.geometryType == "covarianceEllipse"
    assert ellipse.covarianceEllipse is not None
    assert ellipse.covarianceEllipse.semiMajorAxisMeters == 6000.0
    assert ellipse.covarianceEllipse.rotationDegrees == 30.0

def test_range_ring_scene_round_trip_through_czml_parser() -> None:
    scene = load_scene_file(RANGE_RING_SCENE_EXAMPLE_PATH)
    rebuilt = parse_czml_to_scene(dump_cesium_scene_json(scene), source="czml")
    assert len(rebuilt.overlays) == 1
    ring = rebuilt.overlays[0]
    assert ring.geometryType == "rangeRing"
    assert ring.rangeRing is not None
    assert ring.rangeRing.radiusMeters == 25000.0
    assert ring.rangeRing.outlineWidthPx == 2.0

def test_bearing_fan_scene_round_trip_through_czml_parser() -> None:
    scene = load_scene_file(BEARING_FAN_SCENE_EXAMPLE_PATH)
    rebuilt = parse_czml_to_scene(dump_cesium_scene_json(scene), source="czml")
    assert len(rebuilt.overlays) == 1
    fan = rebuilt.overlays[0]
    assert fan.geometryType == "bearingFan"
    assert fan.bearingFan is not None
    assert fan.bearingFan.outerRadiusMeters == 46000.0
    assert fan.bearingFan.azimuthStartDegrees == -12.0
    assert fan.orientation is not None
    assert fan.orientation.headingDeg == 15.0

def test_fan_scene_round_trip_through_czml_parser() -> None:
    scene = load_scene_file(FAN_SCENE_EXAMPLE_PATH)
    rebuilt = parse_czml_to_scene(dump_cesium_scene_json(scene), source="czml")
    assert len(rebuilt.overlays) == 1
    fan = rebuilt.overlays[0]
    assert fan.geometryType == "fan"
    assert fan.fan is not None
    assert fan.fan.outerRadiusMeters == 38000.0
    assert fan.fan.azimuthStartDegrees == -20.0
    assert fan.orientation is not None
    assert fan.orientation.headingDeg == 5.0

def test_custom_pattern_sensor_scene_round_trip_through_czml_parser() -> None:
    scene = load_scene_file(CUSTOM_PATTERN_SENSOR_SCENE_EXAMPLE_PATH)
    rebuilt = parse_czml_to_scene(dump_cesium_scene_json(scene), source="czml")
    assert len(rebuilt.overlays) == 1
    sensor = rebuilt.overlays[0]
    assert sensor.geometryType == "customPatternSensor"
    assert sensor.customPatternSensor is not None
    assert sensor.customPatternSensor.outerRadiusMeters == 70000.0
    assert sensor.customPatternSensor.azimuthStartDegrees == -35.0
    assert sensor.customPatternSensor.patternAzimuthElevationDegrees[2] == (0.0, 55.0)

def test_wall_scene_round_trip_through_czml_parser() -> None:
    scene = load_scene_file(WALL_SCENE_EXAMPLE_PATH)
    rebuilt = parse_czml_to_scene(dump_cesium_scene_json(scene), source="czml")
    assert len(rebuilt.overlays) == 1
    wall = rebuilt.overlays[0]
    assert wall.geometryType == "wall"
    assert wall.wall is not None
    assert wall.wall.maximumHeightsMeters == [2500.0, 3000.0, 2800.0]

def test_cylinder_scene_round_trip_through_czml_parser() -> None:
    scene = load_scene_file(CYLINDER_SCENE_EXAMPLE_PATH)
    rebuilt = parse_czml_to_scene(dump_cesium_scene_json(scene), source="czml")
    assert len(rebuilt.overlays) == 1
    cylinder = rebuilt.overlays[0]
    assert cylinder.geometryType == "cylinder"
    assert cylinder.cylinder is not None
    assert cylinder.cylinder.lengthMeters == 6000.0

def test_cone_scene_round_trip_through_czml_parser() -> None:
    scene = load_scene_file(CONE_SCENE_EXAMPLE_PATH)
    rebuilt = parse_czml_to_scene(dump_cesium_scene_json(scene), source="czml")
    assert len(rebuilt.overlays) == 1
    cone = rebuilt.overlays[0]
    assert cone.geometryType == "cone"
    assert cone.cone is not None
    assert cone.cone.radiusMeters == 14000.0
    assert cone.orientation is not None
    assert cone.orientation.headingDeg == 35.0

def test_conic_sensor_scene_round_trip_through_czml_parser() -> None:
    scene = load_scene_file(Path("examples/scenes/conic-sensor-demo.scene.json"))
    rebuilt = parse_czml_to_scene(dump_cesium_scene_json(scene), source="czml")
    assert len(rebuilt.overlays) == 1
    sensor = rebuilt.overlays[0]
    assert sensor.geometryType == "conicSensor"
    assert sensor.conicSensor is not None
    assert sensor.conicSensor.radiusMeters == 14000.0
    assert sensor.conicSensor.outerHalfAngleDegrees == 18.0
    assert sensor.conicSensor.innerHalfAngleDegrees == 4.5

def test_rectangular_sensor_scene_round_trip_through_czml_parser() -> None:
    scene = load_scene_file(RECTANGULAR_SENSOR_SCENE_EXAMPLE_PATH)
    rebuilt = parse_czml_to_scene(dump_cesium_scene_json(scene), source="czml")
    assert len(rebuilt.overlays) == 1
    sensor = rebuilt.overlays[0]
    assert sensor.geometryType == "rectangularSensor"
    assert sensor.rectangularSensor is not None
    assert sensor.rectangularSensor.radiusMeters == 22000.0
    assert sensor.rectangularSensor.xHalfAngleDegrees == 16.0
    assert sensor.rectangularSensor.yHalfAngleDegrees == 28.0

def test_polyline_volume_scene_round_trip_through_czml_parser() -> None:
    scene = load_scene_file(POLYLINE_VOLUME_SCENE_EXAMPLE_PATH)
    rebuilt = parse_czml_to_scene(dump_cesium_scene_json(scene), source="czml")
    assert len(rebuilt.overlays) == 1
    volume = rebuilt.overlays[0]
    assert volume.geometryType == "polylineVolume"
    assert volume.polylineVolume is not None
    assert len(volume.polylineVolume.positions) == 3
    assert len(volume.polylineVolume.shapePositions) == 4

def test_plane_scene_round_trip_through_czml_parser() -> None:
    scene = load_scene_file(PLANE_SCENE_EXAMPLE_PATH)
    rebuilt = parse_czml_to_scene(dump_cesium_scene_json(scene), source="czml")
    assert len(rebuilt.overlays) == 1
    plane = rebuilt.overlays[0]
    assert plane.geometryType == "plane"
    assert plane.plane is not None
    assert plane.plane.normal == (0.0, 0.0, 1.0)

def test_tileset_scene_round_trip_through_czml_parser() -> None:
    scene = load_scene_file(TILESET_SCENE_EXAMPLE_PATH)
    rebuilt = parse_czml_to_scene(dump_cesium_scene_json(scene), source="czml")
    assert len(rebuilt.overlays) == 1
    tileset = rebuilt.overlays[0]
    assert tileset.geometryType == "tileset"
    assert tileset.tileset is not None
    assert tileset.tileset.uri == "https://example.org/tilesets/demo/tileset.json"

def test_vector_scene_round_trip_through_czml_parser() -> None:
    scene = load_scene_file(VECTOR_SCENE_EXAMPLE_PATH)
    rebuilt = parse_czml_to_scene(dump_cesium_scene_json(scene), source="czml")
    assert len(rebuilt.vectors) == 1
    vector = rebuilt.vectors[0]
    assert vector.id == "vector-001"
    assert vector.startPosition.longitudeDeg == -97.74
    assert vector.endPosition.latitudeDeg == 30.33
    assert vector.widthPx == 4.0

def test_velocity_vector_scene_round_trip_through_czml_parser() -> None:
    scene = load_scene_file(VELOCITY_VECTOR_SCENE_EXAMPLE_PATH)
    rebuilt = parse_czml_to_scene(dump_cesium_scene_json(scene), source="czml")
    assert len(rebuilt.velocityVectors) == 1
    velocity_vector = rebuilt.velocityVectors[0]
    assert velocity_vector.id == "velocity-vector-001"
    assert velocity_vector.startPosition.longitudeDeg == -97.72
    assert velocity_vector.endPosition.latitudeDeg == 30.31
    assert velocity_vector.widthPx == 3.5

def test_acceleration_vector_scene_round_trip_through_czml_parser() -> None:
    scene = load_scene_file(ACCELERATION_VECTOR_SCENE_EXAMPLE_PATH)
    rebuilt = parse_czml_to_scene(dump_cesium_scene_json(scene), source="czml")
    assert len(rebuilt.accelerationVectors) == 1
    acceleration_vector = rebuilt.accelerationVectors[0]
    assert acceleration_vector.id == "acceleration-vector-001"
    assert acceleration_vector.startPosition.longitudeDeg == -97.70
    assert acceleration_vector.endPosition.latitudeDeg == 30.29
    assert acceleration_vector.widthPx == 3.0

def test_line_of_sight_scene_round_trip_through_czml_parser() -> None:
    scene = load_scene_file(LINE_OF_SIGHT_SCENE_EXAMPLE_PATH)
    rebuilt = parse_czml_to_scene(dump_cesium_scene_json(scene), source="czml")
    assert len(rebuilt.lineOfSights) == 1
    line_of_sight = rebuilt.lineOfSights[0]
    assert line_of_sight.id == "los-001"
    assert line_of_sight.startPosition.longitudeDeg == -97.74
    assert line_of_sight.endPosition.latitudeDeg == 30.31
    assert line_of_sight.widthPx == 2.5

def test_axes_scene_round_trip_through_czml_parser() -> None:
    scene = load_scene_file(AXES_SCENE_EXAMPLE_PATH)
    rebuilt = parse_czml_to_scene(dump_cesium_scene_json(scene), source="czml")
    assert len(rebuilt.bodyAxes) == 1
    assert len(rebuilt.principalAxes) == 1
    body_axes = rebuilt.bodyAxes[0]
    assert body_axes.id == "body-axes-001"
    assert body_axes.axisLengthsMeters == (4500.0, 3000.0, 1800.0)
    assert body_axes.orientation is not None
    assert body_axes.orientation.headingDeg == 42.0
    principal_axes = rebuilt.principalAxes[0]
    assert principal_axes.id == "principal-axes-001"
    assert principal_axes.axisLengthsMeters == (3800.0, 2200.0, 2600.0)

def test_relative_intercept_scene_round_trip_through_czml_parser() -> None:
    scene = load_scene_file(RELATIVE_INTERCEPT_SCENE_EXAMPLE_PATH)
    rebuilt = parse_czml_to_scene(dump_cesium_scene_json(scene), source="czml")
    assert len(rebuilt.relativeLines) == 1
    assert len(rebuilt.interceptLines) == 1
    relative_line = rebuilt.relativeLines[0]
    assert relative_line.id == "relative-line-001"
    assert relative_line.startPosition.longitudeDeg == -97.74
    assert relative_line.endPosition.altitudeM == 9400.0
    intercept_line = rebuilt.interceptLines[0]
    assert intercept_line.id == "intercept-line-001"
    assert intercept_line.startPosition.latitudeDeg == 30.29
    assert intercept_line.endPosition.longitudeDeg == -97.66

def test_ellipsoid_sphere_scene_round_trip_through_czml_parser() -> None:
    scene = load_scene_file(ELLIPSOID_SPHERE_SCENE_EXAMPLE_PATH)
    rebuilt = parse_czml_to_scene(dump_cesium_scene_json(scene), source="czml")
    assert len(rebuilt.overlays) == 2
    assert rebuilt.overlays[0].geometryType == "ellipsoid"
    assert rebuilt.overlays[0].ellipsoid is not None
    assert rebuilt.overlays[0].ellipsoid.radiiMeters == (8000.0, 12000.0, 6000.0)
    assert rebuilt.overlays[1].geometryType == "sphere"
    assert rebuilt.overlays[1].sphere is not None
    assert rebuilt.overlays[1].sphere.radiusMeters == 10000.0

def test_scene_files_can_be_written(example_scene: VssScene, tmp_path: Path) -> None:
    scene_path = write_scene_file(example_scene, tmp_path / "scene.json")
    czml_path = write_cesium_scene(example_scene, tmp_path / "scene.czml.json")

    loaded_scene = load_scene_file(scene_path)
    assert loaded_scene.document.name == "Demo Scene"
    assert '"id": "aircraft-001"' in czml_path.read_text(encoding="utf-8")

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

def test_cesium_viewer_html_renders_scene_views() -> None:
    scene = load_scene_file(VIEW_SCENE_EXAMPLE_PATH)
    html = render_cesium_viewer_html(
        czml_path="./view-demo.scene.czml.json",
        title="View Demo",
        views=scene.views + scene.cameraViews,
    )
    assert "viewControls" in html
    assert "aircraft-overview" in html
    assert "aircraft-camera-view" in html
    assert "activateSceneView" in html

def test_view_scene_round_trip_through_czml_parser() -> None:
    scene = load_scene_file(VIEW_SCENE_EXAMPLE_PATH)
    rebuilt = parse_czml_to_scene(dump_cesium_scene_json(scene), source="czml")
    assert len(rebuilt.cameraViews) == 1
    camera_view = rebuilt.cameraViews[0]
    assert camera_view.id == "aircraft-camera-view"
    assert camera_view.rangeMeters == 22000.0
    assert camera_view.orientation is not None
    assert camera_view.orientation.pitchDeg == -30.0

def test_cesium_viewer_file_can_be_written(tmp_path: Path) -> None:
    viewer_path = write_cesium_viewer(
        tmp_path / "air-track.viewer.html",
        czml_path="./air-track.czml.json",
        title="VSS Air Track Viewer",
    )
    html = viewer_path.read_text(encoding="utf-8")
    assert "air-track.czml.json" in html
