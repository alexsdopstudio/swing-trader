from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from swing_trader.portfolio import PortfolioBacktestConfig, PortfolioReplayBar, PortfolioReplaySession
from swing_trader.prospective_evaluator import evaluate_holdout_archives
from swing_trader.prospective_recorder import capture_snapshot


def _replay_row(
    *, open_price: float, high: float, low: float, close: float, atr: float = 2.0,
    high20: float = 100.0, sma50: float = 90.0, sma200: float = 80.0,
) -> pd.Series:
    return pd.Series({
        "Open": open_price, "High": high, "Low": low, "Close": close,
        "atr14": atr, "high20": high20, "sma50": sma50, "sma200": sma200,
    })


def test_replay_session_pending_signal_waits_for_next_asset_bar() -> None:
    session = PortfolioReplaySession(PortfolioBacktestConfig())
    day1 = pd.Timestamp("2026-09-14")
    day2 = pd.Timestamp("2026-09-15")
    day3 = pd.Timestamp("2026-09-16")

    session.process_date(day1, {"TEST": PortfolioReplayBar(
        symbol="TEST",
        row=_replay_row(open_price=99.0, high=106.0, low=98.0, close=105.0),
        score=80,
        regime=True,
    )})
    assert len(session.pending_signals) == 1
    assert not session.open_positions

    session.process_date(day2, {})
    assert len(session.pending_signals) == 1
    assert not session.open_positions

    session.process_date(day3, {"TEST": PortfolioReplayBar(
        symbol="TEST",
        row=_replay_row(open_price=103.0, high=105.0, low=102.0, close=104.0, high20=103.0),
        score=0,
        regime=True,
    )})
    assert not session.pending_signals
    assert len(session.open_positions) == 1
    assert session.open_positions[0].entry_date == day3
    assert not session.trades


def test_replay_session_terminal_liquidation_is_explicit() -> None:
    session = PortfolioReplaySession(PortfolioBacktestConfig())
    signal_day = pd.Timestamp("2026-09-14")
    entry_day = pd.Timestamp("2026-09-15")
    terminal_day = pd.Timestamp("2026-09-16")

    session.process_date(signal_day, {"TEST": PortfolioReplayBar(
        "TEST", _replay_row(open_price=99, high=106, low=98, close=105), 80, True
    )})
    session.process_date(entry_day, {"TEST": PortfolioReplayBar(
        "TEST", _replay_row(open_price=103, high=105, low=102, close=104, high20=103), 0, True
    )})
    assert len(session.open_positions) == 1
    session.process_date(terminal_day, {"TEST": PortfolioReplayBar(
        "TEST", _replay_row(open_price=104, high=106, low=103, close=105, high20=104), 0, True
    )}, terminal_symbols={"TEST"})
    assert not session.open_positions
    assert len(session.trades) == 1
    assert session.trades[0].exit_reason == "end_of_test"


def _market_frame(symbol: str, end: str, *, revise_prior: bool = False) -> pd.DataFrame:
    end_ts = pd.Timestamp(end)
    start = pd.Timestamp("2025-10-01")
    if symbol in {"META", "NVDA", "QQQ"}:
        index = pd.bdate_range(start, end_ts - pd.Timedelta(days=1))
    else:
        index = pd.date_range(start, end_ts - pd.Timedelta(days=1), freq="D")
    steps = np.arange(len(index), dtype=float)
    close = 100.0 * np.power(1.005, steps)
    frame = pd.DataFrame({
        "Open": close * 0.999,
        "High": close * 1.002,
        "Low": close * 0.997,
        "Close": close,
        "Volume": np.full(len(index), 1_000.0),
    }, index=index)
    breakout = pd.Timestamp("2026-09-14")
    if symbol == "BTC-USD" and breakout in frame.index:
        prior_high = float(frame.loc[frame.index < breakout, "High"].tail(50).max())
        frame.loc[breakout, ["Open", "High", "Low", "Close", "Volume"]] = [
            prior_high + 4.0, prior_high + 6.0, prior_high + 3.0, prior_high + 5.0, 4_000.0,
        ]
    if revise_prior and pd.Timestamp("2026-09-14") in frame.index:
        target = pd.Timestamp("2026-09-14")
        frame.loc[target, ["Open", "High", "Low", "Close"]] *= 1.001
    return frame


def _record(
    archive_dir: Path,
    observation_date: str,
    *,
    revise_prior: bool = False,
    omit_market_date_for: str | None = None,
) -> Path:
    recorded_at = datetime.fromisoformat(f"{observation_date}T01:00:00+00:00")
    market_date = pd.Timestamp(observation_date) - pd.Timedelta(days=1)

    def downloader(symbol: str, start: str, end: str | None) -> pd.DataFrame:
        assert end is not None
        frame = _market_frame(symbol, end, revise_prior=revise_prior)
        if symbol == omit_market_date_for:
            frame = frame.drop(market_date, errors="ignore")
        return frame

    result = capture_snapshot(
        archive_dir,
        downloader=downloader,
        recorded_at=recorded_at,
        commit_sha="synthetic-recorder-sha",
    )
    assert result is not None
    return result.archive_path


def test_evaluator_is_read_only_deterministic_and_uses_canonical_daily_chain(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    archives = tmp_path / "archives"
    _record(archives, "2026-09-15")
    _record(archives, "2026-09-16", revise_prior=True)

    def forbidden_download(*args, **kwargs):
        raise AssertionError("prospective evaluator must not download provider data")

    monkeypatch.setattr("swing_trader.data.download_daily", forbidden_download)
    first = evaluate_holdout_archives(archives, tmp_path / "out-a")
    second = evaluate_holdout_archives(archives, tmp_path / "out-b")

    assert first == second
    assert first["research_integrity"]["provider_downloads"] == 0
    assert first["research_integrity"]["validation_claim"] is False
    assert first["research_integrity"]["parameter_tuning_allowed"] is False
    assert first["evidence"]["processed_archive_count"] == 2
    assert first["evidence"]["first_missing_observation_date"] is None
    assert first["state"]["processed_through_market_date"] == "2026-09-15"
    assert (tmp_path / "out-a" / "state.json").read_bytes() == (tmp_path / "out-b" / "state.json").read_bytes()
    assert (tmp_path / "out-a" / "daily-state.csv").read_bytes() == (tmp_path / "out-b" / "daily-state.csv").read_bytes()

    daily = pd.read_csv(tmp_path / "out-a" / "daily-state.csv")
    assert daily["market_date"].tolist() == ["2026-09-14", "2026-09-15"]
    assert int(daily.iloc[0]["pending_signal_count"]) >= 1
    assert int(daily.iloc[1]["open_position_count"]) >= 1


def test_evaluator_stops_at_first_missing_canonical_observation(tmp_path: Path) -> None:
    archives = tmp_path / "archives"
    _record(archives, "2026-09-15")
    _record(archives, "2026-09-17", revise_prior=True)

    result = evaluate_holdout_archives(archives, tmp_path / "out")
    assert result["evidence"]["processed_archive_count"] == 1
    assert result["evidence"]["first_missing_observation_date"] == "2026-09-16"
    assert result["evidence"]["evidence_complete_through_available_range"] is False
    assert result["evidence"]["unprocessed_archives_after_gap"] == ["2026-09-17"]
    assert result["state"]["processed_through_market_date"] == "2026-09-14"


def test_evaluator_rejects_incomplete_new_crypto_market_date(tmp_path: Path) -> None:
    archives = tmp_path / "archives"
    _record(archives, "2026-09-15", omit_market_date_for="BTC-USD")

    with pytest.raises(RuntimeError, match="missing newly observable crypto bar"):
        evaluate_holdout_archives(archives, tmp_path / "out")


def test_evaluator_rejects_incomplete_equity_session(tmp_path: Path) -> None:
    archives = tmp_path / "archives"
    _record(archives, "2026-09-15", omit_market_date_for="META")

    with pytest.raises(RuntimeError, match="benchmark session but missing equity bar"):
        evaluate_holdout_archives(archives, tmp_path / "out")


def test_evaluator_rejects_duplicate_observation_dates(tmp_path: Path) -> None:
    archives = tmp_path / "archives"
    original = _record(archives, "2026-09-15")
    duplicate = archives / ("PROSPECTIVE-v1-holdout-2026-09-15-" + "0" * 64 + ".zip")
    shutil.copyfile(original, duplicate)
    with pytest.raises(RuntimeError, match="duplicate prospective archive date"):
        evaluate_holdout_archives(archives, tmp_path / "out")


def test_evaluator_rejects_archive_before_first_active_date(tmp_path: Path) -> None:
    archives = tmp_path / "archives"
    original = _record(archives, "2026-09-15")
    early = archives / ("PROSPECTIVE-v1-holdout-2026-09-14-" + "0" * 64 + ".zip")
    shutil.copyfile(original, early)
    original.unlink()
    with pytest.raises(RuntimeError, match="precedes first active observation"):
        evaluate_holdout_archives(archives, tmp_path / "out")
