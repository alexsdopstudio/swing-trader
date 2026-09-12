# Evaluate parameter neighborhoods without selecting the historical winner

## Problem

A backtest can look strong at one parameter point and still be fragile to small perturbations. A naive robustness sweep creates a second problem: after seeing the grid, it is tempting to promote the best historical cell and silently turn a diagnostic into optimization.

## Reusable approach

For a local parameter-robustness diagnostic:

1. freeze the production/research center before the run;
2. preregister a small, interpretable neighborhood and pass/fail criteria;
3. vary only the intended parameters and keep universe, costs, risk policy, dates, and strategy logic fixed;
4. reuse one provider snapshot across every scenario;
5. rerun the full portfolio path when the varied parameter affects sizing, exits, cash, risk, or subsequent opportunities;
6. summarize the distribution and immediate neighbors rather than ranking a winner;
7. record whether the center reproduces the durable baseline within explicit provider-revision tolerances;
8. never promote a retrospective winner into a frozen prospective specification.

## Why this matters

The useful question is not “which parameter set won?” but “does the strategy's sign and economic quality survive reasonable local perturbations?” A neighborhood can support robustness even when metric magnitude varies materially. Conversely, one exceptional cell surrounded by weak neighbors is evidence of fragility rather than evidence for optimization.

## Evidence from EXP-0005

EXP-0005 preregistered a 27-cell neighborhood around frozen v1 and shared one five-symbol snapshot across all scenarios. All 27 cells and all six immediate axial neighbors remained joint-positive, with median expectancy +0.92R. Metric magnitude still varied substantially, so the result was recorded as local robustness rather than parameter irrelevance or permission to retune.

## Applicability boundaries

This pattern is retrospective sensitivity analysis. It does not create unseen evidence, erase regime dependence, fix survivorship bias, or validate deployment. Prospective protocols must remain frozen independently of the neighborhood result.

## Checks for future experiments

- exact grid and criteria versioned before the first real-data run;
- one center scenario and expected neighbor count;
- source digests identical across scenarios;
- only approved parameter fields differ from the base config;
- full-path rerun when path-dependent controls change;
- no `selected_parameter_set` or equivalent winner-promotion output;
- durable interpretation explicitly separates robustness from optimization and validation.

Related: `experiments/EXP-0005-parameter-neighborhood/`, `docs/solutions/trading-research/control-inputs-in-sensitivity-experiments.md`, and `experiments/PROSPECTIVE-v1-holdout/protocol.yaml`.
