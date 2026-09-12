# Knowledge Base

This directory stores curated external knowledge that informs Swing Trader research methodology and hypothesis formation.

It is deliberately separate from project evidence:

- `knowledge/` records what authoritative external sources say and how that may inform the project;
- `experiments/` records what Swing Trader itself has actually tested;
- `docs/decisions/` records project decisions;
- `docs/solutions/` records reusable lessons learned while building the system.

An external paper or official methodology can motivate a hypothesis or research control. It cannot, by itself, validate Swing Trader v1.

## Structure

```text
knowledge/
  SOURCE_POLICY.md
  sources/       canonical bibliographic/source metadata
  notes/         project-authored interpretive notes
  registry.json  deterministic generated index; never edit by hand
```

Source records use stable `SRC-####` identifiers. Knowledge notes use stable `KN-####` identifiers and cite source IDs in YAML front matter.

Generate or verify the deterministic registry with:

```bash
swing-knowledge-registry --root .
swing-knowledge-registry --root . --check
```

## Initial curated topics

- momentum and trend evidence;
- data snooping, multiple testing, and backtest overfitting;
- performance-statistic interpretation;
- point-in-time universes, constituent changes, and delistings.

The initial corpus is intentionally small and high-signal. Source count is not a quality target.
