# Design Plan — EXP-0005 Parameter Neighborhood

Status: Completed

## Problem

Frozen v1 had positive aggregate history and cost robustness but failed temporal-stability thresholds. EXP-0005 tested whether that aggregate result depended on the exact score/stop/trailing-stop point.

## Frozen design

The preregistered center remained `min_score=70`, `stop_atr=2.0`, `trail_atr=2.5`.

Exactly 27 Cartesian scenarios were fixed before real-data execution:

- `min_score`: `[65, 70, 75]`
- `stop_atr`: `[1.5, 2.0, 2.5]`
- `trail_atr`: `[2.0, 2.5, 3.0]`

Only those three fields could change. Universe, dates, execution costs, risk fraction, position/risk caps, indicators, score logic, and prospective v1 specification stayed frozen.

## Preregistered criteria

A scenario was `joint_positive` only if total return > 0, expectancy R > 0, and profit factor > 1. Local robustness required all of:

- >=18 / 27 joint-positive scenarios;
- >=5 / 6 immediate axial neighbors joint-positive;
- median expectancy >= +0.50R;
- frozen center joint-positive and within explicit EXP-0001 reproduction tolerances.

Missing expectancy was preregistered as 0R for the median. Criteria were not changed after results.

## Implementation

`src/swing_trader/parameter_neighborhood.py` provides strict config validation, deterministic scenario expansion, shared-download input control, per-scenario EXP-0001-derived configs, full `run_experiment` reruns, digest checks, scenario summaries, center reproduction checks, and aggregate preregistered criteria.

`src/swing_trader/parameter_neighborhood_cli.py`, tests, versioned config, and `.github/workflows/exp-0005.yml` provide local/CI execution and artifact validation.

The implementation deliberately does not provide optimization, ranking, winner promotion, generic hyperparameter search, or parallel scheduling.

## Trading/research integrity

- No look-ahead semantics changed.
- Every path-dependent parameter variation reran the full portfolio engine.
- One five-symbol provider snapshot was reused across all 27 scenarios.
- No risk/execution policy outside the three declared variables changed.
- All history was already observed; EXP-0005 is retrospective sensitivity evidence only.
- No scenario was promoted into v1 or the prospective holdout.

## Validation and reviewed result

- `pytest -q`: PASS
- `ruff check src tests`: PASS
- real-data EXP-0005 workflow: PASS
- provider downloads: 5 total across 27 scenarios
- source digests identical across scenarios
- joint-positive scenarios: 27 / 27 (required >=18)
- joint-positive axial neighbors: 6 / 6 (required >=5)
- median expectancy: +0.92R (required >=+0.50R)
- frozen-center reproduction: PASS within every preregistered tolerance
- all preregistered criteria: PASS

Metric magnitude remained parameter-sensitive, with expectancy roughly +0.43R to +1.73R. The interpretation is therefore local robustness, not parameter irrelevance.

## Simplify

PASS. The final implementation remains one strict scenario model/generator plus one orchestrator around the existing experiment runner. No generic optimizer or parameter framework was added.

## Compound

Reusable lesson captured in `docs/solutions/trading-research/evaluate-parameter-neighborhoods-without-winner-selection.md`: preregister the neighborhood and criteria, share inputs, rerun the full path, evaluate the surface and immediate neighbors, and never promote the retrospective winner into a frozen prospective strategy.

## Definition of done

Completed: exact neighborhood reproducible on one controlled snapshot, reviewed result durably recorded, v1 unchanged, prospective holdout unchanged, validation green, plan archived, and final PR review required before merge.
