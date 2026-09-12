# Roadmap

## Now

- Keep v1 frozen for `PROSPECTIVE-v1-holdout`, beginning 2026-09-14.
- Build a provenance-preserving forward holdout recorder; interim results must not feed v1 tuning.
- Preregister and run broader-universe testing to reduce survivor and selection bias.
- Preserve source/provider revision provenance for every prospective observation.

## Next

- Persistent experiment registry/index automation.
- Daily scan persistence built on the forward observation store.
- Additional robustness diagnostics only when they answer a new preregistered question rather than mine completed historical surfaces.

## Prospective validation gate

The first true v1 holdout cannot support validation claims until both conditions are met:

- minimum observation end: 2028-09-14;
- minimum closed trades: 30.

Interim monitoring is allowed. Interim performance must not be used to tune v1.

## Completed research infrastructure

- Shared-account, cost-aware portfolio backtester and portfolio/trade metrics.
- Reproducible real-data experiment runner with input/runtime provenance.
- EXP-0001 cost-aware exploratory baseline.
- EXP-0002 execution-cost sensitivity using one shared market-data snapshot.
- EXP-0003 retrospective temporal-stability diagnostic across six independent calendar folds.
- EXP-0004 cost-aware passive/reference comparison on one shared snapshot.
- EXP-0005 preregistered 27-scenario parameter-neighborhood diagnostic; all preregistered local-robustness criteria passed without selecting a replacement parameter set.
- Preregistered `PROSPECTIVE-v1-holdout` protocol separating future unseen evidence from retrospective diagnostics.

## Later

- AI catalyst/research agent for earnings, filings, news and crypto-specific events.
- Paper-trading broker integration only after the forward recording layer is trustworthy.
- Semantic retrieval over research memory if repository scale warrants it.
