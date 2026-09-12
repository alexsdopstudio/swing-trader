from pathlib import Path

import swing_trader.handoff as handoff
from swing_trader.handoff import PullRequestSummary, build_handoff, parse_github_repository, select_active_pr


def _pr(
    number: int,
    branch: str,
    *,
    updated_at: str,
    body: str = "",
    draft: bool = True,
) -> PullRequestSummary:
    return PullRequestSummary(
        number=number,
        title=f"feat(test): pr {number}",
        url=f"https://github.com/example/project/pull/{number}",
        head_ref=branch,
        head_sha=f"sha-{number}",
        base_ref="main",
        draft=draft,
        updated_at=updated_at,
        body=body,
    )


def test_parse_github_repository_supports_common_remote_forms() -> None:
    assert parse_github_repository("https://github.com/example/project.git") == "example/project"
    assert parse_github_repository("git@github.com:example/project.git") == "example/project"
    assert parse_github_repository("ssh://git@github.com/example/project.git") == "example/project"
    assert parse_github_repository("https://gitlab.com/example/project.git") is None


def test_select_active_pr_prefers_current_branch_match() -> None:
    older_match = _pr(7, "feat/current", updated_at="2026-09-01T00:00:00Z")
    newer_other = _pr(8, "feat/other", updated_at="2026-09-12T00:00:00Z")

    selected, reason = select_active_pr("feat/current", [newer_other, older_match])

    assert selected == older_match
    assert reason == "current branch matches open PR"


def test_select_active_pr_uses_only_open_pr_without_branch_match() -> None:
    only = _pr(7, "feat/current", updated_at="2026-09-12T00:00:00Z")

    selected, reason = select_active_pr("main", [only])

    assert selected == only
    assert reason == "only open PR"


def test_select_active_pr_marks_multi_pr_recency_as_inferred() -> None:
    older = _pr(7, "feat/older", updated_at="2026-09-01T00:00:00Z")
    newer = _pr(8, "feat/newer", updated_at="2026-09-12T00:00:00Z")

    selected, reason = select_active_pr("main", [older, newer])

    assert selected == newer
    assert "inferred" in reason


class FakeGitHubClient:
    def __init__(self, pull_requests: list[PullRequestSummary], plan_text: str | None = None) -> None:
        self.pull_requests = pull_requests
        self.plan_text = plan_text
        self.fetch_calls: list[tuple[str, str, str]] = []

    def list_open_pull_requests(self, repository: str) -> list[PullRequestSummary]:
        assert repository == "example/project"
        return self.pull_requests

    def fetch_text_file(self, repository: str, path: str, ref: str) -> str | None:
        self.fetch_calls.append((repository, path, ref))
        return self.plan_text


def _fake_git(root: Path, *args: str) -> str:
    values = {
        ("branch", "--show-current"): "feat/handoff",
        ("log", "-1", "--oneline"): "abc123 feat(agents): work",
        ("status", "--short"): "clean",
        ("remote", "get-url", "origin"): "https://github.com/example/project.git",
    }
    return values[args]


def test_build_handoff_includes_active_pr_body_and_remote_plan(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(handoff, "_git", _fake_git)
    (tmp_path / ".ai").mkdir()
    (tmp_path / ".ai/current-state.md").write_text("# Current State\n\nReady.", encoding="utf-8")

    pr = _pr(
        8,
        "feat/handoff",
        updated_at="2026-09-12T00:00:00Z",
        body=(
            "## Agent handoff\n\nCurrent stage: Implementation\n\n"
            "Design plan: `docs/plans/active/agent-handoff.md`"
        ),
    )
    client = FakeGitHubClient([pr], plan_text="# Agent Handoff Plan\n\nContinue implementation.")

    rendered = build_handoff(tmp_path, client=client)

    assert "#8" in rendered
    assert "**ACTIVE**" in rendered
    assert "Current stage: Implementation" in rendered
    assert "# Agent Handoff Plan" in rendered
    assert "current branch matches open PR" in rendered
    assert client.fetch_calls == [
        ("example/project", "docs/plans/active/agent-handoff.md", "sha-8")
    ]


def test_build_handoff_degrades_to_local_state_when_remote_is_disabled(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(handoff, "_git", _fake_git)
    plan_dir = tmp_path / "docs/plans/active"
    plan_dir.mkdir(parents=True)
    (plan_dir / "local.md").write_text("# Local Plan\n\nNext action.", encoding="utf-8")

    rendered = build_handoff(tmp_path, allow_remote=False)

    assert "remote discovery disabled" in rendered
    assert "No remote pull requests available." in rendered
    assert "# Local Plan" in rendered
    assert "Never require manual user context transfer" in rendered
