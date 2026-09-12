# EXP-0004 Reference Baselines

Status: Completed on merge

## Problem

The frozen v1 strategy had exploratory historical performance, execution-cost sensitivity, and retrospective temporal-stability diagnostics, but no simple passive/reference comparison. Without one, opportunity cost was invisible.

## Goals

- Compare frozen v1 with per-symbol buy-and-hold and an initial equal-weight buy-and-hold basket over the same evaluation window.
- Apply the same asset-class execution-cost assumptions to passive entry and terminal liquidation.
- Reuse one provider snapshot for v1 and all references.
- Record return, CAGR, maximum drawdown, Sharpe, Sortino, exposure, and provenance.
- Keep v1 and the prospective holdout unchanged regardless of the retrospective result.

## Non-goals

- No v1 tuning.
- No optimized weights, rebalance frequency, volatility targeting, or leverage normalization.
- No broader-universe or parameter-neighborhood test.
- No out-of-sample claim.

## Implemented design

- `reference_baselines.py` builds deterministic cost-aware buy-and-hold sleeves and an initial equal-weight basket.
- Passive sleeves enter at the first real evaluation-window open, remain fixed, and liquidate at the final real close.
- Mixed calendars do not create synthetic fills; an allocation remains cash before its first tradable bar.
- `metrics.py` exposes reusable equity-curve return/risk metrics while preserving existing portfolio metrics.
- `reference_comparison.py` runs frozen v1 and all references through one shared provider cache, verifies no additional passive downloads, and writes strict artifacts.
- `swing-reference-comparison` and `.github/workflows/exp-0004.yml` make the experiment reproducible locally and in CI.

## Validation

- `pytest -q`: PASS in CI on producer SHA `7401577f0eaf80878091b7ac317e688c369b4a67`.
- `ruff check src tests`: PASS on the same SHA.
- EXP-0001, EXP-0003, and EXP-0004 real-data workflows passed after the reusable metrics change; EXP-0002 was also rerun by dependency paths.
- EXP-0004 workflow run `34711644430`: PASS.
- Artifact `10303308018`, SHA-256 `a145fa51e2f03e449218b857270264ef6f7c3f49f4a0230c5be9cc243ffb32af`, inspected before durable interpretation was written.
- Passive construction reused the strategy-populated five-symbol snapshot and caused zero extra provider downloads.

## Reviewed result

Frozen v1 produced +39.17% total return, 6.01% CAGR, -4.25% maximum drawdown, 1.27 Sharpe, 2.16 Sortino, and about 6.04% average exposure.

The initial equal-weight passive basket produced +2,139.01% total return, 73.16% CAGR, -95.19% maximum drawdown, 1.06 Sharpe, 1.62 Sortino, and about 99.89% average exposure.

Every single-asset passive reference also exceeded v1's absolute return, while v1 had the smallest drawdown and the highest recorded Sharpe/Sortino of the reference set. The passive outcome is heavily influenced by SOL and NVDA and therefore reinforces rather than resolves narrow-universe selection concerns.

## Simplify

No further simplification was justified after implementation. The solution remains limited to pure passive-sleeve helpers, reusable equity metrics, and one experiment orchestrator. A generic benchmark framework, rebalance engine, optimizer, and leverage-normalization layer were intentionally not introduced.

## Compound

Reusable learning is recorded in `docs/solutions/trading-research/control-passive-reference-comparisons.md`: passive references should be preregistered and share snapshot/cost conventions with the active strategy, while return must be interpreted beside exposure and drawdown.

## Research integrity

EXP-0004 is retrospective on already-observed data. It does not repair the EXP-0003 temporal-stability failure and does not alter `PROSPECTIVE-v1-holdout`. Interim or retrospective evidence must not be used to tune v1.

## Decision

`REFERENCE BASELINES ADDED — CONTINUE RESEARCH — DO NOT DEPLOY — KEEP V1 FROZEN`

## Follow-up

Run parameter-neighborhood robustness next without selecting a new v1 parameter set from retrospective results, then broaden the universe. Build prospective forward recording independently.
