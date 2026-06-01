from __future__ import annotations

from pathlib import Path

from .editor import OrbScenarioEditor
from .io import parse_orb_text
from .typed import OrbScenario


def parse_orb_scenario_text(raw_text: str) -> OrbScenario:
    return OrbScenario.from_document(parse_orb_text(raw_text))


def parse_orb_scenario_file(path: str | Path) -> OrbScenario:
    return parse_orb_scenario_text(Path(path).read_text(encoding="utf-8"))


def edit_orb_scenario_text(raw_text: str) -> OrbScenarioEditor:
    return OrbScenarioEditor(document=parse_orb_text(raw_text))


def edit_orb_scenario_file(path: str | Path) -> OrbScenarioEditor:
    return edit_orb_scenario_text(Path(path).read_text(encoding="utf-8"))
