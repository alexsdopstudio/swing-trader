# Design Plan — Automated Experiment Registry

Status: Completed

## Problem

The repository had durable experiment directories and a useful human-maintained index in `experiments/README.md`, but no machine-generated registry proving that the index still matched repository state. A new experiment could be added with an incorrect directory/config/result id, missing reviewed artifacts, or stale protocol fingerprint without a central CI check detecting the drift.

The registry needed to improve integrity without becoming a second research schema or duplicating interpretation already stored in `notes.md` and reviewed result files.

## Implemented design

- Discover every historical `experiments/EXP-*` directory deterministically.
- Validate directory/config/result identity and required `config.yaml`, `results.json`, and `notes.md` files.
- Record SHA-256 fingerprints for the exact durable historical records.
- Normalize existing producer/workflow/artifact provenance from both legacy experiment-local fields and the newer top-level `provenance` mapping, failing on conflicts.
- Discover prospective protocol directories separately and validate exact protocol bytes against their versioned lock.
- Require the curated `experiments/README.md` to cover every discovered experiment/protocol.
- Generate deterministic `experiments/registry.json` with stable ordering and no timestamp.
- Expose `swing-experiment-registry --root .` and `--check`.
- Run focused registry validation in a dedicated read-only PR workflow and full repository tests in normal CI.
- Make the workflow stale gate inspect `git status --porcelain` so a newly generated/untracked registry cannot pass unnoticed.

## Source-of-truth boundary

The registry contains only mechanically derivable identity/provenance facts. Human research questions and interpretation remain in `experiments/README.md`, reviewed `notes.md`, and result files. Existing historical records were not rewritten to satisfy a new schema.

## Simplify

PASS. The implementation uses one small builder/validator module, one CLI, one generated JSON file, and one focused workflow. It does not introduce a database, generated Markdown mirror, registry service, or second experiment execution framework.

## Validation

- deterministic generation and stale check covered;
- directory/config/result mismatch rejection covered;
- missing required durable files and duplicate ids covered;
- legacy and top-level provenance normalization covered;
- prospective protocol byte-lock mismatch covered;
- README coverage covered;
- repository committed registry-current check covered;
- dedicated registry workflow green after exercising the real heterogeneous EXP-0001…EXP-0006 records;
- normal pytest/Ruff CI green on the implementation head before documentation finalization.

During implementation, real-data registry generation exposed EXP-0006's newer top-level provenance layout. The parser was generalized to normalize supported layouts rather than rewriting historical records. Review also found that `git diff` alone ignores a first-generation untracked registry; the workflow was hardened to use repository status instead.

## Compound

Reusable lesson recorded in `docs/solutions/engineering/keep-derived-repository-indexes-regenerable.md`: generated indexes should remain deterministic projections of canonical records, support compatible historical layouts explicitly, and use stale checks that include untracked output.

## Definition of done

Implementation, Simplify, Validation, Compound, documentation, and memory are complete. Final-head CI, diff review, formal PASS, and squash merge remain the final lifecycle gates.
