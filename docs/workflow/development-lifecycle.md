# Development Lifecycle

This document defines the required lifecycle for repository changes performed by humans or AI agents.

The default lifecycle is:

```text
Intake
  -> Design
  -> Draft PR
  -> Implementation
  -> Validation
  -> PR Review
  -> Merge
```

The process is designed to keep implementation traceable, reviewable, and consistent with the project's trading and research constraints.

## 1. Intake

Before editing production code, define:

- the problem or opportunity;
- the desired outcome;
- scope and explicit non-goals;
- measurable acceptance criteria;
- relevant architecture, ADRs, strategy rules, and prior experiments;
- material risks, especially look-ahead bias, execution assumptions, position/risk logic, data quality, reproducibility, and overfitting.

For non-trivial changes, create or update a plan under `docs/plans/active/` using `.ai/design-template.md`.

## 2. Design

Design comes before implementation for any non-trivial change.

A design should describe enough of the intended solution that another engineer or agent could review the approach before reading implementation details.

At minimum include:

- context and problem statement;
- goals and non-goals;
- proposed architecture or code changes;
- affected modules and interfaces;
- data flow and execution timing where relevant;
- trading/research implications;
- failure modes and edge cases;
- test strategy;
- rollout or migration considerations when applicable;
- alternatives considered for material design choices.

Create an ADR when the change establishes a durable architectural, trading, data, or workflow decision.

### Design gate

Implementation should not begin until the design is internally coherent and satisfies project invariants.

Material changes to trading behavior, risk policy, execution semantics, live-trading boundaries, or core architecture should be explicitly surfaced in the PR before implementation proceeds.

## 3. Branch and Draft PR

Create one dedicated branch from the latest `main` before implementation.

Open a Draft PR early, once the design is sufficiently clear. The Draft PR is the shared audit trail for the entire feature: design, implementation, tests, review feedback, and final decision.

The Draft PR must reference the active plan and summarize:

- why the change is needed;
- the proposed design;
- expected trading/research impact;
- validation strategy.

Do not open a second implementation PR for the same logical feature.

## 4. Implementation

Implement the approved design on the same branch and PR.

During implementation:

- use focused Conventional Commits;
- keep changes within the agreed scope;
- add or update tests with the implementation;
- update docs and durable memory when behavior or decisions change;
- record research experiments when applicable;
- keep repository content in English;
- never weaken deterministic risk controls or introduce look-ahead bias for convenience.

If implementation reveals that the design is materially wrong, update the design first, explain the change in the PR, and then continue implementation.

## 5. Validation

Before the PR is ready for review:

- run the required test suite;
- run lint/static checks;
- run relevant integration or backtest validation;
- inspect execution assumptions and data alignment;
- verify no unintended risk-policy changes;
- verify documentation and project memory reflect the state that will exist after merge.

The active plan should be finalized as part of the feature PR. Before merge, move it to `docs/plans/completed/` or otherwise mark it as completed-on-merge, and update `.ai/current-state.md` when the project state changes materially.

## 6. PR Review

Every PR requires a formal review pass before merge, including PRs authored by an AI agent.

The reviewer must inspect the diff rather than relying only on the PR description.

Review should cover:

### Correctness

- Does the implementation satisfy the acceptance criteria?
- Are edge cases and failure modes handled?
- Are tests meaningful rather than merely increasing coverage?

### Trading and research integrity

- Is there any look-ahead or survivorship bias?
- Are signal and execution timestamps realistic?
- Are transaction costs/slippage assumptions preserved where relevant?
- Are deterministic risk controls intact?
- Is the change likely to encourage overfitting or data leakage?

### Architecture and maintainability

- Does the implementation match the documented design?
- Is complexity justified?
- Are module boundaries and interfaces clean?
- Is duplicated or dead code introduced?

### Repository hygiene

- Are branch, commits, and PR title compliant?
- Is all repository content in English?
- Are docs, ADRs, plans, and current-state memory updated?
- Are all CI checks green?
- Are there unresolved review threads?

### Review outcome

The review must end with one of:

- `PASS` — ready to merge once required CI is green;
- `CHANGES REQUESTED` — issues must be fixed on the same branch and reviewed again;
- `BLOCKED` — external decision or unresolved design issue prevents merge.

When the PR author and reviewer use the same GitHub identity, GitHub cannot provide an independent approval signal. In that case, record the review as a formal review comment with the outcome and findings. A separate human or bot identity may provide an additional approval when configured.

## 7. Merge

The agent responsible for the change also owns completing the merge after review.

Merge only when all of the following are true:

- design and acceptance criteria are satisfied;
- formal review outcome is `PASS`;
- required CI checks are green;
- no unresolved review threads remain;
- repository memory/documentation is current;
- no known blocker remains.

Use squash merge by default. The squash commit title should match the Conventional Commit PR title.

Delete the feature branch after merge when possible.

## 8. Exceptions

Tiny typo-only or formatting-only documentation changes may use a shortened design section, but they still require a dedicated branch, PR, review, and green checks.

Emergency fixes still require a branch and PR. The design may be concise, but the reason for the expedited path and the regression risk must be documented.

## AI operating rule

For AI-driven development, the default behavior is autonomous execution of this lifecycle:

1. understand the task and repository context;
2. write/update the design plan;
3. create the dedicated branch and Draft PR;
4. implement and validate;
5. perform a diff-based PR review;
6. fix any review findings and re-review;
7. merge only after a `PASS` review and green CI.

Ask for user input only when a material product, trading-risk, architecture, or scope decision cannot be safely inferred from existing project decisions.