# Prospective v1 holdout

`protocol.yaml` is the preregistered v1 holdout specification. It starts on 2026-09-14 and cannot support a validation claim until both the minimum observation end (`2028-09-14`) and minimum closed-trade count (30) are satisfied.

`protocol-lock.json` fingerprints the exact registered protocol bytes and frozen source commit. The normal recorder fails if the registered protocol is edited in place.

## Forward evidence recording

After the holdout starts, `.github/workflows/prospective-v1-holdout-recorder.yml` runs daily after UTC rollover. The first active observation is therefore the 2026-09-15 capture, whose data cutoff is exclusive `2026-09-15` and can contain bars dated no later than 2026-09-14.

Each active observation records the complete normalized yfinance OHLCV history from the frozen warm-up start through the exclusive cutoff for BTC-USD, SOL-USD, META, NVDA, and QQQ. Full snapshots preserve later provider revisions rather than only proving that a hash changed.

The recorder creates a deterministic archive named:

```text
PROSPECTIVE-v1-holdout-YYYY-MM-DD-<sha256>.zip
```

The ZIP contains `manifest.json` plus one source CSV per required symbol. The manifest records the protocol digest, frozen source commit, recorder code SHA, capture timestamp, runtime versions, source coverage, and per-file SHA-256 values. The archive filename contains the SHA-256 of the archive bytes.

## Durable publication

The scheduled workflow publishes one archive per active observation date to yearly GitHub Releases named `prospective-v1-holdout-data-YYYY`. It checks for an existing date asset before recording and uploads without overwrite/clobber semantics.

The workflow intentionally does **not** commit generated observations to `main`.

A missed observation is not backfilled from a later provider state. Manual workflow dispatch records only the current UTC date under the same rules. This makes schedule gaps visible instead of converting later revised history into falsely prospective evidence.

Repository administrators can still delete release assets; the append-only property is therefore an automation contract rather than an access-control guarantee. Archive digests embedded in filenames and source digests in manifests make replacement or corruption detectable when evidence is collected.

## Evaluation boundary

The recorder captures provider evidence only. It does not calculate interim PnL, validation status, preferred parameters, or strategy changes. Frozen v1 remains defined by this protocol, and interim observations must not be used to tune it.

To record locally for the current UTC date after the holdout starts:

```bash
swing-holdout-record \
  --protocol experiments/PROSPECTIVE-v1-holdout/protocol.yaml \
  --lock experiments/PROSPECTIVE-v1-holdout/protocol-lock.json \
  --output-dir .artifacts/PROSPECTIVE-v1-holdout
```
