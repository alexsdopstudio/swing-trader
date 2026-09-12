---
schema_version: 1
id: KN-0002
title: Repeated historical selection weakens inference
topics:
  - backtesting
  - data-snooping
  - multiple-testing
  - overfitting
source_ids:
  - SRC-0003
  - SRC-0004
  - SRC-0005
status: curated
---

# Repeated historical selection weakens inference

## What the evidence says

`SRC-0003` formalizes the data-snooping problem: reusing the same data for model selection and inference creates a material chance that an apparently good result arose from search rather than genuine predictive content. `SRC-0004` shows why conventional significance standards become less convincing when many return predictors have been tried. `SRC-0005` develops a framework specifically for estimating backtest-overfitting risk after selecting among investment simulations.

The common lesson is that the path by which a strategy was selected matters. Reporting only a surviving backtest hides information needed to judge the result.

## Project implication

Swing Trader should continue to record failed and successful experiments, freeze decisions before genuinely future evidence arrives, avoid promoting retrospective parameter winners, and keep the prospective holdout isolated from tuning. Parameter-neighborhood and sensitivity diagnostics are useful as robustness checks, but they remain retrospective evidence.

The number and nature of alternatives tried should be visible in repository history whenever a strategy decision depends on historical comparisons.

## What it does not establish

No single anti-overfitting procedure guarantees that a strategy has a real edge. Passing a parameter-neighborhood test, using a holdout split, or applying a multiple-testing correction cannot compensate for unrealistic execution, survivorship bias, regime dependence, or poor data provenance.

This note also does not convert the existing retrospective experiments into out-of-sample validation. Only the preregistered future protocol can do that for frozen v1.

## Sources

- `SRC-0003` — White (2000), data snooping and model selection.
- `SRC-0004` — Harvey, Liu & Zhu (2016), multiple testing in return research.
- `SRC-0005` — Bailey, Borwein, López de Prado & Zhu (2017), probability of backtest overfitting.
