from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
import yaml

import swing_trader.universe_breadth as universe_breadth
from swing_trader.experiment import load_experiment_config
from swing_trader.universe_breadth import (
    aggregate_asset_classes,
    aggregate_symbol_contributions,
    build_path_config,
    evaluate_breadth,
    load_universe_breadth_config,
    run_universe_breadth,
)


CONFIG_PATH = Path("experiments/EXP-0006-configured-universe-breadth/config.yaml")
CONTROL = ["BTC-USD", "SOL-USD", "META", "NVDA"]
EXPANDED = [
    "BTC-USD",
    "ETH-USD",
    "SOL-USD",
    "META",
    "NVDA",
    "MSFT",
    "AAPL",
    "AMZN",
    "GOOGL",
    "AVGO",
    "TSLA",
]
ADDED = ["ETH-USD", "MSFT", "AAPL", "AMZN", "GOOGL", "AVGO", "TSLA"]


def test_exp0006_config_is_strictly_preregistered() -> None:
    config = load_universe_breadth_config(CONFIG_PATH)

    assert config["control_symbols"] == CONTROL
    assert config["expanded_symbols"] == EXPANDED
    assert config["added_symbols"] == ADDED
    criteria = config["breadth_criteria"]
    assert criteria["minimum_positive_symbol_contributors"] == 4
    assert criteria["minimum_positive_added_symbol_contributors"] == 2
    assert criteria["maximum_largest_positive_contributor_share"] == 0.60


def test_exp0006_rejects_posthoc_universe_or_threshold_changes(tmp_path: Path) -> None:
    payload = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    payload["expanded_symbols"] = list(reversed(payload["expanded_symbols"]))
    changed_universe = tmp_path / "changed-universe.yaml"
    changed_universe.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    with pytest.raises(ValueError, match="expanded symbols"):
        load_universe_breadth_config(changed_universe)

    payload = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    payload["breadth_criteria"]["minimum_positive_symbol_contributors"] = 3
    changed_criteria = tmp_path / "changed-criteria.yaml"
    changed_criteria.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    with pytest.raises(ValueError, match="breadth criteria"):
        load_universe_breadth_config(changed_criteria)


def test_generated_paths_preserve_frozen_experiment_and_portfolio_settings() -> None:
    config = load_universe_breadth_config(CONFIG_PATH)
    base = load_experiment_config(config["experiment"]["base_experiment_config"])

    control = build_path_config(base, path_name="control", symbols=CONTROL)
    expanded = build_path_config(base, path_name="expanded", symbols=EXPANDED)

    assert control["portfolio"] == base["portfolio"]
    assert expanded["portfolio"] == base["portfolio"]
    for generated, symbols in ((control, CONTROL), (expanded, EXPANDED)):
        assert generated["experiment"]["symbols"] == symbols
        for key in (
            "strategy_version",
            "data_provider",
            "universe_config",
            "cost_config",
            "warmup_start",
            "evaluation_start",
            "evaluation_end",
        ):
            assert generated["experiment"][key] == base["experiment"][key]


def _trade(symbol: str, pnl: float, r_multiple: float) -> dict:
    return {"symbol": symbol, "pnl": pnl, "r_multiple": r_multiple}


def test_symbol_and_asset_class_contributions_cover_zero_trade_symbols() -> None:
    trades = pd.DataFrame(
        [
            _trade("BTC-USD", 100.0, 2.0),
            _trade("BTC-USD", -25.0, -0.5),
            _trade("META", 50.0, 1.0),
        ]
    )
    asset_classes = {
        symbol: ("crypto" if "-USD" in symbol else "equity") for symbol in EXPANDED
    }
    rows = aggregate_symbol_contributions(trades, EXPANDED, asset_classes)
    by_symbol = {row["symbol"]: row for row in rows}

    assert by_symbol["BTC-USD"]["trade_count"] == 2
    assert by_symbol["BTC-USD"]["net_pnl"] == pytest.approx(75.0)
    assert by_symbol["META"]["positive_contributor"] is True
    assert by_symbol["AAPL"]["trade_count"] == 0
    assert by_symbol["AAPL"]["net_pnl"] == 0.0
    assert by_symbol["AAPL"]["expectancy_r"] is None

    classes = {row["asset_class"]: row for row in aggregate_asset_classes(rows)}
    assert classes["crypto"]["net_pnl"] == pytest.approx(75.0)
    assert classes["equity"]["net_pnl"] == pytest.approx(50.0)


def _symbol_rows() -> list[dict]:
    values = {
        "BTC-USD": 150.0,
        "ETH-USD": 90.0,
        "SOL-USD": -30.0,
        "META": 80.0,
        "NVDA": 60.0,
        "MSFT": 40.0,
        "AAPL": -10.0,
        "AMZN": 0.0,
        "GOOGL": -20.0,
        "AVGO": 30.0,
        "TSLA": -15.0,
    }
    return [
        {
            "symbol": symbol,
            "asset_class": "crypto" if "-USD" in symbol else "equity",
            "trade_count": 1,
            "net_pnl": pnl,
            "positive_contributor": pnl > 0,
        }
        for symbol, pnl in values.items()
    ]


def test_evaluate_breadth_applies_all_preregistered_criteria() -> None:
    config = load_universe_breadth_config(CONFIG_PATH)
    metrics = {
        "total_return": 0.25,
        "expectancy_r": 0.8,
        "profit_factor": 2.0,
        "cagr": 0.05,
        "max_drawdown": -0.04,
        "trade_count": 65,
    }

    result = evaluate_breadth(
        metrics,
        _symbol_rows(),
        ADDED,
        config["breadth_criteria"],
        metrics,
        dict(metrics),
    )

    assert result["added_symbols_aggregate_net_pnl"] > 0
    assert result["positive_symbol_count"] >= 4
    assert result["positive_added_symbol_count"] >= 2
    assert set(result["positive_asset_classes"]) == {"crypto", "equity"}
    assert result["largest_positive_contributor_share"] <= 0.60
    assert result["all_preregistered_criteria_passed"]


def test_concentration_failure_blocks_breadth_pass() -> None:
    config = load_universe_breadth_config(CONFIG_PATH)
    rows = _symbol_rows()
    for row in rows:
        row["net_pnl"] = 1.0
        row["positive_contributor"] = True
    rows[0]["net_pnl"] = 100.0
    metrics = {
        "total_return": 0.25,
        "expectancy_r": 0.8,
        "profit_factor": 2.0,
        "cagr": 0.05,
        "max_drawdown": -0.04,
        "trade_count": 65,
    }

    result = evaluate_breadth(
        metrics,
        rows,
        ADDED,
        config["breadth_criteria"],
        metrics,
        metrics,
    )

    assert not result["criteria"]["largest_positive_contributor_share"]["passed"]
    assert not result["all_preregistered_criteria_passed"]


def test_runner_reuses_one_twelve_symbol_snapshot_and_emits_no_selected_subset(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[tuple[str, str, str | None]] = []

    def downloader(symbol: str, start: str, end: str | None) -> pd.DataFrame:
        calls.append((symbol, start, end))
        return pd.DataFrame(
            {
                "Open": [100.0],
                "High": [101.0],
                "Low": [99.0],
                "Close": [100.5],
                "Volume": [1000.0],
            },
            index=pd.DatetimeIndex([pd.Timestamp("2026-01-01")]),
        )

    asset_classes = {
        "BTC-USD": "crypto",
        "ETH-USD": "crypto",
        "SOL-USD": "crypto",
        "META": "equity",
        "NVDA": "equity",
        "MSFT": "equity",
        "AAPL": "equity",
        "AMZN": "equity",
        "GOOGL": "equity",
        "AVGO": "equity",
        "TSLA": "equity",
    }
    contribution_pnl = {
        "BTC-USD": 120.0,
        "ETH-USD": 90.0,
        "SOL-USD": 30.0,
        "META": 100.0,
        "NVDA": 80.0,
        "MSFT": 60.0,
        "AAPL": 40.0,
        "AMZN": -10.0,
        "GOOGL": -10.0,
        "AVGO": 20.0,
        "TSLA": -10.0,
    }

    def fake_run_experiment(
        config_path: str | Path,
        output_dir: str | Path,
        *,
        downloader,
        commit_sha: str | None = None,
    ) -> dict:
        scenario = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
        symbols = scenario["experiment"]["symbols"]
        requested = list(symbols)
        if any(asset_classes[symbol] == "equity" for symbol in symbols):
            requested.append("QQQ")
        if any(asset_classes[symbol] == "crypto" for symbol in symbols):
            requested.append("BTC-USD")
        unique_requested: list[str] = []
        for symbol in requested:
            if symbol not in unique_requested:
                unique_requested.append(symbol)
        source = {}
        for symbol in unique_requested:
            frame = downloader(symbol, "2020-01-01", "2026-09-01")
            source[symbol] = {"sha256": f"sha-{symbol}", "rows": len(frame)}

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        trades = [
            {
                "symbol": symbol,
                "pnl": contribution_pnl[symbol],
                "r_multiple": 1.0 if contribution_pnl[symbol] > 0 else -0.5,
            }
            for symbol in symbols
        ]
        pd.DataFrame(trades).to_csv(output_dir / "trades.csv", index=False)

        is_control = symbols == CONTROL
        return {
            "data_coverage": {"source": source},
            "metrics": {
                "total_return": 0.3917035 if is_control else 0.50,
                "cagr": 0.0601156 if is_control else 0.07,
                "max_drawdown": -0.0424915 if is_control else -0.05,
                "profit_factor": 3.18 if is_control else 2.5,
                "expectancy_r": 1.0466 if is_control else 0.9,
                "trade_count": 65 if is_control else len(symbols),
            },
            "diagnostics": {
                "trade_count": 65 if is_control else len(symbols),
                "total_execution_cost": 80.0,
            },
        }

    monkeypatch.setattr(universe_breadth, "run_experiment", fake_run_experiment)
    results = run_universe_breadth(
        CONFIG_PATH,
        tmp_path / "output",
        downloader=downloader,
        commit_sha="test-sha",
    )

    assert len(calls) == 12
    assert results["data_consistency"]["shared_provider_download_count"] == 12
    assert results["data_consistency"]["identical_overlapping_source_digests"]
    assert results["control_symbols"] == CONTROL
    assert results["expanded_symbols"] == EXPANDED
    assert "selected_symbol_subset" not in results["experiment"]
    assert results["breadth"]["all_preregistered_criteria_passed"]
