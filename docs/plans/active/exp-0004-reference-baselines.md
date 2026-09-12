# Design Plan

Status: Active

## Problem

The frozen v1 strategy has exploratory historical performance, execution-cost sensitivity, and retrospective temporal-stability diagnostics, but the repository still lacks simple passive/reference baselines. Without them, the research cannot show whether the strategy's return and risk profile added value relative to simply holding the same assets through the same evaluation window.

## Goals

- Add deterministic passive baseline construction for the same symbols and evaluation window used by the frozen v1 experiment.
- Compare v1 with per-symbol buy-and-hold and an equal-weight buy-and-hold basket.
- Apply the same asset-class execution-cost assumptions to baseline entry and end-of-window liquidation.
- Reuse one downloaded market-data snapshot for the strategy and all reference baselines.
- Record return, CAGR, max drawdown, Sharpe, and Sortino for each baseline and strategy-relative deltas.
- Run EXP-0004 as a retrospective comparison only; preserve the prospective v1 holdout and do not tune v1 from these results.

## Non-goals

- No change to v1 score, entry, exit, sizing, stop, risk, or execution parameters.
- No rebalancing optimizer, tactical benchmark, volatility targeting, or benchmark-selection search.
- No claim that historical baseline outperformance or underperformance is true out-of-sample evidence.
- No broader-universe or parameter-neighborhood study in this PR.

## Relevant context

- `experiments/EXP-0001-baseline/config.yaml` freezes the evaluation universe, dates, portfolio settings, and execution-cost configuration.
- `src/swing_trader/experiment.py` already orchestrates the frozen v1 run and records reproducibility metadata.
- `src/swing_trader/execution.py` defines immutable asset-class execution costs.
- `src/swing_trader/metrics.py` owns portfolio return/risk metrics.
- `.ai/current-state.md` and `docs/roadmap.md` explicitly name passive/reference baselines as the next research milestone.
- `PROSPECTIVE-v1-holdout` remains frozen and begins 2026-09-14; EXP-0004 must not alter it.

## Proposed design

Add `src/swing_trader/reference_baselines.py` with small pure helpers that build cost-aware buy-and-hold equity curves from already-downloaded OHLC data.

For each symbol:

1. Allocate the requested starting capital.
2. Enter once at the first available evaluation-window open using the configured adverse buy fill and entry commission.
3. Hold a fixed quantity with no rebalancing.
4. Mark daily equity from cash plus position value at market-reference close.
5. On the final available bar, liquidate using the configured adverse sell fill and exit commission so terminal equity is cost-comparable with the strategy backtest.

For the equal-weight basket, divide initial equity equally across the experiment symbols and sum the independently marked sleeves on the union of evaluation dates. Each sleeve remains cash until its first tradable bar, so mixed equity/crypto calendars do not create synthetic fills.

Refactor `src/swing_trader/metrics.py` minimally to expose equity-curve return/risk metrics reusable by both strategy and passive curves while preserving current `BacktestMetrics` behavior.

Add `src/swing_trader/reference_comparison.py` and a `swing-reference-comparison` CLI. The runner will:

- load a versioned EXP-0004 config;
- use a shared download cache/snapshot for all required symbols and benchmarks;
- run the frozen v1 strategy through the existing experiment/backtest path semantics;
- construct per-symbol and equal-weight passive baselines from the same source frames;
- verify source-data digests are shared across strategy and baseline calculations;
- write strict JSON, a compact comparison CSV, baseline equity curves, resolved config, and generated notes.

Add `.github/workflows/exp-0004.yml` for the real-data run and artifact upload.

## Trading and research implications

- Look-ahead: passive entries use only the first available open in the evaluation window; no future prices determine entries.
- Execution realism: baseline entry and terminal liquidation use the same asset-class commission/spread/slippage model as the strategy.
- Mixed calendars: allocations remain cash until each asset's first available open; curves are aligned by forward-filling the last known marked sleeve value, never by fabricating missing bars.
- Risk controls: v1 deterministic risk controls are unchanged. Passive baselines intentionally do not use v1 sizing/stops because they are opportunity-cost references, not alternate active strategies.
- Overfitting: baseline definitions are fixed before observing EXP-0004 results. No baseline weights or rules will be selected based on performance.
- Reproducibility: config, code SHA, runtime versions, source coverage, and source-data digests are recorded.
- Evidence status: EXP-0004 is retrospective on already-observed history and cannot support a true out-of-sample validation claim.

## Alternatives considered

- Compare only with cash: rejected because it does not measure opportunity cost of owning the same risk assets.
- Use only QQQ and BTC benchmark buy-and-hold: rejected as the sole reference because a 50/50 cross-asset allocation would add an arbitrary portfolio-weight choice. Benchmark symbols may remain contextual data, but the primary passive reference should use the exact experiment symbols.
- Periodically rebalance the equal-weight basket: rejected because rebalance frequency would introduce another parameter and additional turnover assumptions.
- Add a generic benchmark framework: rejected as premature. A small passive-baseline module is sufficient for the current research question.

## Test and validation plan

- Unit tests for single-symbol cost-aware buy-and-hold arithmetic.
- Tests that equal-weight sleeves sum correctly across mixed calendars and remain cash before first tradable bars.
- Regression tests that reusable equity metrics preserve existing strategy metric calculations.
- Tests that the comparison runner reuses one source snapshot and rejects mismatched/empty data.
- `pytest -q` and `ruff check src tests`.
- Real-data EXP-0004 workflow, artifact inspection, and durable reviewed results before merge.
- Formal diff review focused on no look-ahead, cost comparability, calendar alignment, frozen-v1 integrity, and non-OOS framing.

## Simplification plan

Challenge any abstraction beyond: one passive sleeve helper, one equal-weight aggregation helper, reusable equity metrics, and one experiment orchestrator. Avoid benchmark class hierarchies, strategy interfaces, rebalance engines, or generalized portfolio optimization.

## Compound plan

Likely reusable learning: passive references must share the same data snapshot and execution-cost convention as the active strategy, while baseline definitions must be fixed before observing comparison results. If confirmed, capture this under `docs/solutions/trading-research/`.

## Documentation and memory updates

- `experiments/EXP-0004-reference-baselines/` config and reviewed outputs.
- `experiments/README.md`.
- `.ai/current-state.md`.
- `docs/roadmap.md`.
- `README.md` if the new comparison workflow is user-relevant.
- `docs/solutions/README.md` and a research solution note if the Compound lesson is confirmed.
- Archive this plan under `docs/plans/completed/` before final review.

## Implementation plan

1. Add reusable equity-curve metrics without changing current portfolio metric semantics.
2. Implement deterministic cost-aware buy-and-hold sleeves and equal-weight aggregation.
3. Add EXP-0004 comparison runner, CLI, config, workflow, and tests.
4. Run Simplify and local/CI validation.
5. Run the real-data experiment and inspect the generated artifact.
6. Record reviewed results and interpretation without changing v1.
7. Perform Compound, update durable memory, archive the plan, and run formal review.
8. Merge only after `PASS`, green CI, and no unresolved threads.

## Review checklist

- [x] Scope and acceptance criteria are clear.
- [x] Design is consistent with project invariants.
- [x] Trading/research risks are addressed.
- [x] Test strategy is sufficient.
- [x] Simplification risks are identified.
- [x] Potential compound knowledge destinations are identified.
- [x] Required memory/documentation changes are identified.

## Definition of done

EXP-0004 is complete when the repository can reproduce a cost-aware passive comparison from one controlled data snapshot, reviewed real-data results are durably recorded with explicit retrospective/non-OOS framing, v1 remains unchanged, tests/lint/experiment CI are green, the final diff receives a formal `PASS`, and the PR is merged into `main`.
