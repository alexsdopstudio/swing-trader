# EXP-0005 — Parameter-Neighborhood Review

Status: Reviewed retrospective parameter-robustness diagnostic

## Research integrity

EXP-0005 does **not** claim out-of-sample validation. The complete 2021-01-01 through 2026-08-31 history was already observed before this experiment.

The purpose is narrower: test whether the frozen v1 historical result survives a small, preregistered neighborhood around its score threshold and ATR stop/trailing-stop settings. The grid and pass/fail criteria were versioned before the real-data run. No scenario is promoted as a replacement for v1.

## Preregistered neighborhood

Frozen v1 center:

- `min_score = 70`
- `stop_atr = 2.0`
- `trail_atr = 2.5`

Exact Cartesian grid:

- `min_score`: 65, 70, 75
- `stop_atr`: 1.5, 2.0, 2.5
- `trail_atr`: 2.0, 2.5, 3.0
- total scenarios: 27

A scenario is `joint_positive` only when total return > 0, expectancy R > 0, and profit factor > 1.

Predeclared support required all of the following:

1. at least 18 / 27 scenarios joint-positive;
2. at least 5 / 6 immediate axial neighbors joint-positive;
3. median expectancy at least +0.50R;
4. the exact v1 center remains joint-positive and reproduces the durable EXP-0001 result within the predeclared provider-revision tolerances.

Missing expectancy, if any, was preregistered as 0R for the median calculation. No scenarios were missing expectancy in the reviewed run.

## Run provenance

- experiment: `EXP-0005`
- producer code SHA: `7db5ac84b03c01af6dbbdc1c72922fe6bc25fb3b`
- GitHub Actions run: `34712328760`
- artifact id: `10303114360`
- artifact SHA-256: `27c1d576a1d0417f2019f3ab6f2091e1e43a1944f45a07aede91fbefd37f1c28`
- runtime: Python 3.12.14, NumPy 2.5.3, pandas 3.0.5, PyYAML 6.0.3, yfinance 1.7.0
- provider downloads: 5 total for the complete 27-scenario run
- source digests: identical across every scenario
- unchanged source symbols versus durable EXP-0001: BTC-USD and SOL-USD
- revised adjusted-data symbols versus durable EXP-0001: META, NVDA, and QQQ

Each scenario reran the complete portfolio path. Only `min_score`, `stop_atr`, and `trail_atr` changed; risk fraction, portfolio caps, universe, strategy logic, and execution-cost assumptions remained frozen.

## Preregistered criteria

| Criterion | Required | Observed | Result |
|---|---:|---:|---|
| Joint-positive scenarios | >= 18 / 27 | 27 / 27 | PASS |
| Joint-positive axial neighbors | >= 5 / 6 | 6 / 6 | PASS |
| Median expectancy | >= +0.50R | +0.92R | PASS |
| Frozen-center reproduction | Within preregistered tolerances and joint-positive | All checks within tolerance | PASS |

All preregistered criteria passed.

## Frozen-center reproduction

The exact v1 center produced:

- 65 closed trades;
- +39.17% total return;
- 6.01% CAGR;
- -4.25% maximum drawdown;
- 3.18 profit factor;
- +1.05R expectancy;
- about 6.04% average exposure.

Differences from the durable EXP-0001 record were effectively zero and comfortably inside every preregistered tolerance. The tiny differences are consistent with the already-documented yfinance revisions to adjusted META/NVDA/QQQ history.

## Neighborhood distribution

The important result is the surface, not the historical winner.

Across all 27 scenarios:

- total return ranged from +19.69% to +63.99%;
- CAGR ranged from +3.23% to +9.13%;
- maximum drawdown ranged from about -3.30% to -7.36%;
- profit factor ranged from 2.18 to 3.96;
- expectancy ranged from +0.43R to +1.73R;
- median expectancy was +0.92R;
- trade count ranged from 54 to 88;
- average exposure ranged from about 3.76% to 8.70%.

Every point remained profitable with positive expectancy and profit factor above 1. That materially reduces concern that the aggregate EXP-0001 result depends on the exact 70 / 2.0 / 2.5 point.

The magnitude is still parameter-sensitive: expectancy and total return vary substantially across the grid. Passing EXP-0005 therefore means **local sign/quality robustness is supported**, not that parameter choice is irrelevant.

## Immediate neighbors

All six one-coordinate perturbations around v1 remained joint-positive. Their expectancy ranged from about +0.67R to +1.38R. This is stronger local evidence than finding isolated positive points elsewhere in the grid because it directly tests the neighborhood adjacent to the frozen center.

## Relationship to prior experiments

EXP-0005 does not repair the temporal-stability failure from EXP-0003. A strategy can be locally robust to parameter perturbations and still be regime-dependent through time. The 2025 and 2026-YTD weakness therefore remains a material limitation.

EXP-0005 also does not resolve the narrow-universe and survivorship/selection concerns made more visible by EXP-0004. All 27 scenarios use the same selected BTC-USD, SOL-USD, META, and NVDA universe.

Execution-cost robustness from EXP-0002, temporal instability from EXP-0003, passive opportunity cost from EXP-0004, and local parameter robustness from EXP-0005 are complementary facts rather than substitutes for one another.

## No winner selection

Some retrospective parameter combinations produced better historical metrics than frozen v1. They are intentionally **not** labeled, selected, promoted, or transferred into the strategy specification.

Using the same already-observed history to choose a replacement after seeing the surface would convert a robustness diagnostic into retrospective optimization and would violate the prospective holdout freeze. v1 remains exactly 70 / 2.0 / 2.5.

## Decision

`LOCAL PARAMETER ROBUSTNESS SUPPORTED RETROSPECTIVELY — KEEP V1 FROZEN — CONTINUE RESEARCH — DO NOT DEPLOY`

The historical result is not a narrow single-point artifact inside the tested three-parameter neighborhood. Confidence in local parameter stability increases, while confidence in temporal uniformity remains limited and true prospective validation remains unavailable.

## Next research step

Keep v1 frozen and begin the preregistered prospective holdout on 2026-09-14 with a provenance-preserving forward recorder. The next retrospective diagnostic should broaden the universe to reduce selection/survivorship bias rather than further mining the same parameter surface.
