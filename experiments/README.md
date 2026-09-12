# Experiment Memory

Every meaningful strategy/backtest experiment should be reproducible from repository state plus the files stored here.

Each durable experiment record should preserve strategy/version, universe, dates, parameters, costs, code SHA, source/runtime provenance, key metrics, reviewed conclusion, and follow-up. Generated trade ledgers/equity curves may remain CI artifacts when reproducible from recorded code/config, but reviewed summary results must stay in the repository.

Do not delete failed experiments merely because they performed poorly. Negative results are project memory and help prevent repeated overfitting.

## Experiment index

| Experiment | Status | Question | Decision |
|---|---|---|---|
| [`EXP-0001-baseline`](EXP-0001-baseline/) | Reviewed exploratory baseline | Does v1 show a positive cost-aware baseline on BTC, SOL, META, and NVDA? | Continue research; do not deploy |
| [`EXP-0002-cost-sensitivity`](EXP-0002-cost-sensitivity/) | Reviewed sensitivity experiment | Does the EXP-0001 result survive materially higher execution-cost assumptions? | Cost robustness supported in-sample; continue research; do not deploy |
| [`EXP-0003-temporal-stability`](EXP-0003-temporal-stability/) | Reviewed retrospective temporal diagnostic | Is the historical v1 result stable across calendar regimes? | Predeclared stability thresholds not met; continue research; do not deploy |
| [`EXP-0004-reference-baselines`](EXP-0004-reference-baselines/) | Reviewed retrospective reference comparison | How does frozen v1 compare with passive ownership of the same selected assets? | Passive return is much higher but with near-full exposure/extreme drawdown; keep v1 frozen |
| [`EXP-0005-parameter-neighborhood`](EXP-0005-parameter-neighborhood/) | Reviewed retrospective parameter-neighborhood diagnostic | Does the frozen v1 result survive reasonable local score/stop/trail perturbations? | All preregistered local-robustness criteria passed; keep v1 frozen; do not select a historical winner |

## Prospective protocols

| Protocol | Status | Start | Validation gate |
|---|---|---|---|
| [`PROSPECTIVE-v1-holdout`](PROSPECTIVE-v1-holdout/protocol.yaml) | Preregistered | 2026-09-14 | At least 24 months and at least 30 closed trades; no interim v1 tuning |
