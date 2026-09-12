# Design Plan

Status: Active

## Problem

`PROSPECTIVE-v1-holdout` begins on 2026-09-14, but the repository does not yet have a durable forward-data recorder. Re-downloading historical yfinance data later is not sufficient because adjusted equity/QQQ history has already changed across repeated experiments. A genuine prospective record must preserve what the provider exposed at each observation time without allowing missed days to be silently reconstructed after the fact.

## Goals

- Record one canonical provider snapshot per active UTC observation date for the preregistered v1 holdout.
- Preserve the complete normalized source history needed to replay frozen v1 as it was visible on each capture date.
- Enforce an information cutoff so the daily snapshot includes only bars strictly before the UTC observation date.
- Fingerprint the frozen protocol, recorder code, runtime, every source file, and the final archive.
- Make automated publication append-only by convention: a date may be published once and never overwritten by the workflow.
- Refuse retrospective backfill through the normal recorder path; a missed daily capture remains an explicit gap rather than synthetic prospective evidence.
- Keep capture separate from strategy evaluation so interim observations cannot implicitly tune or replace frozen v1.

## Non-goals

- No live/paper orders or broker integration.
- No interim performance dashboard, validation claim, parameter tuning, signal ranking, or strategy change.
- No automatic reconstruction of a missed prospective date from later provider data.
- No change to `PROSPECTIVE-v1-holdout/protocol.yaml`, frozen v1, risk rules, or execution assumptions.
- No broader-universe research in this PR.

## Relevant context

- `experiments/PROSPECTIVE-v1-holdout/protocol.yaml` preregisters v1, the four traded symbols, BTC/QQQ benchmarks, start date `2026-09-14`, and the no-interim-tuning rule.
- `src/swing_trader/data.py` downloads auto-adjusted daily OHLCV via yfinance.
- Prior experiments observed repeated META/NVDA/QQQ adjusted-history revisions. Hashes detect those revisions but do not reconstruct prior provider states.
- The holdout validation gate remains both `2028-09-14` and at least 30 closed trades.

## Proposed design

### Protocol lock

Add `experiments/PROSPECTIVE-v1-holdout/protocol-lock.json` containing the registered protocol SHA-256 and frozen source commit. `prospective_recorder.py` will fail if the protocol bytes no longer match the lock. Any future strategy/risk change therefore requires a new protocol/version rather than editing the registered v1 holdout in place.

### Observation semantics

A canonical `observation_date` is the current UTC date at recorder execution. The data cutoff is that date, exclusive. For example, a capture on `2026-09-15` downloads with end `2026-09-15`, so only bars dated `2026-09-14` or earlier can enter the snapshot.

The first active capture date is the day after `holdout.evaluation_start`. Scheduled runs before then exit successfully without producing a holdout asset.

The normal CLI accepts no arbitrary historical observation date. Tests may inject a clock through the Python API, but production CLI/workflow always derives the date from current UTC time. This prevents a missed prospective date from being backfilled later and mislabeled as contemporaneous evidence.

### Snapshot contents

For the four traded symbols plus unique benchmark symbols, download from the frozen experiment warm-up start through the exclusive observation cutoff. Normalize each frame to sorted daily `Open,High,Low,Close,Volume` CSV with stable date formatting and numeric serialization.

Each snapshot directory contains:

- `manifest.json` with schema version, protocol id/SHA, frozen source commit, recorder code SHA, UTC capture timestamp, observation date, cutoff semantics, runtime/package versions, provider, required symbols, and per-source coverage/file SHA-256;
- `source/<symbol>.csv` for each of BTC-USD, SOL-USD, META, NVDA, and QQQ;
- one deterministic ZIP archive containing the manifest and source files.

The archive filename includes its SHA-256 prefix, e.g. `PROSPECTIVE-v1-holdout-2026-09-15-<digest>.zip`, so downloaded bytes can be checked against their name independently of GitHub metadata.

Full source snapshots intentionally duplicate history across days. At the current five-symbol daily scale this is a simpler and more auditable integrity trade-off than mutable rolling state plus revision patches, and it guarantees exact replay of every captured provider state.

### Durable publication

Add a scheduled GitHub Actions workflow running daily after UTC rollover (02:17 UTC) plus manual dispatch for same-day recovery. The workflow:

1. resolves the current UTC observation date and reads the protocol start date;
2. skips dates on/before the evaluation start;
3. maps the observation to a yearly release tag such as `prospective-v1-holdout-data-2026`;
4. checks whether that date already has an asset and exits successfully if so;
5. runs `swing-holdout-record` and validates the archive/manifest/source hashes;
6. creates the yearly release if absent, targeting the recorder code revision that first creates it;
7. uploads exactly one date-keyed archive without `--clobber`.

Automation receives `contents: write` only for release/tag publication. It does not commit generated observations to `main`.

The release-asset contract is append-only by workflow behavior, not an authorization claim: repository administrators could still delete assets. The archive digest embedded in its filename plus the internal manifest makes replacement/tampering detectable when evidence is later collected.

### Evaluation boundary

This PR records provider evidence only. It does not compute portfolio performance, trade counts, or validation status. A later evaluator may replay the frozen source commit against stored snapshots, but interim evaluation must remain read-only and must not feed v1 tuning.

## Trading and research implications

- **Look-ahead:** source rows are clipped to dates strictly before the capture's UTC observation date. The recorder does not generate fills or signals.
- **Prospective integrity:** normal production code cannot assign a historical observation date, so a missed day cannot be recreated from revised later data as if it had been observed contemporaneously.
- **Provider revisions:** complete daily snapshots preserve both the old and new provider states rather than only noting that hashes changed.
- **Execution/risk:** frozen strategy, risk, and execution rules are untouched; evaluation is explicitly out of scope.
- **Data leakage/tuning:** the recorder exposes raw evidence only and produces no optimization or validation output.
- **Reproducibility:** protocol lock, source digests, runtime versions, capture time, code SHA, deterministic serialization, and archive digest are recorded.

## Alternatives considered

- Store only source hashes: rejected because a later hash mismatch proves revision but cannot reconstruct the prior provider values.
- Store only newly arrived bars: rejected because adjusted historical bars may later revise; a full snapshot is required for exact provider-state replay.
- Maintain mutable source-state files plus revision patches in `main`: rejected as more complex and as daily generated commits would pollute the code branch/lifecycle.
- GitHub Actions artifacts only: rejected because retention is finite relative to a multi-year holdout.
- Automatically backfill missed schedule dates: rejected because later provider state is not contemporaneous prospective evidence.
- Compute interim strategy PnL in the recorder: rejected to keep capture independent from evaluation and tuning pressure.

## Test and validation plan

- Unit tests for protocol lock verification and mismatch rejection.
- Tests for required five-symbol universe resolution and duplicate benchmark removal.
- Tests that capture rejects/ignores rows at or after the exclusive observation cutoff.
- Tests that pre-start dates produce no active snapshot.
- Tests that production observation date comes from the injected/current UTC clock rather than user-supplied historical input.
- Deterministic serialization/archive tests including source and archive SHA verification.
- Synthetic downloader test proving exactly five provider downloads.
- Workflow validation that duplicate date assets are skipped and uploads never use overwrite/clobber semantics.
- `pytest -q` and `ruff check src tests`.
- Manual workflow-dispatch dry run before the holdout begins may exercise pre-start skip behavior; no pre-start asset should be published.

## Simplification plan

Keep the implementation to one protocol/snapshot module, one CLI, and one scheduled workflow. Do not add a database, generic object store abstraction, signal engine, evaluator, registry service, or revision-diff engine. Prefer full immutable snapshots over incremental state machinery at this scale.

## Compound plan

Likely reusable learning: genuine forward evidence requires preserving provider state at observation time, and missing prospective captures must remain gaps rather than being backfilled from revised history. If confirmed, record this under `docs/solutions/trading-research/`.

## Documentation and memory updates

- `experiments/PROSPECTIVE-v1-holdout/protocol-lock.json`.
- Holdout README/recording documentation if needed.
- `README.md`, `ARCHITECTURE.md`, `.ai/current-state.md`, and `docs/roadmap.md`.
- `docs/solutions/README.md` plus a trading-research solution note if Compound is confirmed.
- Archive this plan under `docs/plans/completed/` before final review.

## Implementation plan

1. Add protocol lock and strict holdout protocol loader.
2. Implement current-date-only snapshot capture, deterministic source serialization, manifest, and archive hashing.
3. Add CLI and unit tests.
4. Add scheduled/manual release-publication workflow with duplicate-date and pre-start guards.
5. Run Simplify and validation, including workflow/static safety checks.
6. Complete Compound and durable documentation/memory updates.
7. Archive the plan and perform formal final-diff review.
8. Merge only after `PASS`, green CI, and no unresolved threads so the first active scheduled capture can occur after 2026-09-14.

## Review checklist

- [x] Scope and acceptance criteria are clear.
- [x] Design preserves the frozen protocol and strategy boundary.
- [x] Information cutoff and no-backfill semantics are explicit.
- [x] Provider revision preservation is stronger than hash-only detection.
- [x] Durable storage lifetime exceeds the prospective holdout horizon.
- [x] Scheduled publication cannot silently overwrite an existing date.
- [x] Simplification and Compound destinations are identified.

## Definition of done

The recorder is complete when a merged scheduled workflow can capture one current-date, cutoff-safe, full provider snapshot after the holdout starts; each archive is self-fingerprinted, durably published without overwrite, the registered protocol cannot mutate silently, missed dates remain explicit gaps, tests/lint are green, the final diff receives `PASS`, and project memory describes how future agents should operate the forward record.
