# Test Universe Breadth with Fixed Membership and Contribution

## Problem

A profitable backtest on a narrow handpicked universe can be driven by a few exceptional assets. Simply adding more present-day winners after seeing the result creates another selection channel and can make the apparent robustness less credible rather than more credible.

Aggregate portfolio return is also insufficient. A larger universe can still produce the same total return because one original symbol dominates while the added symbols contribute little or negatively.

## Reusable approach

1. Fix the broader universe independently of the experiment outcome. Prefer a list that was already versioned or preregistered before the breadth run.
2. Preserve a control path using the prior research subset.
3. Run control and expanded portfolios on one shared provider snapshot so data revisions cannot masquerade as a universe effect.
4. Rerun the full shared-account portfolio. Do not substitute independent per-symbol backtests when symbols compete for cash, risk budget, or position slots.
5. Keep strategy, risk, execution, dates, and benchmarks frozen; universe membership is the only intended research dimension.
6. Attribute realized net PnL and trade counts by symbol and asset class.
7. Predeclare breadth criteria such as positive added-symbol aggregate contribution, contributor counts across old/new symbols and asset classes, and a maximum single-contributor concentration.
8. Treat the historical control as a reproduction check under fixed provider-revision tolerances.
9. Never use the result to remove losing symbols or promote a better-performing subset inside the same frozen strategy.

## Why concentration matters

A positive expanded portfolio can still be fragile if almost all positive PnL comes from one asset. Measuring the largest positive symbol's share of summed positive symbol PnL answers a different question from portfolio-level `top5_profit_share`: it tests whether the universe-level conclusion itself is diversified across names.

## Applicability boundary

This method reduces dependence on a small research subset, but a broader list of current survivors does **not** eliminate survivorship bias. Stronger survivorship evidence requires point-in-time membership or another membership rule knowable at each historical date.

Likewise, breadth evidence is retrospective. It does not repair temporal instability or replace preregistered prospective validation.

## Checks

- exact control and expanded lists are locked before the real-data run;
- overlapping symbols have identical source digests across paths;
- total provider downloads equal the unique union of assets and benchmarks;
- portfolio/risk/cost/evaluation settings are byte/structure-equivalent outside permitted experiment metadata and symbols;
- zero-trade and negative-contribution symbols remain in attribution output;
- contribution arithmetic sums back to realized portfolio PnL;
- no selected/preferred subset is emitted.

## Evidence in this repository

EXP-0006 applied this pattern to the complete 11-asset universe that was already present in `config/universe.yaml`, using the original four-symbol EXP-0001 set as a same-snapshot control. The result broadened positive contribution across symbols and asset classes without changing frozen v1, while still retaining the explicit limitation that the configured universe is not a point-in-time constituent dataset.
