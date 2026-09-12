from __future__ import annotations

import argparse
from pathlib import Path

from .universe_breadth import run_universe_breadth


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the preregistered EXP-0006 configured-universe breadth diagnostic."
    )
    parser.add_argument(
        "--config",
        default="experiments/EXP-0006-configured-universe-breadth/config.yaml",
        help="Path to EXP-0006 configuration.",
    )
    parser.add_argument(
        "--output-dir",
        default=".artifacts/EXP-0006",
        help="Directory for generated EXP-0006 artifacts.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    run_universe_breadth(Path(args.config), Path(args.output_dir))


if __name__ == "__main__":
    main()
