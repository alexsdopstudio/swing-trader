from __future__ import annotations

from datetime import date

import pandas as pd
import yfinance as yf


REQUIRED_COLUMNS = ["Open", "High", "Low", "Close", "Volume"]


def download_daily(symbol: str, start: str = "2015-01-01", end: str | None = None) -> pd.DataFrame:
    end = end or date.today().isoformat()
    df = yf.download(
        symbol,
        start=start,
        end=end,
        interval="1d",
        auto_adjust=True,
        progress=False,
    )
    if df.empty:
        raise RuntimeError(f"No data returned for {symbol}")

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise RuntimeError(f"{symbol}: missing columns {missing}")
    return df[REQUIRED_COLUMNS].dropna().copy()
