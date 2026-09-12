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
- `metrics.py`: portfolio performance and trade statistics.
- `backtest_cli.py`: cost-aware historical portfolio research entry point.
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

## Current architectural milestone

The shared-account, cost-aware portfolio research engine is in place. The next milestone is reproducible real-data experimentation, followed by walk-forward/out-of-sample evaluation and execution-cost sensitivity analysis before paper execution is considered.
