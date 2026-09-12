from pathlib import Path

import pandas as pd
import pytest

from swing_trader.execution import ExecutionCostModel
from swing_trader.metrics import calculate_equity_curve_metrics
from swing_trader.reference_baselines import buy_and_hold, equal_weight_basket
from swing_trader.reference_comparison import load_reference_comparison_config


def _prices(start: str, opens: list[float], closes: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {"Open": opens, "Close": closes},
        index=pd.date_range(start, periods=len(opens), freq="D"),
    )


def test_buy_and_hold_applies_entry_and_terminal_execution_costs() -> None:
    data = _prices("2026-01-01", [100.0, 115.0], [110.0, 120.0])
    model = ExecutionCostModel(commission_bps=10.0, spread_bps=20.0, slippage_bps=10.0)

    result = buy_and_hold(data, 1_000.0, model)

    expected_units = 1_000.0 / model.buy_cash_per_unit(100.0)
    expected_exit_fill = model.sell_fill(120.0)
    expected_terminal = expected_units * expected_exit_fill
    expected_terminal -= model.commission(expected_terminal)

    assert result.units == pytest.approx(expected_units)
    assert result.equity_curve.iloc[-1] == pytest.approx(expected_terminal)
    assert result.position_value_curve.iloc[-1] == 0.0
    assert result.exposure_curve.iloc[-1] == 0.0
    assert result.total_execution_cost > 0.0


def test_equal_weight_basket_handles_mixed_calendars_without_synthetic_entries() -> None:
    first = buy_and_hold(
        _prices("2026-01-01", [100.0, 110.0], [110.0, 120.0]),
        500.0,
    )
    second = buy_and_hold(
        _prices("2026-01-02", [50.0, 50.0], [50.0, 55.0]),
        500.0,
    )

    basket = equal_weight_basket({"A": first, "B": second})

    assert basket.equity_curve.loc[pd.Timestamp("2026-01-01")] == pytest.approx(1_050.0)
    assert basket.position_value_curve.loc[pd.Timestamp("2026-01-01")] == pytest.approx(550.0)
    assert basket.equity_curve.loc[pd.Timestamp("2026-01-03")] == pytest.approx(1_150.0)
    assert basket.position_value_curve.loc[pd.Timestamp("2026-01-03")] == 0.0


def test_equity_curve_metrics_can_include_entry_cost_against_initial_equity() -> None:
    curve = pd.Series(
        [990.0, 1_100.0],
        index=pd.date_range("2026-01-01", periods=2, freq="D"),
    )

    metrics = calculate_equity_curve_metrics(curve, initial_equity=1_000.0)

    assert metrics.total_return == pytest.approx(0.10)
    assert metrics.max_drawdown == pytest.approx(-0.01)


def test_equal_weight_basket_rejects_unequal_allocations() -> None:
    first = buy_and_hold(_prices("2026-01-01", [100.0], [100.0]), 400.0)
    second = buy_and_hold(_prices("2026-01-01", [100.0], [100.0]), 600.0)

    with pytest.raises(ValueError, match="equal initial"):
        equal_weight_basket({"A": first, "B": second})


def test_exp0004_config_preregisters_reference_definitions() -> None:
    path = Path("experiments/EXP-0004-reference-baselines/config.yaml")
    config = load_reference_comparison_config(path)

    assert config["experiment"]["id"] == "EXP-0004"
    assert config["reference_baselines"] == {
        "per_symbol": "buy-and-hold",
        "portfolio": "equal-weight-buy-and-hold",
        "rebalance": "none",
        "entry": "first-evaluation-open",
        "exit": "final-evaluation-close",
    }
