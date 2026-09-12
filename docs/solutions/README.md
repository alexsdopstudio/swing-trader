# Solution Memory

This directory stores reusable lessons that future engineers or AI agents should not have to rediscover.

Solution memory complements, but does not replace, other project memory: `docs/decisions/` records durable decisions, `docs/plans/` planned/completed work, `experiments/` reproducible quantitative research, and `docs/solutions/` reusable problem/solution knowledge.

## Categories

- `engineering/` — recurring software, architecture, data, testing, tooling, and operational lessons.
- `trading-research/` — recurring cross-experiment lessons about backtesting, execution realism, data quality, bias, robustness, and research methodology.

Create a solution note when the learning is likely to recur, rediscovery would waste meaningful time or add risk, and the lesson is broader than one isolated result. Prefer concise, evidence-backed notes with applicability boundaries and concrete checks.

## Curated index

### Engineering

- [`separate-durable-memory-from-inflight-state.md`](engineering/separate-durable-memory-from-inflight-state.md) — keep durable project knowledge versioned while deriving fast-changing branch/PR/check/review state into replaceable cross-agent handoffs.

### Trading research

- [`order-events-by-information-time.md`](trading-research/order-events-by-information-time.md) — preserve realistic open/intraday/close ordering, next-asset-bar execution, and stop semantics.
- [`include-costs-in-risk-accounting.md`](trading-research/include-costs-in-risk-accounting.md) — include commissions, spread, and slippage in sizing, cash constraints, aggregate risk, and R accounting.
- [`separate-warmup-and-evaluation-windows.md`](trading-research/separate-warmup-and-evaluation-windows.md) — calculate rolling features on warm-up history, then slice to an explicit evaluation window.
- [`control-inputs-in-sensitivity-experiments.md`](trading-research/control-inputs-in-sensitivity-experiments.md) — reuse one market-data snapshot and rerun the full portfolio path when tested assumptions affect path-dependent state.
- [`preregister-true-holdout-windows.md`](trading-research/preregister-true-holdout-windows.md) — separate retrospective diagnostics from genuine unseen evidence with preregistered future validation gates.
- [`control-passive-reference-comparisons.md`](trading-research/control-passive-reference-comparisons.md) — preregister passive rules, share snapshot/cost conventions, and report exposure/drawdown beside return.
- [`evaluate-parameter-neighborhoods-without-winner-selection.md`](trading-research/evaluate-parameter-neighborhoods-without-winner-selection.md) — preregister a local grid and stability criteria, evaluate the surface on shared inputs, and never promote the retrospective winner into a frozen strategy.
