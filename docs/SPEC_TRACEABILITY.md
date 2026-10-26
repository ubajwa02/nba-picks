# NBA Betting Intelligence spec: traceability and gap list (2026-10-26)

Status key: DONE = built, tested and running; PART = partly built; GAP = not built; DECISION = needs Uday's choice (cost, provider or risk). Evidence is in the repo `ubajwa02/nba-picks` (237 tests pass).

## Where the spec and the current system differ on architecture
The spec assumes a persistent cloud server, PostgreSQL, `nba_api` and an off-GitHub repo. The current system is Python on **GitHub Actions** (scheduled), with an append-only JSONL ledger replayed into SQLite, a static dashboard, and ESPN plus bet365/MovioOdds as data. It already satisfies the *behavioural* requirements below; the infrastructure sections (4, 13, 16) are the main gap.

## Requirement table
| § | Requirement | Status | Implementation / test / evidence | Gap or next step |
|---|---|---|---|---|
| 1-2 | Autonomous, no real-money bets, 1 unit straights, parlays separate | DONE | `nbapicks/pipeline.py`, `qualify.py`; parlays are research-only (`parlay.py`, `build_parlays`); stakes in `config/nbapicks.yaml`; `test_upgrade_pipeline.py` | none |
| 2 | Props: pts/reb/ast/3PM, over+under | DONE | `models/props_v1.py` (negative binomial, minutes projection, teammates-out, opponent); both sides recorded (`propsides.py`) | combination props (PRA, PR, PA, RA): `combos.py` empirical estimator, research only and unpriced because no feed lists combo prices; not wired into picks |
| 2 | Minutes, matchup, availability, pace, home/away | PART | minutes, role, opponent, teammates-out in props-v1; pace proxy built (`pace_k`) and tested on validate: no gain (all t < 2), so it stays off (decision 2026-10-26); starter role tested and rejected earlier | home/away effect not modelled separately |
| 3A | Historical stats: `nba_api`, caching, backoff, fallback | PART | ESPN box scores 2023-26 cached in `data/history`; stats.nba.com and cdn.nba.com **time out / 403 from GitHub runners** (`docs/sources.yaml`) | DECISION: test `nba_api` from the chosen server; ESPN stays the fallback |
| 3B | Injuries with timestamps; no hindsight in backtests | PART | ESPN injury list observed per run (`data/ledger/injuries`), stale-report hold (240 min); no historical injury history exists, so backtest teammates-out uses the game's own box (flagged optimistic, in skeptic review) | NBA official injury PDFs parser GAP (candidate in sources.yaml) |
| 3C | Odds/props prices, timestamps, no fabrication | DONE (limits) | DraftKings via ESPN (unlabelled sides: labelled from bet365 ladder or priced conservatively), bet365 via MovioOdds; every snapshot timestamped; implausible alt-ladder pairs now dropped | **No FanDuel or multi-book prop feed.** DECISION: The Odds API paid tier if wanted |
| 3D | Ingestion validation, suppress picks on failure | DONE | `nbapicks/validate.py`: games, box scores, injuries, odds; naive timestamps rejected; injury-vs-box team conflicts hold the prop; failing critical sources hold every pick; empty injury feed goes stale and holds. Tests in `tests/test_validate.py` | none
| 4 | Postgres, server, encrypted off-GitHub backups, restore doc | PART | Decision 2026-10-26: stay on free GitHub Actions, no server or Postgres. `nba-backup` workflow bundles the repo when it changes; `tools/backup_local.sh` mirrors it to the Mac; `docs/BACKUP.md` has restore steps | not encrypted (private repo needed first); Uday must keep a copy outside GitHub |
| 5 | Distribution model, baselines | DONE | props-v0 (baseline), splitcard, naive, props-v1; discrete NB with push handling | Poisson / ML families compared only on request |
| 6 | EV with push, de-vig, 5% threshold, unpriced labelled | DONE | `odds.py`, `qualify.py`, `max_ev` plausibility hold; props min EV 5% | none |
| 7 | Backtest engine, no leakage, walk-forward | DONE (limits) | `propbacktest.py`, `backtest.py`, `monthtest.py`; real DK prices exist only Oct-Nov 2025 and Apr-Jun 2026; holdout 2026-02-01..06-30 untouched | drawdown and per-player breakdowns: check `reports/backtest_props.md` and add if missing |
| 8 | Paper mode, immutable predictions, settle | DONE | versioned ledger, `settle.py`, corrections as events | pre-registered paper gates exist in `config/gates.yaml` |
| 9-10 | Research ledger, champion/challenger, rollback | DONE | `weekly.py`, `research.py`, `data/research/*`; props-v1 promoted via gate + skeptic review; auto-demotion to props-v0 | model rollback by `champion.json` edit; `python -m nbapicks.rollback` and the manual `nba-rollback` workflow; see `docs/MODEL_VERSIONING.md` |
| 11 | Discord alerts, dedupe, line-change updates | PART (Discord skipped by decision 2026-10-26) | `discord.py` (dry run; needs `NBA_DISCORD_WEBHOOK_URL`); dedupe by pred version | line-change update messages and caveat fields: verify against §11 list |
| 12 | Dashboard | DONE | 8-tab dashboard, separate populations (qualified / all model / leans / signals / wagers) | by-model-version table verify |
| 13 | Health checks, global pause, backups, disk, restart recovery | PART | run logs, freshness warnings, global pause (`data/state/PAUSED` or `pause: true`) with dashboard banner, backup bundle on change | no failure alerts (Discord skipped by decision); no disk/restart concerns on Actions |
| 14 | Event-aware schedule | PART | cron runs plus a 22:30 UTC pre-tip refresh, not per-game | per-slate scheduling needs a server or dispatcher |
| 15-16 | Cost, security, separate from SPY system | DONE/PART | no secrets in repo; separate repo from tradingbot; **repo is public** | DECISION: make repo private; secrets scanning |
| 18 | 14 deliverables | DONE (drafts) | architecture, sources, contracts, operations, platform/deployment/cost plan, `BACKUP.md`, `RISKS.md`, `MODEL_VERSIONING.md` | cost figures for a server are estimates to confirm before any purchase |
| 19 | Definition of done | PART | reproducible predictions, no look-ahead, settled results, gated promotion all shown | backups restorable, runs without Claude Code on a server, failure suppression: open |

## What I can build now without your decisions
1. Global pause (flag file or config switch) honoured by predict and publish, with tests and dashboard banner.
2. Failure notifications and health summary (Discord/file) once the webhook exists.
3. Schema-change and impossible-value validators per source.
4. Missing deliverable documents: deployment, backup/restore, monitoring/recovery, cost estimate, risk register.
5. Pace and starter-role terms for props-v1, evaluated on the validate window only.

## Choices that are yours
1. **Hosting**: the spec wants a persistent server. Options: keep GitHub Actions (free, already works, no Postgres), or a small VPS (roughly $5-12 per month) running Postgres and cron. I recommend a small VPS only if you want event-aware per-game scheduling and real backups; otherwise Actions plus a nightly encrypted export is cheaper.
2. **Repo provider** after the earlier GitHub suspension: the code is on GitHub now. A second private mirror (GitLab, Codeberg) is free.
3. **Backup target**: encrypted object storage (cost small) plus an external drive.
4. **Paid odds** (The Odds API) for FanDuel and more books: not added without your OK.
