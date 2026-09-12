from __future__ import annotations

import argparse
import json

from .prospective_recorder import (
    DEFAULT_LOCK_PATH,
    DEFAULT_PROTOCOL_PATH,
    capture_snapshot,
    verify_snapshot_archive,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Record the current UTC prospective holdout provider snapshot. "
            "Historical observation dates cannot be supplied."
        )
    )
    parser.add_argument(
        "--protocol",
        default=str(DEFAULT_PROTOCOL_PATH),
        help="Path to the preregistered holdout protocol.",
    )
    parser.add_argument(
        "--lock",
        default=str(DEFAULT_LOCK_PATH),
        help="Path to the immutable protocol lock.",
    )
    parser.add_argument("--output-dir", required=True, help="Directory for snapshot artifacts.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = capture_snapshot(
        args.output_dir,
        protocol_path=args.protocol,
        lock_path=args.lock,
    )
    if result is None:
        print("Holdout recorder: pre-start date; no prospective snapshot produced.")
        return

    manifest = verify_snapshot_archive(result.archive_path)
    print(
        json.dumps(
            {
                "status": "recorded",
                "observation_date": result.observation_date.isoformat(),
                "archive": str(result.archive_path),
                "archive_sha256": result.archive_sha256,
                "source_count": len(manifest["source"]),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
