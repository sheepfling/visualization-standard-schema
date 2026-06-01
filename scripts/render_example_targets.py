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
