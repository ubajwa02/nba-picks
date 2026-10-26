"""Ingestion validators. Each takes parsed rows and returns (clean_rows, problems).

Rows that cannot be trusted are dropped and named in `problems`; the caller records a
source failure when the problems are structural (a schema change, an empty feed), so the
affected picks are held instead of being priced from partial data."""
from __future__ import annotations

import datetime as dt

# generous single-game ceilings: anything above is a parsing error, not a performance
LIMITS = dict(minutes=70.0, pts=100, reb=45, ast=40, fg3m=20, stl=15, blk=15, tov=20)
BOX_REQUIRED = ("game_id", "player_id", "team", "minutes", "pts", "reb", "ast")
GAME_REQUIRED = ("game_id", "home", "away", "start_utc", "status")
INJURY_REQUIRED = ("player_id", "team", "status")
ODDS_REQUIRED = ("game_id", "market", "observed_at")
STATUSES = {"Out", "Doubtful", "Questionable", "Probable", "Day-To-Day", "Available", "Suspension"}


def _parse_utc(s):
    try:
        return dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def validate_box_rows(rows: list[dict], game_id: str) -> tuple[list[dict], list[str]]:
    problems, clean, seen = [], [], set()
    if not rows:
        return [], [f"{game_id}: box score has no player rows"]
    for r in rows:
        miss = [k for k in BOX_REQUIRED if k not in r]
        if miss:
            problems.append(f"{game_id}: schema change, missing {','.join(miss)}")
            continue
        pid = r["player_id"]
        if not pid or pid == "None":
            problems.append(f"{game_id}: row without a player id")
            continue
        if pid in seen:
            problems.append(f"{game_id}: duplicate player {pid}")
            continue
        seen.add(pid)
        bad = [k for k, hi in LIMITS.items() if r.get(k) is not None and not 0 <= r[k] <= hi]
        if bad:
            problems.append(f"{game_id}: impossible {','.join(bad)} for player {pid}")
            continue
        if r.get("played") and r.get("minutes") is None:
            problems.append(f"{game_id}: played without minutes for player {pid}")
            continue
        if r.get("played") and r.get("fg3m") is not None and r.get("fga") is not None and r["fg3m"] > r["fga"]:
            problems.append(f"{game_id}: more threes made than field goals tried for player {pid}")
            continue
        clean.append(r)
    teams = {r["team"] for r in clean}
    if clean and len(teams) != 2:
        problems.append(f"{game_id}: box score covers {len(teams)} teams, expected 2")
        return [], problems
    return clean, problems


def validate_games(games: list[dict]) -> tuple[list[dict], list[str]]:
    problems, clean, seen = [], [], set()
    for g in games:
        miss = [k for k in GAME_REQUIRED if k not in g]
        if miss:
            problems.append(f"game schema change, missing {','.join(miss)}")
            continue
        if _parse_utc(g["start_utc"]) is None:
            problems.append(f"game {g['game_id']}: unreadable start time {g['start_utc']!r}")
            continue
        if g["home"] == g["away"]:
            problems.append(f"game {g['game_id']}: same team on both sides")
            continue
        if g["game_id"] in seen:
            continue   # the same game on two scoreboard dates
        seen.add(g["game_id"])
        if g["status"] == "final" and (g.get("home_score") is None or g.get("away_score") is None):
            problems.append(f"game {g['game_id']}: final without a score")
            continue
        clean.append(g)
    return clean, problems


def validate_injuries(rows: list[dict], now: dt.datetime) -> tuple[list[dict], list[str]]:
    """An empty or schema-changed injury feed must never read as 'everyone is healthy'."""
    problems, clean = [], []
    for r in rows:
        miss = [k for k in INJURY_REQUIRED if not r.get(k) or r.get(k) == "None"]
        if miss:
            problems.append(f"injury row for {r.get('player_name', '?')}: missing {','.join(miss)}")
            continue
        if r["status"] == "?":
            problems.append(f"injury row for {r.get('player_name', '?')}: unknown status")
            continue
        when = _parse_utc(r.get("source_date"))
        if when is not None and when > now + dt.timedelta(days=1):
            problems.append(f"injury row for {r.get('player_name', '?')}: report dated in the future")
            continue
        clean.append(r)
    if not rows:
        problems.append("injury feed returned no rows")
    elif not clean:
        problems.append("injury feed had no usable rows")
    return clean, problems


def validate_odds(rows: list[dict]) -> tuple[list[dict], list[str]]:
    problems, clean = [], []
    for r in rows:
        miss = [k for k in ODDS_REQUIRED if not r.get(k)]
        if miss:
            problems.append(f"odds row missing {','.join(miss)}")
            continue
        price = r.get("price_dec")
        if price is not None and not 1.01 <= price <= 1000:
            problems.append(f"odds row {r['game_id']}/{r['market']}: implausible price {price}")
            continue
        clean.append(r)
    return clean, problems
