import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vss import (
    assess_scene_for_target,
    get_cesium_capabilities,
    get_simdis_capabilities,
    get_soap_capabilities,
    load_scene_file,
)

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


def _assert_schema_feature_support(report, feature_id: str, support: str) -> None:
    assert any(feature.featureId == feature_id and feature.support == support for feature in report.schemaFeatures)


def _assert_scene_feature_support(assessment, feature_id: str, support: str) -> None:
    assert any(feature.featureId == feature_id and feature.support == support for feature in assessment.features)


def test_static_target_capability_reports_describe_current_surfaces() -> None:
    cesium = get_cesium_capabilities()
    simdis = get_simdis_capabilities()
    soap = get_soap_capabilities()

    assert [surface.id for surface in cesium.surfaces] == ["czml", "cesium-js-viewer", "cesium-js-loader"]
    assert [surface.id for surface in simdis.surfaces] == ["simdis-asi", "simdis-gog", "simdis-bundle"]
    assert [surface.id for surface in soap.surfaces] == ["soap-envelope", "soap-bundle", "orb-related"]
    _assert_schema_feature_support(cesium, "object.entity.orientation", "partial")
    _assert_schema_feature_support(cesium, "object.path.sampledMotion", "partial")
    _assert_schema_feature_support(cesium, "object.track.sampledMotion", "strong")
    _assert_schema_feature_support(cesium, "object.rectangle.geometry", "strong")
    _assert_schema_feature_support(cesium, "object.corridor.geometry", "strong")
    _assert_schema_feature_support(cesium, "object.ellipse.geometry", "strong")
    _assert_schema_feature_support(cesium, "object.circle.geometry", "strong")
    _assert_schema_feature_support(cesium, "object.wall.geometry", "strong")
    _assert_schema_feature_support(cesium, "object.box.geometry", "strong")
    _assert_schema_feature_support(cesium, "object.cylinder.geometry", "strong")
    _assert_schema_feature_support(cesium, "object.cone.geometry", "strong")
    _assert_schema_feature_support(cesium, "object.polylineVolume.geometry", "strong")
    _assert_schema_feature_support(cesium, "object.plane.geometry", "strong")
    _assert_schema_feature_support(cesium, "object.tileset.geometry", "strong")
    _assert_schema_feature_support(cesium, "object.vector.geometry", "strong")
    _assert_schema_feature_support(cesium, "object.velocityVector.geometry", "strong")
    _assert_schema_feature_support(cesium, "object.accelerationVector.geometry", "strong")
    _assert_schema_feature_support(cesium, "object.lineOfSight.geometry", "strong")
    _assert_schema_feature_support(cesium, "object.ellipsoid.geometry", "strong")
    _assert_schema_feature_support(cesium, "object.sphere.geometry", "strong")
    _assert_schema_feature_support(cesium, "views", "partial")
    _assert_schema_feature_support(cesium, "cameraView", "partial")
    _assert_schema_feature_support(simdis, "object.cone.geometry", "unsupported")
    _assert_schema_feature_support(soap, "object.cone.geometry", "unsupported")
    _assert_schema_feature_support(simdis, "object.velocityVector.geometry", "unsupported")
    _assert_schema_feature_support(soap, "object.velocityVector.geometry", "unsupported")
    _assert_schema_feature_support(simdis, "object.accelerationVector.geometry", "unsupported")
    _assert_schema_feature_support(soap, "object.accelerationVector.geometry", "unsupported")
    _assert_schema_feature_support(simdis, "object.lineOfSight.geometry", "unsupported")
    _assert_schema_feature_support(soap, "object.lineOfSight.geometry", "unsupported")
    _assert_schema_feature_support(soap, "views", "partial")
    _assert_schema_feature_support(simdis, "style.model", "unsupported")


def test_scene_target_assessment_reports_supported_and_unsupported_features() -> None:
    scene = load_scene_file(MIXED_SCENE_EXAMPLE_PATH)

    cesium = assess_scene_for_target(scene, "cesium")
    simdis = assess_scene_for_target(scene, "simdis")
    soap = assess_scene_for_target(scene, "soap")

    assert cesium.objectCount == 5
    _assert_scene_feature_support(cesium, "object.overlay.polygon", "strong")
    _assert_scene_feature_support(cesium, "object.entity.orientation", "partial")

    assert simdis.objectCount == 5
    _assert_scene_feature_support(simdis, "style.model", "unsupported")
    _assert_scene_feature_support(simdis, "object.overlay.polyline", "strong")

    assert soap.objectCount == 5
    _assert_scene_feature_support(soap, "style.icon", "unsupported")
    _assert_scene_feature_support(soap, "object.sensor", "partial")


def test_path_scene_assessment_reports_path_support() -> None:
    scene = load_scene_file(Path("examples/scenes/path-demo.scene.json"))
    assessment = assess_scene_for_target(scene, "cesium")
    assert assessment.objectCount == 1
    _assert_scene_feature_support(assessment, "object.path.sampledMotion", "partial")


def test_track_scene_assessment_reports_track_support() -> None:
    scene = load_scene_file(Path("examples/scenes/track-demo.scene.json"))
    assessment = assess_scene_for_target(scene, "cesium")
    assert assessment.objectCount == 1
    _assert_scene_feature_support(assessment, "object.track.sampledMotion", "strong")


def test_rectangle_scene_assessment_reports_rectangle_support() -> None:
    scene = load_scene_file(Path("examples/scenes/rectangle-demo.scene.json"))
    assessment = assess_scene_for_target(scene, "cesium")
    assert assessment.objectCount == 1
    _assert_scene_feature_support(assessment, "object.rectangle.geometry", "strong")


def test_corridor_scene_assessment_reports_corridor_support() -> None:
    scene = load_scene_file(CORRIDOR_SCENE_EXAMPLE_PATH)
    assessment = assess_scene_for_target(scene, "cesium")
    assert assessment.objectCount == 1
    _assert_scene_feature_support(assessment, "object.corridor.geometry", "strong")


def test_ellipse_circle_scene_assessment_reports_ellipse_and_circle_support() -> None:
    scene = load_scene_file(ELLIPSE_CIRCLE_SCENE_EXAMPLE_PATH)
    assessment = assess_scene_for_target(scene, "cesium")
    assert assessment.objectCount == 2
    _assert_scene_feature_support(assessment, "object.ellipse.geometry", "strong")
    _assert_scene_feature_support(assessment, "object.circle.geometry", "strong")


def test_uncertainty_covariance_scene_assessment_reports_support() -> None:
    scene = load_scene_file(UNCERTAINTY_COVARIANCE_SCENE_EXAMPLE_PATH)
    cesium = assess_scene_for_target(scene, "cesium")
    simdis = assess_scene_for_target(scene, "simdis")
    soap = assess_scene_for_target(scene, "soap")
    assert cesium.objectCount == 2
    _assert_scene_feature_support(cesium, "object.uncertaintyEllipsoid.geometry", "partial")
    _assert_scene_feature_support(cesium, "object.covarianceEllipse.geometry", "partial")
    _assert_scene_feature_support(simdis, "object.uncertaintyEllipsoid.geometry", "unsupported")
    _assert_scene_feature_support(simdis, "object.covarianceEllipse.geometry", "unsupported")
    _assert_scene_feature_support(soap, "object.uncertaintyEllipsoid.geometry", "unsupported")
    _assert_scene_feature_support(soap, "object.covarianceEllipse.geometry", "unsupported")


def test_range_ring_scene_assessment_reports_range_ring_support() -> None:
    scene = load_scene_file(RANGE_RING_SCENE_EXAMPLE_PATH)
    assessment = assess_scene_for_target(scene, "cesium")
    assert assessment.objectCount == 1
    _assert_scene_feature_support(assessment, "object.rangeRing.geometry", "partial")


def test_bearing_fan_scene_assessment_reports_bearing_fan_support() -> None:
    scene = load_scene_file(BEARING_FAN_SCENE_EXAMPLE_PATH)
    assessment = assess_scene_for_target(scene, "cesium")
    assert assessment.objectCount == 1
    _assert_scene_feature_support(assessment, "object.bearingFan.geometry", "partial")


def test_fan_scene_assessment_reports_fan_support() -> None:
    scene = load_scene_file(FAN_SCENE_EXAMPLE_PATH)
    assessment = assess_scene_for_target(scene, "cesium")
    assert assessment.objectCount == 1
    _assert_scene_feature_support(assessment, "object.fan.geometry", "partial")


def test_custom_pattern_sensor_scene_assessment_reports_support() -> None:
    scene = load_scene_file(CUSTOM_PATTERN_SENSOR_SCENE_EXAMPLE_PATH)
    cesium = assess_scene_for_target(scene, "cesium")
    simdis = assess_scene_for_target(scene, "simdis")
    soap = assess_scene_for_target(scene, "soap")
    assert cesium.objectCount == 1
    _assert_scene_feature_support(cesium, "object.customPatternSensor.geometry", "partial")
    _assert_scene_feature_support(simdis, "object.customPatternSensor.geometry", "unsupported")
    _assert_scene_feature_support(soap, "object.customPatternSensor.geometry", "unsupported")


def test_wall_scene_assessment_reports_wall_support() -> None:
    scene = load_scene_file(WALL_SCENE_EXAMPLE_PATH)
    assessment = assess_scene_for_target(scene, "cesium")
    assert assessment.objectCount == 1
    _assert_scene_feature_support(assessment, "object.wall.geometry", "strong")


def test_box_scene_assessment_reports_box_support() -> None:
    scene = load_scene_file(BOX_SCENE_EXAMPLE_PATH)
    assessment = assess_scene_for_target(scene, "cesium")
    assert assessment.objectCount == 1
    _assert_scene_feature_support(assessment, "object.box.geometry", "strong")


def test_cylinder_scene_assessment_reports_cylinder_support() -> None:
    scene = load_scene_file(CYLINDER_SCENE_EXAMPLE_PATH)
    assessment = assess_scene_for_target(scene, "cesium")
    assert assessment.objectCount == 1
    _assert_scene_feature_support(assessment, "object.cylinder.geometry", "strong")


def test_cone_scene_assessment_reports_cone_support() -> None:
    scene = load_scene_file(CONE_SCENE_EXAMPLE_PATH)
    cesium = assess_scene_for_target(scene, "cesium")
    simdis = assess_scene_for_target(scene, "simdis")
    soap = assess_scene_for_target(scene, "soap")
    assert cesium.objectCount == 1
    _assert_scene_feature_support(cesium, "object.cone.geometry", "strong")
    _assert_scene_feature_support(simdis, "object.cone.geometry", "unsupported")
    _assert_scene_feature_support(soap, "object.cone.geometry", "unsupported")


def test_conic_sensor_scene_assessment_reports_support() -> None:
    scene = load_scene_file(Path("examples/scenes/conic-sensor-demo.scene.json"))
    cesium = assess_scene_for_target(scene, "cesium")
    simdis = assess_scene_for_target(scene, "simdis")
    soap = assess_scene_for_target(scene, "soap")
    assert cesium.objectCount == 1
    _assert_scene_feature_support(cesium, "object.conicSensor.geometry", "strong")
    _assert_scene_feature_support(simdis, "object.conicSensor.geometry", "unsupported")
    _assert_scene_feature_support(soap, "object.conicSensor.geometry", "unsupported")


def test_rectangular_sensor_scene_assessment_reports_support() -> None:
    scene = load_scene_file(RECTANGULAR_SENSOR_SCENE_EXAMPLE_PATH)
    cesium = assess_scene_for_target(scene, "cesium")
    simdis = assess_scene_for_target(scene, "simdis")
    soap = assess_scene_for_target(scene, "soap")
    assert cesium.objectCount == 1
    _assert_scene_feature_support(cesium, "object.rectangularSensor.geometry", "strong")
    _assert_scene_feature_support(simdis, "object.rectangularSensor.geometry", "unsupported")
    _assert_scene_feature_support(soap, "object.rectangularSensor.geometry", "unsupported")


def test_sector2d_scene_assessment_reports_support() -> None:
    scene = load_scene_file(SECTOR2D_SCENE_EXAMPLE_PATH)
    cesium = assess_scene_for_target(scene, "cesium")
    simdis = assess_scene_for_target(scene, "simdis")
    soap = assess_scene_for_target(scene, "soap")
    assert cesium.objectCount == 1
    _assert_scene_feature_support(cesium, "object.sector2d.geometry", "partial")
    _assert_scene_feature_support(simdis, "object.sector2d.geometry", "unsupported")
    _assert_scene_feature_support(soap, "object.sector2d.geometry", "unsupported")


def test_sector_volume_scene_assessment_reports_support() -> None:
    scene = load_scene_file(SECTOR_VOLUME_SCENE_EXAMPLE_PATH)
    cesium = assess_scene_for_target(scene, "cesium")
    simdis = assess_scene_for_target(scene, "simdis")
    soap = assess_scene_for_target(scene, "soap")
    assert cesium.objectCount == 1
    _assert_scene_feature_support(cesium, "object.sectorVolume.geometry", "partial")
    _assert_scene_feature_support(simdis, "object.sectorVolume.geometry", "unsupported")
    _assert_scene_feature_support(soap, "object.sectorVolume.geometry", "unsupported")


def test_hemisphere_scene_assessment_reports_support() -> None:
    scene = load_scene_file(HEMISPHERE_SCENE_EXAMPLE_PATH)
    cesium = assess_scene_for_target(scene, "cesium")
    simdis = assess_scene_for_target(scene, "simdis")
    soap = assess_scene_for_target(scene, "soap")
    assert cesium.objectCount == 1
    _assert_scene_feature_support(cesium, "object.hemisphere.geometry", "partial")
    _assert_scene_feature_support(simdis, "object.hemisphere.geometry", "unsupported")
    _assert_scene_feature_support(soap, "object.hemisphere.geometry", "unsupported")


def test_spherical_cap_scene_assessment_reports_support() -> None:
    scene = load_scene_file(SPHERICAL_CAP_SCENE_EXAMPLE_PATH)
    cesium = assess_scene_for_target(scene, "cesium")
    simdis = assess_scene_for_target(scene, "simdis")
    soap = assess_scene_for_target(scene, "soap")
    assert cesium.objectCount == 1
    _assert_scene_feature_support(cesium, "object.sphericalCap.geometry", "partial")
    _assert_scene_feature_support(simdis, "object.sphericalCap.geometry", "unsupported")
    _assert_scene_feature_support(soap, "object.sphericalCap.geometry", "unsupported")


def test_keyhole_scene_assessment_reports_support() -> None:
    scene = load_scene_file(KEYHOLE_SCENE_EXAMPLE_PATH)
    cesium = assess_scene_for_target(scene, "cesium")
    simdis = assess_scene_for_target(scene, "simdis")
    soap = assess_scene_for_target(scene, "soap")
    assert cesium.objectCount == 1
    _assert_scene_feature_support(cesium, "object.keyhole.geometry", "partial")
    _assert_scene_feature_support(simdis, "object.keyhole.geometry", "unsupported")
    _assert_scene_feature_support(soap, "object.keyhole.geometry", "unsupported")


def test_frustum_scene_assessment_reports_support() -> None:
    scene = load_scene_file(FRUSTUM_SCENE_EXAMPLE_PATH)
    cesium = assess_scene_for_target(scene, "cesium")
    simdis = assess_scene_for_target(scene, "simdis")
    soap = assess_scene_for_target(scene, "soap")
    assert cesium.objectCount == 1
    _assert_scene_feature_support(cesium, "object.frustum.geometry", "partial")
    _assert_scene_feature_support(simdis, "object.frustum.geometry", "unsupported")
    _assert_scene_feature_support(soap, "object.frustum.geometry", "unsupported")


def test_polyline_volume_scene_assessment_reports_support() -> None:
    scene = load_scene_file(POLYLINE_VOLUME_SCENE_EXAMPLE_PATH)
    assessment = assess_scene_for_target(scene, "cesium")
    assert assessment.objectCount == 1
    _assert_scene_feature_support(assessment, "object.polylineVolume.geometry", "strong")


def test_plane_scene_assessment_reports_plane_support() -> None:
    scene = load_scene_file(PLANE_SCENE_EXAMPLE_PATH)
    assessment = assess_scene_for_target(scene, "cesium")
    assert assessment.objectCount == 1
    _assert_scene_feature_support(assessment, "object.plane.geometry", "strong")


def test_tileset_scene_assessment_reports_tileset_support() -> None:
    scene = load_scene_file(TILESET_SCENE_EXAMPLE_PATH)
    assessment = assess_scene_for_target(scene, "cesium")
    simdis = assess_scene_for_target(scene, "simdis")
    soap = assess_scene_for_target(scene, "soap")
    assert assessment.objectCount == 1
    _assert_scene_feature_support(assessment, "object.tileset.geometry", "strong")
    _assert_scene_feature_support(simdis, "object.tileset.geometry", "unsupported")
    _assert_scene_feature_support(soap, "object.tileset.geometry", "unsupported")


def test_view_scene_assessment_reports_view_support() -> None:
    scene = load_scene_file(VIEW_SCENE_EXAMPLE_PATH)
    cesium = assess_scene_for_target(scene, "cesium")
    assert cesium.objectCount == 2
    _assert_scene_feature_support(cesium, "views", "partial")
    _assert_scene_feature_support(cesium, "cameraView", "partial")


def test_camera_view_scene_assessment_reports_camera_view_support() -> None:
    scene = load_scene_file(VIEW_SCENE_EXAMPLE_PATH)
    cesium = assess_scene_for_target(scene, "cesium")
    simdis = assess_scene_for_target(scene, "simdis")
    soap = assess_scene_for_target(scene, "soap")
    assert cesium.objectCount == 2
    _assert_scene_feature_support(cesium, "cameraView", "partial")
    _assert_scene_feature_support(simdis, "cameraView", "unsupported")
    _assert_scene_feature_support(soap, "cameraView", "unsupported")


def test_vector_scene_assessment_reports_vector_support() -> None:
    scene = load_scene_file(VECTOR_SCENE_EXAMPLE_PATH)
    cesium = assess_scene_for_target(scene, "cesium")
    simdis = assess_scene_for_target(scene, "simdis")
    soap = assess_scene_for_target(scene, "soap")
    assert cesium.objectCount == 1
    _assert_scene_feature_support(cesium, "object.vector.geometry", "strong")
    _assert_scene_feature_support(simdis, "object.vector.geometry", "unsupported")
    _assert_scene_feature_support(soap, "object.vector.geometry", "unsupported")


def test_velocity_vector_scene_assessment_reports_velocity_vector_support() -> None:
    scene = load_scene_file(VELOCITY_VECTOR_SCENE_EXAMPLE_PATH)
    cesium = assess_scene_for_target(scene, "cesium")
    simdis = assess_scene_for_target(scene, "simdis")
    soap = assess_scene_for_target(scene, "soap")
    assert cesium.objectCount == 1
    _assert_scene_feature_support(cesium, "object.velocityVector.geometry", "strong")
    _assert_scene_feature_support(simdis, "object.velocityVector.geometry", "unsupported")
    _assert_scene_feature_support(soap, "object.velocityVector.geometry", "unsupported")


def test_acceleration_vector_scene_assessment_reports_acceleration_vector_support() -> None:
    scene = load_scene_file(ACCELERATION_VECTOR_SCENE_EXAMPLE_PATH)
    cesium = assess_scene_for_target(scene, "cesium")
    simdis = assess_scene_for_target(scene, "simdis")
    soap = assess_scene_for_target(scene, "soap")
    assert cesium.objectCount == 1
    _assert_scene_feature_support(cesium, "object.accelerationVector.geometry", "strong")
    _assert_scene_feature_support(simdis, "object.accelerationVector.geometry", "unsupported")
    _assert_scene_feature_support(soap, "object.accelerationVector.geometry", "unsupported")


def test_line_of_sight_scene_assessment_reports_support() -> None:
    scene = load_scene_file(LINE_OF_SIGHT_SCENE_EXAMPLE_PATH)
    cesium = assess_scene_for_target(scene, "cesium")
    simdis = assess_scene_for_target(scene, "simdis")
    soap = assess_scene_for_target(scene, "soap")
    assert cesium.objectCount == 1
    _assert_scene_feature_support(cesium, "object.lineOfSight.geometry", "strong")
    _assert_scene_feature_support(simdis, "object.lineOfSight.geometry", "unsupported")
    _assert_scene_feature_support(soap, "object.lineOfSight.geometry", "unsupported")


def test_axes_scene_assessment_reports_support() -> None:
    scene = load_scene_file(AXES_SCENE_EXAMPLE_PATH)
    cesium = assess_scene_for_target(scene, "cesium")
    simdis = assess_scene_for_target(scene, "simdis")
    soap = assess_scene_for_target(scene, "soap")
    assert cesium.objectCount == 2
    _assert_scene_feature_support(cesium, "object.bodyAxes.geometry", "strong")
    _assert_scene_feature_support(cesium, "object.principalAxes.geometry", "strong")
    _assert_scene_feature_support(simdis, "object.bodyAxes.geometry", "unsupported")
    _assert_scene_feature_support(simdis, "object.principalAxes.geometry", "unsupported")
    _assert_scene_feature_support(soap, "object.bodyAxes.geometry", "unsupported")
    _assert_scene_feature_support(soap, "object.principalAxes.geometry", "unsupported")


def test_relative_intercept_scene_assessment_reports_support() -> None:
    scene = load_scene_file(RELATIVE_INTERCEPT_SCENE_EXAMPLE_PATH)
    cesium = assess_scene_for_target(scene, "cesium")
    simdis = assess_scene_for_target(scene, "simdis")
    soap = assess_scene_for_target(scene, "soap")
    assert cesium.objectCount == 2
    _assert_scene_feature_support(cesium, "object.relativeLine.geometry", "strong")
    _assert_scene_feature_support(cesium, "object.interceptLine.geometry", "strong")
    _assert_scene_feature_support(simdis, "object.relativeLine.geometry", "unsupported")
    _assert_scene_feature_support(simdis, "object.interceptLine.geometry", "unsupported")
    _assert_scene_feature_support(soap, "object.relativeLine.geometry", "unsupported")
    _assert_scene_feature_support(soap, "object.interceptLine.geometry", "unsupported")


def test_ellipsoid_sphere_scene_assessment_reports_support() -> None:
    scene = load_scene_file(ELLIPSOID_SPHERE_SCENE_EXAMPLE_PATH)
    assessment = assess_scene_for_target(scene, "cesium")
    assert assessment.objectCount == 2
    _assert_scene_feature_support(assessment, "object.ellipsoid.geometry", "strong")
    _assert_scene_feature_support(assessment, "object.sphere.geometry", "strong")
