# Separate Paper Planning from Recorded Fills

## Problem

A daily scanner knows the completed close that created a signal, but not the next available open where a long entry could occur. Treating a close-based sizing preview as an executed trade hides the timing boundary and lets a later manual fill or quantity bypass deterministic risk controls.

## Symptoms

- A ticket claims to be filled on the same date as its completed-close signal.
- A human changes ticket quantity, fill, stop, or risk budget while recording an entry.
- An entry after a gap retains stale close-based size without a fresh cash/risk check.
- A later provider revision changes a historical trailing-stop mark.

## Root cause

Planning, approval, and execution facts are collapsed into one mutable trade record. That loses the distinction between information available at the close, the later market reference, and the deterministic paper fill derived from that reference.

## Reusable solution

Use a verified completed-bar observation to create an immutable planning ticket. Require an explicit approval event before recording a separate entry event with a market reference dated after the signal. Re-price the paper fill, stop, units, fee, and initial loss through the existing cost/risk model at append time; do not accept a quantity or fill override.

Keep decisions and fills in a line-oriented append-only ledger with ticket, archive, and config digests. Derive current positions from validated events. For close-derived trailing stops, consume daily observations in information-time order and use the first supplied archive for a completed market date rather than a later revised copy.

## When this applies

- Daily or slower paper-trading workflows with next-open execution.
- Human approval layers on top of deterministic strategy/risk code.
- Systems that preserve both operational scanner history and later fill records.

## When this does not apply

This pattern does not replace a venue-specific broker adapter, an intraday event feed, or an immutable administrator-proof ledger. Those systems need their own authorization, timestamp, failure-control, and regulatory design.

## Tests and checks

- Reject entry dates on or before the ticket signal date.
- Recompute entry units from the paper market reference and current conservative cash/risk state.
- Reject duplicate decisions/fills, timestamp reordering, and provenance mismatches.
- Verify trailing stops never move down and ignore scanner archives later than the current brief.
- Verify the operational ledger remains ineligible for prospective-holdout validation.

## References

- `docs/decisions/ADR-001-next-open-execution.md`
- `docs/decisions/ADR-002-deterministic-risk.md`
- `docs/decisions/ADR-009-personal-trade-operations.md`
- `src/swing_trader/paper_operations.py`
- `tests/test_paper_operations.py`
