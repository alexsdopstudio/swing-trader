from __future__ import annotations

import pandas as pd


def historical_scores(
    df: pd.DataFrame,
    benchmark_df: pd.DataFrame | None = None,
) -> pd.Series:
    """Return the v1 Swing Score for every bar without using future data."""
    required = {
        "Close",
        "sma50",
        "sma200",
        "roc20",
        "roc60",
        "high20",
        "high50",
        "volume_ratio",
    }
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing score columns: {sorted(missing)}")

    score = pd.Series(0, index=df.index, dtype="int64")

    score += (df["Close"] > df["sma50"]).astype(int) * 10
    score += (df["sma50"] > df["sma200"]).astype(int) * 10
    score += (df["sma50"] > df["sma50"].shift(20)).astype(int) * 10

    score += (df["roc20"] > 0.05).astype(int) * 10
    score += (df["roc20"] > 0.10).astype(int) * 5
    score += (df["roc60"] > 0.10).astype(int) * 5
    score += (df["roc60"] > 0.20).astype(int) * 5

    if benchmark_df is not None:
        if "roc60" not in benchmark_df.columns:
            raise ValueError("benchmark_df must contain roc60")
        benchmark_roc60 = benchmark_df["roc60"].reindex(df.index).ffill()
        relative_strength = df["roc60"] - benchmark_roc60
        for threshold in (0.00, 0.05, 0.10, 0.20):
            score += (relative_strength > threshold).astype(int) * 5

    score += (df["Close"] > df["high20"]).astype(int) * 10
    score += (df["Close"] > df["high50"]).astype(int) * 5
    score += (df["volume_ratio"] > 1.2).astype(int) * 5
    score += (df["volume_ratio"] > 1.5).astype(int) * 5

    return score


def historical_regime(
    benchmark_df: pd.DataFrame,
    index: pd.Index | None = None,
) -> pd.Series:
    """Return bullish-regime state aligned without looking forward."""
    required = {"Close", "sma200"}
    missing = required.difference(benchmark_df.columns)
    if missing:
        raise ValueError(f"Missing regime columns: {sorted(missing)}")

    regime = (benchmark_df["Close"] > benchmark_df["sma200"]).astype(bool)
    if index is not None:
        regime = regime.reindex(index).ffill().fillna(False).astype(bool)
    return regime
