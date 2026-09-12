# Portfolio Backtester

Status: Draft

## Problem

The current backtester evaluates one asset in isolation. It cannot answer the portfolio-level questions that matter for a €5,000 account: which simultaneous signals can actually be funded, how aggregate open risk is constrained, what the combined equity curve looks like, or whether results remain attractive after positions compete for capital.

## Goals

- Backtest multiple assets against one shared cash/equity account.
- Preserve next-open execution and deterministic ATR risk rules.
- Enforce max positions, max aggregate open risk, per-trade risk, and per-position notional caps.
- Produce a trade ledger, daily equity/exposure curves, and portfolio metrics.
- Provide a CLI that can run the initial BTC, SOL, META, and NVDA portfolio from historical data.
- Keep the engine deterministic and independently testable from the data provider.

## Non-goals

- No commissions/slippage model in this PR; the result must be labeled pre-cost and not treated as decision-useful yet.
- No walk-forward optimization.
- No short positions, leverage, options, futures, or intraday data.
- No AI/LLM decision-making.
- No portfolio optimizer or correlation-based allocation.

## Relevant context

- `src/swing_trader/backtest.py` contains the existing single-asset next-open prototype.
- `src/swing_trader/risk.py` owns deterministic sizing and ATR stop helpers.
- `src/swing_trader/scoring.py` currently scores only the latest bar.
- `docs/product/strategy-v1.md` and `docs/domain/risk-model.md` define the v1 strategy/risk invariants.
- ADR-002 requires next-open execution.
- ADR-003 requires deterministic risk controls.
- The initial portfolio universe is BTC-USD, SOL-USD, META, and NVDA.

## Proposed design

### Historical signal preparation

Add a vectorized historical score function that applies the same v1 score rules to every bar. Benchmark relative-strength data is aligned to the asset calendar without using future values. Regime state is derived from the benchmark close versus SMA200 and aligned to the asset calendar.

### Portfolio engine

Add `portfolio.py` with explicit dataclasses:

- `PortfolioAsset`: enriched OHLCV data, historical scores, and regime series.
- `PortfolioBacktestConfig`: initial equity and deterministic risk limits.
- `PortfolioTrade`: complete realized trade ledger record.
- `PortfolioBacktestResult`: trades plus equity, exposure, and position-count curves.

The engine iterates over the union of all asset dates. For each date it processes events in market-time order:

1. Existing positions that gap through a stop exit at that day's open.
2. Pending signals from the asset's previous bar may enter at the current open.
3. Stops are active intraday, including on the entry bar.
4. Surviving positions update trailing stops from closing information; the updated stop is effective on the next bar.
5. Portfolio equity/exposure is marked at close.
6. Signals are generated from that close and scheduled only for the asset's next available bar.

When several entries compete for capital at the same open, candidates are processed by descending signal score and then symbol for deterministic tie-breaking.

Sizing uses current portfolio equity, available cash, per-position notional cap, and remaining aggregate open-risk capacity. Signals that cannot receive positive size are skipped rather than deferred.

Stop fills model gaps conservatively: if the open is already below the stop, fill at the open; otherwise a low-through-stop fills at the stop.

Open positions are liquidated at the end of the test at the latest available close and labeled `end_of_test`.

### Metrics

Add `metrics.py` with deterministic portfolio metrics:

- start/end equity and total return;
- CAGR;
- maximum drawdown;
- Sharpe and Sortino from portfolio daily returns;
- profit factor;
- win rate;
- average winner/loser and expectancy in R;
- trade count and average holding days;
- average exposure;
- best/worst R;
- share of positive PnL contributed by the top five winning trades.

### CLI

Add a separate `swing-backtest` entry point so the existing scanner CLI stays backward compatible. The CLI downloads/enriches the selected symbols, constructs historical scores/regimes, runs the shared-account engine, and prints a compact summary and trade ledger.

## Trading and research implications

- No signal may execute on the signal bar; entries occur only at the next available asset open.
- Trailing stops computed from a close are not allowed to affect that same bar's stop decision.
- Same-day entry stops are allowed because the initial stop is known at the entry open.
- Gap-through-stop fills use the open rather than the stale stop price to avoid optimistic execution.
- Mixed equity/crypto calendars use each asset's next available bar, not an assumed global next day.
- No transaction costs or slippage are included yet; metrics are pre-cost and must be treated as research plumbing, not evidence of a tradable edge.
- Fractional units are allowed in v1 research so equities and crypto share one sizing model.

## Alternatives considered

### Run independent single-asset backtests and combine returns afterward

Rejected because it ignores cash competition, simultaneous positions, portfolio risk limits, and execution ordering.

### Put data downloading inside the portfolio engine

Rejected because it would couple accounting logic to one provider and make deterministic tests harder.

### Reject an entry when remaining risk is below the full target size

Rejected. The engine may reduce size to fit remaining cash/risk capacity, preserving deterministic limits while using available capacity.

## Test and validation plan

- Unit test next-open entry timing.
- Unit test same-bar initial stop and gap-through-stop execution.
- Unit test max positions and aggregate risk enforcement.
- Unit test deterministic score-priority entry ordering.
- Unit test end-of-test liquidation and equity accounting.
- Unit test historical score-series consistency for a fully bullish synthetic asset.
- Unit test key metrics on controlled equity/trade data.
- Run `pytest -q` and `ruff check src tests` in CI.

## Simplification plan

Keep the engine event loop explicit rather than introducing a generic event bus, broker abstraction, order hierarchy, or portfolio optimizer. Prefer small dataclasses and pure helper functions. Reuse `position_plan`, `initial_stop`, and `trailing_stop` rather than duplicating risk formulas.

## Compound plan

Potential reusable learnings include multi-calendar next-bar semantics and stop-event ordering. If implementation confirms a generally useful pattern, capture it under `docs/solutions/trading-research/`; otherwise record `No reusable learning`.

## Documentation and memory updates

- Update `.ai/current-state.md` after the feature is complete.
- Update README with the new CLI.
- Archive this plan under `docs/plans/completed/` before final review.
- Add solution memory only if a reusable lesson emerges.

## Implementation plan

1. Add historical score/regime helpers.
2. Implement shared-account portfolio engine and result dataclasses.
3. Implement metrics.
4. Add the `swing-backtest` CLI.
5. Add unit/integration-style synthetic tests.
6. Perform Simplify, then validation.
7. Perform Compound and memory/documentation updates.
8. Final diff review and squash merge.

## Review checklist

- [x] Scope and acceptance criteria are clear.
- [x] Design is consistent with project invariants.
- [x] Trading/research risks are addressed.
- [x] Test strategy is sufficient.
- [x] Simplification risks are identified.
- [x] Potential compound knowledge destinations are identified.
- [x] Required memory/documentation changes are identified.

## Definition of done

The portfolio engine deterministically shares one account across multiple assets, enforces all v1 portfolio-risk limits, preserves realistic next-open/stop timing, produces portfolio metrics and a ledger, has synthetic tests for execution/risk edge cases, passes CI, receives a formal `PASS` review, and is squash-merged into `main`.