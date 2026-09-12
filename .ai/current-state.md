# Current State

Last updated: 2026-09-12

## Working

- daily data loader
- technical indicators
- Swing Score and historical score series
- scanner
- deterministic position sizing
- ATR initial/trailing stops
- single-asset backtester
- shared-account portfolio backtester
- reusable stateful daily portfolio replay session shared by historical and prospective paths
- portfolio trade ledger, equity/exposure curves, and metrics
- asset-class execution cost models for commission, spread, and slippage
- cost-aware position sizing, shared cash, aggregate risk, and realized PnL
- `swing-backtest` historical research CLI with reproducible cost configuration
- versioned experiment runner with warm-up/evaluation separation and strict JSON artifacts
- execution-cost sensitivity runner with shared market-data snapshots across scenarios
- temporal-stability runner with independent calendar folds and one shared provider snapshot
- passive/reference comparison runner with cost-aware per-symbol and initial equal-weight buy-and-hold baselines
- parameter-neighborhood runner with a preregistered 27-scenario local grid, shared inputs, full-path reruns, and no winner selection
- configured-universe breadth runner with same-snapshot control/expanded paths and symbol/asset-class contribution attribution
- preregistered prospective-v1 holdout protocol with byte-locked protocol fingerprint
- current-date-only prospective holdout recorder preserving complete provider snapshots with exclusive UTC cutoffs and end-to-end digests
- scheduled/manual GitHub Release publication path with yearly durable evidence releases, duplicate-date skip, and no overwrite/backfill semantics
- read-only prospective holdout evaluator replaying one newly observable market date per verified canonical archive with no provider fallback
- deterministic prospective derived state/trade outputs with fail-closed handling of missing or duplicate observation dates
- deterministic machine-generated experiment/protocol registry with content digests, normalized provenance, protocol-lock validation, and stale-state CI enforcement
- CI workflows capable of running real-data experiments and validating prospective recorder/evaluator infrastructure
- experiment index and durable reviewed experiment memory
- CI with pytest and Ruff
- repo-native AI memory and context builder
- automated cross-session/cross-agent PR handoff generation and resume protocol
- gated branch/design/PR/review/merge development lifecycle
- Simplify and Compound stages for AI-assisted development
- reusable solution-memory taxonomy for engineering and trading research

## Validation status

- unit test suite is passing in CI
- experiment registry tests cover deterministic bytes, stale detection, identity/file mismatch rejection, duplicate ids, README coverage, normalized legacy/top-level provenance, and prospective protocol-lock mismatch
- dedicated registry CI regenerates `experiments/registry.json` and rejects modified or newly generated/untracked registry state
- portfolio execution/risk semantics are covered by synthetic tests
- stateful replay preserves next-asset-bar, stop ordering, terminal-liquidation separation, and pending-state continuity
- all real-data EXP-0001 through EXP-0006 workflows remain green after the portfolio event-loop refactor
- cost-aware sizing and execution arithmetic are covered by synthetic tests
- EXP-0001 real-data workflow completed successfully on BTC-USD, SOL-USD, META, and NVDA
- EXP-0001 exploratory baseline: 65 trades, +1.05R expectancy, 3.18 profit factor, 6.01% CAGR, -4.25% max drawdown
- EXP-0002 execution-cost sensitivity completed with one shared provider snapshot across all scenarios
- EXP-0002 high 2.0x-cost scenario: 65 trades, +0.99R expectancy, 3.03 profit factor, 5.67% CAGR
- EXP-0002 stress 4.0x-cost scenario: 66 trades, +0.82R expectancy, 2.62 profit factor, 4.77% CAGR
- EXP-0002 supports execution-cost robustness inside the same historical sample but is not out-of-sample validation
- EXP-0003 retrospective temporal diagnostic completed across six independent calendar folds
- EXP-0003 positive expectancy / profit-factor>1 / positive-return folds: 3 of 6; both preregistered 4-of-6 stability thresholds failed
- EXP-0003 confirmed 2025 and 2026-YTD as weak; 2022 produced no trades and no exposure
- EXP-0004 passive/reference comparison completed on the same four-asset retrospective sample
- EXP-0004 initial equal-weight buy-and-hold: +2,139.01% total return, 73.16% CAGR, -95.19% max drawdown, 1.06 Sharpe, 99.89% average exposure
- EXP-0004 frozen v1: +39.17% total return, 6.01% CAGR, -4.25% max drawdown, 1.27 Sharpe, 6.04% average exposure
- EXP-0004 shows much higher passive absolute return but radically different drawdown/exposure; it is retrospective and does not validate v1
- EXP-0005 parameter-neighborhood diagnostic completed across exactly 27 preregistered score/stop/trail scenarios on one shared provider snapshot
- EXP-0005 joint-positive scenarios: 27 of 27; joint-positive immediate axial neighbors: 6 of 6; median expectancy: +0.92R versus preregistered +0.50R threshold
- EXP-0005 exact frozen-v1 center reproduced EXP-0001 within every preregistered provider-revision tolerance
- EXP-0005 supports local retrospective parameter robustness but does not select a replacement parameter set; expectancy still spans roughly +0.43R to +1.73R across the grid
- EXP-0006 configured-universe breadth diagnostic completed on the exact 11 assets that predated the experiment, with a same-snapshot four-symbol EXP-0001 control
- EXP-0006 expanded path: 141 trades, +39.98% total return, +0.49R expectancy, 2.04 profit factor, 6.12% CAGR, -5.13% max drawdown, and 14.98% average exposure
- EXP-0006 breadth criteria all passed: added-symbol aggregate net PnL +514.76; 8 of 11 total and 5 of 7 added symbols positive; both asset classes positive; largest positive contributor share 30.58% versus a 60% ceiling
- EXP-0006 supports broader retrospective contribution but not superiority of the expanded portfolio; expectancy/PF fell and drawdown/exposure rose relative to the four-symbol control
- `PROSPECTIVE-v1-holdout` is preregistered to start 2026-09-14 with no interim v1 tuning
- prospective recorder tests cover protocol-lock mismatch, exclusive cutoff behavior, pre-start no-op, exactly five provider downloads, deterministic archives, and the absence of a production backfill date argument
- prospective evaluator tests cover canonical daily-chain processing, zero provider downloads, deterministic repeated output, provider revisions without retroactive replay, pending next-asset-bar continuity, duplicate/pre-start rejection, and stop-at-first-gap behavior
- first active prospective capture is expected on 2026-09-15 after the completed 2026-09-14 bar is available; no prospective observation exists yet
- no validated portfolio-level trading edge yet
- no live or paper execution yet

## Known limitations

- execution costs use linear basis-point assumptions rather than order-book or nonlinear market-impact models
- baseline cost assumptions and sensitivity multipliers are research inputs, not broker/exchange quotes
- EXP-0001 through EXP-0006 still use current/high-profile survivor assets rather than a point-in-time investable-universe reconstruction
- EXP-0006 reduces dependence on the original four-symbol subset but does not eliminate survivorship/selection bias
- profit contribution remains regime-dependent even though EXP-0006 broadened positive contribution across symbols and asset classes
- passive-reference returns are strongly influenced by exceptional SOL and NVDA paths and do not remove selection/survivorship bias
- passive references are nearly fully invested while v1 averages about 6% exposure in the four-symbol baseline; no volatility/leverage normalization has been preregistered or tested
- the aggregate historical edge is not temporally uniform: 2025 and 2026-YTD are negative and 2022 is inactive
- EXP-0005 supports local sign/quality robustness but parameter choice still materially affects historical magnitude
- EXP-0003, EXP-0004, EXP-0005, and EXP-0006 are retrospective diagnostics, not true out-of-sample validation
- the prospective holdout cannot support validation claims before both 2028-09-14 and 30 closed trades
- pre-recorder historical yfinance snapshots cannot be reconstructed exactly after provider revisions; forward holdout captures preserve complete provider states only once active
- GitHub Release append-only behavior is enforced by workflow convention and digests, not by an administrator-proof storage primitive
- evaluator outputs are derived/reproducible monitoring state rather than a second durable evidence store
- evaluator infrastructure has only synthetic evidence so far because the first real active archive is not expected until 2026-09-15
- the generated experiment registry validates structural/provenance integrity but deliberately does not replace human interpretation or prove research conclusions correct
- no point-in-time universe membership/survivorship study
- no semantic retrieval for solution memory
- no persistent daily scan history
- no catalyst/news agent

## Current milestone

Keep v1 frozen. Let the forward recorder produce the first active UTC observation on 2026-09-15 and treat any missed scheduled day as a gap rather than backfill it. Replay captured evidence only through the read-only information-time evaluator and never feed interim state/trades into tuning. The experiment/protocol registry is now automated and should remain a derived integrity index rather than a second research source of truth. If historical universe work continues, preregister point-in-time membership rather than adding more current survivors; otherwise the next infrastructure candidate is persistent daily scan history.
