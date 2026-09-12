from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import pytest

from swing_trader.prospective_recorder import (
    DEFAULT_LOCK_PATH,
    DEFAULT_PROTOCOL_PATH,
    capture_snapshot,
    load_locked_protocol,
    required_symbols,
    verify_snapshot_archive,
)
from swing_trader.prospective_recorder_cli import build_parser


def _source_frame() -> pd.DataFrame:
    index = pd.to_datetime(["2026-09-13", "2026-09-14", "2026-09-15"])
    return pd.DataFrame(
        {
            "Open": [100.0, 101.0, 102.0],
            "High": [102.0, 103.0, 104.0],
            "Low": [99.0, 100.0, 101.0],
            "Close": [101.0, 102.0, 103.0],
            "Volume": [1000.0, 1100.0, 1200.0],
        },
        index=index,
    )


def test_registered_protocol_matches_lock() -> None:
    protocol, lock, digest = load_locked_protocol()

    assert protocol["protocol"]["id"] == "PROSPECTIVE-v1-holdout"
    assert digest == lock["protocol_sha256"]
    assert lock["frozen_source_commit"] == protocol["protocol"]["frozen_source_commit"]
    assert lock["warmup_start"] == "2020-01-01"


def test_protocol_lock_rejects_mutated_registered_bytes(tmp_path: Path) -> None:
    mutated = tmp_path / "protocol.yaml"
    mutated.write_bytes(DEFAULT_PROTOCOL_PATH.read_bytes() + b"\n")

    with pytest.raises(RuntimeError, match="protocol lock"):
        load_locked_protocol(mutated, DEFAULT_LOCK_PATH)


def test_required_symbols_include_unique_benchmarks() -> None:
    protocol, _, _ = load_locked_protocol()

    assert required_symbols(protocol) == ["BTC-USD", "SOL-USD", "META", "NVDA", "QQQ"]


def test_prestart_capture_produces_no_snapshot_or_download(tmp_path: Path) -> None:
    calls: list[str] = []

    def downloader(symbol: str, start: str, end: str | None) -> pd.DataFrame:
        calls.append(symbol)
        return _source_frame()

    result = capture_snapshot(
        tmp_path,
        downloader=downloader,
        recorded_at=datetime(2026, 9, 14, 2, 17, tzinfo=UTC),
        commit_sha="test-sha",
    )

    assert result is None
    assert calls == []
    assert list(tmp_path.iterdir()) == []


def test_capture_uses_current_utc_date_as_exclusive_cutoff_and_downloads_once_per_symbol(
    tmp_path: Path,
) -> None:
    calls: list[tuple[str, str, str | None]] = []

    def downloader(symbol: str, start: str, end: str | None) -> pd.DataFrame:
        calls.append((symbol, start, end))
        return _source_frame()

    result = capture_snapshot(
        tmp_path,
        downloader=downloader,
        recorded_at=datetime(2026, 9, 15, 2, 17, tzinfo=UTC),
        commit_sha="test-sha",
    )

    assert result is not None
    assert len(calls) == 5
    assert {symbol for symbol, _, _ in calls} == {
        "BTC-USD",
        "SOL-USD",
        "META",
        "NVDA",
        "QQQ",
    }
    assert {start for _, start, _ in calls} == {"2020-01-01"}
    assert {end for _, _, end in calls} == {"2026-09-15"}
    assert result.manifest["capture"]["observation_date"] == "2026-09-15"
    assert result.manifest["capture"]["data_cutoff_exclusive"] == "2026-09-15"
    assert result.manifest["research_integrity"]["historical_backfill_supported"] is False
    assert result.manifest["research_integrity"]["strategy_evaluation_included"] is False

    for record in result.manifest["source"].values():
        assert record["rows"] == 2
        assert record["last_observation"] == "2026-09-14"
        stored = pd.read_csv(result.snapshot_dir / record["path"], parse_dates=["Date"])
        assert stored["Date"].max() == pd.Timestamp("2026-09-14")

    verified = verify_snapshot_archive(result.archive_path)
    assert verified["capture"]["observation_date"] == "2026-09-15"
    assert result.archive_path.name.endswith(f"-{result.archive_sha256}.zip")


def test_same_input_clock_and_code_produce_identical_archive_bytes(tmp_path: Path) -> None:
    def downloader(symbol: str, start: str, end: str | None) -> pd.DataFrame:
        return _source_frame()

    recorded_at = datetime(2026, 9, 15, 2, 17, tzinfo=UTC)
    first = capture_snapshot(
        tmp_path / "first",
        downloader=downloader,
        recorded_at=recorded_at,
        commit_sha="test-sha",
    )
    second = capture_snapshot(
        tmp_path / "second",
        downloader=downloader,
        recorded_at=recorded_at,
        commit_sha="test-sha",
    )

    assert first is not None and second is not None
    assert first.archive_sha256 == second.archive_sha256
    assert first.archive_path.read_bytes() == second.archive_path.read_bytes()


def test_capture_rejects_naive_injected_clock(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        capture_snapshot(tmp_path, recorded_at=datetime(2026, 9, 15, 2, 17))


def test_cli_has_no_historical_observation_date_argument() -> None:
    parser = build_parser()
    destinations = {action.dest for action in parser._actions}

    assert "observation_date" not in destinations
    assert "date" not in destinations


def test_recorder_workflow_is_append_only_and_has_no_backfill_input() -> None:
    workflow = Path(".github/workflows/prospective-v1-holdout-recorder.yml").read_text(
        encoding="utf-8"
    )

    assert "workflow_dispatch:" in workflow
    assert "observation_date:" not in workflow
    assert "--clobber" not in workflow
    assert "gh release upload" in workflow
    assert "prospective-v1-holdout-data-" in workflow
    assert "02:17" not in workflow  # cron is UTC fields, not prose that could drift.
    assert "17 2 * * *" in workflow
