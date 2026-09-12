from __future__ import annotations

import hashlib
import json
import math
import subprocess
from dataclasses import asdict
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from .cost_sensitivity import SharedDownloadCache
from .data import download_daily
from .execution import load_execution_cost_models
from .experiment import load_experiment_config, run_experiment
from .metrics import calculate_equity_curve_metrics
from .reference_baselines import buy_and_hold, equal_weight_basket
from .scanner import load_universe


_EXPECTED_REFERENCES = {
    "per_symbol": "buy-and-hold",
    "portfolio": "equal-weight-buy-and-hold",
    "rebalance": "none",
    "entry": "first-evaluation-open",
    "exit": "final-evaluation-close",
}


def load_reference_comparison_config(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    if not isinstance(payload, dict):
        raise ValueError("reference comparison config must be a mapping")

    experiment = payload.get("experiment")
    references = payload.get("reference_baselines")
    if not isinstance(experiment, dict):
        raise ValueError("reference comparison config must define an 'experiment' mapping")
    if not isinstance(experiment.get("base_experiment_config"), str):
        raise ValueError("experiment.base_experiment_config must be a path string")
    if references != _EXPECTED_REFERENCES:
        raise ValueError("reference_baselines must match the preregistered EXP-0004 definitions")
    return payload


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _file_sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if hasattr(value, "item"):
        return _json_safe(value.item())
    return value


def _delta(value: Any, reference: Any) -> float | None:
    if value is None or reference is None:
        return None
    return float(value) - float(reference)


def _metric_payload(curve: pd.Series, initial_equity: float) -> dict[str, Any]:
    return _json_safe(asdict(calculate_equity_curve_metrics(curve, initial_equity=initial_equity)))


def _selected_strategy_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    return {
        key: metrics.get(key)
        for key in (
            "start_equity",
            "end_equity",
            "total_return",
            "cagr",
            "max_drawdown",
            "sharpe",
            "sortino",
        )
    }


def _strategy_minus_reference(
    strategy: dict[str, Any], reference: dict[str, Any]
) -> dict[str, float | None]:
    return {
        key: _delta(strategy.get(key), reference.get(key))
        for key in ("total_return", "cagr", "max_drawdown", "sharpe", "sortino")
    }


def _execution_payload(result) -> dict[str, Any]:
    return {
        "entry_date": result.entry_date,
        "exit_date": result.exit_date,
        "entry_reference": result.entry_reference,
        "entry_fill": result.entry_fill,
        "entry_fee": result.entry_fee,
        "exit_reference": result.exit_reference,
        "exit_fill": result.exit_fill,
        "exit_fee": result.exit_fee,
        "total_execution_cost": result.total_execution_cost,
    }


def run_reference_comparison(
    config_path: str | Path,
    output_dir: str | Path,
    *,
    downloader=download_daily,
    commit_sha: str | None = None,
) -> dict[str, Any]:
    config_path = Path(config_path)
    output_dir = Path(output_dir)
    comparison = load_reference_comparison_config(config_path)
    experiment = comparison["experiment"]
    base_config_path = Path(experiment["base_experiment_config"])
    base_config = load_experiment_config(base_config_path)
    base_experiment = base_config["experiment"]
    portfolio = base_config["portfolio"]

    universe_path = Path(base_experiment.get("universe_config", "config/universe.yaml"))
    cost_path = Path(base_experiment.get("cost_config", "config/execution-costs.yaml"))
    universe = load_universe(universe_path)
    cost_models = load_execution_cost_models(cost_path)
    asset_classes = {item["symbol"]: item["asset_class"] for item in universe["assets"]}
    symbols = list(base_experiment["symbols"])
    unknown = [symbol for symbol in symbols if symbol not in asset_classes]
    if unknown:
        raise ValueError(f"symbols not found in universe config: {', '.join(unknown)}")

    output_dir.mkdir(parents=True, exist_ok=True)
    shared_downloader = SharedDownloadCache(downloader)
    producer_sha = commit_sha or _git_sha()
    strategy_result = run_experiment(
        base_config_path,
        output_dir / "strategy",
        downloader=shared_downloader,
        commit_sha=producer_sha,
    )
    downloads_after_strategy = shared_downloader.download_count

    warmup_start = str(base_experiment["warmup_start"])
    evaluation_start = pd.Timestamp(base_experiment["evaluation_start"])
    evaluation_end = pd.Timestamp(base_experiment["evaluation_end"])
    provider_end = evaluation_end.date().isoformat()
    initial_equity = float(portfolio.get("initial_equity", 5_000.0))
    sleeve_equity = initial_equity / len(symbols)

    full_capital = {}
    equal_weight_sleeves = {}
    for symbol in symbols:
        raw = shared_downloader(symbol, warmup_start, provider_end)
        evaluation = raw.loc[(raw.index >= evaluation_start) & (raw.index < evaluation_end)].copy()
        if evaluation.empty:
            raise RuntimeError(f"no passive evaluation data for {symbol}")
        model = cost_models.get(asset_classes[symbol], cost_models["default"])
        full_capital[symbol] = buy_and_hold(evaluation, initial_equity, model)
        equal_weight_sleeves[symbol] = buy_and_hold(evaluation, sleeve_equity, model)

    if shared_downloader.download_count != downloads_after_strategy:
        raise RuntimeError("passive baselines triggered additional provider downloads")

    basket = equal_weight_basket(equal_weight_sleeves)
    strategy_metrics = _selected_strategy_metrics(strategy_result["metrics"])
    basket_metrics = _metric_payload(basket.equity_curve, initial_equity)
    source_records = strategy_result["data_coverage"]["source"]
    missing_source = [symbol for symbol in symbols if symbol not in source_records]
    if missing_source:
        raise RuntimeError(f"strategy source provenance is missing symbols: {missing_source}")

    per_symbol: dict[str, Any] = {}
    for symbol in symbols:
        baseline = full_capital[symbol]
        metrics = _metric_payload(baseline.equity_curve, initial_equity)
        per_symbol[symbol] = {
            "asset_class": asset_classes[symbol],
            "metrics": metrics,
            "average_exposure": float(baseline.exposure_curve.mean()),
            "execution": _json_safe(_execution_payload(baseline)),
            "source_sha256": source_records[symbol]["sha256"],
            "strategy_minus_reference": _strategy_minus_reference(strategy_metrics, metrics),
        }

    basket_cost = sum(result.total_execution_cost for result in equal_weight_sleeves.values())
    results = _json_safe(
        {
            "experiment": {
                "id": experiment["id"],
                "name": experiment["name"],
                "research_stage": experiment.get(
                    "research_stage", "retrospective-reference-comparison"
                ),
                "true_out_of_sample_claim": False,
                "code_commit_sha": producer_sha,
                "base_experiment_config": str(base_config_path),
                "base_experiment_config_sha256": _file_sha256(base_config_path),
                "comparison_config_sha256": _file_sha256(config_path),
            },
            "runtime": strategy_result["runtime"],
            "data_consistency": {
                "shared_provider_download_count": shared_downloader.download_count,
                "provider_downloads_after_strategy": downloads_after_strategy,
                "no_additional_provider_downloads_for_baselines": True,
                "source": source_records,
                "passive_source_sha256": {
                    symbol: source_records[symbol]["sha256"] for symbol in symbols
                },
            },
            "strategy": {
                "strategy_version": strategy_result["experiment"]["strategy_version"],
                "metrics": strategy_metrics,
                "diagnostics": strategy_result["diagnostics"],
            },
            "reference_baselines": {
                "definitions": comparison["reference_baselines"],
                "equal_weight": {
                    "metrics": basket_metrics,
                    "average_exposure": float(basket.exposure_curve.mean()),
                    "total_execution_cost": basket_cost,
                    "strategy_minus_reference": _strategy_minus_reference(
                        strategy_metrics, basket_metrics
                    ),
                },
                "per_symbol": per_symbol,
            },
        }
    )

    (output_dir / "results.json").write_text(
        json.dumps(results, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    (output_dir / "resolved-config.yaml").write_text(
        yaml.safe_dump(comparison, sort_keys=False),
        encoding="utf-8",
    )

    rows = [
        {
            "reference": "strategy-v1",
            **strategy_metrics,
            "strategy_minus_total_return": 0.0,
            "strategy_minus_cagr": 0.0,
            "strategy_minus_max_drawdown": 0.0,
            "strategy_minus_sharpe": 0.0,
            "strategy_minus_sortino": 0.0,
        },
        {
            "reference": "equal-weight-buy-and-hold",
            **basket_metrics,
            **{
                f"strategy_minus_{key}": value
                for key, value in _strategy_minus_reference(
                    strategy_metrics, basket_metrics
                ).items()
            },
        },
    ]
    for symbol in symbols:
        metrics = per_symbol[symbol]["metrics"]
        rows.append(
            {
                "reference": f"{symbol}-buy-and-hold",
                **metrics,
                **{
                    f"strategy_minus_{key}": value
                    for key, value in per_symbol[symbol]["strategy_minus_reference"].items()
                },
            }
        )
    pd.DataFrame(rows).to_csv(output_dir / "comparison.csv", index=False)

    baseline_curves = pd.DataFrame(index=basket.equity_curve.index)
    baseline_curves["equal_weight"] = basket.equity_curve
    for symbol in symbols:
        curve = full_capital[symbol].equity_curve
        baseline_curves[symbol] = curve.reindex(baseline_curves.index).ffill().fillna(initial_equity)
    baseline_curves.index.name = "date"
    baseline_curves.to_csv(output_dir / "baseline-equity.csv")

    notes = [
        f"# {experiment['id']} — Generated Reference-Baseline Summary",
        "",
        "This file is machine-generated factual output. Research interpretation is pending review.",
        "",
        f"- Code SHA: `{producer_sha}`",
        f"- Shared provider downloads: {shared_downloader.download_count}",
        "- Passive baselines triggered additional provider downloads: no",
        "- True out-of-sample claim: false",
        "",
        "| Reference | Total return | CAGR | Max DD | Sharpe | Sortino |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        notes.append(
            "| "
            + " | ".join(
                [
                    str(row["reference"]),
                    str(row.get("total_return")),
                    str(row.get("cagr")),
                    str(row.get("max_drawdown")),
                    str(row.get("sharpe")),
                    str(row.get("sortino")),
                ]
            )
            + " |"
        )
    notes.extend(
        [
            "",
            "## Interpretation status",
            "",
            "Pending formal artifact inspection. These retrospective results must not be used to tune frozen v1.",
            "",
        ]
    )
    (output_dir / "notes.md").write_text("\n".join(notes), encoding="utf-8")
    return results
