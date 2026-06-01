from __future__ import annotations

from pathlib import Path

from ..util import write_text_file
from .models import OrbDefineBlock, OrbDocument, OrbEntry, OrbLine

BLOCK_END_KEYWORDS = {
    "CLOCK_CONE_GRID": "GRID_END",
    "DRIVER": "DRIVER_END",
}


def parse_orb_text(raw_text: str) -> OrbDocument:
    entries: list[OrbEntry] = []
    stack: list[tuple[int, OrbLine | None]] = [(-1, None)]

    for raw_line in raw_text.splitlines(keepends=True):
        line_body, line_ending = _split_line_ending(raw_line)
        indent, content = _split_indent(line_body)
        indent_width = _indent_width(indent)
        node = _make_node(indent, content, line_ending)

        if isinstance(node, OrbDefineBlock):
            stack = [stack[0]]
            entries.append(node)
            stack.append((indent_width, node))
            continue

        block_end_parent = _find_block_end_parent(stack, node)
        if block_end_parent is not None:
            block_end_parent.children.append(node)
            _pop_through_parent(stack, block_end_parent)
            continue

        continuation_parent = _find_continuation_parent(stack, node)
        if continuation_parent is not None:
            parent = continuation_parent
            parent.children.append(node)
            stack.append((indent_width, node))
            continue

        while len(stack) > 1 and indent_width <= stack[-1][0]:
            stack.pop()

        parent = stack[-1][1]
        if parent is None:
            entries.append(node)
        else:
            parent.children.append(node)
        stack.append((indent_width, node))

    return OrbDocument(entries=entries)


def parse_orb_file(path: str | Path) -> OrbDocument:
    return parse_orb_text(Path(path).read_text(encoding="utf-8"))


def dump_orb_text(document: OrbDocument) -> str:
    return document.to_text()


def dump_orb_file(document: OrbDocument, path: str | Path) -> None:
    write_text_file(path, dump_orb_text(document), encoding="utf-8", trailing_newline=False)


def _make_node(indent: str, content: str, line_ending: str) -> OrbEntry:
    if not indent and content.startswith("DEFINE "):
        return OrbDefineBlock(indent=indent, content=content, line_ending=line_ending)
    return OrbLine(indent=indent, content=content, line_ending=line_ending)


def _split_indent(raw_line: str) -> tuple[str, str]:
    offset = 0
    while offset < len(raw_line) and raw_line[offset] in (" ", "\t"):
        offset += 1
    return raw_line[:offset], raw_line[offset:]


def _indent_width(indent: str) -> int:
    return len(indent.expandtabs(8))


def _split_line_ending(raw_line: str) -> tuple[str, str]:
    if raw_line.endswith("\r\n"):
        return raw_line[:-2], "\r\n"
    if raw_line.endswith("\n") or raw_line.endswith("\r"):
        return raw_line[:-1], raw_line[-1]
    return raw_line, ""


def _find_continuation_parent(
    stack: list[tuple[int, OrbLine | None]],
    node: OrbLine,
) -> OrbLine | None:
    for _, parent in reversed(stack[1:]):
        if parent is not None and _accepts_continuation(parent, node):
            return parent
    return None


def _accepts_continuation(parent: OrbLine, node: OrbLine) -> bool:
    parent_keyword = parent.keyword or ""
    node_keyword = node.keyword or ""
    node_text = node.stripped_content

    if parent_keyword == "VARIABLE" and node_keyword in {"DISTANCEU", "TIMEU", "ANGLEU", "COMMENT"}:
        return True
    if parent_keyword.endswith("LIST") and node_text.startswith('"'):
        return True
    if parent_keyword in {"CLOCK_CONE_GRID", "DRIVER"}:
        return True
    if parent.tokens[-1:] == ("SET",) and node_keyword.endswith("LIST"):
        return True
    if parent_keyword == "TRAJECTORY_CHOICE" and node_text[:1] in "-0123456789":
        return True
    return False


def _find_block_end_parent(
    stack: list[tuple[int, OrbLine | None]],
    node: OrbLine,
) -> OrbLine | None:
    node_keyword = node.keyword
    if node_keyword is None:
        return None

    for _, parent in reversed(stack[1:]):
        if parent is None:
            continue
        if BLOCK_END_KEYWORDS.get(parent.keyword or "") == node_keyword:
            return parent
    return None


def _pop_through_parent(
    stack: list[tuple[int, OrbLine | None]],
    parent: OrbLine,
) -> None:
    while len(stack) > 1:
        _, candidate = stack.pop()
        if candidate is parent:
            break
