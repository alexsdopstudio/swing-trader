# EXP-0001 — Cost-Aware Baseline

Status: Draft

## Goal

Create the first reproducible real-data portfolio experiment for the v1 swing strategy using the cost-aware shared-account backtester.

This is an exploratory baseline, not out-of-sample validation and not evidence that the strategy is deployable.

## Research question

Does the current v1 long-only swing strategy show a positive cost-aware baseline on a mixed crypto/equity portfolio before walk-forward testing and parameter robustness analysis?

## Universe

- BTC-USD
- SOL-USD
- META
- NVDA

Benchmarks remain those defined by the repository strategy:

- BTC-USD for crypto relative strength/regime;
- QQQ for US equities relative strength/regime.

## Time windows

- warm-up download start: `2020-01-01`
- evaluation start: `2021-01-01`
- evaluation end: `2026-09-01` (exclusive in the data provider request)

Indicators and score history are calculated using the warm-up period, but portfolio trades and reported metrics begin only at the evaluation start.

## Capital and strategy configuration

- initial equity: 5,000
- risk per trade: 0.5% of equity
- max aggregate open risk: 2% of equity
- max concurrent positions: 4
- max position notional: 25% of equity
- minimum Swing Score: 70
- initial stop: 2 ATR
- trailing stop: 2.5 ATR
- next-asset-open execution
- long-only

Execution costs are loaded from `config/execution-costs.yaml` and must be copied into the resolved experiment metadata.

## Data source

Use the repository's current `yfinance` daily adjusted-data adapter. Record the actual first/last observation and row count for every asset and benchmark in the experiment output.

The experiment must fail loudly if required data is missing rather than silently dropping a requested symbol.

## Hypotheses

Primary exploratory hypothesis:

- cost-aware expectancy in R is greater than 0.

Supporting diagnostics:

- profit factor greater than 1;
- trade count large enough to characterize the baseline;
- maximum drawdown is reported and inspected rather than optimized away;
- top-five-profit share is reported to identify dependence on a small number of trend trades;
- results are not called robust until cost sensitivity, walk-forward testing, and parameter perturbation are complete.

## Deliverables

Add a reusable experiment runner that reads a versioned YAML configuration and writes deterministic research artifacts:

- `results.json` — experiment metadata, code SHA, resolved assumptions, data coverage, metrics and summary diagnostics;
- `trades.csv` — realized trade ledger;
- `equity.csv` — equity, exposure and open-position curves;
- `notes.md` — machine-generated factual run summary with an explicit warning that interpretation is pending review.

Add `experiments/EXP-0001-baseline/config.yaml` as the immutable experiment specification.

Run EXP-0001 in GitHub Actions and upload the generated directory as an artifact. After inspecting that artifact, commit the reviewed result files under the experiment directory so the repository becomes the durable research record.

## Reproducibility requirements

The result must record:

- experiment id and name;
- strategy/version label;
- requested universe;
- warm-up/evaluation dates;
- data provider;
- actual data coverage per symbol;
- code commit SHA;
- portfolio parameters;
- execution-cost assumptions;
- key metrics;
- trade count and exit-reason counts;
- aggregate fees and execution cost;
- top-five-profit share.

JSON output must use `null` for undefined/non-finite metrics instead of non-standard `NaN`/`Infinity` values.

## Non-goals

- No parameter optimization.
- No changing strategy thresholds in response to results.
- No walk-forward split in this experiment.
- No comparison shopping across many universes.
- No AI/news/catalyst overlays.
- No live or paper execution.
- No claim that the baseline execution-cost assumptions equal a specific broker or exchange.

## Test plan

- unit-test warm-up/evaluation slicing so pre-evaluation bars cannot appear in portfolio output;
- unit-test strict JSON normalization for NaN/Infinity;
- unit-test experiment artifact serialization from a synthetic backtest result;
- test config validation and missing-symbol rejection;
- run `pytest -q` and `ruff check src tests`;
- execute the real-data experiment in GitHub Actions and inspect the generated artifact before committing results.

## Simplify plan

Keep the runner as orchestration around existing data, indicators, scoring, portfolio and metrics modules. Do not build a generic experiment framework, database, registry service or plugin system for one experiment.

## Compound plan

Potential reusable learning to evaluate after the run:

- warm-up history must be separated explicitly from evaluation history in any time-series experiment;
- experiment outputs should preserve both requested windows and actual per-symbol data coverage.

Only capture these as solution memory if implementation/run experience confirms they are broadly reusable.

## Definition of done

EXP-0001 is complete only when the versioned runner/config exist, unit tests and lint pass, the GitHub Actions real-data run succeeds, generated artifacts are inspected, reviewed results are committed under `experiments/EXP-0001-baseline/`, the final PR receives a formal `PASS` review, and the PR is squash-merged into `main`.
