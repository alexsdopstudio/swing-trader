# Control passive references like experiment inputs

## Problem

An active strategy can look attractive in isolation while still lagging simple ownership of the same assets. Adding a passive reference after seeing results can also create a second source of bias if the reference uses different dates, provider revisions, execution assumptions, or post-hoc weighting rules.

## Reusable solution

Treat passive/reference definitions as controlled experiment inputs rather than presentation-only benchmarks.

For an active-vs-passive comparison:

1. Fix the passive rule before reading the comparison result.
2. Reuse the same provider snapshot and evaluation window as the active strategy.
3. Apply explicit, comparable entry and terminal execution costs.
4. Do not fabricate fills across mixed trading calendars; keep an allocation in cash until its first real tradable bar.
5. Keep weighting/rebalancing rules simple and preregistered. If the question only needs an opportunity-cost reference, avoid adding optimization parameters.
6. Report exposure and drawdown beside return. A mostly-cash active strategy and a continuously invested passive portfolio are not equivalent risk allocations.
7. Preserve source hashes and artifact provenance so provider revisions cannot silently change one side of the comparison.

## Why this matters

A shared snapshot prevents provider drift from being mistaken for strategy value. Shared cost conventions prevent a frictionless reference from receiving an artificial advantage. Exposure and drawdown prevent a high-return, nearly fully invested reference from being interpreted as directly comparable to a low-exposure risk-controlled strategy.

The comparison can still answer useful questions without pretending to normalize every dimension. If volatility targeting, leverage normalization, or periodic rebalancing would materially change the question, those should be separate preregistered experiments rather than post-hoc adjustments.

## Checks

- active and passive calculations read identical source-data hashes;
- passive construction adds no provider downloads after the shared snapshot is populated;
- entry/exit timestamps use real tradable bars only;
- cost models are the same asset-class models used by the active backtest;
- weighting and rebalancing rules are versioned before the real-data run;
- results report return, drawdown, risk-adjusted metrics, and exposure;
- conclusions distinguish retrospective opportunity-cost evidence from out-of-sample validation.

## Applicability

Use this pattern for passive benchmarks, cash/reference portfolios, and simple alternative-policy comparisons where input drift or unequal assumptions could dominate the apparent result.

Do not use it to justify post-hoc leverage, benchmark selection, or portfolio optimization. Those choices create new research hypotheses and need their own controls.

## Evidence

EXP-0004 compared frozen v1 with per-symbol buy-and-hold and an initial equal-weight buy-and-hold basket. All paths reused one provider snapshot and the same execution-cost models. The passive portfolio delivered dramatically higher absolute return but approximately 99.9% average exposure and a roughly 95% maximum drawdown, while v1 averaged about 6% exposure and a roughly 4.25% maximum drawdown. Reporting both dimensions prevented a misleading return-only conclusion.
