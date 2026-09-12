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
- execution-cost sensitivity runner with shared market-data snapshots across scenarios
- CI workflows capable of running real-data experiments and uploading artifacts
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
- EXP-0002 execution-cost sensitivity completed with one shared provider snapshot across all scenarios
- EXP-0002 high 2.0x-cost scenario: 65 trades, +0.99R expectancy, 3.03 profit factor, 5.67% CAGR
- EXP-0002 stress 4.0x-cost scenario: 66 trades, +0.82R expectancy, 2.62 profit factor, 4.77% CAGR
- EXP-0002 supports execution-cost robustness inside the same historical sample but is not out-of-sample validation
- no validated portfolio-level trading edge yet
- no live or paper execution yet

## Known limitations

- execution costs use linear basis-point assumptions rather than order-book or nonlinear market-impact models
- baseline cost assumptions and sensitivity multipliers are research inputs, not broker/exchange quotes
- EXP-0001/EXP-0002 have only about 65 trades and a narrow, survivor/high-profile universe
- profit contribution in EXP-0001 is concentrated in SOL-USD, NVDA, and a small number of large winners
- 2025 and the available 2026 EXP-0001 baseline subperiods are negative
- EXP-0002 reuses the same exploratory historical window, so cost robustness does not establish temporal robustness
- yfinance revised adjusted history for META, NVDA, and QQQ between EXP-0001 and EXP-0002; baseline metrics remained effectively unchanged but exact provider replay is not guaranteed without snapshots
- no walk-forward / held-out validation
- no parameter robustness analysis
- no broader-universe survivorship/selection-bias study
- no passive/reference baseline comparison
- no semantic retrieval for solution memory
- no persistent daily scan history
- no catalyst/news agent

## Current milestone

Run a held-out / walk-forward evaluation with v1 strategy and risk parameters frozen. Do not tune parameters before that evidence is recorded.
