"""Player availability for the team model: how much regular production is missing from a game.

Production metric (one number per player-game, points scale; a simplified Hollinger game score
that uses only the columns every ESPN box file has):

    prod = pts + 0.4*reb + 0.7*ast + stl + 0.7*blk - tov

Shot volume (fga/fta) and plus-minus exist only in box files fetched after 2026-10-22, so they
are deliberately left out: a metric that changed with the file vintage would make seasons
incomparable and give the model a feature whose scale drifts with data coverage.

A player's value is the recency-weighted mean of prod over his games this season strictly
before the prediction day (exponential weights, half-life `half_life_days`), for players with
at least `min_games` games played this season. A team's *regulars* for a game are the players
who averaged >= `min_mpg` minutes over the team's last `last_n` games before that day (total
minutes over those team games / number of team games, so a player who sat most of them is not
a regular: his absence is already in the team's recent results).

missing value = sum of the values of regulars who are absent.

LEAKAGE CAVEAT (reported with every result that uses this feature):
  * In backtests "absent" means the regular does not appear as having played in that game's box
    score. That is known only after the game and includes late scratches that a bettor could not
    have known before the price was taken. Backtest gains are therefore an upper bound.
  * Live, "absent" means listed Out or Doubtful on the pregame injury report (passed in as
    player ids); late scratches are missed and some Doubtful players play.
  * Trades: a regular traded away counts as missing for his old team (correctly: he is gone) until he
    drops out of its last-10 window. The injury report never lists him, so live callers must remove
    players no longer on the roster from the regulars themselves.
Everything else (values, regulars, the fitted coefficients) uses only games before the day.
"""
from __future__ import annotations

import datetime as dt
import glob
import math
import os
from bisect import bisect_left
from collections import defaultdict
from typing import Iterable

PROD_WEIGHTS = {"pts": 1.0, "reb": 0.4, "ast": 0.7, "stl": 1.0, "blk": 0.7, "tov": -1.0}
LEAKAGE_NOTE = ("Availability caveat: in backtests a regular counts as missing when he does not appear in that "
                "game's box score (known only after the game, includes late scratches), so backtest gains are "
                "an upper bound; live use relies on the pregame injury report (Out/Doubtful). A regular traded away also counts "
                "as missing for his old team in backtests.")


def _f(v) -> float:
    if v in (None, ""):
        return 0.0
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _played(r: dict) -> bool:
    return str(r.get("played", "")).strip() in ("1", "True", "true") and _f(r.get("minutes")) > 0


def production(r: dict) -> float:
    """Box 'game score' of one player-game (see module docstring)."""
    return sum(w * _f(r.get(k)) for k, w in PROD_WEIGHTS.items())


def _date(v) -> dt.date:
    return v if isinstance(v, dt.date) else dt.date.fromisoformat(str(v)[:10])


def _ginfo(g) -> tuple[dt.date, int | None]:
    """(date, season) from a Game object or a dict with date/season."""
    if isinstance(g, dict):
        return _date(g["date"]), (int(g["season"]) if g.get("season") not in (None, "") else None)
    return g.date, getattr(g, "season", None)


class BoxIndex:
    """Box rows indexed for point-in-time lookups. games: {game_id: Game or {date, season}}."""

    def __init__(self, box_rows: Iterable[dict], games: dict):
        self.games = {gid: _ginfo(g) for gid, g in games.items()}
        self.names: dict[str, str] = {}
        self.by_game_team: dict[tuple[str, str], dict[str, dict]] = defaultdict(dict)
        team_games: dict[str, set] = defaultdict(set)
        pg: dict[str, list] = defaultdict(list)
        for r in box_rows:
            gid = r["game_id"]
            if gid not in self.games:
                continue
            d, season = self.games[gid]
            pid, team = str(r["player_id"]), r["team"]
            self.names[pid] = r.get("player_name") or pid
            played = _played(r)
            self.by_game_team[(gid, team)][pid] = dict(minutes=_f(r.get("minutes")) if played else 0.0, played=played)
            team_games[team].add((d, gid, season))
            if played:
                pg[pid].append((d, gid, season, production(r)))
        self.team_games = {t: sorted(v) for t, v in team_games.items()}
        self.player_games = {p: sorted(v) for p, v in pg.items()}
        self.games_with_box = {gid for gid, _ in self.by_game_team}

    # ---- point-in-time pieces -----------------------------------------------------------
    def value(self, pid: str, before: dt.date, season: int | None, half_life_days: float = 30.0,
              min_games: int = 5) -> float | None:
        rows = self.player_games.get(pid, [])
        i = bisect_left(rows, (before,))
        xs = [(d, p) for d, _, s, p in rows[:i] if season is None or s == season]
        if len(xs) < min_games:
            return None
        ws = [math.exp(-math.log(2) * (before - d).days / half_life_days) for d, _ in xs]
        return sum(w * p for w, (_, p) in zip(ws, xs)) / sum(ws)

    def last_team_games(self, team: str, before: dt.date, season: int | None, last_n: int = 10) -> list[str]:
        tg = self.team_games.get(team, [])
        i = bisect_left(tg, (before,))
        return [gid for d, gid, s in tg[:i] if season is None or s == season][-last_n:]

    def regulars(self, team: str, before: dt.date, season: int | None, min_mpg: float = 20.0,
                 last_n: int = 10) -> set[str]:
        gids = self.last_team_games(team, before, season, last_n)
        if not gids:
            return set()
        mins: dict[str, float] = defaultdict(float)
        for gid in gids:
            for pid, r in self.by_game_team.get((gid, team), {}).items():
                mins[pid] += r["minutes"]
        return {p for p, m in mins.items() if m / len(gids) >= min_mpg}

    def played_ids(self, game_id: str, team: str) -> set[str]:
        return {p for p, r in self.by_game_team.get((game_id, team), {}).items() if r["played"]}


def player_values(box_rows: Iterable[dict], games: dict, before: dt.date, season: int | None = None,
                  half_life_days: float = 30.0, min_games: int = 5, index: BoxIndex | None = None) -> dict[str, float]:
    """{player_id: value} as of `before` (games strictly before it), for players with >= min_games
    games this season. `season` defaults to the season of the latest game before `before`."""
    ix = index or BoxIndex(box_rows, games)
    if season is None:
        prior = [(d, s) for d, s in ix.games.values() if d < before]
        season = max(prior)[1] if prior else None
    out = {}
    for pid in ix.player_games:
        v = ix.value(pid, before, season, half_life_days, min_games)
        if v is not None:
            out[pid] = v
    return out


def expected_regulars(box_rows: Iterable[dict], games: dict, team: str, before: dt.date, season: int | None = None,
                      min_mpg: float = 20.0, last_n: int = 10, index: BoxIndex | None = None) -> set[str]:
    ix = index or BoxIndex(box_rows, games)
    return ix.regulars(team, before, season, min_mpg, last_n)


def missing_value(team: str, values: dict[str, float], expected_regulars: set[str], *,
                  played_ids: set[str] | None = None, out_ids: Iterable[str] | None = None,
                  names: dict[str, str] | None = None) -> tuple[float, list[str]]:
    """(sum of values, [names]) of the team's missing regulars.

    Backtest: pass played_ids (players who played in that game's box); missing = regulars not in it.
    Live: pass out_ids (injury report Out/Doubtful); missing = regulars among them. A regular
    without a value (fewer than min_games this season) counts 0.
    """
    if (played_ids is None) == (out_ids is None):
        raise ValueError(f"{team}: pass exactly one of played_ids (backtest) or out_ids (live)")
    if played_ids is not None:
        miss = [p for p in expected_regulars if p not in played_ids]
    else:
        out = {str(p) for p in out_ids}
        miss = [p for p in expected_regulars if p in out]
    miss.sort(key=lambda p: -values.get(p, 0.0))
    names = names or {}
    return float(sum(values.get(p, 0.0) for p in miss)), [names.get(p, p) for p in miss]


# ---- backtests: attach the feature to Game objects -----------------------------------------
def read_box(hist_dir: str) -> list[dict]:
    from ..history import read_csv
    rows = []
    for path in sorted(glob.glob(os.path.join(hist_dir, "box_*.csv.gz"))):
        rows.extend(read_csv(path))
    return rows


def attach(games: list, box_rows: Iterable[dict], min_mpg: float = 20.0, last_n: int = 10,
           half_life_days: float = 30.0, min_games: int = 5, min_team_games: int = 5) -> dict:
    """Set g.home_missing / g.away_missing / g.avail_known (and *_missing_names) on each Game, point
    in time. A game without a box score, or a team with fewer than min_team_games earlier games
    this season, gets 0 and avail_known False. Returns coverage counts per season."""
    ix = BoxIndex(box_rows, {g.game_id: g for g in games})
    cov: dict = defaultdict(lambda: dict(games=0, games_with_box=0, games_with_feature=0))
    for g in games:
        season = getattr(g, "season", None)
        c = cov[str(season)]; c["games"] += 1
        g.home_missing = g.away_missing = 0.0
        g.home_missing_names, g.away_missing_names = [], []
        g.avail_known = False
        if g.game_id not in ix.games_with_box:
            continue
        c["games_with_box"] += 1
        sides = {}
        for side, team in (("home", g.home), ("away", g.away)):
            if len(ix.last_team_games(team, g.date, season, min_team_games)) < min_team_games:
                break
            regs = ix.regulars(team, g.date, season, min_mpg, last_n)
            vals = {p: v for p in regs if (v := ix.value(p, g.date, season, half_life_days, min_games)) is not None}
            sides[side] = missing_value(team, vals, regs, played_ids=ix.played_ids(g.game_id, team), names=ix.names)
        else:
            (g.home_missing, g.home_missing_names), (g.away_missing, g.away_missing_names) = sides["home"], sides["away"]
            g.avail_known = True
            c["games_with_feature"] += 1
    return {k: dict(v) for k, v in sorted(cov.items())}
