# Strategy V1

## Scope

- Daily timeframe
- Long-only
- Crypto: BTC, ETH, SOL
- US equities: selected mega-cap names
- Benchmarks: BTC for altcoins, QQQ for equities

## Swing Score

Maximum 100 points:

- Trend: 30
- Momentum: 25
- Relative strength: 20
- Breakout: 15
- Volume: 10

## Entry

A candidate must satisfy the configured minimum score, a 20-day breakout, positive trend structure and a bullish benchmark regime.

Signals are generated using the completed daily bar. Execution is modeled no earlier than the next session open.

## Risk and exit

- Default account risk per trade: 0.5%
- Initial stop: 2 ATR
- Trailing stop: highest close minus 2.5 ATR
- Maximum position notional: 25% of equity

These are research defaults, not claims of optimality.

## Research standard

A parameter set is not considered robust because it wins on one asset or one period. It must survive out-of-sample evaluation, reasonable parameter perturbations, realistic costs and portfolio-level testing.
