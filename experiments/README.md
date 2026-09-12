# Experiment Memory

Every meaningful strategy/backtest experiment should be reproducible from repository state plus the files stored here.

Recommended layout:

```text
experiments/EXP-0001-baseline/
  config.yaml
  results.json
  notes.md
```

Each experiment should record at least:

- strategy/version
- universe
- start/end dates
- parameters
- costs/slippage assumptions
- code commit SHA
- key metrics
- conclusion and follow-up

Generated trade ledgers, equity curves, and resolved configuration files may be stored as CI artifacts when they are reproducible from the recorded code/config. The durable repository record must still preserve enough provenance and reviewed results to understand what was run and why the conclusion was reached.

Do not delete failed experiments merely because they performed poorly. Negative results are project memory and help prevent repeated overfitting.

## Experiment index

| Experiment | Status | Question | Decision |
|---|---|---|---|
| [`EXP-0001-baseline`](EXP-0001-baseline/) | Reviewed exploratory baseline | Does v1 show a positive cost-aware baseline on BTC, SOL, META, and NVDA? | Continue research; do not deploy |
| [`EXP-0002-cost-sensitivity`](EXP-0002-cost-sensitivity/) | Reviewed sensitivity experiment | Does the EXP-0001 result survive materially higher execution-cost assumptions? | Cost robustness supported in-sample; continue research; do not deploy |
| [`EXP-0003-temporal-stability`](EXP-0003-temporal-stability/) | Reviewed retrospective temporal diagnostic | Is the historical v1 result stable across calendar regimes? | Predeclared stability thresholds not met; continue research; do not deploy |

## Prospective protocols

| Protocol | Status | Start | Validation gate |
|---|---|---|---|
| [`PROSPECTIVE-v1-holdout`](PROSPECTIVE-v1-holdout/protocol.yaml) | Preregistered | 2026-09-14 | At least 24 months and at least 30 closed trades; no interim v1 tuning |
