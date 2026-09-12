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
- versioned experiment runner with warm-up/evaluation separation and strict JSON artifacts
- CI workflow capable of running real-data experiments and uploading artifacts
- experiment index and durable reviewed experiment memory
- CI with pytest and Ruff
- repo-native AI memory and context builder
- gated branch/design/PR/review/merge development lifecycle
- Simplify and Compound stages for AI-assisted development
- reusable solution-memory taxonomy for engineering and trading research

## Validation status

- unit test suite is passing in CI
- portfolio execution/risk semantics are covered by synthetic tests
- cost-aware sizing and execution arithmetic are covered by synthetic tests
- EXP-0001 real-data workflow completed successfully on BTC-USD, SOL-USD, META, and NVDA
- EXP-0001 exploratory baseline: 65 trades, +1.05R expectancy, 3.18 profit factor, 6.01% CAGR, -4.25% max drawdown
- EXP-0001 is not out-of-sample validation and does not justify deployment
- no validated portfolio-level trading edge yet
- no live or paper execution yet

## Known limitations

- execution costs use linear basis-point assumptions rather than order-book or nonlinear market-impact models
- baseline cost assumptions are research inputs, not broker/exchange quotes
- EXP-0001 has only 65 trades and a narrow, survivor/high-profile universe
- EXP-0001 profit contribution is concentrated in SOL-USD and NVDA and in a small number of large winners
- 2025 and the available 2026 EXP-0001 subperiods are negative
- no execution-cost sensitivity experiment yet
- no walk-forward / held-out validation
- no parameter robustness analysis
- no broader-universe survivorship/selection-bias study
- no passive/reference baseline comparison
- no semantic retrieval for solution memory
- no persistent daily scan history
- no catalyst/news agent

## Current milestone

Test whether the encouraging EXP-0001 baseline survives execution-cost sensitivity without changing v1 strategy parameters, then move to walk-forward / held-out validation.
