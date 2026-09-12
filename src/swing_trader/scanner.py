from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import yaml

from .data import download_daily
from .indicators import add_indicators
from .scoring import ScoreBreakdown, is_entry_candidate, score_latest


Downloader = Callable[[str, str, str | None], pd.DataFrame]


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


def required_symbols(config: dict) -> list[str]:
    """Return configured assets and benchmarks once each, preserving config order."""
    candidates = [asset["symbol"] for asset in config["assets"]]
    candidates.extend([config["benchmark_equities"], config["benchmark_crypto"]])
    symbols: list[str] = []
    for raw in candidates:
        if not isinstance(raw, str) or not raw.strip():
            raise ValueError("configured symbols and benchmarks must be non-empty strings")
        symbol = raw.strip()
        if symbol not in symbols:
            symbols.append(symbol)
    return symbols


def scan_frames(config: dict, frames: Mapping[str, pd.DataFrame]) -> list[ScanResult]:
    """Score a configured universe from an already captured market-data snapshot."""
    symbols = required_symbols(config)
    missing = [symbol for symbol in symbols if symbol not in frames]
    if missing:
        raise ValueError(f"missing scan frames for symbols: {missing}")

    enriched = {symbol: add_indicators(frames[symbol]) for symbol in symbols}
    benchmark_symbols = {
        "equity": config["benchmark_equities"],
        "crypto": config["benchmark_crypto"],
    }
    benchmark_data = {
        asset_class: enriched[symbol] for asset_class, symbol in benchmark_symbols.items()
    }

    results: list[ScanResult] = []
    for asset in config["assets"]:
        symbol = asset["symbol"]
        asset_class = asset["asset_class"]
        df = enriched[symbol]
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


def scan(
    config_path: str | Path = "config/universe.yaml",
    *,
    downloader: Downloader = download_daily,
) -> list[ScanResult]:
    config = load_universe(config_path)
    frames = {symbol: downloader(symbol, "2015-01-01", None) for symbol in required_symbols(config)}
    return scan_frames(config, frames)
