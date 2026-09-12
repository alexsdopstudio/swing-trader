from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

import numpy as np

from .portfolio import PortfolioBacktestResult


@dataclass(frozen=True)
class BacktestMetrics:
    start_equity: float
    end_equity: float
    total_return: float
    cagr: float
    max_drawdown: float
    sharpe: float
    sortino: float
    profit_factor: float
    win_rate: float
    average_winner_r: float
    average_loser_r: float
    expectancy_r: float
    trade_count: int
    average_holding_days: float
    average_exposure: float
    best_r: float
    worst_r: float
    top5_profit_share: float


def _safe_mean(values: list[float]) -> float:
    return float(np.mean(values)) if values else float("nan")


def calculate_metrics(
    result: PortfolioBacktestResult,
    periods_per_year: float | None = None,
) -> BacktestMetrics:
    """Calculate deterministic summary metrics for a portfolio backtest result."""
    equity = result.equity_curve.dropna().astype(float)
    if equity.empty:
        raise ValueError("equity curve cannot be empty")

    start_equity = float(equity.iloc[0])
    end_equity = float(equity.iloc[-1])
    total_return = end_equity / start_equity - 1.0 if start_equity > 0 else float("nan")

    elapsed_days = (equity.index[-1] - equity.index[0]).total_seconds() / 86_400
    years = elapsed_days / 365.25
    if years > 0 and start_equity > 0 and end_equity > 0:
        cagr = (end_equity / start_equity) ** (1.0 / years) - 1.0
    else:
        cagr = float("nan")

    drawdown = equity / equity.cummax() - 1.0
    max_drawdown = float(drawdown.min())

    returns = equity.pct_change().dropna()
    annualization = periods_per_year
    if annualization is None:
        annualization = len(returns) / years if years > 0 and len(returns) > 0 else 365.25

    return_std = float(returns.std(ddof=1)) if len(returns) >= 2 else 0.0
    if return_std > 0:
        sharpe = float(returns.mean() / return_std * sqrt(annualization))
    else:
        sharpe = float("nan")

    downside_deviation = float(np.sqrt(np.mean(np.square(np.minimum(returns, 0.0)))))
    if len(returns) > 0 and downside_deviation > 0:
        sortino = float(returns.mean() / downside_deviation * sqrt(annualization))
    else:
        sortino = float("nan")

    trades = list(result.trades)
    pnls = [trade.pnl for trade in trades]
    r_values = [trade.r_multiple for trade in trades]
    winners = [trade for trade in trades if trade.pnl > 0]
    losers = [trade for trade in trades if trade.pnl < 0]

    gross_profit = sum(trade.pnl for trade in winners)
    gross_loss = abs(sum(trade.pnl for trade in losers))
    if gross_loss > 0:
        profit_factor = gross_profit / gross_loss
    elif gross_profit > 0:
        profit_factor = float("inf")
    else:
        profit_factor = float("nan")

    win_rate = len(winners) / len(trades) if trades else float("nan")
    average_winner_r = _safe_mean([trade.r_multiple for trade in winners])
    average_loser_r = _safe_mean([trade.r_multiple for trade in losers])
    expectancy_r = _safe_mean(r_values)
    average_holding_days = _safe_mean(
        [(trade.exit_date - trade.entry_date).total_seconds() / 86_400 for trade in trades]
    )
    average_exposure = float(result.exposure_curve.mean()) if not result.exposure_curve.empty else 0.0
    best_r = max(r_values) if r_values else float("nan")
    worst_r = min(r_values) if r_values else float("nan")

    positive_pnls = sorted((pnl for pnl in pnls if pnl > 0), reverse=True)
    if positive_pnls:
        top5_profit_share = sum(positive_pnls[:5]) / sum(positive_pnls)
    else:
        top5_profit_share = float("nan")

    return BacktestMetrics(
        start_equity=start_equity,
        end_equity=end_equity,
        total_return=total_return,
        cagr=cagr,
        max_drawdown=max_drawdown,
        sharpe=sharpe,
        sortino=sortino,
        profit_factor=profit_factor,
        win_rate=win_rate,
        average_winner_r=average_winner_r,
        average_loser_r=average_loser_r,
        expectancy_r=expectancy_r,
        trade_count=len(trades),
        average_holding_days=average_holding_days,
        average_exposure=average_exposure,
        best_r=best_r,
        worst_r=worst_r,
        top5_profit_share=top5_profit_share,
    )
