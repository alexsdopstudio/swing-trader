# Roadmap

## Now

- Keep v1 frozen for `PROSPECTIVE-v1-holdout`, which begins 2026-09-14.
- Run parameter-neighborhood robustness sweeps without changing the frozen v1 specification or selecting a new v1 parameter set from retrospective results.
- Build forward paper/holdout recording without allowing interim v1 tuning.
- Preserve provenance for every prospective observation and provider revision.

## Next

- Broader-universe testing to reduce survivor and selection bias.
- Persistent experiment registry/index automation.
- Daily scan persistence.

## Prospective validation gate

The first true v1 holdout is preregistered, but it cannot support validation claims until both conditions are met:

- minimum observation end: 2028-09-14;
- minimum closed trades: 30.

Interim monitoring is allowed. Interim performance must not be used to tune v1.

## Completed research infrastructure

- Shared-account portfolio backtester.
- Portfolio equity curve, exposure curve, and trade ledger.
- CAGR, max drawdown, Sharpe, Sortino, profit factor, expectancy in R, and exposure metrics.
- Commission, spread, and slippage modeling in sizing, cash, risk, and PnL.
- Reproducible real-data experiment runner with input/runtime provenance.
- EXP-0001 cost-aware exploratory baseline.
- EXP-0002 execution-cost sensitivity using one shared market-data snapshot.
- EXP-0003 retrospective temporal-stability diagnostic using six independent calendar folds.
- EXP-0004 cost-aware passive/reference comparison using per-symbol and initial equal-weight buy-and-hold baselines on one shared snapshot.
- Preregistered `PROSPECTIVE-v1-holdout` protocol separating future unseen evidence from retrospective diagnostics.

## Later

- AI catalyst/research agent for earnings, filings, news and crypto-specific events.
- Paper-trading broker integration after the forward recording layer is trustworthy.
- Semantic retrieval over research memory if repository scale warrants it.
