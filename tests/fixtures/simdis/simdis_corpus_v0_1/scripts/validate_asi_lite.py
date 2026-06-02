from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


COMMAND_ARITY: dict[str, tuple[int, int | None]] = {
    "ReferenceYear": (1, 1),
    "DegreeAngles": (1, 1),
    "PlatformID": (1, 1),
    "PlatformName": (2, None),
    "PlatformIcon": (2, None),
    "PlatformData": (11, 11),
    "BeamID": (2, 2),
    "BeamType": (2, None),
    "HorzBW": (2, 2),
    "VertBW": (2, 2),
    "BeamOnOffCmd": (3, 3),
    "BeamColorCmd": (3, 3),
    "BeamDataRAE": (5, 5),
    "BeamTargetIDCmd": (3, 3),
    "GateID": (2, 2),
    "GateType": (2, None),
    "GateOnOffCmd": (3, 3),
    "GateColorCmd": (3, 3),
    "GateDataRAE": (9, 9),
    "Projector": (2, 2),
    "ProjectorRasterFile": (2, None),
    "ProjectorInterpolateFOV": (2, 2),
    "ProjectorOn": (3, 3),
    "ProjectorFOV": (3, 3),
}


@dataclass(frozen=True)
class AsiIssue:
    line: int
    severity: str
    message: str
    text: str


@dataclass(frozen=True)
class AsiValidation:
    path: str
    ok: bool
    commandCounts: dict[str, int]
    issues: list[AsiIssue]


def _tokenize(line: str) -> list[str]:
    tokens: list[str] = []
    current: list[str] = []
    quoted = False
    escaped = False
    for char in line:
        if escaped:
            current.append(char)
            escaped = False
            continue
        ####
        if char == "\\":
            escaped = True
            continue
        ####
        if char == '"':
            quoted = not quoted
            current.append(char)
            continue
        ####
        if char.isspace() and not quoted:
            if current:
                tokens.append("".join(current))
                current = []
            ####
            continue
        ####
        current.append(char)
    ####
    if current:
        tokens.append("".join(current))
    ####
    return tokens
####


def validate_asi(path: Path) -> AsiValidation:
    issues: list[AsiIssue] = []
    command_counts: dict[str, int] = {}
    for number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        ####
        tokens = _tokenize(line)
        if not tokens:
            continue
        ####
        command = tokens[0]
        command_counts[command] = command_counts.get(command, 0) + 1
        arity = COMMAND_ARITY.get(command)
        if arity is None:
            issues.append(AsiIssue(number, "warning", f"Unknown ASI-lite command: {command}", raw_line))
            continue
        ####
        actual = len(tokens) - 1
        minimum, maximum = arity
        if actual < minimum or (maximum is not None and actual > maximum):
            issues.append(AsiIssue(number, "error", f"Expected {arity}, got {actual} arguments for {command}", raw_line))
        ####
    ####
    ok = not any(issue.severity == "error" for issue in issues)
    return AsiValidation(str(path), ok, command_counts, issues)
####


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the public ASI-lite seed subset.")
    parser.add_argument("paths", nargs="+", help="ASI files to validate.")
    return parser.parse_args()
####


def main() -> int:
    args = parse_args()
    results = [validate_asi(Path(path)) for path in args.paths]
    payload: dict[str, Any] = {
        "ok": all(result.ok for result in results),
        "results": [
            {
                "path": result.path,
                "ok": result.ok,
                "commandCounts": result.commandCounts,
                "issues": [asdict(issue) for issue in result.issues],
            }
            for result in results
        ],
    }
    print(json.dumps(payload, indent=2))
    return 0 if payload["ok"] else 1
####


if __name__ == "__main__":
    raise SystemExit(main())
####
