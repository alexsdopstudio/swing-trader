from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Mapping

import pandas as pd

from .execution import ExecutionCostModel


@dataclass(frozen=True)
class BuyAndHoldResult:
    initial_equity: float
    equity_curve: pd.Series
    position_value_curve: pd.Series
    entry_date: pd.Timestamp
    exit_date: pd.Timestamp
    entry_reference: float
    entry_fill: float
    units: float
    entry_fee: float
    exit_reference: float
    exit_fill: float
    exit_fee: float
    total_execution_cost: float

    @property
    def exposure_curve(self) -> pd.Series:
        exposure = self.position_value_curve / self.equity_curve
        return exposure.where(self.equity_curve > 0, 0.0).fillna(0.0).rename("exposure")


@dataclass(frozen=True)
class PassiveBasketResult:
    initial_equity: float
    equity_curve: pd.Series
    position_value_curve: pd.Series

    @property
    def exposure_curve(self) -> pd.Series:
        exposure = self.position_value_curve / self.equity_curve
        return exposure.where(self.equity_curve > 0, 0.0).fillna(0.0).rename("exposure")


def _prepare_prices(data: pd.DataFrame) -> pd.DataFrame:
    missing = {"Open", "Close"}.difference(data.columns)
    if missing:
        raise ValueError(f"price data is missing columns {sorted(missing)}")
    if not isinstance(data.index, pd.DatetimeIndex):
        raise ValueError("price data index must be a DatetimeIndex")
    if not data.index.is_unique:
        raise ValueError("price data index must be unique")
    prepared = data.sort_index().copy()
    if prepared.empty:
        raise ValueError("price data cannot be empty")
    return prepared


def buy_and_hold(
    data: pd.DataFrame,
    initial_equity: float,
    cost_model: ExecutionCostModel | None = None,
) -> BuyAndHoldResult:
    """Buy once at the first open and liquidate at the final close with explicit costs."""
    if initial_equity <= 0:
        raise ValueError("initial_equity must be positive")

    model = cost_model or ExecutionCostModel()
    prices = _prepare_prices(data)
    entry_date = prices.index[0]
    exit_date = prices.index[-1]
    entry_reference = float(prices.iloc[0]["Open"])
    exit_reference = float(prices.iloc[-1]["Close"])
    if not isfinite(entry_reference) or entry_reference <= 0:
        raise ValueError("first open must be a finite positive price")
    if not isfinite(exit_reference) or exit_reference <= 0:
        raise ValueError("final close must be a finite positive price")

    closes = prices["Close"].astype(float)
    if not closes.map(lambda value: isfinite(value) and value > 0).all():
        raise ValueError("all close prices must be finite and positive")

    entry_fill = model.buy_fill(entry_reference)
    units = initial_equity / model.buy_cash_per_unit(entry_reference)
    entry_notional = units * entry_fill
    entry_fee = model.commission(entry_notional)
    cash = initial_equity - entry_notional - entry_fee

    position_value = (closes * units).rename("position_value")
    equity = (cash + position_value).rename("equity")

    exit_fill = model.sell_fill(exit_reference)
    exit_notional = units * exit_fill
    exit_fee = model.commission(exit_notional)
    terminal_cash = cash + exit_notional - exit_fee
    equity.iloc[-1] = terminal_cash
    position_value.iloc[-1] = 0.0

    price_cost = (
        (entry_fill - entry_reference) * units
        + (exit_reference - exit_fill) * units
    )
    total_execution_cost = price_cost + entry_fee + exit_fee

    return BuyAndHoldResult(
        initial_equity=initial_equity,
        equity_curve=equity,
        position_value_curve=position_value,
        entry_date=entry_date,
        exit_date=exit_date,
        entry_reference=entry_reference,
        entry_fill=entry_fill,
        units=units,
        entry_fee=entry_fee,
        exit_reference=exit_reference,
        exit_fill=exit_fill,
        exit_fee=exit_fee,
        total_execution_cost=total_execution_cost,
    )


def equal_weight_basket(
    sleeves: Mapping[str, BuyAndHoldResult],
) -> PassiveBasketResult:
    """Combine equal-capital buy-and-hold sleeves on their union of market dates."""
    if not sleeves:
        raise ValueError("at least one passive sleeve is required")

    allocations = [result.initial_equity for result in sleeves.values()]
    first_allocation = allocations[0]
    tolerance = max(1e-9, abs(first_allocation) * 1e-12)
    if any(abs(value - first_allocation) > tolerance for value in allocations[1:]):
        raise ValueError("equal-weight basket requires equal initial sleeve allocations")

    union_index = pd.DatetimeIndex(
        sorted(set().union(*(result.equity_curve.index for result in sleeves.values())))
    )
    equity_parts: list[pd.Series] = []
    position_parts: list[pd.Series] = []
    for result in sleeves.values():
        equity_parts.append(
            result.equity_curve.reindex(union_index).ffill().fillna(result.initial_equity)
        )
        position_parts.append(
            result.position_value_curve.reindex(union_index).ffill().fillna(0.0)
        )

    equity = pd.concat(equity_parts, axis=1).sum(axis=1).rename("equity")
    position_value = pd.concat(position_parts, axis=1).sum(axis=1).rename("position_value")
    return PassiveBasketResult(
        initial_equity=sum(allocations),
        equity_curve=equity,
        position_value_curve=position_value,
    )
