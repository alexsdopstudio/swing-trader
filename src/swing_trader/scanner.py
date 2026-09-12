from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import yaml

from .data import download_daily
from .indicators import add_indicators
from .scoring import ScoreBreakdown, is_entry_candidate, score_latest


@dataclass(frozen=True)
class ScanResult:
    symbol: str
    asset_class: str
    score: int
    signal: str
    close: float
    atr14: float
    breakdown: ScoreBreakdown


def load_universe(path: str | Path) -> dict:
    with Path(path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def scan(config_path: str | Path = "config/universe.yaml") -> list[ScanResult]:
    config = load_universe(config_path)
    benchmark_symbols = {
        "equity": config["benchmark_equities"],
        "crypto": config["benchmark_crypto"],
    }
    benchmark_data: dict[str, pd.DataFrame] = {}
    for asset_class, symbol in benchmark_symbols.items():
        benchmark_data[asset_class] = add_indicators(download_daily(symbol))

    results: list[ScanResult] = []
    for asset in config["assets"]:
        symbol = asset["symbol"]
        asset_class = asset["asset_class"]
        df = add_indicators(download_daily(symbol))
        benchmark = benchmark_data[asset_class]
        score_benchmark = None if symbol == benchmark_symbols[asset_class] else benchmark
        breakdown = score_latest(df, score_benchmark)
        signal = "BUY" if is_entry_candidate(df, breakdown, benchmark) else "WATCH"
        row = df.iloc[-1]
        results.append(
            ScanResult(
                symbol=symbol,
                asset_class=asset_class,
                score=breakdown.total,
                signal=signal,
                close=float(row["Close"]),
                atr14=float(row["atr14"]),
                breakdown=breakdown,
            )
        )

    return sorted(results, key=lambda item: item.score, reverse=True)
