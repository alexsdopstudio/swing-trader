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
from .execution import load_execution_cost_models, scale_execution_cost_models
from .experiment import load_experiment_config, run_experiment


Downloader = Callable[[str, str, str | None], pd.DataFrame]


class SharedDownloadCache:
    """Cache provider downloads so every sensitivity scenario sees identical input frames."""

    def __init__(self, downloader: Downloader = download_daily) -> None:
        self._downloader = downloader
        self._cache: dict[tuple[str, str, str | None], pd.DataFrame] = {}

    def __call__(self, symbol: str, start: str, end: str | None) -> pd.DataFrame:
        key = (symbol, start, end)
        if key not in self._cache:
            self._cache[key] = self._downloader(symbol, start, end).copy()
        return self._cache[key].copy()

    @property
    def download_count(self) -> int:
        return len(self._cache)


def load_cost_sensitivity_config(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    if not isinstance(payload, dict):
        raise ValueError("cost sensitivity config must be a mapping")

    experiment = payload.get("experiment")
    scenarios = payload.get("scenarios")
    if not isinstance(experiment, dict):
        raise ValueError("cost sensitivity config must define an 'experiment' mapping")
    if not isinstance(scenarios, dict) or not scenarios:
        raise ValueError("cost sensitivity config must define non-empty 'scenarios'")
    if not isinstance(experiment.get("base_experiment_config"), str):
        raise ValueError("experiment.base_experiment_config must be a path string")

    normalized: dict[str, float] = {}
    for name, multiplier in scenarios.items():
        if not isinstance(name, str) or not name:
            raise ValueError("scenario names must be non-empty strings")
        value = float(multiplier)
        if value < 0:
            raise ValueError(f"scenario '{name}' multiplier cannot be negative")
        normalized[name] = value

    if normalized.get("baseline") != 1.0:
        raise ValueError("cost sensitivity scenarios must define baseline: 1.0")
    payload["scenarios"] = normalized
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
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if hasattr(value, "item"):
        return _json_safe(value.item())
    return value


def _model_payload(models) -> dict[str, Any]:
    return {
        "models": {
            name: {
                "commission_bps": model.commission_bps,
                "spread_bps": model.spread_bps,
                "slippage_bps": model.slippage_bps,
            }
            for name, model in models.items()
        }
    }


def _source_digests(result: dict[str, Any]) -> dict[str, str]:
    return {
        symbol: str(record["sha256"])
        for symbol, record in result["data_coverage"]["source"].items()
    }


def _digests_match(results: dict[str, dict[str, Any]]) -> bool:
    digest_sets = [_source_digests(result) for result in results.values()]
    return all(digests == digest_sets[0] for digests in digest_sets[1:])


def _delta(value: Any, baseline: Any) -> float | None:
    if value is None or baseline is None:
        return None
    return float(value) - float(baseline)


def _nonincreasing(values: list[float | None], tolerance: float = 1e-12) -> bool:
    finite = [value for value in values if value is not None]
    return all(right <= left + tolerance for left, right in zip(finite, finite[1:]))


def _nondecreasing(values: list[float | None], tolerance: float = 1e-12) -> bool:
    finite = [value for value in values if value is not None]
    return all(right + tolerance >= left for left, right in zip(finite, finite[1:]))


def _scenario_summary(
    name: str,
    multiplier: float,
    result: dict[str, Any],
    baseline: dict[str, Any],
) -> dict[str, Any]:
    metrics = result["metrics"]
    diagnostics = result["diagnostics"]
    baseline_metrics = baseline["metrics"]
    baseline_diagnostics = baseline["diagnostics"]
    return {
        "name": name,
        "multiplier": multiplier,
        "execution_costs": result["portfolio"]["execution_costs"],
        "metrics": metrics,
        "diagnostics": diagnostics,
        "deltas_vs_baseline": {
            "end_equity": _delta(metrics.get("end_equity"), baseline_metrics.get("end_equity")),
            "cagr": _delta(metrics.get("cagr"), baseline_metrics.get("cagr")),
            "profit_factor": _delta(
                metrics.get("profit_factor"), baseline_metrics.get("profit_factor")
            ),
            "expectancy_r": _delta(
                metrics.get("expectancy_r"), baseline_metrics.get("expectancy_r")
            ),
            "max_drawdown": _delta(
                metrics.get("max_drawdown"), baseline_metrics.get("max_drawdown")
            ),
            "total_execution_cost": _delta(
                diagnostics.get("total_execution_cost"),
                baseline_diagnostics.get("total_execution_cost"),
            ),
            "trade_count": _delta(
                diagnostics.get("trade_count"), baseline_diagnostics.get("trade_count")
            ),
        },
    }


def run_cost_sensitivity(
    config_path: str | Path,
    output_dir: str | Path,
    *,
    downloader: Downloader = download_daily,
    commit_sha: str | None = None,
) -> dict[str, Any]:
    config_path = Path(config_path)
    output_dir = Path(output_dir)
    sensitivity = load_cost_sensitivity_config(config_path)
    experiment = sensitivity["experiment"]
    scenarios = sensitivity["scenarios"]

    base_config_path = Path(experiment["base_experiment_config"])
    base_config = load_experiment_config(base_config_path)
    base_cost_path = Path(base_config["experiment"].get("cost_config", "config/execution-costs.yaml"))
    base_cost_models = load_execution_cost_models(base_cost_path)

    reference_results_path = experiment.get("reference_results")
    reference_results = None
    if isinstance(reference_results_path, str) and Path(reference_results_path).exists():
        reference_results = json.loads(Path(reference_results_path).read_text(encoding="utf-8"))

    output_dir.mkdir(parents=True, exist_ok=True)
    generated_dir = output_dir / "generated"
    scenarios_dir = output_dir / "scenarios"
    generated_dir.mkdir(parents=True, exist_ok=True)
    scenarios_dir.mkdir(parents=True, exist_ok=True)

    shared_downloader = SharedDownloadCache(downloader)
    producer_sha = commit_sha or _git_sha()
    scenario_results: dict[str, dict[str, Any]] = {}

    ordered = sorted(scenarios.items(), key=lambda item: item[1])
    for name, multiplier in ordered:
        scaled_models = scale_execution_cost_models(base_cost_models, multiplier)
        cost_path = generated_dir / f"{name}-costs.yaml"
        cost_path.write_text(
            yaml.safe_dump(_model_payload(scaled_models), sort_keys=False),
            encoding="utf-8",
        )

        scenario_config = copy.deepcopy(base_config)
        scenario_experiment = scenario_config["experiment"]
        scenario_experiment["id"] = f"{experiment['id']}-{name}"
        scenario_experiment["name"] = f"{experiment['name']}-{name}"
        scenario_experiment["research_stage"] = "sensitivity-scenario"
        scenario_experiment["cost_config"] = str(cost_path.resolve())

        scenario_config_path = generated_dir / f"{name}-config.yaml"
        scenario_config_path.write_text(
            yaml.safe_dump(scenario_config, sort_keys=False),
            encoding="utf-8",
        )
        scenario_results[name] = run_experiment(
            scenario_config_path,
            scenarios_dir / name,
            downloader=shared_downloader,
            commit_sha=producer_sha,
        )

    if not _digests_match(scenario_results):
        raise RuntimeError("market-data source digests differ across sensitivity scenarios")

    baseline = scenario_results["baseline"]
    summaries = {
        name: _scenario_summary(name, multiplier, scenario_results[name], baseline)
        for name, multiplier in ordered
    }

    ordered_summaries = [summaries[name] for name, _ in ordered]
    research_questions = sensitivity.get("research_questions", {})
    primary_name = str(research_questions.get("primary_scenario", "high"))
    stress_name = str(research_questions.get("stress_scenario", "stress"))
    if primary_name not in summaries or stress_name not in summaries:
        raise ValueError("research question scenario names must exist in scenarios")

    baseline_source = _source_digests(baseline)
    reference_source = None
    if reference_results is not None:
        reference_source = {
            symbol: str(record["sha256"])
            for symbol, record in reference_results.get("data_coverage", {}).get("source", {}).items()
            if "sha256" in record
        }

    exp0001_comparison = None
    if reference_results is not None:
        reference_metrics = reference_results.get("metrics", {})
        exp0001_comparison = {
            "reference_path": str(reference_results_path),
            "reference_code_commit_sha": reference_results.get("experiment", {}).get(
                "code_commit_sha"
            ),
            "source_digests_match_reference": reference_source == baseline_source,
            "metric_deltas_current_baseline_minus_reference": {
                key: _delta(baseline["metrics"].get(key), reference_metrics.get(key))
                for key in (
                    "end_equity",
                    "cagr",
                    "max_drawdown",
                    "profit_factor",
                    "expectancy_r",
                    "trade_count",
                )
            },
        }

    results = _json_safe(
        {
            "experiment": {
                "id": experiment["id"],
                "name": experiment["name"],
                "research_stage": experiment.get("research_stage", "sensitivity"),
                "code_commit_sha": producer_sha,
                "base_experiment_config": str(base_config_path),
                "base_experiment_config_sha256": _file_sha256(base_config_path),
                "base_execution_cost_config": str(base_cost_path),
                "base_execution_cost_config_sha256": _file_sha256(base_cost_path),
                "sensitivity_config_sha256": _file_sha256(config_path),
            },
            "runtime": baseline["runtime"],
            "data_coverage": baseline["data_coverage"],
            "data_consistency": {
                "identical_source_digests_across_scenarios": True,
                "shared_provider_download_count": shared_downloader.download_count,
            },
            "scenarios": summaries,
            "robustness": {
                "primary_scenario": primary_name,
                "primary_expectancy_positive": (
                    summaries[primary_name]["metrics"].get("expectancy_r") or 0.0
                )
                > 0.0,
                "stress_scenario": stress_name,
                "stress_expectancy_positive": (
                    summaries[stress_name]["metrics"].get("expectancy_r") or 0.0
                )
                > 0.0,
                "profit_factor_nonincreasing": _nonincreasing(
                    [summary["metrics"].get("profit_factor") for summary in ordered_summaries]
                ),
                "cagr_nonincreasing": _nonincreasing(
                    [summary["metrics"].get("cagr") for summary in ordered_summaries]
                ),
                "end_equity_nonincreasing": _nonincreasing(
                    [summary["metrics"].get("end_equity") for summary in ordered_summaries]
                ),
                "execution_cost_nondecreasing": _nondecreasing(
                    [
                        summary["diagnostics"].get("total_execution_cost")
                        for summary in ordered_summaries
                    ]
                ),
            },
            "exp0001_reference_comparison": exp0001_comparison,
        }
    )

    (output_dir / "results.json").write_text(
        json.dumps(results, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    (output_dir / "resolved-config.yaml").write_text(
        yaml.safe_dump(sensitivity, sort_keys=False),
        encoding="utf-8",
    )

    rows = []
    for name, _ in ordered:
        summary = summaries[name]
        metrics = summary["metrics"]
        diagnostics = summary["diagnostics"]
        rows.append(
            {
                "scenario": name,
                "multiplier": summary["multiplier"],
                "trade_count": metrics.get("trade_count"),
                "end_equity": metrics.get("end_equity"),
                "cagr": metrics.get("cagr"),
                "max_drawdown": metrics.get("max_drawdown"),
                "profit_factor": metrics.get("profit_factor"),
                "expectancy_r": metrics.get("expectancy_r"),
                "win_rate": metrics.get("win_rate"),
                "average_exposure": metrics.get("average_exposure"),
                "total_execution_cost": diagnostics.get("total_execution_cost"),
                "total_fees": diagnostics.get("total_fees"),
            }
        )
    pd.DataFrame(rows).to_csv(output_dir / "comparison.csv", index=False)

    notes = [
        f"# {experiment['id']} — Generated Cost-Sensitivity Summary",
        "",
        "This file is machine-generated factual output. Research interpretation is pending review.",
        "",
        f"- Code SHA: `{producer_sha}`",
        f"- Shared provider downloads: {shared_downloader.download_count}",
        f"- Source digests identical across scenarios: {_digests_match(scenario_results)}",
        "",
        "| Scenario | Multiplier | Trades | CAGR | Max DD | Profit factor | Expectancy R | Cost |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, _ in ordered:
        summary = summaries[name]
        metrics = summary["metrics"]
        diagnostics = summary["diagnostics"]
        notes.append(
            "| "
            + " | ".join(
                [
                    name,
                    f"{summary['multiplier']:.2f}x",
                    str(metrics.get("trade_count")),
                    str(metrics.get("cagr")),
                    str(metrics.get("max_drawdown")),
                    str(metrics.get("profit_factor")),
                    str(metrics.get("expectancy_r")),
                    str(diagnostics.get("total_execution_cost")),
                ]
            )
            + " |"
        )
    notes.extend(
        [
            "",
            "## Interpretation status",
            "",
            "Pending formal artifact inspection. Economic outcomes do not control workflow success.",
            "",
        ]
    )
    (output_dir / "notes.md").write_text("\n".join(notes), encoding="utf-8")
    return results
