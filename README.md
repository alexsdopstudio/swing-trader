# Swing Trader

A rule-based swing trading research project for equities and crypto.

The v1 system is deliberately simple: daily bars, long-only, trend + momentum + relative strength + breakout + volume scoring, ATR-based risk, and next-session execution assumptions. The goal is to test whether the strategy has a robust historical edge before adding AI agents or live execution.

> Research software only. This repository is not financial advice and is not designed to guarantee profits.

## Strategy v1

- Universe: BTC, ETH, SOL and selected US mega-cap equities
- Benchmarks: BTC for crypto, QQQ for equities
- Timeframe: daily
- Entry score: 0-100
- Entry threshold: 70+
- Equity regime filter: QQQ above SMA200
- Crypto regime filter: BTC above SMA200
- Entry: signal on daily close, fill on next session open
- Initial stop: 2 ATR
- Trailing stop: 2.5 ATR
- Default risk: 0.5% of account equity per trade
- Max position notional: 25% of account equity
- Max aggregate open risk: 2% of account equity
- Max concurrent positions: 4

## Score

| Component | Max points |
|---|---:|
| Trend | 30 |
| Momentum | 25 |
| Relative strength | 20 |
| Breakout | 15 |
| Volume | 10 |

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -e ".[dev]"
pytest -q
```

## Run the scanner

```bash
swing-trader --config config/universe.yaml
```

or:

```bash
python -m swing_trader.cli --config config/universe.yaml
```

## Run the portfolio backtester

The portfolio backtester shares one cash balance and one risk budget across all selected assets. It models execution costs at trade time: adverse spread/slippage changes fill prices, commissions reduce cash, and position sizing includes expected friction to the initial stop.

Default initial research portfolio:

```bash
swing-backtest \
  --symbols BTC-USD,SOL-USD,META,NVDA \
  --start 2018-01-01 \
  --initial-equity 5000 \
  --cost-config config/execution-costs.yaml
```

The engine generates signals from a completed daily close, enters only at that asset's next available open, applies initial stops on the entry bar, fills gaps through stops from the gap-open market reference, and only applies close-derived trailing-stop updates to later bars.

The result includes a realized trade ledger plus portfolio equity/exposure curves and metrics including CAGR, maximum drawdown, Sharpe, Sortino, profit factor, win rate, expectancy in R, holding period, average exposure, commissions, and aggregate execution costs.

### Execution-cost assumptions

`config/execution-costs.yaml` contains baseline research assumptions, not broker or exchange quotes. The default configuration currently uses:

| Asset class | Commission | Full spread | Additional slippage per side |
|---|---:|---:|---:|
| Equity | 1 bps | 5 bps | 5 bps |
| Crypto | 10 bps | 10 bps | 10 bps |

A long buy pays half the configured spread plus slippage above the market reference; a sell receives half the spread plus slippage below it. Commission is charged on executed notional. Because these are research assumptions, strategy conclusions should be sensitivity-tested across multiple cost scenarios.

The technical stop remains a market-reference trigger. Execution costs affect the realized exit fill and are included in position sizing, aggregate open-risk accounting, shared cash, and realized R multiples.

## Reproducible experiments

Versioned research lives under `experiments/`. Experiment configs separate indicator warm-up history from the actual evaluation window and record code revision, data coverage, source-data digests, portfolio parameters, execution assumptions, metrics, and reviewed conclusions.

Run the baseline experiment locally with:

```bash
swing-experiment \
  --config experiments/EXP-0001-baseline/config.yaml \
  --output-dir .artifacts/EXP-0001
```

Run execution-cost sensitivity with:

```bash
swing-cost-sensitivity \
  --config experiments/EXP-0002-cost-sensitivity/config.yaml \
  --output-dir .artifacts/EXP-0002
```

Run historical temporal-stability diagnostics with:

```bash
swing-temporal-stability \
  --config experiments/EXP-0003-temporal-stability/config.yaml \
  --output-dir .artifacts/EXP-0003
```

Run the passive/reference comparison with:

```bash
swing-reference-comparison \
  --config experiments/EXP-0004-reference-baselines/config.yaml \
  --output-dir .artifacts/EXP-0004
```

Run the preregistered local parameter-neighborhood diagnostic with:

```bash
swing-parameter-neighborhood \
  --config experiments/EXP-0005-parameter-neighborhood/config.yaml \
  --output-dir .artifacts/EXP-0005
```

Run the configured-universe breadth diagnostic with:

```bash
swing-universe-breadth \
  --config experiments/EXP-0006-configured-universe-breadth/config.yaml \
  --output-dir .artifacts/EXP-0006
```

GitHub Actions runs the same real-data experiments and retains detailed trade/equity artifacts for review.

### EXP-0001 baseline

The first exploratory cost-aware baseline used BTC-USD, SOL-USD, META, and NVDA from 2021-01-01 through 2026-08-31, with warm-up history beginning in 2020.

Headline result: 65 trades, +1.05R expectancy, 3.18 profit factor, 6.01% CAGR and -4.25% maximum drawdown. The result is explicitly **not considered validated** because the sample is small, profits are concentrated in a few assets/trades, 2025–2026 is negative, and no true prospective holdout has matured.

### EXP-0002 execution-cost sensitivity

EXP-0002 freezes the EXP-0001 strategy and tests 0.5x, 1.0x, 2.0x and 4.0x execution-cost assumptions on one shared market-data snapshot.

The 2.0x scenario retains +0.99R expectancy and a 3.03 profit factor. The 4.0x stress scenario retains +0.82R expectancy and a 2.62 profit factor. This supports execution-cost robustness **inside the same historical sample**, but it is not held-out validation and does not justify deployment.

### EXP-0003 temporal stability

EXP-0003 decomposes the already-observed 2021–2026 history into six independent calendar folds, resetting the portfolio to 5,000 for each fold while keeping v1 frozen.

Only 3 of 6 folds had positive expectancy, positive return, and profit factor above 1. The preregistered 4-of-6 stability thresholds therefore failed. 2022 produced no trades, while 2025 and 2026-YTD were negative.

This is a retrospective temporal diagnostic, **not** an out-of-sample claim. It shows that the positive aggregate result is concentrated in favorable regimes rather than being temporally uniform.

### EXP-0004 passive/reference baselines

EXP-0004 keeps v1 frozen and compares it with cost-aware buy-and-hold of each selected asset plus an initially equal-weight, never-rebalanced buy-and-hold basket. Strategy and references reuse one provider snapshot and the same asset-class execution-cost assumptions.

The passive basket produced +2,139.01% total return and 73.16% CAGR versus v1's +39.17% and 6.01%, but the passive path was essentially fully invested and suffered a -95.19% maximum drawdown. v1 averaged only about 6.04% exposure, had a -4.25% maximum drawdown, and recorded higher Sharpe/Sortino than every passive reference in this selected sample.

This does not establish economic superiority for either approach. The comparison exposes a large return-versus-capital-at-risk trade-off, is strongly influenced by exceptional SOL and NVDA histories, and remains retrospective rather than out-of-sample evidence.

### EXP-0005 parameter neighborhood

EXP-0005 keeps v1 frozen and evaluates exactly 27 preregistered combinations of `min_score` 65/70/75, `stop_atr` 1.5/2.0/2.5, and `trail_atr` 2.0/2.5/3.0 on one shared provider snapshot.

All 27 scenarios and all six immediate axial neighbors were joint-positive, median expectancy was +0.92R versus a preregistered +0.50R threshold, and the exact v1 center reproduced EXP-0001 within every preregistered tolerance. This supports local retrospective parameter robustness.

The magnitude is still parameter-sensitive: expectancy ranges from roughly +0.43R to +1.73R across the tested surface. No historical winner is selected or promoted, and frozen v1 remains 70 / 2.0 / 2.5. EXP-0005 does not repair EXP-0003's temporal instability or create out-of-sample evidence.

### EXP-0006 configured-universe breadth

EXP-0006 keeps v1 frozen and reruns the original four-symbol research subset plus the complete 11-asset list that was already present in `config/universe.yaml`, using one shared provider snapshot. Added assets compete for the same cash, four position slots, and 2% open-risk budget rather than being tested independently.

All preregistered breadth criteria passed. The expanded path produced +39.98% total return, 6.12% CAGR, +0.49R expectancy, a 2.04 profit factor and -5.13% maximum drawdown across 141 trades. Five of the seven added symbols and 8 of 11 symbols overall were positive net-PnL contributors; added symbols contributed +514.76 in aggregate, both equities and crypto contributed positively, and the largest positive symbol contribution (SOL-USD) was 30.58% of summed positive symbol PnL versus a 60% ceiling.

This supports broader retrospective contribution but not superiority of the expanded portfolio: compared with the four-symbol control, expectancy/profit factor fell and exposure/drawdown rose. It also does not eliminate survivorship bias because the configured universe contains current/high-profile survivors rather than point-in-time membership data.

### Prospective v1 holdout

`experiments/PROSPECTIVE-v1-holdout/protocol.yaml` preregisters the first genuinely future v1 holdout. It starts on 2026-09-14 and freezes the v1 strategy/risk/execution specification from before the holdout begins.

Validation claims are blocked until both gates are satisfied:

- minimum observation end: 2028-09-14;
- minimum closed trades: 30.

Interim monitoring is allowed, but interim results must not be used to tune v1. Any strategy or risk change requires a new prospective protocol/version.

The forward recorder preserves one canonical provider-state archive per active UTC observation date. The read-only evaluator replays frozen v1 from a locally downloaded contiguous archive chain without provider access, processing only the newly observable market date from each archive and stopping at the first missing observation.

```bash
swing-holdout-evaluate \
  --archives .artifacts/PROSPECTIVE-v1-holdout/archives \
  --output-dir .artifacts/PROSPECTIVE-v1-holdout/evaluation
```

Evaluator outputs are derived interim state/trade records, not validation and not tuning inputs. See `experiments/PROSPECTIVE-v1-holdout/README.md` for capture, archive, gap, and replay semantics.

See `experiments/README.md` and each experiment's `notes.md` for reviewed interpretation and limitations.

## Development workflow

Development uses dedicated branches and pull requests. Do not implement features directly on `main`.

Examples:

```text
feat/portfolio-backtester
fix/yfinance-missing-volume
experiment/breakout-50-day
```

Commits and PR titles follow Conventional Commits, and the repository validates these conventions in CI. Squash merge is preferred after CI is green and the change has been reviewed.

See `CONTRIBUTING.md` for the complete workflow.

## AI development memory

The repository is designed to be continued across AI coding sessions without depending on one chat history.

Primary memory sources:

- `AGENTS.md` — agent guide and repository map
- `ARCHITECTURE.md` — system boundaries and module responsibilities
- `.ai/current-state.md` — current project state and milestone
- `docs/decisions/` — durable architecture/research decisions
- `docs/plans/active/` — active implementation plans
- `docs/solutions/` — reusable engineering and trading-research lessons
- `experiments/` — reproducible research history and prospective protocols

Generate a compact working context before an AI coding session:

```bash
python scripts/build_context.py
```

This writes `.ai/context.md`, which is intentionally ignored by Git because it is derived working memory.

## Repository layout

```text
config/                 universe and execution-cost configuration
src/swing_trader/       production code
tests/                  unit tests
docs/                   strategy, domain, decisions, plans, solutions, roadmap
experiments/             reproducible research history and prospective protocols
.ai/                     current state and task/context helpers
.github/workflows/      CI, PR convention checks, and experiment runs
```

## Roadmap

1. Keep v1 frozen and record the prospective holdout from 2026-09-14 onward without interim tuning.
2. Preserve complete provider states with the provenance-preserving forward recorder; never backfill missed prospective dates.
3. Replay those captured observations through the read-only information-time evaluator without feeding interim results into tuning.
4. If more historical universe research is warranted, use preregistered point-in-time membership rather than adding current survivors.
5. Add persistent daily scan history and later an AI research layer for catalysts, filings, earnings and crypto-specific events.
6. Add broker/exchange execution only after paper-trading infrastructure and prospective evidence are trustworthy.

## Risk model for the initial €5k account

The initial research assumption is 0.5% account risk per trade, or roughly €25 on €5,000. Position size is derived from cost-adjusted loss to the initial stop and is also capped by maximum position notional, aggregate portfolio risk, and available cash including entry commission. This is a research default, not a recommendation.
