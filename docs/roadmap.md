# Roadmap

## Now

- Keep v1 frozen for `PROSPECTIVE-v1-holdout`, which begins 2026-09-14.
- Let the provenance-preserving forward recorder begin with the first active 2026-09-15 UTC capture; do not backfill missed prospective dates.
- Preregister and run broader-universe testing to reduce survivor and selection bias.
- Preserve and verify provenance for every prospective observation and provider revision.

## Next

- Build a read-only prospective holdout evaluator/trade-state replay on top of captured evidence without feeding interim performance into v1 tuning.
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
- EXP-0005 preregistered 27-scenario parameter-neighborhood diagnostic; all preregistered local-robustness criteria passed without selecting a replacement parameter set.
- Preregistered `PROSPECTIVE-v1-holdout` protocol separating future unseen evidence from retrospective diagnostics.
- Byte-locked, current-date-only prospective provider-state recorder with complete snapshots, deterministic archive/source digests, yearly durable release publication, and explicit no-backfill semantics.

## Later

- AI catalyst/research agent for earnings, filings, news and crypto-specific events.
- Paper-trading broker integration after the forward recording/evaluation layer is trustworthy.
- Semantic retrieval over research memory if repository scale warrants it.
