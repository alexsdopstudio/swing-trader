# Paper trading operations

Status: Draft

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

## Proposed design

Add a focused `paper_operations` module and CLI that consume a verified daily scanner observation plus a user-supplied operations configuration and append-only ledger.

The CLI will render a deterministic daily brief containing eligible long candidates, proposed entry status, position quantity, initial stop, current trailing stop where applicable, planned initial loss, and explicit rejection reasons. Human actions are explicit ledger events (`approved`, `declined`, `deferred`, `entry_recorded`, `exit_recorded`) rather than implicit state mutations. A later step may derive current positions from those events; it must reject malformed, duplicate, out-of-order, or provenance-mismatched events.

Paper fills and manually reported fills are distinct event sources. A proposed price is never presented as an actual fill. The first implementation will keep broker order type as a human-readable instruction boundary rather than pretending to know every venue's behavior.

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
- Run `pytest -q`, `ruff check src tests`, experiment/knowledge registry checks, and a CLI integration fixture.

## Simplification plan

Reuse existing portfolio/risk/execution types instead of copying their calculations. Keep one narrow append-only ledger format and avoid broker abstractions until a real broker integration is designed.

## Compound plan

Update ADR-009 and architecture/current-state memory. Create a solution note only if implementation reveals a reusable separation or ledger-integrity lesson.

## Documentation and memory updates

Update README, architecture, risk model, roadmap, current state, this plan, ADR-009, CLI documentation, and dashboard documentation if a new brief projection is added.

## Implementation plan

1. Define operations configuration, canonical scanner-observation input, and append-only ledger schema.
2. Implement deterministic candidate/ticket generation by reusing existing strategy/risk/execution rules.
3. Implement ledger validation and derived position state.
4. Add a CLI daily brief and fixture-driven tests.
5. Add dashboard projection only after the CLI/ledger path is proven.
6. Simplify, validate, capture compound learning, finalize memory, review, and merge.

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
