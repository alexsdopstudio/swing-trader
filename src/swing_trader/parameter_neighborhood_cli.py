from __future__ import annotations

import argparse

from .parameter_neighborhood import run_parameter_neighborhood


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the preregistered EXP-0005 parameter-neighborhood diagnostic."
    )
    parser.add_argument("--config", required=True, help="Path to the EXP-0005 YAML config.")
    parser.add_argument("--output-dir", required=True, help="Directory for generated artifacts.")
    args = parser.parse_args()

    results = run_parameter_neighborhood(args.config, args.output_dir)
    robustness = results["robustness"]
    print(f"Experiment: {results['experiment']['id']}")
    print(f"Joint-positive scenarios: {robustness['joint_positive_count']} / 27")
    print(f"Joint-positive axial neighbors: {robustness['axial_joint_positive_count']} / 6")
    print(f"Median expectancy R: {robustness['median_expectancy_r']}")
    print(
        "All preregistered criteria passed: "
        f"{robustness['all_preregistered_criteria_passed']}"
    )
    print(f"Results: {args.output_dir}/results.json")


if __name__ == "__main__":
    main()
