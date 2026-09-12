from __future__ import annotations

import argparse
from pathlib import Path

from .experiment_registry import check_registry, write_registry


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build or verify the deterministic repository experiment registry."
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root containing experiments/ (default: current directory).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if experiments/registry.json differs from canonical experiment/protocol files.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    root = Path(args.root)
    path = check_registry(root) if args.check else write_registry(root)
    action = "Current" if args.check else "Wrote"
    print(f"{action} experiment registry: {path}")


if __name__ == "__main__":
    main()
