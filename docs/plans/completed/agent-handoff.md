# Agent Handoff and Autonomous Session Continuity

Status: Completed

## Goal

Allow a new AI coding session to reconstruct and resume repository work without previous chat history or manual user context transfer.

## Outcome

Implemented a repo-native, vendor-neutral continuity layer based on authoritative workflow state rather than a second manually maintained memory system.

The final session lifecycle is:

```text
Session bootstrap
  -> derive Git/repository/open-PR state
  -> resume active PR or start normal Intake
  -> branch/design/Draft PR
  -> implementation
  -> Simplify
  -> Validation
  -> Compound
  -> formal Review
  -> Merge
```

## Implemented components

### Derived handoff builder

Added `src/swing_trader/handoff.py`.

It:

- inspects local branch, latest commit, working-tree status, and origin;
- recognizes common GitHub HTTPS and SSH remotes;
- discovers open GitHub pull requests with a small read-only standard-library client;
- uses `GITHUB_TOKEN` or `GH_TOKEN` when available but supports public repositories without credentials;
- selects the current-branch PR first;
- selects the only open PR when there is one;
- otherwise selects the most recently updated PR and explicitly labels the choice as inferred;
- includes all open PRs so ambiguity remains visible;
- includes the selected PR body as the canonical transient lifecycle record;
- resolves the plan path referenced by the PR body when available;
- includes local active plans and `.ai/current-state.md`;
- degrades to local-only state when GitHub discovery is disabled or unavailable;
- never switches branches, mutates GitHub, or discards working-tree state.

Generated `.ai/handoff.md` is ignored by Git.

### Autonomous bootstrap

Added `scripts/agent_bootstrap.py`.

One agent-owned command generates:

- `.ai/context.md` via the existing context builder;
- `.ai/handoff.md` via the new handoff builder.

The user is explicitly not responsible for running this command. When an agent has shell access it runs the command itself. When shell access is unavailable, `AGENTS.md` defines the equivalent repository/GitHub-tool reconstruction protocol.

### PR handoff contract

Every PR template now includes:

```text
## Agent handoff

Current stage: ...
Last verified head: ...
Next actions:
- ...
Blockers: None
```

`PR conventions` requires both the section and its four fields.

The PR body remains the canonical transient lifecycle record; generated handoff files are disposable views.

### Workflow integration

Updated:

- `AGENTS.md` with mandatory autonomous session bootstrap/resume behavior;
- `docs/workflow/development-lifecycle.md` with a new Session bootstrap stage;
- `.github/pull_request_template.md` with machine-discoverable handoff state;
- `.github/workflows/pr-conventions.yml` to enforce handoff fields;
- `.github/workflows/ci.yml` with an offline bootstrap smoke test;
- `.github/copilot-instructions.md` as a thin Copilot adapter;
- `CLAUDE.md` as a thin Claude-compatible adapter;
- `README.md` to document autonomous cross-agent continuity;
- `.ai/current-state.md` with the new working capability;
- `.gitignore` so `.ai/handoff.md` remains derived.

## Main synchronization

While this feature was in progress, EXP-0003 completed and was squash-merged into `main` as `8d5b468`.

The feature branch was explicitly synchronized with that new `main` before updating project memory, preserving EXP-0003 temporal-stability results and the prospective holdout protocol.

## Failure behavior

Validated design behavior:

- no GitHub remote -> local-only state;
- non-GitHub remote -> local-only state;
- GitHub/API failure -> local-only state without failing bootstrap;
- detached HEAD -> reported explicitly;
- multiple open PRs -> all exposed and recency-based selection marked inferred;
- current branch matching an open PR -> branch match takes precedence;
- dirty worktree -> reported, never modified;
- missing remote plan -> PR body plus local active plans remain available.

## Simplify outcome

The final implementation intentionally remains small and read-only.

Not introduced:

- vector database;
- external memory service;
- agent registry;
- background daemon;
- branch auto-switching;
- GitHub mutation from bootstrap;
- generic orchestration framework;
- duplicated context-builder implementation.

The existing context builder is reused directly.

## Validation outcome

CI validation includes:

- handoff unit tests for GitHub remote parsing;
- active-PR selection precedence;
- only-PR and multi-PR inference;
- PR body and remote-plan inclusion;
- offline fallback;
- GitHub/API failure fallback;
- `pytest -q`;
- `ruff check src tests`;
- an offline `python scripts/agent_bootstrap.py` smoke test that verifies both generated files are non-empty;
- PR-conventions validation for the handoff section and required fields.

The first full validation run after implementation passed pytest, Ruff, bootstrap smoke, and PR conventions.

## Compound outcome

Reusable learning was captured in:

`docs/solutions/engineering/derive-agent-handoff-from-workflow-state.md`

Core lesson:

> Cross-agent continuity should derive transient state from authoritative workflow objects such as Git, pull requests, plans, CI, and durable repository memory rather than maintaining a second versioned handoff state that can drift.

## Trading / research impact

No trading strategy, signal, execution, risk, market-data, backtest, or experiment semantics changed.

The feature improves research-process safety because new agents can recover frozen experiment constraints, validation state, prospective-holdout rules, and review findings without depending on prior chat context.

## Definition of done

Satisfied when:

- autonomous bootstrap generates both context and handoff;
- remote discovery is read-only and failure tolerant;
- tool-only fallback is documented;
- agents are forbidden from requiring manual context transfer when state is derivable;
- PR handoff state is enforced in CI;
- compatibility adapters point to canonical `AGENTS.md`;
- memory/docs are current;
- Simplify and Compound are complete;
- final CI is green;
- final diff receives formal `PASS` review;
- PR #8 is squash-merged into `main`.
