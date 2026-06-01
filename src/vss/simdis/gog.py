from __future__ import annotations

import shlex
from typing import Any

from ..models import (
    SceneDocument,
    SceneEntity,
    SceneOverlay,
    ScenePolygon,
    ScenePolyline,
    Style,
    VssScene,
    Wgs84Position,
)
from ..util import float_or_default, format_float, to_bool, to_float
from .models import SimdisGogDocument, SimdisGogShape, SimdisGogVertex


def parse_simdis_gog_text(raw_text: str, *, source: str = "simdis-gog") -> SimdisGogDocument:
    shapes: list[SimdisGogShape] = []
    current: dict[str, Any] | None = None
    shape_index = 0

    for raw_line in raw_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        tokens = _tokenize(line)
        if not tokens:
            continue
        command = tokens[0].lower()

        if command in {"start", "start_gog", "start_annotation"}:
            if current is not None:
                shapes.append(_finalize_shape(current))
            shape_index += 1
            current = {
                "id": _shape_id(tokens, shape_index),
                "kind": "annotation" if command == "start_annotation" else None,
                "name": None,
                "vertices": [],
                "properties": {},
                "attachments": {},
            }
            continue

        if command in {"end", "end_gog", "end_annotation"}:
            if current is not None:
                shapes.append(_finalize_shape(current))
                current = None
            continue

        if current is None:
            continue

        _ingest_gog_command(current, tokens)

    if current is not None:
        shapes.append(_finalize_shape(current))

    return SimdisGogDocument(source=source, shapes=shapes)


def parse_simdis_gog_to_scene(
    raw_text: str,
    *,
    source: str = "simdis-gog",
    include_annotations: bool = True,
) -> VssScene:
    document = parse_simdis_gog_text(raw_text, source=source)
    objects: list[SceneEntity | SceneOverlay] = []

    for shape in document.shapes:
        if shape.kind == "annotation":
            if not include_annotations:
                continue
            entity = _shape_to_annotation(shape, source=source)
            if entity is not None:
                objects.append(entity)
            continue
        overlay = _shape_to_overlay(shape, source=source)
        if overlay is not None:
            objects.append(overlay)

    return VssScene(
        schemaVersion="1.0.0-scene",
        document=SceneDocument(
            id=source,
            name="SIMDIS GOG Scene",
            source=source,
        ),
        objects=objects,
    )


def render_simdis_gog_text(document: SimdisGogDocument) -> str:
    lines: list[str] = []
    if document.source:
        lines.append(f"# SIMDIS GOG export source={document.source}")
    for shape in document.shapes:
        lines.extend(_render_shape(shape))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _ingest_gog_command(current: dict[str, Any], tokens: tuple[str, ...]) -> None:
    command = tokens[0].lower()
    properties: dict[str, Any] = current["properties"]
    attachments: dict[str, Any] = current["attachments"]

    if current["kind"] is None and command in _SHAPE_COMMANDS:
        current["kind"] = command
        if command == "annotation" and len(tokens) > 1:
            current["properties"]["annotationText"] = tokens[1]
            current["name"] = tokens[1]
        return

    if command in _SHAPE_COMMANDS:
        current["kind"] = command
        if command == "annotation" and len(tokens) > 1:
            current["properties"]["annotationText"] = tokens[1]
            current["name"] = tokens[1]
        return

    if command in {"lla", "xyz", "point"}:
        mode = "xyz" if command == "xyz" else "lla"
        values = [_to_float(value) for value in tokens[1:4]]
        if all(value is not None for value in values):
            current["vertices"].append(SimdisGogVertex(mode=mode, values=[float(value) for value in values if value is not None]))
        return

    if command in {"centerlla", "centerxyz"}:
        mode = "xyz" if command == "centerxyz" else "lla"
        values = [_to_float(value) for value in tokens[1:4]]
        if all(value is not None for value in values):
            attachments["center"] = SimdisGogVertex(mode=mode, values=[float(value) for value in values if value is not None])
        return

    if command == "3d" and len(tokens) >= 3 and tokens[1].lower() == "name":
        current["name"] = tokens[2]
        return

    if command == "name" and len(tokens) > 1:
        current["name"] = tokens[1]
        return

    if command in {"filled", "outline"}:
        properties[command] = True if len(tokens) == 1 else _to_bool(tokens[1])
        return

    if command in {"linecolor", "fillcolor", "textoutlinecolor"}:
        properties[command] = _parse_color(tokens[1:])
        return

    if command in {"fontname", "textoutlinethickness", "lineprojection", "rangeunits", "angleunits", "altitudeunits", "imagefile"}:
        properties[command] = tokens[1] if len(tokens) > 1 else None
        return

    if command in {"fontsize", "linewidth", "pointsize", "opacity", "radius", "majoraxis", "minoraxis", "height", "innerradius", "anglestart", "angledeg"}:
        properties[command] = _to_float(tokens[1]) if len(tokens) > 1 else None
        return

    if command == "tessellate":
        properties[command] = _to_bool(tokens[1]) if len(tokens) > 1 else True
        return

    if command == "label" and len(tokens) > 1:
        properties[command] = tokens[1]
        return

    if command == "opacity" and len(tokens) > 1:
        properties[command] = _to_float(tokens[1])
        return

    if command == "latlonaltbox" and len(tokens) >= 7:
        values = [_to_float(value) for value in tokens[1:7]]
        if all(value is not None for value in values):
            properties[command] = [float(value) for value in values if value is not None]
        return

    if command == "imageoverlay" and len(tokens) >= 6:
        values = [_to_float(value) for value in tokens[1:6]]
        if all(value is not None for value in values):
            properties[command] = [float(value) for value in values if value is not None]
        return

    if command in {"center", "anchor", "position"} and len(tokens) >= 4:
        values = [_to_float(value) for value in tokens[1:4]]
        if all(value is not None for value in values):
            attachments[command] = [float(value) for value in values if value is not None]
        return

    properties.setdefault("rawCommands", []).append(list(tokens))


def _shape_to_annotation(shape: SimdisGogShape, *, source: str) -> SceneEntity | None:
    position = _first_lla_position(shape.vertices) or _center_position(shape.attachments.get("center"))
    if position is None:
        return None
    label = shape.name or shape.properties.get("label") or shape.id
    style = Style(label=label)
    return SceneEntity(
        objectType="entity",
        id=shape.id,
        name=label,
        position=position,
        style=style,
        attributes={"simdis": {"gog": shape.model_dump(mode="json", exclude_none=True)}},
        source=source,
        timestamp=None,
    )


def _shape_to_overlay(shape: SimdisGogShape, *, source: str) -> SceneOverlay | None:
    vertices = [_vertex_to_position(vertex) for vertex in shape.vertices if _vertex_to_position(vertex) is not None]
    if shape.kind in {"line", "linesegs", "polyline", "points"}:
        if len(vertices) == 1:
            vertices.append(vertices[0])
        if len(vertices) < 2:
            return None
        style = _shape_style(shape)
        return SceneOverlay(
            objectType="overlay",
            id=shape.id,
            name=shape.name or shape.id,
            position=vertices[0],
            geometryType="polyline",
            polyline=ScenePolyline(
                positions=vertices,
                widthPx=_float_or_default(shape.properties.get("linewidth"), 2.0),
                clampToGround=False,
            ),
            style=style,
            attributes={"simdis": {"gog": shape.model_dump(mode="json", exclude_none=True)}},
            source=source,
            timestamp=None,
        )
    if shape.kind in {"polygon", "poly"}:
        if len(vertices) < 3:
            return None
        style = _shape_style(shape)
        return SceneOverlay(
            objectType="overlay",
            id=shape.id,
            name=shape.name or shape.id,
            position=vertices[0],
            geometryType="polygon",
            polygon=ScenePolygon(
                positions=vertices,
                clampToGround=False,
            ),
            style=style,
            attributes={"simdis": {"gog": shape.model_dump(mode="json", exclude_none=True)}},
            source=source,
            timestamp=None,
        )
    return None


def _render_shape(shape: SimdisGogShape) -> list[str]:
    lines: list[str] = ["start"]
    if shape.kind == "annotation":
        annotation_text = shape.properties.get("annotationText") or shape.name or shape.id
        lines.append(f"annotation {_quote_text(str(annotation_text))}")
    else:
        lines.append(shape.kind)

    if shape.name and shape.kind != "annotation":
        lines.append(f'3d name {_quote_text(shape.name)}')
    elif shape.kind == "annotation" and shape.name and shape.properties.get("annotationText") != shape.name:
        lines.append(f'3d name {_quote_text(shape.name)}')

    for vertex in shape.vertices:
        lines.append(_render_vertex(vertex))

    center = shape.attachments.get("center")
    if isinstance(center, SimdisGogVertex):
        lines.append(_render_attachment("center", center))

    for attachment_name, attachment_value in shape.attachments.items():
        if attachment_name == "center":
            continue
        rendered_attachment = _render_generic_attachment(attachment_name, attachment_value)
        if rendered_attachment is not None:
            lines.append(rendered_attachment)

    lines.extend(_render_shape_properties(shape.properties))
    lines.extend(_render_raw_commands(shape.properties.get("rawCommands")))
    lines.append("end")
    return lines


def _shape_style(shape: SimdisGogShape) -> Style | None:
    color = shape.properties.get("linecolor") or shape.properties.get("fillcolor")
    rgba = color if isinstance(color, tuple) else None
    return Style(
        label=shape.name,
        colorRgba=rgba,
    )


def _shape_id(tokens: tuple[str, ...], shape_index: int) -> str:
    if len(tokens) > 1 and tokens[1]:
        return tokens[1]
    return f"gog-{shape_index:04d}"


def _finalize_shape(current: dict[str, Any]) -> SimdisGogShape:
    return SimdisGogShape(
        id=str(current["id"]),
        kind=str(current["kind"] or "unknown"),
        name=current.get("name"),
        vertices=list(current["vertices"]),
        properties=dict(current["properties"]),
        attachments=dict(current["attachments"]),
    )


def _shape_to_position(values: list[float], *, mode: str) -> Wgs84Position | None:
    if len(values) < 3:
        return None
    if mode == "lla":
        return Wgs84Position(latitudeDeg=values[0], longitudeDeg=values[1], altitudeM=values[2])
    return None


def _vertex_to_position(vertex: SimdisGogVertex) -> Wgs84Position | None:
    return _shape_to_position(vertex.values, mode=vertex.mode)


def _first_lla_position(vertices: list[SimdisGogVertex]) -> Wgs84Position | None:
    for vertex in vertices:
        position = _vertex_to_position(vertex)
        if position is not None:
            return position
    return None


def _center_position(value: Any) -> Wgs84Position | None:
    if not isinstance(value, SimdisGogVertex):
        return None
    return _vertex_to_position(value)


def _tokenize(raw_line: str) -> tuple[str, ...]:
    try:
        return tuple(shlex.split(raw_line, posix=True))
    except ValueError:
        return ()


def _render_shape_properties(properties: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    if properties.get("label") is not None:
        lines.append(f'label {_quote_text(str(properties["label"]))}')
    if properties.get("fontname") is not None:
        lines.append(f'fontname {_quote_text(str(properties["fontname"]))}')
    if properties.get("fontsize") is not None:
        lines.append(f'fontsize {_format_number(properties["fontsize"])}')
    for key in ("linecolor", "fillcolor", "textoutlinecolor"):
        if key in properties and properties[key] is not None:
            lines.append(f"{key} hex {_render_color(properties[key])}")
    if properties.get("textoutlinethickness") is not None:
        lines.append(f'textoutlinethickness {_quote_text(str(properties["textoutlinethickness"]))}')
    if properties.get("lineprojection") is not None:
        lines.append(f'lineprojection {_quote_text(str(properties["lineprojection"]))}')
    if properties.get("rangeunits") is not None:
        lines.append(f'rangeunits {_quote_text(str(properties["rangeunits"]))}')
    if properties.get("angleunits") is not None:
        lines.append(f'angleunits {_quote_text(str(properties["angleunits"]))}')
    if properties.get("altitudeunits") is not None:
        lines.append(f'altitudeunits {_quote_text(str(properties["altitudeunits"]))}')
    for key in ("pointsize", "linewidth", "opacity", "radius", "majoraxis", "minoraxis", "height", "innerradius", "anglestart", "angledeg", "fontsize"):
        if key in properties and properties[key] is not None and key not in {"fontsize"}:
            lines.append(f"{key} {_format_number(properties[key])}")
    for key in ("filled", "outline", "tessellate"):
        if properties.get(key) is not None:
            value = properties[key]
            lines.append(key if value is True else f"{key} {str(value).lower()}")
    if properties.get("imagefile") is not None:
        lines.append(f'imagefile {_quote_text(str(properties["imagefile"]))}')
    if properties.get("priority") is not None:
        lines.append(f'priority {_format_number(properties["priority"])}')
    return lines


def _render_raw_commands(raw_commands: Any) -> list[str]:
    if not isinstance(raw_commands, list):
        return []
    lines: list[str] = []
    for command in raw_commands:
        if isinstance(command, list) and command:
            lines.append(" ".join(_quote_token(token) for token in command))
    return lines


def _render_vertex(vertex: SimdisGogVertex) -> str:
    return _render_xyz_like(vertex.mode, vertex.values)


def _render_attachment(name: str, value: SimdisGogVertex) -> str:
    return _render_xyz_like(f"{name}lla" if value.mode == "lla" else f"{name}xyz", value.values)


def _render_generic_attachment(name: str, value: Any) -> str | None:
    if isinstance(value, SimdisGogVertex):
        return _render_attachment(name, value)
    if isinstance(value, list) and len(value) >= 3:
        return _render_xyz_like(name, value[:3])
    return None


def _render_xyz_like(command: str, values: list[float] | tuple[float, ...]) -> str:
    rendered_values = " ".join(_format_number(value) for value in values)
    return f"{command} {rendered_values}".rstrip()


def _render_color(value: Any) -> str:
    if not isinstance(value, tuple) or len(value) < 3:
        return "0x000000ff"
    red, green, blue = int(value[0]), int(value[1]), int(value[2])
    alpha = int(value[3]) if len(value) > 3 else 255
    return f"0x{alpha:02x}{red:02x}{green:02x}{blue:02x}"


def _quote_text(value: str) -> str:
    if value == "":
        return '""'
    if any(character.isspace() for character in value) or '"' in value:
        return f'"{value.replace("\\", "\\\\").replace("\"", "\\\"")}"'
    return value


def _quote_token(value: str) -> str:
    if not value:
        return '""'
    if any(character.isspace() for character in value) or any(character in value for character in ['"', "\\"]):
        return f'"{value.replace("\\", "\\\\").replace("\"", "\\\"")}"'
    return value


_format_number = format_float


def _parse_color(tokens: list[str]) -> tuple[int, int, int, int] | None:
    if not tokens:
        return None
    value = tokens[-1].lower()
    if value.startswith("0x"):
        value = value[2:]
    if len(value) == 8:
        alpha = int(value[0:2], 16)
        red = int(value[2:4], 16)
        green = int(value[4:6], 16)
        blue = int(value[6:8], 16)
        return red, green, blue, alpha
    if len(value) == 6:
        red = int(value[0:2], 16)
        green = int(value[2:4], 16)
        blue = int(value[4:6], 16)
        return red, green, blue, 255
    return None


_to_bool = to_bool
_to_float = to_float
_float_or_default = float_or_default


_SHAPE_COMMANDS = {
    "annotation",
    "points",
    "line",
    "linesegs",
    "polyline",
    "polygon",
    "poly",
    "circle",
    "arc",
    "ellipse",
    "sphere",
    "hemisphere",
    "cylinder",
    "cone",
    "ellipsoid",
    "imageoverlay",
    "latlonaltbox",
}
