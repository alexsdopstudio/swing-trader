from __future__ import annotations

import argparse
import json

from .daily_scan_recorder import (
    DEFAULT_CONFIG_PATH,
    capture_daily_scan,
    verify_daily_scan_archive,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Record the scanner state visible at the current UTC information boundary. "
            "Historical observation dates cannot be supplied."
        )
    )
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG_PATH),
        help="Path to the scanner universe configuration.",
    )
    parser.add_argument("--output-dir", required=True, help="Directory for daily scan artifacts.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = capture_daily_scan(args.output_dir, config_path=args.config)
    manifest = verify_daily_scan_archive(result.archive_path)
    print(
        json.dumps(
            {
                "status": "recorded",
                "observation_date": result.observation_date.isoformat(),
                "archive": str(result.archive_path),
                "archive_sha256": result.archive_sha256,
                "source_count": len(manifest["source"]),
                "result_count": manifest["outputs"]["json"]["rows"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
