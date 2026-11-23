# Free official data provider foundation

Status: Initial provider clients implemented; source expansion remains active.

## Scope

Implement dependency-free clients for official public U.S. data sources with a free unauthenticated access path: SEC EDGAR, Treasury Fiscal Data, and BLS Public Data API v1. Record a qualified inventory for subsequent increments.

## Design

- Use Python standard-library HTTP/JSON only; no new runtime dependency.
- SEC clients require an identifying User-Agent with contact email and normalize CIKs to ten digits.
- Treasury accepts endpoint paths only under the official API root and returns one explicitly bounded page.
- BLS v1 enforces the 25-series request limit and validates provider status.
- Clients return provider payloads; they do not create signals, persist data, infer event times, or alter the existing price pipeline.
- Fail with explicit typed errors rather than returning empty or fabricated data.

## Acceptance criteria

- SEC submissions and Company Facts use documented no-key endpoints and identifying User-Agent.
- Treasury uses the official no-token API and bounded pagination.
- BLS uses no-key v1 and enforces limits.
- Offline tests cover URL construction, validation, request headers/body and provider status.
- Source inventory distinguishes implemented clients from candidates and records access caveats.
- Frozen v1, holdout and paper-trading semantics remain untouched.

## Known limitations

FRED, BEA and EIA require free API-key registration and are deferred to a subsequent increment. BLS v1 has lower quotas than keyed v2. SEC requests must comply with fair-access policy. Social access is inconsistent and several platforms have no unrestricted free API. Historical depth and point-in-time revisions vary by provider.

## Simplify

A small module with explicit functions and standard-library transport. No generic plugin framework, database, scheduler or speculative abstraction.

## Compound

Maintain docs/data-sources/free-public-data.md as the canonical inventory. Update roadmap and current-state memory to distinguish implemented clients from candidates.

## Validation

Mock HTTP responses; tests must not require network access. Require GitHub CI and diff review.

## Checklist

- [x] Review existing data and knowledge architecture.
- [x] Implement SEC submissions and Company Facts.
- [x] Implement Treasury Fiscal Data.
- [x] Implement BLS API v1.
- [x] Add offline unit tests.
- [x] Add source inventory and access caveats.
- [ ] CI and formal review.
- [ ] Add FRED/ALFRED, BEA, EIA and further public sources separately.
