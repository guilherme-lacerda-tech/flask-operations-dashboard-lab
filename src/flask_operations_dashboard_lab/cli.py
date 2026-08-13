from __future__ import annotations

import argparse
import json
from pathlib import Path

from flask_operations_dashboard_lab.service import OperationsService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Print a synthetic operations dashboard summary.")
    parser.add_argument("--database", default="operations-dashboard.sqlite3")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    service = OperationsService(Path(args.database))
    print(json.dumps(service.summary(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

