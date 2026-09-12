# Current State

Last updated: 2026-09-12

## Working

- daily data loader
- technical indicators
- Swing Score
- scanner
- deterministic position sizing
- ATR initial/trailing stops
- single-asset backtester
- CI with pytest and Ruff

## Validation status

- unit test suite is passing in CI
- no validated portfolio-level edge yet
- no live or paper execution yet

## Known limitations

- no portfolio-aware backtest
- no costs/slippage model
- no walk-forward validation
- no experiment database/index
- no persistent daily scan history
- no catalyst/news agent

## Current milestone

Implement and validate the portfolio-aware historical backtester described in `docs/plans/active/portfolio-backtester.md`.
