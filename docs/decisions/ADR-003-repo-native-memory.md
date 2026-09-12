# ADR-003 — Repo-native AI memory

Status: accepted

## Context

Multiple AI coding sessions should be able to continue development without relying on one chat history.

## Decision

Use version-controlled Markdown and structured experiment files as the primary project memory. `AGENTS.md` acts as the map; deeper knowledge lives in architecture, domain, decision, plan and experiment documents.

## Reason

Repository-native memory is inspectable, reviewable, branch-aware and available to humans and different AI tools.

## Consequences

Generated working context is derived from these source documents. A vector database is deferred until repository/research scale makes semantic retrieval necessary.
