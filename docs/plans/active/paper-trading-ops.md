# Paper trading operations

Status: Completed pending final review and merge

## Problem

The scanner, portfolio replay, risk model, and daily operational capture are technically capable but do not yet give the owner a daily workflow from a completed signal to a reviewable decision, proposed trade, managed exit rule, and result. The product needs to support disciplined pursuit of net returns without turning historical research into an automated or guaranteed trading service.

## Goals

- Build an approval-only, paper-first daily operations workflow for the existing long-only v1 universe.
- Create deterministic candidate and ticket views using existing score, next-open, cost, sizing, and stop rules.
- Persist append-only human decisions and paper/manual execution facts with source/config provenance.
- Surface open-position stop/trailing-stop rules and operational health in a readable brief.
- Keep all personal operational records separate from prospective validation and v1 tuning.

## Non-goals

- Broker connectivity, credential storage, order transmission, or automatic execution.
- New entry/exit parameters, take-profit rules, leverage, shorting, or strategy optimization.
- A profitability guarantee, investment advice, or a replacement for broker-specific order semantics.

## Relevant context

- `scanner.py` creates completed-bar `BUY`/`WATCH` observations.
- `portfolio.py`, `risk.py`, and `execution.py` own next-open, cost, sizing, initial-stop, trailing-stop, cash, and aggregate-risk semantics.
- ADR-001, ADR-002, and ADR-009 are binding.
- Daily scanner history is operational audit evidence; `PROSPECTIVE-v1-holdout` remains separate and byte-locked.

## Implemented design

`paper_operations.py` and `swing-paper-ops` consume a verified `daily-scan-history` archive, a narrow paper-only account configuration, and a local JSONL ledger. The configuration exposes starting capital and the existing execution-cost config, while frozen v1 score, stop, trail, position-notional, position-count, and aggregate-risk settings remain in `PortfolioBacktestConfig`; it has no broker, credential, quantity-override, or fill-override field.

The deterministic brief includes eligible long candidates, planning reference, proposed quantity, initial stop, planned initial loss, explicit rejection reasons, and ledger-derived open positions. A completed-bar close is a planning reference only. A ticket may enter no earlier than the next available open after its per-symbol completed signal date. After explicit approval, `record-entry` receives a market reference and deterministically re-prices the paper fill, stop, quantity, fee, and initial loss under conservative cash/risk constraints. It does not transmit an order.

The append-only ledger has explicit `approved`, `declined`, `deferred`, `entry_recorded`, and `exit_recorded` events. It stores immutable ticket/config/archive provenance, planning values, paper market reference, deterministic paper fill/fee, and exit facts. It rejects malformed, duplicate, out-of-order, same-day-or-earlier, and provenance-mismatched events. The first implementation accepts `paper` fills only; a future manual-live journal remains out of scope.

Current trailing stops are reconstructed from the first observed completed scanner rows in the supplied archive history. That preserves close-before-next-open ordering and prevents a later archive with revised provider data from retroactively changing a previously observed trail mark.

## Trading and research implications

Signals are generated only after the completed day-T bar and may enter no earlier than the next available open. Existing cost-aware sizing and stop logic remain authoritative. The operations layer records rather than changes v1. It must show that gaps and venue order behavior can cause a fill to differ from the stop reference. No personal operational record becomes prospective-holdout evidence or a tuning input.

## Alternatives considered

- Direct broker integration: rejected for the first release because credentials, venue semantics, and failure controls would expand the risk boundary before the daily workflow is proven.
- A dashboard-only feature: rejected because the owner needs durable decisions and execution facts, not a transient display.
- A new strategy with take-profit targets: rejected because it would change frozen v1 and require a separate research protocol.

## Test and validation plan

- Unit-test deterministic ticket sizing, stop calculation, and rejection conditions from synthetic scanner/portfolio inputs.
- Test append-only ledger validation, event ordering, duplicate refusal, and provenance mismatch failure.
- Test no same-day execution, no risk-cap bypass, and no mutation of prospective evidence.
- Run `pytest -q`, `ruff check src tests scripts`, experiment/knowledge registry checks, and a CLI integration fixture.

## Simplification outcome

Reused `PortfolioBacktestConfig`, `ExecutionCostModel`, and `risk.py` for all sizing, stops, trailing stops, cost-aware fills, and caps. Kept one local JSONL ledger and one focused CLI instead of adding a database, broker abstraction, position-management service, or duplicate strategy engine. The remaining explicit schema validation is justified by append-only/provenance and risk-boundary failure modes.

## Compound outcome

Updated ADR-009, architecture, risk model, roadmap, and current state. Added `docs/solutions/engineering/separate-paper-planning-from-recorded-fills.md` because the separation of completed-close planning, approval, later paper fill, and first-observed trailing marks is reusable for any next-open paper workflow.

## Documentation and memory updates

Updated README, architecture, risk model, roadmap, current state, this plan, ADR-009, CLI documentation, and solution memory. Dashboard projection remains intentionally deferred until the local CLI/ledger path has operating evidence.

## Implementation plan

1. [x] Define operations configuration, canonical scanner-observation input, and append-only ledger schema.
2. [x] Implement deterministic candidate/ticket generation by reusing existing strategy/risk/execution rules.
3. [x] Implement ledger validation and derived position state.
4. [x] Add a CLI daily brief and fixture-driven tests.
5. [x] Defer dashboard projection until the CLI/ledger path is proven.
6. [ ] Simplify, validate, capture compound learning, finalize memory, review, and merge.

## Review checklist

- [x] Scope and acceptance criteria are clear.
- [x] Design is consistent with project invariants.
- [x] Trading/research risks are addressed.
- [x] Test strategy is sufficient.
- [x] Simplification risks are identified.
- [x] Potential compound knowledge destinations are identified.
- [x] Required memory/documentation changes are identified.

## Definition of done

The feature is complete only when the owner can generate a deterministic, approval-only paper brief from canonical inputs; every decision and later fill is provenance-linked and validated; no event can bypass next-open timing or risk limits; tests cover failure modes; documentation is current; and the PR passes the repository lifecycle.
