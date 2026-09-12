from __future__ import annotations

import copy
import hashlib
import json
import math
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from .data import download_daily
from .experiment import load_experiment_config, run_experiment
from .scanner import load_universe


Downloader = Callable[[str, str, str | None], pd.DataFrame]


class HistoricalSnapshot:
    """One immutable provider snapshot that serves date slices to multiple fold runs."""

    def __init__(
        self,
        symbols: list[str],
        start: str,
        end: str,
        *,
        downloader: Downloader = download_daily,
    ) -> None:
        self.start = pd.Timestamp(start)
        self.end = pd.Timestamp(end)
        if self.start >= self.end:
            raise ValueError("snapshot start must be before snapshot end")

        self._frames: dict[str, pd.DataFrame] = {}
        for symbol in dict.fromkeys(symbols):
            frame = downloader(symbol, start, end)
            if frame.empty:
                raise RuntimeError(f"no data returned for required snapshot symbol {symbol}")
            self._frames[symbol] = frame.copy()

    def __call__(self, symbol: str, start: str, end: str | None) -> pd.DataFrame:
        if symbol not in self._frames:
            raise RuntimeError(f"symbol {symbol} is not present in the frozen snapshot")
        requested_start = pd.Timestamp(start)
        requested_end = pd.Timestamp(end) if end is not None else self.end
        if requested_start < self.start or requested_end > self.end:
            raise RuntimeError(
                f"requested slice {requested_start.date()}..{requested_end.date()} "
                f"is outside snapshot {self.start.date()}..{self.end.date()}"
            )
        frame = self._frames[symbol]
        sliced = frame.loc[(frame.index >= requested_start) & (frame.index < requested_end)].copy()
        if sliced.empty:
            raise RuntimeError(f"snapshot slice is empty for {symbol}")
        return sliced

    @property
    def download_count(self) -> int:
        return len(self._frames)

    def source_records(self) -> dict[str, dict[str, Any]]:
        return {symbol: _source_record(frame) for symbol, frame in sorted(self._frames.items())}


def load_temporal_stability_config(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    if not isinstance(payload, dict):
        raise ValueError("temporal stability config must be a mapping")

    experiment = payload.get("experiment")
    folds = payload.get("folds")
    if not isinstance(experiment, dict):
        raise ValueError("temporal stability config must define an 'experiment' mapping")
    if not isinstance(experiment.get("base_experiment_config"), str):
        raise ValueError("experiment.base_experiment_config must be a path string")
    if not isinstance(folds, list) or not folds:
        raise ValueError("temporal stability config must define a non-empty 'folds' list")

    snapshot_start = pd.Timestamp(experiment.get("snapshot_start"))
    snapshot_end = pd.Timestamp(experiment.get("snapshot_end"))
    if snapshot_start >= snapshot_end:
        raise ValueError("snapshot_start must be before snapshot_end")

    normalized_folds: list[dict[str, Any]] = []
    previous_end: pd.Timestamp | None = None
    names: set[str] = set()
    for raw in folds:
        if not isinstance(raw, dict):
            raise ValueError("each fold must be a mapping")
        name = str(raw.get("name", "")).strip()
        if not name:
            raise ValueError("each fold must have a non-empty name")
        if name in names:
            raise ValueError(f"duplicate fold name: {name}")
        names.add(name)

        start = pd.Timestamp(raw.get("evaluation_start"))
        end = pd.Timestamp(raw.get("evaluation_end"))
        if not start < end:
            raise ValueError(f"fold {name} must have evaluation_start < evaluation_end")
        if start < snapshot_start or end > snapshot_end:
            raise ValueError(f"fold {name} is outside the configured snapshot window")
        if previous_end is not None and start < previous_end:
            raise ValueError("folds must be ordered and non-overlapping")
        previous_end = end
        normalized_folds.append(
            {
                "name": name,
                "evaluation_start": start.date().isoformat(),
                "evaluation_end": end.date().isoformat(),
            }
        )

    payload["folds"] = normalized_folds
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


def _frame_digest(data: pd.DataFrame) -> str:
    payload = data.to_csv(
        index=True,
        float_format="%.12g",
        date_format="%Y-%m-%dT%H:%M:%S",
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _source_record(data: pd.DataFrame) -> dict[str, Any]:
    return {
        "first_observation": data.index[0].date().isoformat(),
        "last_observation": data.index[-1].date().isoformat(),
        "rows": int(len(data)),
        "sha256": _frame_digest(data),
    }


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if hasattr(value, "item"):
        return _json_safe(value.item())
    return value


def _required_symbols(base_config: dict[str, Any]) -> list[str]:
    experiment = base_config["experiment"]
    universe = load_universe(Path(experiment.get("universe_config", "config/universe.yaml")))
    asset_classes = {item["symbol"]: item["asset_class"] for item in universe["assets"]}
    symbols = list(experiment["symbols"])
    required = list(symbols)
    for symbol in symbols:
        asset_class = asset_classes[symbol]
        benchmark = (
            universe["benchmark_equities"]
            if asset_class == "equity"
            else universe["benchmark_crypto"]
        )
        if benchmark not in required:
            required.append(benchmark)
    return required


def _fold_summary(name: str, result: dict[str, Any]) -> dict[str, Any]:
    metrics = result["metrics"]
    diagnostics = result["diagnostics"]
    return {
        "name": name,
        "trade_count": int(metrics.get("trade_count", diagnostics.get("trade_count", 0))),
        "start_equity": metrics.get("start_equity"),
        "end_equity": metrics.get("end_equity"),
        "total_return": metrics.get("total_return"),
        "cagr": metrics.get("cagr"),
        "max_drawdown": metrics.get("max_drawdown"),
        "sharpe": metrics.get("sharpe"),
        "sortino": metrics.get("sortino"),
        "profit_factor": metrics.get("profit_factor"),
        "expectancy_r": metrics.get("expectancy_r"),
        "win_rate": metrics.get("win_rate"),
        "average_winner_r": metrics.get("average_winner_r"),
        "average_loser_r": metrics.get("average_loser_r"),
        "average_holding_days": metrics.get("average_holding_days"),
        "average_exposure": metrics.get("average_exposure"),
        "top5_profit_share": metrics.get("top5_profit_share"),
        "total_execution_cost": diagnostics.get("total_execution_cost"),
        "total_fees": diagnostics.get("total_fees"),
    }


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    return float(pd.Series(values).median())


def aggregate_temporal_diagnostics(folds: list[dict[str, Any]]) -> dict[str, Any]:
    if not folds:
        raise ValueError("at least one fold is required")

    positive_expectancy = [
        fold for fold in folds if fold.get("expectancy_r") is not None and fold["expectancy_r"] > 0
    ]
    pf_above_one = [
        fold for fold in folds if fold.get("profit_factor") is not None and fold["profit_factor"] > 1
    ]
    positive_return = [
        fold for fold in folds if fold.get("total_return") is not None and fold["total_return"] > 0
    ]

    expectancy_values = [
        float(fold["expectancy_r"])
        for fold in folds
        if fold.get("expectancy_r") is not None
    ]
    profit_factors = [
        float(fold["profit_factor"])
        for fold in folds
        if fold.get("profit_factor") is not None
    ]
    drawdowns = [
        float(fold["max_drawdown"])
        for fold in folds
        if fold.get("max_drawdown") is not None
    ]
    total_trades = sum(int(fold.get("trade_count") or 0) for fold in folds)
    weighted_numerator = sum(
        float(fold["expectancy_r"]) * int(fold.get("trade_count") or 0)
        for fold in folds
        if fold.get("expectancy_r") is not None
    )

    return {
        "fold_count": len(folds),
        "positive_expectancy_folds": len(positive_expectancy),
        "positive_expectancy_fraction": len(positive_expectancy) / len(folds),
        "profit_factor_above_one_folds": len(pf_above_one),
        "profit_factor_above_one_fraction": len(pf_above_one) / len(folds),
        "positive_return_folds": len(positive_return),
        "positive_return_fraction": len(positive_return) / len(folds),
        "median_expectancy_r": _median(expectancy_values),
        "minimum_expectancy_r": min(expectancy_values) if expectancy_values else None,
        "median_profit_factor": _median(profit_factors),
        "worst_fold_max_drawdown": min(drawdowns) if drawdowns else None,
        "total_closed_trades_across_independent_folds": total_trades,
        "trade_count_weighted_expectancy_r": (
            weighted_numerator / total_trades if total_trades > 0 else None
        ),
    }


def run_temporal_stability(
    config_path: str | Path,
    output_dir: str | Path,
    *,
    downloader: Downloader = download_daily,
    commit_sha: str | None = None,
) -> dict[str, Any]:
    config_path = Path(config_path)
    output_dir = Path(output_dir)
    config = load_temporal_stability_config(config_path)
    experiment = config["experiment"]
    folds = config["folds"]

    base_config_path = Path(experiment["base_experiment_config"])
    base_config = load_experiment_config(base_config_path)
    snapshot_start = str(experiment["snapshot_start"])
    snapshot_end = str(experiment["snapshot_end"])
    required_symbols = _required_symbols(base_config)
    snapshot = HistoricalSnapshot(
        required_symbols,
        snapshot_start,
        snapshot_end,
        downloader=downloader,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    generated_dir = output_dir / "generated"
    folds_dir = output_dir / "folds"
    generated_dir.mkdir(parents=True, exist_ok=True)
    folds_dir.mkdir(parents=True, exist_ok=True)

    producer_sha = commit_sha or _git_sha()
    fold_results: list[dict[str, Any]] = []
    for fold in folds:
        fold_config = copy.deepcopy(base_config)
        fold_experiment = fold_config["experiment"]
        fold_experiment["id"] = f"{experiment['id']}-{fold['name']}"
        fold_experiment["name"] = f"{experiment['name']}-{fold['name']}"
        fold_experiment["research_stage"] = "retrospective-temporal-fold"
        fold_experiment["evaluation_start"] = fold["evaluation_start"]
        fold_experiment["evaluation_end"] = fold["evaluation_end"]

        fold_config_path = generated_dir / f"{fold['name']}-config.yaml"
        fold_config_path.write_text(
            yaml.safe_dump(fold_config, sort_keys=False),
            encoding="utf-8",
        )
        result = run_experiment(
            fold_config_path,
            folds_dir / fold["name"],
            downloader=snapshot,
            commit_sha=producer_sha,
        )
        summary = _fold_summary(fold["name"], result)
        summary["evaluation_start"] = fold["evaluation_start"]
        summary["evaluation_end_exclusive"] = fold["evaluation_end"]
        fold_results.append(summary)

    diagnostics = aggregate_temporal_diagnostics(fold_results)
    questions = config.get("research_questions", {})
    min_positive = int(questions.get("minimum_positive_expectancy_folds", 4))
    min_pf = int(questions.get("minimum_profit_factor_above_one_folds", 4))
    weak_names = [str(name) for name in questions.get("weak_folds_to_confirm", [])]
    folds_by_name = {fold["name"]: fold for fold in fold_results}
    weak_fold_checks = {
        name: {
            "present": name in folds_by_name,
            "nonpositive_expectancy": (
                folds_by_name[name].get("expectancy_r") is not None
                and folds_by_name[name]["expectancy_r"] <= 0
            )
            if name in folds_by_name
            else None,
            "nonpositive_total_return": (
                folds_by_name[name].get("total_return") is not None
                and folds_by_name[name]["total_return"] <= 0
            )
            if name in folds_by_name
            else None,
        }
        for name in weak_names
    }

    reference_results = None
    reference_path = experiment.get("reference_results")
    if isinstance(reference_path, str) and Path(reference_path).exists():
        reference_results = json.loads(Path(reference_path).read_text(encoding="utf-8"))

    results = _json_safe(
        {
            "experiment": {
                "id": experiment["id"],
                "name": experiment["name"],
                "research_stage": experiment.get(
                    "research_stage", "retrospective-temporal-diagnostic"
                ),
                "code_commit_sha": producer_sha,
                "base_experiment_config": str(base_config_path),
                "base_experiment_config_sha256": _file_sha256(base_config_path),
                "snapshot_start": snapshot_start,
                "snapshot_end_exclusive": snapshot_end,
                "historical_data_already_observed": True,
                "true_out_of_sample_claim": False,
            },
            "runtime": {
                "source_runtime": "recorded in per-fold results",
            },
            "data_snapshot": {
                "provider_download_count": snapshot.download_count,
                "source": snapshot.source_records(),
            },
            "folds": fold_results,
            "diagnostics": diagnostics,
            "predeclared_questions": {
                "minimum_positive_expectancy_folds": min_positive,
                "minimum_profit_factor_above_one_folds": min_pf,
                "positive_expectancy_threshold_met": (
                    diagnostics["positive_expectancy_folds"] >= min_positive
                ),
                "profit_factor_threshold_met": (
                    diagnostics["profit_factor_above_one_folds"] >= min_pf
                ),
                "weak_fold_checks": weak_fold_checks,
            },
            "exp0001_reference": {
                "path": reference_path,
                "aggregate_metrics": reference_results.get("metrics")
                if reference_results is not None
                else None,
                "note": (
                    "EXP-0001 is contextual reference only; EXP-0003 folds are retrospective and "
                    "must not be described as unseen holdout data."
                ),
            },
        }
    )

    (output_dir / "results.json").write_text(
        json.dumps(results, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    (output_dir / "resolved-config.yaml").write_text(
        yaml.safe_dump(config, sort_keys=False),
        encoding="utf-8",
    )
    pd.DataFrame(fold_results).to_csv(output_dir / "fold-comparison.csv", index=False)

    notes = [
        f"# {experiment['id']} — Generated Temporal-Stability Summary",
        "",
        "This file is machine-generated factual output. Research interpretation is pending review.",
        "",
        "Historical fold results are retrospective diagnostics, not true out-of-sample validation.",
        "",
        f"- Code SHA: `{producer_sha}`",
        f"- Provider downloads: {snapshot.download_count}",
        f"- Positive-expectancy folds: {diagnostics['positive_expectancy_folds']}/{diagnostics['fold_count']}",
        f"- Profit-factor>1 folds: {diagnostics['profit_factor_above_one_folds']}/{diagnostics['fold_count']}",
        "",
        "| Fold | Trades | Return | Max DD | Profit factor | Expectancy R | Exposure |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for fold in fold_results:
        notes.append(
            "| "
            + " | ".join(
                [
                    fold["name"],
                    str(fold["trade_count"]),
                    str(fold["total_return"]),
                    str(fold["max_drawdown"]),
                    str(fold["profit_factor"]),
                    str(fold["expectancy_r"]),
                    str(fold["average_exposure"]),
                ]
            )
            + " |"
        )
    notes.extend(
        [
            "",
            "## Interpretation status",
            "",
            "Pending formal artifact inspection. Do not tune v1 from these folds in this PR.",
            "",
        ]
    )
    (output_dir / "notes.md").write_text("\n".join(notes), encoding="utf-8")
    return results
