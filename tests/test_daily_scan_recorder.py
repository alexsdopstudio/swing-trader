from __future__ import annotations

import hashlib
import shutil
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import pytest

from swing_trader.daily_scan_recorder import capture_daily_scan, verify_daily_scan_archive
from swing_trader.daily_scan_recorder_cli import build_parser
from swing_trader.scanner import load_universe, required_symbols, scan


def _source_frame() -> pd.DataFrame:
    index = pd.date_range("2025-11-01", periods=320, freq="D")
    closes = [100.0 + index_value * 0.4 for index_value in range(len(index))]
    return pd.DataFrame(
        {
            "Open": [value * 0.995 for value in closes],
            "High": [value * 1.01 for value in closes],
            "Low": [value * 0.99 for value in closes],
            "Close": closes,
            "Volume": [1000.0 + index_value for index_value in range(len(index))],
        },
        index=index,
    )


def _downloader(symbol: str, start: str, end: str | None) -> pd.DataFrame:
    return _source_frame()


def test_configured_scan_symbols_include_each_benchmark_once() -> None:
    config = load_universe("config/universe.yaml")
    symbols = required_symbols(config)

    assert len(config["assets"]) == 11
    assert len(symbols) == 12
    assert symbols.count("BTC-USD") == 1
    assert symbols[-1] == "QQQ"


def test_scanner_downloads_each_unique_symbol_once() -> None:
    calls: list[str] = []

    def downloader(symbol: str, start: str, end: str | None) -> pd.DataFrame:
        calls.append(symbol)
        return _source_frame()

    results = scan(downloader=downloader)

    assert len(results) == 11
    assert len(calls) == 12
    assert len(set(calls)) == 12
    assert calls.count("BTC-USD") == 1


def test_capture_uses_current_utc_date_as_exclusive_cutoff_and_records_outputs(
    tmp_path: Path,
) -> None:
    calls: list[tuple[str, str, str | None]] = []

    def downloader(symbol: str, start: str, end: str | None) -> pd.DataFrame:
        calls.append((symbol, start, end))
        return _source_frame()

    result = capture_daily_scan(
        tmp_path,
        downloader=downloader,
        recorded_at=datetime(2026, 9, 13, 2, 37, tzinfo=UTC),
        commit_sha="test-sha",
    )

    assert len(calls) == 12
    assert len({symbol for symbol, _, _ in calls}) == 12
    assert {start for _, start, _ in calls} == {"2015-01-01"}
    assert {end for _, _, end in calls} == {"2026-09-13"}
    assert result.manifest["capture"]["observation_date"] == "2026-09-13"
    assert result.manifest["capture"]["data_cutoff_exclusive"] == "2026-09-13"
    assert result.manifest["outputs"]["json"]["rows"] == 11
    assert result.manifest["outputs"]["csv"]["rows"] == 11
    assert result.manifest["research_integrity"]["historical_backfill_supported"] is False
    assert result.manifest["research_integrity"]["validation_evidence"] is False
    assert result.manifest["research_integrity"]["holdout_substitution_allowed"] is False

    for record in result.manifest["source"].values():
        assert record["last_observation"] == "2026-09-12"
        stored = pd.read_csv(result.snapshot_dir / record["path"], parse_dates=["Date"])
        assert stored["Date"].max() == pd.Timestamp("2026-09-12")

    verified = verify_daily_scan_archive(result.archive_path)
    assert verified["capture"]["observation_date"] == "2026-09-13"
    assert result.archive_path.name.endswith(f"-{result.archive_sha256}.zip")


def test_same_input_clock_and_code_produce_identical_archive_bytes(tmp_path: Path) -> None:
    recorded_at = datetime(2026, 9, 13, 2, 37, tzinfo=UTC)
    first = capture_daily_scan(
        tmp_path / "first",
        downloader=_downloader,
        recorded_at=recorded_at,
        commit_sha="test-sha",
    )
    second = capture_daily_scan(
        tmp_path / "second",
        downloader=_downloader,
        recorded_at=recorded_at,
        commit_sha="test-sha",
    )

    assert first.archive_sha256 == second.archive_sha256
    assert first.archive_path.read_bytes() == second.archive_path.read_bytes()


def test_same_date_capture_is_refused(tmp_path: Path) -> None:
    recorded_at = datetime(2026, 9, 13, 2, 37, tzinfo=UTC)
    capture_daily_scan(
        tmp_path,
        downloader=_downloader,
        recorded_at=recorded_at,
        commit_sha="test-sha",
    )

    with pytest.raises(FileExistsError, match="already exists"):
        capture_daily_scan(
            tmp_path,
            downloader=_downloader,
            recorded_at=recorded_at,
            commit_sha="test-sha",
        )


def test_verifier_rejects_archive_digest_filename_mismatch(tmp_path: Path) -> None:
    result = capture_daily_scan(
        tmp_path,
        downloader=_downloader,
        recorded_at=datetime(2026, 9, 13, 2, 37, tzinfo=UTC),
        commit_sha="test-sha",
    )
    wrong_name = tmp_path / f"daily-scan-history-2026-09-13-{'0' * 64}.zip"
    shutil.copyfile(result.archive_path, wrong_name)

    with pytest.raises(RuntimeError, match="SHA-256"):
        verify_daily_scan_archive(wrong_name)


def test_verifier_rejects_tampered_source_with_valid_outer_digest(tmp_path: Path) -> None:
    result = capture_daily_scan(
        tmp_path,
        downloader=_downloader,
        recorded_at=datetime(2026, 9, 13, 2, 37, tzinfo=UTC),
        commit_sha="test-sha",
    )
    temporary = tmp_path / "tampered.zip"
    changed = False
    with zipfile.ZipFile(result.archive_path, "r") as source, zipfile.ZipFile(
        temporary, "w"
    ) as target:
        for info in source.infolist():
            payload = source.read(info.filename)
            if not changed and info.filename.startswith("source/"):
                payload += b"\n"
                changed = True
            target.writestr(info, payload)
    assert changed

    digest = hashlib.sha256(temporary.read_bytes()).hexdigest()
    tampered = tmp_path / f"daily-scan-history-2026-09-13-{digest}.zip"
    temporary.replace(tampered)

    with pytest.raises(RuntimeError, match="source SHA-256 mismatch"):
        verify_daily_scan_archive(tampered)


def test_capture_rejects_naive_injected_clock(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        capture_daily_scan(tmp_path, recorded_at=datetime(2026, 9, 13, 2, 37))


def test_cli_has_no_historical_observation_date_argument() -> None:
    parser = build_parser()
    destinations = {action.dest for action in parser._actions}

    assert "observation_date" not in destinations
    assert "date" not in destinations


def test_daily_scan_workflow_is_append_only_and_has_no_backfill_input() -> None:
    workflow = Path(".github/workflows/daily-scan-history.yml").read_text(encoding="utf-8")

    assert "  workflow_dispatch:\n" in workflow
    assert "  workflow_dispatch:\n    inputs:" not in workflow
    assert "--clobber" not in workflow
    assert "gh release upload" in workflow
    assert "daily-scan-history-" in workflow
    assert "37 2 * * *" in workflow
    assert "assets=\"$(gh release view" in workflow
