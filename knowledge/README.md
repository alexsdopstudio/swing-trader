# Knowledge Base

This directory stores curated external knowledge and time-bounded external observations that inform Swing Trader research methodology, hypothesis formation, and future catalyst context.

It is deliberately separate from project evidence:

- `knowledge/sources/` records durable external references such as papers, standards, and official methodology;
- `knowledge/news/` records contemporaneous, time-bounded news/event observations;
- `knowledge/notes/` records project-authored curated interpretation that cites stable source/news IDs;
- `experiments/` records what Swing Trader itself has actually tested;
- `docs/decisions/` records project decisions;
- `docs/solutions/` records reusable lessons learned while building the system.

An external paper, standard, methodology, or news item can motivate a hypothesis or provide context. It cannot, by itself, validate Swing Trader v1.

## Structure

```text
knowledge/
  SOURCE_POLICY.md
  sources/       canonical durable-source metadata (`SRC-*`)
  news/          canonical time-bounded observations (`NEWS-*`)
  notes/         project-authored curated interpretation (`KN-*`)
  registry.json  deterministic generated index; never edit by hand
```

Canonical human-reviewable records use YAML for structured source/news metadata and Markdown for curated notes. `registry.json` is generated for machines, dashboards, and future retrieval layers; it is not a second editable source of truth.

Source records use stable `SRC-####` identifiers. News observations use `NEWS-YYYYMMDD-NNNN` identifiers whose date matches the UTC publication date. Knowledge notes use stable `KN-####` identifiers and may cite source IDs, news IDs, or both in YAML front matter.

Generate or verify the deterministic registry with:

```bash
swing-knowledge-registry --root .
swing-knowledge-registry --root . --check
```

## Why URLs are not enough

A URL is provenance metadata, not a complete knowledge record. Pages can change, disappear, be corrected, or be retrieved after the event. News observations therefore preserve the canonical URL together with publication/retrieval timestamps, publisher/source class, entities, topics, retrieval method, an observed-content SHA-256 fingerprint, and project-authored summary/claims.

Copyrighted source/news full text is not committed by default. The record preserves attribution and a fingerprint while the repository stores its own summaries and interpretation.

## Initial curated topics

- momentum and trend evidence;
- data snooping, multiple testing, and backtest overfitting;
- performance-statistic interpretation;
- point-in-time universes, constituent changes, and delistings;
- provenance for AI-agent knowledge and time-bounded observations.

The initial corpus is intentionally small and high-signal. Source count and news volume are not quality targets.

No arbitrary real news item is added simply to populate `knowledge/news/`. A future catalyst/news ingestion workflow should write a `NEWS-*` record only when it has a genuine contemporaneous observation, then pass the same registry validation used in CI.
