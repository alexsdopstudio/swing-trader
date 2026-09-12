# EXP-0002 — Execution-Cost Sensitivity

Status: Draft

## Goal

Test whether the encouraging EXP-0001 baseline survives materially different execution-cost assumptions without changing any v1 strategy, portfolio, universe, or date parameter.

This is a sensitivity experiment, not strategy optimization and not deployment validation.

## Research question

How sensitive are the EXP-0001 portfolio results to proportionally lower and higher commission, spread, and slippage assumptions when every scenario uses the same downloaded market-data snapshot and the same strategy parameters?

## Frozen strategy baseline

EXP-0002 must inherit the research configuration from:

`experiments/EXP-0001-baseline/config.yaml`

The following are frozen across all scenarios:

- symbols: BTC-USD, SOL-USD, META, NVDA;
- warm-up start: 2020-01-01;
- evaluation start: 2021-01-01;
- evaluation end: 2026-09-01 exclusive;
- initial equity: 5,000;
- risk per trade: 0.5%;
- max aggregate open risk: 2%;
- max concurrent positions: 4;
- max position notional: 25%;
- minimum Swing Score: 70;
- initial stop: 2 ATR;
- trailing stop: 2.5 ATR;
- long-only next-asset-open execution semantics;
- benchmark and regime rules.

No strategy or portfolio parameter may be changed after observing EXP-0002 results.

## Cost scenarios

Use `config/execution-costs.yaml` as the baseline cost shape and multiply every configured commission, full-spread, and per-side slippage value by one scalar per scenario.

| Scenario | Multiplier | Purpose |
|---|---:|---|
| low | 0.5x | optimistic but still non-zero friction |
| baseline | 1.0x | reproduce current research assumptions |
| high | 2.0x | materially worse execution |
| stress | 4.0x | adverse stress case |

The multipliers are research stress parameters, not broker/exchange quotes.

Scaling all components together is intentionally simple for EXP-0002. Separate commission/spread/slippage sensitivity can be tested later if the aggregate result warrants it.

## Data consistency requirement

All scenarios must use the same in-memory downloaded OHLCV snapshot during one experiment run.

The sensitivity runner should cache each required provider download once and reuse the same frame for every scenario. The final result must verify that source-data SHA-256 digests are identical across scenarios.

This prevents a provider refresh between scenarios from being misinterpreted as cost sensitivity.

## Hypotheses

Primary robustness question:

- expectancy in R should remain positive at the `high` 2.0x scenario.

Stress diagnostic:

- record whether expectancy remains positive at 4.0x, but do not require it for the experiment to be considered methodologically successful.

Additional diagnostics:

- profit factor should degrade monotonically or approximately monotonically as costs rise;
- CAGR and ending equity should not improve materially as costs rise;
- total modeled execution cost should increase with the multiplier;
- trade count may change because cost-aware sizing and cash/risk constraints can alter portfolio admission, so scenario trade-count differences must be reported rather than assumed to be invariant;
- maximum drawdown must be recorded for every scenario;
- the experiment must remain valid even if the economic result is negative.

## Deliverables

Add a lightweight cost-sensitivity runner that:

1. loads the frozen EXP-0001 experiment config;
2. loads baseline execution-cost assumptions;
3. downloads each required symbol once through a shared cache;
4. scales execution-cost models for each scenario;
5. invokes the existing experiment/backtest infrastructure for every scenario;
6. verifies common source-data digests;
7. writes an aggregate `results.json` with scenario metrics, resolved costs, deltas versus baseline, runtime provenance, and data digests;
8. retains per-scenario detailed experiment artifacts under the generated CI artifact;
9. writes a factual generated summary for review.

Version `experiments/EXP-0002-cost-sensitivity/config.yaml` as the immutable sensitivity specification.

Add a dedicated GitHub Actions workflow that runs EXP-0002 on real data and uploads the complete generated directory for inspection.

After artifact inspection, commit the reviewed aggregate results and interpretation under `experiments/EXP-0002-cost-sensitivity/`.

## Aggregate metrics

For every scenario record at least:

- execution-cost multiplier;
- resolved equity and crypto commission/spread/slippage assumptions;
- trade count;
- end equity;
- total return;
- CAGR;
- max drawdown;
- Sharpe;
- Sortino;
- profit factor;
- expectancy in R;
- win rate;
- average winner R;
- average loser R;
- average holding period;
- average exposure;
- top-five-profit share;
- total fees;
- total modeled execution cost.

Also compute baseline-relative deltas for:

- end equity;
- CAGR;
- profit factor;
- expectancy R;
- max drawdown;
- total execution cost;
- trade count.

## Reproducibility requirements

The aggregate result must record:

- EXP-0002 id and name;
- frozen base experiment config path;
- code commit SHA;
- runtime/package versions;
- scenario definitions;
- actual source coverage;
- source-series SHA-256 digests;
- baseline execution-cost file identity/content digest;
- scenario metrics and deltas;
- whether all scenarios used identical market-data digests.

JSON output must remain strict and contain no non-standard NaN/Infinity values.

## Non-goals

- No strategy parameter optimization.
- No changes to Swing Score thresholds.
- No changes to stop/trailing parameters.
- No broader universe in this experiment.
- No walk-forward split.
- No passive benchmark comparison yet.
- No broker-specific fee schedule modeling.
- No nonlinear market-impact model.
- No separate one-factor-at-a-time decomposition of commission vs spread vs slippage.
- No live or paper trading decision.

## Test plan

- unit-test execution-cost model scaling;
- unit-test the shared downloader cache so repeated scenario requests do not redownload the same symbol;
- unit-test scenario aggregation and baseline-relative deltas;
- unit-test detection of mismatched source-data digests across scenarios;
- unit-test strict JSON output;
- run `pytest -q` and `ruff check src tests`;
- execute EXP-0002 in GitHub Actions against real data;
- download and inspect the artifact before committing reviewed results.

## Simplify plan

Keep EXP-0002 as orchestration around the existing experiment runner. Do not create a generic parameter-sweep framework, distributed job system, database, optimization engine, or strategy registry.

A four-scenario sequential run with one shared data cache is sufficient.

## Compound plan

Evaluate whether the run confirms reusable research lessons about:

- sensitivity scenarios sharing an identical market-data snapshot;
- distinguishing strategy robustness from execution-model assumptions;
- treating scenario-induced trade-count changes as part of the model rather than an error.

Create solution memory only for broadly reusable findings.

## Definition of done

EXP-0002 is complete only when:

- the runner and versioned config exist;
- all automated tests and lint pass;
- the real-data GitHub Actions run succeeds;
- the generated artifact is inspected;
- reviewed aggregate results and conclusions are committed;
- Simplify and Compound are completed;
- the final PR receives a formal `PASS` review;
- the PR is squash-merged into `main`.
