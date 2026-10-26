# Operations

## Where it runs

Everything that needs the network runs on GitHub Actions (`.github/workflows/nba-*.yml`). The code lives on `main` of `ubajwa02/nba-picks` (rebuilt there on 2026-10-26 from the backup after the old bajwa19u account was lost), so the scheduled workflows fire on their own.

| workflow | trigger | does |
|---|---|---|
| nba-daily | cron 15:00, 20:30, 22:30, 23:15, 07:00, 13:00 UTC; push to `ops/trigger`; manual | ingest, predict (every candidate recorded, versioned), publish (20:30 only, dry-run until enabled), settle, recap, diagnose, export; commits ledger, state, reports and `site/` |
| nba-research | Monday 10:00 UTC; manual | `python -m nbapicks.weekly`: diagnostics, queued game challengers, prop-model challengers on the validate window, forward demotion check, `reports/weekly_latest.md`, export |
| nba-backtest | manual (inputs kind, start, end, models, holdout) | `nbapicks.propbacktest` or `nbapicks.monthtest` on cached history; writes `reports/backtest_*.json` (shown on the dashboard) |
| nba-backfill | manual | rebuild `data/history` (games, closing odds, box scores with shot volume, historical prop prices) |
| nba-tests | push to main, pull requests | full test suite |
| nba-probe | manual | capture fresh source responses into `reports/probe_fixtures/` (never over the pinned test fixtures) |
| nba-pages | after daily/weekly/backtest runs, only if repo variable `PAGES_ENABLED` is `true` | optional public copy of `site/` on GitHub Pages |

All writers share the `nba-state` concurrency group, commit only the files they changed on top of the branch tip (`ops/commit_changed.sh`), and mark their commits `[skip ci]`; pushes made with the workflow token do not start other workflows, so generated commits cannot loop.

## Running a backtest

```bash
python -m nbapicks.propbacktest --start 2026-01-01 --end 2026-01-31 --models props-v0,splitcard,props-v1   # props
python -m nbapicks.monthtest --start 2023-02-01 --end 2023-02-28 --variants trend,avail                    # game markets
```
Both use `data/history/*.csv.gz` and cache intermediate results in `data/cache/` (keyed by the input files, function and parameters; `--refresh` rebuilds). Holdout dates are refused without `--holdout`. On GitHub: Actions -> nba-backtest -> Run workflow.

## Diagnosing failures

- **A daily run is red**: open the run log; the last 60 lines are printed. `data/state/runs.jsonl` has one line per run with each step's status and error. A failed ingest (ESPN scoreboard down) marks predict/publish `skipped` on purpose.
- **Dashboard looks stale**: the page shows "Last updated" and a warning banner when the last run failed or odds are older than `quality.max_odds_age_minutes`. Check `data/state/source_health.json` for the failing source.
- **No props priced**: `data/state/last_predict.json` -> `prop_side_check` shows per game how many DraftKings pairs were labelled from the bet365 ladder and how many were priced conservatively.
- **Weekly cycle**: `reports/weekly_latest.md`; experiments in `data/research/experiments.jsonl`; promotions/demotions in `data/research/decisions.jsonl`.

GitHub only fires `schedule` triggers from a repository's default branch. Until NBA Picks has its own repository (or the branch becomes a default branch), runs happen when `ops/trigger` is changed and pushed:

```bash
date -u > ops/trigger && git commit -am "run" && git push
```

## Secrets and settings

| name | where | needed for |
|---|---|---|
| `NBA_DISCORD_WEBHOOK_URL` | repo Settings → Secrets → Actions | posting picks and recaps (create a webhook in the target Discord channel). Never reuse tradingbot's `DISCORD_WEBHOOK_URL`. |
| `publishing.dry_run` | `config/nbapicks.yaml` | set `false` only after the webhook is in place and a dry-run message looks right |
| `ODDS_API_KEY` (optional) | secret | The Odds API, not wired yet (backlog); free tier only |

## Your manual inputs

- `data/manual/wagers.csv`: one row per bet you actually placed (FanDuel odds and stake). Settled automatically; the only source of actual P/L.
- `data/manual/signals.csv`: Discord picks pasted by hand. Rows without a stated price are kept as ambiguous and never priced from invented odds.

See `data/manual/README.md` for columns.

## Recovery

- **Bad run**: the ledger is append-only, so revert the run's commit (`git revert <sha>`) and push; the next run replays from the remaining ledger.
- **Wrong settlement**: add a `corrected` event (never edit a line). Settlement is recomputed from box scores on the next settle step.
- **Source outage**: each run logs per-source health in `data/state/runs.jsonl`; predict refuses to price games whose odds are stale (`quality.max_odds_age_minutes`), so an outage produces no picks rather than bad ones.
- **Rollback a model**: set `data/research/champion.json` back to the previous `model_id` and record why in `data/research/decisions.jsonl`.
- **Turn everything off**: disable the `nba-daily` workflow in the Actions tab.

## Moving to a dedicated repository

1. Create an empty repository (for example `ubajwa02/nba-picks`).
2. Push this branch as its `main`: `git push <new-remote> nba-picks:main`.
3. Add the secrets above, enable Actions, and (optionally) GitHub Pages from `/site`.
Schedules then start on their own.

## Scheduled tasks (Claude project routines, not GitHub cron)
- **NBA research cycle**: Mon and Thu 13:58 America/Toronto. Pre-registered experiment from team/backlog.yaml; priority since 2026-10-21 is player props (NBA-030..033).
- **Grade slate**: one-off runs push `ops/trigger` with `ingest settle export`, grade the posted watchlist at 1u flat and republish the dashboard snapshot (site/index.html with site/data.json embedded).
- Runs: push a change to `ops/trigger` (first line = pipeline steps, optional `--slate YYYY-MM-DD`).

## Global pause
Create `data/state/PAUSED` (optionally `{"reason": "...", "since": "..."}`) or set `pause: true` in `config/nbapicks.yaml` to stop all new recommendations: `predict` and `publish` are skipped and the run records `paused`; `ingest`, `settle` and `export` keep running and the dashboard shows a red banner. Resume by deleting the file (or setting `pause: false`) only after the cause is fixed. Nothing resumes automatically.
