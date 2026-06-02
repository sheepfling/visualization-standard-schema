from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vss import load_message_file, load_scene_file
from vss.targets import (
    compile_cesium_document,
    compile_cesium_scene,
    compile_simdis_lines,
    compile_soap_envelope,
    write_cesium_viewer,
)
from vss.util import dumps_json, write_text_file


def main() -> None:
    message = load_message_file("examples/cesium/air-track.json")
    scene = load_scene_file("examples/scenes/air-pair.scene.json")
    mixed_scene = load_scene_file("examples/scenes/mixed-ops.scene.json")
    path_scene = load_scene_file("examples/scenes/path-demo.scene.json")
    track_scene = load_scene_file("examples/scenes/track-demo.scene.json")
    rectangle_scene = load_scene_file("examples/scenes/rectangle-demo.scene.json")
    corridor_scene = load_scene_file("examples/scenes/corridor-demo.scene.json")
    ellipse_circle_scene = load_scene_file("examples/scenes/ellipse-circle-demo.scene.json")
    uncertainty_covariance_scene = load_scene_file("examples/scenes/uncertainty-covariance-demo.scene.json")
    particle_system_scene = load_scene_file("examples/scenes/particle-system-demo.scene.json")
    voxel_scene = load_scene_file("examples/scenes/voxel-demo.scene.json")
    runtime_subclasses_scene = load_scene_file("examples/scenes/runtime-subclasses-demo.scene.json")
    attachment_runtime_scene = load_scene_file("examples/scenes/attachment-runtime-demo.scene.json")
    shader_stage_scene = load_scene_file("examples/scenes/shader-stage-demo.scene.json")
    range_ring_scene = load_scene_file("examples/scenes/range-ring-demo.scene.json")
    bearing_fan_scene = load_scene_file("examples/scenes/bearing-fan-demo.scene.json")
    fan_scene = load_scene_file("examples/scenes/fan-demo.scene.json")
    custom_pattern_sensor_scene = load_scene_file("examples/scenes/custom-pattern-sensor-demo.scene.json")
    wall_scene = load_scene_file("examples/scenes/wall-demo.scene.json")
    box_scene = load_scene_file("examples/scenes/box-demo.scene.json")
    cylinder_scene = load_scene_file("examples/scenes/cylinder-demo.scene.json")
    cone_scene = load_scene_file("examples/scenes/cone-demo.scene.json")
    conic_sensor_scene = load_scene_file("examples/scenes/conic-sensor-demo.scene.json")
    custom_pattern_sensor_scene = load_scene_file("examples/scenes/custom-pattern-sensor-demo.scene.json")
    rectangular_sensor_scene = load_scene_file("examples/scenes/rectangular-sensor-demo.scene.json")
    sector2d_scene = load_scene_file("examples/scenes/sector2d-demo.scene.json")
    sector_volume_scene = load_scene_file("examples/scenes/sectorVolume-demo.scene.json")
    hemisphere_scene = load_scene_file("examples/scenes/hemisphere-demo.scene.json")
    keyhole_scene = load_scene_file("examples/scenes/keyhole-demo.scene.json")
    frustum_scene = load_scene_file("examples/scenes/frustum-demo.scene.json")
    spherical_cap_scene = load_scene_file("examples/scenes/sphericalcap-demo.scene.json")
    polyline_volume_scene = load_scene_file("examples/scenes/polyline-volume-demo.scene.json")
    plane_scene = load_scene_file("examples/scenes/plane-demo.scene.json")
    tileset_scene = load_scene_file("examples/scenes/tileset-demo.scene.json")
    vector_scene = load_scene_file("examples/scenes/vector-demo.scene.json")
    velocity_vector_scene = load_scene_file("examples/scenes/velocity-vector-demo.scene.json")
    acceleration_vector_scene = load_scene_file("examples/scenes/acceleration-vector-demo.scene.json")
    line_of_sight_scene = load_scene_file("examples/scenes/line-of-sight-demo.scene.json")
    relative_intercept_scene = load_scene_file("examples/scenes/relative-intercept-demo.scene.json")
    axes_scene = load_scene_file("examples/scenes/axes-demo.scene.json")
    view_scene = load_scene_file("examples/scenes/view-demo.scene.json")
    ellipsoid_sphere_scene = load_scene_file("examples/scenes/ellipsoid-sphere-demo.scene.json")
    out_dir = Path("examples/generated")
    out_dir.mkdir(parents=True, exist_ok=True)

    write_text_file(
        out_dir / "air-track.czml.json",
        dumps_json(compile_cesium_document(message), indent=2),
        encoding="utf-8",
    )
    write_cesium_viewer(
        out_dir / "air-track.viewer.html",
        czml_path="./air-track.czml.json",
        title="VSS Air Track Viewer",
    )
    write_text_file(
        out_dir / "air-pair.scene.czml.json",
        dumps_json(compile_cesium_scene(scene), indent=2),
        encoding="utf-8",
    )
    write_cesium_viewer(
        out_dir / "air-pair.scene.viewer.html",
        czml_path="./air-pair.scene.czml.json",
        title="VSS Air Pair Scene Viewer",
        views=scene.views,
    )
    write_text_file(
        out_dir / "mixed-ops.scene.czml.json",
        dumps_json(compile_cesium_scene(mixed_scene), indent=2),
        encoding="utf-8",
    )
    write_cesium_viewer(
        out_dir / "mixed-ops.scene.viewer.html",
        czml_path="./mixed-ops.scene.czml.json",
        title="VSS Mixed Ops Scene Viewer",
    )
    write_text_file(
        out_dir / "path-demo.scene.czml.json",
        dumps_json(compile_cesium_scene(path_scene), indent=2),
        encoding="utf-8",
    )
    write_cesium_viewer(
        out_dir / "path-demo.scene.viewer.html",
        czml_path="./path-demo.scene.czml.json",
        title="VSS Path Demo Scene Viewer",
    )
    write_text_file(
        out_dir / "track-demo.scene.czml.json",
        dumps_json(compile_cesium_scene(track_scene), indent=2),
        encoding="utf-8",
    )
    write_cesium_viewer(
        out_dir / "track-demo.scene.viewer.html",
        czml_path="./track-demo.scene.czml.json",
        title="VSS Track Demo Scene Viewer",
    )
    write_text_file(
        out_dir / "rectangle-demo.scene.czml.json",
        dumps_json(compile_cesium_scene(rectangle_scene), indent=2),
        encoding="utf-8",
    )
    write_cesium_viewer(
        out_dir / "rectangle-demo.scene.viewer.html",
        czml_path="./rectangle-demo.scene.czml.json",
        title="VSS Rectangle Demo Scene Viewer",
    )
    write_text_file(
        out_dir / "corridor-demo.scene.czml.json",
        dumps_json(compile_cesium_scene(corridor_scene), indent=2),
        encoding="utf-8",
    )
    write_cesium_viewer(
        out_dir / "corridor-demo.scene.viewer.html",
        czml_path="./corridor-demo.scene.czml.json",
        title="VSS Corridor Demo Scene Viewer",
    )
    write_text_file(
        out_dir / "ellipse-circle-demo.scene.czml.json",
        dumps_json(compile_cesium_scene(ellipse_circle_scene), indent=2),
        encoding="utf-8",
    )
    write_cesium_viewer(
        out_dir / "ellipse-circle-demo.scene.viewer.html",
        czml_path="./ellipse-circle-demo.scene.czml.json",
        title="VSS Ellipse Circle Demo Scene Viewer",
    )
    write_text_file(
        out_dir / "uncertainty-covariance-demo.scene.czml.json",
        dumps_json(compile_cesium_scene(uncertainty_covariance_scene), indent=2),
        encoding="utf-8",
    )
    write_cesium_viewer(
        out_dir / "uncertainty-covariance-demo.scene.viewer.html",
        czml_path="./uncertainty-covariance-demo.scene.czml.json",
        title="VSS Uncertainty Covariance Demo Scene Viewer",
    )
    write_text_file(
        out_dir / "particle-system-demo.scene.czml.json",
        dumps_json(compile_cesium_scene(particle_system_scene), indent=2),
        encoding="utf-8",
    )
    write_cesium_viewer(
        out_dir / "particle-system-demo.scene.viewer.html",
        czml_path="./particle-system-demo.scene.czml.json",
        title="VSS Particle System Demo Scene Viewer",
    )
    write_text_file(
        out_dir / "voxel-demo.scene.czml.json",
        dumps_json(compile_cesium_scene(voxel_scene), indent=2),
        encoding="utf-8",
    )
    write_cesium_viewer(
        out_dir / "voxel-demo.scene.viewer.html",
        czml_path="./voxel-demo.scene.czml.json",
        title="VSS Voxel Demo Scene Viewer",
    )
    write_text_file(
        out_dir / "runtime-subclasses-demo.scene.czml.json",
        dumps_json(compile_cesium_scene(runtime_subclasses_scene), indent=2),
        encoding="utf-8",
    )
    write_cesium_viewer(
        out_dir / "runtime-subclasses-demo.scene.viewer.html",
        czml_path="./runtime-subclasses-demo.scene.czml.json",
        title="VSS Runtime Subclasses Demo Scene Viewer",
    )
    write_text_file(
        out_dir / "attachment-runtime-demo.scene.czml.json",
        dumps_json(compile_cesium_scene(attachment_runtime_scene), indent=2),
        encoding="utf-8",
    )
    write_cesium_viewer(
        out_dir / "attachment-runtime-demo.scene.viewer.html",
        czml_path="./attachment-runtime-demo.scene.czml.json",
        title="VSS Attachment Runtime Demo Scene Viewer",
    )
    write_text_file(
        out_dir / "shader-stage-demo.scene.czml.json",
        dumps_json(compile_cesium_scene(shader_stage_scene), indent=2),
        encoding="utf-8",
    )
    write_cesium_viewer(
        out_dir / "shader-stage-demo.scene.viewer.html",
        czml_path="./shader-stage-demo.scene.czml.json",
        title="VSS Shader Stage Demo Scene Viewer",
    )
    write_text_file(
        out_dir / "range-ring-demo.scene.czml.json",
        dumps_json(compile_cesium_scene(range_ring_scene), indent=2),
        encoding="utf-8",
    )
    write_cesium_viewer(
        out_dir / "range-ring-demo.scene.viewer.html",
        czml_path="./range-ring-demo.scene.czml.json",
        title="VSS Range Ring Demo Scene Viewer",
    )
    write_text_file(
        out_dir / "bearing-fan-demo.scene.czml.json",
        dumps_json(compile_cesium_scene(bearing_fan_scene), indent=2),
        encoding="utf-8",
    )
    write_cesium_viewer(
        out_dir / "bearing-fan-demo.scene.viewer.html",
        czml_path="./bearing-fan-demo.scene.czml.json",
        title="VSS Bearing Fan Demo Scene Viewer",
    )
    write_text_file(
        out_dir / "fan-demo.scene.czml.json",
        dumps_json(compile_cesium_scene(fan_scene), indent=2),
        encoding="utf-8",
    )
    write_cesium_viewer(
        out_dir / "fan-demo.scene.viewer.html",
        czml_path="./fan-demo.scene.czml.json",
        title="VSS Fan Demo Scene Viewer",
    )
    write_text_file(
        out_dir / "custom-pattern-sensor-demo.scene.czml.json",
        dumps_json(compile_cesium_scene(custom_pattern_sensor_scene), indent=2),
        encoding="utf-8",
    )
    write_cesium_viewer(
        out_dir / "custom-pattern-sensor-demo.scene.viewer.html",
        czml_path="./custom-pattern-sensor-demo.scene.czml.json",
        title="VSS Custom Pattern Sensor Demo Scene Viewer",
    )
    write_text_file(
        out_dir / "wall-demo.scene.czml.json",
        dumps_json(compile_cesium_scene(wall_scene), indent=2),
        encoding="utf-8",
    )
    write_cesium_viewer(
        out_dir / "wall-demo.scene.viewer.html",
        czml_path="./wall-demo.scene.czml.json",
        title="VSS Wall Demo Scene Viewer",
    )
    write_text_file(
        out_dir / "box-demo.scene.czml.json",
        dumps_json(compile_cesium_scene(box_scene), indent=2),
        encoding="utf-8",
    )
    write_cesium_viewer(
        out_dir / "box-demo.scene.viewer.html",
        czml_path="./box-demo.scene.czml.json",
        title="VSS Box Demo Scene Viewer",
    )
    write_text_file(
        out_dir / "cylinder-demo.scene.czml.json",
        dumps_json(compile_cesium_scene(cylinder_scene), indent=2),
        encoding="utf-8",
    )
    write_cesium_viewer(
        out_dir / "cylinder-demo.scene.viewer.html",
        czml_path="./cylinder-demo.scene.czml.json",
        title="VSS Cylinder Demo Scene Viewer",
    )
    write_text_file(
        out_dir / "cone-demo.scene.czml.json",
        dumps_json(compile_cesium_scene(cone_scene), indent=2),
        encoding="utf-8",
    )
    write_cesium_viewer(
        out_dir / "cone-demo.scene.viewer.html",
        czml_path="./cone-demo.scene.czml.json",
        title="VSS Cone Demo Scene Viewer",
    )
    write_text_file(
        out_dir / "conic-sensor-demo.scene.czml.json",
        dumps_json(compile_cesium_scene(conic_sensor_scene), indent=2),
        encoding="utf-8",
    )
    write_cesium_viewer(
        out_dir / "conic-sensor-demo.scene.viewer.html",
        czml_path="./conic-sensor-demo.scene.czml.json",
        title="VSS Conic Sensor Demo Scene Viewer",
    )
    write_text_file(
        out_dir / "custom-pattern-sensor-demo.scene.czml.json",
        dumps_json(compile_cesium_scene(custom_pattern_sensor_scene), indent=2),
        encoding="utf-8",
    )
    write_cesium_viewer(
        out_dir / "custom-pattern-sensor-demo.scene.viewer.html",
        czml_path="./custom-pattern-sensor-demo.scene.czml.json",
        title="VSS Custom Pattern Sensor Demo Scene Viewer",
    )
    write_text_file(
        out_dir / "frustum-demo.scene.czml.json",
        dumps_json(compile_cesium_scene(frustum_scene), indent=2),
        encoding="utf-8",
    )
    write_cesium_viewer(
        out_dir / "frustum-demo.scene.viewer.html",
        czml_path="./frustum-demo.scene.czml.json",
        title="VSS Frustum Demo Scene Viewer",
    )
    write_text_file(
        out_dir / "sphericalcap-demo.scene.czml.json",
        dumps_json(compile_cesium_scene(spherical_cap_scene), indent=2),
        encoding="utf-8",
    )
    write_cesium_viewer(
        out_dir / "sphericalcap-demo.scene.viewer.html",
        czml_path="./sphericalcap-demo.scene.czml.json",
        title="VSS Spherical Cap Demo Scene Viewer",
    )
    write_text_file(
        out_dir / "rectangular-sensor-demo.scene.czml.json",
        dumps_json(compile_cesium_scene(rectangular_sensor_scene), indent=2),
        encoding="utf-8",
    )
    write_cesium_viewer(
        out_dir / "rectangular-sensor-demo.scene.viewer.html",
        czml_path="./rectangular-sensor-demo.scene.czml.json",
        title="VSS Rectangular Sensor Demo Scene Viewer",
    )
    write_text_file(
        out_dir / "sector2d-demo.scene.czml.json",
        dumps_json(compile_cesium_scene(sector2d_scene), indent=2),
        encoding="utf-8",
    )
    write_cesium_viewer(
        out_dir / "sector2d-demo.scene.viewer.html",
        czml_path="./sector2d-demo.scene.czml.json",
        title="VSS Sector 2D Demo Scene Viewer",
    )
    write_text_file(
        out_dir / "sectorVolume-demo.scene.czml.json",
        dumps_json(compile_cesium_scene(sector_volume_scene), indent=2),
        encoding="utf-8",
    )
    write_cesium_viewer(
        out_dir / "sectorVolume-demo.scene.viewer.html",
        czml_path="./sectorVolume-demo.scene.czml.json",
        title="VSS Sector Volume Demo Scene Viewer",
    )
    write_text_file(
        out_dir / "hemisphere-demo.scene.czml.json",
        dumps_json(compile_cesium_scene(hemisphere_scene), indent=2),
        encoding="utf-8",
    )
    write_cesium_viewer(
        out_dir / "hemisphere-demo.scene.viewer.html",
        czml_path="./hemisphere-demo.scene.czml.json",
        title="VSS Hemisphere Demo Scene Viewer",
    )
    write_text_file(
        out_dir / "keyhole-demo.scene.czml.json",
        dumps_json(compile_cesium_scene(keyhole_scene), indent=2),
        encoding="utf-8",
    )
    write_cesium_viewer(
        out_dir / "keyhole-demo.scene.viewer.html",
        czml_path="./keyhole-demo.scene.czml.json",
        title="VSS Keyhole Demo Scene Viewer",
    )
    write_text_file(
        out_dir / "polyline-volume-demo.scene.czml.json",
        dumps_json(compile_cesium_scene(polyline_volume_scene), indent=2),
        encoding="utf-8",
    )
    write_cesium_viewer(
        out_dir / "polyline-volume-demo.scene.viewer.html",
        czml_path="./polyline-volume-demo.scene.czml.json",
        title="VSS Polyline Volume Demo Scene Viewer",
    )
    write_text_file(
        out_dir / "plane-demo.scene.czml.json",
        dumps_json(compile_cesium_scene(plane_scene), indent=2),
        encoding="utf-8",
    )
    write_cesium_viewer(
        out_dir / "plane-demo.scene.viewer.html",
        czml_path="./plane-demo.scene.czml.json",
        title="VSS Plane Demo Scene Viewer",
    )
    write_text_file(
        out_dir / "tileset-demo.scene.czml.json",
        dumps_json(compile_cesium_scene(tileset_scene), indent=2),
        encoding="utf-8",
    )
    write_cesium_viewer(
        out_dir / "tileset-demo.scene.viewer.html",
        czml_path="./tileset-demo.scene.czml.json",
        title="VSS Tileset Demo Scene Viewer",
    )
    write_text_file(
        out_dir / "sector-volume-demo.scene.czml.json",
        dumps_json(compile_cesium_scene(sector_volume_scene), indent=2),
        encoding="utf-8",
    )
    write_cesium_viewer(
        out_dir / "sector-volume-demo.scene.viewer.html",
        czml_path="./sector-volume-demo.scene.czml.json",
        title="VSS Sector Volume Demo Scene Viewer",
    )
    write_text_file(
        out_dir / "hemisphere-demo.scene.czml.json",
        dumps_json(compile_cesium_scene(hemisphere_scene), indent=2),
        encoding="utf-8",
    )
    write_cesium_viewer(
        out_dir / "hemisphere-demo.scene.viewer.html",
        czml_path="./hemisphere-demo.scene.czml.json",
        title="VSS Hemisphere Demo Scene Viewer",
    )
    write_text_file(
        out_dir / "vector-demo.scene.czml.json",
        dumps_json(compile_cesium_scene(vector_scene), indent=2),
        encoding="utf-8",
    )
    write_cesium_viewer(
        out_dir / "vector-demo.scene.viewer.html",
        czml_path="./vector-demo.scene.czml.json",
        title="VSS Vector Demo Scene Viewer",
    )
    write_text_file(
        out_dir / "velocity-vector-demo.scene.czml.json",
        dumps_json(compile_cesium_scene(velocity_vector_scene), indent=2),
        encoding="utf-8",
    )
    write_cesium_viewer(
        out_dir / "velocity-vector-demo.scene.viewer.html",
        czml_path="./velocity-vector-demo.scene.czml.json",
        title="VSS Velocity Vector Demo Scene Viewer",
    )
    write_text_file(
        out_dir / "acceleration-vector-demo.scene.czml.json",
        dumps_json(compile_cesium_scene(acceleration_vector_scene), indent=2),
        encoding="utf-8",
    )
    write_cesium_viewer(
        out_dir / "acceleration-vector-demo.scene.viewer.html",
        czml_path="./acceleration-vector-demo.scene.czml.json",
        title="VSS Acceleration Vector Demo Scene Viewer",
    )
    write_text_file(
        out_dir / "line-of-sight-demo.scene.czml.json",
        dumps_json(compile_cesium_scene(line_of_sight_scene), indent=2),
        encoding="utf-8",
    )
    write_cesium_viewer(
        out_dir / "line-of-sight-demo.scene.viewer.html",
        czml_path="./line-of-sight-demo.scene.czml.json",
        title="VSS Line of Sight Demo Scene Viewer",
    )
    write_text_file(
        out_dir / "relative-intercept-demo.scene.czml.json",
        dumps_json(compile_cesium_scene(relative_intercept_scene), indent=2),
        encoding="utf-8",
    )
    write_cesium_viewer(
        out_dir / "relative-intercept-demo.scene.viewer.html",
        czml_path="./relative-intercept-demo.scene.czml.json",
        title="VSS Relative Intercept Demo Scene Viewer",
    )
    write_text_file(
        out_dir / "axes-demo.scene.czml.json",
        dumps_json(compile_cesium_scene(axes_scene), indent=2),
        encoding="utf-8",
    )
    write_cesium_viewer(
        out_dir / "axes-demo.scene.viewer.html",
        czml_path="./axes-demo.scene.czml.json",
        title="VSS Axes Demo Scene Viewer",
    )
    write_text_file(
        out_dir / "view-demo.scene.czml.json",
        dumps_json(compile_cesium_scene(view_scene), indent=2),
        encoding="utf-8",
    )
    write_cesium_viewer(
        out_dir / "view-demo.scene.viewer.html",
        czml_path="./view-demo.scene.czml.json",
        title="VSS View Demo Scene Viewer",
        views=view_scene.views + view_scene.cameraViews,
    )
    write_text_file(
        out_dir / "ellipsoid-sphere-demo.scene.czml.json",
        dumps_json(compile_cesium_scene(ellipsoid_sphere_scene), indent=2),
        encoding="utf-8",
    )
    write_cesium_viewer(
        out_dir / "ellipsoid-sphere-demo.scene.viewer.html",
        czml_path="./ellipsoid-sphere-demo.scene.czml.json",
        title="VSS Ellipsoid Sphere Demo Scene Viewer",
    )
    write_text_file(
        out_dir / "air-track.simdis.txt",
        "\n".join(compile_simdis_lines(message)),
        encoding="utf-8",
    )
    write_text_file(
        out_dir / "air-track.soap.xml",
        compile_soap_envelope(message),
        encoding="utf-8",
    )
    print(out_dir)


if __name__ == "__main__":
    main()
