# Automated Agent Handoff

Status: Active

## Goal

Make development continuity independent from any single chat or LLM session. A new AI agent with repository access must discover in-flight work, reconstruct PR/branch/check context, identify the lifecycle stage, and continue without asking the user to restate project history or run manual commands.

## Problem

Durable project memory already lives in the repository, but active work may exist only on an open feature branch and pull request. A new session starting from `main` can therefore miss where the previous agent stopped.

Manual copy/paste handoffs are out of scope. Repository and GitHub metadata must provide the handoff automatically.

## Design

Use the pull request as the canonical transport for in-flight state.

The system has three layers:

1. **Agent startup protocol** in `AGENTS.md` and workflow docs. New agents inspect open PRs before opening new work, read the latest automated handoff comment, then inspect PR body/diff/checks/review threads and the active plan.
2. **Deterministic handoff builder** in `src/swing_trader/handoff.py` plus `scripts/build_handoff.py`. It generates `handoff.json` and `handoff.md` from local repository state plus PR metadata supplied by the caller.
3. **GitHub Actions automation** in `.github/workflows/agent-handoff.yml`. Pull-request lifecycle events generate handoff artifacts, upload them, and create/update one PR comment marked with `<!-- agent-handoff -->`.

No user action is required. Local AI agents may invoke the builder automatically when working outside GitHub Actions.

## Active-work discovery

A new GitHub-capable agent must:

1. read `AGENTS.md` from `main`;
2. list open PRs;
3. inspect their latest automated handoff comments;
4. continue the matching in-flight task rather than opening a duplicate branch/PR;
5. reconstruct missing details from PR metadata, diff, checks, active plans, and project memory before asking the user anything.

Multiple PRs are supported; each PR carries its own handoff state.

## Generated handoff

`handoff.json` records:

- schema version;
- repository;
- PR number/title/url;
- base branch;
- head branch and SHA;
- draft state;
- inferred lifecycle stage;
- latest commit;
- changed files;
- active plan paths;
- current-state path;
- check-run summary supplied by CI;
- next recommended actions;
- generated timestamp.

`handoff.md` is the concise agent-readable projection. Local `.ai/handoff.md` and `.ai/handoff.json` are derived state and ignored by Git.

## Lifecycle inference

Use conservative deterministic inference from PR state/body:

- `Review outcome: PASS` -> `review-passed`;
- `CHANGES REQUESTED` -> `changes-requested`;
- `BLOCKED` -> `blocked`;
- draft + implementation pending -> `design`;
- other draft -> `implementation`;
- ready PR without PASS -> `review`.

If uncertain, instruct the next agent to inspect the PR body and diff rather than inventing state.

## Automated PR handoff

The workflow must upsert exactly one top-level PR comment containing `<!-- agent-handoff -->` and upload `handoff.json` / `handoff.md` as an artifact.

The comment includes branch/head SHA, stage, active plans, check summary, next actions, and a resume instruction.

## Agent operating rule

Agents own handoff maintenance. They must not ask the user to copy context between sessions or manually run bootstrap commands when repository/GitHub access is available. User input is reserved for genuinely unresolved product, risk, architecture, or scope decisions.

## Security

The workflow uses only repository-scoped permissions needed for read access, check inspection, and PR-comment updates. No trading credentials, broker permissions, external memory services, or secrets are introduced.

## Non-goals

- no vector database or external memory SaaS;
- no chat-history scraping;
- no vendor-specific agent framework;
- no user-maintained status file;
- no automatic merge based only on handoff state;
- no replacement for formal review and CI gates.

## Tests

- lifecycle-stage inference;
- next-action inference;
- JSON/Markdown generation;
- repository-state discovery;
- feature PR exercises the workflow itself;
- existing pytest and Ruff suite.

## Simplify plan

Keep generation stdlib-only. Do not add a database, service, GitHub SDK dependency, or LLM call.

## Compound plan

Capture the distinction between durable project memory and ephemeral in-flight work if it proves reusable.

## Acceptance criteria

- new sessions can discover and resume open work without user-provided chat context;
- handoff artifacts are generated automatically on PR lifecycle changes;
- one marked PR comment is created/updated automatically;
- stage, branch/SHA, active plans, changed files, checks, and next actions are included;
- local agents can generate equivalent handoff files without external dependencies;
- `AGENTS.md` forbids manual context shuttling when repo access exists;
- tests/lint/conventions pass;
- Simplify, Compound, formal review, and squash merge complete.
