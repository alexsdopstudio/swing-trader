from pathlib import Path

import pandas as pd
import pytest

from swing_trader.cost_sensitivity import (
    SharedDownloadCache,
    _digests_match,
    _scenario_summary,
    load_cost_sensitivity_config,
)
from swing_trader.execution import ExecutionCostModel, scale_execution_cost_models


def test_scale_execution_cost_models_scales_every_component() -> None:
    models = {
        "equity": ExecutionCostModel(
            commission_bps=1.0,
            spread_bps=5.0,
            slippage_bps=5.0,
        ),
        "crypto": ExecutionCostModel(
            commission_bps=10.0,
            spread_bps=10.0,
            slippage_bps=10.0,
        ),
    }

    scaled = scale_execution_cost_models(models, 2.0)

    assert scaled["equity"] == ExecutionCostModel(2.0, 10.0, 10.0)
    assert scaled["crypto"] == ExecutionCostModel(20.0, 20.0, 20.0)
    assert models["equity"] == ExecutionCostModel(1.0, 5.0, 5.0)


def test_scale_execution_cost_models_rejects_negative_multiplier() -> None:
    with pytest.raises(ValueError, match="multiplier"):
        scale_execution_cost_models({"default": ExecutionCostModel()}, -1.0)


def test_shared_download_cache_downloads_each_request_once_and_returns_copy() -> None:
    calls: list[tuple[str, str, str | None]] = []

    def downloader(symbol: str, start: str, end: str | None) -> pd.DataFrame:
        calls.append((symbol, start, end))
        return pd.DataFrame(
            {"Close": [100.0, 101.0]},
            index=pd.date_range("2026-01-01", periods=2, freq="D"),
        )

    cache = SharedDownloadCache(downloader)
    first = cache("BTC-USD", "2026-01-01", "2026-01-03")
    second = cache("BTC-USD", "2026-01-01", "2026-01-03")
    first.iloc[0, 0] = 1.0

    assert calls == [("BTC-USD", "2026-01-01", "2026-01-03")]
    assert cache.download_count == 1
    assert second.iloc[0, 0] == 100.0


def test_digests_match_requires_identical_source_hashes() -> None:
    base = {
        "data_coverage": {
            "source": {
                "BTC-USD": {"sha256": "abc"},
                "QQQ": {"sha256": "def"},
            }
        }
    }
    same = {
        "data_coverage": {
            "source": {
                "BTC-USD": {"sha256": "abc"},
                "QQQ": {"sha256": "def"},
            }
        }
    }
    changed = {
        "data_coverage": {
            "source": {
                "BTC-USD": {"sha256": "changed"},
                "QQQ": {"sha256": "def"},
            }
        }
    }

    assert _digests_match({"low": base, "baseline": same})
    assert not _digests_match({"low": base, "baseline": changed})


def test_scenario_summary_reports_baseline_relative_deltas() -> None:
    baseline = {
        "portfolio": {"execution_costs": {"equity": {"commission_bps": 1.0}}},
        "metrics": {
            "end_equity": 6000.0,
            "cagr": 0.05,
            "profit_factor": 2.0,
            "expectancy_r": 0.5,
            "max_drawdown": -0.10,
        },
        "diagnostics": {"total_execution_cost": 50.0, "trade_count": 20},
    }
    high = {
        "portfolio": {"execution_costs": {"equity": {"commission_bps": 2.0}}},
        "metrics": {
            "end_equity": 5800.0,
            "cagr": 0.04,
            "profit_factor": 1.7,
            "expectancy_r": 0.4,
            "max_drawdown": -0.12,
        },
        "diagnostics": {"total_execution_cost": 90.0, "trade_count": 19},
    }

    summary = _scenario_summary("high", 2.0, high, baseline)

    assert summary["deltas_vs_baseline"]["end_equity"] == -200.0
    assert summary["deltas_vs_baseline"]["total_execution_cost"] == 40.0
    assert summary["deltas_vs_baseline"]["trade_count"] == -1.0


def test_load_cost_sensitivity_config_requires_one_x_baseline(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text(
        """
experiment:
  id: EXP-TEST
  base_experiment_config: experiments/EXP-0001-baseline/config.yaml
scenarios:
  low: 0.5
  baseline: 2.0
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="baseline"):
        load_cost_sensitivity_config(path)


def test_exp0002_config_is_versioned_and_well_formed() -> None:
    config = load_cost_sensitivity_config("experiments/EXP-0002-cost-sensitivity/config.yaml")

    assert config["experiment"]["id"] == "EXP-0002"
    assert config["scenarios"] == {
        "low": 0.5,
        "baseline": 1.0,
        "high": 2.0,
        "stress": 4.0,
    }
