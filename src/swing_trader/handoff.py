from __future__ import annotations

import json
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

HANDOFF_MARKER = "<!-- agent-handoff -->"
SCHEMA_VERSION = 1


def _git(root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip()


def infer_lifecycle_stage(pr_body: str, draft: bool) -> str:
    """Infer a conservative lifecycle stage from the PR body and draft state."""
    match = re.search(
        r"Review outcome:\s*`?(PASS|CHANGES REQUESTED|BLOCKED)`?",
        pr_body or "",
        flags=re.IGNORECASE,
    )
    if match:
        outcome = match.group(1).upper()
        if outcome == "PASS":
            return "review-passed"
        if outcome == "CHANGES REQUESTED":
            return "changes-requested"
        return "blocked"

    if draft:
        implementation = re.search(
            r"## Implementation\s+Pending(?:\.|\s|$)",
            pr_body or "",
            flags=re.IGNORECASE,
        )
        return "design" if implementation else "implementation"
    return "review"


def recommended_actions(stage: str, checks: list[dict[str, Any]]) -> list[str]:
    failed = [
        check.get("name", "unnamed check")
        for check in checks
        if str(check.get("conclusion") or "").lower()
        in {"failure", "cancelled", "timed_out", "action_required", "startup_failure"}
    ]
    pending = [
        check.get("name", "unnamed check")
        for check in checks
        if str(check.get("status") or "").lower() not in {"completed", "success"}
        and not check.get("conclusion")
    ]

    actions: list[str] = []
    if failed:
        actions.append("Inspect and fix failing checks: " + ", ".join(sorted(failed)) + ".")
    elif pending:
        actions.append("Inspect current check state before changing code: " + ", ".join(sorted(pending)) + ".")

    stage_actions = {
        "design": [
            "Read the active design plan and PR body, then continue implementation on the existing branch.",
            "Do not open a duplicate PR for the same logical task.",
        ],
        "implementation": [
            "Inspect the current diff and active plan, then finish implementation on the existing branch.",
            "Complete Simplify, Validation, Compound, and memory updates before marking the PR ready.",
        ],
        "changes-requested": [
            "Read the formal review findings and unresolved threads, fix them on the same branch, then repeat validation and review.",
        ],
        "blocked": [
            "Read the documented blocker and resolve it only if repository decisions provide sufficient authority; otherwise request the specific missing decision.",
        ],
        "review": [
            "Inspect the final diff, unresolved review threads, and required checks, then perform the formal diff-based review.",
        ],
        "review-passed": [
            "Verify required CI is green and no unresolved review threads remain, then squash-merge using the PR title.",
        ],
    }
    actions.extend(stage_actions.get(stage, stage_actions["implementation"]))
    return actions


def _changed_files(root: Path, base_branch: str | None) -> list[str]:
    candidates: list[str] = []
    if base_branch:
        candidates.extend((f"origin/{base_branch}", base_branch))
    for base in candidates:
        output = _git(root, "diff", "--name-only", f"{base}...HEAD")
        if output is not None:
            return sorted(line for line in output.splitlines() if line.strip())

    status = _git(root, "status", "--short") or ""
    files: list[str] = []
    for line in status.splitlines():
        path = line[3:].strip() if len(line) > 3 else line.strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if path:
            files.append(path)
    return sorted(set(files))


def build_handoff(
    root: Path,
    *,
    pr: dict[str, Any] | None = None,
    checks: list[dict[str, Any]] | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    pr = dict(pr or {})
    checks = [dict(check) for check in (checks or [])]
    draft = bool(pr.get("draft", False))
    stage = infer_lifecycle_stage(str(pr.get("body") or ""), draft)
    base_branch = str(pr.get("base") or "") or None
    head_branch = str(pr.get("head") or "") or (_git(root, "branch", "--show-current") or "unknown")
    head_sha = str(pr.get("head_sha") or "") or (_git(root, "rev-parse", "HEAD") or "unknown")
    active_plans = sorted(
        path.relative_to(root).as_posix()
        for path in (root / "docs/plans/active").glob("*.md")
    )

    normalized_checks = sorted(
        [
            {
                "name": str(check.get("name") or "unnamed"),
                "status": str(check.get("status") or "unknown"),
                "conclusion": check.get("conclusion"),
                "url": check.get("url"),
            }
            for check in checks
        ],
        key=lambda item: item["name"],
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at or datetime.now(UTC).isoformat(),
        "repository": str(pr.get("repository") or "local"),
        "pull_request": {
            "number": pr.get("number"),
            "title": pr.get("title"),
            "url": pr.get("url"),
            "base": base_branch,
            "head": head_branch,
            "head_sha": head_sha,
            "draft": draft,
        },
        "lifecycle_stage": stage,
        "latest_commit": _git(root, "log", "-1", "--oneline") or "unavailable",
        "changed_files": _changed_files(root, base_branch),
        "active_plans": active_plans,
        "current_state_path": ".ai/current-state.md" if (root / ".ai/current-state.md").exists() else None,
        "checks": normalized_checks,
        "next_actions": recommended_actions(stage, normalized_checks),
    }


def render_handoff_markdown(handoff: dict[str, Any]) -> str:
    pr = handoff["pull_request"]
    lines = [
        HANDOFF_MARKER,
        "# Automated Agent Handoff",
        "",
        f"- Repository: `{handoff['repository']}`",
        f"- PR: #{pr.get('number') or 'local'} — {pr.get('title') or 'local working session'}",
        f"- Branch: `{pr.get('head')}` → `{pr.get('base') or 'unknown'}`",
        f"- Head SHA: `{pr.get('head_sha')}`",
        f"- Lifecycle stage: **{handoff['lifecycle_stage']}**",
        f"- Draft: `{str(bool(pr.get('draft'))).lower()}`",
        f"- Generated: `{handoff['generated_at']}`",
        "",
        "## Active plans",
        "",
    ]
    plans = handoff.get("active_plans") or []
    lines.extend([f"- `{plan}`" for plan in plans] or ["- None detected."])

    lines.extend(("", "## Checks", ""))
    checks = handoff.get("checks") or []
    if checks:
        for check in checks:
            conclusion = check.get("conclusion") or "pending"
            lines.append(f"- `{check['name']}`: {check['status']} / {conclusion}")
    else:
        lines.append("- No check-run metadata supplied; inspect GitHub before making merge decisions.")

    lines.extend(("", "## Changed files", ""))
    changed = handoff.get("changed_files") or []
    lines.extend([f"- `{path}`" for path in changed[:50]] or ["- None detected."])
    if len(changed) > 50:
        lines.append(f"- ... and {len(changed) - 50} more.")

    lines.extend(("", "## Next actions", ""))
    lines.extend(f"{index}. {action}" for index, action in enumerate(handoff["next_actions"], start=1))
    lines.extend(
        (
            "",
            "## Resume rule",
            "",
            "Read `AGENTS.md`, the PR body and final diff, the active plan(s), current checks, and unresolved review threads before editing. Reconstruct context from repository/GitHub state first; do not ask the user to manually shuttle chat context when repository access is available.",
            "",
        )
    )
    return "\n".join(lines)


def write_handoff(
    root: Path,
    *,
    output_dir: Path | None = None,
    pr: dict[str, Any] | None = None,
    checks: list[dict[str, Any]] | None = None,
    generated_at: str | None = None,
) -> tuple[Path, Path]:
    root = root.resolve()
    output_dir = (output_dir or root / ".ai").resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = build_handoff(root, pr=pr, checks=checks, generated_at=generated_at)
    json_path = output_dir / "handoff.json"
    markdown_path = output_dir / "handoff.md"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(render_handoff_markdown(payload), encoding="utf-8")
    return json_path, markdown_path
