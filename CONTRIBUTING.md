# Contributing

All changes to this repository follow the gated lifecycle defined in `docs/workflow/development-lifecycle.md`. Direct development on `main` is not part of the normal process.

## Repository language

English is the only language used in version-controlled repository content.

This applies to:

- file and directory names
- source code identifiers where natural-language naming is involved
- comments and docstrings
- Markdown and other documentation
- configuration comments and descriptive values
- test names and test descriptions
- experiment notes and research conclusions
- ADRs, plans, solution notes, and AI memory files
- branch names
- commit messages
- pull request titles and descriptions

Market symbols, proper nouns, external source text, and raw data values are not translated when translation would change their meaning. Any explanation, annotation, metadata, or surrounding prose added by this project must still be written in English.

Human conversations outside the repository may use any language, but text committed to the repository must be English before review and merge.

## Required lifecycle

The default lifecycle for every non-trivial change is:

```text
Session resume / intake
  -> Dedicated branch
  -> Design
  -> Draft PR
  -> Implementation
  -> Simplify
  -> Validation
  -> Compound
  -> Formal PR review
  -> Squash merge
```

Before intake creates new work, contributors and agents must inspect existing open PRs and resume matching in-flight work when appropriate. For AI agents, `docs/workflow/agent-session-handoff.md` defines the required autonomous discovery protocol.

Create the dedicated branch before committing the design plan so design and implementation remain in one auditable history. For non-trivial changes, create a design plan under `docs/plans/active/` using `.ai/design-template.md` before implementing production code. Open the PR as Draft once the design is clear enough to review, then implement the feature on the same branch and PR.

A PR is not complete when the code works. It is complete only after simplification, validation, compound knowledge capture, a formal diff-based `PASS` review, green required CI checks, updated project memory, recoverable handoff state, and merge into `main`.

## Branches

Create one dedicated branch per logical change from the latest `main`, unless the logical change already has an open branch/PR that should be resumed.

Allowed prefixes:

- `feat/` — user-visible or strategy/product functionality
- `fix/` — bug fixes
- `refactor/` — internal restructuring without intended behavior changes
- `perf/` — performance improvements
- `test/` — test-only changes
- `docs/` — documentation-only changes
- `build/` — packaging/build changes
- `ci/` — CI/CD changes
- `chore/` — maintenance work
- `experiment/` — research/backtest experiments and experiment infrastructure

Use lowercase kebab-case after the prefix and keep the branch name in English.

Examples:

```text
feat/portfolio-backtester
fix/yfinance-missing-volume
experiment/breakout-50-day
ci/cache-python-dependencies
```

Do not reuse branches for unrelated work. Delete the branch after merge when possible.

## Commits

Use Conventional Commits:

```text
<type>(<optional-scope>): <imperative summary>
```

Allowed commit types:

```text
feat fix docs style refactor perf test build ci chore revert experiment
```

Examples:

```text
feat(backtest): add portfolio position accounting
fix(data): handle missing volume rows
experiment(momentum): record 50-day breakout baseline
ci(workflow): validate pull request conventions
```

Commit subjects and bodies must be written in English. Keep commits focused. Avoid generic subjects such as `changes`, `fix stuff`, `update`, or `wip` in a PR that is ready for review.

Breaking changes use `!` before the colon and must explain the migration in the commit body when relevant:

```text
feat(config)!: replace flat risk settings with profiles
```

## Pull requests

Every feature, fix, refactor, experiment, and other non-trivial code change must be developed on a dedicated branch and merged through a pull request into `main`.

Open the PR as Draft after the design phase. Keep design and implementation in the same PR so the full reasoning and change history are reviewable together.

PR titles use the same Conventional Commit format as commits. The title and PR description must be written in English. The title should describe the complete logical change because squash merge is the preferred merge strategy.

A PR should:

1. Cover one logical change.
2. Link or name the active design plan when required.
3. Explain the motivation and proposed design before implementation details.
4. State trading/research assumptions affected by the change.
5. Record the Simplify outcome.
6. List tests and validation performed.
7. Record the Compound outcome: reusable learning captured or `No reusable learning`.
8. Call out look-ahead, execution, risk, data-quality, overfitting, or reproducibility implications when applicable.
9. Update durable project memory (`AGENTS.md`, ADRs, plans, current state, strategy docs, solution notes) when future agent behavior should change.
10. Keep all repository-facing text introduced by the PR in English.
11. Pass a formal diff-based review.
12. Pass all required CI checks before merge.
13. Remain resumable from repository/PR state without relying on one chat session.

## Simplify

After implementation and before final validation, perform a dedicated simplification pass.

Review the implementation for:

- dead code;
- unnecessary abstractions;
- avoidable indirection;
- duplicated logic;
- overly broad interfaces;
- complexity not justified by requirements or evidence.

Record what was simplified in the PR. If no simplification is warranted, record `No simplification needed` and briefly explain why.

Simplify is not permission to change scope or remove necessary safeguards. Trading invariants, deterministic risk controls, and reproducibility requirements take priority over cosmetic code reduction.

## Compound

Before final review, ask:

> What did this change teach us that a future agent should not have to rediscover?

Record one of the following in the PR:

1. `No reusable learning`.
2. A durable update to an existing source of truth such as an ADR, architecture/domain doc, plan, experiment record, or current-state memory.
3. A reusable solution note under `docs/solutions/` using `.ai/solution-template.md`.

Use solution notes for recurring problem/solution knowledge. Use ADRs for durable project decisions. Use `experiments/` for experiment-specific evidence and failed hypotheses.

Compound occurs before final formal review so every knowledge artifact created by the step is part of the reviewed diff.

## Formal review

Before merge, perform a review of the actual final diff. Do not review only the PR description.

The review must cover:

- correctness and acceptance criteria;
- meaningful tests and edge cases;
- look-ahead, survivorship, data leakage, and execution timing;
- deterministic risk controls and trading assumptions;
- architecture, complexity, maintainability, and duplication;
- whether the Simplify pass was sufficient;
- whether the Compound outcome captured reusable knowledge appropriately;
- English-only repository content;
- required documentation/memory updates;
- recoverable agent handoff state for non-trivial work;
- green CI and unresolved review threads.

The review outcome must be explicitly recorded as one of:

```text
PASS
CHANGES REQUESTED
BLOCKED
```

If the reviewer finds issues, fix them on the same branch and repeat the relevant Simplify, Validation, Compound, and Review stages. Merge only after `PASS`.

When the PR author and reviewer share the same GitHub identity, record the formal review as a review comment because GitHub does not provide an independent self-approval signal.

## Merge

The agent or engineer responsible for the PR owns finishing the lifecycle rather than leaving a merge-ready PR open indefinitely.

Merge only when:

- the design and acceptance criteria are satisfied;
- the Simplify and Compound stages are complete;
- formal review outcome is `PASS`;
- required CI is green;
- no unresolved review threads or known blockers remain;
- repository memory and documentation reflect the post-merge state.

Prefer squash merge. Use the Conventional Commit PR title as the squash commit title. Delete the source branch after merge when possible.

## Cross-session continuity

The user is not responsible for carrying technical context between AI sessions.

When repository/GitHub access is available, AI agents must:

1. inspect open PRs before starting a duplicate task;
2. read the latest automated `<!-- agent-handoff -->` comment for relevant PRs;
3. inspect the PR body, branch, diff, checks, active plan, reviews, and unresolved threads;
4. reconstruct state from repository/GitHub sources before asking the user for context;
5. run local handoff/context builders themselves when useful.

The complete protocol is in `docs/workflow/agent-session-handoff.md`.

## AI agents

AI coding agents follow the same process as humans and should execute it autonomously when the task and project decisions are clear:

1. Run the session bootstrap/resume protocol and continue matching in-flight work when present.
2. Read repository context and existing decisions.
3. Create a dedicated branch from the latest `main` only when a matching branch/PR does not already exist.
4. Write/update the design plan.
5. Open a Draft PR.
6. Implement on that branch.
7. Simplify the implementation.
8. Validate tests, lint, integration/backtest behavior, and research invariants.
9. Perform the Compound check and update durable knowledge when appropriate.
10. Finalize project memory and the active plan.
11. Mark the PR ready and perform a formal diff-based review.
12. Fix findings and repeat the relevant stages if necessary.
13. Merge after `PASS` and green CI.

Agents must not bypass review, leave a completed PR unmerged merely because they have write access, or ask the user to manually shuttle context that is available from repository/GitHub state. Ask for user input only when a material product, trading-risk, architecture, or scope decision cannot be safely inferred from existing project decisions.
