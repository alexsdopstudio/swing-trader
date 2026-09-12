# EXP-0002 — Execution-Cost Sensitivity

Status: Completed

## Goal

Test whether the positive EXP-0001 baseline survives materially different execution-cost assumptions without changing any v1 strategy, portfolio, universe, or date parameter.

EXP-0002 was a sensitivity experiment, not strategy optimization and not deployment validation.

## Frozen baseline

The experiment inherited `experiments/EXP-0001-baseline/config.yaml` unchanged for:

- BTC-USD, SOL-USD, META, and NVDA;
- warm-up/evaluation dates;
- initial equity;
- risk per trade;
- max aggregate open risk;
- max concurrent positions;
- max position notional;
- Swing Score threshold;
- ATR stop and trailing-stop parameters;
- long-only next-asset-open execution;
- benchmark and regime rules.

No strategy or portfolio parameter was changed after observing the result.

## Cost scenarios

`config/execution-costs.yaml` was scaled uniformly across commission, full spread, and per-side slippage:

| Scenario | Multiplier |
|---|---:|
| low | 0.5x |
| baseline | 1.0x |
| high | 2.0x |
| stress | 4.0x |

All four scenarios reused one shared in-memory market-data snapshot.

## Implementation outcome

Added:

- `scale_execution_cost_models` for deterministic basis-point scaling;
- a shared provider-download cache;
- `swing-cost-sensitivity` CLI;
- an EXP-0002 sensitivity orchestrator that reuses the existing experiment runner;
- source-digest equality checks across scenarios;
- aggregate scenario metrics and baseline-relative deltas;
- a dedicated GitHub Actions real-data workflow;
- unit tests for cost scaling, shared downloads, digest consistency, config validation, and metric deltas.

The design intentionally did not introduce a generic sweep framework, optimizer, database, distributed runner, or duplicate backtest engine.

## Producer run

- code SHA: `36475d98ce36e4b1fef533a540be0d9b03c5bcd6`
- GitHub Actions run: `34708027981`
- artifact id: `10302117801`
- artifact SHA-256: `3041370a940bf44c6448c02b9a99acb1594d5f514c8101422bbcac898a1e67b7`
- shared provider downloads: 5
- market-data digests identical across all four scenarios: yes

## Research result

| Scenario | Trades | CAGR | Max DD | Profit factor | Expectancy |
|---|---:|---:|---:|---:|---:|
| low 0.5x | 65 | 6.19% | -4.27% | 3.26 | +1.08R |
| baseline 1.0x | 65 | 6.01% | -4.25% | 3.18 | +1.05R |
| high 2.0x | 65 | 5.67% | -4.21% | 3.03 | +0.99R |
| stress 4.0x | 66 | 4.77% | -4.44% | 2.62 | +0.82R |

The primary robustness question was supported: expectancy remained positive at 2.0x baseline costs. It also remained positive under the 4.0x stress scenario.

Decision: `COST ROBUSTNESS SUPPORTED IN-SAMPLE — CONTINUE RESEARCH — DO NOT DEPLOY`.

## Provider revision observation

Compared with the durable EXP-0001 record, current Yahoo source digests changed for META, NVDA, and QQQ while BTC-USD and SOL-USD remained unchanged.

The current 1.0x baseline nevertheless reproduced EXP-0001 metrics to effectively numerical precision. The digest mismatch remains recorded because provider-history revisions are part of experiment provenance.

## Simplify outcome

The final implementation remained a four-scenario sequential orchestration over the existing experiment runner. No additional abstraction was justified.

## Compound outcome

EXP-0002 confirmed two reusable lessons:

1. sensitivity scenarios must reuse one controlled market-data snapshot so provider revisions cannot contaminate the comparison;
2. cost sensitivity is path-dependent when friction participates in sizing, stops, cash, and portfolio risk, so higher costs can legitimately change trade count and timing.

These lessons are recorded in:

`docs/solutions/trading-research/control-inputs-in-sensitivity-experiments.md`

## Next research step

Run a held-out / walk-forward evaluation with v1 strategy and risk parameters frozen. Do not tune parameters before recording that evidence. Parameter-neighborhood robustness should follow as a separate experiment.
