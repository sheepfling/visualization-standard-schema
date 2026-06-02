from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vss.models import EntityUpsertMessage, VssScene
from vss.util import dumps_json, write_text_file


def main() -> None:
    destinations = {
        "schemas/vss-message.pydantic.schema.json": EntityUpsertMessage.export_json_schema(),
        "schemas/vss-scene.pydantic.schema.json": VssScene.model_json_schema(),
    }

    for destination, schema in destinations.items():
        write_text_file(Path(destination), dumps_json(schema, indent=2), encoding="utf-8")
        print(destination)


if __name__ == "__main__":
    main()
