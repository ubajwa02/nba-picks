# Backup and restore (free, on change)

Goal: never depend on GitHub alone. Two copies, both free.

## 1. Automatic bundle (no action needed)
Workflow `nba-backup` builds `nba-picks.bundle` (every branch, full history) and attaches it to the run as the artifact `nba-picks-bundle`, kept 90 days. It runs when `main` changes: on every push and after each `nba-daily`, `nba-backfill`, `nba-research` and `nba-backtest` run. Nothing is created when nothing changed.
To keep it: GitHub → Actions → nba-backup → latest run → download `nba-picks-bundle`, unzip and store the file somewhere outside GitHub (Mac, external drive, iCloud/Drive).

## 2. Local mirror on your Mac (recommended, 30 seconds)
Run `tools/backup_local.sh` (or copy the command below). It keeps a full mirror in `~/nba-picks-backup` and writes a dated bundle next to it. Run it whenever you like, for example after a change you care about.
    git clone --mirror https://github.com/ubajwa02/nba-picks.git ~/nba-picks-backup/nba-picks.git

## Restore on a new repo or machine
    git clone nba-picks.bundle nba-picks        # from a bundle
    cd nba-picks && git remote set-url origin <new repo url> && git push --all origin
Then re-add the secret `NBA_DISCORD_WEBHOOK_URL` (secrets are never in the backup), confirm Settings → Actions is enabled, and run the `nba-tests` workflow. Check: `python -m pytest -q` passes and the dashboard totals match the old ones.

## What is not backed up
Secrets, GitHub settings and Actions run history. The artifact expires after 90 days, so a copy outside GitHub is the real backup.
