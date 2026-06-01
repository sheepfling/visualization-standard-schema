from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import cast

from .models import OrbDefineBlock, OrbDocument, OrbLine
from .typed import OrbPrimitive, OrbScenario


@dataclass(slots=True)
class OrbScenarioEditor:
    document: OrbDocument

    @classmethod
    def from_scenario(cls, scenario: OrbScenario) -> "OrbScenarioEditor":
        return cls(document=scenario.document)

    def to_text(self) -> str:
        return self.document.to_text()

    def refresh(self) -> OrbScenario:
        return OrbScenario.from_document(self.document)

    def create_platform(
        self,
        platform_type: str,
        platform_name: str,
        *,
        properties: dict[str, OrbPrimitive | tuple[OrbPrimitive, ...]] | None = None,
    ) -> None:
        block = self._append_define_block(
            ("PLATFORM", platform_type, platform_name),
            properties=properties,
        )
        if properties and "STATE" in properties:
            self._move_statement_to_front(block, "STATE")

    def add_airroute_platform(
        self,
        platform_name: str,
        *,
        start_state: tuple[OrbPrimitive, ...],
        parent: str = "Earth",
        waypoint_type: str = "BY_SPEED",
        waypoints: list[tuple[OrbPrimitive, ...]] | None = None,
        shape: str = "AIRCRAFT",
        color: str | None = None,
        smooth: bool | None = None,
    ) -> None:
        properties: dict[str, OrbPrimitive | tuple[OrbPrimitive, ...]] = {
            "STATE": start_state,
            "PLAT": parent,
            "WAYPOINT_TYPE": waypoint_type,
            "SHAPE": shape,
        }
        if color is not None:
            properties["COLOR"] = color
        if smooth is not None:
            properties["SMOOTH"] = smooth
        self.create_platform("AIRROUTE", platform_name, properties=properties)
        if waypoints is not None:
            self.set_platform_repeated(platform_name, "WAYPOINT", waypoints)

    def delete_platform(self, platform_name: str) -> None:
        self._delete_named_block("PLATFORM", platform_name)

    def create_view(
        self,
        view_type: str,
        view_name: str,
        observer: str,
        coordinate_system: str,
        *,
        properties: dict[str, OrbPrimitive | tuple[OrbPrimitive, ...]] | None = None,
    ) -> None:
        self._append_define_block(
            ("VIEW", view_type, view_name, observer, coordinate_system),
            properties=properties,
        )

    def add_world_view(
        self,
        view_name: str,
        *,
        observer: str,
        coordinate_system: str,
        icon_list: Sequence[str] | None = None,
        label_list: Sequence[str] | None = None,
        viewangles: tuple[OrbPrimitive, ...] | None = None,
    ) -> None:
        properties: dict[str, OrbPrimitive | tuple[OrbPrimitive, ...]] = {}
        if viewangles is not None:
            properties["VIEWANGLES"] = viewangles
        self.create_view("WORLD", view_name, observer, coordinate_system, properties=properties)
        if icon_list is not None:
            self.set_view_list_items(view_name, "ICON_LIST", icon_list)
        if label_list is not None:
            self.set_view_list_items(view_name, "LABEL_LIST", label_list)

    def delete_view(self, view_name: str) -> None:
        self._delete_named_block("VIEW", view_name)

    def create_trajectory(
        self,
        trajectory_name: str,
        *,
        coordinate_system: str,
        platform_name: str,
        trajectory_choice: tuple[OrbPrimitive, ...],
        rows: list[tuple[OrbPrimitive, ...]] | None = None,
        properties: dict[str, OrbPrimitive | tuple[OrbPrimitive, ...]] | None = None,
    ) -> None:
        combined_properties: dict[str, OrbPrimitive | tuple[OrbPrimitive, ...]] = {
            "CS": coordinate_system,
            "PLATFORM": platform_name,
            "TRAJECTORY_CHOICE": trajectory_choice,
        }
        if properties:
            combined_properties.update(properties)
        self._append_define_block(("TRAJECTORY", trajectory_name), properties=combined_properties)
        if rows is not None:
            self.set_trajectory_rows(trajectory_name, rows)

    def create_grid(
        self,
        grid_type: str,
        grid_name: str,
        *,
        properties: dict[str, OrbPrimitive | tuple[OrbPrimitive, ...]] | None = None,
    ) -> None:
        self._append_define_block(("GRID", grid_type, grid_name), properties=properties)

    def create_coordinate_system(
        self,
        cs_type: str,
        cs_name: str,
        *,
        properties: dict[str, OrbPrimitive | tuple[OrbPrimitive, ...]] | None = None,
    ) -> None:
        self._append_define_block(("CS", cs_type, cs_name), properties=properties)

    def create_config(
        self,
        *,
        properties: dict[str, OrbPrimitive | tuple[OrbPrimitive, ...]] | None = None,
    ) -> None:
        self._append_define_block(("CONFIG",), properties=properties)

    def create_analysis(
        self,
        analysis_name: str,
        *,
        properties: dict[str, OrbPrimitive | tuple[OrbPrimitive, ...]] | None = None,
        variable_details: dict[str, OrbPrimitive | tuple[OrbPrimitive, ...]] | None = None,
    ) -> None:
        block = self._append_define_block(
            ("ANALYSIS", analysis_name),
            properties={k: v for k, v in (properties or {}).items() if k != "VARIABLE"},
        )
        variable_value = (properties or {}).get("VARIABLE")
        if variable_value is not None:
            variable_line = OrbLine(
                indent=_preferred_child_indent(block),
                content=_format_statement("VARIABLE", variable_value),
                line_ending=_preferred_line_ending(block),
            )
            variable_line.children = [
                OrbLine(
                    indent=f"{variable_line.indent}    ",
                    content=_format_statement(key, value),
                    line_ending=_preferred_line_ending(block),
                )
                for key, value in (variable_details or {}).items()
            ]
            block.children.insert(0, variable_line)
        elif variable_details:
            for key, value in variable_details.items():
                block.children.append(
                    OrbLine(
                        indent="\t",
                        content=_format_statement(key, value),
                        line_ending=_preferred_line_ending(block),
                    )
                )

    def create_stabilization(
        self,
        stabilization_name: str,
        *,
        properties: dict[str, OrbPrimitive | tuple[OrbPrimitive, ...]] | None = None,
    ) -> None:
        self._append_define_block(("STABILIZATION", f'"{stabilization_name}"'), properties=properties)

    def clone_named_block(self, kind: str, source_name: str, target_name: str) -> None:
        source = self._require_named_block(kind, source_name)
        clone = cast(OrbDefineBlock, _clone_line(source))
        clone.content = _replace_named_token(clone.define_tokens, source_name, target_name)
        self.document.entries.append(clone)

    def set_group_list_items(self, group_name: str, list_key: str, items: Sequence[OrbPrimitive]) -> None:
        block = self._require_named_block("GROUP", group_name)
        list_line = self._require_or_create_list_line(block, list_key)
        self._replace_list_children(list_line, items)

    def set_view_list_items(self, view_name: str, list_key: str, items: Sequence[OrbPrimitive]) -> None:
        block = self._require_named_block("VIEW", view_name)
        list_line = self._find_nested_list_line(block, list_key)
        if list_line is None:
            list_line = self._append_list_container(block, list_key)
        self._replace_list_children(list_line, items)

    def set_spice_files(self, values: Sequence[str]) -> None:
        block = self._require_singleton_block("SPICE")
        self._replace_repeated_statements(block, "SPICEFILE", values)

    def set_platform_repeated(
        self,
        platform_name: str,
        key: str,
        rows: Sequence[OrbPrimitive | tuple[OrbPrimitive, ...]],
    ) -> None:
        block = self._require_named_block("PLATFORM", platform_name)
        self._replace_repeated_statements(block, key, rows)

    def set_trajectory_rows(
        self,
        trajectory_name: str,
        rows: list[tuple[OrbPrimitive, ...]],
    ) -> None:
        block = self._require_named_block("TRAJECTORY", trajectory_name)
        trajectory_choice = self._require_statement(block, "TRAJECTORY_CHOICE")
        line_ending = _preferred_line_ending(trajectory_choice)
        indent = _preferred_child_indent(trajectory_choice)
        trajectory_choice.children = [
            OrbLine(
                indent=indent,
                content=_format_values(row),
                line_ending=line_ending,
            )
            for row in rows
        ]

    def delete_config_property(self, key: str) -> None:
        self._delete_statement(self._require_singleton_block("CONFIG"), key)

    def delete_units_property(self, key: str) -> None:
        self._delete_statement(self._require_singleton_block("UNITS"), key)

    def delete_clock_property(self, key: str) -> None:
        self._delete_statement(self._require_singleton_block("CLOCK"), key)

    def set_config_property(self, key: str, value: OrbPrimitive | tuple[OrbPrimitive, ...]) -> None:
        block = self._require_singleton_block("CONFIG")
        self._set_statement(block, key, value)

    def set_units_property(self, key: str, value: OrbPrimitive | tuple[OrbPrimitive, ...]) -> None:
        block = self._require_singleton_block("UNITS")
        self._set_statement(block, key, value)

    def set_clock_property(self, key: str, value: OrbPrimitive | tuple[OrbPrimitive, ...]) -> None:
        block = self._require_singleton_block("CLOCK")
        self._set_statement(block, key, value)

    def set_platform_property(
        self,
        platform_name: str,
        key: str,
        value: OrbPrimitive | tuple[OrbPrimitive, ...],
    ) -> None:
        block = self._require_named_block("PLATFORM", platform_name)
        self._set_statement(block, key, value)

    def set_view_property(
        self,
        view_name: str,
        key: str,
        value: OrbPrimitive | tuple[OrbPrimitive, ...],
    ) -> None:
        block = self._require_named_block("VIEW", view_name)
        self._set_statement(block, key, value)

    def _require_singleton_block(self, kind: str) -> OrbDefineBlock:
        matches = [block for block in self.document.define_blocks if block.block_kind == kind]
        if not matches:
            raise KeyError(f"DEFINE {kind} block not found")
        return matches[0]

    def _require_named_block(self, kind: str, name: str) -> OrbDefineBlock:
        for block in self.document.define_blocks:
            if block.block_kind != kind:
                continue
            tokens = block.define_tokens
            if name in tokens[1:]:
                return block
        raise KeyError(f"DEFINE {kind} block named {name!r} not found")

    def _set_statement(
        self,
        block: OrbDefineBlock,
        key: str,
        value: OrbPrimitive | tuple[OrbPrimitive, ...],
    ) -> None:
        for child in block.children:
            if child.keyword == key:
                child.content = _format_statement(key, value)
                return
        block.children.append(
            OrbLine(
                indent=_preferred_child_indent(block),
                content=_format_statement(key, value),
                line_ending=_preferred_line_ending(block),
            )
        )

    def _require_statement(self, block: OrbDefineBlock | OrbLine, key: str) -> OrbLine:
        for child in block.children:
            if child.keyword == key:
                return child
        raise KeyError(f"Statement {key!r} not found")

    def _delete_statement(self, block: OrbDefineBlock, key: str) -> None:
        for index, child in enumerate(block.children):
            if child.keyword == key:
                del block.children[index]
                return
        raise KeyError(f"Statement {key!r} not found in DEFINE {block.block_kind}")

    def _replace_repeated_statements(
        self,
        block: OrbDefineBlock,
        key: str,
        rows: Sequence[OrbPrimitive | tuple[OrbPrimitive, ...]],
    ) -> None:
        existing_indexes = [index for index, child in enumerate(block.children) if child.keyword == key]
        first_index = existing_indexes[0] if existing_indexes else len(block.children)
        template_indent = block.children[first_index].indent if existing_indexes else _preferred_child_indent(block)
        template_ending = block.children[first_index].line_ending if existing_indexes else _preferred_line_ending(block)

        for index in reversed(existing_indexes):
            del block.children[index]

        block.children[first_index:first_index] = [
            OrbLine(
                indent=template_indent,
                content=_format_statement(key, row),
                line_ending=template_ending,
            )
            for row in rows
        ]

    def _append_define_block(
        self,
        define_tokens: tuple[str, ...],
        *,
        properties: dict[str, OrbPrimitive | tuple[OrbPrimitive, ...]] | None = None,
    ) -> OrbDefineBlock:
        line_ending = _preferred_document_line_ending(self.document)
        block = OrbDefineBlock(
            indent="",
            content=_format_define_header(define_tokens),
            line_ending=line_ending,
        )
        for key, value in (properties or {}).items():
            block.children.append(
                OrbLine(
                    indent="\t",
                    content=_format_statement(key, value),
                    line_ending=line_ending,
                )
            )
        self.document.entries.append(block)
        return block

    def _move_statement_to_front(self, block: OrbDefineBlock, key: str) -> None:
        for index, child in enumerate(block.children):
            if child.keyword == key:
                block.children.insert(0, block.children.pop(index))
                return

    def _require_or_create_list_line(self, block: OrbDefineBlock, list_key: str) -> OrbLine:
        for child in block.children:
            if child.keyword == list_key:
                return child
        list_line = OrbLine(
            indent=_preferred_child_indent(block),
            content=list_key,
            line_ending=_preferred_line_ending(block),
        )
        block.children.append(list_line)
        return list_line

    def _find_nested_list_line(self, block: OrbDefineBlock, list_key: str) -> OrbLine | None:
        for child in block.children:
            if child.keyword == list_key:
                return child
            for grandchild in child.children:
                if grandchild.keyword == list_key:
                    return grandchild
        return None

    def _append_list_container(self, block: OrbDefineBlock, list_key: str) -> OrbLine:
        list_prefix = list_key.removesuffix("_LIST")
        container_key = f"{list_prefix}S"
        container = OrbLine(
            indent=_preferred_child_indent(block),
            content=f"{container_key} ON",
            line_ending=_preferred_line_ending(block),
        )
        list_line = OrbLine(
            indent="\t",
            content=f'{list_key} "ON"',
            line_ending=_preferred_line_ending(block),
        )
        container.children.append(list_line)
        block.children.append(container)
        return list_line

    def _replace_list_children(self, list_line: OrbLine, items: Sequence[OrbPrimitive]) -> None:
        line_ending = _preferred_line_ending(list_line)
        indent = _preferred_child_indent(list_line)
        list_line.children = [
            OrbLine(
                indent=indent,
                content=_format_list_item(item),
                line_ending=line_ending,
            )
            for item in items
        ]

    def _delete_named_block(self, kind: str, name: str) -> None:
        for index, entry in enumerate(self.document.entries):
            if not isinstance(entry, OrbDefineBlock):
                continue
            if entry.block_kind != kind:
                continue
            if name in entry.define_tokens[1:]:
                del self.document.entries[index]
                return
        raise KeyError(f"DEFINE {kind} block named {name!r} not found")


def _preferred_child_indent(block: OrbDefineBlock | OrbLine) -> str:
    if block.children:
        return block.children[-1].indent
    if isinstance(block, OrbLine) and block.indent == "\t":
        return "     "
    return "\t"


def _preferred_line_ending(block: OrbDefineBlock | OrbLine) -> str:
    if block.children:
        return block.children[-1].line_ending
    return block.line_ending or "\n"


def _preferred_document_line_ending(document: OrbDocument) -> str:
    for entry in reversed(document.entries):
        if entry.line_ending:
            return entry.line_ending
    return "\n"


def _format_define_header(tokens: tuple[str, ...]) -> str:
    rendered = " ".join(_format_primitive(token) for token in tokens)
    return f"DEFINE {rendered}"


def _format_statement(
    key: str,
    value: OrbPrimitive | tuple[OrbPrimitive, ...],
) -> str:
    values = value if isinstance(value, tuple) else (value,)
    rendered = _format_values(values)
    return f"{key} {rendered}" if rendered else key


def _format_values(values: tuple[OrbPrimitive, ...]) -> str:
    return " ".join(_format_primitive(item) for item in values)


def _format_list_item(value: OrbPrimitive) -> str:
    if isinstance(value, str):
        escaped = value.replace('"', '""')
        return f'"{escaped}"'
    return _format_primitive(value)


def _format_primitive(value: OrbPrimitive) -> str:
    if isinstance(value, bool):
        return "ON" if value else "OFF"
    if isinstance(value, (int, float)):
        return str(value)
    if value == "":
        return '""'
    if _needs_quotes(value):
        escaped = value.replace('"', '""')
        return f'"{escaped}"'
    return value


def _needs_quotes(value: str) -> bool:
    if any(ch.isspace() for ch in value):
        return True
    if any(ch in value for ch in '.{}:/()'):
        return True
    return False


def _clone_line(line: OrbLine) -> OrbLine:
    cloned = OrbDefineBlock(
        indent=line.indent,
        content=line.content,
        line_ending=line.line_ending,
    ) if isinstance(line, OrbDefineBlock) else OrbLine(
        indent=line.indent,
        content=line.content,
        line_ending=line.line_ending,
    )
    cloned.children = [_clone_line(child) for child in line.children]
    return cloned


def _replace_named_token(define_tokens: tuple[str, ...], source_name: str, target_name: str) -> str:
    tokens = list(define_tokens)
    for index in range(1, len(tokens)):
        if tokens[index] == source_name:
            tokens[index] = target_name
            break
    else:
        raise ValueError(f"Source name {source_name!r} not found in DEFINE header")
    return _format_define_header(tuple(tokens))
