from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


def main() -> None:
    from swing_trader.handoff import write_handoff

    parser = argparse.ArgumentParser(description="Generate cross-agent handoff artifacts.")
    parser.add_argument("--root", default=None, help="Repository root. Defaults to script parent repo.")
    parser.add_argument("--metadata-file", default=None, help="JSON file containing `pr` and `checks`.")
    parser.add_argument("--output-dir", default=None, help="Output directory. Defaults to .ai/.")
    args = parser.parse_args()

    root = Path(args.root).resolve() if args.root else REPO_ROOT
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
