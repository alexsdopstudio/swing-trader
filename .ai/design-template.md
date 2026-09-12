# Design Plan

Status: Draft

## Problem

Describe the problem or opportunity and why it matters.

## Goals

- Define the intended outcome.
- State measurable acceptance criteria.

## Non-goals

- Explicitly list what this change will not attempt to solve.

## Relevant context

List affected modules, ADRs, strategy assumptions, prior experiments, and current limitations.

## Proposed design

Describe the intended architecture and implementation approach before writing production code.

Include where relevant:

- components/modules affected;
- public interfaces and data structures;
- data flow and execution timing;
- persistence or migration behavior;
- configuration changes;
- failure handling and edge cases.

## Trading and research implications

Address applicable risks:

- look-ahead bias;
- survivorship bias;
- execution realism;
- transaction costs/slippage;
- deterministic risk controls;
- data leakage;
- overfitting;
- reproducibility.

Write `None` only when none of these are applicable.

## Alternatives considered

Record meaningful alternatives and why they were rejected.

## Test and validation plan

Describe unit, integration, backtest, regression, and manual checks required before merge.

## Documentation and memory updates

List ADRs, strategy docs, architecture docs, `.ai/current-state.md`, experiment records, or other durable memory that must change.

## Implementation plan

1. List the implementation steps in dependency order.
2. Keep each step independently understandable.
3. Include tests and documentation as part of implementation, not as afterthoughts.

## Review checklist

- [ ] Scope and acceptance criteria are clear.
- [ ] Design is consistent with project invariants.
- [ ] Trading/research risks are addressed.
- [ ] Test strategy is sufficient.
- [ ] Required memory/documentation changes are identified.

## Definition of done

State the conditions that must be true before the PR can receive a `PASS` review and be merged.