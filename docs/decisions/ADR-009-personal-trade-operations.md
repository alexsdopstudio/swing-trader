# ADR-009 — Personal trade-operations boundary

Status: accepted

## Context

The repository already produces deterministic daily scanner observations and a cost-aware portfolio replay, but those outputs are not yet a usable daily workflow for the owner. The product goal is to support repeatable, risk-bounded decisions that can be evaluated by net results, without misrepresenting historical research as a profit guarantee.

## Decision

Add a personal trade-operations layer with these boundaries:

- initial mode is paper-only and requires explicit human approval for every candidate;
- proposed quantity, initial stop, trailing stop, and portfolio-cap eligibility are derived only from existing deterministic strategy, risk, and execution rules;
- operational records are append-only and preserve the signal observation, decision, proposed values, and later paper or manually reported execution;
- the layer neither transmits broker orders nor stores broker credentials;
- paper or manual-live records remain operational evidence and cannot tune frozen v1 or satisfy the prospective validation gate.

## Consequences

The owner can use a daily brief and ticket workflow before prospective validation matures, but the product must state that candidate status, stop levels, and expected fills are not guarantees. Any future broker integration requires a separate reviewed decision covering authorization, credentials, venue-specific order behavior, failure controls, and regulatory scope.

## Implementation boundary

The first implementation accepts only verified `daily-scan-history` archives, a narrow paper-only account configuration, and a local append-only JSONL ledger. A planning ticket uses the completed-bar close solely as a deterministic planning reference and is eligible no earlier than the next available open after its signal date. A human approval precedes a separate paper-entry record, which re-prices from the supplied market reference and recomputes deterministic sizing/caps without accepting a manual quantity or fill override.

Open-position trailing stops are derived from the first observed completed scanner marks in the supplied archive history. The ledger and brief have no broker adapter, credential field, or network order path.
