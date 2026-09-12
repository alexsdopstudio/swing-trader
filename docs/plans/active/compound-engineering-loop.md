# Compound Engineering Loop

Status: Draft

## Problem

The repository already has a design-first, branch-and-PR gated development lifecycle with durable project memory. However, completed work does not yet have an explicit mechanism for turning implementation and review lessons into reusable knowledge for future tasks.

Without that feedback loop, AI agents can still rediscover the same engineering mistakes, repeat failed research directions, or re-evaluate settled trade-offs from scratch.

## Goals

- Extend the development lifecycle with explicit `Simplify` and `Compound` stages.
- Keep the final formal review over the complete final diff.
- Add a durable solution-memory structure for reusable engineering and trading-research lessons.
- Make solution memory discoverable by the AI context builder.
- Standardize how PRs record simplification work and reusable learnings.
- Preserve the existing gated review and merge guarantees.

## Non-goals

- Do not vendor or depend on an external compound-engineering plugin.
- Do not add a vector database or semantic search service.
- Do not automatically create solution records for every PR.
- Do not change trading strategy behavior, execution rules, or risk controls.
- Do not replace ADRs, plans, experiments, or current-state memory.

## Relevant context

Current project memory is split across:

- `AGENTS.md` for agent instructions;
- `ARCHITECTURE.md` and domain/product docs for system behavior;
- `docs/decisions/` for durable decisions;
- `docs/plans/` for active/completed work;
- `.ai/current-state.md` for project state;
- `experiments/` for quantitative research history.

The current lifecycle is:

`Intake -> Dedicated branch -> Design -> Draft PR -> Implementation -> Validation -> PR Review -> Merge`

The final review must continue to inspect the complete diff that will be merged.

## Proposed design

### Canonical lifecycle

Change the lifecycle to:

`Intake -> Dedicated branch -> Design -> Draft PR -> Implementation -> Simplify -> Validation -> Compound -> Formal Review -> Squash Merge`

`Compound` intentionally occurs before the final formal review. If the compound stage creates or changes repository files, those changes must be included in the final reviewed diff.

If formal review requests changes, the loop returns to implementation and then repeats Simplify, Validation, Compound, and Review as applicable.

### Simplify stage

Before validation is considered final, inspect the implementation specifically for unnecessary complexity:

- remove dead code;
- reduce unnecessary abstractions;
- remove duplication;
- simplify interfaces and data flow;
- prefer explicit domain logic over clever indirection;
- confirm new complexity is justified by requirements or evidence.

The PR template will require a short simplification record, including `No simplification needed` when appropriate.

### Compound stage

Before final review, ask:

`What did this change teach us that a future agent should not have to rediscover?`

Possible outcomes:

1. `No reusable learning` — record this explicitly in the PR.
2. Update an existing durable source of truth such as an ADR, architecture doc, risk rule, or experiment record.
3. Create a reusable solution note under `docs/solutions/` when the lesson is a recurring problem/solution pattern rather than a project-wide decision.

### Solution memory

Add:

```text
docs/solutions/
  README.md
  engineering/
    README.md
  trading-research/
    README.md
```

Solution notes should capture:

- problem/symptoms;
- root cause;
- reusable solution;
- when the lesson applies;
- tests/checks to require;
- references to relevant ADRs, modules, experiments, or PRs.

Add `.ai/solution-template.md` as the canonical template.

Solution notes are different from ADRs:

- ADR = a durable decision the project intends to follow;
- solution note = reusable knowledge learned while solving a recurring class of problem.

### Context builder integration

Update the context builder to include a lightweight solution-memory index rather than blindly embedding every future solution file.

Initially `docs/solutions/README.md` acts as the curated index and is included in generated AI context. Category README files document the taxonomy. Future semantic retrieval can replace or augment this when repository scale warrants it.

### PR workflow integration

Update the PR template with explicit sections:

- `Simplify`
- `Compound`

Update PR-convention CI to require these sections.

The final formal review remains after Compound so the reviewer sees all durable knowledge changes.

## Trading and research implications

No trading behavior changes are introduced.

The Compound stage should improve research safety over time by preserving lessons about:

- look-ahead and data leakage;
- execution timing;
- survivorship bias;
- transaction-cost assumptions;
- deterministic risk controls;
- parameter robustness and overfitting;
- failed hypotheses and experiment results.

Research learnings that are experiment-specific belong in `experiments/`; recurring cross-experiment lessons may additionally become `docs/solutions/trading-research/` notes.

## Alternatives considered

### Adopt the external compound-engineering plugin directly

Rejected as a repository dependency. The project should keep its workflow portable across ChatGPT, Codex, Copilot, Claude, and other agents.

### Put Compound after formal review

Rejected because compound work may modify repository files, making the prior review stale.

### Store all lessons only in ADRs

Rejected because many useful lessons are reusable problem/solution patterns rather than architectural decisions.

### Add a vector database now

Rejected as unnecessary complexity at the current repository size.

## Test and validation plan

- Update context-builder tests to verify the solution-memory index is included when present.
- Run `pytest -q`.
- Run `ruff check src tests`.
- Verify PR-convention CI accepts the new required PR sections.
- Review the final diff for lifecycle consistency across `AGENTS.md`, `CONTRIBUTING.md`, workflow docs, PR template, and ADRs.

## Documentation and memory updates

Expected updates:

- `AGENTS.md`
- `CONTRIBUTING.md`
- `docs/workflow/development-lifecycle.md`
- `.github/pull_request_template.md`
- `.github/workflows/pr-conventions.yml`
- `.ai/design-template.md`
- `.ai/solution-template.md`
- `docs/solutions/`
- `docs/decisions/ADR-007-compound-engineering-loop.md`
- `.ai/current-state.md`
- context builder and tests

## Implementation plan

1. Add solution-memory taxonomy and template.
2. Update the lifecycle and contributor/agent instructions with Simplify and Compound stages.
3. Extend PR template and convention CI.
4. Add ADR-007.
5. Include solution-memory index in the generated AI context.
6. Add/update tests.
7. Update current-state memory.
8. Perform a simplify pass on the implementation itself.
9. Record the compound outcome for this PR.
10. Run validation and formal review.

## Review checklist

- [x] Scope and acceptance criteria are clear.
- [x] Design is consistent with project invariants.
- [x] Trading/research risks are addressed.
- [x] Test strategy is sufficient.
- [x] Required memory/documentation changes are identified.

## Definition of done

- Canonical lifecycle includes Simplify and Compound in a consistent order across repository instructions.
- PR template and convention CI require both stages.
- Solution memory has documented taxonomy and template.
- Generated AI context surfaces the solution-memory index.
- Unit tests and lint pass.
- Formal review outcome is `PASS`.
- Required CI is green.
- The PR is squash-merged into `main`.
