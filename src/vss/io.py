from __future__ import annotations

from pathlib import Path
from typing import Any

from .models import EntityUpsertMessage, VssScene
from .util import dumps_json, write_text_file


def load_message(data: dict[str, Any]) -> EntityUpsertMessage:
    return EntityUpsertMessage.model_validate(data)


def parse_message_json(raw_json: str) -> EntityUpsertMessage:
    return EntityUpsertMessage.model_validate_json(raw_json)


def load_message_file(path: str | Path) -> EntityUpsertMessage:
    return parse_message_json(Path(path).read_text(encoding="utf-8"))


def dump_message(message: EntityUpsertMessage) -> dict[str, Any]:
    return message.model_dump(mode="json", exclude_none=True)


def dump_message_json(message: EntityUpsertMessage, *, indent: int = 2) -> str:
    return dumps_json(dump_message(message), indent=indent)


def write_message_file(
    message: EntityUpsertMessage,
    path: str | Path,
    *,
    indent: int = 2,
) -> Path:
    return write_text_file(path, f"{dump_message_json(message, indent=indent)}", encoding="utf-8")


def load_scene(data: dict[str, Any]) -> VssScene:
    return VssScene.model_validate(data)


def parse_scene_json(raw_json: str) -> VssScene:
    return VssScene.model_validate_json(raw_json)


def load_scene_file(path: str | Path) -> VssScene:
    return parse_scene_json(Path(path).read_text(encoding="utf-8"))


def dump_scene(scene: VssScene) -> dict[str, Any]:
    return scene.model_dump(mode="json", exclude_none=True)


def dump_scene_json(scene: VssScene, *, indent: int = 2) -> str:
    return dumps_json(dump_scene(scene), indent=indent)


def write_scene_file(
    scene: VssScene,
    path: str | Path,
    *,
    indent: int = 2,
) -> Path:
    return write_text_file(path, f"{dump_scene_json(scene, indent=indent)}", encoding="utf-8")
