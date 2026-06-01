from __future__ import annotations

import signal
import tarfile
from contextlib import contextmanager
from pathlib import Path, PurePosixPath

from pydantic import Field

from ..cesium import dump_cesium_scene_json
from ..io import write_scene_file
from ..models import VssModel, VssScene
from ..soap import compile_soap_scene, dump_soap_bundle_json
from ..util import write_text_file
from .schema import parse_orb_scenario_text


class OrbCorpusTargets(VssModel):
    sdj: str | None = None
    cesium: str | None = None
    soap: str | None = None


class OrbCorpusEntry(VssModel):
    archiveMember: str = Field(min_length=1)
    relativeName: str = Field(min_length=1)
    sceneId: str = Field(min_length=1)
    revision: str | int | None = None
    fileType: str | None = None
    platforms: int = 0
    trajectories: int = 0
    views: int = 0
    entities: int = 0
    overlays: int = 0
    targets: OrbCorpusTargets = Field(default_factory=OrbCorpusTargets)
    error: str | None = None


class OrbCorpusManifest(VssModel):
    sourceArchive: str = Field(min_length=1)
    outputRoot: str = Field(min_length=1)
    totals: dict[str, int] = Field(default_factory=dict)
    entries: list[OrbCorpusEntry] = Field(default_factory=list)


def build_orb_fixture_set(
    archive_path: str | Path,
    output_root: str | Path,
    *,
    limit: int | None = None,
    timeout_seconds: int = 5,
) -> OrbCorpusManifest:
    archive = Path(archive_path)
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)

    entries: list[OrbCorpusEntry] = []
    with tarfile.open(archive) as handle:
        members = sorted(
            (
                member
                for member in handle.getmembers()
                if member.isfile()
                and member.name.lower().endswith(".orb")
                and not PurePosixPath(member.name).name.startswith("._")
            ),
            key=lambda member: member.name,
        )
        if limit is not None:
            members = members[:limit]

        for member in members:
            with _time_limit(timeout_seconds):
                try:
                    entries.append(_process_member(handle, member, output))
                except TimeoutError:
                    entries.append(
                        OrbCorpusEntry(
                            archiveMember=member.name,
                            relativeName=PurePosixPath(member.name).as_posix(),
                            sceneId=_scene_id_for_member(PurePosixPath(member.name)),
                            error=f"TimeoutError: exceeded {timeout_seconds}s parse budget",
                        )
                    )

    manifest = OrbCorpusManifest(
        sourceArchive=str(archive),
        outputRoot=str(output),
        totals={
            "orbFiles": len(entries),
            "parsed": sum(1 for entry in entries if entry.error is None),
            "failed": sum(1 for entry in entries if entry.error is not None),
            "entities": sum(entry.entities for entry in entries),
            "overlays": sum(entry.overlays for entry in entries),
        },
        entries=entries,
    )
    write_text_file(output / "manifest.json", manifest.model_dump_json(indent=2), encoding="utf-8")
    return manifest


def _process_member(handle: tarfile.TarFile, member: tarfile.TarInfo, output_root: Path) -> OrbCorpusEntry:
    relative_name = PurePosixPath(member.name)
    scene_id = _scene_id_for_member(relative_name)
    entry = OrbCorpusEntry(
        archiveMember=member.name,
        relativeName=relative_name.as_posix(),
        sceneId=scene_id,
    )

    extracted = handle.extractfile(member)
    if extracted is None:
        entry.error = "archive member could not be extracted"
        return entry
    raw_text = extracted.read().decode("utf-8", errors="replace")

    try:
        scenario = parse_orb_scenario_text(raw_text)
        from ..convert import _scene_from_orb_scenario

        scene = _scene_from_orb_scenario(scenario, scene_source="orb-scenario")
    except Exception as exc:  # pragma: no cover
        entry.error = f"{type(exc).__name__}: {exc}"
        return entry

    _normalize_scene(scene, member_name=member.name, scene_id=scene_id, scene_name=relative_name.stem)

    entry.revision = scenario.revision
    entry.fileType = scenario.file_type
    entry.platforms = len(scenario.platforms)
    entry.trajectories = len(scenario.trajectories)
    entry.views = len(scenario.views)
    entry.entities = len(scene.entities)
    entry.overlays = len(scene.overlays)

    sdj_path = output_root / "sdj" / relative_name.with_suffix(".sdj.json")
    cesium_path = output_root / "cesium" / relative_name.with_suffix(".czml.json")
    soap_path = output_root / "soap" / relative_name.with_suffix(".bundle.json")

    write_scene_file(scene, sdj_path)
    write_text_file(cesium_path, dump_cesium_scene_json(scene), encoding="utf-8")
    write_text_file(soap_path, dump_soap_bundle_json(compile_soap_scene(scene)), encoding="utf-8")

    entry.targets = OrbCorpusTargets(
        sdj=sdj_path.relative_to(output_root).as_posix(),
        cesium=cesium_path.relative_to(output_root).as_posix(),
        soap=soap_path.relative_to(output_root).as_posix(),
    )
    return entry


def _normalize_scene(scene: VssScene, *, member_name: str, scene_id: str, scene_name: str) -> None:
    scene.document.id = scene_id
    scene.document.name = scene_name
    scene.document.source = member_name
    for obj in scene.objects:
        obj.source = obj.source or member_name
        obj.attributes.setdefault("orbArchiveMember", member_name)


def _scene_id_for_member(member_name: PurePosixPath) -> str:
    parts: list[str] = []
    for part in member_name.with_suffix("").parts:
        cleaned = "".join(char if char.isalnum() else "-" for char in part).strip("-").lower()
        parts.append(cleaned or "item")
    return "__".join(parts)


@contextmanager
def _time_limit(seconds: int):
    if seconds <= 0:
        yield
        return

    def _raise_timeout(signum, frame):  # type: ignore[unused-argument]
        raise TimeoutError

    previous = signal.signal(signal.SIGALRM, _raise_timeout)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
