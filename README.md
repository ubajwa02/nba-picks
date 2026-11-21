# NBA Picks

A research and paper-trading system for NBA betting markets, built on free data only. It ingests games, injuries and multi-book odds, prices moneylines, spreads, totals and player props, filters candidates through data-quality, risk and skeptic gates, keeps an immutable prediction ledger separate from your real wagers, settles everything automatically, and publishes a dark analytics dashboard plus optional Discord posts.

**It never places bets.** Real wagers count only when you enter them in `data/manual/wagers.csv` with the actual FanDuel price and stake.

## Current honest status (2026-10-20)

- Every market is in **research** status. Walk-forward testing over 2014-15 to 2022-23 found no model edge over closing lines (`reports/research_latest.md`, `reports/backtest_raw_model.md`), so nothing is published as a qualified pick. The system records a forward "research record" of watch-level candidates to test whether earlier prices are softer than closing ones (backlog NBA-016).
- Promotion from research to paper to live is governed by gates written before any result was seen (`config/gates.yaml`). The 2024-26 holdout has not been scored because no candidate reached it.
- Discord publishing runs in dry-run until the `NBA_DISCORD_WEBHOOK_URL` secret exists and `publishing.dry_run` is set to `false`.

## Posted picks (2026-11-17)

The daily picks no longer come from the prop model. `reports/red_week_2026-11.md` shows it has no measured skill beyond the book's price, and that the old rule (most likely props first) lost about 6% per bet. A pick is now a FanDuel prop whose price beats the DraftKings fair price for the same line by 5%, ranked by that edge and graded at the FanDuel price (`nbapicks/leans.py`). Days with no pick are normal. This rule is research, not validated.

## Layout

| path | what |
|---|---|
| `nbapicks/` | the package: sources, ledger, models, qualification, parlays, props, settlement, Discord, pipeline, research, diagnostics, dashboard export |
| `config/nbapicks.yaml` | stakes, targets, market status, thresholds, quality gates, risk caps, publishing |
| `config/gates.yaml` | pre-registered promotion and demotion gates |
| `data/ledger/` | append-only JSONL ledger (source of truth); replayed into SQLite with constraints |
| `data/history/` | backfilled games, closing odds and box scores per season |
| `data/manual/` | your inputs: `wagers.csv` (actual bets), `signals.csv` (Discord picks pasted by hand) |
| `data/research/` | experiment registry, champion, decisions log, diagnostic queue |
| `site/` | dashboard (`index.html` + `data.json`) |
| `team/` | AI team roles, backlog, scorecards, independent reviews |
| `docs/` | sources inventory, architecture, operations runbook |
| `reports/` | source probes, backfill logs, backtests, research and diagnostics reports |

## Quick start

```bash
pip install -r requirements.txt
python -m pytest -q                      # 92+ tests, offline, on recorded real responses
python -m nbapicks.pipeline --steps ingest,predict,publish,settle,recap,diagnose,export   # needs network
python -m nbapicks.research              # walk-forward experiments on data/history
```

Live data is fetched from GitHub Actions runners (see `docs/OPERATIONS.md`); the development container has no route to the sports data hosts.

Docs: [architecture](docs/ARCHITECTURE.md) · [operations](docs/OPERATIONS.md) · [data sources](docs/sources.yaml)
