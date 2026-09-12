from pathlib import Path

from swing_trader.context_builder import build_context, write_context


def test_build_context_includes_memory_and_active_plan(tmp_path: Path) -> None:
    (tmp_path / ".ai").mkdir()
    (tmp_path / "docs/plans/active").mkdir(parents=True)
    (tmp_path / "AGENTS.md").write_text("agent rules", encoding="utf-8")
    (tmp_path / ".ai/current-state.md").write_text("current state", encoding="utf-8")
    (tmp_path / "docs/plans/active/test.md").write_text("active plan", encoding="utf-8")

    context = build_context(tmp_path)

    assert "agent rules" in context
    assert "current state" in context
    assert "active plan" in context


def test_write_context_creates_generated_file(tmp_path: Path) -> None:
    output = write_context(tmp_path)

    assert output == tmp_path / ".ai/context.md"
    assert output.exists()
    assert "# AI Working Context" in output.read_text(encoding="utf-8")
