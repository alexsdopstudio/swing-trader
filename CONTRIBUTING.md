# Contributing

All changes to this repository follow a branch-and-pull-request workflow. Direct development on `main` is not part of the normal process.

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

Do not reuse branches for unrelated work. Delete the branch after merge.

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

PR titles use the same Conventional Commit format as commits. The title and PR description must be written in English. The title should describe the complete logical change because squash merge is the preferred merge strategy.

A PR should:

1. Cover one logical change.
2. Explain the motivation and implementation.
3. State trading/research assumptions affected by the change.
4. List tests performed.
5. Call out look-ahead, execution, risk, data-quality, or reproducibility implications when applicable.
6. Update durable project memory (`AGENTS.md`, ADRs, active plans, current state, strategy docs) when the decision changes future agent behavior.
7. Keep all repository-facing text introduced by the PR in English.
8. Pass all required CI checks before merge.

Prefer squash merge. Delete the source branch after merge.

## Pull request lifecycle

```text
main
  └── dedicated branch
        ├── focused Conventional Commits
        ├── tests + docs
        └── Pull Request
              ├── CI green
              ├── self-review / review
              └── squash merge → main
```

## AI agents

AI coding agents must follow the same workflow as humans:

1. Read `AGENTS.md` and relevant project memory.
2. Start from updated `main`.
3. Create a dedicated branch before editing.
4. Write all repository content in English.
5. Make Conventional Commits in English.
6. Open a PR in English; do not push the feature directly to `main`.
7. Leave the PR unmerged until CI is green and the change has been reviewed.

Agents must not bypass this workflow merely because they have write access to the repository.
