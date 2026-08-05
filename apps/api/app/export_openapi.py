from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .main import app


def stable_openapi_schema() -> dict[str, Any]:
    schema = app.openapi()
    paths = schema.get("paths", {})
    if isinstance(paths, dict):
        for path_item in paths.values():
            if not isinstance(path_item, dict):
                continue
            for operation in path_item.values():
                if not isinstance(operation, dict):
                    continue
                responses = operation.get("responses")
                if not isinstance(responses, dict):
                    continue
                unprocessable = responses.get("422")
                if isinstance(unprocessable, dict):
                    unprocessable["description"] = "Unprocessable Content"
    return schema


def main() -> None:
    parser = argparse.ArgumentParser(description="Exporta el contrato OpenAPI estable.")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    output: Path = args.output
    output.write_text(
        json.dumps(stable_openapi_schema(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
