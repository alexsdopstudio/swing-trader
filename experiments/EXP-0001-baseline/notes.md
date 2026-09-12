# EXP-0001 — Cost-Aware Baseline Review

Status: Reviewed exploratory baseline

## Run provenance

- experiment: `EXP-0001`
- strategy: v1 long-only swing strategy
- code SHA that produced the artifact: `926ce69b6214b237866fbcff97e0de7a16ddff3d`
- GitHub Actions run: `34706655020`
- artifact id: `10302140885`
- artifact SHA-256: `6edcddf3341e34e3c3122177442b17e488bcb68d7780c7058990f6abc18b4bb6`
- data provider: yfinance adjusted daily bars
- evaluation window: 2021-01-01 through 2026-08-31
- warm-up begins: 2020-01-01
- initial equity: 5,000

The workflow artifact contained `results.json`, `trades.csv`, `equity.csv`, `resolved-config.yaml`, and the generated run summary. The durable repository record keeps the versioned configuration, reviewed results, provenance, and interpretation; the full trade/equity files can be regenerated from the recorded code/config/data provider assumptions.

## Headline result

The exploratory baseline is positive after the configured execution costs:

- ending equity: 6,958.52
- total return: 39.17%
- CAGR: 6.01%
- maximum drawdown: -4.25%
- Sharpe: 1.27
- Sortino: 2.16
- profit factor: 3.18
- expectancy: +1.05R per trade
- win rate: 46.15%
- average winner: +3.19R
- average loser: -0.79R
- trades: 65
- average holding period: 23.17 days
- average portfolio exposure: 6.04%
- top-five-profit share: 47.98%
- total modeled execution cost: 86.11
- total modeled commissions: 24.32

The primary exploratory hypothesis, positive cost-aware expectancy, is therefore supported in this specific historical sample.

## Contribution by asset

| Asset | Trades | Net PnL | Average R | Win rate | Modeled execution cost |
|---|---:|---:|---:|---:|---:|
| BTC-USD | 14 | 209.75 | 0.48R | 50.00% | 31.78 |
| SOL-USD | 14 | 912.82 | 2.35R | 71.43% | 18.49 |
| META | 16 | 189.75 | 0.37R | 31.25% | 17.02 |
| NVDA | 21 | 646.20 | 1.07R | 38.10% | 18.82 |

SOL-USD and NVDA produced about 79.6% of total portfolio net PnL. This is a meaningful concentration and prevents us from interpreting the aggregate result as broad evidence across the universe.

## Result by exit year

| Exit year | Trades | Net PnL | Average R | Win rate |
|---|---:|---:|---:|---:|
| 2021 | 21 | 651.92 | 1.19R | 57.14% |
| 2022 | 0 | 0.00 | n/a | n/a |
| 2023 | 11 | 802.20 | 2.50R | 63.64% |
| 2024 | 19 | 673.81 | 1.07R | 42.11% |
| 2025 | 11 | -95.37 | -0.24R | 27.27% |
| 2026 through August | 3 | -74.03 | -0.70R | 0.00% |

The absence of 2022 trades is consistent with the long-only market-regime filters suppressing entries during a broadly bearish period. More importantly, 2025 and the available 2026 sample are negative, which is direct evidence that the edge is not stable across all subperiods.

## Interpretation

This experiment is encouraging enough to justify further research, but it is not strategy validation.

Positive aspects:

- expectancy and profit factor are comfortably positive after modeled costs;
- winners are substantially larger than losers, which matches the intended trend-following payoff profile;
- maximum drawdown is modest in this sample;
- the strategy naturally avoided much of 2022 through its regime filters;
- execution friction did not eliminate the baseline edge under the current assumptions.

Reasons not to deploy or optimize yet:

- only 65 trades were observed, far below the project's desired evidence threshold for robust conclusions;
- average exposure is only about 6%, so the 6% CAGR reflects low capital utilization and should not be confused with a high-return production system;
- almost half of all winning PnL comes from the top five winners;
- SOL-USD and NVDA dominate portfolio profits;
- 2025 and 2026 are negative in the observed sample;
- the universe is narrow and consists of known surviving/high-profile assets, so selection and survivorship bias remain material concerns;
- the evaluation period is exploratory, not a held-out out-of-sample test;
- execution costs are linear assumptions rather than actual broker/exchange fills;
- historical data can be revised by the provider and is not snapshotted in this experiment.

## Decision

`CONTINUE RESEARCH — DO NOT DEPLOY`

Do not change the v1 parameters based on EXP-0001. The next research stages should test whether the result survives:

1. execution-cost sensitivity;
2. walk-forward / held-out evaluation;
3. parameter perturbation around breakout and ATR settings;
4. a broader, less selectively chosen universe;
5. comparison against simple passive/reference baselines.

A future failure in any of those stages is a valid result and should be preserved rather than tuned away.
