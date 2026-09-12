# Derive Agent Handoff from Workflow State

## Problem

Cross-session AI development needs enough transient state to answer:

- which logical change is active;
- which branch and pull request should be resumed;
- what lifecycle stage the work is in;
- what was last verified;
- what should happen next;
- whether anything is blocked.

A tempting solution is a manually maintained, version-controlled `handoff.md`. That creates a second state machine beside Git, pull requests, plans, CI, and repository memory. The duplicate state can become stale, especially when a session ends unexpectedly or multiple branches exist.

## Root cause

The real workflow state already exists in authoritative systems:

- Git records branch/head/working-tree state;
- pull requests record the active logical change and lifecycle discussion;
- active plans record design intent;
- CI/reviews record validation state;
- durable repository memory records architecture, decisions, research, and current project state.

Copying that state into another manually maintained file creates synchronization work without adding authority.

## Reusable solution

Treat the pull request as the canonical transient lifecycle record and derive session handoff from authoritative workflow objects.

At session start:

1. inspect local Git state;
2. discover open pull requests;
3. prefer the PR matching the current branch;
4. otherwise use an explicitly documented inference rule and expose ambiguity;
5. read the selected PR body and its `Agent handoff` section;
6. read the referenced active plan and durable repository memory;
7. inspect current CI/review state before mutating or merging;
8. generate local context/handoff files only as disposable derived views.

Generated context files should be ignored by Git. They are caches/views, not sources of truth.

## Handoff contract

Keep a small machine-discoverable section inside the PR itself:

```text
## Agent handoff

Current stage: ...
Last verified head: ...
Next actions:
- ...
Blockers: None
```

Update it at meaningful lifecycle transitions rather than relying on one final end-of-session save. Abrupt termination may prevent a final write, while incremental PR updates leave a useful recovery point.

## Failure behavior

Continuity infrastructure should degrade safely:

- if GitHub is unavailable, use local Git, active plans, and durable repository state;
- if multiple PRs are open, expose all of them and mark any recency-based selection as inferred;
- never discard dirty working-tree state;
- never auto-switch branches when selection is ambiguous;
- never require the user to manually transfer context that can be reconstructed.

## Why this compounds

Every future agent starts from the same workflow evidence instead of a vendor-specific chat memory. The approach works across coding agents as long as they can read repository/GitHub state or execute the bootstrap script.

It also keeps the repository portable: no external vector store, daemon, or proprietary memory service is required for basic continuity.

## Tests and checks

Require coverage for:

- GitHub remote parsing;
- active-PR selection precedence;
- multiple-PR ambiguity/inference;
- active-plan retrieval;
- remote/API failure fallback;
- generated context/handoff files being ignored;
- an offline bootstrap smoke test in CI;
- PR convention checks requiring the handoff contract.

## References

- `AGENTS.md`
- `docs/workflow/development-lifecycle.md`
- `src/swing_trader/handoff.py`
- `scripts/agent_bootstrap.py`
- `.github/pull_request_template.md`
- PR #8 — autonomous agent session handoff
