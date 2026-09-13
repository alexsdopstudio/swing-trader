from __future__ import annotations

import argparse
import json
from typing import Any

from .paper_operations import (
    DECISIONS,
    EXIT_REASONS,
    PAPER_MODE,
    brief_as_dict,
    build_daily_brief,
    load_paper_ledger,
    load_paper_operations_config,
    record_decision,
    record_paper_entry,
    record_paper_exit,
    render_daily_brief,
)


def _add_config_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--operations-config",
        default="config/paper-operations.yaml",
        help="Path to the paper-only operations configuration.",
    )


def _add_ledger_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--ledger", required=True, help="Append-only local paper ledger path.")


def _add_brief_arguments(parser: argparse.ArgumentParser) -> None:
    _add_config_argument(parser)
    _add_ledger_argument(parser)
    parser.add_argument("--archive", required=True, help="Verified daily scanner archive path.")
    parser.add_argument(
        "--archive-dir",
        help="Optional directory of prior daily scanner archives for trailing-stop reconstruction.",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Approval-only personal paper-trading operations. No broker order, credential, "
            "or automatic execution is supported."
        )
    )
    commands = parser.add_subparsers(dest="command", required=True)

    brief = commands.add_parser("brief", help="Render a deterministic daily paper brief.")
    _add_brief_arguments(brief)
    brief.add_argument("--format", choices=("markdown", "json"), default="markdown")

    decide = commands.add_parser("decide", help="Append an explicit human decision for a ticket.")
    _add_brief_arguments(decide)
    decide.add_argument("--ticket-id", required=True)
    decide.add_argument("--decision", choices=tuple(sorted(DECISIONS)), required=True)
    decide.add_argument("--note")

    entry = commands.add_parser(
        "record-entry",
        help="Append a deterministic paper fill after an approved ticket; no order is sent.",
    )
    _add_config_argument(entry)
    _add_ledger_argument(entry)
    entry.add_argument("--ticket-id", required=True)
    entry.add_argument("--execution-date", required=True)
    entry.add_argument(
        "--entry-reference",
        required=True,
        type=float,
        help="Observed next-open market reference used for the deterministic paper fill.",
    )

    exit_parser = commands.add_parser(
        "record-exit",
        help="Append a full paper exit record; no order is sent.",
    )
    _add_config_argument(exit_parser)
    _add_ledger_argument(exit_parser)
    exit_parser.add_argument("--ticket-id", required=True)
    exit_parser.add_argument("--execution-date", required=True)
    exit_parser.add_argument("--exit-reference", required=True, type=float)
    exit_parser.add_argument("--reason", choices=tuple(sorted(EXIT_REASONS)), required=True)

    validate = commands.add_parser("validate-ledger", help="Validate ledger ordering and provenance.")
    _add_config_argument(validate)
    _add_ledger_argument(validate)
    return parser


def _eligible_ticket(args: argparse.Namespace) -> Any:
    config = load_paper_operations_config(args.operations_config)
    brief = build_daily_brief(
        args.archive,
        config,
        args.ledger,
        archive_dir=args.archive_dir,
    )
    for candidate in brief.candidates:
        if candidate.ticket is not None and candidate.ticket.ticket_id == args.ticket_id:
            if candidate.status != "eligible":
                raise ValueError(f"ticket {args.ticket_id} is not eligible: {candidate.status}")
            return config, candidate.ticket
    raise ValueError(f"ticket {args.ticket_id} was not found in the current daily brief")


def _event_output(event: dict[str, Any]) -> str:
    return json.dumps(
        {
            "status": "recorded",
            "mode": PAPER_MODE,
            "event": event,
            "broker_orders_sent": False,
        },
        allow_nan=False,
        sort_keys=True,
    )


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.command == "brief":
            config = load_paper_operations_config(args.operations_config)
            brief = build_daily_brief(
                args.archive,
                config,
                args.ledger,
                archive_dir=args.archive_dir,
            )
            if args.format == "json":
                print(json.dumps(brief_as_dict(brief), allow_nan=False, indent=2, sort_keys=True))
            else:
                print(render_daily_brief(brief))
            return
        if args.command == "decide":
            config, ticket = _eligible_ticket(args)
            event = record_decision(
                args.ledger,
                config,
                ticket,
                args.decision,
                note=args.note,
            )
            print(_event_output(event))
            return
        config = load_paper_operations_config(args.operations_config)
        if args.command == "record-entry":
            event = record_paper_entry(
                args.ledger,
                config,
                args.ticket_id,
                args.execution_date,
                args.entry_reference,
            )
            print(_event_output(event))
            return
        if args.command == "record-exit":
            event = record_paper_exit(
                args.ledger,
                config,
                args.ticket_id,
                args.execution_date,
                args.exit_reference,
                args.reason,
            )
            print(_event_output(event))
            return
        state = load_paper_ledger(args.ledger, config)
        print(
            json.dumps(
                {
                    "status": "valid",
                    "mode": PAPER_MODE,
                    "event_count": len(state.events),
                    "open_position_count": len(state.positions),
                    "cash": state.cash,
                    "broker_orders_sent": False,
                },
                allow_nan=False,
                sort_keys=True,
            )
        )
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
