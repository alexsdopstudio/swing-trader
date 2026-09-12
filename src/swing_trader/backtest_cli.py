from __future__ import annotations

import argparse

from .data import download_daily
from .historical import historical_regime, historical_scores
from .indicators import add_indicators
from .metrics import calculate_metrics
from .portfolio import PortfolioAsset, PortfolioBacktestConfig, backtest_portfolio
from .scanner import load_universe


def _format_pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def main() -> None:
    parser = argparse.ArgumentParser(description="Shared-account swing portfolio backtester")
    parser.add_argument("--config", default="config/universe.yaml")
    parser.add_argument("--symbols", default="BTC-USD,SOL-USD,META,NVDA")
    parser.add_argument("--start", default="2018-01-01")
    parser.add_argument("--end", default=None)
    parser.add_argument("--initial-equity", type=float, default=5_000.0)
    args = parser.parse_args()

    universe = load_universe(args.config)
    asset_classes = {item["symbol"]: item["asset_class"] for item in universe["assets"]}
    benchmark_symbols = {
        "equity": universe["benchmark_equities"],
        "crypto": universe["benchmark_crypto"],
    }

    symbols = [symbol.strip() for symbol in args.symbols.split(",") if symbol.strip()]
    unknown = [symbol for symbol in symbols if symbol not in asset_classes]
    if unknown:
        raise SystemExit(f"Symbols not found in universe config: {', '.join(unknown)}")

    benchmark_data = {}
    for asset_class in {asset_classes[symbol] for symbol in symbols}:
        benchmark_symbol = benchmark_symbols[asset_class]
        benchmark_data[asset_class] = add_indicators(
            download_daily(benchmark_symbol, start=args.start, end=args.end)
        )

    assets: list[PortfolioAsset] = []
    for symbol in symbols:
        asset_class = asset_classes[symbol]
        data = add_indicators(download_daily(symbol, start=args.start, end=args.end))
        benchmark = benchmark_data[asset_class]
        score_benchmark = None if symbol == benchmark_symbols[asset_class] else benchmark
        assets.append(
            PortfolioAsset(
                symbol=symbol,
                data=data,
                scores=historical_scores(data, score_benchmark),
                regime=historical_regime(benchmark, data.index),
            )
        )

    result = backtest_portfolio(
        assets,
        PortfolioBacktestConfig(initial_equity=args.initial_equity),
    )
    metrics = calculate_metrics(result)

    print("PORTFOLIO BACKTEST — PRE-COST")
    print(f"Start equity:       {metrics.start_equity:,.2f}")
    print(f"End equity:         {metrics.end_equity:,.2f}")
    print(f"Total return:       {_format_pct(metrics.total_return)}")
    print(f"CAGR:               {_format_pct(metrics.cagr)}")
    print(f"Max drawdown:       {_format_pct(metrics.max_drawdown)}")
    print(f"Sharpe:             {metrics.sharpe:.2f}")
    print(f"Sortino:            {metrics.sortino:.2f}")
    print(f"Profit factor:      {metrics.profit_factor:.2f}")
    print(f"Win rate:           {_format_pct(metrics.win_rate)}")
    print(f"Expectancy:         {metrics.expectancy_r:.2f}R")
    print(f"Trades:             {metrics.trade_count}")
    print(f"Average exposure:   {_format_pct(metrics.average_exposure)}")
    print()
    print(f"{'SYMBOL':<10} {'ENTRY':<10} {'EXIT':<10} {'PNL':>12} {'R':>8} {'REASON':>12}")
    print("-" * 68)
    for trade in result.trades:
        print(
            f"{trade.symbol:<10} {trade.entry_date.date().isoformat():<10} "
            f"{trade.exit_date.date().isoformat():<10} {trade.pnl:>12.2f} "
            f"{trade.r_multiple:>8.2f} {trade.exit_reason:>12}"
        )


if __name__ == "__main__":
    main()
