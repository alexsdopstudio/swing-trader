# Design Plan — Prospective Holdout Recorder

Status: Completed

## Problem

`PROSPECTIVE-v1-holdout` begins on 2026-09-14, but mutable yfinance history cannot be re-downloaded later and treated as the provider state that was visible during the holdout. The project needed durable forward evidence before the first active observation.

## Goals delivered

- Byte-lock the preregistered holdout protocol before capture begins.
- Record one canonical current-UTC-date provider snapshot after the holdout starts.
- Enforce a data cutoff strictly before the observation date.
- Preserve complete normalized source histories for the four traded assets plus unique benchmarks.
- Fingerprint protocol, code, runtime, source files, capture time, and deterministic archive bytes.
- Publish one date-keyed archive to yearly GitHub Releases without overwrite/clobber behavior.
- Prevent retrospective backfill through the production CLI/workflow.
- Keep evidence capture separate from interim strategy evaluation/tuning.

## Final design

`experiments/PROSPECTIVE-v1-holdout/protocol-lock.json` stores the SHA-256 of the exact registered protocol bytes, frozen source commit, and fixed warm-up start. Capture fails closed if the protocol changes in place.

`src/swing_trader/prospective_recorder.py` derives the observation date from the current UTC clock. Tests may inject a clock, but the production CLI exposes no date argument. Dates on/before the 2026-09-14 evaluation start are pre-start no-ops, making 2026-09-15 the first active capture.

For BTC-USD, SOL-USD, META, NVDA, and QQQ, the recorder downloads from 2020-01-01 through the observation date exclusive, removes any row at/after the cutoff, validates normalized OHLCV, and stores stable CSV bytes. `manifest.json` records protocol/code/runtime/workflow/source provenance. A deterministic ZIP contains the manifest and all source files; the complete archive SHA-256 is embedded in its filename.

`.github/workflows/prospective-v1-holdout-recorder.yml` runs daily at 02:17 UTC and supports same-day manual dispatch. PR events execute a read-only validation job only. Scheduled/manual recording receives `contents: write`, checks for an existing date asset, creates a yearly release if needed, and uploads without overwrite semantics. Existing canonical dates are skipped.

## Research integrity

- No strategy/risk/execution parameters changed.
- The recorder computes no signals, trades, PnL, preferred parameters, or validation outcome.
- Information cutoff is explicit and tested.
- A missed prospective date cannot be supplied later to the production interface; it remains a gap.
- Complete source snapshots preserve the actual provider state across later yfinance revisions.
- Release append-only behavior is an automation contract rather than administrator-proof storage; archive/source digests make replacement detectable.

## Validation

- Registered protocol byte fingerprint: PASS.
- Protocol mutation mismatch: PASS/fails closed.
- Required unique source set: 5 symbols.
- Pre-start behavior: PASS/no download and no snapshot.
- Exclusive cutoff: PASS; rows at the observation date are excluded.
- Production CLI has no historical date input: PASS.
- Same clock/input/code produces byte-identical archive: PASS.
- Archive/source digest verifier: PASS.
- PR workflow skips the write-capable record job: PASS.
- Duplicate-date/no-clobber workflow checks: PASS.
- `pytest -q`: PASS after correcting one overly broad static test assertion.
- `ruff check src tests`: PASS.

## Simplify

PASS. Full compressed daily snapshots were retained instead of introducing mutable rolling state plus revision patches, a database, storage abstraction, evaluator, or generic provenance service. At five daily symbols this is simpler and guarantees exact replay.

## Compound

Reusable learning captured in `docs/solutions/trading-research/preserve-forward-provider-state-without-backfill.md`: forward evidence must preserve provider state at observation time, and a missed prospective capture must remain a gap rather than be reconstructed later from revised history.

## Post-merge operation

The workflow may run before the holdout starts but produces no active asset on/before 2026-09-14. The first canonical active archive is expected on 2026-09-15 and contains data strictly before that date. v1 remains frozen and validation gates remain unchanged.

## Definition of done

Completed when the final diff receives `PASS`, all CI checks are green, the scheduled workflow is merged before the first active capture, durable project memory is current, and a pre-start manual dispatch confirms no asset is published before activation.
