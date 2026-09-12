# Control Inputs in Sensitivity Experiments

## Problem

A sensitivity experiment is only interpretable if the tested assumption changes while unrelated inputs stay fixed.

For market-data research, running each scenario against a fresh provider download can silently change historical bars between scenarios. The resulting metric differences would then mix execution-cost sensitivity with provider-data revisions.

A second failure mode is treating execution costs as a simple PnL haircut after a backtest. In a cost-aware portfolio, friction can affect position size, cash usage, aggregate risk, stop economics, exit timing, and later trade admission.

## Root cause

Sensitivity tests are controlled experiments, but external data providers and path-dependent portfolio accounting introduce hidden variables unless they are explicitly controlled.

## Reusable solution

For one sensitivity run:

1. download each required market series once;
2. cache and reuse that exact in-memory frame for every scenario;
3. record deterministic input-data digests;
4. change only the intended scenario assumptions;
5. rerun the complete portfolio simulation for every scenario;
6. compare both performance metrics and path diagnostics such as trade count, exposure, exits, and total modeled cost;
7. fail the experiment if source-data digests differ between scenarios.

Do not calculate a sensitivity curve by taking one baseline trade ledger and subtracting larger costs afterward when costs participate in sizing, stops, cash, or portfolio-risk rules.

## Path dependence

Execution-cost sensitivity can change the actual trade sequence.

Higher costs may:

- reduce position sizes;
- change the executed entry price used by technical/risk rules;
- alter effective loss to the stop;
- change available cash and aggregate open risk;
- change exit timing;
- free or consume capacity for later trades.

Therefore trade-count differences across scenarios can be legitimate model outcomes rather than implementation errors.

## Provider revisions between experiments

The shared-snapshot rule controls data **within** one sensitivity experiment. It does not guarantee that a provider returns the same history in a future run.

Record source-series digests and runtime versions so cross-experiment revisions are visible. If exact replay matters, retain an immutable data snapshot or the original generated artifact externally; a digest can detect change but cannot reconstruct old data.

## Tests and checks

Require:

- a test proving repeated scenario requests hit one shared downloader cache;
- source digest equality across all scenarios;
- versioned scenario definitions;
- baseline-relative metric deltas;
- path diagnostics including trade count and total execution cost;
- a real-data artifact inspection before durable conclusions are committed.

## Evidence

EXP-0002 reused five provider downloads across four cost scenarios. Market-data digests were identical within the experiment.

At 4.0x baseline execution costs the portfolio produced 66 trades instead of the baseline 65 because friction changed the portfolio path. This confirms that cost sensitivity cannot be represented accurately as a post-hoc PnL subtraction.

EXP-0002 also detected that META, NVDA, and QQQ provider digests had changed since EXP-0001 while BTC-USD and SOL-USD had not, reinforcing the need for cross-run provenance.

## References

- `src/swing_trader/cost_sensitivity.py`
- `src/swing_trader/execution.py`
- `experiments/EXP-0002-cost-sensitivity/`
- `docs/solutions/trading-research/include-costs-in-risk-accounting.md`
- PR #6 — EXP-0002 cost sensitivity
