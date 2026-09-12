# Execution Cost Model

Status: Draft

## Problem

The portfolio backtester currently reports pre-cost results. Those results are useful for validating event ordering and risk accounting, but they are not decision-useful because entries and exits assume frictionless fills.

The next research step requires deterministic transaction-cost assumptions that can differ between equities and crypto without coupling the backtest engine to a specific broker or exchange.

## Goals

- Model commissions, spread, and additional slippage separately.
- Apply adverse execution prices to every entry and exit.
- Deduct commissions from shared portfolio cash at execution time.
- Size positions using cost-adjusted initial risk rather than adding costs only after the trade.
- Enforce aggregate open risk using cost-adjusted liquidation risk at the current stop.
- Support different cost assumptions by asset class.
- Keep cost assumptions configurable and reproducible.
- Expose total execution costs in the trade ledger and summary output.

## Non-goals

- No broker- or exchange-specific live fee integration.
- No order-book simulation, volume participation model, or nonlinear market impact.
- No maker/taker logic.
- No borrowing, funding, financing, or tax model.
- No intraday bid/ask data.
- No attempt to claim that one default configuration is universally realistic.

## Relevant context

- `src/swing_trader/portfolio.py` owns shared-account execution and risk accounting.
- `src/swing_trader/risk.py` owns deterministic risk helpers.
- `src/swing_trader/backtest_cli.py` is the historical research entry point.
- `docs/solutions/trading-research/order-events-by-information-time.md` defines execution-event ordering.
- `AGENTS.md` requires transaction costs and slippage before backtest results are treated as decision-useful.
- The current universe distinguishes `equity` and `crypto` asset classes.

## Proposed design

### Execution cost model

Add `execution.py` with a small immutable `ExecutionCostModel`:

- `commission_bps`: commission charged on executed notional;
- `spread_bps`: full quoted spread assumption;
- `slippage_bps`: additional adverse execution slippage per side.

For a long trade, each execution applies half the configured spread plus the configured slippage against the trader:

- buy fill = reference price × (1 + half-spread + slippage);
- sell fill = reference price × (1 - half-spread - slippage).

Commission is then charged on the executed notional.

The model remains linear in notional. This is intentional: fixed/minimum fees and nonlinear impact would complicate sizing and are not needed for the first cost-aware research baseline.

### Cost-aware risk sizing

The technical initial stop remains an ATR-based market trigger derived from the executed entry price. Position sizing must include the adverse sell fill and both entry/estimated stop-exit commissions.

For one unit of a long position:

`initial risk = entry cash outflow per unit - estimated net proceeds per unit if the stop is hit`

The same cost-aware liquidation logic is used for aggregate open risk as the stop trails upward.

This preserves the meaning of the configured risk fraction after transaction costs.

### Portfolio accounting

On entry:

1. derive adverse buy fill from the next-open reference price;
2. calculate the technical stop;
3. calculate cost-adjusted risk per unit;
4. size from account risk, notional cap, aggregate risk, and available cash including commission;
5. debit executed notional plus entry commission from cash.

On exit:

1. determine the market reference price from the existing execution semantics (`stop`, `stop_gap`, or `end_of_test`);
2. derive adverse sell fill;
3. deduct exit commission from proceeds;
4. record gross fill PnL, net PnL, fees, and total execution cost versus frictionless reference prices.

### Data model

Extend `PortfolioAsset` with `asset_class`, defaulting to `default` for backward-compatible synthetic tests.

Extend `PortfolioTrade` with:

- `entry_reference` and `exit_reference`;
- actual executed `entry` and `exit` prices;
- `entry_fee` and `exit_fee`;
- `gross_pnl` before commissions but after price slippage;
- `total_cost` relative to frictionless reference execution;
- `pnl` as the final net result.

`PortfolioBacktestConfig` receives a mapping of asset-class names to `ExecutionCostModel`. Missing asset classes fall back to a zero-cost `default` model unless configuration explicitly supplies another default.

### Configuration

Add `config/execution-costs.yaml` with clearly labeled baseline research assumptions for `equity` and `crypto`. These values are assumptions, not claims about a specific broker or exchange.

The backtest CLI receives `--cost-config` and loads these assumptions. The output changes from `PRE-COST` to `COST-AWARE` and reports aggregate execution costs.

## Trading and research implications

- Costs are applied at execution time, not subtracted only from final metrics.
- Position sizing includes expected entry and stop-exit friction so configured account risk remains meaningful.
- Stop triggers remain market-reference levels; slippage affects the realized fill after the trigger.
- Gap-through-stop behavior remains conservative: the market reference is the open, then adverse sell execution cost is applied.
- Spread is modeled as a full spread, with half charged adversely on each side of the trade.
- Default assumptions must remain explicit and reproducible; they are sensitivity inputs, not ground truth.
- A later experiment should test multiple cost scenarios rather than trusting one baseline.

## Alternatives considered

### Subtract a fixed percentage from final returns

Rejected because it ignores trade count, notional, entry/exit timing, sizing, and cash availability.

### Apply costs to PnL but not position sizing

Rejected because the configured risk budget would no longer represent expected loss to the initial stop after fees and execution friction.

### Model fixed/minimum broker fees now

Rejected for the first version because they make affordability and risk sizing nonlinear and broker-specific. The linear basis-point model is sufficient to establish cost-aware portfolio research and can be extended later if evidence requires it.

### Hardcode costs inside the portfolio engine

Rejected because assumptions must be explicit, configurable, and independently testable.

## Test and validation plan

- Unit test buy/sell adverse fill prices.
- Unit test commission calculation.
- Unit test cost-adjusted risk per unit.
- Verify zero-cost configuration preserves existing portfolio behavior.
- Verify entry cash includes commission.
- Verify exit PnL is net of both commissions and adverse fills.
- Verify aggregate open risk uses cost-aware stop liquidation.
- Verify asset classes receive different models.
- Verify gap-stop exits apply sell-side costs after the gap reference price.
- Verify CLI/config loading with controlled YAML.
- Run `pytest -q` and `ruff check src tests`.

## Simplification plan

Keep the cost model pure and linear. Avoid broker abstractions, order objects, inheritance, callbacks, or separate commission/spread strategy classes. Prefer one immutable model with explicit arithmetic and small helper methods.

## Compound plan

Potential reusable learning: execution costs must participate in position sizing and portfolio cash/risk accounting, not only performance reporting. If confirmed during implementation, capture it under `docs/solutions/trading-research/`.

## Documentation and memory updates

- Update README with cost configuration and cost-aware CLI behavior.
- Update `.ai/current-state.md` after implementation.
- Archive this plan under `docs/plans/completed/` before final review.
- Add reusable solution memory only if implementation confirms a general lesson.

## Implementation plan

1. Add pure execution-cost model and configuration loader.
2. Extend portfolio asset/trade/config data structures.
3. Integrate cost-aware sizing, cash accounting, open risk, and exits.
4. Update backtest CLI and add baseline cost config.
5. Add focused unit and portfolio regression tests.
6. Perform Simplify and final validation.
7. Perform Compound and update durable memory.
8. Complete formal diff review and squash merge.

## Review checklist

- [x] Scope and acceptance criteria are clear.
- [x] Design is consistent with project invariants.
- [x] Trading/research risks are addressed.
- [x] Test strategy is sufficient.
- [x] Simplification risks are identified.
- [x] Potential compound knowledge destinations are identified.
- [x] Required memory/documentation changes are identified.

## Definition of done

Every portfolio execution uses an explicit asset-class cost model; position sizing and aggregate risk are cost-aware; cash accounting includes fees; trade records expose execution costs; the CLI runs with reproducible cost assumptions; zero-cost behavior remains regression-compatible; tests/lint pass; final review is `PASS`; and the PR is squash-merged into `main`.