# Architecture

## Goal

Swing Trader is a research-first system for identifying and validating medium-term momentum/trend opportunities in crypto and US equities.

## Current flow

```text
Market data
   ↓
Indicators
   ↓
Swing Score / signal rules
   ↓
Deterministic risk sizing
   ↓
Backtest / scanner
   ↓
Metrics and experiment record
```

## Modules

- `data.py`: historical daily market data adapter.
- `indicators.py`: SMA, ROC, breakout levels, volume ratio and ATR.
- `scoring.py`: deterministic 0–100 Swing Score.
- `scanner.py`: universe scan and ranking.
- `risk.py`: position sizing, initial stop and trailing stop.
- `backtest.py`: current single-asset event-driven backtest.
- `context_builder.py`: builds a compact AI working-context snapshot from repository memory.

## AI boundary

AI may help with research, code generation, review, experiment interpretation and later catalyst/news analysis. It must not override position size, stops, portfolio-risk limits or other hard controls.

## Planned architecture

```text
                 Research / Catalyst Agent
                         ↓
Data → Features → Strategy → Portfolio Backtester → Experiment Store
                         ↓
                  Deterministic Risk
                         ↓
                   Paper Execution
```

The next major architectural milestone is a portfolio-aware backtester sharing one account across multiple assets.
