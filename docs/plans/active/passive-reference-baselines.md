# Design Plan: Passive Reference Baselines

Status: Draft

## Problem

The frozen v1 strategy has historical results and temporal diagnostics, but those results are not yet shown beside a simple investable reference. Without a passive baseline, the research cannot distinguish strategy value from market beta or describe the opportunity cost of remaining in cash.

## Goals

- Add a deterministic, cost-aware passive buy-and-hold baseline runner for the same symbols and evaluation window as a versioned experiment.
- Report an equal-weight portfolio baseline and per-symbol references using one shared provider snapshot.
- Persist reproducible configuration, input coverage/digests, execution-cost assumptions, equity curves, and metrics.
- Keep the v1 signal, portfolio engine, risk controls, and prospective-holdout protocol unchanged.

## Non-goals

- No v1 parameter tuning, strategy selection, or performance claim.
- No optimization of benchmark weights, rebalancing frequency, taxes, dividends, cash yield, or nonlinear market impact.
- No use of prospective-holdout observations to modify v1.

## Relevant context

- `docs/roadmap.md` identifies passive/reference baselines as the next research task while v1 remains frozen.
- `experiment.py` establishes versioned experiment artifacts, warm-up/evaluation separation, and provider provenance.
- `cost_sensitivity.py` establishes one shared provider snapshot across comparable scenarios.
- `execution.py` defines adverse fills and commission assumptions.
- `metrics.py` currently consumes a portfolio-backtest result with a trade ledger; passive references need return metrics without inventing strategy trades.

## Proposed design

Add a `reference_baseline` module and CLI. A YAML config points to a base experiment config, names the selected symbols, and specifies equal weights unless explicit fixed weights are supplied. The runner downloads each required asset once through a cache, slices only the base experiment's evaluation window, buys each allocation at the first usable open using the existing adverse buy fill plus commission, and liquidates at the final close using the existing adverse sell fill plus commission.

The baseline retains fractional units, starts from the same initial equity, and does not rebalance. It emits a synthetic equity curve aligned to the union of asset evaluation dates, per-symbol and portfolio metrics, input digests, configuration hashes, and a comparison-ready summary. A small standalone return-metrics helper avoids constructing fictitious strategy trades or altering the existing strategy metrics contract.

## Trading and research implications

The reference contains no strategy signal and therefore cannot create look-ahead bias: positions are entered at the first evaluation-session open, and exit at the final available evaluation close. The same explicit execution-cost model is applied at both ends. Equal weighting is declared before evaluation and is not optimized. The runner uses the same configured universe and window as the referenced experiment, but it is still historical evidence, not new out-of-sample validation.

## Alternatives considered

- Frictionless close-to-close benchmarks were rejected because they would be incomparable with cost-aware strategy results.
- Reusing `PortfolioBacktestResult` with artificial trades was rejected because trade-level expectancy and stop-based R metrics are undefined for passive holding.
- Dynamic rebalancing was rejected as unnecessary additional policy and execution assumptions.

## Test and validation plan

- Unit-test config validation, fixed-weight validation, cost-aware entry/exit arithmetic, date alignment, and absence of warm-up leakage using synthetic frames.
- Verify one provider download per symbol and stable source digests.
- Run `pytest -q` and `ruff check src tests`.
- Run a relevant baseline command using the existing historical configuration when provider access is available; record only factual artifacts and review interpretation separately.

## Simplification plan

Keep the reference model to one initial allocation and one final liquidation. Reuse existing execution-cost calculations and avoid a benchmark abstraction, a rebalance engine, or a second market-data framework.

## Compound plan

Capture a reusable trading-research note if the implementation establishes a durable comparability rule for passive references; otherwise record `No reusable learning` in the PR.

## Documentation and memory updates

Update architecture, roadmap/current state, experiment documentation, and solution-memory index if a reusable comparability rule is recorded. Archive the plan when the PR is ready for final review.

## Implementation plan

1. Add the active design plan and create a Draft PR.
2. Implement config parsing, cached data loading, cost-aware passive valuation, and serializable artifacts.
3. Add a CLI and unit tests with deterministic synthetic data.
4. Add a versioned reference-baseline configuration and documentation.
5. Simplify, validate, capture compound learning, update memory, then conduct final diff review.

## Review checklist

- [x] Scope and acceptance criteria are clear.
- [x] Design is consistent with project invariants.
- [x] Trading/research risks are addressed.
- [x] Test strategy is sufficient.
- [x] Simplification risks are identified.
- [x] Potential compound knowledge destinations are identified.
- [x] Required memory/documentation changes are identified.

## Definition of done

The PR will provide reproducible passive-reference artifacts for a declared historical window, apply explicit execution costs, have deterministic tests and green lint, leave v1 unchanged, include required memory updates and a completed plan, pass final diff review, and merge through the required lifecycle.
