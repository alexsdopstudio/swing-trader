# Swing Trader

A rule-based swing trading research project for equities and crypto.

The v1 system is deliberately simple: daily bars, long-only, trend + momentum + relative strength + breakout + volume scoring, ATR-based risk, and next-session execution assumptions. The goal is to test whether the strategy has a robust edge before adding live execution.

> Research software only. This repository is not financial advice and is not designed to guarantee profits.

## Strategy v1

- Universe: BTC, ETH, SOL and selected US mega-cap equities
- Benchmarks: BTC for crypto, QQQ for equities
- Timeframe: daily
- Entry threshold: Swing Score 70+
- Equity regime: QQQ above SMA200
- Crypto regime: BTC above SMA200
- Entry: signal on completed daily close, fill no earlier than next asset open
- Initial stop: 2 ATR
- Trailing stop: 2.5 ATR
- Default risk: 0.5% of equity per trade
- Max position notional: 25% of equity
- Max aggregate open risk: 2% of equity
- Max concurrent positions: 4

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -e ".[dev]"
pytest -q
```

## Main commands

```bash
swing-trader --config config/universe.yaml
swing-backtest --symbols BTC-USD,SOL-USD,META,NVDA --start 2018-01-01 --initial-equity 5000 --cost-config config/execution-costs.yaml
swing-experiment --config experiments/EXP-0001-baseline/config.yaml --output-dir .artifacts/EXP-0001
swing-cost-sensitivity --config experiments/EXP-0002-cost-sensitivity/config.yaml --output-dir .artifacts/EXP-0002
swing-temporal-stability --config experiments/EXP-0003-temporal-stability/config.yaml --output-dir .artifacts/EXP-0003
swing-reference-comparison --config experiments/EXP-0004-reference-baselines/config.yaml --output-dir .artifacts/EXP-0004
swing-parameter-neighborhood --config experiments/EXP-0005-parameter-neighborhood/config.yaml --output-dir .artifacts/EXP-0005
```

The portfolio engine shares cash and risk across selected assets, generates signals from completed closes, enters at the next real asset open, models commissions/spread/slippage in fills and risk, handles stop gaps explicitly, and writes realized trades plus equity/exposure curves.

## Execution-cost assumptions

`config/execution-costs.yaml` contains research assumptions, not broker/exchange quotes. The baseline currently uses 1 bps commission / 5 bps full spread / 5 bps slippage per side for equities and 10 / 10 / 10 bps for crypto. These assumptions are included in fills, cash, sizing, aggregate risk, and realized PnL.

## Research record

Versioned research lives under `experiments/`. Each experiment separates warm-up from evaluation history, records code/runtime/data provenance, and preserves reviewed conclusions. GitHub Actions reruns the real-data workflows and uploads detailed reproducible artifacts.

### EXP-0001 baseline

On BTC-USD, SOL-USD, META, and NVDA over 2021-01-01 through 2026-08-31, frozen v1 produced 65 trades, +1.05R expectancy, 3.18 profit factor, 6.01% CAGR and -4.25% max drawdown. This is exploratory history, not validation.

### EXP-0002 execution-cost sensitivity

The same frozen strategy remained positive under 2x and 4x execution-cost scenarios on one shared snapshot. This supports historical cost robustness but is not held-out evidence.

### EXP-0003 temporal stability

Only 3 of 6 calendar folds met the preregistered positive-expectancy / profit-factor-above-one criteria. The 4-of-6 thresholds failed; 2025 and 2026-YTD were negative and 2022 had no trades. The aggregate edge is therefore not temporally uniform.

### EXP-0004 passive/reference baselines

An initially equal-weight, never-rebalanced passive basket of the selected assets returned +2,139.01% with -95.19% max drawdown and about 99.89% exposure, versus frozen v1 at +39.17%, -4.25%, and about 6.04% exposure. Passive ownership had far higher absolute return; v1 had a much more defensive path. The comparison remains heavily affected by the selected SOL/NVDA histories.

### EXP-0005 parameter neighborhood

EXP-0005 preregistered exactly 27 combinations of `min_score` 65/70/75, `stop_atr` 1.5/2.0/2.5, and `trail_atr` 2.0/2.5/3.0 around frozen v1.

All 27 scenarios and all six immediate axial neighbors were joint-positive, median expectancy was +0.92R versus a preregistered +0.50R threshold, and the frozen center reproduced EXP-0001 within tolerance. Local retrospective parameter robustness is therefore supported. Metric magnitude still varied materially (expectancy roughly +0.43R to +1.73R), and no historical winner is selected or promoted. v1 remains 70 / 2.0 / 2.5.

### Prospective v1 holdout

`experiments/PROSPECTIVE-v1-holdout/protocol.yaml` preregisters the first genuinely future v1 holdout beginning 2026-09-14. Validation claims are blocked until both the minimum observation end (2028-09-14) and 30 closed trades are reached. Interim monitoring must not tune v1; any strategy/risk change requires a new prospective version/protocol.

## Development workflow and AI memory

Development uses dedicated branches/PRs, Conventional Commits, required CI, formal final-diff review, Simplify, Compound, and squash merge. Repository-native continuity comes from `AGENTS.md`, `ARCHITECTURE.md`, `.ai/current-state.md`, `docs/plans/`, `docs/solutions/`, and `experiments/`. `python scripts/build_context.py` builds replaceable working context.

## Roadmap

1. Keep v1 frozen and record the prospective holdout from 2026-09-14 onward without interim tuning.
2. Build the provenance-preserving forward observation/holdout recorder.
3. Test a broader universe to reduce survivor/selection bias.
4. Add persistent daily scan history on the same forward-data foundation.
5. Add an AI research layer for catalysts, filings, earnings and crypto-specific events.
6. Add broker/exchange execution only after paper-trading infrastructure and prospective evidence are trustworthy.

## Risk model for the initial €5k account

The initial research assumption is 0.5% account risk per trade, roughly €25 on €5,000. Position size is derived from cost-adjusted loss to the initial stop and capped by position notional, aggregate portfolio risk, and available cash. This is a research default, not a recommendation.
