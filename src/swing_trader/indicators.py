from __future__ import annotations

import numpy as np
import pandas as pd


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy enriched with the indicators used by the v1 strategy."""
    required = {"Open", "High", "Low", "Close", "Volume"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    out = df.copy().sort_index()
    close = out["Close"].astype(float)
    high = out["High"].astype(float)
    low = out["Low"].astype(float)
    volume = out["Volume"].astype(float)

    out["sma50"] = close.rolling(50).mean()
    out["sma200"] = close.rolling(200).mean()
    out["roc20"] = close.pct_change(20)
    out["roc60"] = close.pct_change(60)
    out["high20"] = high.shift(1).rolling(20).max()
    out["high50"] = high.shift(1).rolling(50).max()

    avg_volume20 = volume.shift(1).rolling(20).mean()
    out["volume_ratio"] = volume / avg_volume20.replace(0, np.nan)

    prev_close = close.shift(1)
    tr = pd.concat(
        [high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1
    ).max(axis=1)
    out["atr14"] = tr.rolling(14).mean()
    return out
