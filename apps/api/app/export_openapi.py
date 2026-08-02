from __future__ import annotations

import argparse
import json
from pathlib import Path

from .main import app


def main() -> None:
    parser = argparse.ArgumentParser(description="Exporta el contrato OpenAPI estable.")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    output: Path = args.output
    output.write_text(
        json.dumps(app.openapi(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
