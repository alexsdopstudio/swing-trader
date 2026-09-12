# EXP-0006 — Configured Universe Breadth Review

Status: Reviewed retrospective universe-breadth diagnostic

## Research integrity

EXP-0006 does **not** claim out-of-sample validation. The 2021-01-01 through 2026-08-31 history was already observable before this study.

The broader universe was not selected from EXP-0006 results. It is exactly the 11-asset list already versioned in `config/universe.yaml` before this experiment: BTC-USD, ETH-USD, SOL-USD, META, NVDA, MSFT, AAPL, AMZN, GOOGL, AVGO, and TSLA. The four-symbol EXP-0001 subset was rerun on the same provider snapshot as a control.

Frozen v1 strategy, risk, execution-cost, benchmark, and evaluation settings were unchanged.

## Run provenance

- experiment: `EXP-0006`
- producer code SHA: `ba7340405f6a27dd092c47447147f64db955fa82`
- GitHub Actions run: `34715353773`
- artifact id: `10304203946`
- artifact SHA-256: `c08bebb910dcdf98e60e8b4b0fabb2d984dd4b8ce945d6d4e669f5e85b6960c6`
- runtime: Python 3.12.14, NumPy 2.5.3, pandas 3.0.5, PyYAML 6.0.3, yfinance 1.7.0
- shared provider downloads: 12 total, covering the 11 assets plus QQQ
- overlapping control/expanded source digests: identical

## Headline comparison

| Path | Return | CAGR | Max DD | Expectancy | Profit factor | Trades | Avg exposure |
|---|---:|---:|---:|---:|---:|---:|---:|
| 4-symbol control | +39.17% | +6.01% | -4.25% | +1.05R | 3.18 | 65 | 6.04% |
| 11-symbol configured universe | +39.98% | +6.12% | -5.13% | +0.49R | 2.04 | 141 | 14.98% |

The expanded path retained positive aggregate economics and produced slightly higher total return/CAGR, but it did so with materially more exposure and a larger drawdown while expectancy and profit factor were substantially lower. EXP-0006 therefore supports contribution breadth, not superiority of the expanded portfolio.

## Breadth criteria

All preregistered criteria passed:

- expanded path was joint-positive;
- the seven added symbols produced +514.76 aggregate realized net PnL;
- 8 of 11 symbols were positive net-PnL contributors, above the minimum of 4;
- 5 of 7 added symbols were positive contributors, above the minimum of 2;
- positive contributors included both crypto and equities;
- SOL-USD was the largest positive contributor at 30.58% of summed positive symbol PnL, below the 60% concentration ceiling;
- the four-symbol control remained joint-positive and reproduced durable EXP-0001 within every preregistered provider-revision tolerance.

## Expanded-universe contribution

| Symbol | Class | Trades | Net PnL | Expectancy R | Profit factor |
|---|---|---:|---:|---:|---:|
| BTC-USD | crypto | 10 | -12.47 | +0.03 | 0.92 |
| ETH-USD | crypto | 15 | +122.50 | +0.33 | 1.94 |
| SOL-USD | crypto | 12 | +684.37 | +1.95 | 11.48 |
| META | equity | 13 | +273.81 | +0.66 | 2.36 |
| NVDA | equity | 18 | +538.49 | +1.03 | 2.85 |
| MSFT | equity | 7 | +196.46 | +0.88 | 7.58 |
| AAPL | equity | 10 | +28.28 | +0.15 | 1.16 |
| AMZN | equity | 10 | -117.08 | -0.37 | 0.40 |
| GOOGL | equity | 17 | +136.36 | +0.23 | 1.62 |
| AVGO | equity | 19 | -109.33 | -0.18 | 0.64 |
| TSLA | equity | 10 | +257.56 | +0.92 | 2.67 |

Crypto contributed +794.40 net PnL across 37 trades and equities contributed +1,204.56 across 104 trades.

## Interpretation

The historical v1 result is not solely a consequence of the original BTC-USD / SOL-USD / META / NVDA subset. Five of the seven pre-existing added symbols made positive net contributions, and the sum of their realized PnL was positive even while all assets competed for the same shared cash, four position slots, and 2% open-risk budget.

This is stronger evidence of breadth than independent per-symbol backtests because the expanded symbols can crowd out original positions and alter the complete portfolio path.

The result does **not** remove survivorship or selection bias. The 11-asset universe consists of current/high-profile assets that were already configured in the repository; it is not a point-in-time reconstruction of an investable universe. A stronger historical survivorship study would require membership information fixed at each historical date rather than adding more present-day survivors.

The result also does not repair EXP-0003's temporal-instability failure. A broader profitable retrospective universe can still be regime-dependent, and the prospective holdout remains the only path to genuinely unseen evidence.

## Provider revision note

BTC-USD and SOL-USD retained the durable EXP-0001 source hashes. Adjusted META, NVDA, and QQQ history differed from the durable EXP-0001 snapshot again. The control and expanded paths remained internally controlled because overlapping symbols reused the same current provider frames, and the four-symbol control reproduced the durable EXP-0001 metrics well inside the preregistered tolerances.

## Decision

`BREADTH SUPPORTED IN CONFIGURED UNIVERSE — CONTINUE RESEARCH — DO NOT DEPLOY — KEEP V1 FROZEN`

The configured-universe diagnostic supports broader retrospective profit contribution, but it does not establish a validated edge or justify deployment.

## Next research step

Keep v1 frozen and let the prospective recorder begin with the first active 2026-09-15 UTC capture. The next prospective infrastructure step is a read-only evaluator/trade-state replay over stored evidence. Any further historical universe work should use a preregistered point-in-time membership methodology rather than selecting additional current winners.
