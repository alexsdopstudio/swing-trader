# Free market-intelligence and catalyst discovery

Status: Design approved for implementation planning; this PR establishes the product goal only.

## Problem

Swing Trader currently has a technical market-data workflow and a curated knowledge/news schema, but no broad operational collection of public information or catalyst detection. Important price moves can be driven by company disclosures, government/regulatory decisions, macroeconomic releases, industry developments, and public attention shifts. A price-only scanner can miss the event context and may identify a move only after much of the reaction has occurred.

The product direction must therefore expand from a technical swing scanner into a market-intelligence and catalyst-discovery decision-support system. The first implementation phase should prioritize sources that are free to access and legally reusable, without equating maximum ingestion volume with useful coverage.

## Goals

- Discover, verify, rank, and evaluate potentially actionable catalysts for US equities and crypto.
- Build broad, extensible coverage of high-quality public information, prioritizing free official APIs, public datasets, company disclosures, reputable news, RSS/Atom, and permitted public social/community interfaces.
- Treat source reliability, provenance, information time, licensing, independence, timeliness, and incremental information value as first-class source-selection criteria.
- Detect events and changes in attention, not merely positive/negative sentiment.
- Corroborate social/community signals against independent sources and observable market behavior.
- Produce explainable, timestamp-correct evidence for human review and later statistical evaluation.
- Preserve existing strategy v1 and its prospective holdout unchanged.

## Non-goals

- Guaranteeing profitable trades or implying that more data automatically creates an edge.
- Scraping private, access-controlled, or prohibited content; bypassing paywalls, API limits, authentication, or platform terms.
- Treating rumors, influencer posts, raw mention counts, or sentiment scores as sufficient trade signals.
- Introducing broker connectivity, automatic order placement, or LLM-controlled risk decisions.
- Changing v1 entries, exits, sizing, risk limits, execution timing, or holdout protocol.
- Paying for data providers in the initial free-first phase without a separate explicit decision.
- Ingesting every available feed regardless of quality, relevance, maintenance cost, or incremental value.

## Relevant context

- `src/swing_trader/data.py` currently uses yfinance for adjusted daily OHLCV; no operational SEC, Federal Reserve/FRED, government, news, or social connector was found during intake.
- `knowledge/news/` and the `NEWS-*` schema already support time-bounded observations with canonical URL, UTC publication/retrieval times, source class, entities/topics, retrieval method, observed-content SHA-256, and project-authored summaries/claims.
- `knowledge/registry.json` is generated and validates evidence/provenance structure; it is not an ingestion store.
- `daily_scan_recorder.py` and prospective recorder/evaluator establish useful patterns for immutable snapshots, provenance, information-time boundaries, and no-backfill behavior.
- `paper_operations.py` is approval-only and paper-only; it remains the downstream human-decision boundary.
- `docs/product/strategy-v1.md` and `experiments/PROSPECTIVE-v1-holdout/` define frozen v1 and its prospective validation boundary.

## Proposed design

This PR changes product direction and durable project memory only. Subsequent implementation should proceed in separately reviewable increments:

1. **Source inventory and policy:** create a maintained catalog of candidate free sources. For each provider record data domain, official/public status, endpoint/access method, authentication requirement, cost, rate limits/quotas, terms/licensing, attribution requirements, latency, historical depth, reliability, operational stability, and expected incremental value.
2. **Provider adapters:** define narrow, testable adapters with explicit request budgets, retries/backoff, caching, pagination, timeouts, and fail-closed behavior. Never bypass access controls or platform terms.
3. **Canonical observations:** normalize events/posts/documents into immutable observations with provider/source ID, canonical URL, author/publisher, publication time, first-seen time, retrieval time, timezone, entity/ticker candidates, topic/event taxonomy, language, retrieval method, content fingerprint, and project-authored summary. Preserve source timestamps separately; never substitute retrieval time for publication time.
4. **Deduplication and corroboration:** cluster syndicated/reposted content, identify independent originating sources, and avoid counting copies as independent confirmation.
5. **Quality and manipulation controls:** evaluate source track record, account/source authenticity where legally and technically available, bot/spam patterns, concentration, coordinated promotion, novelty, freshness, and historical incremental value. Unknown quality must remain unknown, not be silently scored as trustworthy.
6. **Event and entity intelligence:** classify material company, regulatory, government, macro, sector, technology, supply-chain, product, and social-attention events; map direct and indirect issuer/ticker relationships with explicit confidence.
7. **Market confirmation:** join observations to point-in-time market data such as gaps, abnormal volume, volatility, relative strength, liquidity, spreads, and post-event continuation/reversal.
8. **Catalyst research:** produce explainable ranked candidates and explicit no-trade/no-chase states. Keep any catalyst strategy and execution timing separately specified and validated before operational promotion.
9. **Evaluation:** measure source-level coverage, freshness, precision, false positives, incremental predictive value, and net outcomes after realistic costs on timestamp-correct data. Use prospective capture where reliable historical point-in-time source data is unavailable.

Initial source domains to investigate include SEC/EDGAR, Federal Reserve/FRED, Treasury, BLS, BEA, EIA, FDA, CFTC, FTC/DOJ, other relevant regulators and government procurement/disclosures, company investor-relations feeds, reputable news/RSS, and public interfaces for X, Reddit, Stocktwits, YouTube, Bluesky, Hacker News, and Google Trends where free access and terms permit. This is an investigation list, not a commitment that every provider has a free production API or usable historical data.

## Trading and research implications

- Information-time correctness is essential: retain event publication time, provider timestamp, first-seen time, and retrieval time separately. A backtest may only use information actually available by its decision timestamp.
- Historical news/social archives are often incomplete, revised, deleted, or unavailable. Do not reconstruct historical signals from current pages or infer missing timestamps.
- Survivorship, selection, and source-coverage bias apply to company and social data as well as price data.
- Syndicated articles and reposts are not independent confirmations.
- Social activity is especially vulnerable to bots, coordinated promotion, influencer incentives, and pump-and-dump behavior. It is context requiring corroboration, not a standalone buy/sell signal.
- Market reaction can be priced in before ingestion; gap/extension and risk/reward must be considered to avoid chasing.
- Include spread, slippage, liquidity, and realistic event-time execution assumptions in any strategy evaluation.
- LLM summaries/classifications may assist triage but cannot fabricate facts, establish source reliability alone, override deterministic risk controls, or create validation evidence.
- No external observation or operational paper-trading record can alter frozen v1 or become prospective-v1 validation evidence.

## Alternatives considered

- **Continue as a technical-only scanner:** rejected as the long-term product direction because it omits material event context and emerging catalysts.
- **Ingest every social post and news item:** rejected because volume creates cost, noise, duplication, manipulation exposure, and unmanageable false positives.
- **Start with a paid all-in-one data vendor:** deferred because the user explicitly prioritizes free integrations and source-level control.
- **Use social sentiment as the primary score:** rejected because raw sentiment/mentions are easily manipulated and often lag or duplicate primary information.
- **Replace v1 with a catalyst strategy immediately:** rejected because v1 is frozen under an active prospective holdout and catalyst timing/execution needs independent research.

## Test and validation plan

This goal-setting PR contains documentation only. Validate the final diff for consistency, English-only repository text, preservation of frozen v1/holdout wording, and accurate distinction between current integrations and future direction. Required CI should still run on the PR.

Future provider PRs must include synthetic contract tests for pagination, quotas, retries, malformed/missing timestamps, duplicate content, source outages, timezone normalization, deterministic snapshots, and licensing/access boundaries. Research validation must use timestamp-correct evidence and compare each source's incremental contribution against a price-only and existing-source baseline.

## Simplification plan

Keep this PR documentation-only. Do not introduce speculative provider abstractions or source lists in production configuration before an adapter design exists. Future integrations should share only proven common behavior and avoid one oversized generic connector interface.

## Compound plan

Update the canonical mission, architecture goal, roadmap, README, and current-state memory so future contributors consistently preserve the new market-intelligence direction and v1 boundary. No separate solution note is warranted for a product-goal clarification.

## Documentation and memory updates

- `AGENTS.md`: project mission and invariant.
- `ARCHITECTURE.md`: product goal and source-quality principles.
- `README.md`: user-facing product description and v1 separation.
- `docs/roadmap.md`: immediate source inventory/integration direction.
- `.ai/current-state.md`: current goal and explicit statement that integrations are not implemented by this PR.
- `docs/plans/active/free-market-intelligence-goal.md`: this plan.

## Implementation plan

1. [x] Inspect current repository, open PRs, strategy, data, knowledge, and handoff conventions.
2. [x] Establish the new product goal and explicit v1 boundary.
3. [x] Document the free-first, quality-gated data acquisition direction.
4. [ ] Review source inventory and integration architecture in a follow-up implementation PR.
5. [ ] Implement free official/public providers in prioritized, independently testable increments.
6. [ ] Add public social/community sources only where official access and terms permit.
7. [ ] Build event intelligence, corroboration, market confirmation, and source-level evaluation.
8. [ ] Simplify, validate, compound, and complete formal review for implementation PRs.

## Review checklist

- [x] Scope and acceptance criteria are clear.
- [x] Design is consistent with project invariants.
- [x] Trading/research risks are addressed.
- [x] Test strategy is sufficient.
- [x] Simplification risks are identified.
- [x] Potential compound knowledge destinations are identified.
- [x] Required memory/documentation changes are identified.

## Definition of done

This goal-setting PR is complete when the new mission is consistently documented, free-first source coverage is prioritized without promising universal API availability, data quality/licensing/provenance controls are explicit, and frozen v1 plus its prospective holdout remain unchanged. Source integrations and catalyst logic are intentionally future work.
