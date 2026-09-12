from pathlib import Path

import pandas as pd
import pytest
import yaml

import swing_trader.parameter_neighborhood as parameter_neighborhood
from swing_trader.experiment import load_experiment_config
from swing_trader.parameter_neighborhood import (
    build_scenario_config,
    evaluate_robustness,
    generate_scenarios,
    is_axial_neighbor,
    is_center,
    load_parameter_neighborhood_config,
    run_parameter_neighborhood,
)


CONFIG_PATH = Path("experiments/EXP-0005-parameter-neighborhood/config.yaml")


def test_exp0005_config_is_strictly_preregistered() -> None:
    config = load_parameter_neighborhood_config(CONFIG_PATH)

    assert config["parameters"] == {
        "min_score": [65, 70, 75],
        "stop_atr": [1.5, 2.0, 2.5],
        "trail_atr": [2.0, 2.5, 3.0],
    }
    assert config["center"] == {"min_score": 70, "stop_atr": 2.0, "trail_atr": 2.5}
    assert config["robustness_criteria"]["minimum_joint_positive_scenarios"] == 18
    assert config["robustness_criteria"]["minimum_joint_positive_axial_neighbors"] == 5
    assert config["robustness_criteria"]["minimum_median_expectancy_r"] == 0.5
    assert config["robustness_criteria"]["missing_expectancy_r_for_median"] == 0.0


def test_exp0005_rejects_posthoc_threshold_changes(tmp_path: Path) -> None:
    payload = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    payload["robustness_criteria"]["minimum_joint_positive_scenarios"] = 17
    path = tmp_path / "changed.yaml"
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    with pytest.raises(ValueError, match="preregistered"):
        load_parameter_neighborhood_config(path)


def test_generate_scenarios_has_one_center_and_six_axial_neighbors() -> None:
    config = load_parameter_neighborhood_config(CONFIG_PATH)
    scenarios = generate_scenarios(config)

    assert len(scenarios) == 27
    assert len({scenario.name for scenario in scenarios}) == 27
    assert sum(is_center(scenario, config["center"]) for scenario in scenarios) == 1
    assert sum(is_axial_neighbor(scenario, config["center"]) for scenario in scenarios) == 6


def test_scenario_config_changes_only_preregistered_portfolio_fields() -> None:
    config = load_parameter_neighborhood_config(CONFIG_PATH)
    base = load_experiment_config(config["experiment"]["base_experiment_config"])
    scenario = generate_scenarios(config)[0]

    generated = build_scenario_config(base, scenario, config["experiment"])

    changed = {
        key
        for key in set(base["portfolio"]) | set(generated["portfolio"])
        if base["portfolio"].get(key) != generated["portfolio"].get(key)
    }
    assert changed == {"min_score", "stop_atr", "trail_atr"}
    for key in (
        "initial_equity",
        "risk_fraction",
        "max_open_risk_fraction",
        "max_positions",
        "max_position_fraction",
    ):
        assert generated["portfolio"][key] == base["portfolio"][key]
    assert generated["experiment"]["symbols"] == base["experiment"]["symbols"]
    assert generated["experiment"]["cost_config"] == base["experiment"]["cost_config"]


def _summary(name: str, *, center: bool = False, axial: bool = False, expectancy=0.8):
    metrics = {
        "total_return": 0.20,
        "cagr": 0.04,
        "max_drawdown": -0.05,
        "profit_factor": 2.0,
        "expectancy_r": expectancy,
        "trade_count": 65,
        "average_exposure": 0.06,
    }
    return {
        "name": name,
        "is_center": center,
        "is_axial_neighbor": axial,
        "joint_positive": expectancy is not None and expectancy > 0,
        "metrics": metrics,
        "diagnostics": {"trade_count": 65, "total_execution_cost": 80.0},
    }


def test_evaluate_robustness_applies_preregistered_criteria_and_missing_value() -> None:
    config = load_parameter_neighborhood_config(CONFIG_PATH)
    reference = json_reference = {
        "metrics": {
            "total_return": 0.20,
            "cagr": 0.04,
            "max_drawdown": -0.05,
            "profit_factor": 2.0,
            "expectancy_r": 0.8,
            "trade_count": 65,
        }
    }
    summaries = [_summary("center", center=True)]
    summaries.extend(_summary(f"axial-{index}", axial=True) for index in range(6))
    summaries.extend(_summary(f"other-{index}") for index in range(19))
    summaries.append(_summary("missing", expectancy=None))

    robustness = evaluate_robustness(
        summaries,
        config["robustness_criteria"],
        reference,
    )

    assert len(summaries) == 27
    assert robustness["joint_positive_count"] == 26
    assert robustness["axial_joint_positive_count"] == 6
    assert robustness["median_expectancy_r"] == pytest.approx(0.8)
    assert robustness["criteria"]["median_expectancy_r"]["missing_value"] == 0.0
    assert robustness["all_preregistered_criteria_passed"]
    assert json_reference is reference


def test_runner_reuses_one_snapshot_across_all_27_scenarios(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[tuple[str, str, str | None]] = []
    symbols = ["BTC-USD", "SOL-USD", "META", "NVDA", "QQQ"]

    def downloader(symbol: str, start: str, end: str | None) -> pd.DataFrame:
        calls.append((symbol, start, end))
        return pd.DataFrame(
            {"Close": [100.0]},
            index=pd.DatetimeIndex([pd.Timestamp("2026-01-01")]),
        )

    def fake_run_experiment(
        config_path: str | Path,
        output_dir: str | Path,
        *,
        downloader,
        commit_sha: str | None = None,
    ) -> dict:
        for symbol in symbols:
            downloader(symbol, "2020-01-01", "2026-09-01")
        scenario_config = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
        portfolio = scenario_config["portfolio"]
        return {
            "runtime": {"python": "test"},
            "data_coverage": {
                "source": {
                    symbol: {"sha256": f"sha-{symbol}", "rows": 1} for symbol in symbols
                }
            },
            "metrics": {
                "start_equity": 5000.0,
                "end_equity": 6958.5,
                "total_return": 0.3917035,
                "cagr": 0.0601156,
                "max_drawdown": -0.0424915,
                "sharpe": 1.27,
                "sortino": 2.15,
                "profit_factor": 3.18,
                "expectancy_r": 1.0466,
                "trade_count": 65,
                "average_exposure": 0.06,
                "scenario_score": portfolio["min_score"],
            },
            "diagnostics": {"trade_count": 65, "total_execution_cost": 86.0},
        }

    monkeypatch.setattr(parameter_neighborhood, "run_experiment", fake_run_experiment)
    results = run_parameter_neighborhood(
        CONFIG_PATH,
        tmp_path / "output",
        downloader=downloader,
        commit_sha="test-sha",
    )

    assert len(calls) == 5
    assert results["data_consistency"]["shared_provider_download_count"] == 5
    assert results["data_consistency"]["identical_source_digests_across_scenarios"]
    assert len(results["scenarios"]) == 27
    assert results["robustness"]["axial_neighbor_count"] == 6
    assert results["experiment"]["true_out_of_sample_claim"] is False
    assert "selected_parameter_set" not in results
