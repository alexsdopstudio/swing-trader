# News Observations

This directory stores time-bounded external observations for future catalyst/news workflows. It is not a feed cache and it is not a validation dataset.

Each real observation is one YAML file named:

```text
NEWS-YYYYMMDD-NNNN-short-slug.yaml
```

The date embedded in the identifier is the UTC publication date. Sequence numbers are assigned per publication date and are stable once committed.

## Canonical record

```yaml
schema_version: 1
id: NEWS-20260913-0001
title: Example issuer announcement
canonical_url: https://example.com/announcement
publisher: Example Issuer
source_type: official_company_release
published_at: "2026-09-13T14:32:00Z"
retrieved_at: "2026-09-13T14:41:17Z"
entities:
  - EXAMPLE
topics:
  - earnings
provenance:
  retrieval_method: web
  observed_content_sha256: 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
rights:
  full_text_committed: false
summary: >-
  Project-authored factual summary of what was observed.
claims:
  - statement: Example claim extracted from the observed source.
    attribution: Example Issuer
status: observed
```

## Semantics

- `canonical_url` identifies the external resource but is not sufficient provenance by itself.
- `published_at` and `retrieved_at` use explicit UTC `Z` timestamps; retrieval cannot precede publication.
- `observed_content_sha256` fingerprints the representation seen by the retriever. It does not grant redistribution rights and is not a substitute for storing full text when lawful archival is required.
- `entities` contain stable market/entity identifiers meaningful to the project, such as tickers or crypto symbols where appropriate.
- `topics` use lowercase kebab-case tags.
- `summary` and `claims` are project-authored descriptions, not copied article text.
- `status` is `observed`, `corrected`, or `retracted`. Corrections/retractions must remain traceable through Git history and later observations; never silently rewrite the historical information-time record.
- `rights.full_text_committed` is `false` in schema v1.

## Evidence boundary

A `NEWS-*` record is contemporaneous context. It may later be cited by a curated `KN-*` note, but it is not prospective holdout evidence, is not proof of a trading edge, and cannot change deterministic strategy or risk controls by itself.

No synthetic example YAML is committed here because generated registries must index only genuine observations. Schema behavior is tested with temporary fixtures until a future ingestion workflow records a real contemporaneous event.
