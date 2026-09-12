from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, date, datetime
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
NEWS_SOURCE_TYPES = {
    "official_filing",
    "official_company_release",
    "regulator_release",
    "exchange_release",
    "primary_news",
    "secondary_news",
}
NEWS_RETRIEVAL_METHODS = {"web", "api", "manual"}
NEWS_STATUSES = {"observed", "corrected", "retracted"}
REQUIRED_NOTE_HEADINGS = (
    "## What the evidence says",
    "## Project implication",
    "## What it does not establish",
    "## Sources",
)
_SOURCE_FILE_RE = re.compile(r"^(SRC-\d{4})-[a-z0-9][a-z0-9-]*\.yaml$")
_NEWS_FILE_RE = re.compile(r"^(NEWS-(\d{8})-\d{4})-[a-z0-9][a-z0-9-]*\.yaml$")
_NOTE_FILE_RE = re.compile(r"^(KN-\d{4})-[a-z0-9][a-z0-9-]*\.md$")
_SOURCE_ID_RE = re.compile(r"^SRC-\d{4}$")
_NEWS_ID_RE = re.compile(r"^NEWS-\d{8}-\d{4}$")
_NOTE_ID_RE = re.compile(r"^KN-\d{4}$")
_TOPIC_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_DOI_RE = re.compile(r"^10\.\S+?/\S+$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_UTC_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


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


def _optional_string_list(mapping: dict[str, Any], key: str, *, label: str) -> list[str]:
    value = mapping.get(key)
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{label}: '{key}' must be a list when present")
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


def _iso_date(mapping: dict[str, Any], key: str, *, label: str) -> str:
    value = mapping.get(key)
    if isinstance(value, datetime):
        raise ValueError(f"{label}: '{key}' must be a date, not a timestamp")
    if isinstance(value, date):
        return value.isoformat()
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label}: expected non-empty '{key}'")
    cleaned = value.strip()
    try:
        return date.fromisoformat(cleaned).isoformat()
    except ValueError as exc:
        raise ValueError(f"{label}: {key} must be YYYY-MM-DD") from exc


def _utc_timestamp(mapping: dict[str, Any], key: str, *, label: str) -> tuple[str, datetime]:
    value = mapping.get(key)
    if isinstance(value, datetime):
        timestamp = value
        if timestamp.microsecond:
            raise ValueError(f"{label}: '{key}' must use whole-second UTC precision")
    elif isinstance(value, str) and _UTC_TIMESTAMP_RE.fullmatch(value.strip()):
        timestamp = datetime.strptime(value.strip(), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    else:
        raise ValueError(f"{label}: '{key}' must be an ISO-8601 UTC timestamp ending in Z")

    if timestamp.tzinfo is None or timestamp.utcoffset() != UTC.utcoffset(timestamp):
        raise ValueError(f"{label}: '{key}' must be UTC")
    normalized = timestamp.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    return normalized, timestamp.astimezone(UTC)


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

    accessed_on = _iso_date(payload, "accessed_on", label=label)
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


def _claims(payload: dict[str, Any], *, label: str) -> list[dict[str, str]]:
    value = payload.get("claims")
    if not isinstance(value, list) or not value:
        raise ValueError(f"{label}: expected non-empty 'claims' list")
    claims: list[dict[str, str]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise ValueError(f"{label}: claims[{index}] must be a mapping")
        statement = _nonempty_string(item, "statement", label=f"{label} claims[{index}]")
        attribution = _nonempty_string(item, "attribution", label=f"{label} claims[{index}]")
        claims.append({"statement": statement, "attribution": attribution})
    return claims


def _news_entry(path: Path, root: Path) -> dict[str, Any]:
    match = _NEWS_FILE_RE.fullmatch(path.name)
    if match is None:
        raise ValueError(
            f"{path}: news filename must start with NEWS-YYYYMMDD-NNNN and use kebab-case"
        )
    filename_id, filename_date = match.groups()
    payload = _load_yaml(path)
    label = str(path)

    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"{path}: unsupported news schema version")
    news_id = _nonempty_string(payload, "id", label=label)
    if _NEWS_ID_RE.fullmatch(news_id) is None or news_id != filename_id:
        raise ValueError(f"{path}: news id must match filename id {filename_id}")

    title = _nonempty_string(payload, "title", label=label)
    canonical_url = _https_url(payload, "canonical_url", label=label)
    publisher = _nonempty_string(payload, "publisher", label=label)
    source_type = _nonempty_string(payload, "source_type", label=label)
    if source_type not in NEWS_SOURCE_TYPES:
        raise ValueError(f"{path}: unsupported news source_type '{source_type}'")

    published_at, published_dt = _utc_timestamp(payload, "published_at", label=label)
    retrieved_at, retrieved_dt = _utc_timestamp(payload, "retrieved_at", label=label)
    if retrieved_dt < published_dt:
        raise ValueError(f"{path}: retrieved_at cannot precede published_at")
    if published_dt.strftime("%Y%m%d") != filename_date:
        raise ValueError(f"{path}: news id date must equal published_at UTC date")

    entities = sorted(_string_list(payload, "entities", label=label))
    topics = _topics(payload, label=label)

    provenance = payload.get("provenance")
    if not isinstance(provenance, dict):
        raise ValueError(f"{path}: expected 'provenance' mapping")
    retrieval_method = _nonempty_string(provenance, "retrieval_method", label=label)
    if retrieval_method not in NEWS_RETRIEVAL_METHODS:
        raise ValueError(f"{path}: unsupported retrieval_method '{retrieval_method}'")
    content_sha256 = _nonempty_string(provenance, "observed_content_sha256", label=label)
    if _SHA256_RE.fullmatch(content_sha256) is None:
        raise ValueError(f"{path}: observed_content_sha256 must be a lowercase SHA-256 digest")

    rights = payload.get("rights")
    if not isinstance(rights, dict):
        raise ValueError(f"{path}: expected 'rights' mapping")
    if rights.get("full_text_committed") is not False:
        raise ValueError(f"{path}: news schema v1 requires rights.full_text_committed=false")

    summary = _nonempty_string(payload, "summary", label=label)
    claims = _claims(payload, label=label)
    status = _nonempty_string(payload, "status", label=label)
    if status not in NEWS_STATUSES:
        raise ValueError(f"{path}: unsupported news status '{status}'")

    return {
        "id": news_id,
        "title": title,
        "canonical_url": canonical_url,
        "publisher": publisher,
        "source_type": source_type,
        "published_at": published_at,
        "retrieved_at": retrieved_at,
        "entities": entities,
        "topics": topics,
        "retrieval_method": retrieval_method,
        "observed_content_sha256": content_sha256,
        "full_text_committed": False,
        "summary": summary,
        "claims": claims,
        "status": status,
        "evidence_class": "time_bounded_context",
        "validation_evidence": False,
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
    source_ids = _optional_string_list(metadata, "source_ids", label=label)
    news_ids = _optional_string_list(metadata, "news_ids", label=label)
    if not source_ids and not news_ids:
        raise ValueError(f"{path}: note must cite at least one source_id or news_id")

    invalid_sources = [item for item in source_ids if _SOURCE_ID_RE.fullmatch(item) is None]
    if invalid_sources:
        raise ValueError(f"{path}: invalid source ids: {', '.join(invalid_sources)}")
    invalid_news = [item for item in news_ids if _NEWS_ID_RE.fullmatch(item) is None]
    if invalid_news:
        raise ValueError(f"{path}: invalid news ids: {', '.join(invalid_news)}")

    status = _nonempty_string(metadata, "status", label=label)
    if status != "curated":
        raise ValueError(f"{path}: canonical knowledge notes must have status 'curated'")

    missing_headings = [heading for heading in REQUIRED_NOTE_HEADINGS if heading not in body.splitlines()]
    if missing_headings:
        raise ValueError(f"{path}: missing required headings: {', '.join(missing_headings)}")
    for reference_id in [*source_ids, *news_ids]:
        if f"`{reference_id}`" not in body:
            raise ValueError(f"{path}: body must visibly cite {reference_id}")

    return (
        {
            "id": note_id,
            "title": title,
            "topics": topics,
            "source_ids": sorted(source_ids),
            "news_ids": sorted(news_ids),
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
    news_root = knowledge_root / "news"
    notes_root = knowledge_root / "notes"
    policy_path = knowledge_root / "SOURCE_POLICY.md"
    readme_path = knowledge_root / "README.md"
    news_readme_path = news_root / "README.md"
    if not sources_root.is_dir() or not news_root.is_dir() or not notes_root.is_dir():
        raise FileNotFoundError(
            "repository must contain knowledge/sources/, knowledge/news/, and knowledge/notes/"
        )
    if not policy_path.is_file() or not readme_path.is_file() or not news_readme_path.is_file():
        raise FileNotFoundError(
            "knowledge/README.md, knowledge/SOURCE_POLICY.md, and knowledge/news/README.md are required"
        )

    source_paths = sorted(path for path in sources_root.rglob("*.yaml") if path.is_file())
    news_paths = sorted(path for path in news_root.rglob("*.yaml") if path.is_file())
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

    news = [_news_entry(path, root) for path in news_paths]
    news_ids = [entry["id"] for entry in news]
    duplicate_news = sorted({item for item in news_ids if news_ids.count(item) > 1})
    if duplicate_news:
        raise ValueError(f"duplicate knowledge news ids: {', '.join(duplicate_news)}")
    news_id_set = set(news_ids)

    notes: list[dict[str, Any]] = []
    for path in note_paths:
        entry, _ = _note_entry(path, root)
        unknown_sources = sorted(set(entry["source_ids"]) - source_id_set)
        if unknown_sources:
            raise ValueError(f"{path}: unknown source ids: {', '.join(unknown_sources)}")
        unknown_news = sorted(set(entry["news_ids"]) - news_id_set)
        if unknown_news:
            raise ValueError(f"{path}: unknown news ids: {', '.join(unknown_news)}")
        notes.append(entry)

    note_ids = [entry["id"] for entry in notes]
    duplicate_notes = sorted({item for item in note_ids if note_ids.count(item) > 1})
    if duplicate_notes:
        raise ValueError(f"duplicate knowledge note ids: {', '.join(duplicate_notes)}")

    source_backlinks: dict[str, list[str]] = {source_id: [] for source_id in source_ids}
    news_backlinks: dict[str, list[str]] = {news_id: [] for news_id in news_ids}
    for note in notes:
        for source_id in note["source_ids"]:
            source_backlinks[source_id].append(note["id"])
        for news_id in note["news_ids"]:
            news_backlinks[news_id].append(note["id"])

    for source in sources:
        source["cited_by_note_ids"] = sorted(source_backlinks[source["id"]])
    for observation in news:
        observation["cited_by_note_ids"] = sorted(news_backlinks[observation["id"]])

    sources.sort(key=lambda entry: entry["id"])
    news.sort(key=lambda entry: (entry["published_at"], entry["id"]))
    notes.sort(key=lambda entry: entry["id"])
    return {
        "schema_version": SCHEMA_VERSION,
        "policy": {
            "path": policy_path.relative_to(root).as_posix(),
            "sha256": _sha256(policy_path),
        },
        "sources": sources,
        "news_observations": news,
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
