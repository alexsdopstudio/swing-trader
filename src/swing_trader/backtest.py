from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .risk import initial_stop, trailing_stop


@dataclass
class Trade:
    entry_date: pd.Timestamp
    exit_date: pd.Timestamp
    entry: float
    exit: float
    initial_stop: float
    r_multiple: float


def backtest_breakout(
    df: pd.DataFrame,
    min_score_series: pd.Series,
    regime_series: pd.Series,
    min_score: int = 70,
    stop_atr: float = 2.0,
    trail_atr: float = 2.5,
) -> list[Trade]:
    """Minimal single-asset v1 backtester using next-session-open entries."""
    trades: list[Trade] = []
    i = 1
    while i < len(df) - 1:
        row = df.iloc[i]
        entry_signal = bool(
            min_score_series.iloc[i] >= min_score
            and row["Close"] > row["high20"]
            and row["Close"] > row["sma50"]
            and row["sma50"] > row["sma200"]
            and regime_series.iloc[i]
        )
        if not entry_signal:
            i += 1
            continue

        entry_i = i + 1
        entry = float(df.iloc[entry_i]["Open"])
        atr = float(df.iloc[i]["atr14"])
        if pd.isna(atr) or atr <= 0:
            i += 1
            continue

        stop0 = initial_stop(entry, atr, stop_atr)
        stop = stop0
        highest_close = float(df.iloc[entry_i]["Close"])
        exit_i = entry_i
        exit_price = float(df.iloc[-1]["Close"])

        j = entry_i + 1
        while j < len(df):
            bar = df.iloc[j]
            if float(bar["Low"]) <= stop:
                exit_price = stop
                exit_i = j
                break

            highest_close = max(highest_close, float(bar["Close"]))
            stop = trailing_stop(stop, highest_close, float(bar["atr14"]), trail_atr)
            exit_i = j
            j += 1

        risk = entry - stop0
        r_multiple = (exit_price - entry) / risk if risk > 0 else 0.0
        trades.append(
            Trade(
                entry_date=df.index[entry_i],
                exit_date=df.index[exit_i],
                entry=entry,
                exit=exit_price,
                initial_stop=stop0,
                r_multiple=r_multiple,
            )
        )
        i = exit_i + 1

    return trades
