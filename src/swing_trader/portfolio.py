from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from math import isfinite

import pandas as pd

from .execution import ExecutionCostModel
from .risk import initial_stop, position_plan_for_risk, trailing_stop


@dataclass(frozen=True)
class PortfolioAsset:
    symbol: str
    data: pd.DataFrame
    scores: pd.Series
    regime: pd.Series
    asset_class: str = "default"


@dataclass(frozen=True)
class PortfolioBacktestConfig:
    initial_equity: float = 5_000.0
    risk_fraction: float = 0.005
    max_open_risk_fraction: float = 0.02
    max_positions: int = 4
    max_position_fraction: float = 0.25
    min_score: int = 70
    stop_atr: float = 2.0
    trail_atr: float = 2.5
    cost_models: Mapping[str, ExecutionCostModel] = field(
        default_factory=lambda: {"default": ExecutionCostModel()}
    )

    def __post_init__(self) -> None:
        if self.initial_equity <= 0:
            raise ValueError("initial_equity must be positive")
        if not 0 < self.risk_fraction < 1:
            raise ValueError("risk_fraction must be between 0 and 1")
        if not 0 < self.max_open_risk_fraction < 1:
            raise ValueError("max_open_risk_fraction must be between 0 and 1")
        if self.max_positions <= 0:
            raise ValueError("max_positions must be positive")
        if not 0 < self.max_position_fraction <= 1:
            raise ValueError("max_position_fraction must be between 0 and 1")
        if self.stop_atr <= 0 or self.trail_atr <= 0:
            raise ValueError("ATR multiples must be positive")
        if not self.cost_models:
            raise ValueError("cost_models cannot be empty")
        if any(not isinstance(model, ExecutionCostModel) for model in self.cost_models.values()):
            raise ValueError("all cost_models values must be ExecutionCostModel instances")

    def cost_model_for(self, asset_class: str) -> ExecutionCostModel:
        model = self.cost_models.get(asset_class)
        if model is not None:
            return model
        return self.cost_models.get("default", ExecutionCostModel())


@dataclass(frozen=True)
class PortfolioTrade:
    symbol: str
    entry_date: pd.Timestamp
    exit_date: pd.Timestamp
    entry: float
    exit: float
    units: float
    initial_stop: float
    initial_risk: float
    pnl: float
    r_multiple: float
    signal_score: int
    exit_reason: str
    entry_reference: float | None = None
    exit_reference: float | None = None
    entry_fee: float = 0.0
    exit_fee: float = 0.0
    gross_pnl: float | None = None
    total_cost: float = 0.0


@dataclass(frozen=True)
class PortfolioBacktestResult:
    trades: tuple[PortfolioTrade, ...]
    equity_curve: pd.Series
    exposure_curve: pd.Series
    position_count_curve: pd.Series


@dataclass
class _Position:
    symbol: str
    entry_date: pd.Timestamp
    entry_reference: float
    entry: float
    entry_fee: float
    units: float
    initial_stop: float
    stop: float
    highest_close: float
    risk_per_unit: float
    signal_score: int
    cost_model: ExecutionCostModel


@dataclass(frozen=True)
class _PendingEntry:
    symbol: str
    signal_date: pd.Timestamp
    execution_date: pd.Timestamp
    score: int
    atr: float


def _prepare_asset(asset: PortfolioAsset) -> PortfolioAsset:
    required = {"Open", "High", "Low", "Close", "atr14", "high20", "sma50", "sma200"}
    missing = required.difference(asset.data.columns)
    if missing:
        raise ValueError(f"{asset.symbol}: missing columns {sorted(missing)}")
    if not isinstance(asset.data.index, pd.DatetimeIndex):
        raise ValueError(f"{asset.symbol}: data index must be a DatetimeIndex")
    if not asset.data.index.is_unique:
        raise ValueError(f"{asset.symbol}: data index must be unique")

    data = asset.data.sort_index().copy()
    scores = asset.scores.reindex(data.index)
    regime = asset.regime.reindex(data.index).fillna(False).astype(bool)
    return PortfolioAsset(asset.symbol, data, scores, regime, asset.asset_class)


def _entry_signal(asset: PortfolioAsset, date: pd.Timestamp, min_score: int) -> bool:
    row = asset.data.loc[date]
    score = asset.scores.loc[date]
    if pd.isna(score):
        return False
    return bool(
        int(score) >= min_score
        and row["Close"] > row["high20"]
        and row["Close"] > row["sma50"]
        and row["sma50"] > row["sma200"]
        and asset.regime.loc[date]
    )


def _open_risk(positions: dict[str, _Position]) -> float:
    return sum(
        position.cost_model.long_risk_per_unit(position.entry, position.stop) * position.units
        for position in positions.values()
    )


def _equity_at_open(
    cash: float,
    positions: dict[str, _Position],
    current_bars: dict[str, pd.Series],
    last_prices: dict[str, float],
) -> float:
    equity = cash
    for symbol, position in positions.items():
        if symbol in current_bars:
            price = float(current_bars[symbol]["Open"])
        else:
            price = last_prices.get(symbol, position.entry)
        equity += position.units * price
    return equity


def _close_position(
    symbol: str,
    date: pd.Timestamp,
    exit_reference: float,
    reason: str,
    positions: dict[str, _Position],
    trades: list[PortfolioTrade],
    cash: float,
) -> float:
    position = positions.pop(symbol)
    exit_price = position.cost_model.sell_fill(exit_reference)
    exit_notional = position.units * exit_price
    exit_fee = position.cost_model.commission(exit_notional)
    gross_pnl = (exit_price - position.entry) * position.units
    pnl = gross_pnl - position.entry_fee - exit_fee
    initial_risk = position.risk_per_unit * position.units
    r_multiple = pnl / initial_risk if initial_risk > 0 else 0.0
    price_cost = (
        (position.entry - position.entry_reference) * position.units
        + (exit_reference - exit_price) * position.units
    )
    total_cost = price_cost + position.entry_fee + exit_fee
    trades.append(
        PortfolioTrade(
            symbol=symbol,
            entry_date=position.entry_date,
            exit_date=date,
            entry=position.entry,
            exit=exit_price,
            units=position.units,
            initial_stop=position.initial_stop,
            initial_risk=initial_risk,
            pnl=pnl,
            r_multiple=r_multiple,
            signal_score=position.signal_score,
            exit_reason=reason,
            entry_reference=position.entry_reference,
            exit_reference=exit_reference,
            entry_fee=position.entry_fee,
            exit_fee=exit_fee,
            gross_pnl=gross_pnl,
            total_cost=total_cost,
        )
    )
    return cash + exit_notional - exit_fee


def backtest_portfolio(
    assets: list[PortfolioAsset],
    config: PortfolioBacktestConfig | None = None,
) -> PortfolioBacktestResult:
    """Backtest multiple long-only assets sharing cash and deterministic risk limits."""
    config = config or PortfolioBacktestConfig()
    if not assets:
        raise ValueError("at least one asset is required")

    prepared: dict[str, PortfolioAsset] = {}
    for raw_asset in assets:
        if raw_asset.symbol in prepared:
            raise ValueError(f"duplicate asset symbol: {raw_asset.symbol}")
        prepared[raw_asset.symbol] = _prepare_asset(raw_asset)

    all_dates = sorted(set().union(*(asset.data.index for asset in prepared.values())))
    if not all_dates:
        raise ValueError("asset data cannot be empty")

    cash = float(config.initial_equity)
    positions: dict[str, _Position] = {}
    pending: dict[pd.Timestamp, list[_PendingEntry]] = {}
    trades: list[PortfolioTrade] = []
    last_prices: dict[str, float] = {}
    equity_points: dict[pd.Timestamp, float] = {}
    exposure_points: dict[pd.Timestamp, float] = {}
    position_count_points: dict[pd.Timestamp, int] = {}
    last_dates = {symbol: asset.data.index[-1] for symbol, asset in prepared.items()}

    for date in all_dates:
        current_bars = {
            symbol: asset.data.loc[date]
            for symbol, asset in prepared.items()
            if date in asset.data.index
        }

        # Existing stops that are already violated at the open fill from that open reference.
        for symbol in list(positions):
            bar = current_bars.get(symbol)
            if bar is None:
                continue
            position = positions[symbol]
            open_price = float(bar["Open"])
            if open_price <= position.stop:
                cash = _close_position(
                    symbol, date, open_price, "stop_gap", positions, trades, cash
                )

        # Signals from a previous close may execute only at this asset's next open.
        candidates = sorted(
            pending.pop(date, []),
            key=lambda item: (-item.score, item.symbol),
        )
        for candidate in candidates:
            if candidate.symbol in positions or len(positions) >= config.max_positions:
                continue
            bar = current_bars.get(candidate.symbol)
            if bar is None:
                continue

            entry_reference = float(bar["Open"])
            asset = prepared[candidate.symbol]
            cost_model = config.cost_model_for(asset.asset_class)
            if (
                not isfinite(entry_reference)
                or entry_reference <= 0
                or not isfinite(candidate.atr)
                or candidate.atr <= 0
            ):
                continue

            entry = cost_model.buy_fill(entry_reference)
            stop = initial_stop(entry, candidate.atr, config.stop_atr)
            if stop <= 0:
                continue
            risk_per_unit = cost_model.long_risk_per_unit(entry, stop)
            if risk_per_unit <= 0:
                continue

            equity = _equity_at_open(cash, positions, current_bars, last_prices)
            if equity <= 0:
                continue

            plan = position_plan_for_risk(
                equity=equity,
                entry=entry,
                stop=stop,
                risk_per_unit=risk_per_unit,
                risk_fraction=config.risk_fraction,
                max_position_fraction=config.max_position_fraction,
            )
            remaining_risk = max(
                0.0,
                equity * config.max_open_risk_fraction - _open_risk(positions),
            )
            units_by_cash = max(0.0, cash / cost_model.buy_cash_per_unit(entry_reference))
            units_by_remaining_risk = remaining_risk / risk_per_unit
            units = min(plan.units, units_by_cash, units_by_remaining_risk)
            if not isfinite(units) or units <= 0:
                continue

            entry_notional = units * entry
            entry_fee = cost_model.commission(entry_notional)
            cash -= entry_notional + entry_fee
            positions[candidate.symbol] = _Position(
                symbol=candidate.symbol,
                entry_date=date,
                entry_reference=entry_reference,
                entry=entry,
                entry_fee=entry_fee,
                units=units,
                initial_stop=stop,
                stop=stop,
                highest_close=float(bar["Close"]),
                risk_per_unit=risk_per_unit,
                signal_score=candidate.score,
                cost_model=cost_model,
            )

        # Initial and trailing stops are active intraday using the stop known at the open.
        for symbol in list(positions):
            bar = current_bars.get(symbol)
            if bar is None:
                continue
            position = positions[symbol]
            if float(bar["Low"]) <= position.stop:
                cash = _close_position(
                    symbol, date, position.stop, "stop", positions, trades, cash
                )

        # Closing information may only change the stop for the following bar.
        for symbol, position in positions.items():
            bar = current_bars.get(symbol)
            if bar is None:
                continue
            close = float(bar["Close"])
            atr = float(bar["atr14"])
            position.highest_close = max(position.highest_close, close)
            if isfinite(atr) and atr > 0:
                position.stop = trailing_stop(
                    position.stop,
                    position.highest_close,
                    atr,
                    config.trail_atr,
                )

        for symbol, bar in current_bars.items():
            last_prices[symbol] = float(bar["Close"])

        # Each asset is liquidated at its own final available close.
        for symbol in list(positions):
            if date != last_dates[symbol]:
                continue
            cash = _close_position(
                symbol,
                date,
                last_prices[symbol],
                "end_of_test",
                positions,
                trades,
                cash,
            )

        equity = cash + sum(
            position.units * last_prices.get(symbol, position.entry)
            for symbol, position in positions.items()
        )
        notional = sum(
            position.units * last_prices.get(symbol, position.entry)
            for symbol, position in positions.items()
        )
        equity_points[date] = equity
        exposure_points[date] = notional / equity if equity > 0 else 0.0
        position_count_points[date] = len(positions)

        # Signals are generated last, from the completed close, for the next asset bar only.
        for symbol, asset in prepared.items():
            if symbol in positions or date not in asset.data.index:
                continue
            if not _entry_signal(asset, date, config.min_score):
                continue
            atr = float(asset.data.loc[date, "atr14"])
            if not isfinite(atr) or atr <= 0:
                continue
            location = asset.data.index.get_loc(date)
            if not isinstance(location, int) or location + 1 >= len(asset.data.index):
                continue
            execution_date = asset.data.index[location + 1]
            pending.setdefault(execution_date, []).append(
                _PendingEntry(
                    symbol=symbol,
                    signal_date=date,
                    execution_date=execution_date,
                    score=int(asset.scores.loc[date]),
                    atr=atr,
                )
            )

    index = pd.DatetimeIndex(equity_points.keys())
    return PortfolioBacktestResult(
        trades=tuple(trades),
        equity_curve=pd.Series(equity_points.values(), index=index, name="equity"),
        exposure_curve=pd.Series(exposure_points.values(), index=index, name="exposure"),
        position_count_curve=pd.Series(
            position_count_points.values(), index=index, name="position_count", dtype="int64"
        ),
    )
