# EXP-0003 — Temporal Stability and Prospective Holdout Registration

Status: Active

## Goal

Measure whether the frozen v1 strategy behaves consistently across distinct historical calendar regimes without changing strategy, risk, universe, or execution assumptions, and preregister the first genuinely prospective holdout window.

EXP-0003 is a **historical temporal-stability diagnostic**. It is not presented as true out-of-sample validation because EXP-0001 and EXP-0002 already exposed aggregate results from the full 2021-01-01 through 2026-08-31 period.

## Research integrity rule

No historical subperiod already included in EXP-0001/EXP-0002 may be relabeled as unseen or held-out after the fact.

The project therefore separates:

1. **historical temporal stability** — rerun the frozen strategy independently on predefined calendar folds to reveal regime dependence;
2. **prospective holdout** — preregister a future start date before any data from that interval can be used for strategy decisions.

## Frozen v1 baseline

Use the same strategy and portfolio assumptions as EXP-0001:

- symbols: BTC-USD, SOL-USD, META, NVDA;
- benchmark/risk regime rules unchanged;
- initial equity: 5,000;
- risk per trade: 0.5%;
- max aggregate open risk: 2%;
- max concurrent positions: 4;
- max position notional: 25%;
- minimum Swing Score: 70;
- initial stop: 2 ATR;
- trailing stop: 2.5 ATR;
- long-only next-asset-open execution semantics;
- baseline execution costs from `config/execution-costs.yaml`.

No v1 strategy or risk parameter may be changed in response to EXP-0003.

## Historical folds

Run independent portfolio simulations with the same 5,000 initial equity and the same frozen assumptions for:

| Fold | Evaluation start | Evaluation end exclusive | Notes |
|---|---|---|---|
| 2021 | 2021-01-01 | 2022-01-01 | full calendar year |
| 2022 | 2022-01-01 | 2023-01-01 | full calendar year |
| 2023 | 2023-01-01 | 2024-01-01 | full calendar year |
| 2024 | 2024-01-01 | 2025-01-01 | full calendar year |
| 2025 | 2025-01-01 | 2026-01-01 | full calendar year |
| 2026-ytd | 2026-01-01 | 2026-09-01 | partial year matching prior experiments |

Every fold uses warm-up history beginning 2020-01-01 so rolling indicators and regime filters are initialized before evaluation.

A fold is independent for portfolio accounting: equity resets to 5,000 at each fold boundary. This makes fold-level behavior comparable and avoids one unusually strong prior year mechanically increasing later nominal risk budgets.

## Controlled market-data snapshot

All folds must use one provider snapshot downloaded once per required symbol through a snapshot downloader covering 2020-01-01 through 2026-09-01.

The snapshot downloader may return date slices requested by individual fold runs, but every slice must originate from the same in-memory source frame.

Record source SHA-256 digests and fail if fold runs do not resolve to the expected common source snapshot.

## Temporal-stability diagnostics

For each fold record at least:

- trade count;
- end equity and total return;
- CAGR / annualized return where meaningful;
- maximum drawdown;
- profit factor;
- expectancy in R;
- win rate;
- average winner R;
- average loser R;
- average holding period;
- average exposure;
- top-five-profit share;
- total modeled execution cost.

Aggregate diagnostics should include:

- number/fraction of folds with positive expectancy;
- number/fraction of folds with profit factor above 1;
- number/fraction of folds with positive total return;
- median and minimum fold expectancy;
- median profit factor;
- worst fold maximum drawdown;
- total closed trades across independent folds;
- trade-count-weighted expectancy across folds;
- whether 2025 and 2026-ytd remain weak when rerun independently.

Do not average CAGR across folds and present it as a portfolio CAGR. Fold metrics are diagnostics, not a synthetic chained investment result.

## Prospective holdout registration

Create a versioned protocol under:

`experiments/PROSPECTIVE-v1-holdout/protocol.yaml`

The protocol must be committed before the holdout begins and freeze:

- strategy version: v1;
- baseline source commit: `dbb45a8a3910298e3565a02758b835975308e88c`;
- universe: BTC-USD, SOL-USD, META, NVDA;
- all v1 risk/entry/exit parameters;
- baseline execution-cost model;
- prospective evaluation start: `2026-09-14`;
- minimum observation horizon: 24 calendar months;
- minimum closed trades before validation claims: 30;
- evaluation gate: both horizon and trade-count requirements must be satisfied;
- changes to strategy/risk parameters invalidate comparability and require a new prospective protocol/version.

Interim paper-trading/monitoring may be recorded, but interim outcomes must not be used to tune v1 while the holdout protocol is active.

## Deliverables

Add a lightweight temporal-stability runner that:

1. loads a versioned EXP-0003 configuration;
2. loads and freezes the EXP-0001 strategy/portfolio configuration;
3. builds one full-period market-data snapshot for assets and required benchmarks;
4. runs each historical fold independently through the existing experiment/backtest infrastructure;
5. verifies common source-data provenance;
6. aggregates fold metrics and stability diagnostics;
7. retains detailed per-fold artifacts in CI output;
8. writes strict JSON and a generated factual summary;
9. compares fold conclusions with the already-known EXP-0001 aggregate without claiming out-of-sample status.

Version:

`experiments/EXP-0003-temporal-stability/config.yaml`

Add a dedicated GitHub Actions workflow for the real-data run and artifact upload.

After inspecting the artifact, commit reviewed EXP-0003 results and interpretation.

## Hypotheses

This is primarily diagnostic rather than a pass/fail optimization gate.

Predeclared questions:

1. Is expectancy positive in at least four of the six calendar folds?
2. Is profit factor above 1 in at least four of six folds?
3. Are the known weak 2025 / 2026-ytd periods confirmed as weak when account state is reset at fold boundaries?
4. Is aggregate historical performance dependent on one or two calendar regimes?

A negative answer is valid evidence and must not trigger parameter tuning inside this PR.

## Non-goals

- Do not call historical folds true out-of-sample data.
- Do not optimize or select parameters per fold.
- Do not alter Swing Score thresholds or ATR settings.
- Do not change the universe.
- Do not broaden execution-cost scenarios; EXP-0002 already covers that dimension.
- Do not chain fold equity into a synthetic walk-forward return series.
- Do not interpret the prospective holdout before its preregistered gate is satisfied.
- Do not implement live or paper broker execution in this PR.

## Test plan

- unit-test snapshot slicing so every fold uses one provider download per symbol;
- unit-test fold config validation and non-overlap/order;
- unit-test aggregate stability diagnostics;
- unit-test that fold evaluation bars never precede fold start or reach fold end;
- unit-test strict JSON output;
- regression-test the frozen v1 config identity;
- run `pytest -q` and `ruff check src tests`;
- run EXP-0001 and EXP-0002 regression workflows when affected;
- execute EXP-0003 real-data workflow;
- download and inspect the generated artifact before committing conclusions.

## Simplify plan

Keep this as orchestration over `run_experiment` and the existing backtester. A sequential six-fold runner plus one shared historical snapshot is sufficient.

Do not introduce a generic ML cross-validation framework, training API, optimizer, experiment database, or distributed scheduler.

## Compound plan

Evaluate reusable lessons about:

- distinguishing retrospective temporal diagnostics from genuine held-out evidence;
- preregistering future evaluation windows before data becomes observable;
- resetting portfolio state at fold boundaries versus chaining performance;
- controlling one market-data snapshot across historical fold comparisons.

## Definition of done

EXP-0003 is complete only when:

- the design, runner, config, tests, workflow, and prospective protocol exist;
- all automated tests/lint/conventions pass;
- the real-data EXP-0003 workflow succeeds;
- the artifact is inspected;
- reviewed results and limitations are committed;
- project memory and roadmap are updated;
- Simplify and Compound are completed;
- the PR receives a formal `PASS` review;
- the PR is squash-merged into `main`.
