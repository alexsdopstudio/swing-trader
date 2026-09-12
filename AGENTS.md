# Swing Trader — Agent Guide

## Mission

Build a robust, testable swing-trading research system. The objective is not to maximize historical returns; it is to find strategies that remain credible out-of-sample and under realistic execution assumptions.

## Read before changing code

- `CONTRIBUTING.md`
- `docs/workflow/development-lifecycle.md`
- `ARCHITECTURE.md`
- `docs/product/strategy-v1.md`
- `docs/domain/risk-model.md`
- `.ai/current-state.md`
- `docs/roadmap.md`
- `docs/decisions/`
- `docs/plans/active/`

## Non-negotiable rules

- Never introduce look-ahead bias.
- A signal calculated from day T close data cannot execute before T+1 open.
- Risk controls are deterministic code; an LLM must never override them.
- Strategy changes require tests.
- Prefer simple rules unless complexity improves out-of-sample evidence.
- Do not tune parameters only to improve one historical backtest.
- Include transaction costs and slippage before treating results as decision-useful.
- Keep research results reproducible: config, period, universe, code revision and metrics must be recorded.
- All version-controlled repository content must be written in English, including comments, docstrings, docs, experiment notes, branch names, commit messages, and pull request text.
- Never develop a feature directly on `main`.
- Every logical change must use a dedicated branch and pull request as defined in `CONTRIBUTING.md`.
- Non-trivial changes require a design plan before production implementation.
- Commit subjects and PR titles must follow Conventional Commits.
- Every PR requires a formal diff-based review before merge.
- The agent responsible for a PR also owns completing the merge after a `PASS` review and green CI.

## Development workflow

1. Read `CONTRIBUTING.md`, `docs/workflow/development-lifecycle.md`, `.ai/current-state.md`, and relevant project memory.
2. Start from the latest `main` and create a dedicated branch using an allowed prefix and an English kebab-case name.
3. For non-trivial work, create or update a design plan under `docs/plans/active/` using `.ai/design-template.md`.
4. Open a Draft PR once the design is clear enough to review.
5. Inspect existing implementation and tests before editing production code.
6. Implement the approved design using focused Conventional Commits in English.
7. Run `pytest -q`, `ruff check src tests`, and any relevant integration/backtest validation.
8. Update documentation, ADRs, experiments, and `.ai/current-state.md` when durable knowledge changes.
9. Finalize the plan and mark the PR ready for review.
10. Perform a formal diff-based PR review covering correctness, trading/research integrity, architecture, tests, repository hygiene, and unresolved threads.
11. If review finds issues, fix them on the same branch and repeat review.
12. Merge only after review outcome is `PASS` and all required CI checks are green.
13. Prefer squash merge using the Conventional Commit PR title and delete the source branch when possible.

## Definition of done

A task is not done until the design is documented where required, implementation and tests are complete, repository content is in English, the PR has received a formal `PASS` review, required CI is green, durable memory is current, and the PR has been merged into `main`.