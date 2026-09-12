from __future__ import annotations

import argparse

from .reference_baseline import run_reference_baseline


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a cost-aware passive reference baseline.")
    parser.add_argument("--config", required=True, help="Path to the reference YAML config.")
    parser.add_argument("--output-dir", required=True, help="Directory for generated artifacts.")
    args = parser.parse_args()
    results = run_reference_baseline(args.config, args.output_dir)
    print(f"Experiment: {results['experiment']['id']}")
    print(f"End equity: {results['metrics']['end_equity']}")
    print(f"Results: {args.output_dir}/results.json")
