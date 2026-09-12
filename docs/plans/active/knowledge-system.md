# Design Plan — Source-Governed Knowledge System

Status: Active

## Problem

The repository has strong experiment, decision, and solution memory, but it does not yet maintain a curated domain-knowledge layer that records which external evidence informs the project. Ad-hoc links, copied PDFs, or uncited prose would make provenance, licensing, authority, and inference boundaries difficult to review.

## Goals

- Add a repo-native knowledge base whose canonical records remain reviewable in Git.
- Prefer primary peer-reviewed research and official regulator/index/data-provider methodology over secondary commentary.
- Store bibliographic metadata and project-authored summaries rather than redistributing copyrighted full text.
- Make every interpretive knowledge note cite stable source IDs.
- Record what a source supports, its important limitations, and what it does not establish for this strategy.
- Generate a deterministic machine-readable registry with content hashes and source-to-note backlinks.
- Fail CI on malformed source metadata, broken source references, duplicate IDs, missing required note sections, or stale registry bytes.
- Seed the system with authoritative material directly relevant to momentum/trend evidence, backtest selection bias, performance statistics, and point-in-time universe construction.
- Keep external knowledge distinct from project-specific experimental evidence: a paper can motivate a hypothesis but cannot validate Swing Trader v1.

## Non-goals

- Do not commit paywalled/copyrighted papers, books, scraped article bodies, or large binary source archives.
- Do not use source count or an arbitrary evidence score as a substitute for research judgment.
- Do not automatically convert literature claims into strategy/risk rules.
- Do not add semantic/vector retrieval in this milestone.
- Do not make the knowledge registry a second editable source of truth.
- Do not change frozen v1 strategy, risk, execution, or prospective holdout rules.

## Canonical structure

```text
knowledge/
  README.md
  SOURCE_POLICY.md
  sources/
    SRC-....yaml
  notes/
    ...md
  registry.json
```

Each source YAML records stable identity, authorship, publication venue/publisher, year, source class, DOI/URL where applicable, access date, topics, redistribution policy, a short project-authored relevance summary, and limitations.

Each note uses YAML front matter with a stable `KN-*` id, title, topics, and cited `SRC-*` ids. The Markdown body must include `What the evidence says`, `Project implication`, `What it does not establish`, and `Sources` sections.

## Source policy

Source classes are descriptive rather than numeric rankings:

- `peer_reviewed_primary`
- `official_methodology`
- `official_documentation`
- `working_paper_primary`
- `secondary_review`

Initial curation should strongly prefer the first three classes. The registry records source class but does not infer a universal quality score from it.

Full text is not committed by default. Canonical records link to DOI/publisher/official pages and contain only project-authored summaries plus minimal bibliographic facts. Any future full-text inclusion requires explicit redistribution rights and a separate review.

## Initial corpus

Seed source records and notes around:

- cross-sectional momentum: Jegadeesh & Titman (1993);
- time-series momentum: Moskowitz, Ooi & Pedersen (2012);
- data snooping: White (2000);
- multiple testing in return research: Harvey, Liu & Zhu (2016);
- probability of backtest overfitting: Bailey, Borwein, López de Prado & Zhu (2017);
- Sharpe-ratio estimation/annualization: Lo (2002);
- changing index membership and point-in-time constituent selection: current S&P Dow Jones Indices methodology/policy material;
- delisting-return treatment as a reminder that disappeared securities remain economically relevant: current CRSP methodology/documentation.

The project notes must state explicitly that these sources motivate methodology and hypotheses but do not establish profitability of Swing Trader v1.

## Deterministic registry

Add `knowledge_registry.py` and a CLI similar to the experiment registry. The generator must:

- discover source YAML and note Markdown records deterministically;
- validate stable IDs and uniqueness;
- validate required bibliographic fields and HTTPS source links;
- reject committed full-text claims unless explicit redistribution metadata permits them;
- validate note front matter and required inference-boundary sections;
- reject notes citing unknown sources;
- hash canonical source/note bytes;
- render deterministic `knowledge/registry.json` with no generation timestamp;
- include backlinks from each source to notes that cite it;
- support `--check` for exact committed-byte verification.

## Validation

- focused synthetic registry tests;
- committed registry consistency test;
- full `pytest -q` and `ruff check src tests`;
- dedicated read-only knowledge-registry workflow regenerating/checking the committed index;
- source records manually checked against authoritative publisher/official pages;
- no strategy/risk/protocol files changed;
- formal final-diff review before merge.

## Simplify

Prefer YAML source records plus Markdown notes over a database or external knowledge service. Reuse deterministic-registry patterns, but do not couple knowledge schema to experiment schema.

## Compound

If implementation produces a reusable lesson about separating external literature from project evidence, capture it under solution memory and index it.

## Follow-on

The Project Dashboard should consume `knowledge/registry.json` alongside `experiments/registry.json` and operational/prospective status. The dashboard is a separate milestone so UI concerns do not weaken knowledge provenance rules.
