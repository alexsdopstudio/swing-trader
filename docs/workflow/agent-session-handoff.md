# Agent Session Handoff

This repository treats chat/model sessions as disposable. Durable project knowledge lives in repository files; in-flight work lives on branches and pull requests. A user is not responsible for transferring context between AI agents.

## Startup protocol

An agent with GitHub access must perform this sequence before creating new work:

1. Read `AGENTS.md` from `main`.
2. List open pull requests.
3. Inspect the latest top-level PR comment containing `<!-- agent-handoff -->` for candidate in-flight tasks.
4. Read the matching PR body, head branch, active plan, diff, check state, formal reviews, and unresolved review threads.
5. Read `.ai/current-state.md`, relevant ADRs/solutions/experiments, and architecture/domain docs.
6. Continue the existing branch and PR when they match the requested work.
7. Ask the user only when a material unresolved decision cannot be inferred safely.

Do not ask the user to paste a previous chat, summarize prior work, run context-generation commands, or choose a branch merely because the agent failed to inspect GitHub.

## Automated PR handoff

`.github/workflows/agent-handoff.yml` runs on same-repository pull-request lifecycle events. It:

1. checks out the exact PR head;
2. gathers current PR and check-run metadata;
3. executes `scripts/build_handoff.py`;
4. uploads `handoff.json` and `handoff.md` as a GitHub Actions artifact;
5. creates or updates exactly one PR comment identified by `<!-- agent-handoff -->`.

The PR comment is the default cross-session resume checkpoint because it is accessible to GitHub-capable agents without requiring a local filesystem.

The generated artifact is the machine-readable equivalent and can be consumed by automation.

## Local agent handoff

Agents operating in a local clone may generate derived state themselves:

```bash
python scripts/build_handoff.py
python scripts/build_context.py
```

This writes `.ai/handoff.json`, `.ai/handoff.md`, and `.ai/context.md`. These files are ignored by Git because they are derived working context. Agents should run these commands themselves when useful; they are not instructions for the user.

## Source-of-truth boundaries

Different knowledge belongs in different places:

- `AGENTS.md`, architecture/domain docs, ADRs — durable rules and decisions;
- `.ai/current-state.md` — current project-level state;
- `docs/plans/active/` — intended work for active tasks;
- PR body/reviews/checks/diff — actual in-flight implementation state;
- automated handoff comment/artifact — derived resume checkpoint;
- `docs/solutions/` — reusable learned problem/solution knowledge;
- `experiments/` — quantitative research evidence.

The generated handoff must never override the underlying sources. If it appears stale or inconsistent, inspect the PR/repository state and regenerate it.

## Multiple open PRs

Multiple open PRs are allowed. There is no manually maintained global `active-pr` pointer.

A new agent identifies the relevant task from the user's requested objective plus each PR's title, handoff, active plan, and lifecycle stage. This avoids a single mutable coordination file becoming a bottleneck or merge-conflict source.

## Lifecycle stages

The deterministic handoff builder infers a conservative stage:

- `design`
- `implementation`
- `changes-requested`
- `blocked`
- `review`
- `review-passed`

The stage is guidance for resumption, not authorization to skip gates. Merge still requires the normal formal `PASS` review, green required CI, current memory, and no unresolved blockers.

## Failure recovery

If the automated handoff workflow is unavailable or stale, an agent must reconstruct state directly from:

1. the PR head and diff;
2. the PR body;
3. check runs;
4. review submissions and unresolved threads;
5. active plans and repository memory.

Failure of the convenience layer is not a reason to ask the user to manually reconstruct technical context that remains available in GitHub.
