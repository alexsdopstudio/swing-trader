from __future__ import annotations

import json
import re
import shutil
from collections import Counter
from pathlib import Path
from typing import Any

import yaml


SCHEMA_VERSION = 1
DEFAULT_REPOSITORY = "alexsdopstudio/swing-trader"
DEFAULT_TEMPLATE_DIR = Path("dashboard")
_TEMPLATE_FILES = ("index.html", "styles.css", "app.js")
_REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return payload


def _load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: expected a YAML mapping")
    return payload


def _mapping_list(payload: dict[str, Any], key: str, *, path: Path) -> list[dict[str, Any]]:
    value = payload.get(key)
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise ValueError(f"{path}: expected '{key}' to be a list of mappings")
    return value


def _nonempty_string(mapping: dict[str, Any], key: str, *, label: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label}: expected non-empty '{key}'")
    return value.strip()


def _knowledge_topic_counts(sources: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for source in sources:
        topics = source.get("topics")
        if not isinstance(topics, list) or any(not isinstance(topic, str) for topic in topics):
            raise ValueError("knowledge source topics must be a list of strings")
        counts.update(topics)
    return dict(sorted(counts.items()))


def _find_holdout(protocols: list[dict[str, Any]]) -> dict[str, Any]:
    matching = [item for item in protocols if item.get("id") == "PROSPECTIVE-v1-holdout"]
    if len(matching) != 1:
        raise ValueError("experiment registry must contain exactly one PROSPECTIVE-v1-holdout")
    return matching[0]


def build_project_snapshot(
    root: str | Path = ".",
    *,
    repository: str = DEFAULT_REPOSITORY,
) -> dict[str, Any]:
    """Build deterministic read-only dashboard state from canonical repository records."""
    if _REPOSITORY_RE.fullmatch(repository) is None:
        raise ValueError("repository must use owner/name format")

    root = Path(root).resolve()
    experiment_path = root / "experiments" / "registry.json"
    knowledge_path = root / "knowledge" / "registry.json"
    universe_path = root / "config" / "universe.yaml"

    experiments = _load_json(experiment_path)
    knowledge = _load_json(knowledge_path)
    universe = _load_yaml(universe_path)

    if experiments.get("schema_version") != 1:
        raise ValueError("dashboard requires experiment registry schema version 1")
    if knowledge.get("schema_version") != 1:
        raise ValueError("dashboard requires knowledge registry schema version 1")

    historical = _mapping_list(experiments, "historical_experiments", path=experiment_path)
    protocols = _mapping_list(experiments, "prospective_protocols", path=experiment_path)
    sources = _mapping_list(knowledge, "sources", path=knowledge_path)
    notes = _mapping_list(knowledge, "notes", path=knowledge_path)
    news = _mapping_list(knowledge, "news_observations", path=knowledge_path)
    holdout = _find_holdout(protocols)

    assets_raw = universe.get("assets")
    if not isinstance(assets_raw, list) or not assets_raw:
        raise ValueError(f"{universe_path}: expected non-empty assets list")
    assets: list[dict[str, str]] = []
    for index, asset in enumerate(assets_raw):
        if not isinstance(asset, dict):
            raise ValueError(f"{universe_path}: assets[{index}] must be a mapping")
        assets.append(
            {
                "symbol": _nonempty_string(asset, "symbol", label=f"assets[{index}]"),
                "asset_class": _nonempty_string(
                    asset, "asset_class", label=f"assets[{index}]"
                ),
            }
        )

    experiment_rows = []
    for experiment in sorted(historical, key=lambda item: str(item.get("id", ""))):
        experiment_rows.append(
            {
                "id": _nonempty_string(experiment, "id", label="historical experiment"),
                "name": _nonempty_string(experiment, "name", label="historical experiment"),
                "research_stage": _nonempty_string(
                    experiment, "research_stage", label="historical experiment"
                ),
                "decision": experiment.get("decision"),
                "directory": _nonempty_string(
                    experiment, "directory", label="historical experiment"
                ),
            }
        )

    strategy_version = _nonempty_string(holdout, "strategy_version", label="prospective holdout")
    return {
        "schema_version": SCHEMA_VERSION,
        "repository": repository,
        "strategy": {
            "version": strategy_version,
            "status": "frozen",
            "validation_status": "not_validated",
            "validation_label": "NOT VALIDATED",
            "deployment_status": "research_only",
        },
        "prospective_holdout": {
            "id": _nonempty_string(holdout, "id", label="prospective holdout"),
            "status": _nonempty_string(holdout, "status", label="prospective holdout"),
            "strategy_version": strategy_version,
            "evaluation_start": _nonempty_string(
                holdout, "evaluation_start", label="prospective holdout"
            ),
            "minimum_observation_end": _nonempty_string(
                holdout, "minimum_observation_end", label="prospective holdout"
            ),
            "minimum_closed_trades": int(holdout["minimum_closed_trades"]),
        },
        "research": {
            "historical_experiment_count": len(experiment_rows),
            "historical_experiments": experiment_rows,
        },
        "knowledge": {
            "source_count": len(sources),
            "note_count": len(notes),
            "news_observation_count": len(news),
            "source_topic_counts": _knowledge_topic_counts(sources),
        },
        "universe": {
            "asset_count": len(assets),
            "assets": assets,
            "benchmark_equities": _nonempty_string(
                universe, "benchmark_equities", label="universe"
            ),
            "benchmark_crypto": _nonempty_string(
                universe, "benchmark_crypto", label="universe"
            ),
        },
        "live_github": {
            "daily_scan_release_tag_prefix": "daily-scan-history-",
            "daily_scan_asset_prefix": "daily-scan-history-",
            "prospective_release_tag_prefix": "prospective-v1-holdout-data-",
            "prospective_asset_prefix": "PROSPECTIVE-v1-holdout-",
        },
        "evidence_boundaries": [
            "Retrospective experiments are research diagnostics, not prospective validation.",
            "Daily scan history is operational evidence and cannot substitute for holdout evidence.",
            "News observations are time-bounded context and are not validation evidence.",
            "Generated registries and this dashboard are derived views, not editable sources of truth.",
        ],
    }


def project_snapshot_bytes(
    root: str | Path = ".",
    *,
    repository: str = DEFAULT_REPOSITORY,
) -> bytes:
    payload = build_project_snapshot(root, repository=repository)
    return (
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def build_dashboard(
    output_dir: str | Path,
    *,
    root: str | Path = ".",
    repository: str = DEFAULT_REPOSITORY,
    template_dir: str | Path | None = None,
) -> Path:
    """Build the static dashboard site without network access or time-dependent inputs."""
    root = Path(root).resolve()
    output_dir = Path(output_dir).resolve()
    source_dir = Path(template_dir).resolve() if template_dir else root / DEFAULT_TEMPLATE_DIR
    missing = [name for name in _TEMPLATE_FILES if not (source_dir / name).is_file()]
    if missing:
        raise FileNotFoundError(f"dashboard template is missing: {', '.join(missing)}")

    output_dir.mkdir(parents=True, exist_ok=True)
    for name in _TEMPLATE_FILES:
        shutil.copyfile(source_dir / name, output_dir / name)
    (output_dir / "project.json").write_bytes(project_snapshot_bytes(root, repository=repository))
    return output_dir
