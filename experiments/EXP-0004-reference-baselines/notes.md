# EXP-0004 — Passive / Reference Baseline Review

Status: Reviewed retrospective reference comparison

## Research integrity

EXP-0004 does **not** claim out-of-sample validation. The full 2021-01-01 through 2026-08-31 evaluation history was already observed in EXP-0001 through EXP-0003.

The purpose is narrower: make opportunity cost visible by comparing the frozen v1 strategy with simple passive ownership of the exact EXP-0001 assets. The passive definitions were fixed before the real-data run and v1 was not modified in response to the result.

## Reference definitions

- per-symbol reference: buy once at the first available evaluation-window open and hold until the final available close;
- portfolio reference: allocate initial capital equally across BTC-USD, SOL-USD, META, and NVDA and never rebalance;
- execution: apply the same asset-class commission, spread, and slippage assumptions used by v1 at entry and terminal liquidation;
- calendars: each sleeve remains cash until its first tradable bar; no synthetic fills are created on missing equity sessions;
- data: v1 and all references reuse the same five-symbol provider snapshot, including QQQ for v1 regime logic.

## Run provenance

- experiment: `EXP-0004`
- producer code SHA: `7401577f0eaf80878091b7ac317e688c369b4a67`
- GitHub Actions run: `34711644430`
- artifact id: `10303308018`
- artifact SHA-256: `a145fa51e2f03e449218b857270264ef6f7c3f49f4a0230c5be9cc243ffb32af`
- runtime: Python 3.12.14, NumPy 2.5.3, pandas 3.0.5, PyYAML 6.0.3, yfinance 1.7.0
- provider downloads: 5 total; passive construction caused no additional provider downloads
- initial capital: 5,000

## Headline comparison

| Reference | Return | CAGR | Max DD | Sharpe | Sortino | Avg exposure |
|---|---:|---:|---:|---:|---:|---:|
| v1 strategy | +39.17% | +6.01% | -4.25% | 1.27 | 2.16 | 6.04% |
| Initial equal-weight buy-and-hold | +2,139.01% | +73.16% | -95.19% | 1.06 | 1.62 | 99.89% |
| BTC-USD buy-and-hold | +169.56% | +19.14% | -76.63% | 0.59 | 0.87 | ~99.95% |
| SOL-USD buy-and-hold | +6,687.98% | +110.63% | -96.27% | 1.22 | 1.95 | ~99.95% |
| META buy-and-hold | +109.76% | +14.00% | -76.74% | 0.52 | 0.76 | ~99.93% |
| NVDA buy-and-hold | +1,588.72% | +64.86% | -66.34% | 1.24 | 1.92 | ~99.93% |

## Interpretation

The passive references decisively beat v1 on absolute historical return. Even META, the weakest passive return in this selected universe, exceeds v1's +39.17% total return.

That is not a like-for-like risk result. v1 held market exposure only about 6% of the time on average, while the passive references were essentially continuously invested. The initial equal-weight basket also experienced an approximately 95% peak-to-trough drawdown. The large return gap therefore comes with radically different capital deployment and loss paths.

On the unlevered daily-return statistics recorded here, v1 had the highest Sharpe and Sortino ratios of every reference and by far the smallest maximum drawdown. This supports the narrower conclusion that the historical v1 path was materially more defensive than passive ownership. It does **not** show that v1 is economically superior after normalizing exposure, volatility, leverage, or investor utility; EXP-0004 intentionally does not introduce such post-hoc normalizations.

The passive basket result is strongly influenced by the exceptional historical paths of SOL-USD and NVDA. This reinforces the existing selection/survivorship limitation of the narrow high-profile universe rather than resolving it.

## Relationship to prior experiments

The frozen v1 run reproduced the established headline baseline: 65 trades, about +39.17% total return, 6.01% CAGR, and -4.25% maximum drawdown. No strategy, risk, or execution parameter changed.

EXP-0004 does not repair the temporal-stability failure from EXP-0003. v1 remains weak in 2025 and 2026-YTD, and the prospective holdout remains the only path to genuinely unseen evidence.

## Provider revision note

BTC-USD and SOL-USD source hashes remain unchanged from recent experiments. Adjusted META, NVDA, and QQQ hashes changed again relative to the EXP-0003 snapshot. The comparison remains internally controlled because strategy and passive references share the same current snapshot.

This is another reason not to interpret tiny cross-run metric changes as strategy changes when immutable provider snapshots are unavailable.

## Decision

`REFERENCE BASELINES ADDED — CONTINUE RESEARCH — DO NOT DEPLOY — KEEP V1 FROZEN`

The project now has an explicit opportunity-cost comparison. v1 has much lower absolute historical return than passive ownership of this selected universe, but also drastically lower drawdown/exposure and higher recorded Sharpe/Sortino. Neither observation establishes a validated edge.

## Next research step

Keep v1 frozen for `PROSPECTIVE-v1-holdout`. Next run a preregistered parameter-neighborhood robustness diagnostic without selecting a new parameter set from the result, then broaden the universe to reduce selection/survivorship bias. Forward holdout recording should proceed independently of retrospective diagnostics.
