# Design Plan — Prospective Holdout Evaluator

Status: Completed

## Problem

The prospective recorder preserves one canonical full provider snapshot per UTC observation date, but a normal rerun over the newest full-history snapshot would allow later yfinance revisions to rewrite earlier indicators, signals, and trade state. The finite historical backtester also liquidates positions at the end of its window, which cannot be repeated at every prospective observation.

## Completed design

The implementation separates durable evidence capture from read-only information-time replay:

- `PortfolioReplaySession` in `portfolio.py` owns one stateful daily event loop shared by historical backtests and prospective replay.
- Finite historical backtests preserve explicit terminal liquidation on each asset's final bar.
- Prospective replay carries cash, open positions, stops, pending signals, last prices, and closed trades forward without artificial terminal exits.
- `prospective_evaluator.py` accepts only recorded holdout archives and exposes no provider-download path.
- Archive `D` is verified against the registered protocol lock and contributes only newly observable market date `D-1`.
- The canonical archive chain begins on 2026-09-15 and must be contiguous by UTC observation date.
- Missing evidence stops replay before all later archives; no later revised snapshot is used to reconstruct the gap.
- Duplicate observation dates and pre-start archives fail closed.
- Frozen v1 symbols, benchmarks, risk parameters, signal/execution semantics, validation gate, and baseline asset-class cost values are enforced before replay.

## Outputs

The evaluator writes deterministic derived monitoring artifacts:

- `state.json`
- `daily-state.csv`
- `trades.csv`
- `notes.md`

Outputs explicitly record zero provider downloads, interim-monitoring-only status, no validation claim, no parameter tuning, processed evidence provenance, first missing observation if any, and processed-through state.

The source archives remain the canonical durable evidence. Evaluator output is derived state and can be regenerated from the archive chain.

## Validation

- `pytest -q`: PASS, including prospective evaluator/session tests.
- `ruff check src tests`: PASS.
- Existing synthetic portfolio execution/risk tests remain green after the event-loop refactor.
- Real-data EXP-0001, EXP-0002, EXP-0003, EXP-0004, EXP-0005, and EXP-0006 workflows all remain green on the refactored portfolio engine.
- Pending close signals wait through calendar dates without an asset bar and execute only on that asset's next available bar.
- Prospective synthetic archives prove deterministic repeated output, zero provider downloads, protocol/archive verification, stop-at-first-gap behavior, duplicate/pre-start rejection, and later provider revisions without retroactive replay.
- A synthetic valid v1 setup proves pending state created from the first canonical market date persists into the next observation and becomes an open position rather than an artificial terminal trade.

No real prospective observation exists yet; the first active archive is expected on 2026-09-15 for completed market date 2026-09-14.

## Simplify

PASS. The final implementation reuses one stateful portfolio event loop rather than creating a second backtester, event-sourcing framework, mutable evaluator database, provider fallback, or incremental cache. The evaluator deterministically reprocesses the small canonical archive chain from source evidence.

## Compound

Reusable methodology is recorded in `docs/solutions/trading-research/replay-prospective-evidence-by-information-time.md`: when historical source data can be revised, prospective evaluation must process evidence in capture order, update only the newly observable decision date, carry state forward, and treat missing observations as incomplete evidence rather than backfilling them from later snapshots.

## Research integrity

- Frozen v1 is unchanged.
- No prospective archive is generated or modified by the evaluator.
- No network/provider fallback exists in the evaluator.
- No interim validation verdict or tuning recommendation is produced.
- The preregistered validation gate remains both 2028-09-14 and 30 closed trades.
- The first genuine live test of this infrastructure begins only when the recorder creates the 2026-09-15 archive.

## Definition of done

Completed: the repository can replay frozen v1 deterministically from a contiguous verified prospective archive chain without network access or retroactive history replacement; finite historical backtests remain regression-equivalent; missing evidence stops replay; outputs are explicitly interim/non-validating/non-tuning; CLI/docs/memory/Compound are complete; final review and green final-head CI remain the merge gates.
