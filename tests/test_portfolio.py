import pandas as pd
import pytest

from swing_trader.portfolio import (
    PortfolioAsset,
    PortfolioBacktestConfig,
    backtest_portfolio,
)


def _asset(
    symbol: str,
    opens: list[float],
    lows: list[float],
    closes: list[float],
    scores: list[int],
) -> PortfolioAsset:
    index = pd.date_range("2026-01-01", periods=len(opens), freq="D")
    data = pd.DataFrame(
        {
            "Open": opens,
            "High": [max(open_, close) + 2 for open_, close in zip(opens, closes)],
            "Low": lows,
            "Close": closes,
            "atr14": [5.0] * len(opens),
            "high20": [close - 10 for close in closes],
            "sma50": [close - 20 for close in closes],
            "sma200": [close - 30 for close in closes],
        },
        index=index,
    )
    return PortfolioAsset(
        symbol=symbol,
        data=data,
        scores=pd.Series(scores, index=index),
        regime=pd.Series(True, index=index),
    )


def test_signal_executes_at_next_open_and_liquidates_at_end() -> None:
    asset = _asset(
        "TEST",
        opens=[100.0, 120.0, 130.0],
        lows=[95.0, 115.0, 129.0],
        closes=[110.0, 125.0, 140.0],
        scores=[80, 0, 0],
    )

    result = backtest_portfolio([asset], PortfolioBacktestConfig(initial_equity=1_000.0))

    assert len(result.trades) == 1
    trade = result.trades[0]
    assert trade.entry_date == pd.Timestamp("2026-01-02")
    assert trade.entry == 120.0
    assert trade.exit_date == pd.Timestamp("2026-01-03")
    assert trade.exit == 140.0
    assert trade.exit_reason == "end_of_test"
    assert result.equity_curve.iloc[-1] == pytest.approx(1_010.0)


def test_initial_stop_is_active_on_entry_bar() -> None:
    asset = _asset(
        "TEST",
        opens=[100.0, 120.0],
        lows=[95.0, 109.0],
        closes=[110.0, 130.0],
        scores=[80, 0],
    )

    result = backtest_portfolio([asset], PortfolioBacktestConfig(initial_equity=1_000.0))

    trade = result.trades[0]
    assert trade.entry == 120.0
    assert trade.exit == 110.0
    assert trade.entry_date == trade.exit_date
    assert trade.exit_reason == "stop"
    assert trade.r_multiple == pytest.approx(-1.0)


def test_gap_through_trailing_stop_fills_at_open() -> None:
    asset = _asset(
        "TEST",
        opens=[100.0, 120.0, 100.0],
        lows=[95.0, 115.0, 95.0],
        closes=[110.0, 125.0, 105.0],
        scores=[80, 0, 0],
    )

    result = backtest_portfolio([asset], PortfolioBacktestConfig(initial_equity=1_000.0))

    trade = result.trades[0]
    assert trade.exit_date == pd.Timestamp("2026-01-03")
    assert trade.exit == 100.0
    assert trade.exit_reason == "stop_gap"
    assert trade.r_multiple == pytest.approx(-2.0)


def test_score_priority_is_deterministic_when_max_positions_is_one() -> None:
    lower = _asset(
        "AAA",
        opens=[100.0, 100.0],
        lows=[95.0, 95.0],
        closes=[110.0, 110.0],
        scores=[80, 0],
    )
    higher = _asset(
        "BBB",
        opens=[100.0, 100.0],
        lows=[95.0, 95.0],
        closes=[110.0, 110.0],
        scores=[90, 0],
    )
    config = PortfolioBacktestConfig(initial_equity=1_000.0, max_positions=1)

    result = backtest_portfolio([lower, higher], config)

    assert len(result.trades) == 1
    assert result.trades[0].symbol == "BBB"


def test_aggregate_open_risk_reduces_second_position_size() -> None:
    first = _asset(
        "AAA",
        opens=[100.0, 100.0],
        lows=[95.0, 95.0],
        closes=[110.0, 110.0],
        scores=[90, 0],
    )
    second = _asset(
        "BBB",
        opens=[100.0, 100.0],
        lows=[95.0, 95.0],
        closes=[110.0, 110.0],
        scores=[80, 0],
    )
    config = PortfolioBacktestConfig(
        initial_equity=1_000.0,
        max_positions=2,
        risk_fraction=0.005,
        max_open_risk_fraction=0.0075,
    )

    result = backtest_portfolio([first, second], config)

    assert len(result.trades) == 2
    risks = {trade.symbol: trade.initial_risk for trade in result.trades}
    assert risks["AAA"] == pytest.approx(5.0)
    assert risks["BBB"] == pytest.approx(2.5)
    assert sum(risks.values()) == pytest.approx(7.5)
