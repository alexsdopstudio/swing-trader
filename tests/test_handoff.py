from pathlib import Path

from swing_trader.handoff import (
    HANDOFF_MARKER,
    build_handoff,
    infer_lifecycle_stage,
    recommended_actions,
    render_handoff_markdown,
    write_handoff,
)


def test_infer_lifecycle_stage_from_review_outcome() -> None:
    assert infer_lifecycle_stage("Review outcome: `PASS`", draft=False) == "review-passed"
    assert (
        infer_lifecycle_stage("Review outcome: `CHANGES REQUESTED`", draft=False)
        == "changes-requested"
    )
    assert infer_lifecycle_stage("Review outcome: `BLOCKED`", draft=True) == "blocked"


def test_infer_lifecycle_stage_for_draft_and_ready_prs() -> None:
    assert infer_lifecycle_stage("## Implementation\n\nPending.", draft=True) == "design"
    assert infer_lifecycle_stage("## Implementation\n\nImplemented.", draft=True) == "implementation"
    assert infer_lifecycle_stage("## Implementation\n\nImplemented.", draft=False) == "review"


def test_recommended_actions_prioritize_failed_checks() -> None:
    actions = recommended_actions(
        "review",
        [{"name": "CI", "status": "completed", "conclusion": "failure"}],
    )

    assert actions[0] == "Inspect and fix failing checks: CI."
    assert "formal diff-based review" in actions[-1]


def test_build_handoff_includes_active_plan_and_metadata(tmp_path: Path) -> None:
    (tmp_path / ".ai").mkdir()
    (tmp_path / ".ai/current-state.md").write_text("state", encoding="utf-8")
    (tmp_path / "docs/plans/active").mkdir(parents=True)
    (tmp_path / "docs/plans/active/test-plan.md").write_text("plan", encoding="utf-8")

    handoff = build_handoff(
        tmp_path,
        pr={
            "repository": "owner/repo",
            "number": 12,
            "title": "feat(test): example",
            "url": "https://example.invalid/pr/12",
            "base": "main",
            "head": "feat/example",
            "head_sha": "abc123",
            "draft": True,
            "body": "## Implementation\n\nImplemented.",
        },
        checks=[{"name": "CI", "status": "completed", "conclusion": "success"}],
        generated_at="2026-09-12T18:00:00+00:00",
    )

    assert handoff["schema_version"] == 1
    assert handoff["repository"] == "owner/repo"
    assert handoff["pull_request"]["number"] == 12
    assert handoff["lifecycle_stage"] == "implementation"
    assert handoff["active_plans"] == ["docs/plans/active/test-plan.md"]
    assert handoff["checks"][0]["name"] == "CI"


def test_render_handoff_markdown_contains_resume_marker_and_actions(tmp_path: Path) -> None:
    (tmp_path / "docs/plans/active").mkdir(parents=True)
    handoff = build_handoff(
        tmp_path,
        pr={
            "repository": "owner/repo",
            "number": 2,
            "title": "feat(test): example",
            "base": "main",
            "head": "feat/example",
            "head_sha": "deadbeef",
            "draft": False,
            "body": "Review outcome: `PASS`",
        },
        generated_at="2026-09-12T18:00:00+00:00",
    )

    markdown = render_handoff_markdown(handoff)

    assert markdown.startswith(HANDOFF_MARKER)
    assert "Lifecycle stage: **review-passed**" in markdown
    assert "squash-merge" in markdown
    assert "do not ask the user to manually shuttle chat context" in markdown


def test_write_handoff_creates_json_and_markdown(tmp_path: Path) -> None:
    (tmp_path / "docs/plans/active").mkdir(parents=True)
    json_path, markdown_path = write_handoff(
        tmp_path,
        output_dir=tmp_path / "output",
        pr={"head": "feat/example", "draft": True, "body": ""},
        generated_at="2026-09-12T18:00:00+00:00",
    )

    assert json_path.exists()
    assert markdown_path.exists()
    assert '"schema_version": 1' in json_path.read_text(encoding="utf-8")
    assert HANDOFF_MARKER in markdown_path.read_text(encoding="utf-8")
