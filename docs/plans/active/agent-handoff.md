# Agent Handoff and Autonomous Session Continuity

Status: Draft

## Problem

The repository already stores durable project memory in `AGENTS.md`, `.ai/current-state.md`, architecture/domain docs, plans, decisions, solutions, experiments, and pull requests. However, starting a new AI session can still require a human to explain which pull request is active, which branch should be resumed, and what the previous agent was doing.

This creates avoidable dependence on chat history and manual user coordination.

## Goals

- Allow a new AI coding session to reconstruct current work without relying on previous chat history.
- Require no manual user steps such as running context scripts, copying summaries, selecting branches, or describing the current lifecycle stage.
- Keep pull requests and versioned repository memory as the source of truth rather than introducing a second manually maintained task state.
- Generate a derived `.ai/handoff.md` that summarizes local Git state, open pull requests, the inferred active pull request, its current PR body, and relevant active design plan.
- Generate `.ai/context.md` and `.ai/handoff.md` together through one autonomous bootstrap command.
- Define a tool-independent fallback protocol for agents that can access GitHub/repository files but cannot execute the local bootstrap script.
- Make session-start and session-handoff behavior mandatory in `AGENTS.md` and the development lifecycle.
- Add a dedicated `Agent handoff` section to pull requests so transient lifecycle state and next actions are explicit and machine-discoverable.

## Non-goals

- Do not create a vector database, external memory service, issue-based state machine, or agent orchestration server.
- Do not write generated handoff/context files to Git history.
- Do not automatically mutate or merge pull requests from the bootstrap script.
- Do not automatically switch branches based on an ambiguous set of open pull requests.
- Do not depend on a single LLM vendor or IDE.
- Do not store chat transcripts in the repository.

## Relevant context

Existing memory and workflow components:

- `AGENTS.md` is the canonical agent guide.
- `src/swing_trader/context_builder.py` and `scripts/build_context.py` generate local working context.
- `.ai/context.md` is derived and ignored by Git.
- PR descriptions already carry Design, Implementation, Simplify, Validation, Compound, Review, and Merge state.
- `docs/plans/active/` contains active design plans.
- `.github/copilot-instructions.md` points GitHub Copilot to `AGENTS.md`.
- `docs/workflow/development-lifecycle.md` defines autonomous AI ownership of the full branch/PR/review/merge lifecycle.

At design time, PR #7 (`experiment/exp-0003-temporal-stability`) is intentionally paused while this independent feature is implemented.

## Proposed design

### 1. Derived handoff state

Add `src/swing_trader/handoff.py`.

The module will:

- inspect the local repository branch, latest commit, working-tree status, and GitHub remote;
- derive the GitHub `owner/repo` slug from common HTTPS and SSH remote forms;
- query the GitHub REST API for open pull requests when network access is available;
- use `GITHUB_TOKEN` or `GH_TOKEN` when present, while supporting public repositories without a token;
- infer the active pull request using deterministic rules:
  1. prefer a pull request whose head branch matches the current local branch;
  2. if exactly one pull request is open, select it;
  3. otherwise select the most recently updated pull request and explicitly mark the selection as inferred rather than certain;
- include all open pull requests in the generated handoff so an agent can inspect ambiguity without asking the user;
- include the selected PR body because it is the canonical transient lifecycle record;
- attempt to include the active design plan referenced by or changed in the selected PR;
- gracefully degrade to local-only handoff when GitHub is unavailable.

The generated `.ai/handoff.md` is derived working state and will be ignored by Git.

### 2. Autonomous bootstrap

Add `scripts/agent_bootstrap.py`.

One command will:

1. locate the repository root;
2. generate `.ai/context.md` using the existing context builder;
3. generate `.ai/handoff.md` using the new handoff builder;
4. print a concise machine/human-readable summary of the inferred active PR and generated paths.

This command is intended to be executed by the AI agent automatically, not by the user.

### 3. Session protocol

Update `AGENTS.md` and `docs/workflow/development-lifecycle.md` so every AI agent must:

- bootstrap repository state before substantive work in a new session;
- run `python scripts/agent_bootstrap.py` when a shell is available;
- otherwise reconstruct the same state using repository/GitHub tools: read `AGENTS.md`, current state, open PRs, selected PR body, active plan, and relevant CI/review state;
- resume the active PR when the intent is unambiguous;
- never ask the user to copy context, run bootstrap scripts, select a branch, or restate work that can be derived from repository/GitHub state;
- keep the PR `Agent handoff` section current at meaningful lifecycle transitions and before yielding control when possible.

An abruptly terminated session cannot guarantee a final write, so the protocol relies on frequent PR-state updates during normal work rather than a single end-of-session save action.

### 4. PR handoff contract

Update `.github/pull_request_template.md` with:

```text
## Agent handoff

Current stage: ...
Last verified head: ...
Next actions:
- ...
Blockers: None
```

Update `.github/workflows/pr-conventions.yml` so the section is mandatory. This makes the transient state machine discoverable to any future agent through GitHub alone.

### 5. Compatibility

Keep `AGENTS.md` canonical. Existing Copilot instructions remain a thin adapter. Add a small root `CLAUDE.md` adapter that instructs Claude-compatible coding agents to read `AGENTS.md` and execute the autonomous bootstrap protocol when shell access exists.

Do not add broad vendor-specific configuration beyond thin pointers unless a future need is demonstrated.

## Failure handling and edge cases

- No `origin` remote: generate local-only handoff and explain that remote PR discovery is unavailable.
- Non-GitHub remote: generate local-only handoff.
- GitHub API unavailable or rate-limited: continue with local state and active plans; do not fail bootstrap.
- Detached HEAD: report detached state and rely on open PR discovery.
- Multiple open PRs: include all; deterministic newest-updated inference is marked explicitly as inferred.
- Current branch matches an open PR: branch match always wins over recency.
- Dirty working tree: preserve and report it; bootstrap never discards or modifies user/agent changes.
- PR has no discoverable active plan: include the PR body and local active plans instead.
- Private repository without credentials: remote state may be unavailable; local bootstrap still succeeds.

## Trading and research implications

No trading strategy, execution, risk, market-data, or backtest behavior changes.

The feature improves research reproducibility indirectly by making it less likely that a new agent silently loses active experiment constraints, frozen parameters, review findings, or next actions.

## Alternatives considered

### Version a manually maintained `.ai/handoff.md`

Rejected because it can become stale and would require every active branch to synchronize transient state back to `main`, conflicting with the branch/PR workflow.

### Store active state in a GitHub issue

Rejected because pull requests already contain the lifecycle state and are naturally tied to the changed code/design.

### Auto-checkout the inferred PR branch

Rejected for the first version because branch switching is destructive when local work exists and ambiguous when multiple PRs are active. The agent receives enough derived state to perform a safe checkout itself when appropriate.

### External memory/vector service

Rejected as unnecessary complexity. Repository memory plus GitHub PR state is sufficient at the current project scale.

## Test and validation plan

- Unit-test GitHub remote parsing for HTTPS and SSH forms.
- Unit-test active-PR selection rules.
- Unit-test handoff generation with a current-branch PR match.
- Unit-test multiple-PR fallback and explicit inference reason.
- Unit-test graceful GitHub/API failure behavior.
- Unit-test active-plan inclusion with a fake GitHub client.
- Verify generated `.ai/handoff.md` and `.ai/context.md` are ignored by Git.
- Run `pytest -q`.
- Run `ruff check src tests`.
- Verify PR conventions with the new mandatory handoff section.
- Execute `python scripts/agent_bootstrap.py` in CI as a local-only smoke test with remote calls disabled or mocked.

## Simplification plan

Keep the implementation standard-library-only and read-only with respect to Git/GitHub. Avoid agent registries, databases, background daemons, branch mutation, or generic orchestration frameworks.

Reuse the existing context builder rather than creating a second context aggregation system.

## Compound plan

Expected reusable learning: cross-agent continuity works best when transient state is derived from authoritative workflow objects (Git + PR + plan) rather than stored in a second manually maintained memory file.

If confirmed, record this as a workflow/engineering solution or ADR only if it adds durable value beyond the updated lifecycle documentation.

## Documentation and memory updates

- `AGENTS.md`
- `docs/workflow/development-lifecycle.md`
- `.github/pull_request_template.md`
- `.github/workflows/pr-conventions.yml`
- `.github/copilot-instructions.md`
- `README.md`
- `.ai/current-state.md`
- `.gitignore`
- optional `CLAUDE.md` compatibility pointer
- active plan moved to `docs/plans/completed/` before final review

## Implementation plan

1. Add handoff state model, GitHub discovery, active-PR inference, and Markdown rendering.
2. Add autonomous bootstrap script that generates both context and handoff.
3. Add tests for parsing, inference, rendering, and degraded/offline behavior.
4. Add PR handoff contract and CI validation.
5. Update agent/lifecycle instructions and compatibility adapters.
6. Update README/current-state memory.
7. Perform Simplify.
8. Run validation.
9. Perform Compound and finalize the plan.
10. Perform formal final-diff review and squash merge after green CI.

## Review checklist

- [x] Scope and acceptance criteria are clear.
- [x] Design is consistent with project invariants.
- [x] Trading/research risks are addressed.
- [x] Test strategy is sufficient.
- [x] Simplification risks are identified.
- [x] Potential compound knowledge destinations are identified.
- [x] Required memory/documentation changes are identified.

## Definition of done

The feature is complete when a new AI session can derive local state plus active GitHub PR state without user-provided context, one autonomous bootstrap command generates both context and handoff files, the fallback tool-only protocol is documented, PRs expose machine-discoverable handoff state, tests and lint pass, CI conventions enforce the handoff section, the final diff receives `PASS`, and the PR is squash-merged into `main`.