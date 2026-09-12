# Design Plan — Source-Governed Knowledge System

Status: Active

## Problem

The repository has strong experiment, decision, and solution memory, but it does not yet maintain a curated domain-knowledge layer that records which external evidence informs the project. Ad-hoc links, copied PDFs, uncited prose, or an undifferentiated stream of news would make provenance, licensing, authority, time boundaries, and inference boundaries difficult to review.

## Goals

- Add a repo-native knowledge base whose canonical records remain reviewable in Git.
- Prefer primary peer-reviewed research and official regulator/index/data-provider methodology over secondary commentary.
- Store bibliographic metadata and project-authored summaries rather than redistributing copyrighted full text.
- Make every interpretive knowledge note cite stable source and/or news-observation IDs.
- Record what a source supports, its important limitations, and what it does not establish for this strategy.
- Represent time-bounded news as observations with canonical URL, publication/retrieval timestamps, entities, topics, provenance, and content fingerprint rather than treating URLs alone as knowledge.
- Keep transient news observations separate from curated durable notes; news can later be consolidated into a note through explicit references.
- Generate a deterministic machine-readable registry with content hashes and source/news-to-note backlinks.
- Fail CI on malformed source/news metadata, broken references, duplicate IDs, missing required note sections, or stale registry bytes.
- Seed the system with authoritative material directly relevant to momentum/trend evidence, backtest selection bias, performance statistics, point-in-time universe construction, and provenance modeling.
- Keep external knowledge distinct from project-specific experimental evidence: a paper or news item can motivate a hypothesis or provide context but cannot validate Swing Trader v1.

## Non-goals

- Do not commit paywalled/copyrighted papers, books, scraped article bodies, or large binary source archives.
- Do not use source count, news volume, sentiment, or an arbitrary evidence score as a substitute for research judgment.
- Do not automatically convert literature or news claims into strategy/risk rules.
- Do not add semantic/vector retrieval in this milestone.
- Do not make the knowledge registry a second editable source of truth.
- Do not build a live news-ingestion/catalyst agent in this milestone; this milestone defines the durable record it will write later.
- Do not change frozen v1 strategy, risk, execution, or prospective holdout rules.

## Canonical structure

```text
knowledge/
  README.md
  SOURCE_POLICY.md
  sources/
    SRC-....yaml
  news/
    README.md
    NEWS-YYYYMMDD-NNNN-....yaml
  notes/
    KN-....md
  registry.json
```

Each source YAML records stable identity, authorship, publication venue/publisher, year, source class, DOI/URL where applicable, access date, topics, redistribution policy, a short project-authored relevance summary, and limitations.

Each news YAML is a time-bounded observation. It records a stable `NEWS-*` id, canonical HTTPS URL, publisher, descriptive source class, UTC publication/retrieval timestamps, entities, topics, retrieval method, an observed-content SHA-256 fingerprint, project-authored summary/claims, and a no-full-text redistribution marker. The URL is provenance metadata, not the knowledge object by itself.

Each note uses YAML front matter with a stable `KN-*` id, title, topics, and cited `SRC-*` and/or `NEWS-*` ids. The Markdown body must include `What the evidence says`, `Project implication`, `What it does not establish`, and `Sources` sections.

## Source policy

Durable source classes are descriptive rather than numeric rankings:

- `peer_reviewed_primary`
- `official_methodology`
- `official_documentation`
- `working_paper_primary`
- `secondary_review`

Initial curation should strongly prefer the first three classes. The registry records source class but does not infer a universal quality score from it.

News source classes are also descriptive:

- `official_filing`
- `official_company_release`
- `regulator_release`
- `exchange_release`
- `primary_news`
- `secondary_news`

Primary/official material should be preferred when it can establish the underlying fact directly. A secondary article may add context but must not silently replace a filing, regulator notice, exchange notice, or issuer release that is available.

Full text is not committed by default. Canonical records link to DOI/publisher/official/news pages and contain only project-authored summaries plus minimal bibliographic facts. Any future full-text inclusion requires explicit redistribution rights and a separate review.

## News observation semantics

News records are immutable-in-spirit observations of what an agent or researcher retrieved at a particular information time. Their `retrieved_at` timestamp must be UTC and no earlier than `published_at`. `provenance.observed_content_sha256` fingerprints the observed representation without requiring copyrighted article text to be committed.

News is not automatically durable knowledge. A later curated note may cite one or more `NEWS-*` records alongside durable sources; the generated registry then exposes backlinks. A corrected or retracted story should be represented through explicit later records/metadata rather than silently erasing the earlier observation from Git history.

News observations are context inputs only. They are not prospective holdout evidence, do not validate the strategy, and cannot override deterministic strategy/risk controls.

## Initial corpus

Seed source records and notes around:

- cross-sectional momentum: Jegadeesh & Titman (1993);
- time-series momentum: Moskowitz, Ooi & Pedersen (2012);
- data snooping: White (2000);
- multiple testing in return research: Harvey, Liu & Zhu (2016);
- probability of backtest overfitting: Bailey, Borwein, López de Prado & Zhu (2017);
- Sharpe-ratio estimation/annualization: Lo (2002);
- changing index membership and point-in-time constituent selection: current S&P Dow Jones Indices methodology/policy material;
- delisting-return treatment as a reminder that disappeared securities remain economically relevant: current CRSP methodology/documentation;
- provenance modeling: W3C PROV family of recommendations.

The project notes must state explicitly that these sources motivate methodology and hypotheses but do not establish profitability of Swing Trader v1.

No arbitrary live-news item is seeded merely to populate the directory. News schema behavior is covered synthetically until a real ingestion/catalyst workflow has a genuine contemporaneous observation to record.

## Deterministic registry

Add `knowledge_registry.py` and a CLI similar to the experiment registry. The generator must:

- discover source YAML, news YAML, and note Markdown records deterministically;
- validate stable IDs and uniqueness within each namespace;
- validate required bibliographic fields and HTTPS source/news links;
- validate UTC news timestamps, source class, entities/topics, retrieval method, fingerprint, summary/claims, and no-full-text rule;
- reject committed full-text claims unless explicit redistribution metadata permits them;
- validate note front matter and required inference-boundary sections;
- reject notes citing unknown sources or news observations;
- hash canonical source/news/note bytes;
- render deterministic `knowledge/registry.json` with no generation timestamp;
- include backlinks from each source/news observation to notes that cite it;
- support `--check` for exact committed-byte verification.

## Validation

- focused synthetic registry tests, including news timestamps, fingerprint, source class, duplicate IDs, and note-to-news references;
- committed registry consistency test;
- full `pytest -q` and `ruff check src tests`;
- dedicated read-only knowledge-registry workflow regenerating/checking the committed index;
- source records manually checked against authoritative publisher/official pages;
- no strategy/risk/protocol files changed;
- formal final-diff review before merge.

## Simplify

Prefer YAML source/news records plus Markdown notes over a database or external knowledge service. YAML is canonical human-reviewable input; JSON remains a generated deterministic machine index. Reuse deterministic-registry patterns, but do not couple knowledge schema to experiment schema.

## Compound

If implementation produces a reusable lesson about separating external literature, time-bounded observations, curated interpretation, and project evidence, capture it under solution memory and index it.

## Follow-on

The Project Dashboard should consume `knowledge/registry.json` alongside `experiments/registry.json` and operational/prospective status. A future catalyst/news agent should write canonical `NEWS-*` observations through the validated schema rather than inventing its own store. The dashboard and ingestion agent remain separate milestones so UI/retrieval concerns do not weaken knowledge provenance rules.
