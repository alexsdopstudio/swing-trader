from __future__ import annotations

import copy
import hashlib
import json
import math
import subprocess
from dataclasses import dataclass
from itertools import product
from pathlib import Path
from statistics import median
from typing import Any

import pandas as pd
import yaml

from .cost_sensitivity import SharedDownloadCache
from .data import download_daily
from .experiment import load_experiment_config, run_experiment


_EXPECTED_PARAMETERS = {
    "min_score": [65, 70, 75],
    "stop_atr": [1.5, 2.0, 2.5],
    "trail_atr": [2.0, 2.5, 3.0],
}
_EXPECTED_CENTER = {"min_score": 70, "stop_atr": 2.0, "trail_atr": 2.5}
_EXPECTED_CRITERIA = {
    "minimum_joint_positive_scenarios": 18,
    "minimum_joint_positive_axial_neighbors": 5,
    "minimum_median_expectancy_r": 0.5,
    "missing_expectancy_r_for_median": 0.0,
    "center_reference_tolerances": {
        "total_return": 0.01,
        "cagr": 0.0025,
        "max_drawdown": 0.005,
        "expectancy_r": 0.10,
        "trade_count": 2,
    },
}
_ALLOWED_PORTFOLIO_FIELDS = frozenset(_EXPECTED_PARAMETERS)


@dataclass(frozen=True)
class NeighborhoodScenario:
    name: str
    min_score: int
    stop_atr: float
    trail_atr: float

    def parameters(self) -> dict[str, int | float]:
        return {
            "min_score": self.min_score,
            "stop_atr": self.stop_atr,
            "trail_atr": self.trail_atr,
        }


def _normalized_parameters(payload: Any) -> dict[str, list[int | float]]:
    if not isinstance(payload, dict):
        raise ValueError("parameter neighborhood config must define a 'parameters' mapping")
    try:
        return {
            "min_score": [int(value) for value in payload["min_score"]],
            "stop_atr": [float(value) for value in payload["stop_atr"]],
            "trail_atr": [float(value) for value in payload["trail_atr"]],
        }
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("parameter neighborhood values are malformed") from exc


def _normalized_center(payload: Any) -> dict[str, int | float]:
    if not isinstance(payload, dict):
        raise ValueError("parameter neighborhood config must define a 'center' mapping")
    try:
        return {
            "min_score": int(payload["min_score"]),
            "stop_atr": float(payload["stop_atr"]),
            "trail_atr": float(payload["trail_atr"]),
        }
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("parameter neighborhood center is malformed") from exc


def _normalized_criteria(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("parameter neighborhood config must define 'robustness_criteria'")
    tolerances = payload.get("center_reference_tolerances")
    if not isinstance(tolerances, dict):
        raise ValueError("center_reference_tolerances must be a mapping")
    try:
        return {
            "minimum_joint_positive_scenarios": int(
                payload["minimum_joint_positive_scenarios"]
            ),
            "minimum_joint_positive_axial_neighbors": int(
                payload["minimum_joint_positive_axial_neighbors"]
            ),
            "minimum_median_expectancy_r": float(payload["minimum_median_expectancy_r"]),
            "missing_expectancy_r_for_median": float(
                payload["missing_expectancy_r_for_median"]
            ),
            "center_reference_tolerances": {
                "total_return": float(tolerances["total_return"]),
                "cagr": float(tolerances["cagr"]),
                "max_drawdown": float(tolerances["max_drawdown"]),
                "expectancy_r": float(tolerances["expectancy_r"]),
                "trade_count": int(tolerances["trade_count"]),
            },
        }
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("robustness criteria are malformed") from exc


def load_parameter_neighborhood_config(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    if not isinstance(payload, dict):
        raise ValueError("parameter neighborhood config must be a mapping")

    experiment = payload.get("experiment")
    if not isinstance(experiment, dict):
        raise ValueError("parameter neighborhood config must define an 'experiment' mapping")
    if experiment.get("id") != "EXP-0005":
        raise ValueError("parameter neighborhood experiment id must remain EXP-0005")
    if experiment.get("base_experiment_config") != "experiments/EXP-0001-baseline/config.yaml":
        raise ValueError("EXP-0005 must remain anchored to the frozen EXP-0001 config")
    if experiment.get("reference_results") != "experiments/EXP-0001-baseline/results.json":
        raise ValueError("EXP-0005 must compare its center with the durable EXP-0001 results")

    parameters = _normalized_parameters(payload.get("parameters"))
    center = _normalized_center(payload.get("center"))
    criteria = _normalized_criteria(payload.get("robustness_criteria"))
    if parameters != _EXPECTED_PARAMETERS:
        raise ValueError("EXP-0005 parameter grid differs from the preregistered neighborhood")
    if center != _EXPECTED_CENTER:
        raise ValueError("EXP-0005 center differs from frozen v1")
    if criteria != _EXPECTED_CRITERIA:
        raise ValueError("EXP-0005 robustness criteria differ from the preregistered values")

    payload["parameters"] = parameters
    payload["center"] = center
    payload["robustness_criteria"] = criteria
    return payload


def _slug(value: int | float) -> str:
    return f"{value:g}".replace("-", "m").replace(".", "p")


def generate_scenarios(config: dict[str, Any]) -> list[NeighborhoodScenario]:
    parameters = config["parameters"]
    scenarios = []
    for min_score, stop_atr, trail_atr in product(
        parameters["min_score"], parameters["stop_atr"], parameters["trail_atr"]
    ):
        scenarios.append(
            NeighborhoodScenario(
                name=(
                    f"score-{_slug(min_score)}-stop-{_slug(stop_atr)}-"
                    f"trail-{_slug(trail_atr)}"
                ),
                min_score=int(min_score),
                stop_atr=float(stop_atr),
                trail_atr=float(trail_atr),
            )
        )
    if len(scenarios) != 27 or len({scenario.name for scenario in scenarios}) != 27:
        raise RuntimeError("EXP-0005 must expand to exactly 27 unique scenarios")
    return scenarios


def is_center(scenario: NeighborhoodScenario, center: dict[str, Any]) -> bool:
    return scenario.parameters() == center


def is_axial_neighbor(scenario: NeighborhoodScenario, center: dict[str, Any]) -> bool:
    differences = sum(
        scenario.parameters()[key] != center[key]
        for key in ("min_score", "stop_atr", "trail_atr")
    )
    return differences == 1


def build_scenario_config(
    base_config: dict[str, Any],
    scenario: NeighborhoodScenario,
    experiment: dict[str, Any],
) -> dict[str, Any]:
    scenario_config = copy.deepcopy(base_config)
    portfolio = scenario_config["portfolio"]
    base_portfolio = base_config["portfolio"]
    for key, value in scenario.parameters().items():
        portfolio[key] = value

    changed = {
        key
        for key in set(base_portfolio) | set(portfolio)
        if base_portfolio.get(key) != portfolio.get(key)
    }
    if not changed.issubset(_ALLOWED_PORTFOLIO_FIELDS):
        raise RuntimeError(f"scenario changes forbidden portfolio fields: {sorted(changed)}")

    scenario_experiment = scenario_config["experiment"]
    scenario_experiment["id"] = f"{experiment['id']}-{scenario.name}"
    scenario_experiment["name"] = f"{experiment['name']}-{scenario.name}"
    scenario_experiment["research_stage"] = "parameter-neighborhood-scenario"
    return scenario_config


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
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


def _source_digests(result: dict[str, Any]) -> dict[str, str]:
    return {
        symbol: str(record["sha256"])
        for symbol, record in result["data_coverage"]["source"].items()
    }


def _digests_match(results: dict[str, dict[str, Any]]) -> bool:
    digest_sets = [_source_digests(result) for result in results.values()]
    return bool(digest_sets) and all(digests == digest_sets[0] for digests in digest_sets[1:])


def _delta(value: Any, baseline: Any) -> float | None:
    if value is None or baseline is None:
        return None
    return float(value) - float(baseline)


def _joint_positive(metrics: dict[str, Any]) -> bool:
    return (
        (metrics.get("total_return") or 0.0) > 0.0
        and (metrics.get("expectancy_r") or 0.0) > 0.0
        and (metrics.get("profit_factor") or 0.0) > 1.0
    )


def _scenario_summary(
    scenario: NeighborhoodScenario,
    result: dict[str, Any],
    center_result: dict[str, Any],
    center: dict[str, Any],
) -> dict[str, Any]:
    metrics = result["metrics"]
    center_metrics = center_result["metrics"]
    diagnostics = result["diagnostics"]
    center_diagnostics = center_result["diagnostics"]
    return {
        "name": scenario.name,
        "parameters": scenario.parameters(),
        "is_center": is_center(scenario, center),
        "is_axial_neighbor": is_axial_neighbor(scenario, center),
        "joint_positive": _joint_positive(metrics),
        "metrics": metrics,
        "diagnostics": diagnostics,
        "deltas_vs_center": {
            "total_return": _delta(metrics.get("total_return"), center_metrics.get("total_return")),
            "cagr": _delta(metrics.get("cagr"), center_metrics.get("cagr")),
            "max_drawdown": _delta(
                metrics.get("max_drawdown"), center_metrics.get("max_drawdown")
            ),
            "profit_factor": _delta(
                metrics.get("profit_factor"), center_metrics.get("profit_factor")
            ),
            "expectancy_r": _delta(
                metrics.get("expectancy_r"), center_metrics.get("expectancy_r")
            ),
            "trade_count": _delta(
                diagnostics.get("trade_count"), center_diagnostics.get("trade_count")
            ),
            "average_exposure": _delta(
                metrics.get("average_exposure"), center_metrics.get("average_exposure")
            ),
        },
    }


def evaluate_robustness(
    summaries: list[dict[str, Any]],
    criteria: dict[str, Any],
    reference_results: dict[str, Any],
) -> dict[str, Any]:
    centers = [summary for summary in summaries if summary["is_center"]]
    axial = [summary for summary in summaries if summary["is_axial_neighbor"]]
    if len(centers) != 1:
        raise RuntimeError("EXP-0005 must contain exactly one frozen-v1 center")
    if len(axial) != 6:
        raise RuntimeError("EXP-0005 must contain exactly six axial neighbors")

    joint_positive_count = sum(bool(summary["joint_positive"]) for summary in summaries)
    axial_joint_positive_count = sum(bool(summary["joint_positive"]) for summary in axial)
    missing_value = float(criteria["missing_expectancy_r_for_median"])
    expectancy_values = [
        missing_value
        if summary["metrics"].get("expectancy_r") is None
        else float(summary["metrics"]["expectancy_r"])
        for summary in summaries
    ]
    median_expectancy_r = float(median(expectancy_values))

    center = centers[0]
    center_metrics = center["metrics"]
    reference_metrics = reference_results["metrics"]
    tolerances = criteria["center_reference_tolerances"]
    reference_checks: dict[str, Any] = {}
    for key, tolerance in tolerances.items():
        center_value = center_metrics.get(key)
        reference_value = reference_metrics.get(key)
        difference = _delta(center_value, reference_value)
        within = difference is not None and abs(difference) <= float(tolerance)
        reference_checks[key] = {
            "center": center_value,
            "reference": reference_value,
            "delta": difference,
            "tolerance": tolerance,
            "within_tolerance": within,
        }
    center_reference_within_tolerance = all(
        check["within_tolerance"] for check in reference_checks.values()
    )

    criteria_status = {
        "joint_positive_scenarios": {
            "observed": joint_positive_count,
            "required": criteria["minimum_joint_positive_scenarios"],
            "passed": joint_positive_count >= criteria["minimum_joint_positive_scenarios"],
        },
        "joint_positive_axial_neighbors": {
            "observed": axial_joint_positive_count,
            "required": criteria["minimum_joint_positive_axial_neighbors"],
            "passed": axial_joint_positive_count
            >= criteria["minimum_joint_positive_axial_neighbors"],
        },
        "median_expectancy_r": {
            "observed": median_expectancy_r,
            "required": criteria["minimum_median_expectancy_r"],
            "missing_value": missing_value,
            "passed": median_expectancy_r >= criteria["minimum_median_expectancy_r"],
        },
        "center_reproduction": {
            "center_joint_positive": bool(center["joint_positive"]),
            "reference_within_tolerance": center_reference_within_tolerance,
            "checks": reference_checks,
            "passed": bool(center["joint_positive"]) and center_reference_within_tolerance,
        },
    }
    return {
        "scenario_count": len(summaries),
        "joint_positive_count": joint_positive_count,
        "axial_neighbor_count": len(axial),
        "axial_joint_positive_count": axial_joint_positive_count,
        "median_expectancy_r": median_expectancy_r,
        "criteria": criteria_status,
        "all_preregistered_criteria_passed": all(
            status["passed"] for status in criteria_status.values()
        ),
    }


def run_parameter_neighborhood(
    config_path: str | Path,
    output_dir: str | Path,
    *,
    downloader=download_daily,
    commit_sha: str | None = None,
) -> dict[str, Any]:
    config_path = Path(config_path)
    output_dir = Path(output_dir)
    config = load_parameter_neighborhood_config(config_path)
    experiment = config["experiment"]
    center = config["center"]
    scenarios = generate_scenarios(config)

    base_config_path = Path(experiment["base_experiment_config"])
    reference_results_path = Path(experiment["reference_results"])
    base_config = load_experiment_config(base_config_path)
    reference_results = json.loads(reference_results_path.read_text(encoding="utf-8"))
    base_portfolio = base_config["portfolio"]
    for key, value in center.items():
        if float(base_portfolio[key]) != float(value):
            raise RuntimeError(f"frozen EXP-0001 {key} does not match EXP-0005 center")

    output_dir.mkdir(parents=True, exist_ok=True)
    generated_dir = output_dir / "generated"
    scenarios_dir = output_dir / "scenarios"
    generated_dir.mkdir(parents=True, exist_ok=True)
    scenarios_dir.mkdir(parents=True, exist_ok=True)

    shared_downloader = SharedDownloadCache(downloader)
    producer_sha = commit_sha or _git_sha()
    scenario_results: dict[str, dict[str, Any]] = {}

    for scenario in scenarios:
        scenario_config = build_scenario_config(base_config, scenario, experiment)
        scenario_config_path = generated_dir / f"{scenario.name}.yaml"
        scenario_config_path.write_text(
            yaml.safe_dump(scenario_config, sort_keys=False), encoding="utf-8"
        )
        scenario_results[scenario.name] = run_experiment(
            scenario_config_path,
            scenarios_dir / scenario.name,
            downloader=shared_downloader,
            commit_sha=producer_sha,
        )

    if not _digests_match(scenario_results):
        raise RuntimeError("market-data source digests differ across parameter scenarios")

    center_scenario = next(scenario for scenario in scenarios if is_center(scenario, center))
    center_result = scenario_results[center_scenario.name]
    summaries = [
        _scenario_summary(
            scenario,
            scenario_results[scenario.name],
            center_result,
            center,
        )
        for scenario in scenarios
    ]
    robustness = evaluate_robustness(
        summaries,
        config["robustness_criteria"],
        reference_results,
    )

    reference_source = {
        symbol: str(record["sha256"])
        for symbol, record in reference_results.get("data_coverage", {}).get("source", {}).items()
    }
    current_source = _source_digests(center_result)
    results = _json_safe(
        {
            "experiment": {
                "id": experiment["id"],
                "name": experiment["name"],
                "research_stage": experiment["research_stage"],
                "historical_data_already_observed": True,
                "true_out_of_sample_claim": False,
                "code_commit_sha": producer_sha,
                "base_experiment_config": str(base_config_path),
                "base_experiment_config_sha256": _file_sha256(base_config_path),
                "reference_results": str(reference_results_path),
                "reference_results_sha256": _file_sha256(reference_results_path),
                "neighborhood_config_sha256": _file_sha256(config_path),
            },
            "runtime": center_result["runtime"],
            "data_consistency": {
                "identical_source_digests_across_scenarios": True,
                "shared_provider_download_count": shared_downloader.download_count,
                "source": center_result["data_coverage"]["source"],
                "source_digests_match_EXP_0001_reference": current_source == reference_source,
                "changed_source_symbols_vs_EXP_0001": sorted(
                    symbol
                    for symbol in set(current_source) | set(reference_source)
                    if current_source.get(symbol) != reference_source.get(symbol)
                ),
            },
            "center": center,
            "preregistered_parameters": config["parameters"],
            "preregistered_criteria": config["robustness_criteria"],
            "scenarios": summaries,
            "robustness": robustness,
        }
    )

    (output_dir / "results.json").write_text(
        json.dumps(results, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    (output_dir / "resolved-config.yaml").write_text(
        yaml.safe_dump(config, sort_keys=False), encoding="utf-8"
    )

    rows = []
    for summary in summaries:
        metrics = summary["metrics"]
        diagnostics = summary["diagnostics"]
        rows.append(
            {
                "scenario": summary["name"],
                **summary["parameters"],
                "is_center": summary["is_center"],
                "is_axial_neighbor": summary["is_axial_neighbor"],
                "joint_positive": summary["joint_positive"],
                "trade_count": diagnostics.get("trade_count"),
                "total_return": metrics.get("total_return"),
                "cagr": metrics.get("cagr"),
                "max_drawdown": metrics.get("max_drawdown"),
                "profit_factor": metrics.get("profit_factor"),
                "expectancy_r": metrics.get("expectancy_r"),
                "average_exposure": metrics.get("average_exposure"),
                "total_execution_cost": diagnostics.get("total_execution_cost"),
            }
        )
    pd.DataFrame(rows).to_csv(output_dir / "scenario-comparison.csv", index=False)

    notes = [
        f"# {experiment['id']} — Generated Parameter-Neighborhood Summary",
        "",
        "This file is machine-generated factual output. Research interpretation is pending review.",
        "",
        f"- Code SHA: `{producer_sha}`",
        f"- Scenarios: {robustness['scenario_count']}",
        f"- Joint-positive scenarios: {robustness['joint_positive_count']} / 27",
        (
            "- Joint-positive axial neighbors: "
            f"{robustness['axial_joint_positive_count']} / 6"
        ),
        f"- Median expectancy: {robustness['median_expectancy_r']}",
        (
            "- All preregistered criteria passed: "
            f"{robustness['all_preregistered_criteria_passed']}"
        ),
        f"- Shared provider downloads: {shared_downloader.download_count}",
        "- True out-of-sample claim: false",
        "- Historical winner selection performed: no",
        "",
        "## Interpretation status",
        "",
        "Pending formal artifact inspection. EXP-0005 must not be used to replace frozen v1 parameters.",
        "",
    ]
    (output_dir / "notes.md").write_text("\n".join(notes), encoding="utf-8")
    return results
