# ADR-007 — Compound Engineering Loop

Status: Accepted

## Context

The repository already uses a design-first, branch-and-pull-request gated workflow with durable project memory. That process makes changes safer and reviewable, but it does not explicitly require each completed change to improve the starting point for future work.

AI-assisted development benefits from a deliberate feedback loop: implementation should be simplified before final validation, and reusable lessons should be captured so future agents do not repeatedly rediscover the same problems, trade-offs, or research pitfalls.

## Decision

Adopt a repository-native compound engineering lifecycle:

```text
Intake
  -> Dedicated branch
  -> Design
  -> Draft PR
  -> Implementation
  -> Simplify
  -> Validation
  -> Compound
  -> Formal Review
  -> Squash Merge
```

`Simplify` is a dedicated pass over the implementation to remove accidental complexity, duplication, dead code, unnecessary abstractions, and unjustified indirection without weakening required safeguards.

`Compound` asks what reusable learning a future agent should not have to rediscover. The outcome may be:

- `No reusable learning`;
- an update to an existing durable source of truth;
- a reusable solution note under `docs/solutions/`.

Solution notes are distinct from ADRs and experiments:

- ADRs record durable project decisions;
- solution notes record reusable recurring problem/solution knowledge;
- experiments record experiment-specific evidence, configurations, and conclusions.

Compound occurs before final formal review so every knowledge artifact created by the step is part of the final reviewed diff.

The project adopts the compound engineering principle, not an external plugin dependency. The workflow must remain portable across AI coding agents and developer tools.

## Consequences

Benefits:

- future tasks begin with more reusable knowledge;
- recurring engineering and research mistakes are less likely to be rediscovered;
- complexity receives an explicit challenge before merge;
- the final review covers both code and newly captured knowledge;
- the repository remains the system of record rather than chat history or one vendor-specific agent framework.

Costs:

- PRs require two additional explicit gates;
- contributors must decide whether a learning deserves durable memory;
- low-value solution notes can create noise if the Compound step is treated as a quota rather than a judgment call.

## Guardrails

- It is valid to record `No reusable learning`.
- Do not create solution notes solely to satisfy process.
- Do not simplify away deterministic risk controls, research reproducibility, or safety checks.
- Prefer updating an existing source of truth over creating duplicate memory.
- Final review must happen after Compound whenever Compound changes repository content.
