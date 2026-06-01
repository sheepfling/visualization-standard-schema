from __future__ import annotations

import argparse
from pathlib import Path

from .capabilities import assess_scene_for_target, get_target_capabilities
from .convert import (
    emit_czml_from_scene,
    emit_orb_from_scene,
    emit_simdis_asi_from_scene,
    emit_soap_envelope_from_scene,
    parse_czml_file_to_scene,
    parse_orb_to_scene,
    parse_simdis_asi_to_scene,
    parse_simdis_bundle_to_scene,
    parse_soap_to_scene,
)
from .io import load_scene_file, write_scene_file
from .util import dumps_json, write_text_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="vss",
        description="Convert between VSS SDJ and SIMDIS/SOAP/ORB/CZML formats",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest = subparsers.add_parser("ingest", help="Convert foreign format into .sdj scene JSON")
    ingest.add_argument(
        "--input",
        "-i",
        required=True,
        help="Input path (simdis-asi text, simdis bundle directory, soap xml/bundle, orb text, or czml)",
    )
    ingest.add_argument("--output", "-o", required=True, help="Output .sdj path")
    ingest.add_argument(
        "--format",
        "-f",
        choices=("simdis-asi", "simdis-bundle", "soap", "orb", "czml"),
        default="czml",
        help="Format of input data",
    )
    ingest.set_defaults(handler=_ingest)

    emit = subparsers.add_parser("emit", help="Convert .sdj scene JSON into target format")
    emit.add_argument("--input", "-i", required=True, help="Input SDJ path")
    emit.add_argument("--output", "-o", required=True, help="Output path")
    emit.add_argument(
        "--format",
        "-f",
        choices=("simdis-asi", "soap", "orb", "czml"),
        default="czml",
        help="Output format",
    )
    emit.set_defaults(handler=_emit)

    capabilities = subparsers.add_parser("capabilities", help="Report target support against the current SDJ/VSS surface")
    capabilities.add_argument("--target", "-t", required=True, choices=("cesium", "simdis", "soap"))
    capabilities.add_argument("--input", "-i", help="Optional input SDJ scene path for per-scene assessment")
    capabilities.add_argument("--output", "-o", help="Optional output JSON path")
    capabilities.set_defaults(handler=_capabilities)

    args = parser.parse_args(argv)
    args.handler(args)
    return 0


def _ingest(args: argparse.Namespace) -> None:
    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"input not found: {input_path}")

    if args.format == "simdis-asi":
        scene = parse_simdis_asi_to_scene(input_path.read_text(encoding="utf-8"), source=input_path.stem)
    elif args.format == "simdis-bundle":
        scene = parse_simdis_bundle_to_scene(input_path, source=input_path.name)
    elif args.format == "soap":
        scene = parse_soap_to_scene(input_path, source=input_path.name)
    elif args.format == "orb":
        scene = parse_orb_to_scene(input_path)
    elif args.format == "czml":
        scene = parse_czml_file_to_scene(input_path)
    else:  # pragma: no cover - argparse prevents this branch
        raise ValueError(f"unsupported ingest format: {args.format}")

    write_scene_file(scene, args.output)


def _emit(args: argparse.Namespace) -> None:
    scene = load_scene_file(args.input)
    if args.format == "simdis-asi":
        text = emit_simdis_asi_from_scene(scene)
    elif args.format == "soap":
        text = emit_soap_envelope_from_scene(scene)
    elif args.format == "orb":
        text = emit_orb_from_scene(scene)
    elif args.format == "czml":
        text = emit_czml_from_scene(scene)
    else:  # pragma: no cover - argparse prevents this branch
        raise ValueError(f"unsupported emit format: {args.format}")

    write_text_file(args.output, text, encoding="utf-8")


def _capabilities(args: argparse.Namespace) -> None:
    payload: dict[str, object] = {
        "capabilities": get_target_capabilities(args.target).model_dump(mode="json", exclude_none=True)
    }
    if args.input:
        scene = load_scene_file(args.input)
        payload["assessment"] = assess_scene_for_target(scene, args.target).model_dump(mode="json", exclude_none=True)
    rendered = dumps_json(payload, indent=2)
    if args.output:
        write_text_file(args.output, rendered, encoding="utf-8")
        return
    print(rendered)


if __name__ == "__main__":
    raise SystemExit(main())
