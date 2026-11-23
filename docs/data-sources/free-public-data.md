# Free public data source inventory

This catalog distinguishes implemented clients from candidates. "Free" means no subscription fee for the documented public access path; it does not remove quotas, attribution duties, terms, or redistribution restrictions.

## Implemented in this increment

| Provider | Coverage | Access and credentials | Constraints | Status |
|---|---|---|---|---|
| SEC EDGAR submissions | Issuer identity, ticker/exchange metadata, filing history including 8-K, 10-K, 10-Q and Form 4 | Official JSON REST; no API key; identifying User-Agent with contact email | SEC fair-access policy; preserve filing/accession/amendment timestamps | Client implemented |
| SEC XBRL Company Facts | Structured reported financial facts | Official JSON REST; no API key; identifying User-Agent | Tags/contexts vary; retain accession, period and filed metadata | Client implemented |
| U.S. Treasury Fiscal Data | Debt, cash balance, rates, receipts, spending and fiscal datasets | Official JSON REST; no account or token | Explicit pagination; dataset-specific cadence and schema | Client implemented |
| BLS Public Data API v1 | CPI, PPI, employment, wages and labor series | Official JSON POST; no key for v1 | Public v1 quota is limited; maximum 25 series per request; keyed v2 is separate | Client implemented |

## Next provider candidates

| Priority | Provider | Useful data | Free access path | Caveats |
|---|---|---|---|---|
| P0 | Federal Reserve / FRED / ALFRED | Rates, yields, macro series, vintages and release calendars | FRED API | Free API-key registration required. ALFRED vintages are important for point-in-time backtests. |
| P0 | BEA | GDP, PCE, income, trade and industry accounts | BEA API | Free API key registration; quotas apply. |
| P0 | EIA | Petroleum, natural gas, electricity and inventories | EIA Open Data API | Free API key registration; quotas and endpoint limits apply. |
| P0 | SEC filing documents and bulk archives | Filing bodies, exhibits, historical issuer facts | EDGAR archives and bulk ZIP | Public; distinguish filed-at time, accession, amendments and nightly bulk snapshots. |
| P1 | FDA openFDA | Drug/device enforcement, recalls, labels and selected regulatory records | openFDA REST | No key for low-volume use; key needed/recommended above unauthenticated limits; coverage is not all FDA data. |
| P1 | ClinicalTrials.gov | Trial registration, status, endpoints and results | Public API v2 | Preserve study version/history and update timestamps. |
| P1 | USAspending.gov | Federal awards, recipients, agencies and contract actions | Public API | Distinguish award, action, modification and publication dates. |
| P1 | CFTC | Commitments of Traders and derivatives positioning | Public reports/downloads | Weekly and delayed; preserve release time. |
| P1 | Federal Register | Rules, notices, executive actions and regulatory timelines | Public API | Distinguish publication, effective and comment dates. |
| P1 | Congress.gov | Bills, actions, committees and legislative events | API | Key registration; legislative status is not enacted law. |
| P2 | Hacker News | Technology/product discussions | Official Firebase API | Public; useful for technology discovery, not direct issuer fundamentals. |
| P2 | Reddit | Public investing/industry discussions | Reddit Data API | Commercial access and terms may require approval; no scraping bypass. |
| P2 | YouTube | Public video/channel metadata | YouTube Data API | Key and quota; transcripts/comments have separate availability and terms. |
| P2 | Bluesky | Public posts and social graph data | AT Protocol public APIs/relay | Public endpoints; rate limits and provenance required. |
| P2 | Stocktwits | Ticker-specific investor messages | API if access is granted | Verify current access, terms and quota; do not assume unrestricted free access. |
| P2 | X | Public posts, cashtags and accounts | X API | Tiered/paid access; exclude from free-first production until a suitable free tier is verified. |
| P2 | Google Trends | Search interest and consumer/product attention | Public website/export | No guaranteed unrestricted official API; do not make unofficial scraping a production dependency. |
| P2 | Telegram | Public channel posts | Bot/API interfaces | Bot access is not universal channel-history access; no private-group scraping. |
| P2 | Discord | Community activity | Authorized bot API | Server authorization required; not a general public feed. |
| P2 | TikTok | Consumer/product trend signals | Restricted research/business interfaces | No assumption of a general free market-data API. |

## Provider admission checklist

Before production inclusion, record official documentation and API version, access/key requirements, price, quota/rate limits, attribution, terms/licensing/storage rights, dataset coverage, update cadence, historical depth, revision behavior, publication/first-seen/retrieval timestamps, pagination, failure modes, and expected incremental value.

Never bypass authentication, paywalls, access restrictions, quotas or platform terms. Do not persist full third-party text unless terms allow it. Preserve source provenance and content fingerprints where permitted.

## Research integrity

- Keep publication time, provider update time, first-seen time and retrieval time distinct.
- Use ALFRED/vintage-aware macro data where possible; revised current macro values must not leak into historical decisions.
- Deduplicate syndicated news and reposts before counting independent confirmation.
- Social mentions and sentiment are corroborating context, not standalone trading signals.
- Unknown source quality remains unknown.
- Evaluate source coverage, latency, false positives and incremental predictive value after costs.
- This inventory does not modify frozen strategy v1 or its prospective holdout.
