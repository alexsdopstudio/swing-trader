# Swing Trader — Agent Guide

## Mission

Build a robust, testable swing-trading research system. The objective is not to maximize historical returns; it is to find strategies that remain credible out-of-sample and under realistic execution assumptions.

## Session bootstrap and resume

Before opening new work, reconstruct repository state autonomously.

When GitHub access is available:

1. Read this file from `main`.
2. Inspect open pull requests before creating a new branch.
3. For candidate in-flight work, read the latest PR comment containing `<!-- agent-handoff -->`.
4. Inspect the PR body, head branch, active plan, final diff, current checks, and unresolved review threads.
5. Continue the existing branch/PR when it matches the requested task; do not create a duplicate implementation PR.
6. Reconstruct missing context from repository and GitHub state before asking the user anything.

When working from a local clone, agents may run `python scripts/build_handoff.py` and `python scripts/build_context.py` themselves. These are agent operations, not user prerequisites.

Do not ask the user to copy chat history, paste a handoff, run bootstrap commands, or manually shuttle context when repository/GitHub access is available. Ask only for a genuinely unresolved product, trading-risk, architecture, or scope decision that cannot be inferred safely from project memory.

See `docs/workflow/agent-session-handoff.md` for the complete cross-agent resume protocol.

## Read before changing code

- `CONTRIBUTING.md`
- `docs/workflow/development-lifecycle.md`
- `docs/workflow/agent-session-handoff.md`
- `ARCHITECTURE.md`
- `docs/product/strategy-v1.md`
- `docs/domain/risk-model.md`
- `.ai/current-state.md`
- generated `.ai/handoff.md` when present
- `docs/roadmap.md`
- `docs/decisions/`
- `docs/plans/active/`
- `docs/solutions/README.md`
- `knowledge/README.md` and `knowledge/registry.json` when external research, news/catalyst context, provenance, or agent retrieval is relevant

## Non-negotiable rules

- Never introduce look-ahead bias.
- A signal calculated from day T close data cannot execute before T+1 open.
- Risk controls are deterministic code; an LLM must never override them.
- Strategy changes require tests.
- Prefer simple rules unless complexity improves out-of-sample evidence.
- Do not tune parameters only to improve one historical backtest.
- Include transaction costs and slippage before treating results as decision-useful.
- Keep research results reproducible: config, period, universe, code revision and metrics must be recorded.
- Treat durable external sources, time-bounded news observations, curated interpretation, project experiments, operational observations, and generated indexes as distinct evidence classes. Do not promote literature or news into project validation, and do not treat generated registries as editable sources of truth.
- External knowledge or news may motivate research or provide context, but must never directly override deterministic strategy, execution, sizing, stop, or portfolio-risk rules.
- All version-controlled repository content must be written in English, including comments, docstrings, docs, experiment notes, branch names, commit messages, and pull request text.
- Never develop a feature directly on `main`.
- Every logical change must use a dedicated branch and pull request as defined in `CONTRIBUTING.md`.
- Non-trivial changes require a design plan before production implementation.
- Commit subjects and PR titles must follow Conventional Commits.
- Every non-trivial implementation receives an explicit Simplify pass before final validation.
- Every PR performs a Compound check before final review: capture reusable learning or explicitly record `No reusable learning`.
- Every PR requires a formal diff-based review before merge.
- The agent responsible for a PR also owns completing the merge after a `PASS` review and green CI.
- Active work must remain recoverable across agent/session boundaries through repository state and the automated PR handoff.

## Development workflow

1. Run the session bootstrap/resume protocol above and continue existing in-flight work when applicable.
2. Read `CONTRIBUTING.md`, `docs/workflow/development-lifecycle.md`, `.ai/current-state.md`, and relevant project memory.
3. Start from the latest `main` and create a dedicated branch using an allowed prefix and an English kebab-case name only when no matching in-flight PR already exists.
4. For non-trivial work, create or update a design plan under `docs/plans/active/` using `.ai/design-template.md`.
5. Open a Draft PR once the design is clear enough to review.
6. Inspect existing implementation and tests before editing production code.
7. Implement the approved design using focused Conventional Commits in English.
8. Simplify the implementation: remove accidental complexity, duplication, dead code, unnecessary abstractions, and unjustified indirection.
9. Run `pytest -q`, `ruff check src tests`, and any relevant integration/backtest validation.
10. Perform the Compound check. Update existing durable memory or create a solution note under `docs/solutions/` when a reusable lesson should not be rediscovered. It is valid to record `No reusable learning`.
11. Update documentation, ADRs, experiments, `.ai/current-state.md`, and the active plan for the post-merge state.
12. Mark the PR ready for review only after implementation, Simplify, Validation, and Compound are complete.
13. Perform a formal diff-based PR review covering correctness, trading/research integrity, architecture, tests, simplification, compound output, repository hygiene, and unresolved threads.
14. If review finds issues, fix them on the same branch and repeat the relevant Simplify, Validation, Compound, and Review stages.
15. Merge only after review outcome is `PASS` and all required CI checks are green.
16. Prefer squash merge using the Conventional Commit PR title and delete the source branch when possible.

## Definition of done

A task is not done until the design is documented where required, implementation and tests are complete, accidental complexity has been reviewed, reusable learnings have been captured or explicitly ruled out, repository content is in English, the final diff has received a formal `PASS` review, required CI is green, durable memory is current, automated handoff state is recoverable, and the PR has been merged into `main`.
