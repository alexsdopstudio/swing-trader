# Order Backtest Events by Information Time

## Problem

A daily backtest can accidentally use information from the end of a bar to affect fills or stops that are assumed to have happened earlier in that same bar. In a multi-asset portfolio this becomes harder to notice because entries, exits, and signals from different calendars share one account event loop.

## Symptoms

- A signal calculated from a close is filled at that same close or earlier.
- A trailing stop calculated from today's close is allowed to stop the position using today's low.
- A stop gap is filled at the stale stop price even though the market opened below it.
- Crypto weekends or equity holidays are treated as if every asset had the same next session.
- Reordering code inside the event loop changes historical performance unexpectedly.

## Root cause

Calendar order alone is not enough to model execution. Events inside each bar have an information order: open information exists before the intraday low/high and before the close, while indicators based on the completed close only exist after the bar is finished.

## Reusable solution

Model each portfolio date in explicit information-time order:

1. Process existing positions that gap through a previously known stop at the current open.
2. Execute signals created from an earlier completed close at the asset's next available open.
3. Apply stops that were known at the open to the current bar's intraday range. The initial stop is therefore active on the entry bar.
4. After the bar is complete, update close-derived state such as highest close and trailing stop.
5. Mark portfolio equity at the completed close.
6. Generate new signals from the completed close and schedule them only for that asset's next available bar.

If a long position opens below its existing stop, fill the stop at the open rather than the stale stop level. A trailing stop calculated from a close becomes effective only on a later bar.

For mixed calendars, define "next" per asset, not per global portfolio date.

## When this applies

- daily or higher-timeframe bar backtests;
- multi-asset portfolios with shared capital;
- next-session execution models;
- ATR/trailing stops computed from completed bars;
- assets with different calendars such as crypto and US equities.

## When this does not apply

A true intraday event/tick simulator may have enough timestamped information to model a more detailed sequence. In that case, use actual event timestamps rather than forcing this daily-bar ordering.

## Tests and checks

Require tests that verify:

- signal date and entry date are different when next-open execution is required;
- the initial stop can trigger on the entry bar;
- a close-derived trailing stop cannot trigger against the same bar's low;
- a gap through a stop fills at the open;
- each asset uses its own next available bar across weekends/holidays;
- simultaneous portfolio entries use deterministic ordering when capital is constrained.

During review, inspect event-loop order directly. A green return metric does not prove execution timing is valid.

## References

- `docs/decisions/ADR-002-next-open-execution.md`
- `docs/domain/risk-model.md`
- `src/swing_trader/portfolio.py`
- `tests/test_portfolio.py`
- PR #3 — portfolio backtester
