from pathlib import Path

import pytest

from swing_trader.execution import ExecutionCostModel, load_execution_cost_models


def test_execution_cost_model_applies_adverse_prices_and_commission() -> None:
    model = ExecutionCostModel(
        commission_bps=10.0,
        spread_bps=20.0,
        slippage_bps=10.0,
    )

    assert model.buy_fill(100.0) == pytest.approx(100.2)
    assert model.sell_fill(100.0) == pytest.approx(99.8)
    assert model.commission(1_000.0) == pytest.approx(1.0)
    assert model.buy_cash_per_unit(100.0) == pytest.approx(100.3002)
    assert model.sell_net_per_unit(100.0) == pytest.approx(99.7002)


def test_long_risk_per_unit_includes_entry_and_stop_exit_friction() -> None:
    model = ExecutionCostModel(
        commission_bps=10.0,
        spread_bps=20.0,
        slippage_bps=10.0,
    )
    entry_fill = model.buy_fill(100.0)

    risk = model.long_risk_per_unit(entry_fill, 90.0)

    assert risk == pytest.approx(10.57002)
    assert risk > entry_fill - 90.0


def test_zero_cost_model_preserves_reference_prices() -> None:
    model = ExecutionCostModel()

    assert model.buy_fill(123.45) == pytest.approx(123.45)
    assert model.sell_fill(123.45) == pytest.approx(123.45)
    assert model.commission(10_000.0) == 0.0
    assert model.long_risk_per_unit(100.0, 90.0) == pytest.approx(10.0)


def test_execution_cost_config_loads_asset_class_models(tmp_path: Path) -> None:
    path = tmp_path / "costs.yaml"
    path.write_text(
        """
models:
  equity:
    commission_bps: 1
    spread_bps: 4
    slippage_bps: 2
  crypto:
    commission_bps: 10
    spread_bps: 12
    slippage_bps: 8
""".strip(),
        encoding="utf-8",
    )

    models = load_execution_cost_models(path)

    assert models["equity"].commission_bps == 1.0
    assert models["crypto"].spread_bps == 12.0
    assert models["default"] == ExecutionCostModel()


def test_execution_cost_model_rejects_negative_assumptions() -> None:
    with pytest.raises(ValueError, match="cannot be negative"):
        ExecutionCostModel(slippage_bps=-1.0)
