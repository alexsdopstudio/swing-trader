from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


_BPS = 10_000.0


@dataclass(frozen=True)
class ExecutionCostModel:
    """Linear execution-cost assumptions for one asset class."""

    commission_bps: float = 0.0
    spread_bps: float = 0.0
    slippage_bps: float = 0.0

    def __post_init__(self) -> None:
        for name, value in (
            ("commission_bps", self.commission_bps),
            ("spread_bps", self.spread_bps),
            ("slippage_bps", self.slippage_bps),
        ):
            if value < 0:
                raise ValueError(f"{name} cannot be negative")
        if self.adverse_price_rate >= 1:
            raise ValueError("combined spread/slippage must keep sell fills positive")
        if self.commission_rate >= 1:
            raise ValueError("commission_bps must be below 10000")

    @property
    def commission_rate(self) -> float:
        return self.commission_bps / _BPS

    @property
    def adverse_price_rate(self) -> float:
        return (self.spread_bps / 2.0 + self.slippage_bps) / _BPS

    def buy_fill(self, reference_price: float) -> float:
        self._validate_price(reference_price)
        return reference_price * (1.0 + self.adverse_price_rate)

    def sell_fill(self, reference_price: float) -> float:
        self._validate_price(reference_price)
        return reference_price * (1.0 - self.adverse_price_rate)

    def commission(self, executed_notional: float) -> float:
        if executed_notional < 0:
            raise ValueError("executed_notional cannot be negative")
        return executed_notional * self.commission_rate

    def buy_cash_per_unit(self, reference_price: float) -> float:
        fill = self.buy_fill(reference_price)
        return fill * (1.0 + self.commission_rate)

    def sell_net_per_unit(self, reference_price: float) -> float:
        fill = self.sell_fill(reference_price)
        return fill * (1.0 - self.commission_rate)

    def long_risk_per_unit(self, entry_fill: float, exit_reference: float) -> float:
        """Return net loss per unit if a long exits at the supplied market reference."""
        self._validate_price(entry_fill)
        self._validate_price(exit_reference)
        entry_cash = entry_fill * (1.0 + self.commission_rate)
        exit_net = self.sell_net_per_unit(exit_reference)
        return max(0.0, entry_cash - exit_net)

    @staticmethod
    def _validate_price(price: float) -> None:
        if price <= 0:
            raise ValueError("price must be positive")


def load_execution_cost_models(path: str | Path) -> dict[str, ExecutionCostModel]:
    """Load named asset-class execution-cost assumptions from YAML."""
    with Path(path).open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}

    raw_models = payload.get("models")
    if not isinstance(raw_models, dict) or not raw_models:
        raise ValueError("execution cost config must define a non-empty 'models' mapping")

    models: dict[str, ExecutionCostModel] = {}
    for name, values in raw_models.items():
        if not isinstance(name, str) or not name:
            raise ValueError("execution cost model names must be non-empty strings")
        if not isinstance(values, dict):
            raise ValueError(f"execution cost model '{name}' must be a mapping")
        models[name] = ExecutionCostModel(
            commission_bps=float(values.get("commission_bps", 0.0)),
            spread_bps=float(values.get("spread_bps", 0.0)),
            slippage_bps=float(values.get("slippage_bps", 0.0)),
        )

    models.setdefault("default", ExecutionCostModel())
    return models
