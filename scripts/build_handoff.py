from __future__ import annotations

import argparse
import json
from pathlib import Path

from swing_trader.handoff import write_handoff


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate cross-agent handoff artifacts.")
    parser.add_argument("--root", default=None, help="Repository root. Defaults to script parent repo.")
    parser.add_argument("--metadata-file", default=None, help="JSON file containing `pr` and `checks`.")
    parser.add_argument("--output-dir", default=None, help="Output directory. Defaults to .ai/.")
    args = parser.parse_args()

    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[1]
    metadata: dict = {}
    if args.metadata_file:
        metadata = json.loads(Path(args.metadata_file).read_text(encoding="utf-8"))

    output_dir = Path(args.output_dir).resolve() if args.output_dir else None
    json_path, markdown_path = write_handoff(
        root,
        output_dir=output_dir,
        pr=metadata.get("pr"),
        checks=metadata.get("checks"),
    )
    print(json_path)
    print(markdown_path)


if __name__ == "__main__":
    main()
