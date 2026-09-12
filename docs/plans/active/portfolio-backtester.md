# Active Plan — Portfolio Backtester

## Goal

Backtest multiple assets sharing one account and one risk budget.

## Initial scope

- Starting equity: €5,000 equivalent
- Assets: BTC, SOL, META, NVDA initially
- 0.5% target risk per trade
- max 4 concurrent positions
- max 2% aggregate open risk
- next-open execution
- ATR stops/trailing exits

## Deliverables

- portfolio backtest engine
- portfolio trade ledger
- equity curve
- metrics module
- CLI entry point
- unit and integration tests

## Definition of done

The run produces deterministic metrics and trade history, tests/lint pass, and the experiment configuration/results can be stored under `experiments/`.
