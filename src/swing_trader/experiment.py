from __future__ import annotations

import hashlib
import json
import math
import platform
import subprocess
from collections import Counter
from collections.abc import Callable
from dataclasses import asdict
from datetime import date, datetime
from importlib.metadata import version
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from .data import download_daily
from .execution import load_execution_cost_models
from .historical import historical_regime, historical_scores
from .indicators import add_indicators
from .metrics import calculate_metrics
from .portfolio import PortfolioAsset, PortfolioBacktestConfig, backtest_portfolio
from .scanner import load_universe


Downloader = Callable[[str, str, str | None], pd.DataFrame]


def _require(mapping: dict[str, Any], key: str) -> Any:
    if key not in mapping:
        raise ValueError(f"experiment config is missing '{key}'")
    return mapping[key]


def load_experiment_config(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    if not isinstance(payload, dict):
        raise ValueError("experiment config must be a mapping")

    experiment = _require(payload, "experiment")
    portfolio = _require(payload, "portfolio")
    if not isinstance(experiment, dict) or not isinstance(portfolio, dict):
        raise ValueError("'experiment' and 'portfolio' must be mappings")

    symbols = experiment.get("symbols")
    if not isinstance(symbols, list) or not symbols or not all(isinstance(x, str) for x in symbols):
        raise ValueError("experiment.symbols must be a non-empty list of strings")

    warmup_start = pd.Timestamp(_require(experiment, "warmup_start"))
    evaluation_start = pd.Timestamp(_require(experiment, "evaluation_start"))
    evaluation_end = pd.Timestamp(_require(experiment, "evaluation_end"))
    if not warmup_start < evaluation_start < evaluation_end:
        raise ValueError("expected warmup_start < evaluation_start < evaluation_end")

    return payload


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (pd.Timestamp, datetime, date)):
        return value.isoformat()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if hasattr(value, "item"):
        return _json_safe(value.item())
    return value


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _slice_evaluation(
    data: pd.DataFrame,
    scores: pd.Series,
    regime: pd.Series,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    mask = (data.index >= start) & (data.index < end)
    sliced_data = data.loc[mask].copy()
    if sliced_data.empty:
        raise RuntimeError(f"no evaluation data between {start.date()} and {end.date()}")
    index = sliced_data.index
    return sliced_data, scores.reindex(index), regime.reindex(index).fillna(False).astype(bool)


def _coverage(data: pd.DataFrame) -> dict[str, Any]:
    return {
        "first_observation": data.index[0].date().isoformat(),
        "last_observation": data.index[-1].date().isoformat(),
        "rows": int(len(data)),
    }


def _frame_digest(data: pd.DataFrame) -> str:
    payload = data.to_csv(
        index=True,
        float_format="%.12g",
        date_format="%Y-%m-%dT%H:%M:%S",
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _source_record(data: pd.DataFrame) -> dict[str, Any]:
    return {**_coverage(data), "sha256": _frame_digest(data)}


def _trade_rows(result) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for trade in result.trades:
        row = asdict(trade)
        row["entry_date"] = trade.entry_date.isoformat()
        row["exit_date"] = trade.exit_date.isoformat()
        rows.append(row)
    return rows


def run_experiment(
    config_path: str | Path,
    output_dir: str | Path,
    *,
    downloader: Downloader = download_daily,
    commit_sha: str | None = None,
) -> dict[str, Any]:
    config_path = Path(config_path)
    output_dir = Path(output_dir)
    config = load_experiment_config(config_path)
    experiment = config["experiment"]
    portfolio_cfg = config["portfolio"]

    universe_path = Path(experiment.get("universe_config", "config/universe.yaml"))
    costs_path = Path(experiment.get("cost_config", "config/execution-costs.yaml"))
    universe = load_universe(universe_path)
    cost_models = load_execution_cost_models(costs_path)

    asset_classes = {item["symbol"]: item["asset_class"] for item in universe["assets"]}
    symbols = list(experiment["symbols"])
    unknown = [symbol for symbol in symbols if symbol not in asset_classes]
    if unknown:
        raise ValueError(f"symbols not found in universe config: {', '.join(unknown)}")

    benchmark_symbols = {
        "equity": universe["benchmark_equities"],
        "crypto": universe["benchmark_crypto"],
    }
    warmup_start = str(experiment["warmup_start"])
    evaluation_start = pd.Timestamp(experiment["evaluation_start"])
    evaluation_end = pd.Timestamp(experiment["evaluation_end"])
    provider_end = evaluation_end.date().isoformat()

    raw_cache: dict[str, pd.DataFrame] = {}
    indicator_cache: dict[str, pd.DataFrame] = {}

    def indicators_for(symbol: str) -> pd.DataFrame:
        if symbol not in indicator_cache:
            raw = downloader(symbol, warmup_start, provider_end)
            if raw.empty:
                raise RuntimeError(f"no data returned for required symbol {symbol}")
            raw_cache[symbol] = raw.copy()
            indicator_cache[symbol] = add_indicators(raw)
        return indicator_cache[symbol]

    benchmark_data = {
        asset_class: indicators_for(benchmark_symbols[asset_class])
        for asset_class in {asset_classes[symbol] for symbol in symbols}
    }

    assets: list[PortfolioAsset] = []
    evaluation_coverage: dict[str, Any] = {}
    source_coverage: dict[str, Any] = {}

    for symbol in symbols:
        asset_class = asset_classes[symbol]
        data = indicators_for(symbol)
        benchmark = benchmark_data[asset_class]
        score_benchmark = None if symbol == benchmark_symbols[asset_class] else benchmark
        scores = historical_scores(data, score_benchmark)
        regime = historical_regime(benchmark, data.index)
        sliced_data, sliced_scores, sliced_regime = _slice_evaluation(
            data,
            scores,
            regime,
            evaluation_start,
            evaluation_end,
        )
        assets.append(
            PortfolioAsset(
                symbol=symbol,
                data=sliced_data,
                scores=sliced_scores,
                regime=sliced_regime,
                asset_class=asset_class,
            )
        )
        source_coverage[symbol] = _source_record(raw_cache[symbol])
        evaluation_coverage[symbol] = _coverage(sliced_data)

    for benchmark_symbol in set(benchmark_symbols.values()):
        if benchmark_symbol in raw_cache:
            source_coverage.setdefault(benchmark_symbol, _source_record(raw_cache[benchmark_symbol]))

    backtest_config = PortfolioBacktestConfig(
        initial_equity=float(portfolio_cfg.get("initial_equity", 5_000.0)),
        risk_fraction=float(portfolio_cfg.get("risk_fraction", 0.005)),
        max_open_risk_fraction=float(portfolio_cfg.get("max_open_risk_fraction", 0.02)),
        max_positions=int(portfolio_cfg.get("max_positions", 4)),
        max_position_fraction=float(portfolio_cfg.get("max_position_fraction", 0.25)),
        min_score=int(portfolio_cfg.get("min_score", 70)),
        stop_atr=float(portfolio_cfg.get("stop_atr", 2.0)),
        trail_atr=float(portfolio_cfg.get("trail_atr", 2.5)),
        cost_models=cost_models,
    )
    result = backtest_portfolio(assets, backtest_config)
    metrics = calculate_metrics(result)
    trade_rows = _trade_rows(result)

    total_fees = sum(float(row["entry_fee"]) + float(row["exit_fee"]) for row in trade_rows)
    total_execution_cost = sum(float(row["total_cost"]) for row in trade_rows)
    exit_reasons = Counter(str(row["exit_reason"]) for row in trade_rows)

    resolved_costs = {
        name: {
            "commission_bps": model.commission_bps,
            "spread_bps": model.spread_bps,
            "slippage_bps": model.slippage_bps,
        }
        for name, model in cost_models.items()
    }

    results = _json_safe(
        {
            "experiment": {
                "id": experiment["id"],
                "name": experiment["name"],
                "strategy_version": experiment.get("strategy_version", "v1"),
                "research_stage": experiment.get("research_stage", "exploratory"),
                "data_provider": experiment.get("data_provider", "yfinance"),
                "symbols": symbols,
                "warmup_start": experiment["warmup_start"],
                "evaluation_start": experiment["evaluation_start"],
                "evaluation_end_exclusive": experiment["evaluation_end"],
                "code_commit_sha": commit_sha or _git_sha(),
            },
            "runtime": {
                "python": platform.python_version(),
                "numpy": version("numpy"),
                "pandas": version("pandas"),
                "PyYAML": version("PyYAML"),
                "yfinance": version("yfinance"),
            },
            "portfolio": {
                **{key: value for key, value in portfolio_cfg.items()},
                "execution_costs": resolved_costs,
            },
            "data_coverage": {
                "source": source_coverage,
                "evaluation": evaluation_coverage,
            },
            "metrics": asdict(metrics),
            "diagnostics": {
                "trade_count": len(trade_rows),
                "exit_reason_counts": dict(sorted(exit_reasons.items())),
                "total_fees": total_fees,
                "total_execution_cost": total_execution_cost,
            },
        }
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "results.json").write_text(
        json.dumps(results, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    pd.DataFrame(trade_rows).to_csv(output_dir / "trades.csv", index=False)
    curves = pd.concat(
        [result.equity_curve, result.exposure_curve, result.position_count_curve],
        axis=1,
    )
    curves.index.name = "date"
    curves.to_csv(output_dir / "equity.csv")
    (output_dir / "resolved-config.yaml").write_text(
        yaml.safe_dump(config, sort_keys=False),
        encoding="utf-8",
    )

    metric_values = results["metrics"]
    notes = [
        f"# {experiment['id']} — Generated Run Summary",
        "",
        "This file is machine-generated factual output. Research interpretation must be added only after review.",
        "",
        f"- Code SHA: `{results['experiment']['code_commit_sha']}`",
        f"- Evaluation: {experiment['evaluation_start']} to {experiment['evaluation_end']} (end exclusive)",
        f"- Symbols: {', '.join(symbols)}",
        f"- Trades: {len(trade_rows)}",
        f"- End equity: {metric_values['end_equity']}",
        f"- Total return: {metric_values['total_return']}",
        f"- CAGR: {metric_values['cagr']}",
        f"- Max drawdown: {metric_values['max_drawdown']}",
        f"- Profit factor: {metric_values['profit_factor']}",
        f"- Expectancy R: {metric_values['expectancy_r']}",
        f"- Total execution cost: {results['diagnostics']['total_execution_cost']}",
        "",
        "## Interpretation status",
        "",
        "Pending formal inspection. This exploratory baseline is not out-of-sample validation.",
        "",
    ]
    (output_dir / "notes.md").write_text("\n".join(notes), encoding="utf-8")
    return results
