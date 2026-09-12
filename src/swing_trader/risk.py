from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PositionPlan:
    entry: float
    stop: float
    units: float
    notional: float
    risk_budget: float
    risk_per_unit: float


def initial_stop(entry: float, atr: float, atr_multiple: float = 2.0) -> float:
    if entry <= 0 or atr <= 0:
        raise ValueError("entry and atr must be positive")
    return entry - atr_multiple * atr


def position_plan_for_risk(
    equity: float,
    entry: float,
    stop: float,
    risk_per_unit: float,
    risk_fraction: float = 0.005,
    max_position_fraction: float = 0.25,
) -> PositionPlan:
    if equity <= 0 or entry <= 0:
        raise ValueError("equity and entry must be positive")
    if not 0 < risk_fraction < 1:
        raise ValueError("risk_fraction must be between 0 and 1")
    if not 0 < max_position_fraction <= 1:
        raise ValueError("max_position_fraction must be between 0 and 1")
    if risk_per_unit <= 0:
        raise ValueError("risk_per_unit must be positive")

    target_risk_budget = equity * risk_fraction
    units_by_risk = target_risk_budget / risk_per_unit
    units_by_notional_cap = (equity * max_position_fraction) / entry
    units = min(units_by_risk, units_by_notional_cap)

    return PositionPlan(
        entry=entry,
        stop=stop,
        units=units,
        notional=units * entry,
        risk_budget=units * risk_per_unit,
        risk_per_unit=risk_per_unit,
    )


def position_plan(
    equity: float,
    entry: float,
    stop: float,
    risk_fraction: float = 0.005,
    max_position_fraction: float = 0.25,
) -> PositionPlan:
    risk_per_unit = entry - stop
    if risk_per_unit <= 0:
        raise ValueError("stop must be below entry for a long position")
    return position_plan_for_risk(
        equity=equity,
        entry=entry,
        stop=stop,
        risk_per_unit=risk_per_unit,
        risk_fraction=risk_fraction,
        max_position_fraction=max_position_fraction,
    )


def trailing_stop(
    previous_stop: float, highest_close: float, atr: float, multiple: float = 2.5
) -> float:
    candidate = highest_close - multiple * atr
    return max(previous_stop, candidate)
