# Swing Trader — Agent Guide

## Mission

Build a robust, testable swing-trading research system. The objective is not to maximize historical returns; it is to find strategies that remain credible out-of-sample and under realistic execution assumptions.

## Read before changing code

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

## Development workflow

1. Read `.ai/current-state.md` and the relevant active plan.
2. Inspect existing implementation and tests before editing.
3. Make the smallest coherent change.
4. Run `pytest -q` and `ruff check src tests`.
5. Update documentation when architecture, strategy assumptions or decisions change.
6. Record meaningful research experiments under `experiments/`.

## Definition of done

A coding task is not done until tests and lint pass and the change is documented where future agents can discover it.
