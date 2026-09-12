---
schema_version: 1
id: KN-0005
title: Provenance for agent knowledge

topics:
  - ai-agents
  - knowledge-management
  - provenance
source_ids:
  - SRC-0009
status: curated
---

# Provenance for agent knowledge

## What the evidence says

`SRC-0009` models provenance around identifiable entities, activities, agents, derivations, attribution, and time. The useful project-level lesson is that a claim is more trustworthy when its origin and transformation path can be reconstructed, not merely when its final text is available.

## Project implication

Swing Trader should preserve distinct canonical objects for durable sources, time-bounded news observations, project-authored notes, experiment evidence, and generated indexes. Machine indexes may derive from those objects, but should not become editable competing sources of truth. Time-sensitive observations should record both publication and retrieval time plus a content fingerprint so an agent can reason about what was knowable at that information boundary.

## What it does not establish

`SRC-0009` is not an AI-agent architecture standard and does not imply that this repository is PROV-O compliant. It also says nothing about whether Swing Trader has a profitable edge. The project borrows provenance principles, not the RDF/OWL serialization or a conformance claim.

## Sources

- `SRC-0009` — W3C PROV-O Recommendation.
