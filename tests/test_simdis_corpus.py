from __future__ import annotations

from pathlib import Path
import sys
from zipfile import ZipFile

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vss.convert import parse_simdis_asi_to_scene
from vss.simdis import compile_simdis_asi, parse_simdis_gog_text, render_simdis_gog_text


CORPUS_ZIP = Path("INBOX/simdis_corpus_v0_1.zip")
ASI_PREFIX = "simdis_corpus_v0_1/public_seed/asi/"
GOG_PREFIX = "simdis_corpus_v0_1/public_seed/gog/"
DISCN_PREFIX = "simdis_corpus_v0_1/inferred/discn/"


def _corpus_members(prefix: str, suffix: str) -> list[str]:
    with ZipFile(CORPUS_ZIP) as archive:
        return sorted(
            name
            for name in archive.namelist()
            if name.startswith(prefix) and name.endswith(suffix)
        )


def _corpus_text(member: str) -> str:
    with ZipFile(CORPUS_ZIP) as archive:
        return archive.read(member).decode("utf-8")


def _platform_ids(raw_text: str) -> list[str]:
    ids: list[str] = []
    for raw_line in raw_text.splitlines():
        line = raw_line.strip()
        if line.startswith("PlatformID "):
            parts = line.split()
            if len(parts) >= 2:
                ids.append(parts[1])
    return ids


@pytest.mark.parametrize("member", _corpus_members(ASI_PREFIX, ".asi"))
def test_simdis_asi_corpus_seed_files_round_trip(member: str) -> None:
    raw_text = _corpus_text(member)
    scene = parse_simdis_asi_to_scene(raw_text, source=Path(member).stem)
    assert {entity.id for entity in scene.entities} == set(_platform_ids(raw_text))

    compiled = compile_simdis_asi(scene)
    rebuilt = parse_simdis_asi_to_scene(compiled, source=f"{Path(member).stem}:roundtrip")
    assert len(rebuilt.entities) == len(scene.entities)
    assert {entity.id for entity in rebuilt.entities} == {entity.id for entity in scene.entities}

    if "BeamID" in raw_text:
        assert "BeamID" in compiled
    if "GateID" in raw_text:
        assert "GateID" in compiled
    if "Projector " in raw_text:
        assert "Projector " in compiled


@pytest.mark.parametrize("member", _corpus_members(GOG_PREFIX, ".gog"))
def test_simdis_gog_corpus_seed_files_round_trip(member: str) -> None:
    raw_text = _corpus_text(member)
    document = parse_simdis_gog_text(raw_text, source=Path(member).stem)
    rendered = render_simdis_gog_text(document)
    rebuilt = parse_simdis_gog_text(rendered, source=f"{Path(member).stem}:roundtrip")

    assert len(rebuilt.shapes) == len(document.shapes)
    assert [shape.kind for shape in rebuilt.shapes] == [shape.kind for shape in document.shapes]


def test_simdis_discn_candidate_is_parseable() -> None:
    member = _corpus_members(DISCN_PREFIX, ".discn")[0]
    raw_text = _corpus_text(member)
    scene = parse_simdis_asi_to_scene(raw_text, source=Path(member).stem)

    assert len(scene.entities) == 1
    assert scene.entities[0].id == "9001"
    assert "PlatformID 9001" in compile_simdis_asi(scene)
