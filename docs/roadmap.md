# Roadmap

## Now

- Build held-out / walk-forward evaluation for the frozen v1 strategy.
- Preserve explicit warm-up, training/research, and held-out evaluation windows.
- Compare held-out results with the exploratory EXP-0001 / EXP-0002 evidence without tuning v1 first.
- Add simple passive/reference baselines to make opportunity cost visible.

## Next

- Parameter-neighborhood robustness sweeps after held-out evidence is recorded.
- Broader-universe testing to reduce survivor and selection bias.
- Persistent experiment registry/index automation.
- Daily scan persistence.

## Completed research infrastructure

- Shared-account portfolio backtester.
- Portfolio equity curve, exposure curve, and trade ledger.
- CAGR, max drawdown, Sharpe, Sortino, profit factor, expectancy in R, and exposure metrics.
- Commission, spread, and slippage modeling in sizing, cash, risk, and PnL.
- Reproducible real-data experiment runner with input/runtime provenance.
- EXP-0001 cost-aware exploratory baseline.
- EXP-0002 execution-cost sensitivity using one shared market-data snapshot.

## Later

- AI catalyst/research agent for earnings, filings, news and crypto-specific events.
- Paper-trading integration.
- Semantic retrieval over research memory if repository scale warrants it.
