from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
import yaml

from swing_trader.experiment_registry import (
    build_registry,
    check_registry,
    registry_bytes,
    write_registry,
)


def _write_historical(
    root: Path,
    directory_name: str = "EXP-0001-alpha",
    *,
    experiment_id: str = "EXP-0001",
    result_id: str | None = None,
    producer_field: str = "code_commit_sha",
    producer_sha: str = "a" * 40,
    include_notes: bool = True,
) -> Path:
    directory = root / "experiments" / directory_name
    directory.mkdir(parents=True, exist_ok=True)
    config = {
        "experiment": {
            "id": experiment_id,
            "name": "alpha",
            "research_stage": "exploratory",
        }
    }
    results = {
        "experiment": {
            "id": result_id or experiment_id,
            "name": "alpha",
            "research_stage": "exploratory",
            producer_field: producer_sha,
        },
        "decision": "CONTINUE RESEARCH",
    }
    (directory / "config.yaml").write_text(
        yaml.safe_dump(config, sort_keys=False), encoding="utf-8"
    )
    (directory / "results.json").write_text(
        json.dumps(results, indent=2) + "\n", encoding="utf-8"
    )
    if include_notes:
        (directory / "notes.md").write_text("# Reviewed\n", encoding="utf-8")
    return directory


def _write_protocol(root: Path, *, corrupt_lock: bool = False) -> Path:
    directory = root / "experiments" / "PROSPECTIVE-v1-test"
    directory.mkdir(parents=True, exist_ok=True)
    protocol = {
        "protocol": {
            "id": "PROSPECTIVE-v1-test",
            "status": "preregistered",
            "registered_on": "2026-01-01",
            "strategy_version": "v1",
            "frozen_source_commit": "b" * 40,
        },
        "holdout": {
            "evaluation_start": "2026-02-01",
            "minimum_observation_end": "2027-02-01",
            "minimum_closed_trades": 10,
        },
    }
    protocol_bytes = yaml.safe_dump(protocol, sort_keys=False).encode("utf-8")
    (directory / "protocol.yaml").write_bytes(protocol_bytes)
    digest = hashlib.sha256(protocol_bytes).hexdigest()
    lock = {
        "schema_version": 1,
        "protocol_id": "PROSPECTIVE-v1-test",
        "protocol_sha256": "0" * 64 if corrupt_lock else digest,
        "frozen_source_commit": "b" * 40,
        "warmup_start": "2020-01-01",
    }
    (directory / "protocol-lock.json").write_text(
        json.dumps(lock, indent=2) + "\n", encoding="utf-8"
    )
    (directory / "README.md").write_text("# Protocol\n", encoding="utf-8")
    return directory


def _write_index(root: Path, *directory_names: str) -> None:
    experiments = root / "experiments"
    experiments.mkdir(parents=True, exist_ok=True)
    links = "\n".join(f"- [{name}]({name}/)" for name in directory_names)
    (experiments / "README.md").write_text(f"# Experiments\n\n{links}\n", encoding="utf-8")


def test_registry_generation_is_deterministic_and_check_detects_staleness(tmp_path: Path) -> None:
    historical = _write_historical(tmp_path)
    protocol = _write_protocol(tmp_path)
    _write_index(tmp_path, historical.name, protocol.name)

    first = registry_bytes(tmp_path)
    second = registry_bytes(tmp_path)
    assert first == second

    registry_path = write_registry(tmp_path)
    assert registry_path.read_bytes() == first
    assert check_registry(tmp_path) == registry_path

    (historical / "notes.md").write_text("# Reviewed\nChanged.\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="stale experiment registry"):
        check_registry(tmp_path)


def test_registry_normalizes_producer_sha_and_existing_provenance(tmp_path: Path) -> None:
    historical = _write_historical(tmp_path, producer_field="producer_code_sha")
    results_path = historical / "results.json"
    results = json.loads(results_path.read_text(encoding="utf-8"))
    results["experiment"].update(
        {
            "workflow_run_id": 123,
            "artifact_id": 456,
            "artifact_sha256": "c" * 64,
        }
    )
    results_path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    _write_index(tmp_path, historical.name)

    entry = build_registry(tmp_path)["historical_experiments"][0]
    assert entry["producer_code_sha"] == "a" * 40
    assert entry["workflow_run_id"] == 123
    assert entry["artifact_id"] == 456
    assert entry["artifact_sha256"] == "c" * 64
    assert entry["decision"] == "CONTINUE RESEARCH"


def test_registry_rejects_directory_config_result_id_mismatch(tmp_path: Path) -> None:
    historical = _write_historical(tmp_path, result_id="EXP-9999")
    _write_index(tmp_path, historical.name)

    with pytest.raises(ValueError, match="directory/config/result experiment ids"):
        build_registry(tmp_path)


def test_registry_rejects_missing_required_historical_file(tmp_path: Path) -> None:
    historical = _write_historical(tmp_path, include_notes=False)
    _write_index(tmp_path, historical.name)

    with pytest.raises(ValueError, match="missing required files: notes.md"):
        build_registry(tmp_path)


def test_registry_rejects_duplicate_historical_ids(tmp_path: Path) -> None:
    first = _write_historical(tmp_path, "EXP-0001-alpha")
    second = _write_historical(tmp_path, "EXP-0001-beta")
    _write_index(tmp_path, first.name, second.name)

    with pytest.raises(ValueError, match="duplicate historical experiment ids: EXP-0001"):
        build_registry(tmp_path)


def test_registry_rejects_protocol_byte_lock_mismatch(tmp_path: Path) -> None:
    protocol = _write_protocol(tmp_path, corrupt_lock=True)
    _write_index(tmp_path, protocol.name)

    with pytest.raises(ValueError, match="protocol bytes do not match protocol lock"):
        build_registry(tmp_path)


def test_registry_rejects_missing_readme_coverage(tmp_path: Path) -> None:
    _write_historical(tmp_path)
    _write_index(tmp_path)

    with pytest.raises(ValueError, match="README.md does not link EXP-0001-alpha"):
        build_registry(tmp_path)
