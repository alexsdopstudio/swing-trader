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

NEWS_TEMPLATE = """\
schema_version: 1
id: {news_id}
title: Test issuer announcement
canonical_url: {canonical_url}
publisher: Test Issuer
source_type: {source_type}
published_at: "{published_at}"
retrieved_at: "{retrieved_at}"
entities:
  - TEST
topics:
  - earnings
provenance:
  retrieval_method: web
  observed_content_sha256: {content_sha256}
rights:
  full_text_committed: {full_text_committed}
summary: >-
  Project-authored summary of the observed event.
claims:
  - statement: Test issuer reported a test event.
    attribution: Test Issuer
status: observed
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

NEWS_NOTE_TEMPLATE = """\
---
schema_version: 1
id: KN-0002
title: Test event note
topics:
  - earnings
news_ids:
  - {news_id}
status: curated
---

# Test event note

## What the evidence says

`{news_id}` records a time-bounded observation.

## Project implication

Treat the observation as catalyst context only.

## What it does not establish

The observation does not validate Swing Trader or change deterministic risk rules.

## Sources

- `{news_id}` — observed event record.
"""


def _write_knowledge_root(root: Path) -> tuple[Path, Path]:
    sources = root / "knowledge" / "sources"
    news = root / "knowledge" / "news"
    notes = root / "knowledge" / "notes"
    sources.mkdir(parents=True)
    news.mkdir(parents=True)
    notes.mkdir(parents=True)
    (root / "knowledge" / "README.md").write_text("# Knowledge\n", encoding="utf-8")
    (root / "knowledge" / "SOURCE_POLICY.md").write_text("# Policy\n", encoding="utf-8")
    (news / "README.md").write_text("# News observations\n", encoding="utf-8")
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


def _write_news(root: Path, *, news_id: str = "NEWS-20260913-0001", **overrides: str) -> Path:
    values = {
        "news_id": news_id,
        "canonical_url": "https://example.com/news/test",
        "source_type": "official_company_release",
        "published_at": "2026-09-13T14:32:00Z",
        "retrieved_at": "2026-09-13T14:41:17Z",
        "content_sha256": "0" * 64,
        "full_text_committed": "false",
    }
    values.update(overrides)
    path = root / "knowledge" / "news" / f"{news_id}-test-event.yaml"
    path.write_text(NEWS_TEMPLATE.format(**values), encoding="utf-8")
    return path


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
    assert registry["news_observations"] == []
    assert registry["notes"][0]["source_ids"] == ["SRC-0001"]
    assert registry["notes"][0]["news_ids"] == []


def test_news_observation_is_indexed_and_can_backlink_to_note(tmp_path: Path) -> None:
    _write_knowledge_root(tmp_path)
    _write_news(tmp_path)
    note_path = tmp_path / "knowledge" / "notes" / "KN-0002-test-event.md"
    note_path.write_text(
        NEWS_NOTE_TEMPLATE.format(news_id="NEWS-20260913-0001"), encoding="utf-8"
    )

    registry = build_registry(tmp_path)
    observation = registry["news_observations"][0]

    assert observation["id"] == "NEWS-20260913-0001"
    assert observation["published_at"] == "2026-09-13T14:32:00Z"
    assert observation["retrieved_at"] == "2026-09-13T14:41:17Z"
    assert observation["entities"] == ["TEST"]
    assert observation["cited_by_note_ids"] == ["KN-0002"]
    assert observation["evidence_class"] == "time_bounded_context"
    assert observation["validation_evidence"] is False
    assert registry["notes"][1]["source_ids"] == []
    assert registry["notes"][1]["news_ids"] == ["NEWS-20260913-0001"]


def test_news_retrieval_cannot_precede_publication(tmp_path: Path) -> None:
    _write_knowledge_root(tmp_path)
    _write_news(tmp_path, retrieved_at="2026-09-13T14:31:59Z")

    with pytest.raises(ValueError, match="retrieved_at cannot precede published_at"):
        build_registry(tmp_path)


def test_news_id_date_must_match_publication_date(tmp_path: Path) -> None:
    _write_knowledge_root(tmp_path)
    _write_news(tmp_path, published_at="2026-09-12T23:59:59Z")

    with pytest.raises(ValueError, match="news id date must equal published_at UTC date"):
        build_registry(tmp_path)


def test_news_requires_supported_source_type_and_fingerprint(tmp_path: Path) -> None:
    _write_knowledge_root(tmp_path)
    news_path = _write_news(tmp_path, source_type="random_blog")

    with pytest.raises(ValueError, match="unsupported news source_type"):
        build_registry(tmp_path)

    news_path.write_text(
        NEWS_TEMPLATE.format(
            news_id="NEWS-20260913-0001",
            canonical_url="https://example.com/news/test",
            source_type="primary_news",
            published_at="2026-09-13T14:32:00Z",
            retrieved_at="2026-09-13T14:41:17Z",
            content_sha256="not-a-digest",
            full_text_committed="false",
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="observed_content_sha256"):
        build_registry(tmp_path)


def test_duplicate_news_ids_are_rejected(tmp_path: Path) -> None:
    _write_knowledge_root(tmp_path)
    _write_news(tmp_path)
    duplicate = tmp_path / "knowledge" / "news" / "NEWS-20260913-0001-duplicate-event.yaml"
    duplicate.write_text(
        NEWS_TEMPLATE.format(
            news_id="NEWS-20260913-0001",
            canonical_url="https://example.com/news/duplicate",
            source_type="primary_news",
            published_at="2026-09-13T15:00:00Z",
            retrieved_at="2026-09-13T15:01:00Z",
            content_sha256="1" * 64,
            full_text_committed="false",
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="duplicate knowledge news ids"):
        build_registry(tmp_path)


def test_unknown_news_reference_is_rejected(tmp_path: Path) -> None:
    _write_knowledge_root(tmp_path)
    note_path = tmp_path / "knowledge" / "notes" / "KN-0002-test-event.md"
    note_path.write_text(
        NEWS_NOTE_TEMPLATE.format(news_id="NEWS-20260913-9999"), encoding="utf-8"
    )

    with pytest.raises(ValueError, match="unknown news ids: NEWS-20260913-9999"):
        build_registry(tmp_path)


def test_news_full_text_commit_is_rejected(tmp_path: Path) -> None:
    _write_knowledge_root(tmp_path)
    _write_news(tmp_path, full_text_committed="true")

    with pytest.raises(ValueError, match="rights.full_text_committed=false"):
        build_registry(tmp_path)


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
