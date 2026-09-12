# Risk Model

Risk management is deterministic and has priority over every strategy or AI component.

## Position sizing

```text
risk_budget = equity × risk_fraction
risk_per_unit = entry - stop
units_by_risk = risk_budget / risk_per_unit
units_by_notional = equity × max_position_fraction / entry
units = min(units_by_risk, units_by_notional)
```

Current research defaults:

- risk per trade: 0.5% of equity
- max position notional: 25% of equity
- target future portfolio open-risk cap: 2% of equity
- target future max concurrent positions: 4

For €5,000 equity, 0.5% corresponds to a nominal risk budget of €25 per trade before execution gaps, slippage and other real-world effects.

## Principles

- Stops define invalidation and sizing; conviction does not.
- Correlated positions must eventually be accounted for at portfolio level.
- Gaps can make realized losses exceed the planned risk budget.
- Crypto and equities may require different execution/cost models.
