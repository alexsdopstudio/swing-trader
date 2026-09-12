# Design Plan

Status: Active

## Problem

Frozen v1 has a positive aggregate retrospective baseline, survives materially higher execution costs, fails temporal-stability thresholds, compares defensively with passive ownership, and is locally robust across a preregistered parameter neighborhood. All completed retrospective experiments still rely on the same narrow four-asset research subset: BTC-USD, SOL-USD, META, and NVDA.

The repository already contained a broader configured universe before this experiment: BTC-USD, ETH-USD, SOL-USD, META, NVDA, MSFT, AAPL, AMZN, GOOGL, AVGO, and TSLA. The next question is whether the frozen v1 result remains positive when the portfolio must compete across that full pre-existing configured universe, and whether realized profit contribution becomes meaningfully broader rather than remaining dominated by the original four symbols.

## Goals

- Run frozen v1 on the exact 11-asset list already present in `config/universe.yaml` before EXP-0006.
- Rerun the original EXP-0001 four-symbol subset on the same provider snapshot as a control.
- Keep strategy logic, portfolio risk controls, execution costs, dates, and benchmarks unchanged.
- Use one shared download cache across both portfolio paths so overlapping symbols see identical provider frames.
- Record portfolio metrics plus realized PnL/trade contribution by symbol and asset class.
- Predeclare breadth criteria before observing real-data results.
- Treat EXP-0006 as retrospective selection-bias evidence only; do not modify frozen v1 or the prospective holdout.

## Non-goals

- No changes to v1 score threshold, stop/trail ATR multiples, risk fraction, position caps, execution assumptions, indicator logic, or signal ordering.
- No search for a better universe, symbol subset, ranking rule, or portfolio size.
- No removal of underperforming symbols after results are observed.
- No point-in-time index-membership reconstruction in this PR.
- No claim that the current configured universe eliminates survivorship bias.
- No use of prospective holdout captures or post-2026-09-01 data.

## Preregistered universes

### Control subset

Exactly the EXP-0001 symbols, in the same order:

- BTC-USD
- SOL-USD
- META
- NVDA

### Expanded configured universe

Exactly every asset already listed in `config/universe.yaml`, preserving file order:

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

The seven added symbols are ETH-USD, MSFT, AAPL, AMZN, GOOGL, AVGO, and TSLA.

## Frozen evaluation specification

Both paths inherit EXP-0001 unchanged except for experiment metadata and the expanded path's symbol list:

- warm-up start: 2020-01-01;
- evaluation start: 2021-01-01;
- evaluation end exclusive: 2026-09-01;
- initial equity: 5,000;
- risk per trade: 0.5%;
- max aggregate open risk: 2%;
- max concurrent positions: 4;
- max position fraction: 25%;
- min score: 70;
- initial stop: 2.0 ATR;
- trailing stop: 2.5 ATR;
- unchanged baseline execution-cost config;
- unchanged QQQ equity and BTC crypto regime benchmarks.

## Preregistered breadth criteria

The expanded configured universe is considered to support broader retrospective breadth only if **all** of these hold:

1. Expanded portfolio is `joint_positive`: total return > 0, expectancy R > 0, and profit factor > 1.
2. The seven added symbols have positive aggregate realized net PnL.
3. At least 4 of the 11 expanded-universe symbols have positive realized net PnL.
4. At least 2 of the 7 added symbols have positive realized net PnL.
5. Positive realized net-PnL contributors include at least one equity and at least one crypto symbol.
6. The largest positive symbol contributor accounts for no more than 60% of the sum of positive symbol net PnL.
7. The four-symbol control remains joint-positive and reproduces the durable EXP-0001 record within the fixed provider-revision tolerances below.

Control reproduction tolerances:

- total return: 0.01 absolute;
- CAGR: 0.0025 absolute;
- max drawdown: 0.005 absolute;
- expectancy R: 0.10 absolute;
- trade count: 2 trades.

These thresholds must not be changed after observing EXP-0006 real-data results.

Passing all criteria would support the narrower statement that the frozen v1 historical result is not solely an artifact of the original four-symbol subset and that realized contribution broadens inside the pre-existing configured universe. It would **not** eliminate survivorship/selection bias because the 11 symbols are still current, high-profile survivors rather than a point-in-time investable-universe reconstruction.

## Relevant context

- `experiments/EXP-0001-baseline/config.yaml` defines the frozen strategy/risk/evaluation center.
- `config/universe.yaml` already defines all 11 assets; EXP-0006 must reject any different expanded list.
- EXP-0003 showed material temporal instability, which universe breadth cannot erase.
- EXP-0005 showed local parameter robustness but explicitly kept v1 frozen.
- `PROSPECTIVE-v1-holdout` is independent future evidence and must not feed this retrospective diagnostic.

## Proposed design

Add `src/swing_trader/universe_breadth.py` with:

- strict EXP-0006 config validation for experiment id, base config, reference results, exact control list, exact configured-universe expansion, and fixed breadth criteria;
- one `SharedDownloadCache` reused by the control and expanded run;
- generated per-path configs derived from EXP-0001, with only experiment metadata and the expanded symbol list allowed to differ;
- overlapping-source digest equality checks between paths;
- per-symbol trade aggregation from generated `trades.csv` files;
- asset-class aggregation using `config/universe.yaml`;
- explicit added-symbol contribution and concentration diagnostics;
- preregistered breadth pass/fail evaluation;
- strict JSON, symbol-comparison CSV, generated factual notes, and detailed control/expanded scenario artifacts.

Add `swing-universe-breadth` CLI and `.github/workflows/exp-0006.yml` to execute the controlled real-data diagnostic and upload artifacts.

## Trading and research implications

- Look-ahead: unchanged; completed-close signals execute no earlier than each asset's next available open.
- Portfolio competition: materially relevant. With 11 assets competing for four slots and a 2% risk budget, the full portfolio path must be rerun; per-symbol standalone tests would not answer the same question.
- Candidate ordering: unchanged deterministic score-descending/symbol-ascending ordering in the portfolio engine.
- Execution realism: unchanged baseline asset-class costs.
- Data control: overlapping control/expanded symbols must reuse identical provider frames from one shared cache.
- Selection bias: reduced relative to the handpicked four-symbol subset by using the complete pre-existing configured universe, but not eliminated because this is not point-in-time membership data.
- Evidence status: all history was previously observable; this remains retrospective evidence, not out-of-sample validation.

## Alternatives considered

- Add a freshly curated larger ticker list: rejected because choosing new symbols now would create a new post-hoc selection channel.
- Use current S&P/Nasdaq constituents: rejected for this step because present-day membership would still embed survivorship and would require a separate point-in-time membership methodology.
- Run each symbol independently: rejected because portfolio slot/risk competition is part of the actual v1 system.
- Compare only expanded portfolio headline return: rejected because a positive headline can still conceal profit concentration in one or two original symbols.

## Test and validation plan

- Unit test exact configured-universe lock and seven-symbol added set.
- Unit test generated configs can change only allowed experiment metadata/symbol fields; portfolio/risk/cost/evaluation settings remain frozen.
- Unit test shared downloader produces exactly 12 provider downloads across both paths: 11 assets plus unique QQQ benchmark.
- Unit test overlapping source digests must match.
- Unit tests for per-symbol aggregation, added-symbol PnL, positive-contributor counts, asset-class breadth, concentration, and preregistered criteria.
- `pytest -q` and `ruff check src tests`.
- Real-data EXP-0006 workflow with artifact inspection before durable interpretation.
- Formal final-diff review focused on universe lock, no post-hoc symbol selection, shared inputs, portfolio competition, contribution arithmetic, no look-ahead, and non-OOS framing.

## Simplification plan

Keep implementation to one strict two-path orchestrator around the existing experiment runner. Do not build a generic universe optimizer, constituent database, portfolio attribution framework, or ranking/search engine.

## Compound plan

Likely reusable lesson: breadth tests should use a universe fixed independently of the observed experiment outcome, rerun the shared-account portfolio rather than independent assets, and inspect contribution concentration instead of relying only on aggregate return. If confirmed, record under `docs/solutions/trading-research/`.

## Documentation and memory updates

- `experiments/EXP-0006-configured-universe-breadth/` config and reviewed outputs.
- `experiments/README.md`.
- `.ai/current-state.md`.
- `docs/roadmap.md`.
- `README.md` and `ARCHITECTURE.md` if the new CLI/workflow is user-relevant.
- `docs/solutions/README.md` and a research solution note if Compound produces reusable knowledge.
- Archive this plan under `docs/plans/completed/` before final review.

## Implementation plan

1. Add strict EXP-0006 config and universe-lock validation.
2. Implement shared-snapshot control/expanded orchestration and contribution diagnostics.
3. Add CLI, tests, and real-data workflow.
4. Run Simplify and validation.
5. Run and inspect EXP-0006 real-data artifact.
6. Record reviewed results without changing v1 or the prospective protocol.
7. Complete Compound and durable memory updates; archive this plan.
8. Perform formal final-diff review and merge only after `PASS` and green CI.

## Review checklist

- [x] Scope and acceptance criteria are clear.
- [x] Control and expanded universes are fixed before real-data results.
- [x] Breadth criteria are fixed before real-data results.
- [x] Design preserves frozen v1 and prospective holdout integrity.
- [x] Full shared-account reruns are required.
- [x] Shared-input and source-digest controls are explicit.
- [x] Simplification and Compound destinations are identified.

## Definition of done

EXP-0006 is complete when the repository can reproduce the four-symbol control and exact 11-symbol configured-universe path on one controlled provider snapshot, contribution breadth and preregistered criteria are durably recorded, no symbol subset is selected from the result, v1 and the prospective holdout remain unchanged, tests/lint/experiment CI are green, the final diff receives a formal `PASS`, and the PR is squash-merged into `main`.
