# Preserve forward provider state and never backfill prospective gaps

## Problem

A future holdout stops being genuinely prospective if its raw evidence is reconstructed later from a mutable data provider. Adjusted historical series can change after corporate actions, corrections, or provider maintenance. A hash-only daily record can prove that something changed, but cannot recover the values that were actually visible at the original observation time.

A second failure mode is subtler: when a scheduled observation is missed, downloading that historical date later and labeling it with the missed date silently converts revised hindsight data into supposedly contemporaneous evidence.

## Reusable approach

For genuine forward evidence:

1. preregister and byte-fingerprint the protocol before observations begin;
2. derive the canonical observation date from the current trusted clock rather than a user-supplied historical date;
3. enforce an explicit information cutoff and reject rows at/after it;
4. preserve the complete provider state needed for replay, not only a digest of that state;
5. fingerprint every source file, capture time, runtime, code revision, and final archive;
6. publish each canonical observation once without overwrite semantics;
7. treat a missed date as a visible gap rather than a backfill opportunity;
8. keep raw evidence capture separate from interim strategy evaluation, tuning, and validation claims.

## Why full snapshots are appropriate here

At the current five-symbol daily scale, duplicating the source history in a compressed daily archive is simpler and safer than maintaining mutable rolling state plus revision patches. It guarantees that a future evaluator can reconstruct exactly what yfinance exposed on each capture date, even if older adjusted rows later change.

This trade-off should be revisited only if storage volume becomes material. The integrity properties must survive any future optimization.

## Publication pattern

The prospective-v1 recorder uses yearly GitHub Releases and one digest-named ZIP asset per UTC observation date. Workflow logic checks for an existing date asset and uploads without overwrite/clobber behavior. The archive filename contains its SHA-256 and the internal manifest contains SHA-256 values for every normalized source file.

This is an append-only automation contract, not a claim that repository administrators are technically unable to delete an asset. Evidence collection should verify archive filenames and manifests before evaluation.

## Applicability boundaries

- A forward snapshot proves what the configured provider returned at capture time; it does not prove exchange-level ground truth.
- Schedule failure remains a gap. Do not retroactively repair it and then count it as prospectively observed.
- The recorder should not compute a preferred strategy, interim validation outcome, or parameter update.
- Historical experiments run before forward snapshotting still retain their previously documented provider-revision limitations.

## Checks for future recorders

- protocol fingerprint mismatch fails closed;
- current-date-only production interface;
- exclusive information cutoff tested;
- required provider state stored, not hash-only;
- source and archive digests verified;
- duplicate canonical date skips rather than replaces;
- no overwrite flag in publication tooling;
- no strategy evaluation or tuning output in the capture path;
- durable storage lifetime exceeds the validation horizon.

Related: `experiments/PROSPECTIVE-v1-holdout/`, `src/swing_trader/prospective_recorder.py`, and `docs/solutions/trading-research/preregister-true-holdout-windows.md`.
