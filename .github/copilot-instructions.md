# Repository instructions

Use `AGENTS.md` as the primary agent guide and repository map. Read the relevant architecture, strategy, risk, ADR and active-plan documents before making substantive changes.

Before creating a new branch or PR, inspect open pull requests and their latest comment containing `<!-- agent-handoff -->`. Continue matching in-flight work instead of opening a duplicate task. Reconstruct context from repository/GitHub state before asking the user to repeat prior chat context or run bootstrap commands.

Preserve the core constraints: no look-ahead bias, next-open execution for close-derived signals, deterministic risk controls, tests for strategy changes, reproducible experiments, and the formal branch/design/PR/Simplify/Validation/Compound/Review/Merge lifecycle.
