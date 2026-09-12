# Design Plan — Persistent Daily Scan History

Status: Active

## Problem

The scanner currently prints only the latest ranking to stdout. There is no durable, provenance-preserving record of what the operational scanner actually observed on a given day, so later review cannot distinguish contemporaneous WATCH/BUY outputs from a reconstruction using revised provider history.

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

## Proposed evidence model

For observation date `D`, download the configured assets plus unique benchmarks with an exclusive provider cutoff at `D`. Store the exact universe config, normalized source CSVs, deterministic scan-result JSON/CSV, and a manifest containing observation/cutoff, config SHA, code SHA, runtime/provider metadata, per-source SHA/coverage, and output SHA.

The archive filename includes the full archive SHA-256 and uses fixed ZIP metadata/order. Production CLI derives `D` from current UTC time and exposes no date override. Tests may inject a clock through the Python API.

## Publication

Use a dedicated yearly GitHub Release such as `daily-scan-history-2026`. Scheduled/manual workflow checks for an existing date-prefixed asset and skips rather than overwrites it. Release publication is durable operational memory, while Actions artifacts may retain a short-lived copy for debugging.

## Research boundary

Daily scan history is contemporaneous operational evidence, but it is not the preregistered v1 validation holdout. Holdout evidence continues to use its byte-locked protocol, fixed four-symbol universe plus QQQ benchmark, and separate release/archive chain. Scan history may cover the broader configured universe and must never be substituted into the holdout evaluator.

## Implementation plan

- Refactor scanner scoring so already-captured frames can be scored without a second provider read.
- Download configured assets and benchmarks exactly once per unique symbol.
- Add a daily recorder with exact captured config, normalized source data, deterministic outputs, manifest, and archive verification.
- Add a production CLI with no historical observation-date option.
- Add focused synthetic tests for cutoff, source deduplication, determinism, overwrite refusal, and archive verification.
- Add a read-only PR validation job plus scheduled/manual publication job.
- Document operational/research separation and update current-state/roadmap.

## Simplify

Keep the holdout recorder protocol-specific rather than introducing a shared abstraction that could blur evidence boundaries. Reuse the scanner's scoring semantics through a small `scan_frames` interface and keep the operational archive implementation explicit.

## Compound

Capture the reusable distinction between operational observations and preregistered validation evidence in durable project memory before final review.

## Validation plan

- full pytest/Ruff;
- focused recorder tests;
- exactly one provider download per unique configured symbol/benchmark;
- exclusive cutoff and no production backfill argument;
- deterministic archive bytes for fixed inputs;
- archive verifier rejects filename/content/source mismatches;
- workflow cannot overwrite same-date release assets;
- formal final-diff review and green CI before merge.
