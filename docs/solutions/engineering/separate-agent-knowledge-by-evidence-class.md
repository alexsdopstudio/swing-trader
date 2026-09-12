# Separate Agent Knowledge by Evidence Class

## Problem

AI agents can consume many kinds of repository context that look superficially similar as text: academic sources, official methodology, current news, project-authored interpretation, experiment results, operational observations, and generated indexes. If these records share one undifferentiated store, agents can accidentally promote a transient article into durable knowledge, treat a literature prior as project validation, or use a generated projection as if it were canonical evidence.

## Symptoms

- URLs are stored without publication/retrieval time or content provenance.
- News and stable reference material are indexed under the same semantics.
- An agent cannot tell whether a claim came from external literature, a contemporaneous observation, or this project's own experiment.
- Generated indexes are edited directly or treated as independent truth.
- Catalyst/news context begins influencing deterministic risk or frozen strategy rules without an explicit research decision.

## Root cause

The storage model classifies information by format rather than epistemic role. A Markdown file, YAML file, JSON record, and web page can each represent very different evidence. Without explicit namespaces and eligibility boundaries, retrieval collapses provenance and inference levels.

## Reusable solution

Model each evidence class explicitly and keep canonical records separate:

1. **Durable external references** — stable `SRC-*` records for papers, standards, official methodology, and documentation.
2. **Time-bounded external observations** — `NEWS-*` records with canonical URL, publication/retrieval timestamps, source class, retrieval provenance, observed-content fingerprint, and project-authored summary/claims.
3. **Curated interpretation** — `KN-*` notes that cite source/news IDs and state evidence, project implication, and non-conclusions separately.
4. **Project evidence** — experiments/prospective protocols remain under `experiments/` and retain their own stronger validation semantics.
5. **Generated machine indexes** — deterministic JSON registries are projections of canonical records, never a second editable source of truth.

Prefer human-reviewable YAML/Markdown for canonical knowledge and deterministic JSON for machine discovery. Attach URLs to records as provenance metadata rather than treating a URL alone as knowledge.

## When this applies

Use this pattern whenever an agent will combine long-lived external knowledge, current web/news observations, repository conclusions, or generated retrieval indexes. It is especially important when information can influence financial research, strategy design, or claims of validation.

## When this does not apply

A tiny static documentation-only project may not need multiple namespaces or a generated registry. Do not add a vector database or knowledge graph merely to mirror a small repository; semantic retrieval is a separate concern from provenance and can be derived later if scale justifies it.

## Tests and checks

- Validate stable IDs and reject duplicate IDs within each namespace.
- Require canonical HTTPS URLs plus explicit publication/retrieval time for time-bounded observations.
- Require content fingerprints for observations without redistributing copyrighted full text.
- Validate that curated notes reference only known source/news IDs and visibly cite them.
- Encode explicit `validation_evidence: false` semantics for news/context records.
- Regenerate machine indexes in CI and fail on stale or untracked generated output.
- Review that literature/news changes do not modify strategy, risk, execution, or holdout rules automatically.

## References

- `knowledge/README.md`
- `knowledge/SOURCE_POLICY.md`
- `knowledge/news/README.md`
- `src/swing_trader/knowledge_registry.py`
- `knowledge/notes/KN-0005-provenance-for-agent-knowledge.md`
- `docs/solutions/engineering/keep-derived-repository-indexes-regenerable.md`
- `docs/solutions/engineering/separate-operational-observations-from-validation-evidence.md`
