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

The portfolio backtester shares one cash balance and one risk budget across all selected assets. Results are currently **pre-cost**: transaction costs and slippage are not modeled yet.

Default initial research portfolio:

```bash
swing-backtest \
  --symbols BTC-USD,SOL-USD,META,NVDA \
  --start 2018-01-01 \
  --initial-equity 5000
```

The engine generates signals from a completed daily close, enters only at that asset's next available open, applies initial stops on the entry bar, fills gaps through stops at the open, and only applies close-derived trailing-stop updates to later bars.

The result includes a realized trade ledger plus portfolio equity/exposure curves and metrics including CAGR, maximum drawdown, Sharpe, Sortino, profit factor, win rate, expectancy in R, holding period, and average exposure.

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
- `experiments/` — reproducible research memory, including failed ideas

Generate a compact working context before an AI coding session:

```bash
python scripts/build_context.py
```

This writes `.ai/context.md`, which is intentionally ignored by Git because it is derived working memory.

## Repository layout

```text
config/                 universe and strategy configuration
src/swing_trader/       production code
tests/                  unit tests
docs/                   strategy, domain, decisions, plans, solutions, roadmap
experiments/             reproducible research history
.ai/                     current state and task/context helpers
.github/workflows/      CI and PR convention checks
```

## Roadmap

1. Add transaction costs and slippage models.
2. Run and record the first portfolio experiments on BTC, SOL, META, and NVDA.
3. Add walk-forward / out-of-sample evaluation.
4. Add parameter robustness sweeps.
5. Add a persistent daily scan database.
6. Add an AI research layer for catalysts, filings, earnings and crypto-specific events.
7. Add broker/exchange execution only after paper-trading validation.

## Risk model for the initial €5k account

The initial research assumption is 0.5% account risk per trade, or roughly €25 on €5,000. Position size is computed from the distance between entry and stop, and is also capped by maximum position notional and aggregate portfolio risk. This is a research default, not a recommendation.
