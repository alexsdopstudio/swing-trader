# Execution Cost Model

Status: Completed

## Completion summary

The portfolio backtester now applies deterministic, configurable execution friction at trade time rather than treating costs as a post-processing adjustment.

Implemented capabilities:

- immutable `ExecutionCostModel` for commission, full spread, and additional slippage assumptions;
- adverse buy/sell fill prices derived from market-reference prices;
- commission charged on executed notional;
- asset-class cost models loaded from reproducible YAML configuration;
- cost-aware initial-risk sizing;
- cost-aware aggregate open-risk accounting as stops trail;
- entry cash constraints that include commission;
- net exit proceeds after adverse fill and commission;
- trade ledger fields for reference prices, executed prices, entry/exit fees, gross PnL, net PnL, and total execution cost;
- cost-aware `swing-backtest` output;
- baseline equity/crypto research assumptions under `config/execution-costs.yaml`;
- zero-cost regression compatibility.

## Scope preserved

The model is intentionally linear in notional. It does not attempt to simulate broker-specific minimum fees, maker/taker schedules, order-book depth, nonlinear market impact, financing, taxes, or intraday bid/ask data.

The baseline cost configuration is a research input, not a broker or exchange quote. Strategy conclusions require cost-sensitivity analysis.

## Simplify outcome

The implementation keeps one immutable model with direct basis-point arithmetic. It avoids broker abstractions, order hierarchies, callbacks, polymorphic fee engines, and nonlinear affordability solvers. The existing portfolio event loop remains explicit.

No further simplification was justified without either hiding execution arithmetic or weakening configurability.

## Compound outcome

The implementation confirmed a reusable trading-research lesson: execution costs belong in sizing and portfolio risk/cash accounting, not only final PnL reporting.

The lesson is captured in `docs/solutions/trading-research/include-costs-in-risk-accounting.md` and indexed in solution memory.

## Validation

- buy/sell adverse-fill arithmetic tests;
- commission tests;
- cost-adjusted initial-risk tests;
- zero-cost regression tests;
- cost-aware portfolio sizing tests;
- asset-class model selection tests;
- gap-stop cost tests;
- YAML configuration loading tests;
- `pytest -q`;
- `ruff check src tests`;
- PR convention checks.

## Next research step

Run and record the first cost-aware portfolio experiment on BTC-USD, SOL-USD, META, and NVDA, then repeat it across multiple execution-cost scenarios before interpreting the strategy's edge.
