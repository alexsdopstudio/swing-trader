# Architecture

## Goal

Swing Trader is a research-first system for identifying and validating medium-term momentum/trend opportunities in crypto and US equities.

## Current flow

```text
Market data
   ↓
Indicators
   ↓
Historical Swing Score / signal rules
   ↓
Portfolio event loop
   ↓
Deterministic risk + execution costs
   ↓
Shared cash / positions / trade ledger
   ↓
Metrics and experiment record
```

The scanner uses the same indicator and scoring concepts for the latest bar, while historical research uses the portfolio backtester with explicit next-open execution semantics.

## Modules

- `data.py`: historical daily market data adapter.
- `indicators.py`: SMA, ROC, breakout levels, volume ratio and ATR.
- `scoring.py`: deterministic 0–100 Swing Score for the latest bar.
- `historical.py`: historical score and market-regime series without future data.
- `scanner.py`: universe scan and ranking.
- `risk.py`: deterministic position sizing, initial stop and trailing stop helpers.
- `execution.py`: immutable commission, spread and slippage assumptions plus cost-config loading.
- `backtest.py`: legacy/minimal single-asset event-driven backtest.
- `portfolio.py`: shared-account multi-asset event loop plus reusable stateful daily replay session, cash/risk constraints, and realized trade ledger.
- `metrics.py`: reusable equity-curve metrics plus portfolio performance and trade statistics.
- `backtest_cli.py`: cost-aware historical portfolio research entry point.
- `reference_baselines.py`: deterministic cost-aware passive buy-and-hold references.
- `reference_comparison.py`: controlled active-vs-passive experiment orchestration on one shared snapshot.
- `parameter_neighborhood.py`: preregistered local score/stop/trail robustness diagnostics with full-path reruns on shared inputs and no winner selection.
- `universe_breadth.py`: controlled same-snapshot subset-vs-configured-universe full-path comparison with realized symbol/asset-class contribution and concentration diagnostics.
- `prospective_recorder.py`: byte-locked, current-date-only forward provider-state capture with exclusive cutoffs, complete source snapshots, and deterministic archive verification.
- `prospective_evaluator.py`: read-only information-time replay of the frozen holdout from verified canonical archives, with state continuity and fail-closed gap handling.
- `experiment_registry.py`: deterministic derived index and integrity validation for durable historical experiment records and prospective protocol locks.
- `context_builder.py`: builds a compact AI working-context snapshot from repository memory.

## Execution and risk boundary

Strategy signals do not own sizing or fill assumptions. The portfolio engine combines deterministic risk policy with an explicit asset-class execution-cost model.

For long trades:

1. a completed close creates a signal;
2. the signal can execute only at that asset's next available open;
3. `execution.py` converts the market-reference open into an adverse buy fill and commission;
4. `risk.py` sizes from cost-adjusted loss to the technical initial stop;
5. `portfolio.py` enforces shared cash, position count, notional and aggregate open-risk limits;
6. stop/end-of-test market-reference exits are converted into adverse sell fills and commissions;
7. the trade ledger records gross and net results plus execution costs.

The technical stop remains a market-reference trigger. Execution cost changes the realized fill, cash flow and risk, not the chronological information available to the strategy.

The same stateful daily portfolio session is used by finite historical backtests and prospective replay. Historical backtests explicitly mark each asset's final bar for terminal liquidation. Prospective replay does not: open positions, pending signals, stops, cash, and last prices carry forward to later canonical observations.

Passive references deliberately do not inherit v1 sizing/stops: they answer an opportunity-cost question. They must still share evaluation dates, provider snapshot, and execution-cost conventions with the active strategy so the comparison is controlled.

Parameter-neighborhood scenarios rerun the full portfolio path because score thresholds and ATR stop/trail distances can alter entries, sizing, exits, cash, open risk, and later opportunities. The diagnostic evaluates a preregistered surface and never promotes the historical winner into frozen v1.

Universe-breadth paths also rerun the full shared-account portfolio because added assets compete for cash, open-risk budget, and position slots. A broader-universe conclusion is evaluated through realized symbol/asset-class contribution and concentration, not headline return alone. Using a fixed pre-existing current-survivor universe reduces dependence on a narrow subset but is not equivalent to point-in-time membership data.

## Research-memory integrity boundary

`experiments/README.md`, each experiment's reviewed `notes.md`/`results.json`, and prospective protocol files remain the canonical durable research sources. `experiments/registry.json` is deliberately derived from them; it contains only mechanically recoverable identity, content digests, provenance, and protocol-lock facts.

`experiment_registry.py` validates directory/config/result identity, required durable files, normalized existing provenance, README coverage, and prospective protocol byte locks before rendering deterministic JSON. It adds no generation timestamp and does not infer research conclusions that are absent from canonical result files.

The generated registry is versioned for review and fast discovery, but it is not a second editable research schema. CI regenerates it and fails when the committed bytes differ, so changes to canonical experiment/protocol memory must update the derived index in the same PR.

## Prospective evidence boundary

Prospective evidence capture is deliberately separate from strategy evaluation. `prospective_recorder.py` records the complete normalized provider state visible before the current UTC observation cutoff and produces no signals, fills, PnL, parameter choices, or validation outcome.

`PROSPECTIVE-v1-holdout` is byte-locked before the forward record begins. Production capture derives its observation date from the current UTC clock; it cannot label a later download as an earlier prospective observation. Missing capture dates therefore remain gaps.

Each active date is stored as a digest-named full snapshot archive. The scheduled workflow publishes one asset per canonical date to a yearly GitHub Release and skips an existing date instead of replacing it. This preserves provider revisions without adding generated daily data commits to `main`.

`prospective_evaluator.py` consumes those verified archives chronologically. Archive `D` contributes only newly observable market date `D-1`; earlier dates are never reprocessed from a later revised provider snapshot. A missing canonical archive stops replay before all later evidence rather than triggering retrospective reconstruction.

The evaluator has no provider fallback and uses the same deterministic portfolio/risk/execution event loop as retrospective research. Its outputs are derived interim monitoring state, not durable source evidence and not a validation verdict. Interim replay cannot feed tuning; the preregistered 2028-09-14 plus 30-closed-trade gate remains authoritative.

## AI boundary

AI may help with research, code generation, review, experiment interpretation and later catalyst/news analysis. It must not override position size, stops, execution assumptions, portfolio-risk limits or other hard controls.

## Research architecture

```text
                  Research / Catalyst Agent
                          ↓
Data → Features → Strategy → Portfolio Backtester → Experiment Store
                          ↓            ↓
                  Deterministic Risk  Execution Costs
                          ↓            ↓
                       Shared Portfolio
                          ↓
                    Paper Execution
```

Retrospective diagnostics and passive references can challenge the frozen strategy, but they do not become unseen evidence. Genuine validation remains separated into preregistered prospective protocols, timestamped forward provider snapshots, and read-only information-time replay.

## Current architectural milestone

The research engine now has reproducible retrospective baseline, cost-sensitivity, temporal-stability, passive/reference, parameter-neighborhood, and configured-universe breadth workflows plus provenance-preserving prospective capture, read-only replay infrastructure, and a deterministic derived experiment/protocol registry. The immediate operational milestone is the first active 2026-09-15 recorder observation and continued gap-free evidence capture. Any stronger historical survivorship study should use preregistered point-in-time universe membership rather than adding further present-day survivors.
