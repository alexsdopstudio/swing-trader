from __future__ import annotations

import argparse

from .scanner import scan


def main() -> None:
    parser = argparse.ArgumentParser(description="Daily swing opportunity scanner")
    parser.add_argument("--config", default="config/universe.yaml")
    args = parser.parse_args()

    results = scan(args.config)
    print(f"{'SYMBOL':<12} {'CLASS':<8} {'SCORE':>5} {'SIGNAL':>7} {'CLOSE':>12}")
    print("-" * 50)
    for result in results:
        print(
            f"{result.symbol:<12} {result.asset_class:<8} "
            f"{result.score:>5} {result.signal:>7} {result.close:>12.2f}"
        )


if __name__ == "__main__":
    main()
