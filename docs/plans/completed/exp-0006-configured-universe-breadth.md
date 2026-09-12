# Design Plan — EXP-0006 Configured Universe Breadth

Status: Completed

## Problem

All prior retrospective diagnostics depended on the same four-symbol BTC-USD / SOL-USD / META / NVDA subset. EXP-0006 tested whether frozen v1 remained positive and whether realized profit contribution broadened when the shared-account portfolio used the complete 11-asset universe already versioned in `config/universe.yaml` before the experiment.

## Frozen design

The four-symbol EXP-0001 subset was rerun as a same-snapshot control. The expanded universe was fixed before results to:

- BTC-USD
- ETH-USD
- SOL-USD
- META
- NVDA
- MSFT
- AAPL
- AMZN
- GOOGL
- AVGO
- TSLA

The seven added symbols were ETH-USD, MSFT, AAPL, AMZN, GOOGL, AVGO, and TSLA.

Dates, strategy logic, score threshold, ATR stops, risk fraction, position/risk caps, execution costs, and benchmarks remained frozen to EXP-0001.

## Preregistered criteria

Breadth required all of:

- expanded portfolio total return > 0, expectancy R > 0, and profit factor > 1;
- added-symbol aggregate realized net PnL > 0;
- at least 4 / 11 symbols positive contributors;
- at least 2 / 7 added symbols positive contributors;
- positive contributors in both equity and crypto;
- largest positive symbol <=60% of summed positive symbol PnL;
- four-symbol control joint-positive and within fixed EXP-0001 reproduction tolerances.

The universe and thresholds were not changed after observing the real-data run.

## Implementation

`src/swing_trader/universe_breadth.py` provides strict universe/criteria locks, EXP-0001-derived control and expanded configs, a shared provider cache, full shared-account path reruns, overlapping-source digest checks, symbol/asset-class realized contribution, concentration diagnostics, control reproduction, and aggregate preregistered criteria.

`src/swing_trader/universe_breadth_cli.py`, tests, versioned config, and `.github/workflows/exp-0006.yml` provide local/CI execution and artifact validation.

The runner does not search, rank, remove, or promote symbols based on historical results.

## Trading/research integrity

- No look-ahead semantics changed.
- Both paths rerun the actual shared-account portfolio so assets compete for the same cash, four position slots, and 2% open-risk budget.
- One 12-symbol provider snapshot covers all 11 assets plus QQQ; overlapping control/expanded digests are identical.
- Frozen strategy/risk/execution settings are unchanged.
- All tested history was already observable; EXP-0006 is retrospective evidence only.
- The current configured universe remains a survivor/high-profile universe rather than point-in-time membership data.

## Validation and reviewed result

- `pytest -q`: PASS
- `ruff check src tests`: PASS
- real-data EXP-0006 workflow: PASS
- shared provider downloads: 12
- overlapping source digests: identical
- expanded path: +39.98% total return, 6.12% CAGR, -5.13% max drawdown, +0.49R expectancy, 2.04 profit factor, 141 trades, 14.98% average exposure
- four-symbol control: +39.17% total return, 6.01% CAGR, -4.25% max drawdown, +1.05R expectancy, 3.18 profit factor, 65 trades, 6.04% average exposure
- added-symbol aggregate net PnL: +514.76
- positive contributors: 8 / 11 total and 5 / 7 added
- positive asset classes: crypto and equity
- largest positive contributor: SOL-USD at 30.58% of positive symbol PnL, below the 60% ceiling
- control reproduction: PASS within every preregistered tolerance
- all preregistered breadth criteria: PASS

The expanded portfolio had slightly higher absolute return/CAGR but lower expectancy/profit factor and higher drawdown/exposure. The reviewed conclusion is broader contribution, not superiority of the expanded path.

## Simplify

PASS. The implementation remains one strict two-path orchestrator around the existing experiment runner. No universe optimizer, constituent database, generic attribution framework, or ranking/search engine was added.

## Compound

Reusable lesson captured in `docs/solutions/trading-research/test-universe-breadth-with-fixed-membership-and-contribution.md`: fix membership independently of results, share inputs, rerun the full shared-account path, inspect contribution/concentration, and do not confuse a broader current-survivor list with point-in-time survivorship control.

## Definition of done

Completed: exact control/expanded paths reproducible on one controlled snapshot, breadth/contribution criteria reviewed and durably recorded, no preferred subset selected, frozen v1 and prospective holdout unchanged, validation green, and plan archived. Final PR review and merge remain the lifecycle gate.
