from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml


SCHEMA_VERSION = 1
REGISTRY_PATH = Path("knowledge/registry.json")
SOURCE_TYPES = {
    "peer_reviewed_primary",
    "official_methodology",
    "official_documentation",
    "working_paper_primary",
    "secondary_review",
}
REQUIRED_NOTE_HEADINGS = (
    "## What the evidence says",
    "## Project implication",
    "## What it does not establish",
    "## Sources",
)
_SOURCE_FILE_RE = re.compile(r"^(SRC-\d{4})-[a-z0-9][a-z0-9-]*\.yaml$")
_NOTE_FILE_RE = re.compile(r"^(KN-\d{4})-[a-z0-9][a-z0-9-]*\.md$")
_SOURCE_ID_RE = re.compile(r"^SRC-\d{4}$")
_NOTE_ID_RE = re.compile(r"^KN-\d{4}$")
_TOPIC_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_DOI_RE = re.compile(r"^10\.\S+?/\S+$")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: expected a mapping")
    return payload


def _nonempty_string(mapping: dict[str, Any], key: str, *, label: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label}: expected non-empty '{key}'")
    return value.strip()


def _string_list(mapping: dict[str, Any], key: str, *, label: str) -> list[str]:
    value = mapping.get(key)
    if not isinstance(value, list) or not value:
        raise ValueError(f"{label}: expected non-empty '{key}' list")
    cleaned: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{label}: '{key}' entries must be non-empty strings")
        cleaned.append(item.strip())
    if len(cleaned) != len(set(cleaned)):
        raise ValueError(f"{label}: '{key}' entries must be unique")
    return cleaned


def _topics(mapping: dict[str, Any], *, label: str) -> list[str]:
    topics = _string_list(mapping, "topics", label=label)
    invalid = [topic for topic in topics if _TOPIC_RE.fullmatch(topic) is None]
    if invalid:
        raise ValueError(f"{label}: invalid topic tags: {', '.join(invalid)}")
    return sorted(topics)


def _https_url(mapping: dict[str, Any], key: str, *, label: str) -> str:
    value = _nonempty_string(mapping, key, label=label)
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError(f"{label}: '{key}' must be a canonical HTTPS URL")
    return value


def _parse_front_matter(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise ValueError(f"{path}: note must begin with YAML front matter")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError(f"{path}: note front matter is not terminated") from exc
    metadata = yaml.safe_load("\n".join(lines[1:end])) or {}
    if not isinstance(metadata, dict):
        raise ValueError(f"{path}: note front matter must be a mapping")
    body = "\n".join(lines[end + 1 :]).strip() + "\n"
    return metadata, body


def _source_entry(path: Path, root: Path) -> dict[str, Any]:
    match = _SOURCE_FILE_RE.fullmatch(path.name)
    if match is None:
        raise ValueError(f"{path}: source filename must start with SRC-#### and use kebab-case")
    filename_id = match.group(1)
    payload = _load_yaml(path)
    label = str(path)

    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"{path}: unsupported source schema version")
    source_id = _nonempty_string(payload, "id", label=label)
    if _SOURCE_ID_RE.fullmatch(source_id) is None or source_id != filename_id:
        raise ValueError(f"{path}: source id must match filename id {filename_id}")
    title = _nonempty_string(payload, "title", label=label)
    authors = _string_list(payload, "authors", label=label)

    year = payload.get("year")
    if isinstance(year, bool) or not isinstance(year, int) or not 1800 <= year <= 2100:
        raise ValueError(f"{path}: 'year' must be an integer between 1800 and 2100")

    source_type = _nonempty_string(payload, "source_type", label=label)
    if source_type not in SOURCE_TYPES:
        raise ValueError(f"{path}: unsupported source_type '{source_type}'")
    publisher = _nonempty_string(payload, "publisher", label=label)
    publication = _nonempty_string(payload, "publication", label=label)
    url = _https_url(payload, "url", label=label)

    doi = payload.get("doi")
    if doi is not None:
        if not isinstance(doi, str) or _DOI_RE.fullmatch(doi.strip()) is None:
            raise ValueError(f"{path}: invalid DOI")
        doi = doi.strip()

    accessed_on = _nonempty_string(payload, "accessed_on", label=label)
    try:
        date.fromisoformat(accessed_on)
    except ValueError as exc:
        raise ValueError(f"{path}: accessed_on must be YYYY-MM-DD") from exc

    topics = _topics(payload, label=label)
    redistribution = payload.get("redistribution")
    if not isinstance(redistribution, dict):
        raise ValueError(f"{path}: expected 'redistribution' mapping")
    if redistribution.get("full_text_committed") is not False:
        raise ValueError(
            f"{path}: knowledge schema v1 requires redistribution.full_text_committed=false"
        )

    project_relevance = _nonempty_string(payload, "project_relevance", label=label)
    limitations = _string_list(payload, "limitations", label=label)

    return {
        "id": source_id,
        "title": title,
        "authors": authors,
        "year": year,
        "source_type": source_type,
        "publisher": publisher,
        "publication": publication,
        "doi": doi,
        "url": url,
        "accessed_on": accessed_on,
        "topics": topics,
        "full_text_committed": False,
        "project_relevance": project_relevance,
        "limitations": limitations,
        "path": path.relative_to(root).as_posix(),
        "sha256": _sha256(path),
    }


def _note_entry(path: Path, root: Path) -> tuple[dict[str, Any], str]:
    match = _NOTE_FILE_RE.fullmatch(path.name)
    if match is None:
        raise ValueError(f"{path}: note filename must start with KN-#### and use kebab-case")
    filename_id = match.group(1)
    metadata, body = _parse_front_matter(path)
    label = str(path)

    if metadata.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"{path}: unsupported note schema version")
    note_id = _nonempty_string(metadata, "id", label=label)
    if _NOTE_ID_RE.fullmatch(note_id) is None or note_id != filename_id:
        raise ValueError(f"{path}: note id must match filename id {filename_id}")
    title = _nonempty_string(metadata, "title", label=label)
    topics = _topics(metadata, label=label)
    source_ids = _string_list(metadata, "source_ids", label=label)
    invalid_sources = [item for item in source_ids if _SOURCE_ID_RE.fullmatch(item) is None]
    if invalid_sources:
        raise ValueError(f"{path}: invalid source ids: {', '.join(invalid_sources)}")
    status = _nonempty_string(metadata, "status", label=label)
    if status != "curated":
        raise ValueError(f"{path}: canonical knowledge notes must have status 'curated'")

    missing_headings = [heading for heading in REQUIRED_NOTE_HEADINGS if heading not in body.splitlines()]
    if missing_headings:
        raise ValueError(f"{path}: missing required headings: {', '.join(missing_headings)}")
    for source_id in source_ids:
        if f"`{source_id}`" not in body:
            raise ValueError(f"{path}: body must visibly cite {source_id}")

    return (
        {
            "id": note_id,
            "title": title,
            "topics": topics,
            "source_ids": sorted(source_ids),
            "status": status,
            "path": path.relative_to(root).as_posix(),
            "sha256": _sha256(path),
        },
        body,
    )


def build_registry(root: str | Path = ".") -> dict[str, Any]:
    root = Path(root).resolve()
    knowledge_root = root / "knowledge"
    sources_root = knowledge_root / "sources"
    notes_root = knowledge_root / "notes"
    policy_path = knowledge_root / "SOURCE_POLICY.md"
    readme_path = knowledge_root / "README.md"
    if not sources_root.is_dir() or not notes_root.is_dir():
        raise FileNotFoundError("repository must contain knowledge/sources/ and knowledge/notes/")
    if not policy_path.is_file() or not readme_path.is_file():
        raise FileNotFoundError("knowledge/README.md and knowledge/SOURCE_POLICY.md are required")

    source_paths = sorted(path for path in sources_root.rglob("*.yaml") if path.is_file())
    note_paths = sorted(path for path in notes_root.rglob("*.md") if path.is_file())
    if not source_paths:
        raise ValueError("knowledge base must contain at least one source")
    if not note_paths:
        raise ValueError("knowledge base must contain at least one note")

    sources = [_source_entry(path, root) for path in source_paths]
    source_ids = [entry["id"] for entry in sources]
    duplicate_sources = sorted({item for item in source_ids if source_ids.count(item) > 1})
    if duplicate_sources:
        raise ValueError(f"duplicate knowledge source ids: {', '.join(duplicate_sources)}")
    source_id_set = set(source_ids)

    notes: list[dict[str, Any]] = []
    for path in note_paths:
        entry, _ = _note_entry(path, root)
        unknown = sorted(set(entry["source_ids"]) - source_id_set)
        if unknown:
            raise ValueError(f"{path}: unknown source ids: {', '.join(unknown)}")
        notes.append(entry)

    note_ids = [entry["id"] for entry in notes]
    duplicate_notes = sorted({item for item in note_ids if note_ids.count(item) > 1})
    if duplicate_notes:
        raise ValueError(f"duplicate knowledge note ids: {', '.join(duplicate_notes)}")

    backlinks: dict[str, list[str]] = {source_id: [] for source_id in source_ids}
    for note in notes:
        for source_id in note["source_ids"]:
            backlinks[source_id].append(note["id"])

    for source in sources:
        source["cited_by_note_ids"] = sorted(backlinks[source["id"]])

    sources.sort(key=lambda entry: entry["id"])
    notes.sort(key=lambda entry: entry["id"])
    return {
        "schema_version": SCHEMA_VERSION,
        "policy": {
            "path": policy_path.relative_to(root).as_posix(),
            "sha256": _sha256(policy_path),
        },
        "sources": sources,
        "notes": notes,
    }


def registry_bytes(root: str | Path = ".") -> bytes:
    payload = build_registry(root)
    return (json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")


def write_registry(root: str | Path = ".") -> Path:
    root = Path(root).resolve()
    path = root / REGISTRY_PATH
    path.write_bytes(registry_bytes(root))
    return path


def check_registry(root: str | Path = ".") -> Path:
    root = Path(root).resolve()
    path = root / REGISTRY_PATH
    expected = registry_bytes(root)
    if not path.is_file():
        raise RuntimeError(f"missing generated knowledge registry: {REGISTRY_PATH}")
    if path.read_bytes() != expected:
        raise RuntimeError(f"stale knowledge registry: run swing-knowledge-registry --root {root}")
    return path
