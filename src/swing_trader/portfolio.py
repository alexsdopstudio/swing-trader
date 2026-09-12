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


@dataclass(frozen=True)
class PortfolioReplayBar:
    symbol: str
    row: pd.Series
    score: float | int | None
    regime: bool
    asset_class: str = "default"


@dataclass(frozen=True)
class PortfolioPositionSnapshot:
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


@dataclass(frozen=True)
class PortfolioPendingSignal:
    symbol: str
    signal_date: pd.Timestamp
    score: int
    atr: float


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
    score: int
    atr: float


_REQUIRED_BAR_FIELDS = {"Open", "High", "Low", "Close", "atr14", "high20", "sma50", "sma200"}


def _prepare_asset(asset: PortfolioAsset) -> PortfolioAsset:
    missing = _REQUIRED_BAR_FIELDS.difference(asset.data.columns)
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


def _entry_signal_values(
    row: pd.Series,
    score: float | int | None,
    regime: bool,
    min_score: int,
) -> bool:
    if score is None or pd.isna(score):
        return False
    return bool(
        int(score) >= min_score
        and row["Close"] > row["high20"]
        and row["Close"] > row["sma50"]
        and row["sma50"] > row["sma200"]
        and regime
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


class PortfolioReplaySession:
    """Stateful daily portfolio event loop shared by backtests and forward replay."""

    def __init__(self, config: PortfolioBacktestConfig | None = None) -> None:
        self.config = config or PortfolioBacktestConfig()
        self.cash = float(self.config.initial_equity)
        self._positions: dict[str, _Position] = {}
        self._pending: dict[str, _PendingEntry] = {}
        self._trades: list[PortfolioTrade] = []
        self._last_prices: dict[str, float] = {}
        self._equity_points: dict[pd.Timestamp, float] = {}
        self._exposure_points: dict[pd.Timestamp, float] = {}
        self._position_count_points: dict[pd.Timestamp, int] = {}
        self._last_processed_date: pd.Timestamp | None = None

    @property
    def trades(self) -> tuple[PortfolioTrade, ...]:
        return tuple(self._trades)

    @property
    def open_positions(self) -> tuple[PortfolioPositionSnapshot, ...]:
        return tuple(
            PortfolioPositionSnapshot(
                symbol=position.symbol,
                entry_date=position.entry_date,
                entry_reference=position.entry_reference,
                entry=position.entry,
                entry_fee=position.entry_fee,
                units=position.units,
                initial_stop=position.initial_stop,
                stop=position.stop,
                highest_close=position.highest_close,
                risk_per_unit=position.risk_per_unit,
                signal_score=position.signal_score,
            )
            for _, position in sorted(self._positions.items())
        )

    @property
    def pending_signals(self) -> tuple[PortfolioPendingSignal, ...]:
        return tuple(
            PortfolioPendingSignal(
                symbol=pending.symbol,
                signal_date=pending.signal_date,
                score=pending.score,
                atr=pending.atr,
            )
            for _, pending in sorted(self._pending.items())
        )

    def result(self) -> PortfolioBacktestResult:
        index = pd.DatetimeIndex(self._equity_points.keys())
        return PortfolioBacktestResult(
            trades=tuple(self._trades),
            equity_curve=pd.Series(
                self._equity_points.values(), index=index, name="equity", dtype="float64"
            ),
            exposure_curve=pd.Series(
                self._exposure_points.values(), index=index, name="exposure", dtype="float64"
            ),
            position_count_curve=pd.Series(
                self._position_count_points.values(),
                index=index,
                name="position_count",
                dtype="int64",
            ),
        )

    def process_date(
        self,
        date: pd.Timestamp,
        bars: Mapping[str, PortfolioReplayBar],
        *,
        terminal_symbols: set[str] | frozenset[str] | None = None,
    ) -> None:
        date = pd.Timestamp(date)
        if self._last_processed_date is not None and date <= self._last_processed_date:
            raise ValueError("portfolio replay dates must be strictly increasing")
        terminal_symbols = set(terminal_symbols or ())
        replay_bars = dict(bars)
        if any(bar.symbol != symbol for symbol, bar in replay_bars.items()):
            raise ValueError("portfolio replay bar keys must match bar symbols")
        for symbol, bar in replay_bars.items():
            missing = _REQUIRED_BAR_FIELDS.difference(bar.row.index)
            if missing:
                raise ValueError(f"{symbol}: missing replay bar fields {sorted(missing)}")

        current_bars = {symbol: bar.row for symbol, bar in replay_bars.items()}

        for symbol in list(self._positions):
            row = current_bars.get(symbol)
            if row is None:
                continue
            position = self._positions[symbol]
            open_price = float(row["Open"])
            if open_price <= position.stop:
                self.cash = _close_position(
                    symbol, date, open_price, "stop_gap", self._positions, self._trades, self.cash
                )

        candidates: list[_PendingEntry] = []
        for symbol, pending in list(self._pending.items()):
            if symbol in current_bars and pending.signal_date < date:
                candidates.append(self._pending.pop(symbol))
        candidates.sort(key=lambda item: (-item.score, item.symbol))

        for candidate in candidates:
            if candidate.symbol in self._positions or len(self._positions) >= self.config.max_positions:
                continue
            row = current_bars[candidate.symbol]
            replay_bar = replay_bars[candidate.symbol]
            entry_reference = float(row["Open"])
            cost_model = self.config.cost_model_for(replay_bar.asset_class)
            if (
                not isfinite(entry_reference)
                or entry_reference <= 0
                or not isfinite(candidate.atr)
                or candidate.atr <= 0
            ):
                continue

            entry = cost_model.buy_fill(entry_reference)
            stop = initial_stop(entry, candidate.atr, self.config.stop_atr)
            if stop <= 0:
                continue
            risk_per_unit = cost_model.long_risk_per_unit(entry, stop)
            if risk_per_unit <= 0:
                continue

            equity = _equity_at_open(self.cash, self._positions, current_bars, self._last_prices)
            if equity <= 0:
                continue

            plan = position_plan_for_risk(
                equity=equity,
                entry=entry,
                stop=stop,
                risk_per_unit=risk_per_unit,
                risk_fraction=self.config.risk_fraction,
                max_position_fraction=self.config.max_position_fraction,
            )
            remaining_risk = max(
                0.0,
                equity * self.config.max_open_risk_fraction - _open_risk(self._positions),
            )
            units_by_cash = max(0.0, self.cash / cost_model.buy_cash_per_unit(entry_reference))
            units_by_remaining_risk = remaining_risk / risk_per_unit
            units = min(plan.units, units_by_cash, units_by_remaining_risk)
            if not isfinite(units) or units <= 0:
                continue

            entry_notional = units * entry
            entry_fee = cost_model.commission(entry_notional)
            self.cash -= entry_notional + entry_fee
            self._positions[candidate.symbol] = _Position(
                symbol=candidate.symbol,
                entry_date=date,
                entry_reference=entry_reference,
                entry=entry,
                entry_fee=entry_fee,
                units=units,
                initial_stop=stop,
                stop=stop,
                highest_close=float(row["Close"]),
                risk_per_unit=risk_per_unit,
                signal_score=candidate.score,
                cost_model=cost_model,
            )

        for symbol in list(self._positions):
            row = current_bars.get(symbol)
            if row is None:
                continue
            position = self._positions[symbol]
            if float(row["Low"]) <= position.stop:
                self.cash = _close_position(
                    symbol, date, position.stop, "stop", self._positions, self._trades, self.cash
                )

        for symbol, position in self._positions.items():
            row = current_bars.get(symbol)
            if row is None:
                continue
            close = float(row["Close"])
            atr = float(row["atr14"])
            position.highest_close = max(position.highest_close, close)
            if isfinite(atr) and atr > 0:
                position.stop = trailing_stop(
                    position.stop, position.highest_close, atr, self.config.trail_atr
                )

        for symbol, row in current_bars.items():
            self._last_prices[symbol] = float(row["Close"])

        for symbol in list(self._positions):
            if symbol not in terminal_symbols:
                continue
            self.cash = _close_position(
                symbol,
                date,
                self._last_prices[symbol],
                "end_of_test",
                self._positions,
                self._trades,
                self.cash,
            )

        equity = self.cash + sum(
            position.units * self._last_prices.get(symbol, position.entry)
            for symbol, position in self._positions.items()
        )
        notional = sum(
            position.units * self._last_prices.get(symbol, position.entry)
            for symbol, position in self._positions.items()
        )
        self._equity_points[date] = equity
        self._exposure_points[date] = notional / equity if equity > 0 else 0.0
        self._position_count_points[date] = len(self._positions)

        for symbol, replay_bar in sorted(replay_bars.items()):
            if symbol in self._positions or symbol in terminal_symbols:
                continue
            if not _entry_signal_values(
                replay_bar.row, replay_bar.score, replay_bar.regime, self.config.min_score
            ):
                continue
            atr = float(replay_bar.row["atr14"])
            if not isfinite(atr) or atr <= 0:
                continue
            self._pending[symbol] = _PendingEntry(
                symbol=symbol,
                signal_date=date,
                score=int(replay_bar.score),
                atr=atr,
            )

        self._last_processed_date = date


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

    last_dates = {symbol: asset.data.index[-1] for symbol, asset in prepared.items()}
    session = PortfolioReplaySession(config)

    for date in all_dates:
        bars = {
            symbol: PortfolioReplayBar(
                symbol=symbol,
                row=asset.data.loc[date],
                score=asset.scores.loc[date],
                regime=bool(asset.regime.loc[date]),
                asset_class=asset.asset_class,
            )
            for symbol, asset in prepared.items()
            if date in asset.data.index
        }
        terminal_symbols = {
            symbol for symbol, terminal_date in last_dates.items() if date == terminal_date
        }
        session.process_date(date, bars, terminal_symbols=terminal_symbols)

    return session.result()
