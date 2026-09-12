# Design Plan — Automated Experiment Registry

Status: Active

## Problem

The repository has durable experiment directories and a useful human-maintained index in `experiments/README.md`, but no machine-generated registry proves that the index still matches repository state. A new experiment can be added with an incorrect directory/config/result id, missing reviewed artifacts, or stale protocol fingerprint without any central CI check detecting the drift.

The registry must improve integrity without becoming a second research schema or duplicating interpretation already stored in `notes.md` and reviewed result files.

## Goals

- Discover every historical `experiments/EXP-*` directory deterministically.
- Validate directory id, `config.yaml` experiment id/name/stage, `results.json` experiment identity, and required durable files.
- Record content SHA-256 values for config/results/notes so the registry identifies the exact reviewed record.
- Normalize producer provenance already present in result files when available without inventing missing metadata.
- Discover prospective protocol directories separately and validate protocol/lock byte fingerprints generically.
- Produce a deterministic versioned `experiments/registry.json` with no generation timestamp.
- Add a CLI check mode that fails when the committed registry is stale.
- Ensure the human `experiments/README.md` links every discovered historical experiment and prospective protocol, while leaving its research questions/decisions human-authored.
- Add CI coverage so future experiment/protocol changes cannot merge with a stale or inconsistent registry.

## Non-goals

- No database or external service.
- No experiment execution or rerun.
- No automatic research interpretation, validation verdict, or parameter promotion.
- No rewrite of existing results or notes.
- No requirement that all heterogeneous experiment result payloads share one detailed metric schema.
- No generated timestamps that create nondeterministic churn.

## Registry schema

Top level:

- `schema_version: 1`
- `historical_experiments`: sorted list by numeric experiment id
- `prospective_protocols`: sorted list by directory/id

Historical entry:

- `id`, `name`, `research_stage`, `directory`
- `config_sha256`, `results_sha256`, `notes_sha256`
- `producer_code_sha` normalized from `producer_code_sha` or `code_commit_sha` when present
- `workflow_run_id`, `artifact_id`, `artifact_sha256` when already present in durable results, otherwise null
- `decision` only when the durable results already expose a machine-readable top-level string; otherwise null

Prospective entry:

- `id`, `status`, `strategy_version`, `directory`
- `registered_on`, `evaluation_start`, `minimum_observation_end`, `minimum_closed_trades` when present
- `protocol_sha256`, `protocol_lock_sha256`, `readme_sha256`
- `frozen_source_commit`

## Validation rules

Historical experiments:

- directory name must match `EXP-####-slug`;
- numeric/id prefix must be unique;
- `config.yaml`, `results.json`, and `notes.md` are required;
- `config.yaml: experiment.id` must equal directory id;
- `results.json: experiment.id` must equal directory id;
- config/result experiment names must be non-empty and equal;
- config research stage must be non-empty; result stage, when present, must match;
- result file must expose a producer/code SHA through one of the recognized fields;
- README must link the experiment directory.

Prospective protocols:

- directory starts `PROSPECTIVE-` and contains `protocol.yaml`, `protocol-lock.json`, and `README.md`;
- protocol id/status/strategy version must be non-empty;
- lock schema/id/frozen-source fields must be present;
- SHA-256 of exact protocol bytes must equal the lock's registered protocol digest;
- lock protocol id and frozen source commit must match protocol metadata;
- README must link the protocol/directory.

## Implementation

Add `src/swing_trader/experiment_registry.py` with pure discovery/validation/render/check functions and `src/swing_trader/experiment_registry_cli.py` with:

```text
swing-experiment-registry --root .
swing-experiment-registry --root . --check
```

Normal mode writes `experiments/registry.json`. Check mode computes the expected bytes and fails if the committed file is missing/stale.

Add tests using temporary synthetic experiment/protocol trees plus one repository-level test that the committed registry is current.

Add `.github/workflows/experiment-registry.yml` scoped to experiment/registry/readme/code paths. The workflow installs the project and runs registry `--check` plus focused tests. Normal CI still runs the full suite.

## Simplification plan

Keep one JSON registry generated directly from existing durable sources. Do not generate a second Markdown index or move questions/decisions into new metadata files. The README remains the curated human research index; the registry is the mechanical integrity/provenance index.

## Compound plan

Likely reusable lesson: derived repository indexes should contain only facts that can be regenerated from canonical source files, remain deterministic, and use CI check mode instead of becoming another manually edited source of truth. If confirmed, record under `docs/solutions/engineering/`.

## Documentation and memory updates

- `experiments/registry.json`
- `experiments/README.md` explaining registry/check command
- root `README.md` if the command is user-relevant
- `ARCHITECTURE.md`
- `.ai/current-state.md`
- `docs/roadmap.md`
- solution memory if Compound confirms reusable knowledge
- archive this plan before final review

## Validation plan

- exact deterministic bytes across repeated generation;
- directory/config/result id mismatch rejection;
- missing required durable file rejection;
- duplicate experiment id rejection;
- producer SHA normalization tests;
- protocol-byte/lock mismatch rejection;
- README coverage rejection;
- stale registry check rejection;
- repository committed registry current test;
- `pytest -q` and `ruff check src tests`;
- formal diff review for source-of-truth boundaries and nondeterminism.

## Definition of done

The task is complete when all historical experiments and prospective protocols are represented by a deterministic machine registry generated only from canonical durable files, CI prevents stale or inconsistent registry state, the curated README remains complete without becoming generated research interpretation, tests/lint are green, Compound/docs/memory are complete, final review is `PASS`, and the PR is squash-merged into `main`.
