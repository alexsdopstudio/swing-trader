# Design Plan

Status: Active

## Problem

Frozen v1 has a positive aggregate historical result, survives materially higher execution costs, fails preregistered temporal-stability thresholds, and now has explicit passive/reference comparisons. The next unresolved question is whether the retrospective result is locally stable around its chosen score/stop/trailing-stop parameters or depends on a narrow point estimate.

## Goals

- Run a preregistered local parameter grid around frozen v1 without changing v1 itself.
- Vary only `min_score`, `stop_atr`, and `trail_atr`; keep data, universe, costs, risk fractions, position caps, and strategy logic fixed.
- Evaluate the full Cartesian neighborhood on one shared provider snapshot.
- Record scenario-level return, CAGR, max drawdown, profit factor, expectancy R, trade count, exposure, and execution cost.
- Predeclare robustness criteria before observing real-data results.
- Treat EXP-0005 as retrospective sensitivity evidence only; do not select or promote a new parameter set from the result.

## Non-goals

- No modification of frozen v1 or `PROSPECTIVE-v1-holdout`.
- No parameter optimization, winner selection, ranking-driven retuning, Bayesian search, or walk-forward selection.
- No changes to indicator lookbacks, score component weights, execution costs, risk fraction, max-open-risk, max positions, or universe.
- No broader-universe test in this PR.
- No true out-of-sample claim.

## Preregistered neighborhood

The v1 center is `min_score=70`, `stop_atr=2.0`, `trail_atr=2.5`.

EXP-0005 will evaluate exactly 27 Cartesian scenarios:

- `min_score`: `[65, 70, 75]`
- `stop_atr`: `[1.5, 2.0, 2.5]`
- `trail_atr`: `[2.0, 2.5, 3.0]`

The baseline center is one of those 27 scenarios. All values and criteria are versioned before the real-data run.

## Predeclared robustness criteria

A scenario is `joint_positive` when all three are true:

1. total return > 0;
2. expectancy R > 0;
3. profit factor > 1.

Local robustness is considered supported only if all of these preregistered criteria hold:

- at least 18 of 27 scenarios are `joint_positive`;
- at least 5 of the 6 immediate axial neighbors of the v1 center are `joint_positive`;
- median expectancy across all 27 scenarios is at least +0.50R;
- the exact v1 center reproduces the current frozen baseline within normal provider-revision tolerance and remains `joint_positive`.

These thresholds will not be changed after observing EXP-0005 results. Passing them would indicate local retrospective robustness, not validation or permission to deploy. Failing them will not trigger parameter replacement inside v1.

## Relevant context

- `experiments/EXP-0001-baseline/config.yaml` is the frozen center configuration.
- EXP-0002 established execution-cost sensitivity on one shared snapshot.
- EXP-0003 failed temporal-stability criteria, so local parameter robustness cannot erase regime dependence.
- EXP-0004 added passive opportunity-cost references and kept v1 frozen.
- `PROSPECTIVE-v1-holdout` starts 2026-09-14 and forbids interim v1 tuning.

## Proposed design

Add `src/swing_trader/parameter_neighborhood.py` with:

- strict config loading/validation for the exact preregistered grid and criteria;
- deterministic Cartesian scenario generation with a stable scenario name;
- one shared `SharedDownloadCache` across every `run_experiment` call;
- generated per-scenario EXP-0001-derived configs that modify only the three allowed portfolio fields;
- source-digest equality checks across all 27 scenarios;
- scenario summaries and aggregate robustness diagnostics;
- strict JSON plus a compact scenario CSV and generated notes.

Add `swing-parameter-neighborhood` CLI and `.github/workflows/exp-0005.yml` to execute the real-data study and upload detailed scenario artifacts.

## Trading and research implications

- Look-ahead: unchanged from the frozen portfolio backtester; close-derived signals still execute no earlier than the next asset open.
- Execution realism: all scenarios use the unchanged asset-class execution-cost config.
- Risk controls: risk fraction and portfolio caps are frozen; ATR stop/trail distances are research variables, so each scenario must rerun the full portfolio path because they alter sizing, exits, open risk, cash, and subsequent opportunities.
- Data control: all scenarios share one provider snapshot to prevent yfinance revisions from masquerading as parameter effects.
- Multiple comparisons: EXP-0005 summarizes the neighborhood distribution and preregistered pass/fail criteria. It will not promote the best-performing scenario.
- Evidence status: all history was already observed. This is a retrospective fragility diagnostic, not out-of-sample evidence.

## Alternatives considered

- One-at-a-time perturbations only: rejected because interactions between score threshold and stop/trail distances can materially alter the portfolio path.
- Larger/finer grid: rejected because it increases multiplicity and compute without improving the immediate local-fragility question.
- Include risk fraction or max-position fraction: rejected because those are account-risk policy rather than the narrow strategy neighborhood being tested here.
- Optimize a replacement v1 configuration: rejected because the prospective v1 protocol is already frozen and retrospective winner selection would increase overfitting.

## Test and validation plan

- Unit tests for strict config validation and exact 27-scenario expansion.
- Unit tests that only the three allowed fields change from the base config.
- Unit tests for axial-neighbor identification and preregistered aggregate criteria.
- Runner test with synthetic downloader proving one shared provider snapshot and identical source digests across scenarios.
- `pytest -q` and `ruff check src tests`.
- Real-data EXP-0005 workflow with artifact inspection before durable interpretation.
- Regression EXP-0001/2/3/4 workflows remain green if shared code changes.
- Formal diff review focused on frozen-v1 integrity, no winner selection, no look-ahead, shared inputs, criteria preregistration, and non-OOS framing.

## Simplification plan

Keep the implementation to one scenario generator and one orchestrator around the existing experiment runner. Do not build a generic optimizer, hyperparameter framework, result database, parallel scheduler, or strategy registry.

## Compound plan

Likely reusable lesson: parameter-neighborhood tests should preregister a local grid and stability criteria, rerun the full path on shared inputs, and evaluate the surface rather than selecting the historical winner. If confirmed, record it under `docs/solutions/trading-research/`.

## Documentation and memory updates

- `experiments/EXP-0005-parameter-neighborhood/` config and reviewed outputs.
- `experiments/README.md`.
- `.ai/current-state.md`.
- `docs/roadmap.md`.
- `README.md` if the new CLI/result is user-relevant.
- `docs/solutions/README.md` and a research solution note if Compound produces reusable knowledge.
- Archive this plan under `docs/plans/completed/` before final review.

## Implementation plan

1. Add strict EXP-0005 config and deterministic scenario expansion.
2. Implement shared-snapshot scenario runner and aggregate robustness diagnostics.
3. Add CLI, tests, and real-data workflow.
4. Run Simplify and validation.
5. Run and inspect the real-data EXP-0005 artifact.
6. Record reviewed results without modifying v1.
7. Complete Compound and durable memory updates; archive this plan.
8. Perform formal final-diff review and merge only after `PASS` and green CI.

## Review checklist

- [x] Scope and acceptance criteria are clear.
- [x] Parameter grid is fixed before real-data results.
- [x] Robustness criteria are fixed before real-data results.
- [x] Design preserves frozen v1 and prospective holdout integrity.
- [x] Full-path reruns are required where parameters alter sizing/exits.
- [x] Shared-input and reproducibility controls are explicit.
- [x] Simplification and Compound destinations are identified.

## Definition of done

EXP-0005 is complete when the repository can reproduce the exact 27-scenario parameter neighborhood on one controlled snapshot, reviewed results and preregistered criteria are durably recorded without selecting a replacement parameter set, v1 and the prospective holdout remain unchanged, tests/lint/experiment CI are green, the final diff receives a formal `PASS`, and the PR is merged into `main`.
