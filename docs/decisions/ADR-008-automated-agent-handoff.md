# ADR-008 — Automated Agent Handoff

Status: Accepted

## Context

The repository already stores durable architecture, workflow, strategy, risk, experiment, and solution memory. That is sufficient for long-term project continuity but not always sufficient for resuming an in-flight task because the latest state can live only on an open feature branch and pull request.

Requiring the user to transfer chat context or manually maintain a status file would make AI-driven development dependent on one conversation and would create a new source of stale state.

## Decision

Use the pull request as the canonical transport for in-flight agent state and generate a derived handoff automatically.

For same-repository PRs, GitHub Actions will create/update one top-level comment marked with `<!-- agent-handoff -->` and upload machine-readable handoff artifacts.

The handoff is generated deterministically from repository state plus GitHub PR/check metadata. It does not call an LLM and does not use an external memory service.

New agents must inspect open PRs and their handoffs before creating new work. When repository/GitHub access exists, agents must reconstruct context themselves rather than asking the user to copy prior chat history or execute bootstrap commands.

## Rationale

- Pull requests already contain branch identity, diff, design/implementation notes, reviews, checks, and merge state.
- A generated handoff can summarize these facts without becoming a competing source of truth.
- PR comments are accessible to GitHub-capable agents across vendors and sessions.
- Local agents can generate equivalent derived files with stdlib-only tooling.
- Avoiding a manually maintained global active-task pointer permits multiple independent PRs and reduces coordination conflicts.

## Consequences

Positive:

- sessions and model vendors become replaceable;
- the user is removed from routine context-transfer work;
- resumed work is anchored to auditable repository state;
- duplicate branches/PRs become less likely;
- handoff generation is deterministic and testable.

Tradeoffs:

- automated handoff comments may briefly show checks as pending because check runs are concurrent;
- the handoff is derived and can become stale if GitHub automation fails;
- new workflow files cannot fully exercise their own `pull_request` automation until merged to the base branch, so first-use validation occurs immediately after adoption.

These tradeoffs do not weaken the existing review/CI lifecycle because the handoff never authorizes merge by itself.

## Alternatives rejected

### Chat memory as the primary handoff

Rejected because it is model/session-specific and not reliably available to other agents.

### Committed `.ai/handoff.md` updated manually

Rejected because it would become stale, create unnecessary commits, and make the user/agent maintain duplicate mutable state.

### External vector database or memory SaaS

Rejected for now because project scale does not justify the operational complexity and it would not solve PR lifecycle state as directly as GitHub metadata.

### Single global active-PR file

Rejected because multiple PRs may legitimately coexist and a global mutable pointer would create contention and merge conflicts.
