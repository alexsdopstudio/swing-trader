from __future__ import annotations

import argparse

from .cost_sensitivity import run_cost_sensitivity


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a versioned execution-cost sensitivity experiment.")
    parser.add_argument("--config", required=True, help="Path to the sensitivity YAML config.")
    parser.add_argument("--output-dir", required=True, help="Directory for generated artifacts.")
    args = parser.parse_args()

    results = run_cost_sensitivity(args.config, args.output_dir)
    robustness = results["robustness"]
    print(f"Experiment: {results['experiment']['id']}")
    print(f"Primary scenario: {robustness['primary_scenario']}")
    print(f"Primary expectancy positive: {robustness['primary_expectancy_positive']}")
    print(f"Stress expectancy positive: {robustness['stress_expectancy_positive']}")
    print(f"Results: {args.output_dir}/results.json")


if __name__ == "__main__":
    main()
