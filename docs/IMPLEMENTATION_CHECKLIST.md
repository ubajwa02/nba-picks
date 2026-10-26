# Upgrade checklist (2026-10-22)

Baseline found on audit (before this upgrade):
- 10 of 146 tests failing: the probe workflow overwrote the pinned fixtures on the repo move. Fixed (fixtures restored; probe now writes `reports/probe_fixtures/`).
- Every DraftKings prop was rejected (`side_unverified`: ESPN lists the two sides unlabelled and the game-level bet365 vote never reached 90%), so the prop model produced **no recorded probabilities** on the market that matters most.
- Prop model `props-v0`: flat 15-game mean x minutes, per-player variance, no opponent, no injuries, no recency weighting.
- Rejected prop candidates were not stored; predictions were re-written every run (one row per run, no versioning).
- Parlays/lotto were only built from `eligible` legs, so with every market in research nothing was ever built or tracked.
- No real-price prop backtest; no one-month backtest report; dashboard Today tab mixed engineering panels with picks.

| # | item | status |
|---|---|---|
| 1 | Restore fixtures, stop probe overwriting them | done |
| 2 | Prop model v1 (recency-weighted rates, minutes projection with teammate-out adjustment, opponent adjustment, fitted dispersion, shrinkage) + walk-forward prop backtest + cache | in progress |
| 3 | Unlabelled DK prop sides: conservative price (worse of the pair) + bet365 ladder interpolation to label sides | in progress |
| 4 | Ledger: every candidate recorded, versioned by content (no duplicate per rerun), explanation inputs stored | in progress |
| 5 | Team model: player-availability adjustment (missing-player value), box score shot volume columns | in progress |
| 6 | Historical prop prices backfill (ESPN propBets on finished games) + one-month backtests with real prices | in progress |
| 7 | Research parlays/lotto tracked separately from straights | in progress |
| 8 | Discord signals compared with the model at the same game/market | in progress |
| 9 | Weekly loop: prop champion/challenger with pre-registered gates | in progress |
| 10 | Dashboard redesign (Today, Picks, Performance, Player & Team, Model Valuation, Research, Settings & Audit) | in progress |
| 11 | Workflows: daily + weekly + manual backtest; persistence; no loops | in progress |
| 12 | Tests for every item above, all passing | in progress |
