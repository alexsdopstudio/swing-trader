# Current State

Last updated: 2026-09-12

## Working

- daily data loader
- technical indicators
- Swing Score and historical score series
- scanner
- deterministic position sizing
- ATR initial/trailing stops
- single-asset backtester
- shared-account portfolio backtester
- portfolio trade ledger, equity/exposure curves, and metrics
- asset-class execution cost models for commission, spread, and slippage
- cost-aware position sizing, shared cash, aggregate risk, and realized PnL
- `swing-backtest` historical research CLI with reproducible cost configuration
- CI with pytest and Ruff
- repo-native AI memory and context builder
- gated branch/design/PR/review/merge development lifecycle
- Simplify and Compound stages for AI-assisted development
- reusable solution-memory taxonomy for engineering and trading research

## Validation status

- unit test suite is passing in CI
- portfolio execution/risk semantics are covered by synthetic tests
- cost-aware sizing and execution arithmetic are covered by synthetic tests
- no validated portfolio-level trading edge yet
- no live or paper execution yet

## Known limitations

- execution costs use linear basis-point assumptions rather than order-book or nonlinear market-impact models
- baseline cost assumptions are research inputs, not broker/exchange quotes
- no recorded real-data portfolio experiment yet
- no walk-forward validation
- no experiment database/index
- no semantic retrieval for solution memory
- no persistent daily scan history
- no catalyst/news agent

## Current milestone

Run and record the first reproducible cost-aware portfolio experiment on BTC-USD, SOL-USD, META, and NVDA, then evaluate execution-cost sensitivity before drawing strategy conclusions.
