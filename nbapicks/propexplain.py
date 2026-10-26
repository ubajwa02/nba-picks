"""Evidence behind a prop candidate, from box scores only (point in time).

Every number carries its sample: hits/n over the exact line, the last five values,
the season average with its game count. These are context for the reader; they are
not the model probability (that comes from the prop model) and are never used as one.
"""
from __future__ import annotations

import datetime as dt
from collections import defaultdict

from .settle import _over_under


def _d(start_utc: str) -> dt.date:
    return (dt.datetime.fromisoformat(start_utc.replace("Z", "+00:00")) - dt.timedelta(hours=6)).date()


def season_of(d: dt.date) -> int:
    return d.year + 1 if d.month >= 8 else d.year


class Logs:
    """player_id -> [(date, game_id, team, opp, minutes, starter, stats)] for games played, sorted."""

    def __init__(self, box_rows: list[dict], games: dict):
        by = defaultdict(list)
        for r in box_rows:
            g = games.get(str(r["game_id"]))
            if not g or not int(float(r.get("played") or 0)) or float(r.get("minutes") or 0) <= 0:
                continue
            team = r.get("team")
            opp = g["away"] if team == g["home"] else g["home"] if team == g["away"] else None
            by[str(r["player_id"])].append((_d(g["start_utc"]), str(r["game_id"]), team, opp, float(r["minutes"]),
                                           int(float(r.get("starter") or 0)), r))
        self.logs = {k: sorted(v, key=lambda x: x[0]) for k, v in by.items()}

    def before(self, pid: str, date: dt.date) -> list:
        return [x for x in self.logs.get(str(pid), []) if x[0] < date]

    def team_of(self, pid: str, date: dt.date) -> str | None:
        h = self.before(pid, date)
        return h[-1][2] if h else None


def _val(x, stat):
    v = x[6].get(stat)
    return None if v in (None, "") else float(v)


def _hits(rows, stat, line, side):
    h = n = pushes = 0
    for x in rows:
        v = _val(x, stat)
        if v is None:
            continue
        r = _over_under(side, v, line)
        if r == "push":
            pushes += 1; continue
        n += 1; h += r == "win"
    return dict(h=h, n=n, pushes=pushes)


def explain(logs: Logs, pid: str, stat: str, line: float, side: str, date: dt.date, opp: str | None) -> dict:
    hist = logs.before(pid, date)
    season = [x for x in hist if season_of(x[0]) == season_of(date)]
    vals = [v for x in season if (v := _val(x, stat)) is not None]
    last = [v for x in reversed(hist[-5:]) if (v := _val(x, stat)) is not None]
    l10 = [v for x in hist[-10:] if (v := _val(x, stat)) is not None]
    vs = [x for x in hist if x[3] == opp]
    vs_vals = [v for x in vs if (v := _val(x, stat)) is not None]
    starts = [x[5] for x in hist[-5:]]
    out = dict(season=dict(avg=round(sum(vals) / len(vals), 2) if vals else None, n=len(vals)),
               last5=last, last10_avg=round(sum(l10) / len(l10), 2) if l10 else None,
               line_hits=_hits(season, stat, line, side), line_hits_last10=_hits(hist[-10:], stat, line, side),
               vs_opp=dict(_hits(vs, stat, line, side), avg=round(sum(vs_vals) / len(vs_vals), 2) if vs_vals else None),
               role=("starter" if sum(starts) >= 3 else "bench") if starts else None,
               recent_minutes=round(sum(x[4] for x in hist[-5:]) / len(hist[-5:]), 1) if hist else None)
    flags = []
    if len(vals) < 10:
        flags.append("low_sample")
    out["flags"] = flags
    return out
