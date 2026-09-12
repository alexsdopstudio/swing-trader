from pathlib import Path

import pandas as pd
import pytest
import yaml

from swing_trader.temporal_stability import (
    HistoricalSnapshot,
    aggregate_temporal_diagnostics,
    load_temporal_stability_config,
)


def _daily_frame(start: str = "2020-01-01", periods: int = 20) -> pd.DataFrame:
    index = pd.date_range(start, periods=periods, freq="D")
    return pd.DataFrame(
        {
            "Open": range(100, 100 + periods),
            "High": range(101, 101 + periods),
            "Low": range(99, 99 + periods),
            "Close": range(100, 100 + periods),
            "Volume": [1_000] * periods,
        },
        index=index,
    ).astype(float)


def test_historical_snapshot_downloads_once_per_symbol_and_serves_slices() -> None:
    calls: list[tuple[str, str, str | None]] = []

    def downloader(symbol: str, start: str, end: str | None) -> pd.DataFrame:
        calls.append((symbol, start, end))
        return _daily_frame(periods=10)

    snapshot = HistoricalSnapshot(
        ["BTC-USD", "QQQ"],
        "2020-01-01",
        "2020-01-11",
        downloader=downloader,
    )

    first = snapshot("BTC-USD", "2020-01-03", "2020-01-06")
    second = snapshot("BTC-USD", "2020-01-03", "2020-01-06")
    first.iloc[0, 0] = -1.0

    assert calls == [
        ("BTC-USD", "2020-01-01", "2020-01-11"),
        ("QQQ", "2020-01-01", "2020-01-11"),
    ]
    assert snapshot.download_count == 2
    assert list(second.index) == list(pd.date_range("2020-01-03", periods=3, freq="D"))
    assert second.iloc[0, 0] != -1.0


def test_historical_snapshot_rejects_slice_outside_registered_window() -> None:
    snapshot = HistoricalSnapshot(
        ["BTC-USD"],
        "2020-01-01",
        "2020-01-11",
        downloader=lambda *_: _daily_frame(periods=10),
    )

    with pytest.raises(RuntimeError, match="outside snapshot"):
        snapshot("BTC-USD", "2019-12-31", "2020-01-05")


def test_temporal_config_rejects_overlapping_folds(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text(
        """
experiment:
  id: EXP-TEST
  base_experiment_config: experiments/EXP-0001-baseline/config.yaml
  snapshot_start: 2020-01-01
  snapshot_end: 2024-01-01
folds:
  - name: first
    evaluation_start: 2021-01-01
    evaluation_end: 2022-06-01
  - name: second
    evaluation_start: 2022-01-01
    evaluation_end: 2023-01-01
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="non-overlapping"):
        load_temporal_stability_config(path)


def test_aggregate_temporal_diagnostics_reports_fold_stability() -> None:
    folds = [
        {
            "name": "a",
            "trade_count": 10,
            "expectancy_r": 0.5,
            "profit_factor": 2.0,
            "total_return": 0.10,
            "max_drawdown": -0.05,
        },
        {
            "name": "b",
            "trade_count": 5,
            "expectancy_r": -0.2,
            "profit_factor": 0.8,
            "total_return": -0.03,
            "max_drawdown": -0.08,
        },
        {
            "name": "c",
            "trade_count": 5,
            "expectancy_r": 0.3,
            "profit_factor": 1.4,
            "total_return": 0.04,
            "max_drawdown": -0.04,
        },
    ]

    result = aggregate_temporal_diagnostics(folds)

    assert result["fold_count"] == 3
    assert result["positive_expectancy_folds"] == 2
    assert result["profit_factor_above_one_folds"] == 2
    assert result["positive_return_folds"] == 2
    assert result["total_closed_trades_across_independent_folds"] == 20
    assert result["trade_count_weighted_expectancy_r"] == pytest.approx(0.275)
    assert result["minimum_expectancy_r"] == -0.2
    assert result["worst_fold_max_drawdown"] == -0.08


def test_exp0003_config_is_versioned_and_historical_only() -> None:
    config = load_temporal_stability_config(
        "experiments/EXP-0003-temporal-stability/config.yaml"
    )

    assert config["experiment"]["id"] == "EXP-0003"
    assert config["experiment"]["base_experiment_config"] == (
        "experiments/EXP-0001-baseline/config.yaml"
    )
    assert [fold["name"] for fold in config["folds"]] == [
        "2021",
        "2022",
        "2023",
        "2024",
        "2025",
        "2026-ytd",
    ]


def test_prospective_holdout_is_preregistered_before_start() -> None:
    path = Path("experiments/PROSPECTIVE-v1-holdout/protocol.yaml")
    protocol = yaml.safe_load(path.read_text(encoding="utf-8"))

    registered = pd.Timestamp(protocol["protocol"]["registered_on"])
    start = pd.Timestamp(protocol["holdout"]["evaluation_start"])
    minimum_end = pd.Timestamp(protocol["holdout"]["minimum_observation_end"])

    assert registered < start < minimum_end
    assert protocol["holdout"]["minimum_closed_trades"] == 30
    assert protocol["holdout"]["gate"] == "both_time_and_trade_count"
    assert protocol["research_integrity"]["interim_parameter_tuning_allowed"] is False
    assert protocol["research_integrity"]["interim_validation_claims_allowed"] is False
