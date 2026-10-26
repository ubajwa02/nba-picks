# NBA Picks: final report (2026-10-20)

## Needs you

1. **Where should it live?** Answer the card in the thread. A dedicated repo lets daily and weekly schedules run on their own; on the current branch a run only happens when `ops/trigger` is pushed. **Privacy:** bajwa19u/tradingbot is public, so the ledger, the dashboard data and anything you log in `wagers.csv` are public. A private repo fixes that. Until then, log stakes in units.
2. **Discord:** create a webhook in the picks channel and add it as repo secret `NBA_DISCORD_WEBHOOK_URL`, then set `publishing.dry_run: false`. Until then messages are built and logged, never sent. Reading other channels needs a bot token you would have to create; signals are pasted into `data/manual/signals.csv` meanwhile.
3. **Optional:** a free The Odds API key (for a US FanDuel reference price), and the location of your AI Engineering Command Center if one exists.

## Outcome

**No credible edge was found, so nothing is published as a qualified pick.** Every market is in `research` status.

- Raw model vs closing lines, 2014-15 to 2019-20, 7,300+ games per market: ML -2.8% to -4.0%, spread -3.3% to -4.2%, total -5.9% to -6.6% ROI (`reports/backtest_raw_model.md`).
- Market blend, 5 pre-registered variants, after cleaning the history lines and tightening the gates following the independent review: the best moneyline blend improved log loss by +0.0005 out-of-fold (t = 1.1, gate needs 2) and lost 3-6% on the 2020-21 to 2022-23 validation seasons. Spreads and totals got a model weight of 0 (`reports/research_latest.md`).
- The 2024-26 holdout was not used, because no candidate earned it.

## Baseline vs now

| | before | now |
|---|---|---|
| NBA code, data, tests | none in any accessible repo | `bajwa19u/tradingbot@nba-picks`: package, 120 tests, CI on every push |
| Data | none | 13 seasons of games and odds (2013-14 to 2025-26), box scores 2023-26; live ESPN odds/injuries/props + bet365 via MovioOdds |
| Ledger | none | append-only, constraint-checked; predictions, publications and your actual wagers kept separate |
| Pipeline | none | GitHub Actions: ingest, predict, publish, settle, recap, diagnose, export. Last live run 2026-10-20 01:00 UTC, all sources OK |
| Research | none | experiment registry, pre-registered gates, champion/challenger, weekly research job, diagnostics queue |
| AI team | no roles, backlog or Command Center found | `team/roles.yaml`, `backlog.yaml` (22 items), `reviews/`, `scorecards.yaml`; Command Center view in the dashboard |
| Dashboard | none | https://claude.ai/artifact/DycMBbHRaBg8pfSMYyjx55 (snapshot) and `site/` (live data, needs Pages or the new repo to host) |

## Independent review

Two fresh-context reviewers (quant Skeptic, QA/security) found 29 issues. 19 were reproduced with failing tests and all are fixed with regression tests. The most important:
- some legacy "closing" lines were in-game quotes;
- the log-loss gate could pass on noise;
- a failed write could wipe the in-memory ledger mid-run;
- injury updates silently stopped after the first run;
- DraftKings live lines were never used because of a name mismatch;
- workflow commits could overwrite your manual files.

Details: `team/reviews/`.

## Not done / known limits

- FanDuel Ontario has no permitted feed. Picks show the reference book's price and "bet only at X or better".
- Player-prop model is a simple recent-form negative binomial, unvalidated; DraftKings prop sides are mapped only where bet365 confirms each pair.
- Open items: NBA-012 to NBA-022 in `backlog.yaml` (repo move, Discord, injury-aware challenger, opening-line study on the 2026-27 forward record, sigma provenance, Bovada ML gaps, Discord sent-record durability).
- Scorecards are scored by the team lead; its own row is a self-assessment for your review.
