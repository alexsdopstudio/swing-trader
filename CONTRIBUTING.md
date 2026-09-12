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
- ADRs, plans, and AI memory files
- branch names
- commit messages
- pull request titles and descriptions

Market symbols, proper nouns, external source text, and raw data values are not translated when translation would change their meaning. Any explanation, annotation, metadata, or surrounding prose added by this project must still be written in English.

Human conversations outside the repository may use any language, but text committed to the repository must be English before review and merge.

## Required lifecycle

The default lifecycle for every non-trivial change is:

```text
Intake
  -> Dedicated branch
  -> Design
  -> Draft PR
  -> Implementation
  -> Validation
  -> Formal PR review
  -> Squash merge
```

Create the dedicated branch before committing the design plan so design and implementation remain in one auditable history. For non-trivial changes, create a design plan under `docs/plans/active/` using `.ai/design-template.md` before implementing production code. Open the PR as Draft once the design is clear enough to review, then implement the feature on the same branch and PR.

A PR is not complete when the code is written. It is complete only after validation, a formal diff-based `PASS` review, green required CI checks, updated project memory, and merge into `main`.

## Branches

Create one dedicated branch per logical change from the latest `main`.

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
5. List tests and validation performed.
6. Call out look-ahead, execution, risk, data-quality, overfitting, or reproducibility implications when applicable.
7. Update durable project memory (`AGENTS.md`, ADRs, plans, current state, strategy docs) when future agent behavior should change.
8. Keep all repository-facing text introduced by the PR in English.
9. Pass a formal diff-based review.
10. Pass all required CI checks before merge.

## Formal review

Before merge, perform a review of the actual diff. Do not review only the PR description.

The review must cover:

- correctness and acceptance criteria;
- meaningful tests and edge cases;
- look-ahead, survivorship, data leakage, and execution timing;
- deterministic risk controls and trading assumptions;
- architecture, complexity, maintainability, and duplication;
- English-only repository content;
- required documentation/memory updates;
- green CI and unresolved review threads.

The review outcome must be explicitly recorded as one of:

```text
PASS
CHANGES REQUESTED
BLOCKED
```

If the reviewer finds issues, fix them on the same branch and repeat the review. Merge only after `PASS`.

When the PR author and reviewer share the same GitHub identity, record the formal review as a review comment because GitHub does not provide an independent self-approval signal.

## Merge

The agent or engineer responsible for the PR owns finishing the lifecycle rather than leaving a merge-ready PR open indefinitely.

Merge only when:

- the design and acceptance criteria are satisfied;
- formal review outcome is `PASS`;
- required CI is green;
- no unresolved review threads or known blockers remain;
- repository memory and documentation reflect the post-merge state.

Prefer squash merge. Use the Conventional Commit PR title as the squash commit title. Delete the source branch after merge when possible.

## AI agents

AI coding agents follow the same process as humans and should execute it autonomously when the task and project decisions are clear:

1. Read repository context and existing decisions.
2. Create the dedicated branch from the latest `main`.
3. Write/update the design plan.
4. Open a Draft PR.
5. Implement and validate on that branch.
6. Update durable memory.
7. Mark the PR ready and perform a formal diff-based review.
8. Fix findings and re-review if necessary.
9. Merge after `PASS` and green CI.

Agents must not bypass review or leave a completed PR unmerged merely because they have write access. Ask for user input only when a material product, trading-risk, architecture, or scope decision cannot be safely inferred from existing project decisions.
