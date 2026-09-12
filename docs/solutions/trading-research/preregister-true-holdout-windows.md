# Preregister True Holdout Windows

## Problem

A historical period cannot become genuinely out-of-sample after its aggregate result has already been inspected.

A common research mistake is to run a strategy over a long historical interval, inspect the result, and later split the same interval into calendar or rolling folds while describing those folds as "held out". The folds can reveal temporal concentration, but the data is no longer unseen.

## Root cause

The terms `walk-forward`, `holdout`, and `out-of-sample` are sometimes used for any chronological split even when the researcher has already observed the full-period result.

This creates false confidence because retrospective decomposition is treated as independent validation.

## Reusable solution

Separate two research questions explicitly:

1. **Retrospective temporal diagnostics** — split previously observed history into fixed folds to study regime dependence, concentration, and inactive periods.
2. **Prospective holdout validation** — register the strategy, parameters, universe, execution assumptions, start date, and evaluation gate before the holdout interval begins.

A prospective protocol should record at least:

- registration date;
- future evaluation start;
- frozen strategy/version or source commit;
- universe and benchmarks;
- entry, exit, sizing, risk, and execution assumptions;
- minimum calendar horizon;
- minimum trade count;
- whether both gates or either gate is required;
- rules for interim monitoring;
- conditions that invalidate comparability and require a new protocol.

## Portfolio-fold semantics

When historical folds are used for diagnostics, decide before running whether portfolio state should:

- reset at each fold boundary; or
- carry continuously across folds.

Resetting state is appropriate when the goal is to compare regime behavior from the same starting capital. Chaining state is appropriate when reconstructing one continuous portfolio path.

Do not combine independently reset fold returns into a synthetic portfolio CAGR.

## Interim monitoring

A prospective holdout can be monitored operationally before its validation gate matures, but interim outcomes should not be used to tune the frozen strategy if the project wants to preserve the holdout's evidentiary value.

If strategy or risk parameters change, start a new protocol/version. The old protocol remains historical evidence for the old version.

## Tests and checks

Require research tooling and review to verify:

- retrospective folds are labeled as retrospective;
- no generated artifact claims unseen/OOS status for already observed data;
- prospective start date is later than registration date;
- strategy/risk parameters are explicitly frozen;
- validation gates are versioned before the holdout begins;
- interim tuning is prohibited or explicitly documented;
- changing the frozen specification creates a new protocol.

## Evidence

EXP-0001 and EXP-0002 had already exposed the complete 2021-01-01 through 2026-08-31 historical result. EXP-0003 therefore used yearly folds only as a temporal-stability diagnostic and explicitly set `true_out_of_sample_claim: false`.

The project preregistered `PROSPECTIVE-v1-holdout` on 2026-09-12 with a future start of 2026-09-14, a minimum observation end of 2028-09-14, and a minimum of 30 closed trades before validation claims.

## References

- `experiments/EXP-0003-temporal-stability/`
- `experiments/PROSPECTIVE-v1-holdout/protocol.yaml`
- `src/swing_trader/temporal_stability.py`
- PR #7 — EXP-0003 temporal stability
