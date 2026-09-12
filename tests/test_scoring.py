import numpy as np
import pandas as pd

from swing_trader.indicators import add_indicators
from swing_trader.scoring import score_latest


def _trend_frame(n: int = 260, slope: float = 0.6) -> pd.DataFrame:
    idx = pd.date_range("2024-01-01", periods=n, freq="D")
    close = 100 + np.arange(n) * slope
    return pd.DataFrame(
        {
            "Open": close - 0.2,
            "High": close + 0.6,
            "Low": close - 0.8,
            "Close": close,
            "Volume": np.full(n, 1_000_000.0),
        },
        index=idx,
    )


def test_strong_trend_scores_trend_points():
    df = add_indicators(_trend_frame())
    score = score_latest(df)
    assert score.trend == 30
    assert score.breakout == 15


def test_relative_strength_awards_points():
    asset = add_indicators(_trend_frame(slope=0.8))
    benchmark = add_indicators(_trend_frame(slope=0.2))
    score = score_latest(asset, benchmark)
    assert score.relative_strength > 0
