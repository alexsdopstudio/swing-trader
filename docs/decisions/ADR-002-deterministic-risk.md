# ADR-002 — Deterministic risk controls

Status: accepted

## Context

The project will increasingly use AI agents for research and development.

## Decision

Position sizing, stops, portfolio-risk limits and execution safety controls remain deterministic code. AI components can recommend or explain but cannot bypass these controls.

## Reason

Risk constraints must be testable, reproducible and fail predictably.

## Consequences

Agent outputs are advisory inputs to the research workflow, never an authority above the risk engine.
