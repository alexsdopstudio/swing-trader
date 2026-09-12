# Repository instructions

Use `AGENTS.md` as the canonical agent guide and repository map.

At the start of a new coding session, reconstruct work state autonomously before substantive edits. When shell access is available, run `python scripts/agent_bootstrap.py` and read `.ai/context.md` plus `.ai/handoff.md`. When shell access is unavailable, inspect open pull requests, their `Agent handoff` sections, the referenced active plan, `.ai/current-state.md`, and relevant CI/review state directly.

Do not ask the user to run bootstrap commands, copy prior chat context, identify the active branch/PR, or restate repository state when it can be derived from the repository or GitHub.

Preserve the core constraints: no look-ahead bias, next-open execution for close-derived signals, deterministic risk controls, tests for strategy changes, reproducible experiments, English-only repository content, dedicated branch/PR workflow, Simplify, Compound, formal review, and agent-owned merge after `PASS` plus green CI.
