from __future__ import annotations

import argparse

from .temporal_stability import run_temporal_stability


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the versioned EXP-0003 historical temporal-stability diagnostic."
    )
    parser.add_argument("--config", required=True, help="Path to the EXP-0003 YAML config.")
    parser.add_argument("--output-dir", required=True, help="Directory for generated artifacts.")
    args = parser.parse_args()

    results = run_temporal_stability(args.config, args.output_dir)
    diagnostics = results["diagnostics"]
    print(f"Experiment: {results['experiment']['id']}")
    print(
        "Positive expectancy folds: "
        f"{diagnostics['positive_expectancy_folds']}/{diagnostics['fold_count']}"
    )
    print(
        "Profit factor > 1 folds: "
        f"{diagnostics['profit_factor_above_one_folds']}/{diagnostics['fold_count']}"
    )
    print(f"Results: {args.output_dir}/results.json")


if __name__ == "__main__":
    main()
