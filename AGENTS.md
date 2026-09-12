# Swing Trader — Agent Guide

## Mission

Build a robust, testable swing-trading research system. The objective is not to maximize historical returns; it is to find strategies that remain credible out-of-sample and under realistic execution assumptions.

## Read before changing code

- `CONTRIBUTING.md`
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
- Never develop a feature directly on `main`.
- Every logical change must use a dedicated branch and pull request as defined in `CONTRIBUTING.md`.
- Commit subjects and PR titles must follow Conventional Commits.

## Development workflow

1. Read `CONTRIBUTING.md`, `.ai/current-state.md`, and the relevant active plan.
2. Start from the latest `main` and create a dedicated branch using an allowed prefix.
3. Inspect existing implementation and tests before editing.
4. Make the smallest coherent change using focused Conventional Commits.
5. Run `pytest -q` and `ruff check src tests`.
6. Update documentation when architecture, strategy assumptions or decisions change.
7. Record meaningful research experiments under `experiments/`.
8. Open a pull request into `main` using the repository PR template.
9. Do not merge until required CI checks are green and the change has been reviewed.
10. Prefer squash merge and delete the source branch after merge.

## Definition of done

A coding task is not done until tests and lint pass, the change is documented where future agents can discover it, and the work is represented by a reviewable pull request rather than a direct feature push to `main`.
