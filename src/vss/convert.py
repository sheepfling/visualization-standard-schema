from __future__ import annotations

from importlib import import_module
from pathlib import Path

__path__ = [str(Path(__file__).with_name("convert"))]
if __spec__ is not None:
    __spec__.submodule_search_locations = __path__

_common = import_module("vss.convert.common")
_emit = import_module("vss.convert.emit")
_ingest = import_module("vss.convert.ingest")

for _name in dir(_common):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_common, _name)

for _module in (_emit, _ingest):
    for _name in getattr(_module, "__all__", ()):
        globals()[_name] = getattr(_module, _name)

_scene_from_orb_scenario = _common._scene_from_orb_scenario

del import_module, Path, _common, _emit, _ingest, _name, _module
