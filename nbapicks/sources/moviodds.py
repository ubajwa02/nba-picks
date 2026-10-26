"""MovioOdds (moviodds.com): free, keyless bet365 feed. Optional comparison source.

Evaluated 2026-10-20 (reports/source_probe2.md): NBA game lines (group 1453
'Game': Line/Total/To Win) plus player milestone props ('Points' 15+, 20+ ...),
per-quote timestamps, /history and /closing since September 2026, /results.
One-developer beta, no published terms page, no uptime guarantee, rate limited
(HTTP 429 seen after two requests in a second). Prices are bet365's, never
FanDuel's, and are labelled book='bet365'.
"""
from __future__ import annotations

import datetime as dt

from ..http import get_json
from ..teams import from_name

BASE = "https://moviodds.com"
GAME_GROUP = "1453"
PROP_GROUPS = {"Points": "pts", "Rebounds": "reb", "Assists": "ast", "Threes Made": "fg3m"}


def fetch_nba() -> dict:
    # one request per run; the response for all basketball is ~8 MB
    return get_json(f"{BASE}/odds?sport=basketball", retries=2, backoff=10, timeout=60)


def match_game(m: dict, games: list[dict], tol_hours: float = 6) -> dict | None:
    home, away = from_name(m.get("home", "")), from_name(m.get("away", ""))
    if not home or not away:
        return None
    try:
        ko = dt.datetime.fromisoformat(m["kickoff_utc"].replace("Z", "+00:00"))
    except Exception:
        return None
    for g in games:
        if {g["home"], g["away"]} != {home, away}:
            continue
        st = dt.datetime.fromisoformat(g["start_utc"].replace("Z", "+00:00"))
        if abs((st - ko).total_seconds()) <= tol_hours * 3600:
            return g
    return None


def parse(d: dict, games: list[dict], observed_at: str) -> tuple[list[dict], list[str]]:
    """Return (odds rows, problems). Only matches with league 'NBA' that map to a known game."""
    rows, problems = [], []
    for m in d.get("matches", []):
        if m.get("league") != "NBA" or m.get("in_play"):
            continue
        g = match_game(m, games)
        if not g:
            problems.append(f"unmapped bet365 match {m.get('away')} @ {m.get('home')} {m.get('kickoff_utc')}")
            continue
        for q in m.get("quotes", []):
            dec = q.get("odds_dec")
            if not dec or dec <= 1:
                continue
            base = dict(game_id=g["game_id"], price_dec=float(dec), book="bet365", source="moviodds", kind="current",
                        observed_at=observed_at, source_updated_at=q.get("ts"))
            if q.get("group_id") == GAME_GROUP:
                team = from_name(q.get("side", ""))
                kind = q.get("line")
                if kind == "To Win" and team:
                    rows.append(dict(base, market="ml", selection="home" if team == g["home"] else "away", line=None))
                elif kind == "Line" and team and q.get("handicap") is not None:
                    rows.append(dict(base, market="spread", selection="home" if team == g["home"] else "away",
                                     line=float(q["handicap"])))
                elif kind == "Total" and q.get("side") in ("Over", "Under"):
                    rows.append(dict(base, market="total", selection=q["side"].lower(), line=float(q["handicap"])))
            elif q.get("group_name") in PROP_GROUPS and q.get("line") and str(q.get("side", "")).isdigit():
                n = int(q["side"])
                rows.append(dict(base, market="prop", selection="over", line=n - 0.5, player_name=q["line"],
                                 stat=PROP_GROUPS[q["group_name"]], flags="milestone_one_sided"))
    return rows, problems
