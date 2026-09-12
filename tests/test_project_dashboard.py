from __future__ import annotations

import json
from pathlib import Path

import pytest

from swing_trader.project_dashboard import (
    build_dashboard,
    build_project_snapshot,
    project_snapshot_bytes,
)
from swing_trader.project_dashboard_cli import build_parser


ROOT = Path(__file__).resolve().parents[1]


def test_project_snapshot_preserves_validation_boundary() -> None:
    snapshot = build_project_snapshot(ROOT)

    assert snapshot["strategy"] == {
        "version": "v1",
        "status": "frozen",
        "validation_status": "not_validated",
        "validation_label": "NOT VALIDATED",
        "deployment_status": "research_only",
    }
    assert snapshot["prospective_holdout"] == {
        "id": "PROSPECTIVE-v1-holdout",
        "status": "preregistered",
        "strategy_version": "v1",
        "evaluation_start": "2026-09-14",
        "minimum_observation_end": "2028-09-14",
        "minimum_closed_trades": 30,
    }
    assert snapshot["research"]["historical_experiment_count"] == 6
    assert any(
        "not prospective validation" in boundary.lower()
        for boundary in snapshot["evidence_boundaries"]
    )
    assert any(
        "news observations" in boundary.lower() and "not validation" in boundary.lower()
        for boundary in snapshot["evidence_boundaries"]
    )


def test_project_snapshot_matches_knowledge_and_universe_registries() -> None:
    snapshot = build_project_snapshot(ROOT)

    assert snapshot["knowledge"]["source_count"] == 9
    assert snapshot["knowledge"]["note_count"] == 5
    assert snapshot["knowledge"]["news_observation_count"] == 0
    assert snapshot["knowledge"]["source_topic_counts"]["momentum"] == 2
    assert snapshot["knowledge"]["source_topic_counts"]["survivorship-bias"] == 2

    universe = snapshot["universe"]
    assert universe["asset_count"] == 11
    assert universe["benchmark_equities"] == "QQQ"
    assert universe["benchmark_crypto"] == "BTC-USD"
    assert universe["assets"][0] == {"symbol": "BTC-USD", "asset_class": "crypto"}
    assert universe["assets"][-1] == {"symbol": "TSLA", "asset_class": "equity"}


def test_project_snapshot_bytes_are_deterministic() -> None:
    first = project_snapshot_bytes(ROOT)
    second = project_snapshot_bytes(ROOT)

    assert first == second
    payload = json.loads(first)
    assert payload["strategy"]["validation_status"] == "not_validated"
    assert "generated_at" not in payload


def test_dashboard_build_copies_only_local_static_assets(tmp_path: Path) -> None:
    output = build_dashboard(tmp_path / "site", root=ROOT)

    assert output == (tmp_path / "site").resolve()
    assert sorted(path.name for path in output.iterdir()) == [
        "app.js",
        "index.html",
        "project.json",
        "styles.css",
    ]
    assert (output / "project.json").read_bytes() == project_snapshot_bytes(ROOT)

    index = (output / "index.html").read_text(encoding="utf-8")
    assert 'href="./styles.css"' in index
    assert 'src="./app.js"' in index
    assert 'src="http' not in index
    assert 'href="http' not in index
    assert "NOT VALIDATED" in index

    styles = (output / "styles.css").read_text(encoding="utf-8")
    assert "@import" not in styles
    assert "url(http" not in styles


def test_live_javascript_cannot_replace_canonical_validation_from_github() -> None:
    script = (ROOT / "dashboard" / "app.js").read_text(encoding="utf-8")

    canonical_start = script.index("function renderCanonical")
    live_start = script.index("async function loadLiveStatus")
    canonical_section = script[canonical_start:live_start]
    live_section = script[live_start:]

    assert 'byId("validation-label").textContent = project.strategy.validation_label' in canonical_section
    assert "validation-label" not in live_section
    assert "validation_status" not in live_section
    assert "validation_label" not in live_section


def test_dashboard_cli_has_no_mutation_or_date_arguments() -> None:
    parser = build_parser()
    destinations = {action.dest for action in parser._actions}

    assert {"root", "output_dir", "repository"}.issubset(destinations)
    assert "date" not in destinations
    assert "observation_date" not in destinations
    assert "write" not in destinations
    assert "deploy" not in destinations


def test_invalid_repository_identifier_is_rejected() -> None:
    with pytest.raises(ValueError, match="owner/name"):
        build_project_snapshot(ROOT, repository="not a repository")


def test_dashboard_workflow_builds_pull_requests_without_deploying() -> None:
    workflow = (ROOT / ".github" / "workflows" / "project-dashboard.yml").read_text(
        encoding="utf-8"
    )

    assert "pull_request:" in workflow
    assert "actions/checkout@v6" in workflow
    assert "actions/upload-artifact@v4" in workflow
    assert "actions/configure-pages@v5" in workflow
    assert "actions/upload-pages-artifact@v4" in workflow
    assert "actions/deploy-pages@v4" in workflow
    assert "pages: write" in workflow
    assert "id-token: write" in workflow
    assert "if: github.event_name != 'pull_request'" in workflow
    assert "enablement: true" not in workflow
