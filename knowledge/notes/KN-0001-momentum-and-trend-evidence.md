---
schema_version: 1
id: KN-0001
title: Momentum and trend are research priors, not strategy validation
topics:
  - momentum
  - trend
  - hypothesis-formation
source_ids:
  - SRC-0001
  - SRC-0002
status: curated
---

# Momentum and trend are research priors, not strategy validation

## What the evidence says

`SRC-0001` documents intermediate-horizon cross-sectional momentum in equities: past relative winners and losers showed return continuation over the study's formation/holding horizons. `SRC-0002` documents time-series momentum across a broad set of liquid futures, with return persistence at intermediate horizons across several asset classes.

Together, these sources establish that momentum/trend effects have serious empirical precedent in financial research and are reasonable phenomena to investigate rather than patterns invented after observing this repository's backtest.

## Project implication

Swing Trader may legitimately use momentum, trend, and relative-strength concepts as preregistered research inputs. Experiments should test the actual implementation, timing, costs, universe, and risk rules instead of treating the existence of published momentum evidence as sufficient.

The relevant project question is not "does momentum exist in some historical literature?" but "does this exact frozen implementation retain useful behavior under realistic costs, changing regimes, broader universes, and genuinely future observations?"

## What it does not establish

The cited work does not validate the v1 Swing Score, the 70-point threshold, ATR stop distances, the configured asset universe, a long-only implementation, or expected future profitability. The papers use different instruments, constructions, horizons, and portfolio assumptions.

Published precedent is a prior for hypothesis formation. Swing Trader's own experiments and prospective holdout remain the evidence for project-specific claims.

## Sources

- `SRC-0001` — Jegadeesh & Titman (1993), cross-sectional equity momentum.
- `SRC-0002` — Moskowitz, Ooi & Pedersen (2012), time-series momentum across liquid futures.
