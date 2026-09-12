# Design Plan — Persistent Daily Scan History

Status: Completed on merge

## Problem

The scanner previously printed only the latest ranking to stdout. There was no durable, provenance-preserving record of what the operational scanner actually observed on a given day, so later review could not distinguish contemporaneous WATCH/BUY outputs from a reconstruction using revised provider history.

## Goals

- Preserve one canonical daily scanner observation after the relevant completed bars are available.
- Record the exact normalized provider state needed to reproduce the scan, not only rendered scores.
- Keep observation dates current-clock-derived in production; no arbitrary historical backfill argument.
- Fingerprint config, code, runtime, source data, and rendered scan rows.
- Make output deterministic for a fixed observation clock and source snapshot.
- Prevent same-date overwrite; missed dates remain explicit gaps.
- Provide a scheduled/manual GitHub Actions publication path with durable append-only-by-convention release assets.
- Keep this operational scan history separate from `PROSPECTIVE-v1-holdout` evidence and validation.

## Non-goals

- No order placement or paper/live broker integration.
- No strategy tuning or validation claims.
- No replacement for the prospective holdout recorder/evaluator.
- No reconstruction/backfill of missed operational scan dates from later provider state.
- No database in the first version.

## Implemented design

For observation date `D`, the recorder downloads the configured assets plus unique benchmarks exactly once with an exclusive provider cutoff at `D`. It stores the exact universe config, normalized source CSVs, deterministic scan-result JSON/CSV, and a manifest containing observation/cutoff, config SHA, code SHA, runtime/provider metadata, per-source SHA/coverage, and output SHA.

The scanner exposes `scan_frames` so the captured frames are the same frames scored by the operational rules. The archive filename includes the full archive SHA-256 and uses fixed ZIP metadata/order. Production CLI derives `D` from current UTC time and exposes no date override; tests inject a fixed clock through the Python API.

## Publication

The dedicated yearly GitHub Release namespace is `daily-scan-history-YYYY`. The scheduled/manual workflow checks for an existing date-prefixed asset and skips rather than overwrites it. A workflow artifact retains a short-lived copy for debugging.

## Research boundary

Daily scan history is contemporaneous operational evidence, not the preregistered v1 validation holdout. Its manifest explicitly marks `validation_evidence` and `holdout_substitution_allowed` false. Holdout evidence retains its byte-locked protocol, fixed universe, separate release/archive chain, and dedicated evaluator.

## Simplify outcome

The holdout recorder remained protocol-specific. No shared recorder framework was introduced because sharing evidence orchestration would blur the inference boundary. Reuse is limited to the scanner's deterministic scoring semantics through the small `scan_frames` interface.

## Compound outcome

Created `docs/solutions/engineering/separate-operational-observations-from-validation-evidence.md`: provenance integrity and preregistration answer different questions, so operational and validation streams need separate namespaces, consumers, and explicit evidence eligibility even when they share hashing/no-backfill techniques.

## Validation

- focused synthetic daily-scan recorder tests pass;
- full `pytest -q` and `ruff check src tests` pass on the implemented code;
- tests verify 12 unique provider reads for the current 11-asset universe plus QQQ benchmark;
- exclusive cutoff/no production backfill argument is enforced;
- fixed inputs produce deterministic archive bytes;
- same-date capture is refused and publication skips existing date assets;
- archive verifier covers archive/config/source/output fingerprints and row/cutoff metadata;
- final-head CI and formal diff review are required immediately before merge.
