import pytest

from swing_trader.risk import initial_stop, position_plan, trailing_stop


def test_position_plan_respects_risk_budget():
    plan = position_plan(equity=5000, entry=150, stop=138, risk_fraction=0.005)
    assert plan.risk_budget == pytest.approx(25.0)
    assert plan.units == pytest.approx(25 / 12)


def test_position_plan_respects_notional_cap():
    plan = position_plan(
        equity=5000,
        entry=100,
        stop=99.5,
        risk_fraction=0.005,
        max_position_fraction=0.25,
    )
    assert plan.notional == pytest.approx(1250.0)


def test_trailing_stop_never_moves_down():
    assert trailing_stop(100, highest_close=120, atr=5, multiple=2.5) == 107.5
    assert trailing_stop(110, highest_close=120, atr=5, multiple=2.5) == 110


def test_initial_stop():
    assert initial_stop(150, 6, 2.0) == 138
