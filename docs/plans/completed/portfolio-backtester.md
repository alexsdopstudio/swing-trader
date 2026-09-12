# Portfolio Backtester

Status: Completed

## Completion summary

The repository now has a deterministic shared-account portfolio backtester for long-only daily research.

Implemented capabilities:

- multiple assets share one cash balance and one account equity curve;
- signals generated at a completed close execute only at that asset's next available open;
- max positions, per-trade risk, aggregate open risk, available cash, and max position notional are enforced;
- simultaneous entries are prioritized by score and then symbol;
- initial stops are active on the entry bar;
- gaps through existing stops fill at the open;
- close-derived trailing stops become effective only on later bars;
- mixed calendars use each asset's own next available bar;
- open positions are liquidated at their final available close;
- trade ledger, equity curve, exposure curve, and position-count curve are produced;
- portfolio metrics include CAGR, maximum drawdown, Sharpe, Sortino, profit factor, win rate, expectancy in R, exposure, holding period, and concentration of winning PnL;
- `swing-backtest` runs historical research for configured assets;
- synthetic tests cover execution timing and portfolio risk constraints.

## Scope preserved

This feature intentionally does not include transaction costs, slippage, walk-forward validation, portfolio optimization, shorting, leverage, or AI-based trade decisions.

Portfolio metrics are therefore pre-cost research outputs and are not yet evidence of a tradable edge.

## Simplify outcome

The implementation uses one explicit chronological event loop, small dataclasses, and existing deterministic risk helpers. It deliberately avoids an event bus, broker/order hierarchy, portfolio optimizer, or provider coupling. No further simplification was justified without making execution ordering less visible.

## Compound outcome

The implementation confirmed a reusable research lesson: bar-based backtests must order events by information time, not merely by date. The lesson is captured in `docs/solutions/trading-research/order-events-by-information-time.md` and indexed in solution memory.

## Validation

- synthetic next-open execution test;
- same-bar initial-stop test;
- gap-through-stop test;
- deterministic score-priority test;
- aggregate open-risk sizing test;
- historical score/regime tests;
- portfolio metrics test;
- `pytest -q`;
- `ruff check src tests`;
- PR convention checks.

## Next research step

Add a realistic transaction-cost/slippage model, then run and record the first reproducible real-data portfolio experiment on BTC-USD, SOL-USD, META, and NVDA.
