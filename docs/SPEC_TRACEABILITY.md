# NBA Betting Intelligence spec: traceability and gap list (2026-10-26)

Status key: DONE = built, tested and running; PART = partly built; GAP = not built; DECISION = needs Uday's choice (cost, provider or risk). Evidence is in the repo `ubajwa02/nba-picks` (225 tests pass).

## Where the spec and the current system differ on architecture
The spec assumes a persistent cloud server, PostgreSQL, `nba_api` and an off-GitHub repo. The current system is Python on **GitHub Actions** (scheduled), with an append-only JSONL ledger replayed into SQLite, a static dashboard, and ESPN plus bet365/MovioOdds as data. It already satisfies the *behavioural* requirements below; the infrastructure sections (4, 13, 16) are the main gap.

## Requirement table
| § | Requirement | Status | Implementation / test / evidence | Gap or next step |
|---|---|---|---|---|
| 1-2 | Autonomous, no real-money bets, 1 unit straights, parlays separate | DONE | `nbapicks/pipeline.py`, `qualify.py`; parlays are research-only (`parlay.py`, `build_parlays`); stakes in `config/nbapicks.yaml`; `test_upgrade_pipeline.py` | none |
| 2 | Props: pts/reb/ast/3PM, over+under | DONE | `models/props_v1.py` (negative binomial, minutes projection, teammates-out, opponent); both sides recorded (`propsides.py`) | combination props (PRA etc.) GAP |
| 2 | Minutes, matchup, availability, pace, home/away | PART | minutes + opponent + teammates-out in props-v1; pace and starter/bench role only implicit | add pace term and explicit starter flag; test via `propbacktest` gate |
| 3A | Historical stats: `nba_api`, caching, backoff, fallback | PART | ESPN box scores 2023-26 cached in `data/history`; stats.nba.com and cdn.nba.com **time out / 403 from GitHub runners** (`docs/sources.yaml`) | DECISION: test `nba_api` from the chosen server; ESPN stays the fallback |
| 3B | Injuries with timestamps; no hindsight in backtests | PART | ESPN injury list observed per run (`data/ledger/injuries`), stale-report hold (240 min); no historical injury history exists, so backtest teammates-out uses the game's own box (flagged optimistic, in skeptic review) | NBA official injury PDFs parser GAP (candidate in sources.yaml) |
| 3C | Odds/props prices, timestamps, no fabrication | DONE (limits) | DraftKings via ESPN (unlabelled sides: labelled from bet365 ladder or priced conservatively), bet365 via MovioOdds; every snapshot timestamped; implausible alt-ladder pairs now dropped | **No FanDuel or multi-book prop feed.** DECISION: The Odds API paid tier if wanted |
| 3D | Ingestion validation, suppress picks on failure | DONE (scoreboard, box, injuries) / PART (odds) | `nbapicks/validate.py` wired into ingest and boxes: missing fields (schema change), duplicates, missing ids, impossible stat lines, bad times, final without score, one-team box scores, empty or unusable injury feed (keeps the old file so it goes stale and holds picks). 8 tests in `tests/test_validate.py` | `validate_odds` exists and is tested but is not yet wired into `put_odds`; time-zone and conflicting player-team checks still open |
| 4 | Postgres, server, encrypted off-GitHub backups, restore doc | GAP | none (JSONL in git is the store) | DECISION: host + backup target (see below) |
| 5 | Distribution model, baselines | DONE | props-v0 (baseline), splitcard, naive, props-v1; discrete NB with push handling | Poisson / ML families compared only on request |
| 6 | EV with push, de-vig, 5% threshold, unpriced labelled | DONE | `odds.py`, `qualify.py`, `max_ev` plausibility hold; props min EV 5% | none |
| 7 | Backtest engine, no leakage, walk-forward | DONE (limits) | `propbacktest.py`, `backtest.py`, `monthtest.py`; real DK prices exist only Oct-Nov 2025 and Apr-Jun 2026; holdout 2026-02-01..06-30 untouched | drawdown and per-player breakdowns: check `reports/backtest_props.md` and add if missing |
| 8 | Paper mode, immutable predictions, settle | DONE | versioned ledger, `settle.py`, corrections as events | pre-registered paper gates exist in `config/gates.yaml` |
| 9-10 | Research ledger, champion/challenger, rollback | DONE | `weekly.py`, `research.py`, `data/research/*`; props-v1 promoted via gate + skeptic review; auto-demotion to props-v0 | model rollback by `champion.json` edit; add one-command rollback doc |
| 11 | Discord alerts, dedupe, line-change updates | PART | `discord.py` (dry run; needs `NBA_DISCORD_WEBHOOK_URL`); dedupe by pred version | line-change update messages and caveat fields: verify against §11 list |
| 12 | Dashboard | DONE | 8-tab dashboard, separate populations (qualified / all model / leans / signals / wagers) | by-model-version table verify |
| 13 | Health checks, **global pause**, backups, disk, restart recovery | GAP | run logs and freshness warnings exist; **no global pause switch**, no backups, no alerting on failure | build pause file/flag checked by predict+publish (small); rest depends on hosting |
| 14 | Event-aware schedule | PART | cron runs plus a 22:30 UTC pre-tip refresh, not per-game | per-slate scheduling needs a server or dispatcher |
| 15-16 | Cost, security, separate from SPY system | DONE/PART | no secrets in repo; separate repo from tradingbot; **repo is public** | DECISION: make repo private; secrets scanning |
| 18 | 14 deliverables | PART | architecture, sources, contracts, ops docs exist | missing: deployment plan, security/backup plan, monitoring plan, cost estimate, risk list |
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
