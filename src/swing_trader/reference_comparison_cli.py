from __future__ import annotations

import argparse

from .reference_comparison import run_reference_comparison


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the versioned passive/reference baseline comparison."
    )
    parser.add_argument("--config", required=True, help="Path to the comparison YAML config.")
    parser.add_argument("--output-dir", required=True, help="Directory for generated artifacts.")
    args = parser.parse_args()

    results = run_reference_comparison(args.config, args.output_dir)
    strategy = results["strategy"]["metrics"]
    equal_weight = results["reference_baselines"]["equal_weight"]["metrics"]
    print(f"Experiment: {results['experiment']['id']}")
    print(f"Strategy CAGR: {strategy['cagr']}")
    print(f"Equal-weight CAGR: {equal_weight['cagr']}")
    print(f"Results: {args.output_dir}/results.json")


if __name__ == "__main__":
    main()
