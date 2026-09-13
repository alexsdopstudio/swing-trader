# Roadmap

## Now

- Keep v1 frozen for `PROSPECTIVE-v1-holdout`, which begins 2026-09-14.
- Let the provenance-preserving forward recorder begin with the first active 2026-09-15 UTC capture; do not backfill missed prospective dates.
- Replay captured evidence only through the read-only information-time evaluator; interim state/trades must not feed v1 tuning.
- Preserve and verify provenance for every prospective observation and provider revision.
- Preserve one current-date operational scanner observation without treating it as holdout evidence.
- Keep external literature, future news observations, curated interpretation, project experiments, and generated indexes in explicit evidence classes.
- Build the approval-only personal paper-operations layer: daily brief, human decision records, deterministic ticket sizing/stops, and append-only operational ledger.

## Next

- Publish and monitor the read-only project dashboard through GitHub Pages once the repository is configured to use GitHub Actions for Pages.
- After paper-operations integrity is demonstrated, add a manual-live journal that records user-reported fills without transmitting broker orders or changing frozen v1.
- If further historical universe work is justified, preregister a point-in-time membership/survivorship methodology rather than selecting additional current survivors.

## Prospective validation gate

The first true v1 holdout is preregistered, but it cannot support validation claims until both conditions are met:

- minimum observation end: 2028-09-14;
- minimum closed trades: 30.

Interim monitoring is allowed. Interim performance must not be used to tune v1.

## Completed research infrastructure

- Shared-account portfolio backtester.
- Stateful daily portfolio replay session shared by finite historical backtests and ongoing prospective replay.
- Portfolio equity curve, exposure curve, and trade ledger.
- CAGR, max drawdown, Sharpe, Sortino, profit factor, expectancy in R, and exposure metrics.
- Commission, spread, and slippage modeling in sizing, cash, risk, and PnL.
- Reproducible real-data experiment runner with input/runtime provenance.
- EXP-0001 cost-aware exploratory baseline.
- EXP-0002 execution-cost sensitivity using one shared market-data snapshot.
- EXP-0003 retrospective temporal-stability diagnostic using six independent calendar folds.
- EXP-0004 cost-aware passive/reference comparison using per-symbol and initial equal-weight buy-and-hold baselines on one shared snapshot.
- EXP-0005 preregistered 27-scenario parameter-neighborhood diagnostic; all preregistered local-robustness criteria passed without selecting a replacement parameter set.
- EXP-0006 configured-universe breadth diagnostic using the complete pre-existing 11-asset universe and a same-snapshot four-symbol control; all preregistered breadth criteria passed without selecting a preferred subset.
- Preregistered `PROSPECTIVE-v1-holdout` protocol separating future unseen evidence from retrospective diagnostics.
- Byte-locked, current-date-only prospective provider-state recorder with complete snapshots, deterministic archive/source digests, yearly durable release publication, and explicit no-backfill semantics.
- Read-only prospective evaluator that verifies canonical archives, processes only each newly observable market date, preserves portfolio state across observations, performs zero provider downloads, and stops at the first evidence gap.
- Deterministic machine-generated experiment/protocol registry with canonical-file digests, normalized existing provenance, prospective protocol-lock validation, and CI stale-state enforcement.
- Current-date-only daily scanner history with exact captured config/source state, deterministic outputs, archive verification, unique-symbol downloads, and append-only-by-convention yearly release publication.
- Source-governed knowledge system with nine initial authoritative durable sources, five curated interpretation notes, a validated time-bounded `NEWS-*` observation schema, deterministic source/news/note registry, and dedicated stale-state/schema CI.
- Explicit agent knowledge evidence classes separating durable references, news observations, curated interpretation, project experiments, operational observations, and generated indexes.
- Read-only static project dashboard with a deterministic canonical snapshot, offline-safe research status, optional public GitHub operational enrichment, PR build artifacts, and GitHub Pages deployment workflow.

## Later

- AI catalyst/research agent for earnings, filings, news and crypto-specific events writing validated `NEWS-*` records rather than an independent ad-hoc store.
- Broker connectivity only after a separately reviewed design establishes user authorization, broker-specific order semantics, risk thresholds, credential handling, and failure controls.
- Semantic/vector retrieval over knowledge/research memory only if repository scale warrants it; retrieval must remain derived from canonical evidence-class-aware records.
