---
schema_version: 1
id: KN-0004
title: Historical universe tests require point-in-time membership
topics:
  - point-in-time-universe
  - survivorship-bias
  - index-membership
  - delistings
source_ids:
  - SRC-0007
  - SRC-0008
status: curated
---

# Historical universe tests require point-in-time membership

## What the evidence says

`SRC-0007` documents that major U.S. equity indices have explicit eligibility and maintenance rules and that constituents are added and deleted as companies and market conditions change. `SRC-0008` documents delisting returns as part of institutional historical equity data, including economic outcomes after a security stops ordinary trading.

A present-day list of successful, liquid companies is therefore not a faithful representation of the securities that were investable or selected at earlier dates. Securities that later disappeared can carry economically important outcomes that are absent from a current-survivor list.

## Project implication

A stronger historical universe experiment should preregister the universe rule and reconstruct membership as it existed at each decision date, including delisted names and the relevant return treatment. The data source must support that reconstruction; simply adding more current high-profile assets does not solve survivorship bias.

Until such a dataset/methodology is implemented, configured-universe breadth results should remain labeled as retrospective breadth evidence rather than survivorship-free evidence.

## What it does not establish

The cited S&P methodology does not supply all historical constituent states by itself, and CRSP documentation does not grant this repository access to CRSP data. These sources establish why point-in-time construction matters, not a finished data solution for the project.

They also do not imply that an S&P index must become the strategy's universe. The appropriate point-in-time universe is a separate research-design decision.

## Sources

- `SRC-0007` — S&P Dow Jones Indices, current U.S. index methodology and maintenance rules.
- `SRC-0008` — CRSP, official U.S. stock database documentation including delisting returns.
