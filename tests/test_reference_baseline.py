from pathlib import Path

import pandas as pd
import pytest

from swing_trader.reference_baseline import load_reference_baseline_config, run_reference_baseline


def _frame(open_price: float, close_price: float) -> pd.DataFrame:
    return pd.DataFrame(
        {"Open": [open_price, open_price], "High": [open_price, close_price], "Low": [open_price, close_price], "Close": [open_price, close_price], "Volume": [1.0, 1.0]},
        index=pd.to_datetime(["2021-01-01", "2021-01-02"]),
    )


def test_reference_baseline_applies_costs_and_uses_one_download_per_symbol(tmp_path: Path) -> None:
    base = tmp_path / "base.yaml"
    base.write_text("""experiment:\n  id: EXP-TEST\n  name: test\n  symbols: [BTC-USD, SOL-USD]\n  warmup_start: 2020-01-01\n  evaluation_start: 2021-01-01\n  evaluation_end: 2021-01-03\n  universe_config: config/universe.yaml\n  cost_config: config/execution-costs.yaml\nportfolio:\n  initial_equity: 1000\n""", encoding="utf-8")
    config = tmp_path / "reference.yaml"
    config.write_text(f"experiment:\n  id: REF-TEST\n  base_experiment_config: {base}\nweights: equal\n", encoding="utf-8")
    calls: list[str] = []

    def downloader(symbol: str, start: str, end: str | None) -> pd.DataFrame:
        calls.append(symbol)
        return _frame(100.0, 110.0)

    results = run_reference_baseline(config, tmp_path / "out", downloader=downloader, commit_sha="test")

    assert calls == ["BTC-USD", "SOL-USD"]
    assert results["diagnostics"]["shared_provider_download_count"] == 2
    assert results["metrics"]["end_equity"] < 1100.0
    assert results["positions"][0]["entry_date"] == "2021-01-01"
    assert (tmp_path / "out" / "equity.csv").exists()


def test_reference_config_rejects_invalid_fixed_weights(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text("""experiment:\n  id: REF\n  base_experiment_config: base.yaml\nweights:\n  BTC-USD: 0.8\n  SOL-USD: 0.1\n""", encoding="utf-8")
    with pytest.raises(ValueError, match="sum"):
        load_reference_baseline_config(path)
