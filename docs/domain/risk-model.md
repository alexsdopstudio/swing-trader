# Risk Model

Risk management is deterministic and has priority over every strategy or AI component.

## Position sizing

The configured risk budget is based on expected account loss if the long position exits at the technical initial stop under the active execution-cost model.

```text
risk_budget = equity × risk_fraction

entry_cash_per_unit = adverse_buy_fill + entry_commission_per_unit
stop_net_per_unit = adverse_sell_fill_at_stop - exit_commission_per_unit
risk_per_unit = entry_cash_per_unit - stop_net_per_unit

units_by_risk = risk_budget / risk_per_unit
units_by_notional = equity × max_position_fraction / executed_entry
units_by_cash = available_cash / entry_cash_per_unit
units_by_open_risk = remaining_portfolio_risk / risk_per_unit

units = min(
    units_by_risk,
    units_by_notional,
    units_by_cash,
    units_by_open_risk,
)
```

With a zero-cost execution model, this reduces to the frictionless `entry - stop` sizing rule.

Current research defaults:

- risk per trade: 0.5% of equity
- max position notional: 25% of equity
- max aggregate open risk: 2% of equity
- max concurrent positions: 4

For €5,000 equity, 0.5% corresponds to a target initial risk budget of approximately €25 per trade. Under non-zero execution costs, position size is reduced so expected non-gap loss to the initial stop remains near that budget.

## Execution costs

Execution costs are deterministic research assumptions selected by asset class. The current model supports:

- commission in basis points of executed notional;
- full spread in basis points, with half applied adversely on each side;
- additional adverse slippage in basis points per side.

The technical stop is a market-reference trigger. When an exit occurs, the execution-cost model converts that reference into the realized sell fill and commission.

Entry and expected stop-exit friction participate in sizing and aggregate open-risk accounting. Costs are not merely subtracted from final performance.

## Open portfolio risk

Open risk is recalculated from each position's executed entry economics and its current technical stop under the same cost model. As a trailing stop rises, open risk can decline toward zero.

The aggregate open-risk cap is enforced before each new entry. When remaining risk capacity is below the normal per-trade target, a new position may be reduced to fit the remaining capacity rather than exceeding the cap.

## Principles

- Stops define invalidation and sizing; conviction does not.
- AI must never override sizing, stops, execution assumptions, or portfolio-risk limits.
- Multiple positions share one account, one cash balance, and one aggregate open-risk budget.
- Gaps can make realized losses exceed the planned risk budget because the market may open beyond the stop reference.
- Equity and crypto use configurable execution-cost assumptions rather than one universal friction model.
- Baseline commission/spread/slippage settings are research inputs, not broker or exchange quotes.
- Any strategy conclusion must be tested for execution-cost sensitivity.
