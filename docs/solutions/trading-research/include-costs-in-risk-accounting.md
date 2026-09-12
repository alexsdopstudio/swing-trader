# Include Execution Costs in Risk Accounting

## Problem

A backtest can model commissions and slippage only when calculating final trade PnL while still sizing positions from frictionless entry-to-stop distance. That makes performance look more realistic while silently violating the configured risk budget.

For small accounts and frequent trading, the difference can be material: the actual loss to the initial stop includes adverse entry execution, adverse stop execution, and commissions on both sides.

## Symptoms

- A trade configured to risk 0.5% loses more than 0.5% when it immediately stops out, even without a gap.
- Adding transaction costs lowers PnL but leaves position sizes unchanged.
- Aggregate open-risk checks ignore commissions and expected stop-exit friction.
- Costlier asset classes receive the same unit size as cheaper ones for the same price/ATR setup.
- Cash can become negative because sizing uses notional but entry fees are added afterward.

## Root cause

Execution costs are treated as reporting adjustments rather than part of the execution and risk model.

A risk budget describes expected account loss under an execution scenario. If the scenario includes real execution friction, that friction must participate in sizing and cash/risk constraints.

## Reusable solution

For a long position, calculate cost-aware initial risk per unit as:

`entry cash outflow per unit - estimated net stop-exit proceeds per unit`

The entry cash outflow includes the adverse buy fill and entry commission. Estimated stop-exit proceeds include adverse sell execution and exit commission.

Use that risk per unit for:

1. per-trade position sizing;
2. aggregate portfolio open-risk accounting;
3. realized R-multiple denominator.

Available-cash sizing must also include entry commission, not only executed notional.

Keep the technical stop trigger separate from the realized exit fill. The stop is a market-reference trigger; execution friction is applied after that trigger price is determined.

## When this applies

- risk-sized systematic strategies;
- shared-account portfolio backtests;
- assets with materially different fee/spread assumptions;
- small accounts where fixed risk budgets are tight;
- any research that reports expectancy in R.

## When this does not apply

A frictionless diagnostic backtest may intentionally set all execution costs to zero. The accounting structure should still support costs so that enabling them does not require changing strategy logic.

Nonlinear market impact, minimum fees, financing, taxes, and maker/taker logic require richer models than this repository's current linear basis-point assumptions.

## Tests and checks

Require tests that verify:

- zero-cost settings reproduce frictionless behavior;
- higher execution costs reduce units for the same account risk budget;
- an immediate non-gap stop-out remains approximately the configured initial risk in currency terms;
- entry fees reduce available cash immediately;
- aggregate open risk includes expected stop-exit friction;
- realized PnL is net of both entry and exit commissions;
- different asset classes can use different cost models.

During review, do not accept a cost model that only subtracts costs from final returns while leaving sizing and risk controls frictionless.

## References

- `src/swing_trader/execution.py`
- `src/swing_trader/portfolio.py`
- `src/swing_trader/risk.py`
- `tests/test_execution.py`
- `tests/test_portfolio.py`
- PR #4 — cost-aware backtesting
