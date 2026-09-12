from pathlib import Path

import swing_trader.handoff as handoff
from swing_trader.handoff import PullRequestSummary, build_handoff


class PlanFailingClient:
    def list_open_pull_requests(self, repository: str) -> list[PullRequestSummary]:
        assert repository == "example/project"
        return [
            PullRequestSummary(
                number=8,
                title="feat(agents): add handoff",
                url="https://github.com/example/project/pull/8",
                head_ref="feat/handoff",
                head_sha="head-sha",
                base_ref="main",
                draft=True,
                updated_at="2026-09-12T00:00:00Z",
                body="Design plan: `docs/plans/active/missing.md`",
            )
        ]

    def fetch_text_file(self, repository: str, path: str, ref: str) -> str | None:
        raise RuntimeError("plan unavailable")


def _fake_git(root: Path, *args: str) -> str:
    values = {
        ("branch", "--show-current"): "feat/handoff",
        ("log", "-1", "--oneline"): "abc123 feat(agents): work",
        ("status", "--short"): "",
        ("remote", "get-url", "origin"): "https://github.com/example/project.git",
    }
    return values[args]


def test_plan_fetch_failure_preserves_discovered_pr_state(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(handoff, "_git", _fake_git)

    rendered = build_handoff(tmp_path, client=PlanFailingClient())

    assert "#8 **ACTIVE**" in rendered
    assert "feat(agents): add handoff" in rendered
    assert "remote plan unavailable: RuntimeError" in rendered
    assert "Plan could not be fetched from the PR head." in rendered
