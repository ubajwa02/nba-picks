# NBA Picks: baseline audit (2026-10-20)

Persistent baseline taken before anything was built. Evidence lives in the repo branch `bajwa19u/tradingbot@nba-picks` unless noted.

## Repositories

| repo | finding |
|---|---|
| bajwa19u/tradingbot | Stock/crypto trading bot (`src/`, `config.yaml`, GitHub Actions, Discord webhook). No NBA code. Chosen host for NBA Picks as an **orphan branch `nba-picks`** so `main` is untouched. |
| bajwa19u/vwap-ema-swing | Equity swing strategy. No NBA code. |
| bajwa19u/job-search-dashboard | Job search tool. No NBA code. |
| bajwa19u/nba-picks | Does not exist. Creating a repo needs your approval (decision card in the thread). |

Baseline: **no NBA Picks code, data, models, ledger, dashboard or tests existed anywhere accessible.**

## AI Engineering roles and Command Center

No role definitions, agent configs, task boards or Command Center were found in the three repos, this project's files, or the account's skills. Built instead: `team/roles.yaml` (10 roles, each naming what actually executes it), `team/backlog.yaml`, `team/reviews/`, `team/scorecards.yaml`, and a Command Center view in the dashboard that reads them. If you have a Command Center elsewhere, say where and it can be wired in.

## Data sources (probed from GitHub Actions runners; `reports/source_probe*.md`)

| source | result | use |
|---|---|---|
| ESPN site API | 200, scoreboard, summary/box score, injuries | games, results, injuries, settlement |
| ESPN core API odds | 200; untimed final lines 2013-14 to 2022-23, open and close from 2023-24; DraftKings current | game lines, history |
| MovioOdds | 200 with occasional 429; bet365 game lines and milestone props; no terms page | optional reference prices, prop-side check |
| NBA CDN / stats.nba.com | 403 / timeout from runners | rejected |
| The Odds API | needs a key (free tier) | candidate, not wired |
| FanDuel Ontario | no permitted feed | execution book only; picks state a minimum acceptable FanDuel price |
| balldontlie, basketball-reference | key/paid tier or scraping terms | rejected |
| Discord | webhook only (no bot token, no read access) | publishing; ingestion of others' picks is manual paste |

## Infrastructure

- Development container: no network route to sports data hosts (PyPI and GitHub only), so all live fetching runs on GitHub Actions, like Uday's other repos.
- GitHub fires scheduled crons only from a default branch, so on the `nba-picks` branch runs are triggered by pushing `ops/trigger`. A dedicated repo removes this limit.
- No hosting, database or paid service was added. Storage is the git repo itself (append-only JSONL).

## Gaps found and how they were closed

See `FINAL_REPORT.md` in this folder.

Outcome and the gaps closed since this baseline: [FINAL_REPORT.md](FINAL_REPORT.md).
