from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import subprocess
import zipfile
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from importlib.metadata import version
from io import BytesIO
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .data import REQUIRED_COLUMNS, download_daily
from .scanner import ScanResult, load_universe, required_symbols, scan_frames


Downloader = Callable[[str, str, str | None], pd.DataFrame]
SCHEMA_VERSION = 1
ARTIFACT_ID = "daily-scan-history"
WARMUP_START = "2015-01-01"
DEFAULT_CONFIG_PATH = Path("config/universe.yaml")
_ARCHIVE_RE = re.compile(r"^daily-scan-history-(\d{4}-\d{2}-\d{2})-([0-9a-f]{64})\.zip$")


@dataclass(frozen=True)
class DailyScanCapture:
    observation_date: date
    snapshot_dir: Path
    archive_path: Path
    archive_sha256: str
    manifest: dict[str, Any]


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _file_sha256(path: str | Path) -> str:
    return _sha256_bytes(Path(path).read_bytes())


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _package_version(name: str) -> str:
    try:
        return version(name)
    except Exception:
        return "unknown"


def _safe_symbol_filename(symbol: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", symbol).strip("._")
    if not safe:
        raise ValueError(f"cannot create source filename for symbol {symbol!r}")
    return f"{safe}.csv"


def _prepare_source_frame(symbol: str, raw: pd.DataFrame, observation_date: date) -> pd.DataFrame:
    if raw.empty:
        raise RuntimeError(f"no data returned for required scan symbol {symbol}")
    missing = set(REQUIRED_COLUMNS).difference(raw.columns)
    if missing:
        raise RuntimeError(f"{symbol}: missing columns {sorted(missing)}")
    if not isinstance(raw.index, pd.DatetimeIndex):
        raise RuntimeError(f"{symbol}: source index must be a DatetimeIndex")

    frame = raw[REQUIRED_COLUMNS].copy().sort_index()
    index = pd.DatetimeIndex(frame.index)
    if index.tz is not None:
        index = index.tz_localize(None)
    frame.index = index.normalize()
    if not frame.index.is_unique:
        raise RuntimeError(f"{symbol}: normalized daily source dates must be unique")

    frame = frame.loc[frame.index < pd.Timestamp(observation_date)].copy()
    if frame.empty:
        raise RuntimeError(f"{symbol}: no completed source rows before {observation_date}")

    values = frame[REQUIRED_COLUMNS].astype(float)
    if not np.isfinite(values.to_numpy()).all():
        raise RuntimeError(f"{symbol}: source contains non-finite OHLCV values")
    if (values[["Open", "High", "Low", "Close"]] <= 0).any().any():
        raise RuntimeError(f"{symbol}: source contains non-positive prices")
    if (values["Volume"] < 0).any():
        raise RuntimeError(f"{symbol}: source contains negative volume")
    return values


def _frame_csv_bytes(frame: pd.DataFrame) -> bytes:
    return frame.to_csv(
        index=True,
        index_label="Date",
        float_format="%.12g",
        date_format="%Y-%m-%d",
        lineterminator="\n",
    ).encode("utf-8")


def _scan_rows(results: list[ScanResult]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for result in results:
        row = {
            "symbol": result.symbol,
            "asset_class": result.asset_class,
            "score": result.score,
            "signal": result.signal,
            "close": result.close,
            "atr14": result.atr14,
            "breakdown": asdict(result.breakdown),
        }
        if not np.isfinite([result.close, result.atr14]).all():
            raise RuntimeError(f"{result.symbol}: scan result contains non-finite values")
        rows.append(row)
    return rows


def _results_json_bytes(rows: list[dict[str, Any]]) -> bytes:
    return (json.dumps(rows, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")


def _results_csv_bytes(rows: list[dict[str, Any]]) -> bytes:
    flat_rows = []
    for row in rows:
        flat_rows.append(
            {
                "symbol": row["symbol"],
                "asset_class": row["asset_class"],
                "score": row["score"],
                "signal": row["signal"],
                "close": row["close"],
                "atr14": row["atr14"],
                **row["breakdown"],
            }
        )
    frame = pd.DataFrame(flat_rows)
    return frame.to_csv(index=False, float_format="%.12g", lineterminator="\n").encode("utf-8")


def _write_deterministic_zip(snapshot_dir: Path, archive_path: Path) -> None:
    with zipfile.ZipFile(
        archive_path,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for path in sorted(item for item in snapshot_dir.rglob("*") if item.is_file()):
            relative = path.relative_to(snapshot_dir).as_posix()
            info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes(), compresslevel=9)


def capture_daily_scan(
    output_dir: str | Path,
    *,
    config_path: str | Path = DEFAULT_CONFIG_PATH,
    downloader: Downloader = download_daily,
    recorded_at: datetime | None = None,
    commit_sha: str | None = None,
) -> DailyScanCapture:
    """Persist the scanner observation visible at the current UTC information boundary."""
    now = recorded_at or datetime.now(UTC)
    if now.tzinfo is None:
        raise ValueError("recorded_at must be timezone-aware")
    now = now.astimezone(UTC)
    observation_date = now.date()

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    existing = list(output_dir.glob(f"{ARTIFACT_ID}-{observation_date}-*.zip"))
    if existing:
        raise FileExistsError(f"archive already exists for {observation_date}")

    snapshot_dir = output_dir / observation_date.isoformat()
    if snapshot_dir.exists():
        raise FileExistsError(f"snapshot directory already exists for {observation_date}")
    source_dir = snapshot_dir / "source"
    config_dir = snapshot_dir / "config"
    source_dir.mkdir(parents=True, exist_ok=False)
    config_dir.mkdir(parents=True, exist_ok=False)

    config_path = Path(config_path)
    config_bytes = config_path.read_bytes()
    config = load_universe(config_path)
    stored_config = config_dir / "universe.yaml"
    stored_config.write_bytes(config_bytes)

    symbols = required_symbols(config)
    cutoff = observation_date.isoformat()
    frames: dict[str, pd.DataFrame] = {}
    source_records: dict[str, dict[str, Any]] = {}
    for symbol in symbols:
        raw = downloader(symbol, WARMUP_START, cutoff)
        frame = _prepare_source_frame(symbol, raw, observation_date)
        frames[symbol] = frame
        filename = _safe_symbol_filename(symbol)
        relative_path = f"source/{filename}"
        payload = _frame_csv_bytes(frame)
        (source_dir / filename).write_bytes(payload)
        source_records[symbol] = {
            "path": relative_path,
            "sha256": _sha256_bytes(payload),
            "rows": int(len(frame)),
            "first_observation": frame.index[0].date().isoformat(),
            "last_observation": frame.index[-1].date().isoformat(),
        }

    results = scan_frames(config, frames)
    rows = _scan_rows(results)
    json_payload = _results_json_bytes(rows)
    csv_payload = _results_csv_bytes(rows)
    (snapshot_dir / "scan-results.json").write_bytes(json_payload)
    (snapshot_dir / "scan-results.csv").write_bytes(csv_payload)

    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "artifact_id": ARTIFACT_ID,
        "capture": {
            "recorded_at_utc": now.isoformat().replace("+00:00", "Z"),
            "observation_date": observation_date.isoformat(),
            "data_cutoff_exclusive": observation_date.isoformat(),
            "information_rule": "source rows must be strictly before observation_date",
            "warmup_start": WARMUP_START,
            "recorder_code_sha": commit_sha or _git_sha(),
            "provider": "yfinance",
        },
        "universe": {
            "config_path": "config/universe.yaml",
            "config_sha256": _sha256_bytes(config_bytes),
            "asset_count": len(config["assets"]),
            "required_symbols": symbols,
        },
        "runtime": {
            "python": platform.python_version(),
            "numpy": _package_version("numpy"),
            "pandas": _package_version("pandas"),
            "PyYAML": _package_version("PyYAML"),
            "yfinance": _package_version("yfinance"),
        },
        "workflow": {
            "repository": os.environ.get("GITHUB_REPOSITORY"),
            "run_id": os.environ.get("GITHUB_RUN_ID"),
            "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
        },
        "source": source_records,
        "outputs": {
            "json": {
                "path": "scan-results.json",
                "sha256": _sha256_bytes(json_payload),
                "rows": len(rows),
            },
            "csv": {
                "path": "scan-results.csv",
                "sha256": _sha256_bytes(csv_payload),
                "rows": len(rows),
            },
        },
        "research_integrity": {
            "historical_backfill_supported": False,
            "validation_evidence": False,
            "holdout_substitution_allowed": False,
            "strategy_parameters_modified": False,
        },
    }
    (snapshot_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )

    temporary_archive = output_dir / f"{ARTIFACT_ID}-{observation_date}.zip.tmp"
    _write_deterministic_zip(snapshot_dir, temporary_archive)
    archive_sha256 = _file_sha256(temporary_archive)
    archive_path = output_dir / f"{ARTIFACT_ID}-{observation_date}-{archive_sha256}.zip"
    temporary_archive.replace(archive_path)

    return DailyScanCapture(
        observation_date=observation_date,
        snapshot_dir=snapshot_dir,
        archive_path=archive_path,
        archive_sha256=archive_sha256,
        manifest=manifest,
    )


def verify_daily_scan_archive(path: str | Path) -> dict[str, Any]:
    """Verify a daily scanner archive's filename, manifest, sources, config, and outputs."""
    path = Path(path)
    match = _ARCHIVE_RE.match(path.name)
    if match is None:
        raise ValueError("daily scan archive filename does not match the required digest format")
    filename_date, filename_sha = match.groups()
    if _file_sha256(path) != filename_sha:
        raise RuntimeError("daily scan archive SHA-256 does not match its filename")

    with zipfile.ZipFile(path, "r") as archive:
        names = set(archive.namelist())
        if "manifest.json" not in names:
            raise RuntimeError("daily scan archive is missing manifest.json")
        manifest = json.loads(archive.read("manifest.json"))
        if manifest.get("schema_version") != SCHEMA_VERSION:
            raise RuntimeError("unsupported daily scan snapshot schema")
        if manifest.get("artifact_id") != ARTIFACT_ID:
            raise RuntimeError("daily scan artifact id mismatch")

        capture = manifest.get("capture", {})
        observation_date = capture.get("observation_date")
        if observation_date != filename_date:
            raise RuntimeError("manifest observation date does not match archive filename")
        if capture.get("data_cutoff_exclusive") != observation_date:
            raise RuntimeError("manifest cutoff must equal the observation date")
        cutoff = pd.Timestamp(observation_date)

        universe = manifest.get("universe")
        if not isinstance(universe, dict):
            raise RuntimeError("daily scan manifest has no universe record")
        config_path = universe.get("config_path")
        if config_path not in names:
            raise RuntimeError("daily scan archive is missing captured universe config")
        if _sha256_bytes(archive.read(config_path)) != universe.get("config_sha256"):
            raise RuntimeError("daily scan universe config SHA-256 mismatch")
        required = universe.get("required_symbols")
        if not isinstance(required, list) or len(required) != len(set(required)):
            raise RuntimeError("daily scan required-symbol set is invalid")

        source = manifest.get("source")
        if not isinstance(source, dict) or set(source) != set(required):
            raise RuntimeError("daily scan source set differs from required symbols")
        for symbol, record in source.items():
            relative = record.get("path")
            if relative not in names:
                raise RuntimeError(f"daily scan archive is missing source file for {symbol}")
            payload = archive.read(relative)
            if _sha256_bytes(payload) != record.get("sha256"):
                raise RuntimeError(f"source SHA-256 mismatch for {symbol}")
            frame = pd.read_csv(BytesIO(payload), parse_dates=["Date"], index_col="Date")
            if list(frame.columns) != REQUIRED_COLUMNS:
                raise RuntimeError(f"source schema mismatch for {symbol}")
            if frame.empty or pd.Timestamp(frame.index.max()) >= cutoff:
                raise RuntimeError(f"source cutoff violation for {symbol}")
            if len(frame) != int(record.get("rows", -1)):
                raise RuntimeError(f"source row-count mismatch for {symbol}")
            if frame.index[0].date().isoformat() != record.get("first_observation"):
                raise RuntimeError(f"source first-observation mismatch for {symbol}")
            if frame.index[-1].date().isoformat() != record.get("last_observation"):
                raise RuntimeError(f"source last-observation mismatch for {symbol}")

        outputs = manifest.get("outputs")
        if not isinstance(outputs, dict) or set(outputs) != {"json", "csv"}:
            raise RuntimeError("daily scan output records are invalid")
        row_counts: set[int] = set()
        for output_name, record in outputs.items():
            relative = record.get("path")
            if relative not in names:
                raise RuntimeError(f"daily scan archive is missing {output_name} output")
            payload = archive.read(relative)
            if _sha256_bytes(payload) != record.get("sha256"):
                raise RuntimeError(f"daily scan {output_name} SHA-256 mismatch")
            row_counts.add(int(record.get("rows", -1)))
        if row_counts != {int(universe.get("asset_count", -1))}:
            raise RuntimeError("daily scan output row count does not match configured assets")

        integrity = manifest.get("research_integrity", {})
        if integrity.get("historical_backfill_supported") is not False:
            raise RuntimeError("daily scan history must not support historical backfill")
        if integrity.get("validation_evidence") is not False:
            raise RuntimeError("daily scan history must not be marked as validation evidence")
        if integrity.get("holdout_substitution_allowed") is not False:
            raise RuntimeError("daily scan history must not substitute for holdout evidence")

    return manifest
