from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import yaml


SCHEMA_VERSION = 1
REGISTRY_PATH = Path("experiments/registry.json")
_EXPERIMENT_DIR_RE = re.compile(r"^(EXP-\d{4})-([a-z0-9][a-z0-9-]*)$")
_COMMIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_bytes()) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: expected a mapping")
    return payload


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: expected a mapping")
    return payload


def _mapping(payload: dict[str, Any], key: str, *, path: Path) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected '{key}' mapping")
    return value


def _nonempty_string(mapping: dict[str, Any], key: str, *, label: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label}: expected non-empty '{key}'")
    return value.strip()


def _optional_int(mapping: dict[str, Any], key: str, *, label: str) -> int | None:
    value = mapping.get(key)
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError(f"{label}: '{key}' must be an integer")
    try:
        integer = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label}: '{key}' must be an integer") from exc
    if integer < 0:
        raise ValueError(f"{label}: '{key}' cannot be negative")
    return integer


def _optional_string(mapping: dict[str, Any], key: str) -> str | None:
    value = mapping.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"expected '{key}' to be a non-empty string when present")
    return value.strip()


def _require_files(directory: Path, names: tuple[str, ...]) -> dict[str, Path]:
    paths = {name: directory / name for name in names}
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        raise ValueError(f"{directory}: missing required files: {', '.join(missing)}")
    return paths


def _readme_has_directory(readme: str, directory_name: str) -> bool:
    return directory_name in readme


def _producer_code_sha(result_experiment: dict[str, Any], *, label: str) -> str:
    producer = result_experiment.get("producer_code_sha")
    legacy = result_experiment.get("code_commit_sha")
    if producer is not None and legacy is not None and producer != legacy:
        raise ValueError(f"{label}: conflicting producer_code_sha and code_commit_sha")
    value = producer if producer is not None else legacy
    if not isinstance(value, str) or _COMMIT_SHA_RE.fullmatch(value) is None:
        raise ValueError(f"{label}: expected a 40-character producer/code commit SHA")
    return value


def _historical_entry(directory: Path, readme: str, root: Path) -> dict[str, Any]:
    match = _EXPERIMENT_DIR_RE.fullmatch(directory.name)
    if match is None:
        raise ValueError(f"{directory}: historical experiment directory name is invalid")
    directory_id = match.group(1)
    files = _require_files(directory, ("config.yaml", "results.json", "notes.md"))
    config = _load_yaml(files["config.yaml"])
    results = _load_json(files["results.json"])
    config_experiment = _mapping(config, "experiment", path=files["config.yaml"])
    result_experiment = _mapping(results, "experiment", path=files["results.json"])

    config_id = _nonempty_string(config_experiment, "id", label=str(files["config.yaml"]))
    result_id = _nonempty_string(result_experiment, "id", label=str(files["results.json"]))
    if config_id != directory_id or result_id != directory_id:
        raise ValueError(
            f"{directory}: directory/config/result experiment ids must all equal {directory_id}"
        )

    config_name = _nonempty_string(config_experiment, "name", label=str(files["config.yaml"]))
    result_name = _nonempty_string(result_experiment, "name", label=str(files["results.json"]))
    if config_name != result_name:
        raise ValueError(f"{directory}: config and result experiment names differ")

    research_stage = _nonempty_string(
        config_experiment, "research_stage", label=str(files["config.yaml"])
    )
    result_stage = result_experiment.get("research_stage")
    if result_stage is not None and result_stage != research_stage:
        raise ValueError(f"{directory}: config and result research stages differ")

    if not _readme_has_directory(readme, directory.name):
        raise ValueError(f"experiments/README.md does not link {directory.name}")

    decision = results.get("decision")
    if decision is not None and (not isinstance(decision, str) or not decision.strip()):
        raise ValueError(f"{files['results.json']}: decision must be a non-empty string when present")

    return {
        "id": directory_id,
        "name": config_name,
        "research_stage": research_stage,
        "directory": directory.relative_to(root).as_posix(),
        "config_sha256": _sha256(files["config.yaml"]),
        "results_sha256": _sha256(files["results.json"]),
        "notes_sha256": _sha256(files["notes.md"]),
        "producer_code_sha": _producer_code_sha(
            result_experiment, label=str(files["results.json"])
        ),
        "workflow_run_id": _optional_int(
            result_experiment, "workflow_run_id", label=str(files["results.json"])
        ),
        "artifact_id": _optional_int(
            result_experiment, "artifact_id", label=str(files["results.json"])
        ),
        "artifact_sha256": _optional_string(result_experiment, "artifact_sha256"),
        "decision": None if decision is None else decision.strip(),
    }


def _prospective_entry(directory: Path, readme: str, root: Path) -> dict[str, Any]:
    files = _require_files(directory, ("protocol.yaml", "protocol-lock.json", "README.md"))
    protocol_bytes = files["protocol.yaml"].read_bytes()
    protocol_sha256 = hashlib.sha256(protocol_bytes).hexdigest()
    protocol = _load_yaml(files["protocol.yaml"])
    lock = _load_json(files["protocol-lock.json"])
    metadata = _mapping(protocol, "protocol", path=files["protocol.yaml"])
    holdout = _mapping(protocol, "holdout", path=files["protocol.yaml"])

    protocol_id = _nonempty_string(metadata, "id", label=str(files["protocol.yaml"]))
    status = _nonempty_string(metadata, "status", label=str(files["protocol.yaml"]))
    strategy_version = _nonempty_string(
        metadata, "strategy_version", label=str(files["protocol.yaml"])
    )
    frozen_source_commit = _nonempty_string(
        metadata, "frozen_source_commit", label=str(files["protocol.yaml"])
    )
    if _COMMIT_SHA_RE.fullmatch(frozen_source_commit) is None:
        raise ValueError(f"{files['protocol.yaml']}: frozen_source_commit must be a commit SHA")

    if lock.get("schema_version") != 1:
        raise ValueError(f"{files['protocol-lock.json']}: unsupported protocol lock schema")
    if lock.get("protocol_id") != protocol_id:
        raise ValueError(f"{directory}: protocol lock id does not match protocol metadata")
    if lock.get("protocol_sha256") != protocol_sha256:
        raise ValueError(f"{directory}: protocol bytes do not match protocol lock")
    if lock.get("frozen_source_commit") != frozen_source_commit:
        raise ValueError(f"{directory}: frozen source commit does not match protocol lock")

    if not directory.name.startswith("PROSPECTIVE-"):
        raise ValueError(f"{directory}: prospective protocol directory name is invalid")
    if not _readme_has_directory(readme, directory.name):
        raise ValueError(f"experiments/README.md does not link {directory.name}")

    return {
        "id": protocol_id,
        "status": status,
        "strategy_version": strategy_version,
        "directory": directory.relative_to(root).as_posix(),
        "registered_on": str(metadata.get("registered_on")),
        "evaluation_start": str(holdout.get("evaluation_start")),
        "minimum_observation_end": str(holdout.get("minimum_observation_end")),
        "minimum_closed_trades": int(holdout.get("minimum_closed_trades")),
        "protocol_sha256": protocol_sha256,
        "protocol_lock_sha256": _sha256(files["protocol-lock.json"]),
        "readme_sha256": _sha256(files["README.md"]),
        "frozen_source_commit": frozen_source_commit,
    }


def build_registry(root: str | Path = ".") -> dict[str, Any]:
    root = Path(root).resolve()
    experiments_root = root / "experiments"
    readme_path = experiments_root / "README.md"
    if not experiments_root.is_dir() or not readme_path.is_file():
        raise FileNotFoundError("repository must contain experiments/ and experiments/README.md")
    readme = readme_path.read_text(encoding="utf-8")

    historical_directories = sorted(
        path for path in experiments_root.iterdir() if path.is_dir() and path.name.startswith("EXP-")
    )
    prospective_directories = sorted(
        path
        for path in experiments_root.iterdir()
        if path.is_dir() and path.name.startswith("PROSPECTIVE-")
    )

    historical = [_historical_entry(path, readme, root) for path in historical_directories]
    ids = [entry["id"] for entry in historical]
    duplicates = sorted({item for item in ids if ids.count(item) > 1})
    if duplicates:
        raise ValueError(f"duplicate historical experiment ids: {', '.join(duplicates)}")
    historical.sort(key=lambda entry: entry["id"])

    prospective = [_prospective_entry(path, readme, root) for path in prospective_directories]
    prospective_ids = [entry["id"] for entry in prospective]
    duplicate_protocols = sorted({item for item in prospective_ids if prospective_ids.count(item) > 1})
    if duplicate_protocols:
        raise ValueError(f"duplicate prospective protocol ids: {', '.join(duplicate_protocols)}")
    prospective.sort(key=lambda entry: (entry["id"], entry["directory"]))

    return {
        "schema_version": SCHEMA_VERSION,
        "historical_experiments": historical,
        "prospective_protocols": prospective,
    }


def registry_bytes(root: str | Path = ".") -> bytes:
    payload = build_registry(root)
    return (json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")


def write_registry(root: str | Path = ".") -> Path:
    root = Path(root).resolve()
    path = root / REGISTRY_PATH
    path.write_bytes(registry_bytes(root))
    return path


def check_registry(root: str | Path = ".") -> Path:
    root = Path(root).resolve()
    path = root / REGISTRY_PATH
    expected = registry_bytes(root)
    if not path.is_file():
        raise RuntimeError(f"missing generated experiment registry: {REGISTRY_PATH}")
    if path.read_bytes() != expected:
        raise RuntimeError(
            f"stale experiment registry: run swing-experiment-registry --root {root}"
        )
    return path
