# ADR-006 — Gated Development Lifecycle

Status: Accepted

## Context

The repository is developed with significant AI assistance. Without an explicit lifecycle, an agent can move directly from a request to code, leave design reasoning only in chat history, perform an informal review, or leave merge-ready pull requests open.

For a trading research system, this creates additional risk because apparently small implementation choices can change execution timing, introduce look-ahead bias, weaken risk controls, or make experiments irreproducible.

## Decision

All non-trivial repository changes follow a gated lifecycle:

```text
Intake
  -> Design
  -> Dedicated branch
  -> Draft PR
  -> Implementation
  -> Validation
  -> Formal diff-based review
  -> Merge
```

Design and implementation remain in one pull request so the complete reasoning and implementation history are auditable together.

Non-trivial work requires a version-controlled design plan before production implementation. Pull requests are opened as Draft after design and become ready for review after implementation and validation.

Every PR receives a formal review of the actual diff. The review records one of `PASS`, `CHANGES REQUESTED`, or `BLOCKED`. A PR may be merged only after a `PASS` review and green required CI.

The agent or engineer responsible for the PR also owns completing the merge once all gates are satisfied. Squash merge is the default.

## Consequences

Benefits:

- design intent survives beyond chat history;
- review can compare implementation against explicit acceptance criteria;
- trading/research risks are considered before code is written;
- AI agents have a deterministic development protocol;
- completed work is less likely to remain indefinitely unmerged;
- one PR provides an audit trail from design through merge.

Costs:

- small changes have slightly more process overhead;
- plans and PR descriptions require maintenance as implementation evolves;
- self-review under one GitHub identity is not equivalent to independent human approval.

## Exceptions

Tiny documentation typo/formatting changes may use a shortened design section, but they still require a dedicated branch, PR, review, and green checks.

Emergency fixes may use a concise design, but the urgency and regression risk must be documented.