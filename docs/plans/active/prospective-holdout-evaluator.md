# Design Plan — Prospective Holdout Evaluator

Status: Active

## Problem

`PROSPECTIVE-v1-holdout` now has a byte-locked protocol and a current-date-only recorder that will preserve one canonical full provider snapshot per UTC observation date. The repository still lacks the read-only layer that can replay frozen v1 from those timestamped snapshots without replacing earlier evidence with later provider revisions.

A normal backtest over the newest full snapshot is not sufficient. yfinance can revise old adjusted history, so recomputing the entire holdout from the latest provider state would silently rewrite information that was actually observed on prior dates. A prospective replay must consume canonical archives chronologically and use each archive only for the newly completed day it makes observable.

The existing portfolio engine also liquidates positions at the end of a finite backtest. Re-running a one-day or growing-window backtest for each snapshot would therefore create artificial daily/end-window exits. The evaluator needs persistent trade state while preserving the exact event ordering and risk semantics already tested in `portfolio.py`.

## Goals

- Refactor the portfolio event loop into a reusable stateful daily session without changing existing backtest semantics or results.
- Keep `backtest_portfolio` behavior backward-compatible, including terminal liquidation for finite retrospective tests.
- Add a read-only prospective evaluator that accepts only recorded holdout archives; it must never query yfinance or any other live provider.
- Verify every archive end-to-end against the registered protocol lock before use.
- Process archives in canonical observation-date order and use only the bar dated `observation_date - 1` from that archive.
- Require a contiguous daily archive chain beginning 2026-09-15. Stop at the first missing canonical observation rather than reconstructing it from a later snapshot.
- Replay frozen v1 using the exact protocol strategy/risk/execution specification and the repository's existing score/regime/risk/execution code.
- Preserve pending next-asset-bar entries across equity weekends/holidays.
- Produce deterministic operational state: processed evidence chain, open positions, pending signals, closed-trade journal, cash/equity/exposure history, and provenance.
- Mark all output as interim/read-only, not a validation claim and not an input to tuning.

## Non-goals

- No strategy/risk/parameter changes.
- No historical backfill of missed prospective observation dates.
- No provider download or latest-data fallback.
- No broker/paper order submission.
- No automatic parameter selection, alert-driven tuning, or model feedback.
- No final validation decision before the preregistered 2028-09-14 + 30-closed-trade gate.
- No requirement to publish evaluator output durably yet; captured source evidence remains the canonical durable input.

## Information-time model

The recorder's canonical observation `D` has an exclusive data cutoff of `D` and may contain completed daily bars dated no later than `D-1`.

The evaluator therefore processes completed market date `D-1` from archive `D`:

1. positions and pending signals carried from earlier canonical observations enter the day;
2. gap-through-stop handling occurs at that day's asset open;
3. pending signals from earlier closes may execute only on the first later bar actually present for that asset;
4. intraday stops use the stop known at the open;
5. completed close data may update trailing stops for future bars;
6. equity/exposure state is recorded;
7. new signals are calculated from the completed close and become pending for a later asset bar.

This is intentionally a read-only after-the-day replay. It reconstructs what frozen v1 would have done using evidence preserved prospectively; it is not a live execution engine.

## Missing-observation rule

Canonical observation dates are daily UTC dates, including weekends. The first active archive is expected on 2026-09-15 for market date 2026-09-14.

If archive `D` is missing, the evaluator must stop before processing any later archive. Later provider snapshots may contain the missing day's OHLCV, but using them would be retrospective backfill under a revised provider state. Output must record the first missing observation date and `evidence_complete=false`.

Duplicate observation dates or conflicting archives for the same date are errors rather than a choice between versions.

## Portfolio refactor

Add a reusable daily session to `portfolio.py` around the existing event ordering.

Proposed public objects:

- `PortfolioReplayBar`: symbol, completed bar including indicators, score, regime, and asset class;
- `PortfolioReplaySession`: initialized with `PortfolioBacktestConfig`, carrying cash, open positions, pending signals, last prices, closed trades, and daily curves;
- `process_date(date, bars, terminal_symbols=...)`: process exactly one calendar date using the existing open/intraday/close ordering;
- read-only snapshots for open positions and pending signals.

Pending entries will no longer need a precomputed future execution date. A signal becomes eligible on the first later date that contains a bar for that asset. In finite historical backtests this is equivalent to the current precomputed-next-index behavior and is easier to use prospectively.

`backtest_portfolio` will prepare its historical assets, feed one date at a time into the session, pass each asset as terminal on its own final available date, and return the same `PortfolioBacktestResult` shape. Existing tests plus a direct regression comparison will guard semantic equivalence.

## Prospective evaluator design

Add `src/swing_trader/prospective_evaluator.py` with:

- archive discovery and strict filename/date uniqueness;
- `verify_snapshot_archive` calls bound to the registered protocol lock;
- exact protocol universe/risk/cost validation;
- contiguous-chain detection from the first expected active date;
- source CSV extraction from each verified archive;
- indicators, historical score and regime calculation inside that archive only;
- construction of replay bars only for `observation_date - 1`;
- stateful processing through `PortfolioReplaySession`;
- deterministic JSON state, trades CSV, daily state CSV, and factual notes;
- no aggregate validation verdict or tuning recommendation.

Add `swing-holdout-evaluate` CLI taking an archive directory plus protocol/lock/output paths. No network/provider arguments are exposed.

## Frozen configuration

The evaluator must verify and use protocol values:

- symbols: BTC-USD, SOL-USD, META, NVDA;
- equity benchmark: QQQ;
- crypto benchmark: BTC-USD;
- evaluation start: 2026-09-14;
- initial equity: 5,000;
- risk fraction: 0.5%;
- max open risk: 2%;
- max positions: 4;
- max position fraction: 25%;
- min score: 70;
- initial stop: 2.0 ATR;
- trailing stop: 2.5 ATR;
- baseline execution costs from the locked protocol's execution-cost config;
- completed-close signals and next-asset-bar execution.

Any incompatible protocol change must fail rather than be interpreted dynamically as a new v1.

## Output research-integrity fields

Evaluator output will explicitly record:

- `interim_monitoring_only: true`;
- `validation_claim: false`;
- `parameter_tuning_allowed: false`;
- `provider_downloads: 0`;
- `evidence_complete` and first gap if any;
- protocol/source/archive digests used;
- processed-through market and observation dates;
- closed-trade count as an operational fact, without declaring the validation gate passed.

## Tests and validation

- Regression suite proves existing portfolio backtests remain unchanged after the session refactor.
- Synthetic session test proves signal-at-close executes only on the next available asset bar and survives missing calendar dates.
- Synthetic session tests cover gap stops, intraday stops, trailing-stop timing, position/risk caps, and terminal liquidation.
- Synthetic archive builder creates valid content-addressed holdout archives without network access.
- Evaluator rejects tampered archives, wrong protocol bindings, duplicate dates, and dates before the expected first active observation.
- Evaluator stops at the first missing canonical date and never consumes later archives.
- Evaluator processes only `observation_date - 1`; revised earlier rows in later archives must not change already-processed decisions.
- Weekend test proves crypto advances daily while equity pending entries wait for the next equity bar.
- Provider download count is structurally zero.
- Deterministic repeated evaluation over the same archive set produces byte-identical JSON/CSV outputs.
- `pytest -q` and `ruff check src tests`.
- Formal diff review focuses on information time, state continuity, absence of hidden backfill/provider access, frozen protocol integrity, and regression equivalence with the historical engine.

## Simplification plan

Reuse one stateful event-loop implementation for both retrospective and prospective paths. Do not create a second portfolio engine, database, event-sourcing framework, broker abstraction, or incremental cache. Reprocessing the small canonical archive chain deterministically is preferable to persisting mutable evaluator state.

## Compound plan

Likely reusable lesson: prospective evaluation over revisable full-history providers must replay the evidence *as captured over time*, not rerun the strategy on the newest revised history. Missing evidence must make the replay incomplete rather than trigger retrospective reconstruction. If confirmed, capture under `docs/solutions/trading-research/`.

## Documentation and memory updates

- `experiments/PROSPECTIVE-v1-holdout/README.md`.
- `ARCHITECTURE.md`.
- `.ai/current-state.md`.
- `docs/roadmap.md`.
- root `README.md` for the evaluator CLI.
- `docs/solutions/README.md` and reusable research note if Compound confirms the lesson.
- Archive this plan under `docs/plans/completed/` before final review.

## Implementation plan

1. Refactor `portfolio.py` into a reusable daily replay session while preserving historical behavior.
2. Add regression/stateful-session tests.
3. Implement strict read-only archive-chain evaluator and CLI.
4. Add synthetic archive/evaluator tests, including gaps and revisions.
5. Run Simplify and validation.
6. Update prospective protocol documentation and durable project memory.
7. Complete Compound; archive this plan.
8. Perform formal final-diff review and squash merge only after `PASS` and green CI.

## Review checklist

- [x] Information-time boundary is explicit.
- [x] Missing evidence fails closed instead of backfilling.
- [x] Evaluator is structurally read-only over captured archives.
- [x] Frozen v1/risk/execution configuration is explicit.
- [x] Historical engine regression equivalence is required.
- [x] Prospective state persists across daily evidence without artificial end-of-test liquidation.
- [x] Simplification and Compound destinations are identified.

## Definition of done

The evaluator is complete when frozen v1 can be replayed deterministically from a contiguous sequence of verified prospective archives without network access or retroactive history replacement, existing retrospective backtest behavior remains unchanged, missing canonical observations stop the replay, output is explicitly interim/non-validating/non-tuning, tests/lint are green, project memory is current, the final diff receives `PASS`, and the PR is squash-merged into `main`.
