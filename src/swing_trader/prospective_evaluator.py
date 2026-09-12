from __future__ import annotations

import json
import math
import re
import zipfile
from dataclasses import asdict
from datetime import date, timedelta
from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd

from .execution import load_execution_cost_models
from .historical import historical_regime, historical_scores
from .indicators import add_indicators
from .portfolio import PortfolioBacktestConfig, PortfolioReplayBar, PortfolioReplaySession
from .prospective_recorder import (
    DEFAULT_LOCK_PATH,
    DEFAULT_PROTOCOL_PATH,
    load_locked_protocol,
    verify_snapshot_archive,
)


_ARCHIVE_RE = re.compile(
    r"^PROSPECTIVE-v1-holdout-(\d{4}-\d{2}-\d{2})-([0-9a-f]{64})\.zip$"
)
_EXPECTED_SYMBOLS = ["BTC-USD", "SOL-USD", "META", "NVDA"]
_EXPECTED_REQUIRED = ["BTC-USD", "SOL-USD", "META", "NVDA", "QQQ"]
_EXPECTED_BENCHMARKS = {"equity": "QQQ", "crypto": "BTC-USD"}
_EXPECTED_ASSET_CLASSES = {
    "BTC-USD": "crypto",
    "SOL-USD": "crypto",
    "META": "equity",
    "NVDA": "equity",
}
_EXPECTED_PORTFOLIO = {
    "initial_equity": 5000.0,
    "risk_fraction": 0.005,
    "max_open_risk_fraction": 0.02,
    "max_positions": 4,
    "max_position_fraction": 0.25,
    "min_score": 70,
    "stop_atr": 2.0,
    "trail_atr": 2.5,
}
_EXPECTED_COSTS = {
    "default": (0.0, 0.0, 0.0),
    "equity": (1.0, 5.0, 5.0),
    "crypto": (10.0, 10.0, 10.0),
}


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (pd.Timestamp, date)):
        return value.isoformat()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if hasattr(value, "item"):
        return _json_safe(value.item())
    return value


def _validate_frozen_protocol(
    protocol_path: str | Path,
    lock_path: str | Path,
) -> tuple[dict[str, Any], dict[str, Any], str, PortfolioBacktestConfig]:
    protocol, lock, protocol_sha = load_locked_protocol(protocol_path, lock_path)
    metadata = protocol["protocol"]
    universe = protocol["universe"]
    portfolio = protocol["portfolio"]
    execution = protocol["execution"]
    holdout = protocol["holdout"]

    expected_metadata = {
        "id": "PROSPECTIVE-v1-holdout",
        "status": "preregistered",
        "strategy_version": "v1",
        "base_experiment_config": "experiments/EXP-0001-baseline/config.yaml",
        "execution_cost_config": "config/execution-costs.yaml",
    }
    for key, expected in expected_metadata.items():
        if metadata.get(key) != expected:
            raise RuntimeError(f"prospective evaluator expected protocol {key}={expected!r}")

    if universe.get("symbols") != _EXPECTED_SYMBOLS:
        raise RuntimeError("prospective evaluator symbol set differs from frozen v1")
    if universe.get("benchmark_equities") != "QQQ":
        raise RuntimeError("prospective evaluator equity benchmark differs from frozen v1")
    if universe.get("benchmark_crypto") != "BTC-USD":
        raise RuntimeError("prospective evaluator crypto benchmark differs from frozen v1")

    for key, expected in _EXPECTED_PORTFOLIO.items():
        observed = portfolio.get(key)
        if isinstance(expected, float):
            if observed is None or float(observed) != expected:
                raise RuntimeError(f"prospective evaluator portfolio {key} differs from frozen v1")
        elif observed != expected:
            raise RuntimeError(f"prospective evaluator portfolio {key} differs from frozen v1")

    expected_execution = {
        "signal_timeframe": "daily",
        "signal_at": "completed_close",
        "entry_at": "next_asset_open",
        "direction": "long_only",
        "costs": "baseline",
    }
    for key, expected in expected_execution.items():
        if execution.get(key) != expected:
            raise RuntimeError(f"prospective evaluator execution {key} differs from frozen v1")

    if str(holdout.get("evaluation_start")) != "2026-09-14":
        raise RuntimeError("prospective evaluator start date differs from preregistration")
    if str(holdout.get("minimum_observation_end")) != "2028-09-14":
        raise RuntimeError("prospective evaluator validation horizon differs from preregistration")
    if int(holdout.get("minimum_closed_trades", -1)) != 30:
        raise RuntimeError("prospective evaluator trade gate differs from preregistration")

    cost_models = load_execution_cost_models(metadata["execution_cost_config"])
    for name, expected in _EXPECTED_COSTS.items():
        model = cost_models.get(name)
        if model is None:
            raise RuntimeError(f"prospective evaluator is missing frozen {name} cost model")
        observed = (model.commission_bps, model.spread_bps, model.slippage_bps)
        if observed != expected:
            raise RuntimeError(f"prospective evaluator {name} costs differ from frozen v1")

    config = PortfolioBacktestConfig(
        initial_equity=float(portfolio["initial_equity"]),
        risk_fraction=float(portfolio["risk_fraction"]),
        max_open_risk_fraction=float(portfolio["max_open_risk_fraction"]),
        max_positions=int(portfolio["max_positions"]),
        max_position_fraction=float(portfolio["max_position_fraction"]),
        min_score=int(portfolio["min_score"]),
        stop_atr=float(portfolio["stop_atr"]),
        trail_atr=float(portfolio["trail_atr"]),
        cost_models=cost_models,
    )
    return protocol, lock, protocol_sha, config


def _discover_archives(archive_dir: str | Path) -> dict[date, Path]:
    archive_dir = Path(archive_dir)
    if not archive_dir.exists():
        raise FileNotFoundError(f"archive directory does not exist: {archive_dir}")
    archives: dict[date, Path] = {}
    for path in sorted(archive_dir.glob("PROSPECTIVE-v1-holdout-*.zip")):
        match = _ARCHIVE_RE.match(path.name)
        if match is None:
            continue
        observation_date = date.fromisoformat(match.group(1))
        if observation_date in archives:
            raise RuntimeError(f"duplicate prospective archive date: {observation_date}")
        archives[observation_date] = path
    return archives


def _read_sources(path: Path, manifest: dict[str, Any]) -> dict[str, pd.DataFrame]:
    source = manifest["source"]
    frames: dict[str, pd.DataFrame] = {}
    with zipfile.ZipFile(path, "r") as archive:
        for symbol in manifest["required_symbols"]:
            payload = archive.read(source[symbol]["path"])
            frame = pd.read_csv(BytesIO(payload), parse_dates=["Date"], index_col="Date")
            frame.index = pd.DatetimeIndex(frame.index).tz_localize(None).normalize()
            frames[symbol] = frame
    return frames


def _replay_bars(
    frames: dict[str, pd.DataFrame],
    market_date: pd.Timestamp,
) -> dict[str, PortfolioReplayBar]:
    indicator_data = {symbol: add_indicators(frame) for symbol, frame in frames.items()}
    bars: dict[str, PortfolioReplayBar] = {}
    for symbol in _EXPECTED_SYMBOLS:
        data = indicator_data[symbol]
        if market_date not in data.index:
            continue
        asset_class = _EXPECTED_ASSET_CLASSES[symbol]
        benchmark_symbol = _EXPECTED_BENCHMARKS[asset_class]
        benchmark = indicator_data[benchmark_symbol]
        score_benchmark = None if symbol == benchmark_symbol else benchmark
        scores = historical_scores(data, score_benchmark)
        regime = historical_regime(benchmark, data.index)
        bars[symbol] = PortfolioReplayBar(
            symbol=symbol,
            row=data.loc[market_date],
            score=scores.loc[market_date],
            regime=bool(regime.loc[market_date]),
            asset_class=asset_class,
        )
    return bars


def _position_rows(session: PortfolioReplaySession) -> list[dict[str, Any]]:
    return [_json_safe(asdict(position)) for position in session.open_positions]


def _pending_rows(session: PortfolioReplaySession) -> list[dict[str, Any]]:
    return [_json_safe(asdict(signal)) for signal in session.pending_signals]


def _trade_rows(session: PortfolioReplaySession) -> list[dict[str, Any]]:
    return [_json_safe(asdict(trade)) for trade in session.trades]


def evaluate_holdout_archives(
    archive_dir: str | Path,
    output_dir: str | Path,
    *,
    protocol_path: str | Path = DEFAULT_PROTOCOL_PATH,
    lock_path: str | Path = DEFAULT_LOCK_PATH,
) -> dict[str, Any]:
    """Replay frozen v1 from canonical prospective archives without provider access."""
    protocol, lock, protocol_sha, config = _validate_frozen_protocol(protocol_path, lock_path)
    archives = _discover_archives(archive_dir)
    evaluation_start = date.fromisoformat(str(protocol["holdout"]["evaluation_start"]))
    first_observation = evaluation_start + timedelta(days=1)

    earlier = sorted(item for item in archives if item < first_observation)
    if earlier:
        raise RuntimeError(f"prospective archive precedes first active observation: {earlier[0]}")

    session = PortfolioReplaySession(config)
    processed_evidence: list[dict[str, Any]] = []
    daily_rows: list[dict[str, Any]] = []
    expected = first_observation
    first_gap: date | None = None

    if archives:
        last_available = max(archives)
        while expected <= last_available:
            path = archives.get(expected)
            if path is None:
                first_gap = expected
                break
            manifest = verify_snapshot_archive(path, lock_path=lock_path)
            if manifest.get("required_symbols") != _EXPECTED_REQUIRED:
                raise RuntimeError("prospective archive required-symbol order differs from frozen v1")

            market_date = pd.Timestamp(expected - timedelta(days=1))
            frames = _read_sources(path, manifest)
            bars = _replay_bars(frames, market_date)
            session.process_date(market_date, bars)
            result = session.result()
            daily_rows.append(
                {
                    "observation_date": expected.isoformat(),
                    "market_date": market_date.date().isoformat(),
                    "cash": session.cash,
                    "equity": float(result.equity_curve.loc[market_date]),
                    "exposure": float(result.exposure_curve.loc[market_date]),
                    "position_count": int(result.position_count_curve.loc[market_date]),
                    "closed_trade_count": len(session.trades),
                    "open_position_count": len(session.open_positions),
                    "pending_signal_count": len(session.pending_signals),
                }
            )
            processed_evidence.append(
                {
                    "observation_date": expected.isoformat(),
                    "market_date": market_date.date().isoformat(),
                    "archive": path.name,
                    "archive_sha256": path.stem.rsplit("-", 1)[-1],
                    "capture_recorded_at_utc": manifest["capture"]["recorded_at_utc"],
                    "source_sha256": {
                        symbol: manifest["source"][symbol]["sha256"]
                        for symbol in _EXPECTED_REQUIRED
                    },
                }
            )
            expected += timedelta(days=1)

    later_after_gap = (
        sorted(day.isoformat() for day in archives if first_gap is not None and day > first_gap)
        if first_gap is not None
        else []
    )
    result = session.result()
    output = _json_safe(
        {
            "protocol": {
                "id": protocol["protocol"]["id"],
                "protocol_sha256": protocol_sha,
                "frozen_source_commit": lock["frozen_source_commit"],
                "strategy_version": protocol["protocol"]["strategy_version"],
            },
            "research_integrity": {
                "interim_monitoring_only": True,
                "validation_claim": False,
                "parameter_tuning_allowed": False,
                "provider_downloads": 0,
                "historical_backfill_supported": False,
            },
            "evidence": {
                "expected_first_observation_date": first_observation.isoformat(),
                "available_archive_count": len(archives),
                "processed_archive_count": len(processed_evidence),
                "evidence_complete_through_available_range": first_gap is None,
                "first_missing_observation_date": None if first_gap is None else first_gap.isoformat(),
                "unprocessed_archives_after_gap": later_after_gap,
                "processed": processed_evidence,
            },
            "state": {
                "processed_through_observation_date": (
                    None if not processed_evidence else processed_evidence[-1]["observation_date"]
                ),
                "processed_through_market_date": None if not daily_rows else daily_rows[-1]["market_date"],
                "cash": session.cash,
                "equity": (
                    config.initial_equity if result.equity_curve.empty else float(result.equity_curve.iloc[-1])
                ),
                "open_positions": _position_rows(session),
                "pending_signals": _pending_rows(session),
                "closed_trade_count": len(session.trades),
            },
        }
    )

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "state.json").write_text(
        json.dumps(output, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    pd.DataFrame(_trade_rows(session)).to_csv(output_dir / "trades.csv", index=False)
    pd.DataFrame(daily_rows).to_csv(output_dir / "daily-state.csv", index=False)
    notes = [
        "# Prospective v1 holdout — Generated evaluator state",
        "",
        "This is read-only interim replay from captured evidence. It is not a validation claim",
        "and must not be used to tune frozen v1.",
        "",
        f"- Processed archives: {len(processed_evidence)}",
        f"- First missing observation: {output['evidence']['first_missing_observation_date']}",
        f"- Closed trades: {len(session.trades)}",
        f"- Open positions: {len(session.open_positions)}",
        f"- Pending signals: {len(session.pending_signals)}",
        "- Provider downloads: 0",
        "",
    ]
    (output_dir / "notes.md").write_text("\n".join(notes), encoding="utf-8")
    return output
