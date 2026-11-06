"""Minute of the New York day at which today's picks may post (printed for nba-daily.yml).

Default: 16:30 on weekdays, 11:00 on weekends. When today's first tip is early (weekend
matinees, holidays such as MLK Day, Christmas or Black Friday), picks move to two hours
before that tip, but never before 10:00 (props are rarely posted earlier).
Reads today's games from data/ledger/games.jsonl (last record per game wins). stdlib only.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sys
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")
WEEKDAY, WEEKEND, FLOOR, LEAD = 16 * 60 + 30, 11 * 60, 10 * 60, 120


def first_tip_minute(path: str, today: dt.date) -> int | None:
    if not os.path.exists(path):
        return None
    games = {}
    with open(path) as fh:
        for line in fh:
            if line.strip():
                r = json.loads(line)
                games[r["game_id"]] = r
    tips = []
    for r in games.values():
        if r.get("start_utc") and r.get("status") not in ("postponed", "cancelled"):
            t = dt.datetime.fromisoformat(r["start_utc"].replace("Z", "+00:00")).astimezone(NY)
            if t.date() == today:
                tips.append(t.hour * 60 + t.minute)
    return min(tips) if tips else None


def target(now: dt.datetime, first_tip: int | None) -> int:
    base = WEEKEND if now.isoweekday() >= 6 else WEEKDAY
    return base if first_tip is None else max(FLOOR, min(base, first_tip - LEAD))


if __name__ == "__main__":
    now = dt.datetime.now(NY)
    path = sys.argv[1] if len(sys.argv) > 1 else "data/ledger/games.jsonl"
    print(target(now, first_tip_minute(path, now.date())))
