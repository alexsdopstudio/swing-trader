import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from swing_trader.experiment import _json_safe, _slice_evaluation, load_experiment_config


def test_slice_evaluation_excludes_warmup_bars() -> None:
    index = pd.date_range("2020-12-29", periods=6, freq="D")
    data = pd.DataFrame({"Close": range(6)}, index=index)
    scores = pd.Series(range(6), index=index)
    regime = pd.Series(True, index=index)

    sliced_data, sliced_scores, sliced_regime = _slice_evaluation(
        data,
        scores,
        regime,
        pd.Timestamp("2021-01-01"),
        pd.Timestamp("2021-01-03"),
    )

    assert list(sliced_data.index) == [pd.Timestamp("2021-01-01"), pd.Timestamp("2021-01-02")]
    assert list(sliced_scores.index) == list(sliced_data.index)
    assert list(sliced_regime.index) == list(sliced_data.index)


def test_json_safe_converts_non_finite_and_date_values() -> None:
    payload = _json_safe(
        {
            "nan": float("nan"),
            "positive_infinity": float("inf"),
            "negative_infinity": float("-inf"),
            "numpy_nan": np.float64(np.nan),
            "date": date(2026, 9, 1),
            "timestamp": pd.Timestamp("2026-09-01"),
            "value": 1.25,
        }
    )

    assert payload == {
        "nan": None,
        "positive_infinity": None,
        "negative_infinity": None,
        "numpy_nan": None,
        "date": "2026-09-01",
        "timestamp": "2026-09-01T00:00:00",
        "value": 1.25,
    }
    json.dumps(payload, allow_nan=False)


def test_load_experiment_config_validates_time_order(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text(
        """
experiment:
  id: EXP-TEST
  name: invalid-window
  symbols: [AAA]
  warmup_start: 2021-01-01
  evaluation_start: 2020-01-01
  evaluation_end: 2022-01-01
portfolio: {}
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="warmup_start"):
        load_experiment_config(path)


def test_load_exp0001_config_is_versioned_and_well_formed() -> None:
    config = load_experiment_config("experiments/EXP-0001-baseline/config.yaml")

    assert config["experiment"]["id"] == "EXP-0001"
    assert config["experiment"]["symbols"] == ["BTC-USD", "SOL-USD", "META", "NVDA"]
    assert config["portfolio"]["initial_equity"] == 5000.0
