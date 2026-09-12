# Separate Warm-Up and Evaluation Windows

## Problem

Time-series strategies need historical observations before an evaluation period begins so long-lookback indicators, relative-strength features, and regime filters are fully initialized.

If the download start and evaluation start are treated as the same concept, one of two errors usually follows:

- the first part of the evaluation period is unusable because indicators are still warming up; or
- pre-evaluation bars leak into reported portfolio results, making the stated test window inaccurate.

## Root cause

Data acquisition, feature initialization, and performance evaluation have different time requirements, but a single `start` date hides those distinct responsibilities.

## Reusable solution

Every historical experiment should version at least three dates explicitly:

1. `warmup_start` — earliest data requested for indicator/feature initialization;
2. `evaluation_start` — first date eligible to affect portfolio trades and reported metrics;
3. `evaluation_end` — exclusive upper bound of the evaluation window.

Calculate indicators, scores, and benchmark regimes over the complete warm-up history first. Only then slice asset data, score series, and regime series to the evaluation window before passing them to the portfolio backtester.

Record both requested windows and actual provider coverage. The actual first observation can differ from the requested warm-up start, especially for newer assets such as SOL-USD.

## When this applies

- moving-average and momentum strategies;
- rolling volatility / ATR features;
- relative-strength features requiring a benchmark;
- market-regime filters;
- walk-forward and held-out experiments;
- assets with different listing dates or trading calendars.

## When this does not apply

A stateless strategy that uses only information from the current bar may not require a separate warm-up period, but the evaluation window should still be explicit.

## Tests and checks

Require tests that verify:

- bars before `evaluation_start` cannot appear in the portfolio equity curve or trades;
- `evaluation_end` is treated consistently as inclusive or exclusive and documented;
- indicators are calculated before slicing to the evaluation window;
- each requested symbol records actual source and evaluation coverage;
- missing evaluation data fails loudly instead of silently removing a requested asset.

During review, distinguish a missing warm-up period from a deliberately quiet trading period. No trades early in a test may be a strategy outcome rather than an indicator-initialization artifact.

## Evidence

EXP-0001 requested warm-up history from 2020-01-01 while evaluation began on 2021-01-01. SOL-USD data actually began on 2020-04-10, while the equity series began on 2020-01-02. Recording actual coverage made that discrepancy explicit without contaminating the evaluation period.

## References

- `src/swing_trader/experiment.py`
- `experiments/EXP-0001-baseline/config.yaml`
- `experiments/EXP-0001-baseline/results.json`
- PR #5 — EXP-0001 baseline
