from __future__ import annotations

import argparse

from .project_dashboard import DEFAULT_REPOSITORY, build_dashboard


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the deterministic read-only Swing Trader project dashboard."
    )
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--output-dir", required=True, help="Static site output directory.")
    parser.add_argument(
        "--repository",
        default=DEFAULT_REPOSITORY,
        help="Public GitHub repository in owner/name form for live read-only enrichment.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    output = build_dashboard(
        args.output_dir,
        root=args.root,
        repository=args.repository,
    )
    print(output)


if __name__ == "__main__":
    main()
