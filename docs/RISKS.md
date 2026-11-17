# Risk register (2026-10-26)

| # | Risk | Effect | Control now | Still open |
|---|---|---|---|---|
| 1 | No prop market shows an edge at real prices | Alerts would lose money | Every market stays `research`; nothing is published as a qualified pick; gates in `config/gates.yaml` are pre-registered | Needs forward evidence, not more tuning |
| 2 | Free odds only (DraftKings via ESPN, bet365 via MovioOdds), no FanDuel | The price you bet may differ from the price modelled | Pair-plausibility check, DraftKings sides labelled by listing order only while the results and same-run checks hold (`docs/SIDE_ORDER.md`), conservative pricing otherwise, `validate_odds` on every row | A paid feed is a later decision |
| 3 | Real historical prop prices cover only Oct-Nov 2025 and Apr-Jun 2026 | Small sample for any ROI claim | Holdout 2026-02-01..06-30 untouched, scored once per frozen candidate | none |
| 4 | Backtest uses the game's own box score to know who sat | Flatters teammates-out results | Flagged in the model notes and reports | No historical injury reports exist to fix it |
| 5 | A data source changes shape or goes down | Wrong or stale picks | `nbapicks/validate.py` (schema, duplicates, impossible values, time zones, team conflicts); empty injury feed keeps the old file so it goes stale and holds; failing critical sources hold all picks | none |
| 6 | Lost GitHub access again | Code and ledger unreachable | `nba-backup` workflow bundle on change, `tools/backup_local.sh`, restore steps in `docs/BACKUP.md` | Keep a copy outside GitHub; a second mirror is optional |
| 7 | Repo is public | Ledger and dashboard data visible | none | Uday to switch the repo to private; never add wager data while public |
| 8 | A bad model promotion | Worse probabilities | Promotion needs gates plus a recorded independent review; weekly automatic demotion; `python -m nbapicks.rollback` or the `nba-rollback` workflow | none |
| 9 | Scheduler jitter and no per-game timing on Actions | Prices a few minutes old | Pre-tip refresh runs at 22:30 and 23:15 UTC; stale odds hold picks (120 min) | Per-game timing needs a server (not chosen) |
| 10 | Correlated parlay legs | Overstated joint probability | Parlays and lotto are research only and labelled so; legs from different games | Correlation model not built |
| 11 | Combination props have no prices | Cannot be evaluated for edge | `combos.py` projects only, marked `research_only` | Needs a feed with combo lines |
| 12 | Secrets | Discord webhook leak | Webhook only as a repo secret; Discord skipped for now | Re-add when wanted |
