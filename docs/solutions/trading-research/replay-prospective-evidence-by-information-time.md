# Replay prospective evidence by information time

## Problem

A forward-data provider can revise previously published daily history. If a prospective evaluator simply reruns a strategy over the newest full-history snapshot, old indicators, signals, fills, and trade state may silently change. The result is no longer a faithful replay of what was observable at each prior decision boundary.

Growing-window backtests can create another distortion when the backtest engine liquidates open positions at the end of every evaluated window. Repeating that process daily turns an operational replay into a sequence of artificial terminal exits.

## Solution

Treat each captured provider snapshot as evidence for one new information boundary, not as permission to rewrite the whole past.

1. Preserve a canonical archive for every observation date before evaluation.
2. Verify the archive and protocol binding before using it.
3. Process only the newly observable market date from that archive.
4. Carry cash, positions, pending next-asset-bar entries, stops, and prior decisions forward in a stateful deterministic session.
5. Recompute rolling features for the new market date using the provider state actually visible in that archive, while never reprocessing earlier market dates.
6. If a canonical observation is missing, stop the replay. Do not reconstruct the missing decision from a later revised snapshot.
7. Keep finite-backtest terminal liquidation explicit and separate from ongoing prospective replay.

## Why this works

Later provider revisions may legitimately affect indicators calculated for a *new* decision date because those revisions are visible at that later information boundary. They must not retroactively change decisions already processed from earlier captured evidence.

This approach makes the evaluator deterministic from the archive chain, preserves next-open and stop ordering across observations, and keeps missing evidence visible instead of disguising it as prospective data.

## Tests and checks

- The historical backtester and stateful session must remain regression-equivalent on existing unit and real-data experiment suites.
- A signal generated on a close must remain pending through calendar dates with no bar and execute only on the next available asset bar.
- Later archives may revise earlier rows, but previously processed state must not be recalculated.
- Duplicate observation dates are errors.
- A missing canonical observation stops processing of all later archives.
- The evaluator must expose no provider-download fallback.
- Repeated replay of the same archive chain must produce byte-identical derived state outputs.

## Applicability boundary

This pattern is appropriate when full-history source snapshots can change after publication and the research question depends on what was knowable at each historical observation time. It does not turn interim forward monitoring into validation, and it does not replace a preregistered validation horizon/trade-count gate.

## Project references

- `src/swing_trader/prospective_recorder.py`
- `src/swing_trader/prospective_evaluator.py`
- `src/swing_trader/portfolio.py`
- `experiments/PROSPECTIVE-v1-holdout/`
