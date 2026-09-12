---
schema_version: 1
id: KN-0003
title: Performance ratios are estimates with assumptions
topics:
  - performance-measurement
  - sharpe-ratio
  - statistics
source_ids:
  - SRC-0006
status: curated
---

# Performance ratios are estimates with assumptions

## What the evidence says

`SRC-0006` derives statistical properties of the Sharpe ratio under different return assumptions and shows that estimation error and serial dependence matter. Simple square-root-time annualization is not automatically valid for every return process.

A backtest metric is therefore an estimate produced from a finite, dependent path, not a timeless property of a trading rule.

## Project implication

Swing Trader should report multiple complementary metrics and interpret Sharpe alongside drawdown, expectancy in R, profit factor, exposure, trade count, temporal stability, and the construction of the return series. Small samples and autocorrelation should reduce confidence in precise comparisons.

Future metric work can add uncertainty or dependence-aware diagnostics when they answer a preregistered research question. Metric sophistication should not be introduced merely to improve a headline value.

## What it does not establish

This source does not imply that Sharpe should be discarded, nor does it provide a universal replacement statistic. It also does not determine whether the project's current strategy is economically attractive.

A higher historical Sharpe remains insufficient evidence of superiority when exposure, drawdown, selection bias, costs, or sample composition differ materially.

## Sources

- `SRC-0006` — Lo (2002), statistical properties and time aggregation of Sharpe ratios.
