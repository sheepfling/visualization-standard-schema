from __future__ import annotations

from collections.abc import Callable
from multiprocessing import get_context
from queue import Empty
import tarfile
from threading import Thread
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


class OrbCorpusFailure(VssModel):
    stage: str = Field(min_length=1)
    errorType: str = Field(min_length=1)
    message: str = Field(min_length=1)


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
    failure: OrbCorpusFailure | None = None

    @property
    def error(self) -> str | None:
        if self.failure is None:
            return None
        return self.failure.message


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
    member_processor: Callable[[str, str, Path], OrbCorpusEntry] | None = None,
) -> OrbCorpusManifest:
    archive = Path(archive_path)
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)

    entries: list[OrbCorpusEntry] = []
    processor = member_processor or _process_member
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
            extracted = handle.extractfile(member)
            if extracted is None:
                entries.append(
                    _build_failure_entry(
                        member_name=member.name,
                        stage="extract",
                        error_type="ValueError",
                        message="archive member could not be extracted",
                    )
                )
                continue
            raw_text = extracted.read().decode("utf-8", errors="replace")
            entries.append(_process_member_with_timeout(processor, raw_text, member.name, output, timeout_seconds))

    manifest = OrbCorpusManifest(
        sourceArchive=str(archive),
        outputRoot=str(output),
        totals={
            "orbFiles": len(entries),
            "parsed": sum(1 for entry in entries if entry.failure is None),
            "failed": sum(1 for entry in entries if entry.failure is not None),
            "entities": sum(entry.entities for entry in entries),
            "overlays": sum(entry.overlays for entry in entries),
        },
        entries=entries,
    )
    write_text_file(output / "manifest.json", manifest.model_dump_json(indent=2), encoding="utf-8")
    return manifest


def _process_member(raw_text: str, member_name: str, output_root: Path) -> OrbCorpusEntry:
    relative_name = PurePosixPath(member_name)
    scene_id = _scene_id_for_member(relative_name)
    entry = OrbCorpusEntry(
        archiveMember=member_name,
        relativeName=relative_name.as_posix(),
        sceneId=scene_id,
    )

    try:
        scenario = parse_orb_scenario_text(raw_text)
        from ..convert.orb import _scene_from_orb_scenario

        scene = _scene_from_orb_scenario(scenario, scene_source="orb-scenario")
    except (AttributeError, KeyError, TypeError, UnicodeError, ValueError) as exc:
        entry.failure = OrbCorpusFailure(
            stage="parse",
            errorType=type(exc).__name__,
            message=str(exc),
        )
        return entry

    _normalize_scene(scene, member_name=member_name, scene_id=scene_id, scene_name=relative_name.stem)

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


def _process_member_with_timeout(
    processor: Callable[[str, str, Path], OrbCorpusEntry],
    raw_text: str,
    member_name: str,
    output_root: Path,
    timeout_seconds: int,
) -> OrbCorpusEntry:
    if timeout_seconds <= 0:
        return processor(raw_text, member_name, output_root)

    if processor is _process_member:
        return _process_member_in_subprocess(raw_text, member_name, output_root, timeout_seconds)

    result: dict[str, dict[str, object] | Exception] = {}

    def _worker() -> None:
        try:
            result["entry"] = processor(raw_text, member_name, output_root).model_dump(mode="json", exclude_none=False)
        except Exception as exc:  # noqa: BLE001 - callback boundary, convert to structured failure
            result["error"] = exc

    thread = Thread(target=_worker, daemon=True)
    thread.start()
    thread.join(timeout_seconds)
    if thread.is_alive():
        return _build_failure_entry(
            member_name=member_name,
            stage="timeout",
            error_type="TimeoutError",
            message=f"exceeded {timeout_seconds}s parse budget",
        )
    error = result.get("error")
    if isinstance(error, Exception):
        return _build_failure_entry(
            member_name=member_name,
            stage="parse",
            error_type=type(error).__name__,
            message=str(error),
        )
    entry = result.get("entry")
    if isinstance(entry, dict):
        return OrbCorpusEntry.model_validate(entry)
    return _build_failure_entry(
        member_name=member_name,
        stage="parse",
        error_type="TypeError",
        message="member processor did not return an OrbCorpusEntry",
    )


def _process_member_in_subprocess(raw_text: str, member_name: str, output_root: Path, timeout_seconds: int) -> OrbCorpusEntry:
    ctx = get_context("spawn")
    queue = ctx.Queue(maxsize=1)
    process = ctx.Process(target=_subprocess_member_worker, args=(queue, raw_text, member_name, output_root))
    process.start()
    process.join(timeout_seconds)
    if process.is_alive():
        process.terminate()
        process.join()
        return _build_failure_entry(
            member_name=member_name,
            stage="timeout",
            error_type="TimeoutError",
            message=f"exceeded {timeout_seconds}s parse budget",
        )

    try:
        status, payload = queue.get_nowait()
    except Empty:
        return _build_failure_entry(
            member_name=member_name,
            stage="parse",
            error_type="RuntimeError",
            message="member processor exited without producing a result",
        )
    if status == "entry" and isinstance(payload, dict):
        return OrbCorpusEntry.model_validate(payload)
    if status == "error" and isinstance(payload, tuple) and len(payload) == 2:
        error_type, message = payload
        return _build_failure_entry(
            member_name=member_name,
            stage="parse",
            error_type=str(error_type),
            message=str(message),
        )
    return _build_failure_entry(
        member_name=member_name,
        stage="parse",
        error_type="RuntimeError",
        message="unexpected result from subprocess worker",
    )


def _subprocess_member_worker(queue, raw_text: str, member_name: str, output_root: Path) -> None:
    try:
        queue.put(("entry", _process_member(raw_text, member_name, output_root).model_dump(mode="json", exclude_none=False)))
    except Exception as exc:  # noqa: BLE001 - subprocess boundary, convert to structured failure
        queue.put(("error", (type(exc).__name__, str(exc))))


def _build_failure_entry(*, member_name: str, stage: str, error_type: str, message: str) -> OrbCorpusEntry:
    relative_name = PurePosixPath(member_name)
    return OrbCorpusEntry(
        archiveMember=member_name,
        relativeName=relative_name.as_posix(),
        sceneId=_scene_id_for_member(relative_name),
        failure=OrbCorpusFailure(
            stage=stage,
            errorType=error_type,
            message=message,
        ),
    )


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
