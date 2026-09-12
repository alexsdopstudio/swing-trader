## Summary

<!-- What changes and why? Keep this focused on one logical change. -->

## Design

<!-- Link or name the active design plan. Summarize the proposed design and important trade-offs. For trivial changes, explain why a full design plan is unnecessary. -->

Design plan: `docs/plans/active/...`

## Type of change

- [ ] Feature
- [ ] Fix
- [ ] Refactor
- [ ] Performance
- [ ] Test
- [ ] Documentation
- [ ] Build / CI / Chore
- [ ] Experiment / research

## Acceptance criteria

<!-- List measurable conditions that define success. -->

- [ ]

## Trading / research impact

<!-- Describe affected assumptions, signals, execution timing, risk controls, data sources, metrics, overfitting/data-leakage risks, or reproducibility. Write "None" if not applicable. -->

## Implementation

<!-- Summarize the implementation after the design has been applied. Call out material deviations from the original design. -->

## Simplify

<!-- Record the dedicated simplification pass: complexity removed, abstractions reduced, duplication removed, or `No simplification needed` with rationale. -->

## Validation

- [ ] `pytest -q`
- [ ] `ruff check src tests`
- [ ] Relevant integration/backtest checks completed
- [ ] No look-ahead or data leakage introduced
- [ ] Execution assumptions remain realistic
- [ ] Risk controls remain deterministic
- [ ] All repository content introduced by this PR is written in English

## Compound

<!-- What should a future agent not have to rediscover? Link durable updates/solution notes, or explicitly write `No reusable learning`. -->

## Memory / documentation

- [ ] No durable project knowledge changed
- [ ] Updated relevant docs / ADR / plan / `.ai/current-state.md`
- [ ] Updated `docs/solutions/` when reusable solution knowledge was created
- [ ] Recorded experiment results when applicable
- [ ] Active plan finalized for the post-merge state

## Agent handoff

<!-- Keep this current whenever the lifecycle stage, verified head, next actions, or blockers materially change. This is the canonical transient state for the next AI session. -->

Current stage: Design / Implementation / Simplify / Validation / Compound / Review / Merge
Last verified head: `pending`
Next actions:
- Replace with concrete next action.
Blockers: None

## Formal review

<!-- Complete after Implementation, Simplify, Validation, Compound, and Agent handoff are current. Review the actual final diff, not only this description. -->

Review outcome: `PENDING`

- [ ] Acceptance criteria satisfied
- [ ] Diff reviewed for correctness and edge cases
- [ ] Trading/research integrity reviewed
- [ ] Architecture and maintainability reviewed
- [ ] Simplify outcome reviewed
- [ ] Compound outcome reviewed
- [ ] Tests are meaningful
- [ ] Documentation/memory is current
- [ ] Agent handoff is current for the reviewed head
- [ ] No unresolved review threads
- [ ] Required CI checks are green

## Reviewer notes

<!-- Record findings, risks, trade-offs, follow-ups, or state "No blocking findings." -->

## Merge

- [ ] Formal review outcome is `PASS`
- [ ] Required CI is green
- [ ] No known blockers remain
- [ ] Squash merge title follows Conventional Commits
