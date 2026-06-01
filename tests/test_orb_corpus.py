from __future__ import annotations

import io
import tarfile
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vss.orb import OrbCorpusEntry, build_orb_fixture_set


def _write_orb_archive(path: Path, text: str) -> None:
    data = text.encode("utf-8")
    with tarfile.open(path, "w") as handle:
        info = tarfile.TarInfo(name="orb_format_collection/demo.orb")
        info.size = len(data)
        handle.addfile(info, fileobj=io.BytesIO(data))


def test_build_orb_fixture_set_records_timeout_failure(tmp_path: Path) -> None:
    archive_path = tmp_path / "fixtures.tar"
    _write_orb_archive(
        archive_path,
        "56 revision\nSOAP_SCENARIO_FILE\nDEFINE PLATFORM AIR \"Air\"\n\tWAYPOINT 33.93 -118.4 1\n",
    )

    def slow_processor(_handle, member, _output_root):
        time.sleep(0.2)
        return OrbCorpusEntry(
            archiveMember=member.name,
            relativeName=member.name,
            sceneId="demo",
        )

    manifest = build_orb_fixture_set(
        archive_path,
        tmp_path / "out",
        timeout_seconds=0.01,
        member_processor=slow_processor,
    )

    entry = manifest.entries[0]
    assert entry.failure is not None
    assert entry.failure.stage == "timeout"
    assert entry.failure.errorType == "TimeoutError"
    assert "parse budget" in entry.failure.message


def test_build_orb_fixture_set_records_parse_failure(tmp_path: Path) -> None:
    archive_path = tmp_path / "fixtures.tar"
    _write_orb_archive(
        archive_path,
        "56 revision\nSOAP_SCENARIO_FILE\nDEFINE PLATFORM AIR \"Air\"\n\tWAYPOINT 33.93 -118.4 1\n",
    )

    def failing_processor(_handle, _member, _output_root):
        raise ValueError("bad orb")

    manifest = build_orb_fixture_set(
        archive_path,
        tmp_path / "out",
        member_processor=failing_processor,
    )

    entry = manifest.entries[0]
    assert entry.failure is not None
    assert entry.failure.stage == "parse"
    assert entry.failure.errorType == "ValueError"
    assert entry.failure.message == "bad orb"
