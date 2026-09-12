# Automated Agent Handoff

Status: Completed

## Goal

Make development continuity independent from any single chat or LLM session. A new AI agent with repository access can discover in-flight work, reconstruct PR/branch/check context, identify the lifecycle stage, and continue without asking the user to restate project history or run manual commands.

## Implemented design

The pull request is the canonical transport for fast-changing in-flight state.

Implemented layers:

1. `AGENTS.md`, `CONTRIBUTING.md`, and workflow docs define an autonomous startup/resume protocol.
2. `src/swing_trader/handoff.py` deterministically builds structured handoff state from repository + PR/check metadata.
3. `scripts/build_handoff.py` generates local or CI handoff artifacts without requiring project installation.
4. `.github/workflows/agent-handoff.yml` runs on same-repository PR lifecycle events, uploads `handoff.json` / `handoff.md`, and upserts exactly one PR comment marked `<!-- agent-handoff -->`.
5. the normal context builder consumes generated `.ai/handoff.md` when present.

Generated local handoff/context files are ignored by Git because they are derived state.

## Integration outcome

The workflow was exercised on PR #9 itself.

The first integration run failed because executing `scripts/build_handoff.py` from a fresh checkout did not place `src/` on Python's import path. The fix was made in the script itself rather than adding an installation prerequisite. This preserves the core requirement that an agent can bootstrap handoff state from a fresh clone without user setup.

A subsequent run succeeded through all steps:

- checkout exact PR head;
- collect PR/check metadata;
- generate handoff JSON/Markdown;
- upload handoff artifact;
- create/update the marked PR comment.

The published comment contained repository, PR, branch/head SHA, inferred lifecycle stage, active plan, current checks, changed files, next actions, and the no-manual-context-shuttle resume rule.

## Simplify outcome

The implementation remains stdlib-only and intentionally has no database, GitHub SDK dependency, external memory service, model API, web service, agent framework, or manually maintained global active-task pointer.

GitHub Actions handles GitHub API integration; the Python builder only transforms supplied metadata and local repository state.

No further abstraction was justified.

## Validation outcome

- `pytest -q` passed in CI.
- `ruff check src tests` passed in CI.
- PR conventions passed.
- Agent handoff integration workflow passed.
- Automated PR handoff comment was created and updated by `github-actions[bot]`.
- Handoff artifact upload succeeded.
- No trading strategy, execution, or deterministic risk behavior changed.

## Compound outcome

Reusable lesson:

> Durable project memory and fast-changing in-flight work state need different sources of truth.

The reusable pattern is documented in:

`docs/solutions/engineering/separate-durable-memory-from-inflight-state.md`

The durable project decision is recorded in:

`docs/decisions/ADR-008-automated-agent-handoff.md`

## Acceptance criteria outcome

- new sessions can discover/resume open work without user-provided chat context: satisfied;
- handoff artifacts generated automatically on PR lifecycle events: satisfied;
- one marked PR comment created/updated automatically: satisfied;
- branch/SHA, stage, plans, changed files, checks, and next actions included: satisfied;
- local builder works without external dependencies/project install: satisfied;
- agent instructions prohibit manual context shuttling when repository access exists: satisfied;
- tests/lint/conventions: green;
- Simplify and Compound: complete.

Formal diff review and squash merge remain the final lifecycle gates.
