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
- temporal-stability runner with independent calendar folds and one shared provider snapshot
- preregistered prospective-v1 holdout protocol
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
- EXP-0003 retrospective temporal diagnostic completed across six independent calendar folds
- EXP-0003 positive expectancy / profit-factor>1 / positive-return folds: 3 of 6; both preregistered 4-of-6 stability thresholds failed
- EXP-0003 confirmed 2025 and 2026-YTD as weak; 2022 produced no trades and no exposure
- `PROSPECTIVE-v1-holdout` is preregistered to start 2026-09-14 with no interim v1 tuning
- no validated portfolio-level trading edge yet
- no live or paper execution yet

## Known limitations

- execution costs use linear basis-point assumptions rather than order-book or nonlinear market-impact models
- baseline cost assumptions and sensitivity multipliers are research inputs, not broker/exchange quotes
- EXP-0001/EXP-0002/EXP-0003 use the same narrow, survivor/high-profile universe
- profit contribution is concentrated in a small number of large winners and favorable calendar regimes
- the aggregate historical edge is not temporally uniform: 2025 and 2026-YTD are negative and 2022 is inactive
- EXP-0003 is retrospective decomposition of already observed history, not true out-of-sample validation
- the prospective holdout cannot support validation claims before both 2028-09-14 and 30 closed trades
- yfinance adjusted equity/QQQ history has changed across repeated runs; exact provider replay is not guaranteed without immutable snapshots
- no parameter-neighborhood robustness analysis yet
- no broader-universe survivorship/selection-bias study
- no passive/reference baseline comparison
- no semantic retrieval for solution memory
- no persistent daily scan history
- no catalyst/news agent

## Current milestone

Keep v1 frozen for the prospective holdout. Add passive/reference baselines next, then run parameter-neighborhood and broader-universe diagnostics without retroactively tuning v1.
