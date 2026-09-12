from __future__ import annotations

from pathlib import Path

import pytest

from swing_trader.knowledge_registry import (
    build_registry,
    check_registry,
    registry_bytes,
    write_registry,
)


SOURCE_TEMPLATE = """\
schema_version: 1
id: {source_id}
title: Test source
authors:
  - Test Author
year: 2020
source_type: peer_reviewed_primary
publisher: Test Publisher
publication: Test Journal
url: https://example.com/{source_id}
accessed_on: 2026-09-13
topics:
  - backtesting
redistribution:
  full_text_committed: {full_text_committed}
project_relevance: >-
  Test relevance for registry validation.
limitations:
  - Test limitation.
"""

NOTE_TEMPLATE = """\
---
schema_version: 1
id: {note_id}
title: Test note
topics:
  - backtesting
source_ids:
  - {source_id}
status: curated
---

# Test note

## What the evidence says

`{source_id}` supports a test proposition.

## Project implication

Use the proposition only as an external research input.

{non_conclusion_heading}

It does not validate Swing Trader.

## Sources

- `{source_id}` — test source.
"""


def _write_knowledge_root(root: Path) -> tuple[Path, Path]:
    sources = root / "knowledge" / "sources"
    notes = root / "knowledge" / "notes"
    sources.mkdir(parents=True)
    notes.mkdir(parents=True)
    (root / "knowledge" / "README.md").write_text("# Knowledge\n", encoding="utf-8")
    (root / "knowledge" / "SOURCE_POLICY.md").write_text("# Policy\n", encoding="utf-8")
    source_path = sources / "SRC-0001-test.yaml"
    source_path.write_text(
        SOURCE_TEMPLATE.format(source_id="SRC-0001", full_text_committed="false"),
        encoding="utf-8",
    )
    note_path = notes / "KN-0001-test.md"
    note_path.write_text(
        NOTE_TEMPLATE.format(
            note_id="KN-0001",
            source_id="SRC-0001",
            non_conclusion_heading="## What it does not establish",
        ),
        encoding="utf-8",
    )
    return source_path, note_path


def test_registry_is_deterministic_and_detects_stale_content(tmp_path: Path) -> None:
    _, note_path = _write_knowledge_root(tmp_path)

    first = registry_bytes(tmp_path)
    second = registry_bytes(tmp_path)
    assert first == second

    registry_path = write_registry(tmp_path)
    assert registry_path.read_bytes() == first
    assert check_registry(tmp_path) == registry_path

    note_path.write_text(note_path.read_text(encoding="utf-8") + "\nNew interpretation.\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="stale knowledge registry"):
        check_registry(tmp_path)


def test_registry_normalizes_yaml_date_and_builds_backlinks(tmp_path: Path) -> None:
    _write_knowledge_root(tmp_path)

    registry = build_registry(tmp_path)

    assert registry["sources"][0]["accessed_on"] == "2026-09-13"
    assert registry["sources"][0]["cited_by_note_ids"] == ["KN-0001"]
    assert registry["notes"][0]["source_ids"] == ["SRC-0001"]


def test_duplicate_source_ids_are_rejected(tmp_path: Path) -> None:
    _write_knowledge_root(tmp_path)
    duplicate = tmp_path / "knowledge" / "sources" / "SRC-0001-duplicate.yaml"
    duplicate.write_text(
        SOURCE_TEMPLATE.format(source_id="SRC-0001", full_text_committed="false"),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="duplicate knowledge source ids"):
        build_registry(tmp_path)


def test_unknown_source_reference_is_rejected(tmp_path: Path) -> None:
    _, note_path = _write_knowledge_root(tmp_path)
    note_path.write_text(
        NOTE_TEMPLATE.format(
            note_id="KN-0001",
            source_id="SRC-9999",
            non_conclusion_heading="## What it does not establish",
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unknown source ids: SRC-9999"):
        build_registry(tmp_path)


def test_missing_inference_boundary_section_is_rejected(tmp_path: Path) -> None:
    _, note_path = _write_knowledge_root(tmp_path)
    note_path.write_text(
        NOTE_TEMPLATE.format(
            note_id="KN-0001",
            source_id="SRC-0001",
            non_conclusion_heading="## Limitations",
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="What it does not establish"):
        build_registry(tmp_path)


def test_committed_full_text_is_rejected_by_v1_policy(tmp_path: Path) -> None:
    source_path, _ = _write_knowledge_root(tmp_path)
    source_path.write_text(
        SOURCE_TEMPLATE.format(source_id="SRC-0001", full_text_committed="true"),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="full_text_committed=false"):
        build_registry(tmp_path)


def test_non_https_canonical_source_is_rejected(tmp_path: Path) -> None:
    source_path, _ = _write_knowledge_root(tmp_path)
    source_path.write_text(
        SOURCE_TEMPLATE.format(source_id="SRC-0001", full_text_committed="false").replace(
            "https://example.com", "http://example.com"
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="canonical HTTPS URL"):
        build_registry(tmp_path)


def test_committed_repository_registry_is_current() -> None:
    root = Path(__file__).resolve().parents[1]
    assert check_registry(root) == root / "knowledge" / "registry.json"
