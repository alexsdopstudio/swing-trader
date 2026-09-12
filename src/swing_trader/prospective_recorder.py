from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import subprocess
import zipfile
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime
from importlib.metadata import version
from io import BytesIO
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

from .data import REQUIRED_COLUMNS, download_daily


Downloader = Callable[[str, str, str | None], pd.DataFrame]
SCHEMA_VERSION = 1
DEFAULT_PROTOCOL_PATH = Path("experiments/PROSPECTIVE-v1-holdout/protocol.yaml")
DEFAULT_LOCK_PATH = Path("experiments/PROSPECTIVE-v1-holdout/protocol-lock.json")
_ARCHIVE_ID = "PROSPECTIVE-v1-holdout"
_ARCHIVE_RE = re.compile(r"^PROSPECTIVE-v1-holdout-(\d{4}-\d{2}-\d{2})-([0-9a-f]{64})\.zip$")


@dataclass(frozen=True)
class CaptureResult:
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


def load_locked_protocol(
    protocol_path: str | Path = DEFAULT_PROTOCOL_PATH,
    lock_path: str | Path = DEFAULT_LOCK_PATH,
) -> tuple[dict[str, Any], dict[str, Any], str]:
    """Load the registered holdout protocol and verify its immutable byte fingerprint."""
    protocol_path = Path(protocol_path)
    lock_path = Path(lock_path)
    protocol_bytes = protocol_path.read_bytes()
    protocol_sha256 = _sha256_bytes(protocol_bytes)
    protocol = yaml.safe_load(protocol_bytes) or {}
    lock = json.loads(lock_path.read_text(encoding="utf-8"))

    if not isinstance(protocol, dict) or not isinstance(lock, dict):
        raise ValueError("holdout protocol and lock must be mappings")
    if lock.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported holdout protocol lock schema")
    if protocol_sha256 != lock.get("protocol_sha256"):
        raise RuntimeError("registered holdout protocol bytes do not match protocol lock")

    metadata = protocol.get("protocol")
    holdout = protocol.get("holdout")
    universe = protocol.get("universe")
    integrity = protocol.get("research_integrity")
    if not all(isinstance(item, dict) for item in (metadata, holdout, universe, integrity)):
        raise ValueError("holdout protocol is missing required mappings")
    if metadata.get("id") != lock.get("protocol_id"):
        raise RuntimeError("protocol id does not match protocol lock")
    if metadata.get("frozen_source_commit") != lock.get("frozen_source_commit"):
        raise RuntimeError("frozen source commit does not match protocol lock")
    if metadata.get("status") != "preregistered":
        raise RuntimeError("holdout protocol must remain preregistered")
    if metadata.get("strategy_version") != "v1":
        raise RuntimeError("holdout recorder is locked to strategy v1")
    if integrity.get("interim_parameter_tuning_allowed") is not False:
        raise RuntimeError("holdout protocol must forbid interim parameter tuning")
    if integrity.get("interim_validation_claims_allowed") is not False:
        raise RuntimeError("holdout protocol must forbid interim validation claims")
    if integrity.get("provider_revisions_must_be_recorded") is not True:
        raise RuntimeError("holdout protocol must require provider revision recording")

    try:
        date.fromisoformat(str(holdout["evaluation_start"]))
        date.fromisoformat(str(lock["warmup_start"]))
    except (KeyError, ValueError) as exc:
        raise ValueError("holdout dates are malformed") from exc

    required_symbols(protocol)
    return protocol, lock, protocol_sha256


def required_symbols(protocol: dict[str, Any]) -> list[str]:
    """Return traded symbols and benchmarks once each, preserving protocol order."""
    universe = protocol.get("universe")
    if not isinstance(universe, dict):
        raise ValueError("holdout protocol must define universe")
    raw_symbols = universe.get("symbols")
    if not isinstance(raw_symbols, list) or not raw_symbols:
        raise ValueError("holdout universe symbols must be a non-empty list")
    candidates = [*raw_symbols, universe.get("benchmark_equities"), universe.get("benchmark_crypto")]
    symbols: list[str] = []
    for raw in candidates:
        if not isinstance(raw, str) or not raw.strip():
            raise ValueError("holdout symbols and benchmarks must be non-empty strings")
        symbol = raw.strip()
        if symbol not in symbols:
            symbols.append(symbol)
    return symbols


def _safe_symbol_filename(symbol: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", symbol).strip("._")
    if not safe:
        raise ValueError(f"cannot create source filename for symbol {symbol!r}")
    return f"{safe}.csv"


def _prepare_source_frame(
    symbol: str,
    raw: pd.DataFrame,
    observation_date: date,
) -> pd.DataFrame:
    if raw.empty:
        raise RuntimeError(f"no data returned for required holdout symbol {symbol}")
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

    cutoff = pd.Timestamp(observation_date)
    frame = frame.loc[frame.index < cutoff].copy()
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
    payload = frame.to_csv(
        index=True,
        index_label="Date",
        float_format="%.12g",
        date_format="%Y-%m-%d",
        lineterminator="\n",
    )
    return payload.encode("utf-8")


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


def capture_snapshot(
    output_dir: str | Path,
    *,
    protocol_path: str | Path = DEFAULT_PROTOCOL_PATH,
    lock_path: str | Path = DEFAULT_LOCK_PATH,
    downloader: Downloader = download_daily,
    recorded_at: datetime | None = None,
    commit_sha: str | None = None,
) -> CaptureResult | None:
    """Capture the provider state visible at the current UTC information boundary.

    Production callers do not supply an observation date. Tests may inject `recorded_at` so
    time-boundary behavior can be exercised deterministically.
    """
    now = recorded_at or datetime.now(UTC)
    if now.tzinfo is None:
        raise ValueError("recorded_at must be timezone-aware")
    now = now.astimezone(UTC)
    observation_date = now.date()

    protocol, lock, protocol_sha256 = load_locked_protocol(protocol_path, lock_path)
    evaluation_start = date.fromisoformat(str(protocol["holdout"]["evaluation_start"]))
    if observation_date <= evaluation_start:
        return None

    output_dir = Path(output_dir)
    snapshot_dir = output_dir / observation_date.isoformat()
    if snapshot_dir.exists():
        raise FileExistsError(f"snapshot directory already exists for {observation_date}")
    source_dir = snapshot_dir / "source"
    source_dir.mkdir(parents=True, exist_ok=False)

    source_records: dict[str, dict[str, Any]] = {}
    warmup_start = str(lock["warmup_start"])
    cutoff = observation_date.isoformat()
    for symbol in required_symbols(protocol):
        raw = downloader(symbol, warmup_start, cutoff)
        frame = _prepare_source_frame(symbol, raw, observation_date)
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

    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "protocol": {
            "id": protocol["protocol"]["id"],
            "protocol_sha256": protocol_sha256,
            "frozen_source_commit": lock["frozen_source_commit"],
            "strategy_version": protocol["protocol"]["strategy_version"],
        },
        "capture": {
            "recorded_at_utc": now.isoformat().replace("+00:00", "Z"),
            "observation_date": observation_date.isoformat(),
            "data_cutoff_exclusive": observation_date.isoformat(),
            "information_rule": "source rows must be strictly before observation_date",
            "recorder_code_sha": commit_sha or _git_sha(),
            "provider": "yfinance",
            "warmup_start": warmup_start,
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
        "required_symbols": required_symbols(protocol),
        "source": source_records,
        "research_integrity": {
            "interim_parameter_tuning_allowed": False,
            "interim_validation_claims_allowed": False,
            "historical_backfill_supported": False,
            "strategy_evaluation_included": False,
        },
    }
    manifest_path = snapshot_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )

    temporary_archive = output_dir / f"{_ARCHIVE_ID}-{observation_date}.zip.tmp"
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_deterministic_zip(snapshot_dir, temporary_archive)
    archive_sha256 = _file_sha256(temporary_archive)
    archive_path = output_dir / f"{_ARCHIVE_ID}-{observation_date}-{archive_sha256}.zip"
    if archive_path.exists():
        temporary_archive.unlink(missing_ok=True)
        raise FileExistsError(f"archive already exists for {observation_date}")
    temporary_archive.replace(archive_path)

    return CaptureResult(
        observation_date=observation_date,
        snapshot_dir=snapshot_dir,
        archive_path=archive_path,
        archive_sha256=archive_sha256,
        manifest=manifest,
    )


def verify_snapshot_archive(path: str | Path) -> dict[str, Any]:
    """Verify archive-name digest, manifest, source digests, and exclusive cutoff."""
    path = Path(path)
    match = _ARCHIVE_RE.match(path.name)
    if match is None:
        raise ValueError("holdout archive filename does not match the required digest format")
    filename_date, filename_sha = match.groups()
    actual_sha = _file_sha256(path)
    if actual_sha != filename_sha:
        raise RuntimeError("holdout archive SHA-256 does not match its filename")

    with zipfile.ZipFile(path, "r") as archive:
        names = set(archive.namelist())
        if "manifest.json" not in names:
            raise RuntimeError("holdout archive is missing manifest.json")
        manifest = json.loads(archive.read("manifest.json"))
        if manifest.get("schema_version") != SCHEMA_VERSION:
            raise RuntimeError("unsupported holdout snapshot schema")
        observation_date = manifest.get("capture", {}).get("observation_date")
        if observation_date != filename_date:
            raise RuntimeError("manifest observation date does not match archive filename")
        if manifest.get("capture", {}).get("data_cutoff_exclusive") != observation_date:
            raise RuntimeError("manifest cutoff must equal the observation date")
        cutoff = pd.Timestamp(observation_date)

        source = manifest.get("source")
        if not isinstance(source, dict) or not source:
            raise RuntimeError("holdout manifest has no source records")
        for symbol, record in source.items():
            relative = record.get("path")
            if relative not in names:
                raise RuntimeError(f"holdout archive is missing source file for {symbol}")
            payload = archive.read(relative)
            if _sha256_bytes(payload) != record.get("sha256"):
                raise RuntimeError(f"source SHA-256 mismatch for {symbol}")
            frame = pd.read_csv(BytesIO(payload), parse_dates=["Date"], index_col="Date")
            if frame.empty or pd.Timestamp(frame.index.max()) >= cutoff:
                raise RuntimeError(f"source cutoff violation for {symbol}")
            if len(frame) != int(record.get("rows", -1)):
                raise RuntimeError(f"source row-count mismatch for {symbol}")

    return manifest
