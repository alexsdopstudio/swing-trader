# Knowledge Source Policy

## Purpose

The knowledge base exists to make external evidence reviewable, attributable, and useful without confusing literature with project-specific validation.

## Preferred source classes

Source classes describe provenance; they are not automatic quality scores.

1. `peer_reviewed_primary` — original peer-reviewed research.
2. `official_methodology` — current methodology published by an index provider, regulator, exchange, or data provider.
3. `official_documentation` — operational or data documentation from the responsible organization.
4. `working_paper_primary` — original research not yet represented here by a peer-reviewed publication.
5. `secondary_review` — synthesis or commentary, used only when it adds context unavailable from primary material.

Prefer the first three classes whenever they can answer the question directly.

## What belongs in the repository

Commit:

- bibliographic metadata;
- DOI and canonical HTTPS links;
- project-authored summaries and limitations;
- explicit links from knowledge notes to source IDs;
- small excerpts only when necessary and legally permitted.

Do not commit by default:

- publisher PDFs;
- book chapters;
- scraped article bodies;
- paywalled full text;
- third-party datasets or large binary source archives.

Version 1 requires `redistribution.full_text_committed: false` for every source record. Future exceptions require explicit redistribution rights plus a reviewed schema/policy change.

## Inference boundary

A source may support a general proposition such as momentum having historical precedent, repeated testing creating selection bias, or index membership changing through time. It does not establish that Swing Trader v1 is profitable, robust, or validated.

Project-specific claims require project-specific evidence in `experiments/`, and true validation remains subject to the preregistered prospective holdout gates.

## Curation rules

Every source record must include:

- stable source ID;
- title and authors/issuing organization;
- year, source class, publisher, and publication/document family;
- canonical HTTPS URL and DOI when applicable;
- access date;
- topic tags;
- project relevance written in our own words;
- material limitations;
- redistribution metadata.

Every knowledge note must include:

- stable note ID and source IDs in front matter;
- `What the evidence says`;
- `Project implication`;
- `What it does not establish`;
- `Sources`.

## Updating sources

For stable academic publications, preserve the canonical record unless a correction/retraction requires an update. For living official methodologies or documentation, add or update the access date and metadata when the project materially relies on a newer revision; do not silently rewrite what an older project decision depended on.
