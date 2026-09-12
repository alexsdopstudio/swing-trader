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

## Repository layout

```text
config/                 universe and strategy configuration
src/swing_trader/       production code
tests/                  unit tests
.github/workflows/      CI
```

## Roadmap

1. Add a portfolio-aware multi-asset backtester.
2. Compute CAGR, max drawdown, Sharpe, Sortino, profit factor, expectancy in R and exposure.
3. Add walk-forward / out-of-sample evaluation.
4. Add transaction costs and slippage models.
5. Add parameter robustness sweeps.
6. Add a persistent daily scan database.
7. Add an AI research agent for catalysts, filings, earnings and crypto-specific events.
8. Add broker/exchange execution only after paper-trading validation.

## Risk model for the initial €5k account

The initial research assumption is 0.5% account risk per trade, or roughly €25 on €5,000. Position size is computed from the distance between entry and stop, and is also capped by maximum position notional. This is a research default, not a recommendation.
