import pandas as pd
import pytest

from swing_trader.historical import historical_regime, historical_scores
from swing_trader.metrics import calculate_metrics
from swing_trader.portfolio import PortfolioBacktestResult, PortfolioTrade


def test_historical_scores_reach_full_score_with_strong_relative_strength() -> None:
    index = pd.date_range("2025-01-01", periods=80, freq="D")
    close = pd.Series(range(100, 180), index=index, dtype=float)
    asset = pd.DataFrame(
        {
            "Close": close,
            "sma50": close - 10,
            "sma200": close - 20,
            "roc20": 0.20,
            "roc60": 0.30,
            "high20": close - 1,
            "high50": close - 2,
            "volume_ratio": 2.0,
        },
        index=index,
    )
    benchmark = pd.DataFrame({"roc60": 0.05}, index=index)

    scores = historical_scores(asset, benchmark)

    assert scores.iloc[-1] == 100


def test_historical_regime_aligns_without_future_fill() -> None:
    benchmark_index = pd.to_datetime(["2026-01-01", "2026-01-03"])
    benchmark = pd.DataFrame(
        {"Close": [90.0, 120.0], "sma200": [100.0, 100.0]},
        index=benchmark_index,
    )
    target = pd.date_range("2025-12-31", "2026-01-03", freq="D")

    regime = historical_regime(benchmark, target)

    assert regime.tolist() == [False, False, False, True]


def test_metrics_use_realized_trade_r_and_equity_curve() -> None:
    index = pd.date_range("2026-01-01", periods=4, freq="D")
    trades = (
        PortfolioTrade(
            symbol="WIN",
            entry_date=index[0],
            exit_date=index[1],
            entry=100.0,
            exit=120.0,
            units=1.0,
            initial_stop=90.0,
            initial_risk=10.0,
            pnl=20.0,
            r_multiple=2.0,
            signal_score=90,
            exit_reason="stop",
        ),
        PortfolioTrade(
            symbol="LOSS",
            entry_date=index[1],
            exit_date=index[2],
            entry=100.0,
            exit=90.0,
            units=1.0,
            initial_stop=90.0,
            initial_risk=10.0,
            pnl=-10.0,
            r_multiple=-1.0,
            signal_score=80,
            exit_reason="stop",
        ),
    )
    result = PortfolioBacktestResult(
        trades=trades,
        equity_curve=pd.Series([1_000.0, 1_100.0, 990.0, 1_200.0], index=index),
        exposure_curve=pd.Series([0.0, 0.5, 0.5, 0.0], index=index),
        position_count_curve=pd.Series([0, 1, 1, 0], index=index),
    )

    metrics = calculate_metrics(result)

    assert metrics.total_return == pytest.approx(0.20)
    assert metrics.max_drawdown == pytest.approx(-0.10)
    assert metrics.profit_factor == pytest.approx(2.0)
    assert metrics.win_rate == pytest.approx(0.5)
    assert metrics.expectancy_r == pytest.approx(0.5)
    assert metrics.average_winner_r == pytest.approx(2.0)
    assert metrics.average_loser_r == pytest.approx(-1.0)
    assert metrics.average_exposure == pytest.approx(0.25)
    assert metrics.best_r == pytest.approx(2.0)
    assert metrics.worst_r == pytest.approx(-1.0)
