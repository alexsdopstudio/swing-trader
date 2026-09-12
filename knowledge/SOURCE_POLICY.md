# Knowledge Source Policy

## Purpose

The knowledge base exists to make external evidence and observations reviewable, attributable, time-aware, and useful without confusing literature or news with project-specific validation.

## Preferred durable source classes

Source classes describe provenance; they are not automatic quality scores.

1. `peer_reviewed_primary` — original peer-reviewed research.
2. `official_methodology` — current methodology published by an index provider, regulator, exchange, or data provider.
3. `official_documentation` — operational, standards, or data documentation from the responsible organization.
4. `working_paper_primary` — original research not yet represented here by a peer-reviewed publication.
5. `secondary_review` — synthesis or commentary, used only when it adds context unavailable from primary material.

Prefer the first three classes whenever they can answer the question directly.

## News source classes

Time-bounded news observations use a separate descriptive source-class vocabulary:

1. `official_filing` — regulator-hosted issuer filing or equivalent official filing.
2. `official_company_release` — issuer/company announcement or investor-relations release.
3. `regulator_release` — regulator announcement, order, notice, or official statement.
4. `exchange_release` — exchange or market-operator announcement.
5. `primary_news` — original reporting by a news organization.
6. `secondary_news` — commentary or aggregation derived from other reporting.

Prefer the underlying filing, issuer, regulator, or exchange source when it can establish the factual event directly. Secondary material may add useful context, but should not silently replace an available primary record.

## What belongs in the repository

Commit:

- bibliographic metadata;
- DOI and canonical HTTPS links;
- time-bounded news metadata and canonical URLs;
- publication/retrieval timestamps and observed-content fingerprints for news observations;
- project-authored summaries, claims, relevance, and limitations;
- explicit links from knowledge notes to stable source/news IDs;
- small excerpts only when necessary and legally permitted.

Do not commit by default:

- publisher PDFs;
- book chapters;
- scraped article bodies;
- paywalled full text;
- copied news article bodies;
- third-party datasets or large binary source archives.

Version 1 requires `redistribution.full_text_committed: false` for durable sources and `rights.full_text_committed: false` for news observations. Future exceptions require explicit redistribution rights plus a reviewed schema/policy change.

## Why an URL is not sufficient

A URL identifies a location, not the complete information-time state. External pages may be edited, corrected, redirected, removed, or retrieved after the relevant market event.

A canonical `NEWS-*` record therefore combines:

- canonical HTTPS URL;
- publisher and descriptive source class;
- UTC `published_at` and `retrieved_at` timestamps;
- entities and topics;
- retrieval method;
- SHA-256 fingerprint of the observed representation;
- project-authored summary and attributed claims;
- explicit no-full-text redistribution metadata.

This preserves provenance without pretending that a mutable URL is immutable evidence.

## Inference boundary

A durable source may support a general proposition such as momentum having historical precedent, repeated testing creating selection bias, or index membership changing through time. A news observation may establish what a source reported or announced at a particular information time. Neither establishes that Swing Trader v1 is profitable, robust, or validated.

Project-specific claims require project-specific evidence in `experiments/`, and true validation remains subject to the preregistered prospective holdout gates. `NEWS-*` observations are context inputs only and are never holdout substitutes.

Literature or news cannot automatically modify deterministic strategy, execution, sizing, stops, or portfolio-risk rules. Material changes require the normal research/design/experiment lifecycle.

## Curation rules

Every durable source record must include:

- stable source ID;
- title and authors/issuing organization;
- year, source class, publisher, and publication/document family;
- canonical HTTPS URL and DOI when applicable;
- access date;
- topic tags;
- project relevance written in our own words;
- material limitations;
- redistribution metadata.

Every news observation must include:

- stable `NEWS-YYYYMMDD-NNNN` ID matching its UTC publication date;
- title, canonical HTTPS URL, publisher, and supported source class;
- whole-second UTC publication and retrieval timestamps, with retrieval no earlier than publication;
- one or more entities and lowercase kebab-case topics;
- retrieval method and lowercase SHA-256 observed-content fingerprint;
- project-authored summary and attributed claims;
- status (`observed`, `corrected`, or `retracted`);
- `rights.full_text_committed: false`.

Every knowledge note must include:

- stable note ID;
- at least one durable source ID or news-observation ID in front matter;
- `What the evidence says`;
- `Project implication`;
- `What it does not establish`;
- `Sources`.

## Corrections and temporal integrity

News is inherently mutable. Do not silently turn a later correction into what the system supposedly knew earlier. A correction or retraction should remain traceable through Git history and later observation records/status changes. The project should prefer append/explicit supersession semantics over retrospective rewriting whenever information-time interpretation matters.

## Updating durable sources

For stable academic publications and standards, preserve the canonical record unless a correction/retraction requires an update. For living official methodologies or documentation, add or update the access date and metadata when the project materially relies on a newer revision; do not silently rewrite what an older project decision depended on.
