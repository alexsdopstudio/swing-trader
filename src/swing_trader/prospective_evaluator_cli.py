from __future__ import annotations

import argparse
from pathlib import Path

from .prospective_evaluator import evaluate_holdout_archives
from .prospective_recorder import DEFAULT_LOCK_PATH, DEFAULT_PROTOCOL_PATH


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Replay frozen v1 from recorded prospective holdout archives only."
    )
    parser.add_argument(
        "--archives",
        required=True,
        help="Directory containing canonical PROSPECTIVE-v1-holdout ZIP archives.",
    )
    parser.add_argument(
        "--protocol",
        default=str(DEFAULT_PROTOCOL_PATH),
        help="Path to the registered prospective protocol.",
    )
    parser.add_argument(
        "--lock",
        default=str(DEFAULT_LOCK_PATH),
        help="Path to the registered protocol lock.",
    )
    parser.add_argument(
        "--output-dir",
        default=".artifacts/PROSPECTIVE-v1-holdout/evaluation",
        help="Directory for read-only derived evaluator outputs.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    evaluate_holdout_archives(
        Path(args.archives),
        Path(args.output_dir),
        protocol_path=Path(args.protocol),
        lock_path=Path(args.lock),
    )


if __name__ == "__main__":
    main()
