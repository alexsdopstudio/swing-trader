from __future__ import annotations

import json
import sys
from datetime import UTC, date, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from swing_trader.daily_scan_recorder import capture_daily_scan
from swing_trader.paper_operations import (
    build_daily_brief,
    load_paper_ledger,
    load_paper_operations_config,
    record_decision,
    record_paper_entry,
    record_paper_exit,
    render_daily_brief,
)
from swing_trader.paper_operations_cli import main as paper_operations_main


def _write_configs(tmp_path: Path) -> tuple[Path, Path]:
    universe_path = tmp_path / "universe.yaml"
    universe_path.write_text(
        """benchmark_equities: BENCH
benchmark_crypto: BENCH

assets:
  - symbol: AAA
    asset_class: equity
  - symbol: BBB
    asset_class: equity
""",
        encoding="utf-8",
    )
    costs_path = tmp_path / "execution-costs.yaml"
    costs_path.write_text(
        """models:
  default:
    commission_bps: 0.0
    spread_bps: 0.0
    slippage_bps: 0.0
  equity:
    commission_bps: 10.0
    spread_bps: 10.0
    slippage_bps: 10.0
""",
        encoding="utf-8",
    )
    operations_path = tmp_path / "paper-operations.yaml"
    operations_path.write_text(
        """schema_version: 1
mode: paper
approval_required: true
account:
  starting_equity: 1000.0
  currency: USD
execution_costs_path: execution-costs.yaml
""",
        encoding="utf-8",
    )
    return universe_path, operations_path


def _frame(symbol: str) -> pd.DataFrame:
    index = pd.date_range("2025-12-01", "2026-09-20", freq="D")
    rates = {"AAA": 1.015, "BBB": 1.012, "BENCH": 1.005}
    close = 100.0 * np.power(rates[symbol], np.arange(len(index), dtype=float))
    volume = np.full(len(index), 1_000.0)
    volume[-1] = 2_000.0
    return pd.DataFrame(
        {
            "Open": close * 0.998,
            "High": close * 1.001,
            "Low": close * 0.997,
            "Close": close,
            "Volume": volume,
        },
        index=index,
    )


def _capture(archive_dir: Path, universe_path: Path, observation_date: date) -> Path:
    def downloader(symbol: str, start: str, end: str | None) -> pd.DataFrame:
        assert start == "2015-01-01"
        assert end == observation_date.isoformat()
        return _frame(symbol)

    result = capture_daily_scan(
        archive_dir,
        config_path=universe_path,
        downloader=downloader,
        recorded_at=datetime.combine(observation_date, datetime.min.time(), tzinfo=UTC),
        commit_sha="paper-operations-test",
    )
    return result.archive_path


def _brief(tmp_path: Path) -> tuple[Path, Path, Path, object]:
    universe_path, operations_path = _write_configs(tmp_path)
    archive_dir = tmp_path / "archives"
    archive = _capture(archive_dir, universe_path, date(2026, 9, 15))
    ledger = tmp_path / "paper-ledger.jsonl"
    config = load_paper_operations_config(operations_path)
    brief = build_daily_brief(archive, config, ledger, archive_dir=archive_dir)
    return archive, archive_dir, ledger, brief


def _ticket(brief: object, symbol: str):
    candidates = getattr(brief, "candidates")
    for candidate in candidates:
        if candidate.symbol == symbol:
            assert candidate.ticket is not None
            return candidate.ticket
    raise AssertionError(f"ticket for {symbol} was not found")


def test_operations_config_cannot_override_frozen_v1_risk_settings(tmp_path: Path) -> None:
    _, operations_path = _write_configs(tmp_path)
    operations_path.write_text(
        operations_path.read_text(encoding="utf-8") + "risk_fraction: 0.01\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unexpected risk_fraction"):
        load_paper_operations_config(operations_path)


def test_daily_brief_is_deterministic_and_only_offers_long_buy_candidates(tmp_path: Path) -> None:
    archive, archive_dir, ledger, first = _brief(tmp_path)
    config = load_paper_operations_config(tmp_path / "paper-operations.yaml")
    second = build_daily_brief(archive, config, ledger, archive_dir=archive_dir)

    first_ticket = _ticket(first, "AAA")
    second_ticket = _ticket(second, "AAA")
    assert first_ticket.ticket_id == second_ticket.ticket_id
    assert first_ticket.ticket_sha256 == second_ticket.ticket_sha256
    assert first_ticket.signal_date < first_ticket.observation_date
    assert first_ticket.entry_timing == "next_available_open_after_signal"
    assert first_ticket.initial_stop < first_ticket.expected_entry_fill
    assert first_ticket.planned_initial_loss <= 5.0 + 1e-9
    assert "Paper-only and approval-only" in render_daily_brief(first)
    assert "sends no broker order" in render_daily_brief(first)


def test_approved_ticket_requires_later_date_and_records_deterministic_paper_fill(
    tmp_path: Path,
) -> None:
    _, _, ledger, brief = _brief(tmp_path)
    config = load_paper_operations_config(tmp_path / "paper-operations.yaml")
    ticket = _ticket(brief, "AAA")
    record_decision(
        ledger,
        config,
        ticket,
        "approved",
        event_id="0" * 32,
        event_at=datetime(2026, 9, 15, 8, tzinfo=UTC),
    )

    with pytest.raises(ValueError, match="signal date"):
        record_paper_entry(
            ledger,
            config,
            ticket.ticket_id,
            ticket.signal_date,
            ticket.planning_reference,
            event_id="1" * 32,
            event_at=datetime(2026, 9, 15, 9, tzinfo=UTC),
        )

    event = record_paper_entry(
        ledger,
        config,
        ticket.ticket_id,
        "2026-09-15",
        ticket.planning_reference,
        event_id="1" * 32,
        event_at=datetime(2026, 9, 15, 9, tzinfo=UTC),
    )
    model = config.portfolio.cost_model_for("equity")
    assert event["paper_fill"] == pytest.approx(model.buy_fill(ticket.planning_reference))
    state = load_paper_ledger(ledger, config)
    position = state.positions["AAA"]
    assert position.entry_date == date(2026, 9, 15)
    assert position.initial_loss <= 5.0 + 1e-9


def test_ledger_refuses_duplicate_decisions_out_of_order_events_and_config_mismatch(
    tmp_path: Path,
) -> None:
    _, _, ledger, brief = _brief(tmp_path)
    config = load_paper_operations_config(tmp_path / "paper-operations.yaml")
    ticket = _ticket(brief, "AAA")
    second_ticket = _ticket(brief, "BBB")
    record_decision(
        ledger,
        config,
        ticket,
        "declined",
        event_id="2" * 32,
        event_at=datetime(2026, 9, 15, 8, tzinfo=UTC),
    )
    with pytest.raises(ValueError, match="timestamps must remain append-only"):
        record_decision(
            ledger,
            config,
            second_ticket,
            "declined",
            event_id="3" * 32,
            event_at=datetime(2026, 9, 15, 7, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="already has a human decision"):
        record_decision(
            ledger,
            config,
            ticket,
            "declined",
            event_id="4" * 32,
            event_at=datetime(2026, 9, 15, 9, tzinfo=UTC),
        )

    event = json.loads(ledger.read_text(encoding="utf-8"))
    event["sequence"] = 2
    ledger.write_text(json.dumps(event) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="append-only"):
        load_paper_ledger(ledger, config)

    ledger.unlink()
    record_decision(
        ledger,
        config,
        ticket,
        "declined",
        event_id="5" * 32,
        event_at=datetime(2026, 9, 15, 8, tzinfo=UTC),
    )
    changed_path = tmp_path / "changed-paper-operations.yaml"
    changed_path.write_text(
        (tmp_path / "paper-operations.yaml").read_text(encoding="utf-8").replace(
            "starting_equity: 1000.0", "starting_equity: 2000.0"
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="provenance"):
        load_paper_ledger(ledger, load_paper_operations_config(changed_path))


def test_entries_cannot_bypass_open_risk_and_exit_stays_append_only(tmp_path: Path) -> None:
    _, _, ledger, brief = _brief(tmp_path)
    config = load_paper_operations_config(tmp_path / "paper-operations.yaml")
    first = _ticket(brief, "AAA")
    second = _ticket(brief, "BBB")
    record_decision(
        ledger,
        config,
        first,
        "approved",
        event_id="5" * 32,
        event_at=datetime(2026, 9, 15, 8, tzinfo=UTC),
    )
    record_paper_entry(
        ledger,
        config,
        first.ticket_id,
        "2026-09-15",
        first.planning_reference,
        event_id="6" * 32,
        event_at=datetime(2026, 9, 15, 9, tzinfo=UTC),
    )
    record_decision(
        ledger,
        config,
        second,
        "approved",
        event_id="7" * 32,
        event_at=datetime(2026, 9, 15, 10, tzinfo=UTC),
    )
    record_paper_entry(
        ledger,
        config,
        second.ticket_id,
        "2026-09-15",
        second.planning_reference,
        event_id="8" * 32,
        event_at=datetime(2026, 9, 15, 11, tzinfo=UTC),
    )
    state = load_paper_ledger(ledger, config)
    assert sum(position.initial_loss for position in state.positions.values()) <= 20.0 + 1e-9

    before = ledger.read_bytes()
    exit_event = record_paper_exit(
        ledger,
        config,
        first.ticket_id,
        "2026-09-16",
        first.planning_reference * 0.95,
        "operator_recorded",
        event_id="9" * 32,
        event_at=datetime(2026, 9, 16, 8, tzinfo=UTC),
    )
    assert exit_event["source"] == "paper"
    assert ledger.read_bytes().startswith(before)
    state = load_paper_ledger(ledger, config)
    assert "AAA" not in state.positions
    assert "BBB" in state.positions


def test_brief_reconstructs_monotonic_trailing_stop_from_archives(tmp_path: Path) -> None:
    first_archive, archive_dir, ledger, brief = _brief(tmp_path)
    universe_path = tmp_path / "universe.yaml"
    config = load_paper_operations_config(tmp_path / "paper-operations.yaml")
    ticket = _ticket(brief, "AAA")
    record_decision(
        ledger,
        config,
        ticket,
        "approved",
        event_id="a" * 32,
        event_at=datetime(2026, 9, 15, 8, tzinfo=UTC),
    )
    record_paper_entry(
        ledger,
        config,
        ticket.ticket_id,
        "2026-09-15",
        ticket.planning_reference,
        event_id="b" * 32,
        event_at=datetime(2026, 9, 15, 9, tzinfo=UTC),
    )
    second_archive = _capture(archive_dir, universe_path, date(2026, 9, 16))
    first_again = build_daily_brief(
        first_archive,
        config,
        ledger,
        archive_dir=archive_dir,
    )
    before_next_close = next(
        item for item in first_again.account.marked_positions if item.position.ticket.symbol == "AAA"
    )
    assert before_next_close.last_mark_date is None
    second = build_daily_brief(second_archive, config, ledger, archive_dir=archive_dir)
    marked = next(item for item in second.account.marked_positions if item.position.ticket.symbol == "AAA")
    assert marked.last_mark_date == date(2026, 9, 15)
    assert marked.current_stop >= marked.position.initial_stop


def test_cli_renders_json_brief_without_broker_side_effect(tmp_path: Path, capsys, monkeypatch) -> None:
    archive, archive_dir, ledger, _ = _brief(tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "swing-paper-ops",
            "brief",
            "--operations-config",
            str(tmp_path / "paper-operations.yaml"),
            "--ledger",
            str(ledger),
            "--archive",
            str(archive),
            "--archive-dir",
            str(archive_dir),
            "--format",
            "json",
        ],
    )
    paper_operations_main()
    output = json.loads(capsys.readouterr().out)
    assert output["mode"] == "paper"
    assert output["approval_required"] is True
    assert output["boundaries"]["broker_orders_sent"] is False
    assert output["boundaries"]["automatic_execution"] is False
