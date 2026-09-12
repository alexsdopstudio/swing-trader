# Current State

Last updated: 2026-09-12

## Working

- daily data loader, technical indicators, historical Swing Score and scanner
- deterministic risk sizing plus ATR initial/trailing stops
- single-asset and shared-account multi-asset backtesters
- cost-aware cash, risk, fills, commissions, spread/slippage, trade ledger, equity/exposure curves, and metrics
- reproducible experiment runner with warm-up/evaluation separation and source/runtime provenance
- execution-cost sensitivity, temporal-stability, passive/reference, and parameter-neighborhood experiment runners
- preregistered prospective-v1 holdout protocol
- real-data GitHub Actions experiment workflows and durable reviewed experiment memory
- repo-native AI memory/context, automated agent handoffs, gated design/PR/review lifecycle, Simplify, and Compound

## Validation status

- CI unit tests and Ruff are passing
- EXP-0001 exploratory baseline: 65 trades, +1.05R expectancy, 3.18 profit factor, 6.01% CAGR, -4.25% max drawdown
- EXP-0002: frozen v1 remained positive under 2x and 4x execution-cost scenarios; this is in-sample sensitivity only
- EXP-0003: only 3 of 6 calendar folds met positive-expectancy / PF>1 / positive-return conditions; preregistered temporal-stability thresholds failed
- EXP-0004: passive ownership of the selected universe produced far higher absolute return but near-full exposure and extreme drawdown; v1 remained much more defensive
- EXP-0005: all 27 preregistered parameter scenarios and all 6 immediate axial neighbors were joint-positive; median expectancy was +0.92R and the frozen center reproduced EXP-0001 within tolerance
- EXP-0005 supports local retrospective parameter robustness, but metric magnitude remains parameter-sensitive and no historical winner was selected
- `PROSPECTIVE-v1-holdout` starts 2026-09-14; interim results must not tune v1
- no validated portfolio-level trading edge yet
- no live or paper execution yet

## Known limitations

- execution costs use linear basis-point assumptions rather than nonlinear market impact/order books
- baseline cost assumptions are research inputs, not broker/exchange quotes
- EXP-0001 through EXP-0005 use the same narrow, high-profile survivor universe
- profit contribution remains concentrated in a small number of large winners and favorable calendar regimes
- EXP-0003 shows the historical edge is not temporally uniform; 2025 and 2026-YTD are weak and 2022 is inactive
- passive references are nearly fully invested while v1 averages about 6% exposure; no volatility/leverage normalization is preregistered
- EXP-0005 shows local sign/quality robustness but not parameter irrelevance; expectancy spans roughly +0.43R to +1.73R across the tested grid
- all completed experiments remain retrospective; the prospective holdout cannot support validation before both 2028-09-14 and 30 closed trades
- yfinance adjusted equity/QQQ history has changed across repeated runs; exact provider replay is not guaranteed without immutable snapshots
- no broader-universe survivorship/selection-bias study yet
- no provenance-preserving forward observation store yet
- no persistent daily scan history or catalyst/news agent

## Current milestone

Keep frozen v1 unchanged for the prospective holdout. Build the provenance-preserving forward holdout recorder for observations beginning 2026-09-14, and run a preregistered broader-universe retrospective diagnostic to reduce selection/survivorship bias. Do not further mine the completed EXP-0005 grid for replacement parameters.
