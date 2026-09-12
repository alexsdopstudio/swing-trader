# ADR-005 — English-only repository content

Status: accepted

## Context

The project is intended to be developed by humans and AI agents across different tools and sessions. A single repository language reduces ambiguity, improves searchability, makes agent context more consistent, and avoids fragmented documentation or mixed-language conventions.

## Decision

English is the only language used for version-controlled repository content.

This includes:

- file and directory names
- code comments and docstrings
- documentation
- descriptive configuration text
- test descriptions
- ADRs and implementation plans
- AI memory and context files
- experiment notes and conclusions
- branch names
- commit messages
- pull request titles and descriptions

Market symbols, proper nouns, external source text, and raw data values remain unchanged when translation would alter their meaning. Any project-authored explanation or annotation around them must still be written in English.

## Consequences

- Contributors and agents must translate repository-facing prose to English before committing it.
- Reviews should reject mixed-language repository content.
- Human conversations outside the repository may use any language.
- Repository memory remains consistent and easier for AI agents to retrieve and reuse.
