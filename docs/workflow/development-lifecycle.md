# Development Lifecycle

This document defines the required lifecycle for repository changes performed by humans or AI agents.

The default lifecycle is:

```text
Session bootstrap
  -> Intake / resume
  -> Dedicated branch
  -> Design
  -> Draft PR
  -> Implementation
  -> Simplify
  -> Validation
  -> Compound
  -> PR Review
  -> Merge
```

The process is designed to keep implementation traceable, reviewable, progressively more useful to future work, and resumable by a new AI session without manual context transfer.

## 0. Autonomous session bootstrap

Before substantive work in every new AI coding session, reconstruct the current project/work state from repository and GitHub sources.

When shell access is available, the agent runs:

```bash
python scripts/agent_bootstrap.py
```

This generates two ignored working files:

- `.ai/context.md` — compact durable repository context plus local Git state;
- `.ai/handoff.md` — local Git state, open pull requests, inferred active PR, PR lifecycle record, and relevant active plan.

The user must not be asked to run this command manually.

When shell execution is unavailable but repository/GitHub tools are available, the agent performs the equivalent reconstruction directly: read `AGENTS.md` and `.ai/current-state.md`, inspect open PRs and branch state, select the current-branch PR when available, otherwise inspect the only or most recently updated open PR, read its `Agent handoff` section and referenced plan, and verify CI/review state.

If a logical change is already in progress, resume its existing branch/PR instead of creating duplicate work. If multiple PRs make the active task ambiguous, inspect all of them and infer from branch, recency, plan, and user intent before asking the user. Ask only when a material product, trading-risk, architecture, or scope decision cannot be derived safely.

The pull request is the canonical transient lifecycle record. Generated handoff files are derived and must not become a separately maintained source of truth.

At meaningful lifecycle transitions, and before yielding control after substantive work when possible, update the PR `Agent handoff` section with:

- current lifecycle stage;
- last verified head SHA;
- concrete next actions;
- blockers or `None`.

An abrupt process/session termination cannot guarantee a final save operation, so agents should update PR state incrementally rather than relying on one end-of-session handoff write.

## 1. Intake

Before editing production code, define:

- the problem or opportunity;
- the desired outcome;
- scope and explicit non-goals;
- measurable acceptance criteria;
- relevant architecture, ADRs, strategy rules, prior solutions, and experiments;
- material risks, especially look-ahead bias, execution assumptions, position/risk logic, data quality, reproducibility, and overfitting.

If Intake has already been completed in an active PR/design plan, resume from that source of truth rather than repeating it.

## 2. Dedicated branch

Create one dedicated branch from the latest `main` before creating version-controlled design or implementation changes, unless the same logical change already has an active branch/PR that should be resumed.

The branch is the working container for the entire logical change: design, implementation, simplification, tests, compound knowledge, review fixes, final documentation, and agent handoff state in the PR body.

Do not reuse a branch for unrelated work.

## 3. Design

Design comes before production implementation for any non-trivial change.

Create or update a plan under `docs/plans/active/` using `.ai/design-template.md`.

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
- simplification considerations;
- expected reusable knowledge or compound opportunities;
- rollout or migration considerations when applicable;
- alternatives considered for material design choices.

Create an ADR when the change establishes a durable architectural, trading, data, or workflow decision.

### Design gate

Production implementation should not begin until the design is internally coherent and satisfies project invariants.

Material changes to trading behavior, risk policy, execution semantics, live-trading boundaries, or core architecture should be explicitly surfaced in the PR before implementation proceeds.

## 4. Draft PR

Open a Draft PR once the design is sufficiently clear. The Draft PR is the shared audit trail for the entire feature: design, implementation, simplification, tests, compound knowledge, review feedback, handoff state, and final decision.

The Draft PR must reference the active plan and summarize:

- why the change is needed;
- the proposed design;
- expected trading/research impact;
- validation strategy;
- current `Agent handoff` state.

Do not open a second implementation PR for the same logical feature.

## 5. Implementation

Implement the approved design on the same branch and PR.

During implementation:

- use focused Conventional Commits;
- keep changes within the agreed scope;
- add or update tests with the implementation;
- update docs and durable memory when behavior or decisions change;
- record research experiments when applicable;
- keep repository content in English;
- never weaken deterministic risk controls or introduce look-ahead bias for convenience;
- keep the PR handoff synchronized when the lifecycle stage or next actions materially change.

If implementation reveals that the design is materially wrong, update the design first, explain the change in the PR, update handoff state, and then continue implementation.

## 6. Simplify

After implementation, perform a dedicated simplification pass before final validation.

Inspect the diff for:

- dead code;
- unnecessary abstractions;
- avoidable indirection;
- duplicated logic;
- overly broad interfaces;
- complexity not justified by requirements or evidence.

Prefer explicit domain logic over clever abstractions. Do not remove safeguards, trading invariants, reproducibility requirements, useful tests, or continuity metadata in the name of simplification.

Record the outcome in the PR. `No simplification needed` is valid when justified.

## 7. Validation

Before the PR is ready for Compound and final review:

- run the required test suite;
- run lint/static checks;
- run relevant integration or backtest validation;
- inspect execution assumptions and data alignment;
- verify no unintended risk-policy changes;
- verify documentation and project memory reflect the state that will exist after merge;
- verify the PR `Agent handoff` section reflects the current head, stage, next actions, and blockers.

## 8. Compound

Before final review, ask:

> What did this change teach us that a future agent should not have to rediscover?

Record one of three outcomes:

1. `No reusable learning`.
2. Update an existing durable source of truth such as an ADR, architecture/domain document, plan, experiment record, or current-state memory.
3. Create a reusable solution note under `docs/solutions/` using `.ai/solution-template.md`.

Use:

- `docs/decisions/` for durable project decisions;
- `docs/solutions/` for recurring problem/solution knowledge;
- `experiments/` for experiment-specific evidence and failed hypotheses.

Compound occurs before final formal review. Any files changed by the Compound stage must be included in the final reviewed diff.

The active plan should also be finalized for the post-merge state before final review. Move it to `docs/plans/completed/` or clearly mark it completed-on-merge, and update `.ai/current-state.md` when project state changes materially.

## 9. PR Review

Every PR requires a formal review pass before merge, including PRs authored by an AI agent.

The reviewer must inspect the final diff rather than relying only on the PR description.

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
- Is remaining complexity justified?
- Did the Simplify pass remove avoidable complexity without weakening safeguards?
- Are module boundaries and interfaces clean?
- Is duplicated or dead code introduced?

### Compound quality

- Did the PR identify reusable learning appropriately?
- Is a new solution note actually reusable rather than process noise?
- Does the learning belong in an ADR, solution note, experiment record, or existing source of truth?

### Repository hygiene and continuity

- Are branch, commits, and PR title compliant?
- Is all repository content in English?
- Are docs, ADRs, plans, solution memory, and current-state memory updated?
- Is the PR `Agent handoff` section current and sufficient for another agent to resume without chat history?
- Are all CI checks green?
- Are there unresolved review threads?

### Review outcome

The review must end with one of:

- `PASS` — ready to merge once required CI is green;
- `CHANGES REQUESTED` — issues must be fixed on the same branch and reviewed again;
- `BLOCKED` — external decision or unresolved design issue prevents merge.

When the PR author and reviewer use the same GitHub identity, GitHub cannot provide an independent approval signal. In that case, record the review as a formal review comment with the outcome and findings. A separate human or bot identity may provide an additional approval when configured.

If review requests changes, return to implementation and repeat Simplify, Validation, Compound, Handoff, and Review as applicable.

## 10. Merge

The agent responsible for the change also owns completing the merge after review.

Merge only when all of the following are true:

- design and acceptance criteria are satisfied;
- Simplify and Compound are complete;
- formal review outcome is `PASS`;
- required CI checks are green;
- no unresolved review threads remain;
- repository memory/documentation is current;
- PR handoff state is current for the final reviewed head;
- no known blocker remains.

Use squash merge by default. The squash commit title should match the Conventional Commit PR title.

Delete the feature branch after merge when possible.

After merge, the next AI session derives the new state from `main`, open PRs, repository memory, and any remaining active plans; no manual user handoff is required.

## 11. Exceptions

Tiny typo-only or formatting-only documentation changes may use shortened Design, Simplify, and Compound sections, but they still require a dedicated branch, PR, Agent handoff section, review, and green checks.

Emergency fixes still require a branch and PR. The design may be concise, but the reason for the expedited path and the regression risk must be documented. Simplify, Compound, and Handoff checks still apply, even when the outcome is intentionally minimal.

## AI operating rule

For AI-driven development, the default behavior is autonomous execution of this lifecycle:

1. bootstrap repository/session state without asking the user to transfer context;
2. resume the active logical change when one exists, otherwise understand the new task and create the dedicated branch from latest `main`;
3. write/update the design plan;
4. open the Draft PR and initialize Agent handoff;
5. implement;
6. keep PR handoff state current through meaningful transitions;
7. simplify;
8. validate;
9. compound reusable learning;
10. finalize memory and the active plan;
11. perform a final diff-based PR review including continuity/handoff state;
12. fix findings and repeat the relevant stages if necessary;
13. merge only after a `PASS` review and green CI.

Ask for user input only when a material product, trading-risk, architecture, or scope decision cannot be safely inferred from existing project decisions and repository/GitHub state.
