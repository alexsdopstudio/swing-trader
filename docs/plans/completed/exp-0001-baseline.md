# EXP-0001 — Cost-Aware Baseline

Status: Completed

## Goal

Create the first reproducible real-data portfolio experiment for the v1 swing strategy using the cost-aware shared-account backtester.

This experiment was explicitly exploratory rather than out-of-sample validation.

## Configuration

Universe:

- BTC-USD
- SOL-USD
- META
- NVDA

Time windows:

- warm-up start: `2020-01-01`
- evaluation start: `2021-01-01`
- evaluation end: `2026-09-01` exclusive

Portfolio settings:

- initial equity: 5,000
- risk per trade: 0.5%
- max aggregate open risk: 2%
- max positions: 4
- max position notional: 25%
- minimum Swing Score: 70
- initial stop: 2 ATR
- trailing stop: 2.5 ATR

Execution costs came from `config/execution-costs.yaml`.

## Implementation outcome

Added a lightweight versioned experiment runner that:

- loads YAML experiment specifications;
- downloads and caches required assets/benchmarks;
- computes indicators/scores over warm-up history;
- slices data to an explicit evaluation window before portfolio simulation;
- records requested and actual provider coverage;
- writes strict JSON results, trade ledger, equity/exposure/position curves, resolved config, and a generated summary;
- records the exact code SHA that produced the run.

Added a dedicated GitHub Actions workflow that runs EXP-0001 against real yfinance data, validates the artifact, and uploads it for review.

## Validation outcome

The first real-data run exposed a serialization bug because YAML ISO dates were parsed as `datetime.date`. The runner was fixed to normalize dates and non-finite metrics before strict JSON serialization, and a regression test was added.

The reviewed successful run used code SHA `926ce69b6214b237866fbcff97e0de7a16ddff3d`.

Workflow run: `34706655020`

Artifact digest: `sha256:6edcddf3341e34e3c3122177442b17e488bcb68d7780c7058990f6abc18b4bb6`

The standard CI suite and PR conventions also passed on the implementation head.

## Research result

Headline metrics:

- 65 trades
- ending equity: 6,958.52
- total return: 39.17%
- CAGR: 6.01%
- max drawdown: -4.25%
- profit factor: 3.18
- expectancy: +1.05R
- win rate: 46.15%
- average exposure: 6.04%
- top-five-profit share: 47.98%

The primary exploratory hypothesis (positive cost-aware expectancy) was supported in this sample.

The result was not considered validated because trade count is small, profit contribution is concentrated in SOL-USD/NVDA and a handful of winners, the universe is narrow, 2025 and available 2026 are negative, and no held-out/walk-forward or sensitivity testing has been performed.

Decision: `CONTINUE RESEARCH — DO NOT DEPLOY`.

Full interpretation is in `experiments/EXP-0001-baseline/notes.md`.

## Simplify outcome

The experiment runner remains orchestration over existing modules. No database, generic experiment plugin framework, strategy registry, or new backtest engine was introduced.

Generated large artifacts remain CI outputs; the repository stores the immutable config, reviewed results, provenance, and interpretation needed for durable experiment memory.

## Compound outcome

The run confirmed that warm-up history and evaluation history must be modeled as separate versioned windows. This is now captured in:

`docs/solutions/trading-research/separate-warmup-and-evaluation-windows.md`

The solution note also requires recording actual provider coverage because requested history and available history can differ by asset.

## Next research step

Run execution-cost sensitivity without changing v1 strategy parameters. Only after that should the project proceed to held-out / walk-forward validation and parameter perturbation.
