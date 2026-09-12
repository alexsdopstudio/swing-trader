# EXP-0002 — Execution-Cost Sensitivity Review

Status: Reviewed sensitivity experiment

## Run provenance

- experiment: `EXP-0002`
- producer code SHA: `36475d98ce36e4b1fef533a540be0d9b03c5bcd6`
- GitHub Actions run: `34708027981`
- artifact id: `10302117801`
- artifact SHA-256: `3041370a940bf44c6448c02b9a99acb1594d5f514c8101422bbcac898a1e67b7`
- base experiment: `EXP-0001`
- base strategy: v1 long-only swing strategy
- evaluation window: 2021-01-01 through 2026-08-31
- warm-up start: 2020-01-01
- initial equity: 5,000

All four scenarios reused one shared in-memory provider snapshot. The run required only five provider downloads: BTC-USD, SOL-USD, META, NVDA, and QQQ. Source-data SHA-256 digests were identical across low, baseline, high, and stress scenarios.

## Cost scenarios

| Scenario | Multiplier | Equity commission / spread / slippage | Crypto commission / spread / slippage |
|---|---:|---|---|
| low | 0.5x | 0.5 / 2.5 / 2.5 bps | 5 / 5 / 5 bps |
| baseline | 1.0x | 1 / 5 / 5 bps | 10 / 10 / 10 bps |
| high | 2.0x | 2 / 10 / 10 bps | 20 / 20 / 20 bps |
| stress | 4.0x | 4 / 20 / 20 bps | 40 / 40 / 40 bps |

Spread is the configured full spread and slippage is per side. These remain research assumptions rather than broker or exchange quotes.

## Headline result

| Scenario | Trades | End equity | CAGR | Max DD | Profit factor | Expectancy | Modeled execution cost |
|---|---:|---:|---:|---:|---:|---:|---:|
| low 0.5x | 65 | 7,025.91 | 6.19% | -4.27% | 3.26 | +1.08R | 43.99 |
| baseline 1.0x | 65 | 6,958.52 | 6.01% | -4.25% | 3.18 | +1.05R | 86.11 |
| high 2.0x | 65 | 6,830.92 | 5.67% | -4.21% | 3.03 | +0.99R | 165.24 |
| stress 4.0x | 66 | 6,509.32 | 4.77% | -4.44% | 2.62 | +0.82R | 308.00 |

The primary EXP-0002 robustness question is supported in this historical sample: expectancy remains positive at 2.0x baseline costs. The stress scenario also remains positive at 4.0x costs.

## Degradation versus baseline

At 2.0x costs:

- ending equity decreases by about 127.60;
- CAGR decreases by about 0.35 percentage points;
- profit factor decreases from 3.18 to 3.03;
- expectancy decreases from +1.05R to +0.99R;
- modeled execution cost increases from 86.11 to 165.24.

At 4.0x costs:

- ending equity decreases by about 449.20;
- CAGR decreases by about 1.24 percentage points;
- profit factor decreases from 3.18 to 2.62;
- expectancy decreases from +1.05R to +0.82R;
- modeled execution cost increases from 86.11 to 308.00.

Profit factor, CAGR, and ending equity all degrade as expected when costs increase. The deterioration is meaningful but does not eliminate the positive historical expectancy in this sample.

## Path dependence

Execution costs are part of the trading path, not merely a final PnL subtraction.

The stress scenario produced 66 trades instead of 65. Higher friction changes executed entry prices, cost-adjusted sizing, stop/risk accounting, cash usage, exit timing, and therefore later portfolio admission. In this run, those changes allowed one additional trade under the stress scenario.

This is why scenario results cannot be reproduced correctly by taking one frictionless or baseline trade ledger and subtracting a larger fixed cost afterward.

## EXP-0001 provider revision check

The current 1.0x baseline reproduces the recorded EXP-0001 metrics to effectively numerical precision, including the same 65 trades and almost identical equity, CAGR, drawdown, profit factor, and expectancy.

However, source-data digests no longer match the original EXP-0001 provider snapshot for:

- META;
- NVDA;
- QQQ.

BTC-USD and SOL-USD digests are unchanged.

This confirms that Yahoo historical adjusted data can be revised even when the practical strategy result changes only negligibly. The digest mismatch is therefore retained as research provenance rather than silently replacing the original EXP-0001 record.

## Interpretation

EXP-0002 increases confidence that the positive EXP-0001 result is not dependent on one narrow execution-cost assumption. It does **not** validate the strategy.

Reasons the project must not move to deployment yet:

- all scenarios use the same exploratory historical window;
- only about 65 trades are observed;
- the universe remains narrow and survivor/high-profile selected;
- EXP-0001 already showed concentration in SOL-USD and NVDA and in a few large winners;
- 2025 and the available 2026 baseline subperiods were negative;
- no held-out or walk-forward test has been completed;
- no parameter-neighborhood robustness test has been completed;
- no broad-universe or passive/reference comparison has been completed;
- linear cost multipliers are stress assumptions, not a substitute for real broker/exchange execution data.

## Decision

`COST ROBUSTNESS SUPPORTED IN-SAMPLE — CONTINUE RESEARCH — DO NOT DEPLOY`

Do not change v1 parameters based on EXP-0002.

The next research stage should be a held-out / walk-forward evaluation with the v1 strategy and current risk rules frozen. Parameter robustness should follow as a separate experiment so held-out evidence is not contaminated by tuning.
