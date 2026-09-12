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
- passive/reference comparison runner with cost-aware per-symbol and initial equal-weight buy-and-hold baselines
- parameter-neighborhood runner with a preregistered 27-scenario local grid, shared inputs, full-path reruns, and no winner selection
- preregistered prospective-v1 holdout protocol
- CI workflows capable of running real-data experiments and uploading artifacts
- experiment index and durable reviewed experiment memory
- CI with pytest and Ruff
- repo-native AI memory and context builder
- automated cross-session/cross-agent PR handoff generation and resume protocol
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
- EXP-0004 passive/reference comparison completed on the same four-asset retrospective sample
- EXP-0004 initial equal-weight buy-and-hold: +2,139.01% total return, 73.16% CAGR, -95.19% max drawdown, 1.06 Sharpe, 99.89% average exposure
- EXP-0004 frozen v1: +39.17% total return, 6.01% CAGR, -4.25% max drawdown, 1.27 Sharpe, 6.04% average exposure
- EXP-0004 shows much higher passive absolute return but radically different drawdown/exposure; it is retrospective and does not validate v1
- EXP-0005 parameter-neighborhood diagnostic completed across exactly 27 preregistered score/stop/trail scenarios on one shared provider snapshot
- EXP-0005 joint-positive scenarios: 27 of 27; joint-positive immediate axial neighbors: 6 of 6; median expectancy: +0.92R versus preregistered +0.50R threshold
- EXP-0005 exact frozen-v1 center reproduced EXP-0001 within every preregistered provider-revision tolerance
- EXP-0005 supports local retrospective parameter robustness but does not select a replacement parameter set; expectancy still spans roughly +0.43R to +1.73R across the grid
- `PROSPECTIVE-v1-holdout` is preregistered to start 2026-09-14 with no interim v1 tuning
- no validated portfolio-level trading edge yet
- no live or paper execution yet

## Known limitations

- execution costs use linear basis-point assumptions rather than order-book or nonlinear market-impact models
- baseline cost assumptions and sensitivity multipliers are research inputs, not broker/exchange quotes
- EXP-0001/EXP-0002/EXP-0003/EXP-0004/EXP-0005 use the same narrow, survivor/high-profile universe
- profit contribution is concentrated in a small number of large winners and favorable calendar regimes
- passive-reference returns are strongly influenced by exceptional SOL and NVDA paths and do not remove selection/survivorship bias
- passive references are nearly fully invested while v1 averages about 6% exposure; no volatility/leverage normalization has been preregistered or tested
- the aggregate historical edge is not temporally uniform: 2025 and 2026-YTD are negative and 2022 is inactive
- EXP-0005 supports local sign/quality robustness but parameter choice still materially affects historical magnitude
- EXP-0003, EXP-0004, and EXP-0005 are retrospective diagnostics, not true out-of-sample validation
- the prospective holdout cannot support validation claims before both 2028-09-14 and 30 closed trades
- yfinance adjusted equity/QQQ history has changed across repeated runs; exact provider replay is not guaranteed without immutable snapshots
- no broader-universe survivorship/selection-bias study
- no provenance-preserving forward holdout observation store
- no semantic retrieval for solution memory
- no persistent daily scan history
- no catalyst/news agent

## Current milestone

Keep v1 frozen for the prospective holdout. Build provenance-preserving forward holdout recording for observations beginning 2026-09-14, and run broader-universe testing next to reduce selection/survivorship bias. Do not further mine the completed EXP-0005 surface for replacement v1 parameters.
