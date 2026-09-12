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
- `docs/solutions/README.md`

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
- Every non-trivial implementation receives an explicit Simplify pass before final validation.
- Every PR performs a Compound check before final review: capture reusable learning or explicitly record `No reusable learning`.
- Every PR requires a formal diff-based review before merge.
- The agent responsible for a PR also owns completing the merge after a `PASS` review and green CI.

## Development workflow

1. Read `CONTRIBUTING.md`, `docs/workflow/development-lifecycle.md`, `.ai/current-state.md`, and relevant project memory.
2. Start from the latest `main` and create a dedicated branch using an allowed prefix and an English kebab-case name.
3. For non-trivial work, create or update a design plan under `docs/plans/active/` using `.ai/design-template.md`.
4. Open a Draft PR once the design is clear enough to review.
5. Inspect existing implementation and tests before editing production code.
6. Implement the approved design using focused Conventional Commits in English.
7. Simplify the implementation: remove accidental complexity, duplication, dead code, unnecessary abstractions, and unjustified indirection.
8. Run `pytest -q`, `ruff check src tests`, and any relevant integration/backtest validation.
9. Perform the Compound check. Update existing durable memory or create a solution note under `docs/solutions/` when a reusable lesson should not be rediscovered. It is valid to record `No reusable learning`.
10. Update documentation, ADRs, experiments, `.ai/current-state.md`, and the active plan for the post-merge state.
11. Mark the PR ready for review only after implementation, Simplify, Validation, and Compound are complete.
12. Perform a formal diff-based PR review covering correctness, trading/research integrity, architecture, tests, simplification, compound output, repository hygiene, and unresolved threads.
13. If review finds issues, fix them on the same branch and repeat the relevant Simplify, Validation, Compound, and Review stages.
14. Merge only after review outcome is `PASS` and all required CI checks are green.
15. Prefer squash merge using the Conventional Commit PR title and delete the source branch when possible.

## Definition of done

A task is not done until the design is documented where required, implementation and tests are complete, accidental complexity has been reviewed, reusable learnings have been captured or explicitly ruled out, repository content is in English, the final diff has received a formal `PASS` review, required CI is green, durable memory is current, and the PR has been merged into `main`.
