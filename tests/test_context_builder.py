from pathlib import Path

from swing_trader.context_builder import build_context, write_context


def test_build_context_includes_memory_plan_solution_index_and_handoff(tmp_path: Path) -> None:
    (tmp_path / ".ai").mkdir()
    (tmp_path / "docs/plans/active").mkdir(parents=True)
    (tmp_path / "docs/solutions").mkdir(parents=True)
    (tmp_path / "AGENTS.md").write_text("agent rules", encoding="utf-8")
    (tmp_path / ".ai/current-state.md").write_text("current state", encoding="utf-8")
    (tmp_path / ".ai/handoff.md").write_text("handoff checkpoint", encoding="utf-8")
    (tmp_path / "docs/plans/active/test.md").write_text("active plan", encoding="utf-8")
    (tmp_path / "docs/solutions/README.md").write_text(
        "reusable solution index", encoding="utf-8"
    )

    context = build_context(tmp_path)

    assert "agent rules" in context
    assert "current state" in context
    assert "handoff checkpoint" in context
    assert "active plan" in context
    assert "reusable solution index" in context


def test_write_context_creates_generated_file(tmp_path: Path) -> None:
    output = write_context(tmp_path)

    assert output == tmp_path / ".ai/context.md"
    assert output.exists()
    assert "# AI Working Context" in output.read_text(encoding="utf-8")
