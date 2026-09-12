from __future__ import annotations

import argparse

from .knowledge_registry import check_registry, write_registry


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate or verify the deterministic external-knowledge registry."
    )
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify that knowledge/registry.json exactly matches canonical source/note records.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    path = check_registry(args.root) if args.check else write_registry(args.root)
    print(path)


if __name__ == "__main__":
    main()
