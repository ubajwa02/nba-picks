# Deployment, backup, monitoring and cost plan (draft, 2026-10-26)

Status: plan only. Nothing here is bought or provisioned; every paid item needs the owner's approval.

## 1. Deployment options
| | A. GitHub Actions (current) | B. Small VPS + Postgres |
|---|---|---|
| Cost | $0 | about $5-12 per month plus backup storage |
| Scheduling | cron, minutes of jitter, no per-game timers | systemd timers or a scheduler that sets per-game jobs |
| Store | JSONL ledger in git, SQLite replay | PostgreSQL, ledger kept append-only |
| Data-source reach | ESPN works; stats.nba.com and cdn.nba.com blocked | test `nba_api` from the server first |
| Independence from GitHub | none: code, state and runner all there | code mirrored; state on the server |
| Risks | single provider; repo is public; state commits | one machine to patch and back up |
Recommendation: stay on A until a reason for B appears (per-game timing, `nba_api`, backups off GitHub). If B, keep the ledger format and add Postgres as a replayed index, so the append-only record remains the source of truth.

## 2. Backup and restore
- Nightly: export `data/ledger`, `data/research`, `data/state` to a tarball, encrypt with `age`, upload to object storage outside GitHub (Backblaze B2 or similar, cents per month) and copy to the external drive monthly.
- Restore test monthly: download, decrypt, replay into an empty directory, run `python -m nbapicks.pipeline export`, compare ledger row counts and the dashboard totals with the source. Record the result in `data/research/decisions.jsonl`.
- Secrets live only in the host's secret store; the backup key is held offline by the owner.

## 3. Monitoring and recovery
- Every run writes `data/state/runs.jsonl`; the dashboard shows stale odds, failed sources and last success per step.
- Add: failure notice to a Discord ops channel after two consecutive failed runs; a freshness check that sets the global pause when odds or injuries are older than the configured limits for more than a slate; disk-space check (server option only).
- Global pause (`data/state/PAUSED` or `pause: true`) blocks new recommendations; resuming is manual after health checks pass.
- Rollback of a model: edit `data/research/champion.json` to the previous model id and add a decisions entry; the weekly job also demotes a badly calibrated prop model automatically.

## 4. Operating-cost estimate
| item | now | if server | if paid odds |
|---|---|---|---|
| compute | $0 | $5-12/mo | - |
| backups | $0 | under $1/mo | - |
| odds data | $0 | - | The Odds API paid tier, price to be confirmed on the vendor site before purchase |
| Discord | $0 | $0 | $0 |

## 5. Unresolved risks and dependencies
1. The repo is public; make it private and rotate nothing is needed (no secrets committed), but private wager data must never be added.
2. No FanDuel feed; prices come from DraftKings (unlabelled sides) and bet365.
3. Real historical prop prices exist only for Oct-Nov 2025 and Apr-Jun 2026; the holdout window is untouched and can be used once.
4. Backtest teammates-out uses the game's own box score, which flatters results.
5. No prop market has shown an edge at real prices; every market stays research.
6. GitHub suspension history: a second mirror is advised.
7. `nba_api` reliability from a server is untested.
