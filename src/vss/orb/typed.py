from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TypeAlias

from .models import OrbDefineBlock, OrbDocument, OrbLine

OrbPrimitive: TypeAlias = bool | int | float | str
OrbValue: TypeAlias = OrbPrimitive | tuple[OrbPrimitive, ...]


@dataclass(slots=True)
class OrbUnits:
    distance: str | None = None
    time: str | None = None
    angle: str | None = None
    angle_shift: bool | None = None
    distance_y: str | None = None
    time_y: str | None = None
    angle_y: str | None = None
    angle_shift_y: bool | None = None
    extra: dict[str, OrbValue] = field(default_factory=dict)


@dataclass(slots=True)
class OrbClock:
    epoch: tuple[OrbPrimitive, ...] | None = None
    simulation_time: OrbPrimitive | None = None
    pause: bool | None = None
    real_time: bool | None = None
    time_step: OrbPrimitive | None = None
    extra: dict[str, OrbValue] = field(default_factory=dict)


@dataclass(slots=True)
class OrbConfig:
    properties: dict[str, OrbValue] = field(default_factory=dict)
    clock_cone_grid: dict[str, OrbValue] = field(default_factory=dict)
    driver: dict[str, OrbValue] = field(default_factory=dict)


@dataclass(slots=True)
class OrbGroup:
    group_type: str | None = None
    name: str | None = None
    properties: dict[str, OrbValue] = field(default_factory=dict)
    lists: dict[str, list[OrbPrimitive]] = field(default_factory=dict)


@dataclass(slots=True)
class OrbPlatform:
    platform_type: str | None = None
    name: str | None = None
    state: tuple[OrbPrimitive, ...] | None = None
    properties: dict[str, OrbValue] = field(default_factory=dict)
    repeated: dict[str, list[OrbValue]] = field(default_factory=dict)


@dataclass(slots=True)
class OrbTrajectory:
    name: str | None = None
    properties: dict[str, OrbValue] = field(default_factory=dict)
    trajectory_rows: list[tuple[OrbPrimitive, ...]] = field(default_factory=list)


@dataclass(slots=True)
class OrbView:
    view_type: str | None = None
    name: str | None = None
    observer: str | None = None
    coordinate_system: str | None = None
    properties: dict[str, OrbValue] = field(default_factory=dict)
    sets: dict[str, OrbValue] = field(default_factory=dict)
    lists: dict[str, list[OrbPrimitive]] = field(default_factory=dict)


@dataclass(slots=True)
class OrbMapCenter:
    properties: dict[str, OrbValue] = field(default_factory=dict)


@dataclass(slots=True)
class OrbSpice:
    properties: dict[str, OrbValue] = field(default_factory=dict)
    repeated: dict[str, list[OrbValue]] = field(default_factory=dict)


@dataclass(slots=True)
class OrbCoordinateSystem:
    cs_type: str | None = None
    name: str | None = None
    properties: dict[str, OrbValue] = field(default_factory=dict)
    repeated: dict[str, list[OrbValue]] = field(default_factory=dict)


@dataclass(slots=True)
class OrbAnalysis:
    name: str | None = None
    properties: dict[str, OrbValue] = field(default_factory=dict)
    variable_details: dict[str, OrbValue] = field(default_factory=dict)


@dataclass(slots=True)
class OrbStabilization:
    name: str | None = None
    properties: dict[str, OrbValue] = field(default_factory=dict)


@dataclass(slots=True)
class OrbGrid:
    grid_type: str | None = None
    name: str | None = None
    properties: dict[str, OrbValue] = field(default_factory=dict)


@dataclass(slots=True)
class OrbScenario:
    document: OrbDocument
    revision: int | str | None = None
    file_type: str | None = None
    units: OrbUnits | None = None
    clock: OrbClock | None = None
    config: OrbConfig | None = None
    groups: list[OrbGroup] = field(default_factory=list)
    platforms: list[OrbPlatform] = field(default_factory=list)
    trajectories: list[OrbTrajectory] = field(default_factory=list)
    views: list[OrbView] = field(default_factory=list)
    map_centers: list[OrbMapCenter] = field(default_factory=list)
    spices: list[OrbSpice] = field(default_factory=list)
    coordinate_systems: list[OrbCoordinateSystem] = field(default_factory=list)
    analyses: list[OrbAnalysis] = field(default_factory=list)
    stabilizations: list[OrbStabilization] = field(default_factory=list)
    grids: list[OrbGrid] = field(default_factory=list)

    @classmethod
    def from_document(cls, document: OrbDocument) -> "OrbScenario":
        revision = _parse_revision(document)
        file_type = _parse_file_type(document)
        units_block = _find_define_block(document, "UNITS")
        clock_block = _find_define_block(document, "CLOCK")
        config_block = _find_define_block(document, "CONFIG")
        return cls(
            document=document,
            revision=revision,
            file_type=file_type,
            units=parse_units_block(units_block) if units_block else None,
            clock=parse_clock_block(clock_block) if clock_block else None,
            config=parse_config_block(config_block) if config_block else None,
            groups=[parse_group_block(block) for block in _find_define_blocks(document, "GROUP")],
            platforms=[parse_platform_block(block) for block in _find_define_blocks(document, "PLATFORM")],
            trajectories=[parse_trajectory_block(block) for block in _find_define_blocks(document, "TRAJECTORY")],
            views=[parse_view_block(block) for block in _find_define_blocks(document, "VIEW")],
            map_centers=[parse_mapcenter_block(block) for block in _find_define_blocks(document, "MAPCENTER")],
            spices=[parse_spice_block(block) for block in _find_define_blocks(document, "SPICE")],
            coordinate_systems=[parse_cs_block(block) for block in _find_define_blocks(document, "CS")],
            analyses=[parse_analysis_block(block) for block in _find_define_blocks(document, "ANALYSIS")],
            stabilizations=[parse_stabilization_block(block) for block in _find_define_blocks(document, "STABILIZATION")],
            grids=[parse_grid_block(block) for block in _find_define_blocks(document, "GRID")],
        )


def parse_units_block(block: OrbDefineBlock) -> OrbUnits:
    values = _collect_statement_map(block.children)
    return OrbUnits(
        distance=_coerce_string(values.pop("DISTANCE", None)),
        time=_coerce_string(values.pop("TIME", None)),
        angle=_coerce_string(values.pop("ANGLE", None)),
        angle_shift=_coerce_bool(values.pop("ANGLE_SHIFT", None)),
        distance_y=_coerce_string(values.pop("DISTANCE_Y", None)),
        time_y=_coerce_string(values.pop("TIME_Y", None)),
        angle_y=_coerce_string(values.pop("ANGLE_Y", None)),
        angle_shift_y=_coerce_bool(values.pop("ANGLE_SHIFT_Y", None)),
        extra=values,
    )


def parse_clock_block(block: OrbDefineBlock) -> OrbClock:
    values = _collect_statement_map(block.children)
    epoch_value = values.pop("EPOCH", None)
    epoch = None
    if isinstance(epoch_value, tuple):
        epoch = epoch_value
    elif epoch_value is not None:
        epoch = (epoch_value,)
    return OrbClock(
        epoch=epoch,
        simulation_time=_coerce_orb_scalar(values.pop("SIMULATION_TIME", None)),
        pause=_coerce_bool(values.pop("PAUSE", None)),
        real_time=_coerce_bool(values.pop("REAL_TIME", None)),
        time_step=_coerce_orb_scalar(values.pop("TIME_STEP", None)),
        extra=values,
    )


def parse_config_block(block: OrbDefineBlock) -> OrbConfig:
    properties: dict[str, OrbValue] = {}
    clock_cone_grid: dict[str, OrbValue] = {}
    driver: dict[str, OrbValue] = {}

    for child in block.children:
        keyword = child.keyword
        if keyword == "CLOCK_CONE_GRID":
            clock_cone_grid = _collect_statement_map(child.children, ignored_keywords={"GRID_END"})
            continue
        if keyword == "DRIVER":
            driver = _collect_statement_map(child.children, ignored_keywords={"DRIVER_END"})
            continue
        if keyword in {"GRID_END", "DRIVER_END"}:
            continue
        if keyword is not None:
            properties[keyword] = _statement_value(child)

    return OrbConfig(
        properties=properties,
        clock_cone_grid=clock_cone_grid,
        driver=driver,
    )


def parse_group_block(block: OrbDefineBlock) -> OrbGroup:
    define_tokens = block.define_tokens
    properties: dict[str, OrbValue] = {}
    lists: dict[str, list[OrbPrimitive]] = {}
    for child in block.children:
        keyword = child.keyword
        if keyword is None:
            continue
        if keyword.endswith("LIST"):
            tokens = child.tokens[1:]
            if tokens:
                properties[keyword] = _normalize_orb_value(_tokens_as_value(tokens))
            lists[keyword] = [_list_item_value(item) for item in child.children if item.tokens]
            continue
        properties[keyword] = _statement_value(child)

    return OrbGroup(
        group_type=_get_token(define_tokens, 1),
        name=_get_token(define_tokens, 2),
        properties=properties,
        lists=lists,
    )


def parse_platform_block(block: OrbDefineBlock) -> OrbPlatform:
    define_tokens = block.define_tokens
    properties: dict[str, OrbValue] = {}
    repeated: dict[str, list[OrbValue]] = {}
    state_tuple: tuple[OrbPrimitive, ...] | None = None

    for child in block.children:
        keyword = child.keyword
        if keyword is None:
            continue
        if keyword == "STATE":
            state = _statement_value(child)
            state_tuple = state if isinstance(state, tuple) else (state,)
            continue
        value = _statement_value(child)
        if keyword in repeated:
            repeated[keyword].append(value)
        elif keyword in properties:
            repeated[keyword] = [properties.pop(keyword), value]
        else:
            properties[keyword] = value

    return OrbPlatform(
        platform_type=_get_token(define_tokens, 1),
        name=_get_token(define_tokens, 2),
        state=state_tuple,
        properties=properties,
        repeated=repeated,
    )


def parse_trajectory_block(block: OrbDefineBlock) -> OrbTrajectory:
    properties: dict[str, OrbValue] = {}
    trajectory_rows: list[tuple[OrbPrimitive, ...]] = []

    for child in block.children:
        keyword = child.keyword
        if keyword is None:
            continue
        if keyword == "TRAJECTORY_CHOICE":
            properties[keyword] = _statement_value(child)
            for row in child.children:
                row_value = _parse_tokens(row.tokens)
                trajectory_rows.append(row_value if isinstance(row_value, tuple) else (row_value,))
            continue
        properties[keyword] = _statement_value(child)

    return OrbTrajectory(
        name=_get_token(block.define_tokens, 1),
        properties=properties,
        trajectory_rows=trajectory_rows,
    )


def parse_view_block(block: OrbDefineBlock) -> OrbView:
    define_tokens = block.define_tokens
    properties: dict[str, OrbValue] = {}
    sets: dict[str, OrbValue] = {}
    lists: dict[str, list[OrbPrimitive]] = {}

    for child in block.children:
        keyword = child.keyword
        if keyword is None:
            continue
        if child.children:
            set_value = _statement_value(child)
            sets[keyword] = True if set_value == "SET" else set_value
            for grandchild in child.children:
                grand_keyword = grandchild.keyword
                if grand_keyword and grand_keyword.endswith("LIST"):
                    list_header_tokens = grandchild.tokens[1:]
                    if list_header_tokens:
                        properties[grand_keyword] = _normalize_orb_value(_tokens_as_value(list_header_tokens))
                    lists[grand_keyword] = [_list_item_value(item) for item in grandchild.children if item.tokens]
            continue
        if keyword.endswith("LIST"):
            header_tokens = child.tokens[1:]
            if header_tokens:
                properties[keyword] = _normalize_orb_value(_tokens_as_value(header_tokens))
            lists[keyword] = [_list_item_value(item) for item in child.children if item.tokens]
            continue
        properties[keyword] = _statement_value(child)

    return OrbView(
        view_type=_get_token(define_tokens, 1),
        name=_get_token(define_tokens, 2),
        observer=_get_token(define_tokens, 3),
        coordinate_system=_get_token(define_tokens, 4),
        properties=properties,
        sets=sets,
        lists=lists,
    )


def parse_mapcenter_block(block: OrbDefineBlock) -> OrbMapCenter:
    return OrbMapCenter(properties=_collect_statement_map(block.children))


def parse_spice_block(block: OrbDefineBlock) -> OrbSpice:
    properties: dict[str, OrbValue] = {}
    repeated: dict[str, list[OrbValue]] = {}
    for child in block.children:
        keyword = child.keyword
        if keyword is None:
            continue
        value = _statement_value(child)
        if keyword in repeated:
            repeated[keyword].append(value)
        elif keyword in properties:
            repeated[keyword] = [properties.pop(keyword), value]
        else:
            properties[keyword] = value
    return OrbSpice(properties=properties, repeated=repeated)


def parse_cs_block(block: OrbDefineBlock) -> OrbCoordinateSystem:
    define_tokens = block.define_tokens
    properties: dict[str, OrbValue] = {}
    repeated: dict[str, list[OrbValue]] = {}
    for child in block.children:
        keyword = child.keyword
        if keyword is None:
            continue
        value = _statement_value(child)
        if keyword in repeated:
            repeated[keyword].append(value)
        elif keyword in properties:
            repeated[keyword] = [properties.pop(keyword), value]
        else:
            properties[keyword] = value
    return OrbCoordinateSystem(
        cs_type=_get_token(define_tokens, 1),
        name=_get_token(define_tokens, 2),
        properties=properties,
        repeated=repeated,
    )


def parse_analysis_block(block: OrbDefineBlock) -> OrbAnalysis:
    properties: dict[str, OrbValue] = {}
    variable_details: dict[str, OrbValue] = {}
    for child in block.children:
        keyword = child.keyword
        if keyword is None:
            continue
        if keyword == "VARIABLE":
            properties[keyword] = _statement_value(child)
            variable_details = _collect_statement_map(child.children)
            continue
        properties[keyword] = _statement_value(child)
    return OrbAnalysis(
        name=_get_token(block.define_tokens, 1),
        properties=properties,
        variable_details=variable_details,
    )


def parse_stabilization_block(block: OrbDefineBlock) -> OrbStabilization:
    return OrbStabilization(
        name=_get_token(block.define_tokens, 1),
        properties=_collect_statement_map(block.children),
    )


def parse_grid_block(block: OrbDefineBlock) -> OrbGrid:
    define_tokens = block.define_tokens
    return OrbGrid(
        grid_type=_get_token(define_tokens, 1),
        name=_get_token(define_tokens, 2),
        properties=_collect_statement_map(block.children),
    )


def _parse_revision(document: OrbDocument) -> int | str | None:
    if not document.entries:
        return None
    tokens = document.entries[0].tokens
    if len(tokens) == 2 and tokens[1].lower() == "revision":
        try:
            return int(tokens[0])
        except ValueError:
            return tokens[0]
    return None


def _parse_file_type(document: OrbDocument) -> str | None:
    if len(document.entries) < 2:
        return None
    tokens = document.entries[1].tokens
    return tokens[0] if tokens else None


def _find_define_block(document: OrbDocument, kind: str) -> OrbDefineBlock | None:
    for block in document.define_blocks:
        if block.block_kind == kind:
            return block
    return None


def _find_define_blocks(document: OrbDocument, kind: str) -> list[OrbDefineBlock]:
    return [block for block in document.define_blocks if block.block_kind == kind]


def _collect_statement_map(
    lines: list[OrbLine],
    *,
    ignored_keywords: set[str] | None = None,
) -> dict[str, OrbValue]:
    values: dict[str, OrbValue] = {}
    for line in lines:
        keyword = line.keyword
        if keyword is None:
            continue
        if ignored_keywords and keyword in ignored_keywords:
            continue
        values[keyword] = _statement_value(line)
    return values


def _statement_value(line: OrbLine) -> OrbValue:
    tokens = line.tokens[1:]
    if not tokens:
        return ""
    parsed = _parse_tokens(tokens)
    if len(parsed) == 1:
        return parsed[0]
    return parsed


def _parse_tokens(tokens: tuple[str, ...]) -> tuple[OrbPrimitive, ...]:
    parsed = tuple(_parse_primitive(token) for token in tokens)
    if len(parsed) == 1:
        return (parsed[0],)
    return parsed


def _tokens_as_value(tokens: tuple[str, ...]) -> OrbValue:
    parsed = _parse_tokens(tokens)
    if len(parsed) == 1:
        return parsed[0]
    return parsed


def _list_item_value(line: OrbLine) -> OrbPrimitive:
    tokens = line.tokens
    if not tokens:
        return ""
    return _parse_primitive(tokens[0])


def _parse_primitive(token: str) -> OrbPrimitive:
    if token == "ON":
        return True
    if token == "OFF":
        return False

    quoted = _parse_quoted_primitive(token)
    if quoted is not None:
        return quoted

    integer = _parse_int_primitive(token)
    if integer is not None:
        return integer

    floating = _parse_float_primitive(token)
    if floating is not None:
        return floating

    return token


def _parse_quoted_primitive(token: str) -> str | None:
    if len(token) < 2:
        return None
    if token[0] != token[-1]:
        return None
    if token[0] not in {'"', "'"}:
        return None
    return token[1:-1]


def _parse_int_primitive(token: str) -> int | None:
    digits = token[1:] if token[:1] in {"+", "-"} else token
    if not digits.isdigit():
        return None
    try:
        return int(token, 10)
    except ValueError:
        return None


def _parse_float_primitive(token: str) -> float | None:
    try:
        value = float(token)
    except ValueError:
        return None
    if not math.isfinite(value):
        return None
    return value


def _coerce_bool(value: OrbValue | None) -> bool | None:
    if isinstance(value, bool):
        return value
    return None


def _coerce_string(value: OrbValue | None) -> str | None:
    if isinstance(value, str):
        return value
    return None


def _coerce_orb_scalar(value: OrbValue | None) -> OrbPrimitive | None:
    if isinstance(value, tuple):
        if len(value) == 1:
            return _coerce_orb_scalar(value[0])
        return None
    return value if isinstance(value, (bool, int, float, str)) else None


def _normalize_orb_value(value: OrbValue) -> OrbValue:
    if isinstance(value, tuple) and len(value) == 1:
        return value[0]
    return value


def _get_token(tokens: tuple[str, ...], index: int) -> str | None:
    if len(tokens) > index:
        value = tokens[index]
        return value if isinstance(value, str) else str(value)
    return None
