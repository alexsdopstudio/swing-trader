from __future__ import annotations

import copy
import json
import math
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from .cost_sensitivity import SharedDownloadCache
from .data import download_daily
from .experiment import load_experiment_config, run_experiment
from .scanner import load_universe


_EXPECTED_CONTROL = ["BTC-USD", "SOL-USD", "META", "NVDA"]
_EXPECTED_EXPANDED = [
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
_EXPECTED_ADDED = ["ETH-USD", "MSFT", "AAPL", "AMZN", "GOOGL", "AVGO", "TSLA"]
_EXPECTED_CRITERIA = {
    "minimum_positive_symbol_contributors": 4,
    "minimum_positive_added_symbol_contributors": 2,
    "maximum_largest_positive_contributor_share": 0.60,
    "require_positive_added_symbols_aggregate_pnl": True,
    "require_positive_equity_contributor": True,
    "require_positive_crypto_contributor": True,
    "control_reference_tolerances": {
        "total_return": 0.01,
        "cagr": 0.0025,
        "max_drawdown": 0.005,
        "expectancy_r": 0.10,
        "trade_count": 2,
    },
}
_ALLOWED_EXPERIMENT_METADATA = frozenset({"id", "name", "research_stage"})


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


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


def _normalize_criteria(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("EXP-0006 breadth_criteria must be a mapping")
    tolerances = payload.get("control_reference_tolerances")
    if not isinstance(tolerances, dict):
        raise ValueError("control_reference_tolerances must be a mapping")
    for key in (
        "require_positive_added_symbols_aggregate_pnl",
        "require_positive_equity_contributor",
        "require_positive_crypto_contributor",
    ):
        if not isinstance(payload.get(key), bool):
            raise ValueError(f"EXP-0006 {key} must be boolean")
    try:
        return {
            "minimum_positive_symbol_contributors": int(
                payload["minimum_positive_symbol_contributors"]
            ),
            "minimum_positive_added_symbol_contributors": int(
                payload["minimum_positive_added_symbol_contributors"]
            ),
            "maximum_largest_positive_contributor_share": float(
                payload["maximum_largest_positive_contributor_share"]
            ),
            "require_positive_added_symbols_aggregate_pnl": bool(
                payload["require_positive_added_symbols_aggregate_pnl"]
            ),
            "require_positive_equity_contributor": bool(
                payload["require_positive_equity_contributor"]
            ),
            "require_positive_crypto_contributor": bool(
                payload["require_positive_crypto_contributor"]
            ),
            "control_reference_tolerances": {
                "total_return": float(tolerances["total_return"]),
                "cagr": float(tolerances["cagr"]),
                "max_drawdown": float(tolerances["max_drawdown"]),
                "expectancy_r": float(tolerances["expectancy_r"]),
                "trade_count": int(tolerances["trade_count"]),
            },
        }
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("EXP-0006 breadth criteria are malformed") from exc


def load_universe_breadth_config(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    if not isinstance(payload, dict):
        raise ValueError("universe breadth config must be a mapping")

    experiment = payload.get("experiment")
    if not isinstance(experiment, dict):
        raise ValueError("universe breadth config must define experiment")
    expected_paths = {
        "id": "EXP-0006",
        "base_experiment_config": "experiments/EXP-0001-baseline/config.yaml",
        "reference_results": "experiments/EXP-0001-baseline/results.json",
        "universe_config": "config/universe.yaml",
    }
    for key, expected in expected_paths.items():
        if experiment.get(key) != expected:
            raise ValueError(f"EXP-0006 {key} must remain {expected!r}")

    control = payload.get("control_symbols")
    expanded = payload.get("expanded_symbols")
    if control != _EXPECTED_CONTROL:
        raise ValueError("EXP-0006 control symbols changed from preregistration")
    if expanded != _EXPECTED_EXPANDED:
        raise ValueError("EXP-0006 expanded symbols changed from preregistration")

    universe = load_universe(experiment["universe_config"])
    configured = [item["symbol"] for item in universe.get("assets", [])]
    if configured != _EXPECTED_EXPANDED:
        raise ValueError("config/universe.yaml no longer matches preregistered EXP-0006 universe")

    criteria = _normalize_criteria(payload.get("breadth_criteria"))
    if criteria != _EXPECTED_CRITERIA:
        raise ValueError("EXP-0006 breadth criteria changed from preregistration")

    payload["breadth_criteria"] = criteria
    payload["added_symbols"] = _EXPECTED_ADDED.copy()
    return payload


def build_path_config(
    base: dict[str, Any],
    *,
    path_name: str,
    symbols: list[str],
) -> dict[str, Any]:
    generated = copy.deepcopy(base)
    experiment = generated["experiment"]
    original_experiment = base["experiment"]
    experiment["id"] = f"EXP-0006-{path_name}"
    experiment["name"] = f"configured-universe-breadth-{path_name}"
    experiment["research_stage"] = "retrospective-universe-breadth"
    experiment["symbols"] = symbols.copy()

    for key, value in original_experiment.items():
        if key in _ALLOWED_EXPERIMENT_METADATA or key == "symbols":
            continue
        if experiment.get(key) != value:
            raise AssertionError(f"generated path changed frozen experiment field {key}")
    if generated["portfolio"] != base["portfolio"]:
        raise AssertionError("generated path changed frozen portfolio configuration")
    return generated


def _source_digests(result: dict[str, Any]) -> dict[str, str]:
    return {
        symbol: str(record["sha256"])
        for symbol, record in result["data_coverage"]["source"].items()
    }


def _joint_positive(metrics: dict[str, Any]) -> bool:
    return bool(
        (metrics.get("total_return") or 0.0) > 0
        and (metrics.get("expectancy_r") or 0.0) > 0
        and (metrics.get("profit_factor") or 0.0) > 1
    )


def _profit_factor(values: pd.Series) -> float | None:
    positives = float(values[values > 0].sum())
    losses = float(values[values < 0].sum())
    if losses == 0:
        return None if positives == 0 else math.inf
    return positives / abs(losses)


def aggregate_symbol_contributions(
    trades: pd.DataFrame,
    symbols: list[str],
    asset_classes: dict[str, str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not trades.empty and "symbol" not in trades.columns:
        raise ValueError("trade ledger must contain symbol")
    for symbol in symbols:
        subset = trades.loc[trades["symbol"] == symbol] if not trades.empty else trades
        pnl = subset["pnl"].astype(float) if not subset.empty else pd.Series(dtype=float)
        r_values = (
            subset["r_multiple"].astype(float) if not subset.empty else pd.Series(dtype=float)
        )
        rows.append(
            {
                "symbol": symbol,
                "asset_class": asset_classes[symbol],
                "trade_count": int(len(subset)),
                "net_pnl": float(pnl.sum()) if not pnl.empty else 0.0,
                "gross_profit": float(pnl[pnl > 0].sum()) if not pnl.empty else 0.0,
                "gross_loss": float(pnl[pnl < 0].sum()) if not pnl.empty else 0.0,
                "profit_factor": _profit_factor(pnl),
                "expectancy_r": float(r_values.mean()) if not r_values.empty else None,
                "positive_contributor": bool(not pnl.empty and float(pnl.sum()) > 0),
            }
        )
    return rows


def aggregate_asset_classes(symbol_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, float | int]] = defaultdict(
        lambda: {"trade_count": 0, "net_pnl": 0.0, "positive_symbols": 0}
    )
    for row in symbol_rows:
        bucket = grouped[str(row["asset_class"])]
        bucket["trade_count"] = int(bucket["trade_count"]) + int(row["trade_count"])
        bucket["net_pnl"] = float(bucket["net_pnl"]) + float(row["net_pnl"])
        bucket["positive_symbols"] = int(bucket["positive_symbols"]) + int(
            bool(row["positive_contributor"])
        )
    return [
        {
            "asset_class": asset_class,
            "trade_count": int(values["trade_count"]),
            "net_pnl": float(values["net_pnl"]),
            "positive_symbols": int(values["positive_symbols"]),
        }
        for asset_class, values in sorted(grouped.items())
    ]


def evaluate_breadth(
    expanded_metrics: dict[str, Any],
    expanded_symbols: list[dict[str, Any]],
    added_symbols: list[str],
    criteria: dict[str, Any],
    control_metrics: dict[str, Any],
    reference_metrics: dict[str, Any],
) -> dict[str, Any]:
    by_symbol = {str(row["symbol"]): row for row in expanded_symbols}
    added_net_pnl = sum(float(by_symbol[symbol]["net_pnl"]) for symbol in added_symbols)
    positive = [row for row in expanded_symbols if float(row["net_pnl"]) > 0]
    positive_added = [row for row in positive if row["symbol"] in added_symbols]
    positive_total = sum(float(row["net_pnl"]) for row in positive)
    largest = max(positive, key=lambda row: float(row["net_pnl"])) if positive else None
    largest_share = (
        float(largest["net_pnl"]) / positive_total if largest and positive_total > 0 else None
    )
    positive_classes = {str(row["asset_class"]) for row in positive}

    tolerances = criteria["control_reference_tolerances"]
    control_deltas: dict[str, float | None] = {}
    control_reproduction = True
    for key in ("total_return", "cagr", "max_drawdown", "expectancy_r", "trade_count"):
        current = control_metrics.get(key)
        reference = reference_metrics.get(key)
        delta = None if current is None or reference is None else float(current) - float(reference)
        control_deltas[key] = delta
        if delta is None or abs(delta) > float(tolerances[key]):
            control_reproduction = False

    checks: dict[str, dict[str, Any]] = {
        "expanded_joint_positive": {
            "observed": _joint_positive(expanded_metrics),
            "required": True,
        },
        "added_symbols_aggregate_pnl": {
            "observed": added_net_pnl,
            "required": "> 0",
        },
        "positive_symbol_contributors": {
            "observed": len(positive),
            "required": criteria["minimum_positive_symbol_contributors"],
        },
        "positive_added_symbol_contributors": {
            "observed": len(positive_added),
            "required": criteria["minimum_positive_added_symbol_contributors"],
        },
        "positive_equity_contributor": {
            "observed": "equity" in positive_classes,
            "required": criteria["require_positive_equity_contributor"],
        },
        "positive_crypto_contributor": {
            "observed": "crypto" in positive_classes,
            "required": criteria["require_positive_crypto_contributor"],
        },
        "largest_positive_contributor_share": {
            "observed": largest_share,
            "required_maximum": criteria["maximum_largest_positive_contributor_share"],
            "symbol": None if largest is None else largest["symbol"],
        },
        "control_joint_positive": {
            "observed": _joint_positive(control_metrics),
            "required": True,
        },
        "control_reproduction": {
            "observed": control_reproduction,
            "required": True,
            "deltas": control_deltas,
            "tolerances": tolerances,
        },
    }
    passes = {
        "expanded_joint_positive": checks["expanded_joint_positive"]["observed"] is True,
        "added_symbols_aggregate_pnl": added_net_pnl > 0,
        "positive_symbol_contributors": len(positive)
        >= criteria["minimum_positive_symbol_contributors"],
        "positive_added_symbol_contributors": len(positive_added)
        >= criteria["minimum_positive_added_symbol_contributors"],
        "positive_equity_contributor": (
            ("equity" in positive_classes)
            if criteria["require_positive_equity_contributor"]
            else True
        ),
        "positive_crypto_contributor": (
            ("crypto" in positive_classes)
            if criteria["require_positive_crypto_contributor"]
            else True
        ),
        "largest_positive_contributor_share": (
            largest_share is not None
            and largest_share <= criteria["maximum_largest_positive_contributor_share"]
        ),
        "control_joint_positive": checks["control_joint_positive"]["observed"] is True,
        "control_reproduction": control_reproduction,
    }
    for name, passed in passes.items():
        checks[name]["passed"] = bool(passed)

    return {
        "added_symbols": added_symbols,
        "added_symbols_aggregate_net_pnl": added_net_pnl,
        "positive_symbol_count": len(positive),
        "positive_added_symbol_count": len(positive_added),
        "positive_asset_classes": sorted(positive_classes),
        "largest_positive_contributor": None if largest is None else largest["symbol"],
        "largest_positive_contributor_share": largest_share,
        "criteria": checks,
        "all_preregistered_criteria_passed": all(passes.values()),
    }


def run_universe_breadth(
    config_path: str | Path,
    output_dir: str | Path,
    *,
    downloader=download_daily,
    commit_sha: str | None = None,
) -> dict[str, Any]:
    config_path = Path(config_path)
    output_dir = Path(output_dir)
    study = load_universe_breadth_config(config_path)
    experiment = study["experiment"]
    base = load_experiment_config(experiment["base_experiment_config"])
    if base["experiment"]["symbols"] != study["control_symbols"]:
        raise RuntimeError("EXP-0001 symbols no longer match preregistered control")
    if base["experiment"].get("universe_config") != experiment["universe_config"]:
        raise RuntimeError("EXP-0001 universe config no longer matches EXP-0006 preregistration")

    reference = json.loads(Path(experiment["reference_results"]).read_text(encoding="utf-8"))
    universe = load_universe(experiment["universe_config"])
    asset_classes = {item["symbol"]: item["asset_class"] for item in universe["assets"]}

    output_dir.mkdir(parents=True, exist_ok=True)
    generated_dir = output_dir / "generated"
    paths_dir = output_dir / "paths"
    generated_dir.mkdir(parents=True, exist_ok=True)
    paths_dir.mkdir(parents=True, exist_ok=True)

    shared = SharedDownloadCache(downloader)
    producer_sha = commit_sha or _git_sha()
    path_results: dict[str, dict[str, Any]] = {}
    path_symbol_rows: dict[str, list[dict[str, Any]]] = {}

    for path_name, symbols in (
        ("control", study["control_symbols"]),
        ("expanded", study["expanded_symbols"]),
    ):
        generated = build_path_config(base, path_name=path_name, symbols=symbols)
        generated_path = generated_dir / f"{path_name}.yaml"
        generated_path.write_text(yaml.safe_dump(generated, sort_keys=False), encoding="utf-8")
        path_output = paths_dir / path_name
        result = run_experiment(
            generated_path,
            path_output,
            downloader=shared,
            commit_sha=producer_sha,
        )
        trades_path = path_output / "trades.csv"
        trades = pd.read_csv(trades_path) if trades_path.stat().st_size else pd.DataFrame()
        path_results[path_name] = result
        path_symbol_rows[path_name] = aggregate_symbol_contributions(
            trades, symbols, asset_classes
        )

    control_digests = _source_digests(path_results["control"])
    expanded_digests = _source_digests(path_results["expanded"])
    overlap = sorted(set(control_digests) & set(expanded_digests))
    overlap_match = all(control_digests[symbol] == expanded_digests[symbol] for symbol in overlap)
    if not overlap_match:
        raise RuntimeError("control and expanded paths did not share identical overlapping inputs")

    expected_download_count = len(
        set(
            study["expanded_symbols"]
            + [universe["benchmark_equities"], universe["benchmark_crypto"]]
        )
    )
    if shared.download_count != expected_download_count:
        raise RuntimeError(
            f"expected {expected_download_count} shared downloads, observed {shared.download_count}"
        )

    breadth = evaluate_breadth(
        path_results["expanded"]["metrics"],
        path_symbol_rows["expanded"],
        study["added_symbols"],
        study["breadth_criteria"],
        path_results["control"]["metrics"],
        reference["metrics"],
    )
    control_reference_digest_mismatches = sorted(
        symbol
        for symbol, digest in control_digests.items()
        if reference.get("data_coverage", {}).get("source", {}).get(symbol, {}).get("sha256")
        not in (None, digest)
    )

    result = _json_safe(
        {
            "experiment": {
                "id": "EXP-0006",
                "name": experiment.get("name", "configured-universe-breadth"),
                "research_stage": experiment.get(
                    "research_stage", "retrospective-universe-breadth"
                ),
                "code_commit_sha": producer_sha,
                "historical_data_already_observed": True,
                "true_out_of_sample_claim": False,
            },
            "control_symbols": study["control_symbols"],
            "expanded_symbols": study["expanded_symbols"],
            "added_symbols": study["added_symbols"],
            "preregistered_criteria": study["breadth_criteria"],
            "data_consistency": {
                "shared_provider_download_count": shared.download_count,
                "expected_provider_download_count": expected_download_count,
                "overlapping_symbols": overlap,
                "identical_overlapping_source_digests": overlap_match,
                "control_reference_source_digest_mismatches": (
                    control_reference_digest_mismatches
                ),
            },
            "paths": {
                name: {
                    "metrics": path_results[name]["metrics"],
                    "diagnostics": path_results[name]["diagnostics"],
                    "source_digests": _source_digests(path_results[name]),
                    "symbol_contributions": path_symbol_rows[name],
                    "asset_class_contributions": aggregate_asset_classes(
                        path_symbol_rows[name]
                    ),
                }
                for name in ("control", "expanded")
            },
            "breadth": breadth,
        }
    )

    (output_dir / "results.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    csv_rows = []
    for path_name in ("control", "expanded"):
        for row in path_symbol_rows[path_name]:
            csv_rows.append({"path": path_name, **row})
    pd.DataFrame(csv_rows).to_csv(output_dir / "symbol-contribution.csv", index=False)

    notes = [
        "# EXP-0006 — Generated Run Summary",
        "",
        "This file is machine-generated factual output. Research interpretation must be added only after review.",
        "",
        f"- Code SHA: `{producer_sha}`",
        f"- Control symbols: {', '.join(study['control_symbols'])}",
        f"- Expanded symbols: {', '.join(study['expanded_symbols'])}",
        f"- Shared provider downloads: {shared.download_count}",
        f"- Overlapping source digests identical: {overlap_match}",
        f"- Expanded total return: {path_results['expanded']['metrics'].get('total_return')}",
        f"- Expanded expectancy R: {path_results['expanded']['metrics'].get('expectancy_r')}",
        f"- Expanded profit factor: {path_results['expanded']['metrics'].get('profit_factor')}",
        f"- Added-symbol aggregate net PnL: {breadth['added_symbols_aggregate_net_pnl']}",
        f"- Positive symbol contributors: {breadth['positive_symbol_count']}",
        f"- Positive added-symbol contributors: {breadth['positive_added_symbol_count']}",
        f"- Largest positive contributor share: {breadth['largest_positive_contributor_share']}",
        f"- All preregistered criteria passed: {breadth['all_preregistered_criteria_passed']}",
        "",
        "## Interpretation status",
        "",
        "Pending formal inspection. EXP-0006 is retrospective and cannot validate v1.",
        "",
    ]
    (output_dir / "notes.md").write_text("\n".join(notes), encoding="utf-8")
    (output_dir / "resolved-config.yaml").write_text(
        yaml.safe_dump(study, sort_keys=False), encoding="utf-8"
    )
    return result
