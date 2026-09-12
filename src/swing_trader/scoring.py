from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class ScoreBreakdown:
    trend: int
    momentum: int
    relative_strength: int
    breakout: int
    volume: int

    @property
    def total(self) -> int:
        return self.trend + self.momentum + self.relative_strength + self.breakout + self.volume


def _value(row: pd.Series, key: str) -> float:
    value = row.get(key)
    if pd.isna(value):
        return float("nan")
    return float(value)


def score_latest(df: pd.DataFrame, benchmark_df: pd.DataFrame | None = None) -> ScoreBreakdown:
    if len(df) < 201:
        raise ValueError("At least 201 bars are required for the v1 score")

    row = df.iloc[-1]
    sma50_20d_ago = df["sma50"].iloc[-21]

    trend = 0
    if _value(row, "Close") > _value(row, "sma50"):
        trend += 10
    if _value(row, "sma50") > _value(row, "sma200"):
        trend += 10
    if _value(row, "sma50") > float(sma50_20d_ago):
        trend += 10

    momentum = 0
    roc20 = _value(row, "roc20")
    roc60 = _value(row, "roc60")
    if roc20 > 0.05:
        momentum += 10
    if roc20 > 0.10:
        momentum += 5
    if roc60 > 0.10:
        momentum += 5
    if roc60 > 0.20:
        momentum += 5

    relative_strength = 0
    if benchmark_df is not None:
        benchmark_roc60 = float(benchmark_df["roc60"].iloc[-1])
        rs = roc60 - benchmark_roc60
        for threshold in (0.00, 0.05, 0.10, 0.20):
            if rs > threshold:
                relative_strength += 5

    breakout = 0
    close = _value(row, "Close")
    if close > _value(row, "high20"):
        breakout += 10
    if close > _value(row, "high50"):
        breakout += 5

    volume = 0
    volume_ratio = _value(row, "volume_ratio")
    if volume_ratio > 1.2:
        volume += 5
    if volume_ratio > 1.5:
        volume += 5

    return ScoreBreakdown(trend, momentum, relative_strength, breakout, volume)


def is_entry_candidate(
    df: pd.DataFrame,
    score: ScoreBreakdown,
    regime_df: pd.DataFrame,
    min_score: int = 70,
) -> bool:
    row = df.iloc[-1]
    regime = regime_df.iloc[-1]
    return bool(
        score.total >= min_score
        and row["Close"] > row["high20"]
        and row["Close"] > row["sma50"]
        and row["sma50"] > row["sma200"]
        and regime["Close"] > regime["sma200"]
    )
