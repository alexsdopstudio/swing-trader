from __future__ import annotations

import subprocess
from pathlib import Path

MEMORY_FILES = (
    "AGENTS.md",
    "ARCHITECTURE.md",
    ".ai/current-state.md",
    "docs/product/strategy-v1.md",
    "docs/domain/risk-model.md",
    "docs/roadmap.md",
)


def _read_if_present(root: Path, relative_path: str) -> str:
    path = root / relative_path
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


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
    return result.stdout.strip() or "clean"


def build_context(root: Path) -> str:
    root = root.resolve()
    sections = [
        "# AI Working Context",
        "",
        "## Git",
        f"- branch: {_git(root, 'branch', '--show-current')}",
        f"- latest commit: {_git(root, 'log', '-1', '--oneline')}",
        "- changed files:",
        "```text",
        _git(root, "status", "--short"),
        "```",
    ]

    for relative_path in MEMORY_FILES:
        content = _read_if_present(root, relative_path)
        if content:
            sections.extend(("", f"## Source: `{relative_path}`", "", content))

    active_plans = sorted((root / "docs/plans/active").glob("*.md"))
    for plan in active_plans:
        relative = plan.relative_to(root).as_posix()
        sections.extend(("", f"## Active plan: `{relative}`", "", plan.read_text(encoding="utf-8").strip()))

    sections.extend(
        (
            "",
            "## Instruction",
            "Treat repository files as the source of truth. Inspect implementation and tests before editing, and update durable memory when decisions change.",
            "",
        )
    )
    return "\n".join(sections)


def write_context(root: Path, output: Path | None = None) -> Path:
    root = root.resolve()
    output = output or root / ".ai/context.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build_context(root), encoding="utf-8")
    return output
