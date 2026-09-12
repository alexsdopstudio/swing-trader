from __future__ import annotations

import argparse

from .experiment import run_experiment


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a versioned swing-trading experiment")
    parser.add_argument("--config", required=True, help="Path to experiment YAML config")
    parser.add_argument("--output-dir", required=True, help="Directory for generated artifacts")
    args = parser.parse_args()

    results = run_experiment(args.config, args.output_dir)
    experiment = results["experiment"]
    metrics = results["metrics"]
    diagnostics = results["diagnostics"]

    print(f"EXPERIMENT {experiment['id']} — {experiment['name']}")
    print(f"Commit:             {experiment['code_commit_sha']}")
    print(f"Trades:             {diagnostics['trade_count']}")
    print(f"End equity:         {metrics['end_equity']}")
    print(f"Total return:       {metrics['total_return']}")
    print(f"CAGR:               {metrics['cagr']}")
    print(f"Max drawdown:       {metrics['max_drawdown']}")
    print(f"Profit factor:      {metrics['profit_factor']}")
    print(f"Expectancy R:       {metrics['expectancy_r']}")
    print(f"Execution cost:     {diagnostics['total_execution_cost']}")


if __name__ == "__main__":
    main()
