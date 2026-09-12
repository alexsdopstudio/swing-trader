# ADR-001 — Next-open execution

Status: accepted

## Context

Daily strategy signals use completed closing-bar information.

## Decision

A signal produced from day T data may execute no earlier than the open of T+1.

## Reason

Using the same close that generated the signal creates an unrealistic execution assumption and can introduce look-ahead bias.

## Consequences

Backtests may look worse than same-close simulations, but the model is more credible and reproducible.
