from __future__ import annotations

import base64
import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class PullRequestSummary:
    number: int
    title: str
    url: str
    head_ref: str
    head_sha: str
    base_ref: str
    draft: bool
    updated_at: str
    body: str


class GitHubClient:
    """Small read-only GitHub client used only to reconstruct agent session state."""

    def __init__(self, token: str | None = None, timeout: float = 5.0) -> None:
        self.token = token or os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
        self.timeout = timeout

    def _get_json(self, url: str) -> Any:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "swing-trader-agent-bootstrap",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = Request(url, headers=headers)
        with urlopen(request, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def list_open_pull_requests(self, repository: str) -> list[PullRequestSummary]:
        payload = self._get_json(
            f"https://api.github.com/repos/{repository}/pulls"
            "?state=open&sort=updated&direction=desc&per_page=100"
        )
        if not isinstance(payload, list):
            raise ValueError("GitHub pull-request response must be a list")
        return [
            PullRequestSummary(
                number=int(item["number"]),
                title=str(item["title"]),
                url=str(item["html_url"]),
                head_ref=str(item["head"]["ref"]),
                head_sha=str(item["head"]["sha"]),
                base_ref=str(item["base"]["ref"]),
                draft=bool(item.get("draft", False)),
                updated_at=str(item["updated_at"]),
                body=str(item.get("body") or ""),
            )
            for item in payload
        ]

    def fetch_text_file(self, repository: str, path: str, ref: str) -> str | None:
        encoded_path = quote(path, safe="/")
        encoded_ref = quote(ref, safe="")
        payload = self._get_json(
            f"https://api.github.com/repos/{repository}/contents/{encoded_path}?ref={encoded_ref}"
        )
        if not isinstance(payload, dict) or payload.get("encoding") != "base64":
            return None
        content = payload.get("content")
        if not isinstance(content, str):
            return None
        return base64.b64decode(content).decode("utf-8").strip()


def _git(root: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"
    return result.stdout.strip()


def parse_github_repository(remote: str) -> str | None:
    """Return owner/repo for common GitHub HTTPS/SSH remotes."""
    remote = remote.strip()
    patterns = (
        r"^https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$",
        r"^git@github\.com:([^/]+)/([^/]+?)(?:\.git)?$",
        r"^ssh://git@github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$",
    )
    for pattern in patterns:
        match = re.match(pattern, remote)
        if match:
            return f"{match.group(1)}/{match.group(2)}"
    return None


def select_active_pr(
    branch: str,
    pull_requests: list[PullRequestSummary],
) -> tuple[PullRequestSummary | None, str]:
    """Select resumable work without requiring a user to identify the PR."""
    matching = [
        pr
        for pr in pull_requests
        if branch not in {"", "main", "master", "unavailable", "detached HEAD"}
        and pr.head_ref == branch
    ]
    if matching:
        return matching[0], "current branch matches open PR"
    if len(pull_requests) == 1:
        return pull_requests[0], "only open PR"
    if pull_requests:
        newest = max(pull_requests, key=lambda pr: (pr.updated_at, pr.number))
        return newest, "most recently updated open PR (inferred)"
    return None, "no open PR"


def _plan_path_from_pr_body(body: str) -> str | None:
    paths = re.findall(r"docs/plans/(?:active|completed)/[A-Za-z0-9._/-]+\.md", body)
    active = [path for path in paths if "/active/" in path]
    if active:
        return active[0]
    return paths[0] if paths else None


def _local_active_plans(root: Path) -> list[tuple[str, str]]:
    plans_dir = root / "docs/plans/active"
    if not plans_dir.exists():
        return []
    return [
        (plan.relative_to(root).as_posix(), plan.read_text(encoding="utf-8").strip())
        for plan in sorted(plans_dir.glob("*.md"))
    ]


def _remote_state(
    repository: str | None,
    branch: str,
    client: GitHubClient | None,
    allow_remote: bool,
) -> tuple[list[PullRequestSummary], PullRequestSummary | None, str, str | None, str | None]:
    if not repository:
        return [], None, "GitHub repository could not be derived from origin", None, None
    if not allow_remote:
        return [], None, "remote discovery disabled", None, None

    client = client or GitHubClient()
    try:
        pull_requests = client.list_open_pull_requests(repository)
        active_pr, reason = select_active_pr(branch, pull_requests)
        plan_path = _plan_path_from_pr_body(active_pr.body) if active_pr else None
        plan_text = (
            client.fetch_text_file(repository, plan_path, active_pr.head_sha)
            if active_pr and plan_path
            else None
        )
        return pull_requests, active_pr, reason, plan_path, plan_text
    except (
        HTTPError,
        URLError,
        TimeoutError,
        OSError,
        RuntimeError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        return [], None, f"remote discovery unavailable: {type(exc).__name__}", None, None


def build_handoff(
    root: Path,
    *,
    client: GitHubClient | None = None,
    allow_remote: bool = True,
) -> str:
    root = root.resolve()
    branch = _git(root, "branch", "--show-current") or "detached HEAD"
    latest_commit = _git(root, "log", "-1", "--oneline")
    changed_files = _git(root, "status", "--short") or "clean"
    remote = _git(root, "remote", "get-url", "origin")
    repository = parse_github_repository(remote) if remote != "unavailable" else None

    pull_requests, active_pr, selection_reason, remote_plan_path, remote_plan = _remote_state(
        repository,
        branch,
        client,
        allow_remote,
    )

    sections = [
        "# AI Session Handoff",
        "",
        f"Generated: {datetime.now(UTC).isoformat()}",
        "",
        "## Resume directive",
        "",
        "Treat repository files, Git state, and GitHub pull requests as the source of truth. "
        "Continue the active PR when the task is unambiguous. Do not ask the user to copy chat "
        "history, run bootstrap commands, choose a branch, or restate information that can be "
        "derived from repository/GitHub state.",
        "",
        "## Local Git",
        f"- branch: {branch}",
        f"- latest commit: {latest_commit}",
        f"- origin: {remote}",
        f"- repository: {repository or 'unavailable'}",
        "- changed files:",
        "```text",
        changed_files,
        "```",
        "",
        "## Remote discovery",
        f"- status: {selection_reason}",
    ]

    if pull_requests:
        sections.extend(("", "## Open pull requests", ""))
        for pr in pull_requests:
            marker = " **ACTIVE**" if active_pr and pr.number == active_pr.number else ""
            sections.append(
                f"- #{pr.number}{marker}: {pr.title} — `{pr.head_ref}` -> `{pr.base_ref}` "
                f"({'draft' if pr.draft else 'ready'}, updated {pr.updated_at}) — {pr.url}"
            )
    else:
        sections.extend(("", "## Open pull requests", "", "No remote pull requests available."))

    if active_pr:
        sections.extend(
            (
                "",
                "## Active pull request",
                "",
                f"- number: #{active_pr.number}",
                f"- title: {active_pr.title}",
                f"- branch: `{active_pr.head_ref}`",
                f"- head: `{active_pr.head_sha}`",
                f"- draft: {str(active_pr.draft).lower()}",
                f"- selection: {selection_reason}",
                "",
                "### PR lifecycle record",
                "",
                active_pr.body.strip() or "_No PR body._",
            )
        )

    if remote_plan_path:
        sections.extend(("", f"## Active PR plan: `{remote_plan_path}`", ""))
        sections.append(remote_plan or "_Plan could not be fetched from the PR head._")

    local_plans = _local_active_plans(root)
    if local_plans:
        for path, content in local_plans:
            if path == remote_plan_path and remote_plan:
                continue
            sections.extend(("", f"## Local active plan: `{path}`", "", content))

    current_state = root / ".ai/current-state.md"
    if current_state.exists():
        sections.extend(
            (
                "",
                "## Current project state",
                "",
                current_state.read_text(encoding="utf-8").strip(),
            )
        )

    sections.extend(
        (
            "",
            "## Autonomous continuation rule",
            "",
            "1. Verify the selected PR/branch against the current task and newest repository state.",
            "2. Read `AGENTS.md`, `.ai/context.md`, this handoff, and the active plan/PR body.",
            "3. Resume the existing branch/PR when the logical change is already in progress.",
            "4. Otherwise start the normal dedicated branch -> design -> Draft PR lifecycle.",
            "5. Keep the PR `Agent handoff` section current at meaningful lifecycle transitions.",
            "6. Never require manual user context transfer when the information is derivable.",
            "",
        )
    )
    return "\n".join(sections)


def write_handoff(
    root: Path,
    output: Path | None = None,
    *,
    client: GitHubClient | None = None,
    allow_remote: bool = True,
) -> Path:
    root = root.resolve()
    output = output or root / ".ai/handoff.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        build_handoff(root, client=client, allow_remote=allow_remote),
        encoding="utf-8",
    )
    return output
