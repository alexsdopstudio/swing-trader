# Solution Memory

This directory stores reusable lessons that future engineers or AI agents should not have to rediscover.

Solution memory complements, but does not replace, other project memory:

- `docs/decisions/` records durable decisions the project intends to follow.
- `docs/plans/` records planned and completed work.
- `experiments/` records reproducible quantitative research results, including failed hypotheses.
- `docs/solutions/` records reusable problem/solution knowledge learned while doing the work.

## Categories

- `engineering/` — recurring software, architecture, data, testing, tooling, and operational lessons.
- `trading-research/` — recurring cross-experiment lessons about backtesting, execution realism, data quality, bias, robustness, and research methodology.

## When to create a solution note

Create a solution note when all of the following are true:

1. The learning is likely to recur in future work.
2. A future contributor could waste meaningful time or introduce risk by rediscovering it.
3. The lesson is more specific than a general project rule but broader than one isolated experiment result.

Do not create a solution note merely to satisfy process. It is valid for a PR to record `No reusable learning` in its Compound section.

## Writing solution notes

Start from `.ai/solution-template.md`.

Prefer concise, evidence-backed notes. Include root cause, applicability boundaries, and concrete tests/checks. Link relevant ADRs, modules, experiments, plans, or PRs.

## Curated index

This README is the lightweight solution-memory index consumed by the AI context builder. Add a short entry here when a new reusable solution note is created.

### Engineering

_No reusable engineering solution notes recorded yet._

### Trading research

_No reusable trading-research solution notes recorded yet._
