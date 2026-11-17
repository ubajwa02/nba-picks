#!/usr/bin/env python3
"""Run nba-daily's schedule on a computer instead of GitHub Actions (e.g. while Actions is blocked by billing).

launchd (or cron) calls this every 30 minutes. It works out which nba-daily slot is due in US Eastern time, runs it once
per slot per day in a dedicated clone, and commits the changed files to main with ops/commit_changed.sh, exactly as
the workflow does. Nothing runs when no slot is due, when the stop file exists, or while another run holds the lock.

Slots (America/New_York), same steps as .github/workflows/nba-daily.yml:
  weekdays 11:00            ingest catchup predict settle export          (morning read)
  weekdays 16:30, weekends 11:00   ingest catchup predict publish leans settle export   (picks)
  18:30, 19:15              ingest catchup predict settle export          (pre-tip refresh)
  23:30, 03:00, 09:00       ingest catchup settle recap diagnose export   (grading and results)
A slot runs if it is due and no more than WINDOW_H hours late (missed slots while the Mac slept are caught up once).

Stop it: touch ~/nba-picks-runner/STOP (or unload the launchd job). Logs: ~/nba-picks-runner/logs/.
"""
from __future__ import annotations

import fcntl
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
HOME = Path(os.environ.get("NBA_RUNNER_HOME", Path.home() / "nba-picks-runner"))
REPO_URL = os.environ.get("NBA_REPO_URL", "https://github.com/ubajwa02/nba-picks.git")
WINDOW_H = 3
MORNING = "ingest catchup predict settle export"
PICKS = "ingest catchup predict publish leans settle export"
GRADE = "ingest catchup settle recap diagnose export"
COMMIT_PATHS = ["data/ledger", "data/state", "data/ref", "data/research", "reports", "site"]


def slots(day):
    """(slot id, ET datetime, steps) for one ET calendar day."""
    wkend = day.weekday() >= 5
    out = [("results-0300", (3, 0), GRADE), ("results-0900", (9, 0), GRADE)]
    out += [("picks-1100", (11, 0), PICKS)] if wkend else [("morning-1100", (11, 0), MORNING), ("picks-1630", (16, 30), PICKS)]
    out += [("pretip-1830", (18, 30), MORNING), ("pretip-1915", (19, 15), MORNING), ("grade-2330", (23, 30), GRADE)]
    return [(sid, datetime(day.year, day.month, day.day, h, m, tzinfo=ET), steps) for sid, (h, m), steps in out]


def due(now, done):
    """The latest due slot not yet run (today or yesterday's late slots), or None."""
    cands = []
    for day in (now.date() - timedelta(days=1), now.date()):
        for sid, at, steps in slots(day):
            key = f"{day.isoformat()}:{sid}"
            if at <= now <= at + timedelta(hours=WINDOW_H) and key not in done:
                cands.append((at, key, steps))
    return max(cands) if cands else None


def sh(args, cwd=None, env=None, log=None):
    r = subprocess.run(args, cwd=cwd, env={**os.environ, **(env or {})}, text=True, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT)
    if log: log.write(f"$ {' '.join(args)}\n{r.stdout}\n")
    return r.returncode, r.stdout


def main(argv):
    now = datetime.now(ET)
    HOME.mkdir(parents=True, exist_ok=True)
    (HOME / "logs").mkdir(exist_ok=True)
    if (HOME / "STOP").exists():
        return 0
    lock = open(HOME / ".lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return 0
    state_p = HOME / "done.json"
    done = json.loads(state_p.read_text()) if state_p.exists() else []
    forced = argv[1] if len(argv) > 1 else None          # e.g. nba_local.py "ingest catchup settle export"
    pick = (now, f"manual:{now.isoformat(timespec='minutes')}", forced) if forced else due(now, set(done))
    if not pick:
        return 0
    _, key, steps = pick
    repo = HOME / "repo"
    with open(HOME / "logs" / f"{now:%Y-%m-%d}.log", "a") as log:
        log.write(f"\n=== {now:%Y-%m-%d %H:%M %Z} slot {key}: {steps}\n")
        if not (repo / ".git").exists():
            code, _ = sh(["git", "clone", "-q", REPO_URL, str(repo)], log=log)
            if code: return 1
        sh(["git", "fetch", "-q", "origin", "main"], cwd=repo, log=log)
        sh(["git", "checkout", "-q", "-B", "main", "origin/main"], cwd=repo, log=log)   # dedicated clone: no local work
        venv = HOME / "venv"
        if not (venv / "bin" / "python").exists():
            sh([sys.executable, "-m", "venv", str(venv)], log=log)
        sh([str(venv / "bin" / "pip"), "install", "-q", "-r", "requirements.txt"], cwd=repo, log=log)
        code, out = sh([str(venv / "bin" / "python"), "-m", "nbapicks.pipeline", *steps.split()], cwd=repo, log=log)
        commit_msg = f"nba: {steps} (local runner)"
        ccode, cout = sh(["bash", "ops/commit_changed.sh", commit_msg, *COMMIT_PATHS], cwd=repo,
                         env={"GITHUB_REF_NAME": "main"}, log=log)
        log.write(f"pipeline exit {code}; commit exit {ccode}\n")
        if not forced:
            done = (done + [key])[-200:]
            state_p.write_text(json.dumps(done))
    return 0 if code == 0 and ccode == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
