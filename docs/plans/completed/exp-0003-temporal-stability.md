# EXP-0003 — Temporal Stability and Prospective Holdout Registration

Status: Completed

## Goal

Measure whether the frozen v1 strategy behaves consistently across distinct historical calendar regimes and preregister the first genuinely prospective holdout window.

EXP-0003 is a retrospective temporal diagnostic, not out-of-sample validation, because EXP-0001 and EXP-0002 had already exposed aggregate results for the full 2021-01-01 through 2026-08-31 period.

## Frozen baseline

The experiment kept the EXP-0001 strategy and portfolio assumptions unchanged:

- BTC-USD, SOL-USD, META, NVDA;
- daily long-only next-asset-open execution;
- minimum Swing Score 70;
- risk per trade 0.5%;
- max aggregate open risk 2%;
- max four concurrent positions;
- max position notional 25%;
- initial stop 2 ATR;
- trailing stop 2.5 ATR;
- baseline execution-cost configuration.

No parameter was changed after observing the fold results.

## Historical fold design

Independent portfolio simulations reset equity to 5,000 at each fold boundary and reused one frozen provider snapshot:

- 2021;
- 2022;
- 2023;
- 2024;
- 2025;
- 2026-YTD through 2026-08-31.

Warm-up history began on 2020-01-01 for every fold.

## Implementation outcome

Added:

- `HistoricalSnapshot`, which downloads each required asset/benchmark once and serves immutable date slices to fold runs;
- `swing-temporal-stability` CLI;
- versioned EXP-0003 configuration;
- six-fold orchestration through the existing experiment/backtest engine;
- aggregate temporal-stability diagnostics;
- strict JSON, fold-comparison CSV, generated summary, and detailed per-fold CI artifacts;
- EXP-0003 GitHub Actions real-data workflow;
- tests for snapshot reuse/slicing, fold validation, aggregation, versioned config, and prospective protocol integrity;
- `PROSPECTIVE-v1-holdout` preregistration.

The implementation remained sequential orchestration over existing modules. No generic ML cross-validation framework, training API, optimizer, database, or distributed scheduler was introduced.

## Producer run

- code SHA: `40fdfe6b665c16d1d3d5e861ca5c4c752b8fe67b`
- GitHub Actions run: `34708885986`
- artifact id: `10302716912`
- artifact SHA-256: `99cf0e0d70eb4d23591e1206af055270eab6b483d6fc8fd1517b6e7298c0ee7f`
- provider downloads: 5
- runtime: Python 3.12.14, NumPy 2.5.3, pandas 3.0.5, PyYAML 6.0.3, yfinance 1.7.0

## Research result

| Fold | Trades | Return | Profit factor | Expectancy |
|---|---:|---:|---:|---:|
| 2021 | 21 | +13.04% | 4.33 | +1.19R |
| 2022 | 0 | 0.00% | n/a | n/a |
| 2023 | 11 | +14.19% | 7.77 | +2.50R |
| 2024 | 19 | +10.44% | 3.40 | +1.07R |
| 2025 | 11 | -1.34% | 0.58 | -0.24R |
| 2026-YTD | 3 | -1.05% | 0.00 | -0.70R |

Predeclared thresholds required positive expectancy and profit factor above 1 in at least four of six folds. Both thresholds failed at three of six.

The known weak 2025 and 2026-YTD periods were confirmed. 2022 produced no trades, no exposure, and no drawdown.

Decision: `PREDECLARED TEMPORAL-STABILITY THRESHOLDS NOT MET — CONTINUE RESEARCH — DO NOT DEPLOY`.

## Interpretation

The positive full-period expectancy is temporally concentrated rather than uniform. Strong years were 2021, 2023, and 2024; the strategy was inactive in 2022 and weak in 2025/2026-YTD.

The six folds contain 65 trades in total and their trade-count-weighted expectancy is effectively identical to EXP-0001, confirming that EXP-0003 decomposes already observed history rather than creating independent evidence.

## Prospective holdout

`experiments/PROSPECTIVE-v1-holdout/protocol.yaml` was preregistered on 2026-09-12 with:

- future start: 2026-09-14;
- minimum observation end: 2028-09-14;
- minimum closed trades: 30;
- validation gate: both time and trade-count requirements;
- no interim v1 parameter tuning.

Any strategy or risk change requires a new prospective protocol/version.

## Simplify outcome

The final runner is a six-fold sequential orchestrator with one shared data snapshot. No additional abstraction was justified.

## Compound outcome

Reusable research learning is captured in:

`docs/solutions/trading-research/preregister-true-holdout-windows.md`

The key rule is that previously observed history may be decomposed for temporal diagnostics, but it cannot be relabeled as unseen evidence. Genuine holdout claims require a future window preregistered before the data becomes observable.

## Next research step

Keep v1 frozen for the prospective holdout. Add passive/reference baselines next, then run parameter-neighborhood and broader-universe diagnostics without retroactively modifying v1.
