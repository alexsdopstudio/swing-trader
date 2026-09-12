# Claude Coding Agent Instructions

`AGENTS.md` is the canonical repository guide. Read and follow it before substantive work.

At the start of a new session, reconstruct project and active-work state autonomously. When shell access is available, run:

```bash
python scripts/agent_bootstrap.py
```

Then read `.ai/context.md`, `.ai/handoff.md`, the selected active PR body, and the referenced active plan before editing.

If shell access is unavailable, perform the equivalent reconstruction through repository/GitHub tools: inspect `AGENTS.md`, `.ai/current-state.md`, open pull requests, the selected PR `Agent handoff` section, its active plan, and current CI/review state.

Do not ask the user to copy prior chat history, run bootstrap commands, identify the active branch/PR, or restate repository state when it can be derived from repository/GitHub state.
