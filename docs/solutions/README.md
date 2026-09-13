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

- [`separate-durable-memory-from-inflight-state.md`](engineering/separate-durable-memory-from-inflight-state.md) — keep durable project knowledge versioned while deriving fast-changing branch/PR/check/review state into replaceable cross-agent handoffs.
- [`keep-derived-repository-indexes-regenerable.md`](engineering/keep-derived-repository-indexes-regenerable.md) — keep generated repository indexes deterministic and mechanically derived from canonical records, and make CI stale checks include untracked first-generation output.
- [`separate-operational-observations-from-validation-evidence.md`](engineering/separate-operational-observations-from-validation-evidence.md) — use separate namespaces, consumers, and explicit eligibility flags for operational audit history versus preregistered validation evidence even when both use the same provenance techniques.
- [`separate-agent-knowledge-by-evidence-class.md`](engineering/separate-agent-knowledge-by-evidence-class.md) — separate durable references, time-bounded news observations, curated interpretation, project experiments, and generated indexes so agent retrieval cannot collapse provenance or validation boundaries.
- [`separate-canonical-state-from-live-dashboard-enrichment.md`](engineering/separate-canonical-state-from-live-dashboard-enrichment.md) — generate an authoritative static snapshot from repository records, then treat live operational API data as a failure-tolerant presentation layer that cannot revise research status.
- [`separate-paper-planning-from-recorded-fills.md`](engineering/separate-paper-planning-from-recorded-fills.md) — keep close-based planning, human approval, later paper fills, and first-observed trailing-stop marks separate so next-open timing and deterministic risk controls remain enforceable.

### Trading research

- [`order-events-by-information-time.md`](trading-research/order-events-by-information-time.md) — preserve realistic open/intraday/close ordering, next-asset-bar execution, and stop semantics in bar-based multi-asset backtests.
- [`include-costs-in-risk-accounting.md`](trading-research/include-costs-in-risk-accounting.md) — include commissions, spread, and slippage in sizing, cash constraints, aggregate risk, and R-multiple accounting rather than treating them only as final PnL adjustments.
- [`separate-warmup-and-evaluation-windows.md`](trading-research/separate-warmup-and-evaluation-windows.md) — calculate rolling features on pre-test warm-up history, then slice to an explicit evaluation window and record actual provider coverage.
- [`control-inputs-in-sensitivity-experiments.md`](trading-research/control-inputs-in-sensitivity-experiments.md) — reuse one market-data snapshot across sensitivity scenarios and rerun the full portfolio path when the tested assumption affects sizing, stops, cash, or risk.
- [`preregister-true-holdout-windows.md`](trading-research/preregister-true-holdout-windows.md) — distinguish retrospective temporal diagnostics from genuine unseen evidence by preregistering future holdout windows and validation gates before they begin.
- [`control-passive-reference-comparisons.md`](trading-research/control-passive-reference-comparisons.md) — preregister passive rules, reuse the active strategy's snapshot and cost conventions, and report exposure/drawdown beside return so opportunity-cost comparisons remain interpretable.
- [`evaluate-parameter-neighborhoods-without-winner-selection.md`](trading-research/evaluate-parameter-neighborhoods-without-winner-selection.md) — preregister a local grid and stability criteria, evaluate the full-path surface on shared inputs, and never promote the retrospective winner into a frozen strategy.
- [`preserve-forward-provider-state-without-backfill.md`](trading-research/preserve-forward-provider-state-without-backfill.md) — preserve complete provider snapshots at observation time, fingerprint them end-to-end, and leave missed prospective dates as explicit gaps rather than recreating them from revised history.
- [`replay-prospective-evidence-by-information-time.md`](trading-research/replay-prospective-evidence-by-information-time.md) — replay only the newly observable date from each canonical archive, preserve state across observations, and stop at missing evidence instead of rewriting the past from later revised snapshots.
- [`test-universe-breadth-with-fixed-membership-and-contribution.md`](trading-research/test-universe-breadth-with-fixed-membership-and-contribution.md) — fix membership independently of results, rerun the shared-account portfolio on common inputs, and inspect symbol/asset-class contribution concentration rather than headline return alone.
