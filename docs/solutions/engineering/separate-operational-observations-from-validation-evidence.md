# Separate Operational Observations from Validation Evidence

## Problem

A trading system may need to preserve what an operational scanner saw each day while also collecting a preregistered prospective holdout. Both artifacts benefit from timestamped source snapshots, content digests, deterministic archives, and no-backfill semantics, which makes it tempting to treat them as interchangeable evidence.

That is unsafe. Operational history can use a different universe, configuration lifecycle, or purpose and may exist primarily for auditability, monitoring, and debugging. A preregistered validation holdout has a frozen protocol and explicit statistical gates established before the evidence arrives.

## Solution

Model the two streams as different evidence classes even when they share integrity techniques.

- Operational observations preserve what the running product saw and produced.
- Prospective validation evidence is bound to a preregistered protocol, frozen strategy/version, fixed evaluation rules, and explicit validation gates.
- Give each stream separate archive identifiers, release namespaces, manifests, workflows, and consumers.
- Mark operational manifests explicitly as not validation evidence and not eligible for holdout substitution.
- Do not let a validation evaluator consume operational archives.
- Keep production observation dates clock-derived and leave missed dates as gaps in both streams rather than reconstructing them later.

## Why this works

Provenance answers whether an artifact is authentic and reproducible; preregistration answers whether it can support a particular inference. Strong provenance alone does not turn an operational record into unseen validation evidence.

Keeping the namespaces and consumers separate makes the inference boundary mechanically visible instead of relying only on documentation or reviewer memory.

## Applicability

Use this pattern whenever one project records both operational telemetry/decisions and controlled research evidence, especially when the underlying market data can be revised by a provider after the fact.

## Checks

- Operational and validation archives have different identifiers and release tags.
- Operational manifests explicitly reject validation/holdout substitution.
- Validation consumers accept only protocol-bound validation archives.
- Neither production recorder exposes a historical observation-date override.
- Duplicate-date publication skips or fails rather than overwriting.
- Tests verify the evidence-class boundary in addition to content hashes.

## Related

- `src/swing_trader/daily_scan_recorder.py`
- `src/swing_trader/prospective_recorder.py`
- `src/swing_trader/prospective_evaluator.py`
- `docs/solutions/trading-research/preregister-true-holdout-windows.md`
- `docs/solutions/trading-research/preserve-forward-provider-state-without-backfill.md`
