from __future__ import annotations

import hashlib
import json
import math
import platform
import subprocess
from collections.abc import Callable
from dataclasses import asdict, dataclass
from importlib.metadata import version
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from .data import download_daily
from .execution import load_execution_cost_models
from .experiment import _json_safe, load_experiment_config
from .scanner import load_universe


Downloader = Callable[[str, str, str | None], pd.DataFrame]


@dataclass(frozen=True)
class ReferenceMetrics:
    start_equity: float
    end_equity: float
    total_return: float
    cagr: float
    max_drawdown: float
    sharpe: float
    sortino: float


@dataclass(frozen=True)
class PassivePosition:
    symbol: str
    weight: float
    entry_date: str
    exit_date: str
    units: float
    entry_reference: float
    entry_fill: float
    entry_fee: float
    exit_reference: float
    exit_fill: float
    exit_fee: float
    total_execution_cost: float


class SharedDownloadCache:
    """Cache source frames so all passive references use one provider snapshot."""

    def __init__(self, downloader: Downloader = download_daily) -> None:
        self._downloader = downloader
        self._frames: dict[str, pd.DataFrame] = {}

    def load(self, symbol: str, start: str, end: str) -> pd.DataFrame:
        if symbol not in self._frames:
            frame = self._downloader(symbol, start, end)
            if frame.empty:
                raise RuntimeError(f"no data returned for required symbol {symbol}")
            self._frames[symbol] = frame.copy()
        return self._frames[symbol].copy()

    @property
    def download_count(self) -> int:
        return len(self._frames)


def load_reference_baseline_config(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    if not isinstance(payload, dict) or not isinstance(payload.get("experiment"), dict):
        raise ValueError("reference baseline config must define an 'experiment' mapping")
    experiment = payload["experiment"]
    if not isinstance(experiment.get("id"), str) or not experiment["id"]:
        raise ValueError("experiment.id must be a non-empty string")
    if not isinstance(experiment.get("base_experiment_config"), str):
        raise ValueError("experiment.base_experiment_config must be a path string")
    weights = payload.get("weights", "equal")
    if weights != "equal":
        if not isinstance(weights, dict) or not weights:
            raise ValueError("weights must be 'equal' or a non-empty mapping")
        values = [float(value) for value in weights.values()]
        if any(value <= 0 for value in values) or not math.isclose(sum(values), 1.0, abs_tol=1e-9):
            raise ValueError("fixed weights must be positive and sum to 1.0")
    return payload


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _frame_digest(data: pd.DataFrame) -> str:
    return hashlib.sha256(
        data.to_csv(index=True, float_format="%.12g", date_format="%Y-%m-%dT%H:%M:%S").encode()
    ).hexdigest()


def _slice(frame: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    sliced = frame.loc[(frame.index >= start) & (frame.index < end)].copy()
    if sliced.empty:
        raise RuntimeError(f"no evaluation data between {start.date()} and {end.date()}")
    if (sliced["Open"] <= 0).any() or (sliced["Close"] <= 0).any():
        raise RuntimeError("reference baseline requires positive Open and Close prices")
    return sliced


def _curve_metrics(equity: pd.Series) -> ReferenceMetrics:
    equity = equity.dropna().astype(float)
    start_equity, end_equity = float(equity.iloc[0]), float(equity.iloc[-1])
    total_return = end_equity / start_equity - 1.0
    days = (equity.index[-1] - equity.index[0]).total_seconds() / 86_400
    years = days / 365.25
    cagr = (end_equity / start_equity) ** (1.0 / years) - 1.0 if years > 0 else float("nan")
    drawdown = equity / equity.cummax() - 1.0
    returns = equity.pct_change().dropna()
    annualization = len(returns) / years if years > 0 and len(returns) else 365.25
    std = float(returns.std(ddof=1)) if len(returns) >= 2 else 0.0
    sharpe = float(returns.mean() / std * math.sqrt(annualization)) if std > 0 else float("nan")
    downside = float((returns.clip(upper=0).pow(2).mean()) ** 0.5)
    sortino = (
        float(returns.mean() / downside * math.sqrt(annualization))
        if len(returns) and downside > 0
        else float("nan")
    )
    return ReferenceMetrics(start_equity, end_equity, total_return, cagr, float(drawdown.min()), sharpe, sortino)


def _resolved_weights(symbols: list[str], weights: Any) -> dict[str, float]:
    if weights == "equal":
        return {symbol: 1.0 / len(symbols) for symbol in symbols}
    if set(weights) != set(symbols):
        raise ValueError("fixed weights must cover exactly the base experiment symbols")
    return {symbol: float(weights[symbol]) for symbol in symbols}


def run_reference_baseline(
    config_path: str | Path,
    output_dir: str | Path,
    *,
    downloader: Downloader = download_daily,
    commit_sha: str | None = None,
) -> dict[str, Any]:
    config_path, output_dir = Path(config_path), Path(output_dir)
    config = load_reference_baseline_config(config_path)
    specification = config["experiment"]
    base_path = Path(specification["base_experiment_config"])
    base = load_experiment_config(base_path)
    base_experiment, portfolio = base["experiment"], base["portfolio"]
    symbols = list(base_experiment["symbols"])
    weights = _resolved_weights(symbols, config.get("weights", "equal"))
    universe = load_universe(Path(base_experiment.get("universe_config", "config/universe.yaml")))
    asset_classes = {item["symbol"]: item["asset_class"] for item in universe["assets"]}
    costs = load_execution_cost_models(Path(base_experiment.get("cost_config", "config/execution-costs.yaml")))
    start, end = pd.Timestamp(base_experiment["evaluation_start"]), pd.Timestamp(base_experiment["evaluation_end"])
    cache = SharedDownloadCache(downloader)
    frames = {
        symbol: _slice(cache.load(symbol, str(base_experiment["warmup_start"]), str(base_experiment["evaluation_end"])), start, end)
        for symbol in symbols
    }
    initial_equity = float(portfolio.get("initial_equity", 5_000.0))
    positions: list[PassivePosition] = []
    value_frames: list[pd.Series] = []
    for symbol in symbols:
        frame, model = frames[symbol], costs.get(asset_classes[symbol], costs["default"])
        allocation = initial_equity * weights[symbol]
        entry_reference, exit_reference = float(frame["Open"].iloc[0]), float(frame["Close"].iloc[-1])
        units = allocation / model.buy_cash_per_unit(entry_reference)
        entry_fill, exit_fill = model.buy_fill(entry_reference), model.sell_fill(exit_reference)
        entry_fee, exit_fee = model.commission(units * entry_fill), model.commission(units * exit_fill)
        position = PassivePosition(
            symbol, weights[symbol], frame.index[0].date().isoformat(), frame.index[-1].date().isoformat(), units,
            entry_reference, entry_fill, entry_fee, exit_reference, exit_fill, exit_fee,
            units * (entry_fill - entry_reference) + entry_fee + units * (exit_reference - exit_fill) + exit_fee,
        )
        positions.append(position)
        marked = units * frame["Close"].astype(float)
        marked.iloc[0] = allocation - entry_fee + units * (float(frame["Close"].iloc[0]) - entry_fill)
        marked.iloc[-1] = units * exit_fill - exit_fee
        value_frames.append(marked.rename(symbol))
    values = pd.concat(value_frames, axis=1).sort_index().ffill().fillna(0.0)
    equity = values.sum(axis=1).rename("equity")
    metrics = _curve_metrics(equity)
    results = _json_safe({
        "experiment": {"id": specification["id"], "name": specification.get("name", "passive-reference-baseline"),
                       "research_stage": specification.get("research_stage", "historical-reference"),
                       "code_commit_sha": commit_sha or _git_sha(), "base_experiment_config": str(base_path),
                       "evaluation_start": base_experiment["evaluation_start"], "evaluation_end_exclusive": base_experiment["evaluation_end"],
                       "symbols": symbols, "weights": weights},
        "runtime": {"python": platform.python_version(), "numpy": version("numpy"), "pandas": version("pandas"), "PyYAML": version("PyYAML"), "yfinance": version("yfinance")},
        "metrics": asdict(metrics), "positions": [asdict(position) for position in positions],
        "data_coverage": {symbol: {"first_observation": frame.index[0].date().isoformat(), "last_observation": frame.index[-1].date().isoformat(), "rows": len(frame), "sha256": _frame_digest(frame)} for symbol, frame in frames.items()},
        "diagnostics": {"shared_provider_download_count": cache.download_count, "total_execution_cost": sum(position.total_execution_cost for position in positions)},
    })
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "results.json").write_text(json.dumps(results, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    equity.to_frame().to_csv(output_dir / "equity.csv", index_label="date")
    pd.DataFrame([asdict(position) for position in positions]).to_csv(output_dir / "positions.csv", index=False)
    (output_dir / "resolved-config.yaml").write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    return results
