# Keep Derived Repository Indexes Regenerable

## Problem

A repository can accumulate canonical records plus a manually maintained index of those records. Once the index starts carrying copied metadata, it can silently drift and become a competing source of truth.

## Root cause

The index mixes two responsibilities: durable domain meaning and mechanical discovery/provenance. Human-authored interpretation cannot be safely regenerated, while identity, paths, content digests, and already-recorded provenance can.

## Solution

Keep the domain records canonical and make the machine index fully derived:

1. discover canonical records from repository structure;
2. validate cross-file identity and required durable files before rendering;
3. normalize only provenance that already exists in canonical records, including supported legacy layouts;
4. fingerprint exact canonical bytes where integrity matters;
5. render deterministically with stable ordering and no generation timestamp;
6. version the generated index for review and discovery;
7. provide a `--check` mode that compares expected bytes with the committed file;
8. make CI regenerate the index and fail on both modified and newly generated/untracked output.

The generated index should never invent research conclusions or other domain meaning absent from canonical records.

## Why `git diff` alone is insufficient

A first-time generated file is untracked, so `git diff --exit-code -- path` can report success even though the committed index is missing. A CI gate that regenerates a versioned derived file should also inspect repository status (for example `git status --porcelain -- path`) or use an equivalent check that includes untracked files.

## Compatibility boundary

Existing durable records may have evolved schemas. A derived index should normalize explicitly supported legacy layouts and fail when two recognized representations conflict, rather than forcing historical records to be rewritten merely to satisfy the index.

## Tests / checks

- repeated generation produces byte-identical output;
- missing/stale committed output fails check mode;
- directory/config/result identity mismatches fail;
- duplicate ids fail;
- missing required canonical files fail;
- supported provenance layouts normalize to the same registry fields;
- conflicting recognized provenance fails;
- exact protocol bytes are checked against preregistered locks;
- CI catches an untracked generated index.

## Applicability

Use this pattern for repository catalogs, manifests, generated indexes, or provenance summaries whose contents are mechanically recoverable from canonical files. Do not use it to generate away human judgment, research interpretation, or decisions that require review.
