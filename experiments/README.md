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

Do not delete failed experiments merely because they performed poorly. Negative results are project memory and help prevent repeated overfitting.
