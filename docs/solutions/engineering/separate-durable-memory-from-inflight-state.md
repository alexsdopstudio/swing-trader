# Separate Durable Memory from In-Flight Work State

## Problem

Long-lived project knowledge and short-lived implementation state have different lifecycles.

Architecture, domain rules, ADRs, research results, and reusable lessons should remain stable and versioned. In contrast, the exact branch, PR head SHA, CI state, review status, and next action can change several times within one hour.

Putting both categories into one manually maintained memory file creates stale state, noisy commits, and merge conflicts. Keeping in-flight state only inside one chat makes work impossible to resume reliably with another agent.

## Root cause

The system needs both:

- **durable semantic memory** — what the project knows and intends to preserve;
- **derived operational state** — where a specific task currently is in its lifecycle.

They should be connected, but they should not have the same source of truth.

## Reusable solution

Keep durable knowledge in version-controlled repository sources such as:

- architecture/domain docs;
- ADRs;
- active/completed plans;
- current-state memory;
- solution notes;
- experiment records.

Keep in-flight task truth in the systems that already own it:

- branch/head SHA;
- pull-request body and diff;
- CI/check runs;
- reviews and unresolved threads.

Generate a **derived handoff** from those sources for convenience. The handoff may be a PR comment, artifact, or local generated file, but it must remain replaceable and must never override its underlying sources.

## Why this compounds well

A future agent can resume by reading a compact handoff first, then verify details against the repository/PR. No human needs to reproduce the previous conversation, and no model-specific memory system becomes mandatory.

This separation also allows multiple active PRs because each task carries its own operational state rather than competing for one global mutable `active-task` file.

## Failure handling

If the generated handoff is stale or unavailable:

1. inspect the PR head and diff;
2. inspect the PR body;
3. inspect current checks;
4. inspect reviews/unresolved threads;
5. inspect the active plan and durable project memory;
6. regenerate the handoff.

Do not ask the user to manually reconstruct technical context that remains available in those sources.

## Evidence

PR #9 introduced a deterministic handoff builder and GitHub Actions workflow. The first integration run exposed a missing Python import bootstrap; fixing the builder itself made it runnable from a fresh checkout without requiring package installation or user setup.

The successful workflow then generated a machine-readable artifact and automatically upserted a marked PR handoff comment containing branch/SHA, lifecycle stage, active plans, checks, changed files, and next actions.

## References

- `docs/decisions/ADR-008-automated-agent-handoff.md`
- `docs/workflow/agent-session-handoff.md`
- `src/swing_trader/handoff.py`
- `.github/workflows/agent-handoff.yml`
- PR #9
