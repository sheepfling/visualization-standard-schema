from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypeAlias


@dataclass(slots=True)
class OrbLine:
    indent: str
    content: str
    line_ending: str = ""
    children: list["OrbLine"] = field(default_factory=list)

    @property
    def stripped_content(self) -> str:
        return self.content.strip()

    @property
    def tokens(self) -> tuple[str, ...]:
        return tokenize_orb_content(self.content)

    @property
    def keyword(self) -> str | None:
        return self.tokens[0] if self.tokens else None

    def to_chunks(self) -> list[str]:
        lines = [f"{self.indent}{self.content}{self.line_ending}"]
        for child in self.children:
            lines.extend(child.to_chunks())
        return lines


@dataclass(slots=True)
class OrbDefineBlock(OrbLine):
    @property
    def define_tokens(self) -> tuple[str, ...]:
        tokens = self.tokens
        if not tokens or tokens[0] != "DEFINE":
            return ()
        return tokens[1:]

    @property
    def block_kind(self) -> str | None:
        tokens = self.define_tokens
        return tokens[0] if tokens else None


OrbEntry: TypeAlias = OrbLine | OrbDefineBlock


@dataclass(slots=True)
class OrbDocument:
    entries: list[OrbEntry]

    @property
    def define_blocks(self) -> list[OrbDefineBlock]:
        return [entry for entry in self.entries if isinstance(entry, OrbDefineBlock)]

    def to_text(self) -> str:
        lines: list[str] = []
        for entry in self.entries:
            lines.extend(entry.to_chunks())
        return "".join(lines)


def tokenize_orb_content(content: str) -> tuple[str, ...]:
    import shlex

    stripped = content.strip()
    if not stripped:
        return ()
    try:
        return tuple(shlex.split(stripped, posix=True))
    except ValueError:
        return (stripped,)
