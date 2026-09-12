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
- `portfolio.py`: shared-account multi-asset event loop, cash/risk constraints and realized trade ledger.
- `metrics.py`: reusable equity-curve metrics plus portfolio performance and trade statistics.
- `experiment.py`: reproducible frozen-strategy experiment orchestration and provenance.
- `cost_sensitivity.py`: controlled execution-cost sensitivity on shared inputs.
- `temporal_stability.py`: retrospective calendar-fold diagnostics on one frozen snapshot.
- `reference_baselines.py`: deterministic cost-aware passive buy-and-hold references.
- `reference_comparison.py`: controlled active-vs-passive orchestration on one shared snapshot.
- `parameter_neighborhood.py`: preregistered local parameter-surface diagnostics with full-path scenario reruns and no winner selection.
- `context_builder.py`: compact AI working-context snapshot from repository memory.

## Execution and risk boundary

Strategy signals do not own sizing or fill assumptions. The portfolio engine combines deterministic risk policy with an explicit asset-class execution-cost model.

For long trades:

1. a completed close creates a signal;
2. the signal can execute only at that asset's next available open;
3. `execution.py` converts the market-reference open into an adverse buy fill and commission;
4. `risk.py` sizes from cost-adjusted loss to the technical initial stop;
5. `portfolio.py` enforces shared cash, position count, notional and aggregate open-risk limits;
6. stop/end-of-test references are converted into adverse sell fills and commissions;
7. the ledger records gross/net results and execution costs.

The technical stop remains a market-reference trigger. Execution cost changes realized fill, cash flow and risk, not the chronological information available to the strategy.

Passive references deliberately do not inherit v1 sizing/stops because they answer an opportunity-cost question. They still share evaluation dates, provider snapshot, and execution-cost conventions with the active strategy.

Parameter-neighborhood scenarios deliberately rerun the full portfolio path when stop/trail/entry threshold changes can affect sizing, exits, cash, open risk, and later opportunities. The diagnostic reports the surface and preregistered criteria; it does not select a replacement strategy.

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

Retrospective diagnostics can challenge the frozen strategy, but they do not become unseen evidence. Genuine validation remains separated into preregistered prospective protocols.

## Current architectural milestone

The research engine now has reproducible baseline, cost-sensitivity, temporal-stability, passive/reference, and parameter-neighborhood workflows. The next retrospective diagnostic is broader-universe testing to reduce selection/survivorship bias. In parallel, the preregistered prospective holdout needs a provenance-preserving forward recording layer before paper execution is considered.
