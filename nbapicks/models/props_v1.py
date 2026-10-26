"""Player-prop model props-v1: expected minutes x per-minute rate x opponent factor,
with a negative-binomial outcome whose dispersion is fitted per stat.

Point-in-time: the model may be built from every box row, but ``predict`` only reads
games whose US/Eastern slate day is strictly before the ``date`` it is given (each
lookup is a bisect on the player's sorted game dates, or a cumulative sum cut at that
date). A game on or after ``date`` never changes a prediction (tests/test_props_v1.py).

Components (every weight below was chosen on the explore split by
``python -m nbapicks.propbacktest --fit``; see reports/props_v1_fit.json):

- Expected minutes: exponentially recency-weighted minutes (half-life in games) over the
  player's played games; previous-season games are down-weighted by a per-season factor,
  so a player with few current-season games falls back to last season with decay. Role
  (starter/bench) comes from the latest 5 games; on a role change the projection can use
  only games in the new role. A player whose team played >= 3 games since his last game
  is "returning_from_absence" and his minutes are scaled by a fitted factor.
- Teammates out: for each listed key teammate (top 3 by minutes this season) the player's
  own with/without split gives a minutes ratio and a per-minute rate ratio; the change is
  measured against the current with/without mix of his recent games and shrunk toward no
  change by n_without / (n_without + MATE_K).
- Per-minute rate: recency-weighted current-season rate, previous seasons down-weighted,
  shrunk toward the league per-minute rate of the player's minutes band (pseudo-minutes K).
  When the box rows carry fga/fg3a (and fta), pts and fg3m use attempt volume x make rate
  with the make rate shrunk separately (needs a fitted ``make_k``; see PARAMS).
- Opponent: the opponent's allowed-per-game of the stat this season relative to the league
  average allowed this season (both before ``date``), shrunk by n_games / (n_games + K).
"""
from __future__ import annotations

import bisect
import copy
import datetime as dt
import math
from collections import defaultdict

import numpy as np

from .. import splitcard as SC
from . import dist

VERSION = "props-v1"
STATS = ("pts", "reb", "ast", "fg3m")
MIN_GAMES = 5            # fewer played games before the date -> abstain (return None)
KEY_MATES = 3            # key teammates = top-3 by minutes per game this season (>= 5 games)
RETURN_GAP = 3           # team games missed since the player's last game -> returning_from_absence
BANDS = (0.0, 15.0, 24.0, 32.0, 99.0)   # minutes bands for the league per-minute prior
MAX_MINUTES = 44.0
FACTOR_CAP = (0.6, 1.6)  # combined teammates-out factor is clipped to this range

# Fitted on the explore split (games before 2025-07-01, ESPN seasons 2023-2025; regular-season
# player-games with >= 10 prior games and >= 10 mpg over the last 10; 1-in-3 hash subsample,
# 21,670 player-games) by `python -m nbapicks.propbacktest --fit` on 2026-10-22 (code at 782cbcd +
# this change): coordinate search, two passes, on mean squared error (minutes for the minutes
# block, stat value given actual minutes for the rate block, full mean for opp_k / mate_k).
# Grids and scores: reports/props_v1_fit.json. No validate or holdout data was used.
# rate_k["reb"] = 5 sits on the lowest grid value: the prior barely matters for rebounds once
# previous seasons are included (MSE 4.920 at 5 vs 4.929 at 50).
PARAMS = {
    "min_half_life": 3.0,          # games (first pass MSE 40.91 vs 42.56 at 7)
    "min_prev_w": 0.1,             # weight multiplier per season back, minutes
    "role_minutes": False,         # on a role change use only games in the new role (rejected on explore)
    "return_factor": 0.892,        # minutes multiplier when returning_from_absence (585 explore events)
    "rate_half_life": {"pts": 20.0, "reb": 40.0, "ast": 10.0, "fg3m": 30.0},
    "rate_prev_w": {"pts": 0.5, "reb": 0.5, "ast": 0.75, "fg3m": 0.5},
    "rate_k": {"pts": 50.0, "reb": 5.0, "ast": 25.0, "fg3m": 25.0},     # pseudo-minutes
    "opp_k": {"pts": 5.0, "reb": 20.0, "ast": 10.0, "fg3m": 20.0},      # pseudo-games
    "mate_k": 40.0,                # pseudo-games for with/without splits (10,726 explore events)
    # Attempt-volume x make-rate path for pts/fg3m. None = off: the history files have no
    # fga/fg3a/fta columns (checked 2026-10-22), so it cannot be fitted on explore yet.
    "make_k": None,
    # Pace proxy: combined points of the two teams' recent games vs the league average this
    # season, shrunk by n / (n + pace_k). None = off (the champion is unchanged); a challenger
    # may switch it on, to be judged on the validate window only (tools/pace_experiment.py).
    "pace_k": None,
}

# Negative-binomial size r per stat (var = mean + mean^2 / r): maximum likelihood on the same
# 21,670 explore events given props-v1 means with the PARAMS above (`--fit`, 2026-10-22).
DISPERSION = {"pts": 3.79, "reb": 10.46, "ast": 12.27, "fg3m": 8.39}

_IDX = {s: i for i, s in enumerate(STATS)}


def _f(x) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def _fn(x) -> float:
    """Optional numeric column: NaN when missing or empty."""
    if x is None or x == "":
        return math.nan
    try:
        return float(x)
    except (TypeError, ValueError):
        return math.nan


def _to_date(d) -> dt.date:
    if isinstance(d, dt.datetime):
        return d.date()
    if isinstance(d, dt.date):
        return d
    return dt.date.fromisoformat(str(d)[:10])


def _season_start(season: int) -> int:
    return dt.date(season - 1, 8, 1).toordinal()


def _band(minutes: float) -> int:
    for b in range(len(BANDS) - 1):
        if minutes < BANDS[b + 1]:
            return b
    return len(BANDS) - 2


def _norm(name: str) -> str:
    return "".join(ch for ch in str(name).lower() if ch.isalpha())


class _Log:
    """One player's played games, sorted by date, as numpy arrays."""
    __slots__ = ("d", "season", "gid", "team", "opp", "home", "starter", "minutes", "vals", "att", "gidset")

    def __init__(self, rows: list[tuple]):
        rows.sort(key=lambda r: (r[0], r[2]))
        self.d = np.array([r[0] for r in rows], dtype=np.int64)
        self.season = np.array([r[1] for r in rows], dtype=np.int64)
        self.gid = [r[2] for r in rows]
        self.team = np.array([r[3] for r in rows], dtype=object)
        self.opp = np.array([r[4] for r in rows], dtype=object)
        self.home = np.array([r[5] for r in rows], dtype=bool)
        self.starter = np.array([r[6] for r in rows], dtype=np.int64)
        self.minutes = np.array([r[7] for r in rows], dtype=float)
        self.vals = np.array([r[8] for r in rows], dtype=float).reshape(len(rows), len(STATS))
        self.att = np.array([r[9] for r in rows], dtype=float).reshape(len(rows), 3)   # fga, fg3a, fta
        self.gidset = set(self.gid)


class PropModelV1:
    version = VERSION

    def __init__(self, box_rows: list[dict], games: dict[str, dict], params: dict | None = None,
                 dispersion: dict | None = None):
        self.params = copy.deepcopy(PARAMS)
        for k, v in (params or {}).items():
            self.params[k] = dict(self.params[k], **v) if isinstance(self.params.get(k), dict) and isinstance(v, dict) else v
        self.dispersion = dict(DISPERSION, **(dispersion or {}))
        gm = {}
        for gid, g in games.items():
            if g.get("start_utc") and g.get("home") and g.get("away"):
                d = SC.et_day(g["start_utc"])
                gm[str(gid)] = (d.toordinal(), SC.season_of(d), g["home"], g["away"])
        per: dict[str, dict] = defaultdict(dict)
        allowed: dict[str, dict] = defaultdict(dict)     # team -> gid -> (d, season, [4 sums])
        self.roster: dict[tuple, set] = defaultdict(set)
        self.names: dict[str, str] = {}
        sched: dict[str, set] = defaultdict(set)
        league_rows = []                                 # (d, band, minutes, vals, att)
        for r in box_rows:
            gid = str(r.get("game_id"))
            g = gm.get(gid)
            team = r.get("team")
            if g is None or team not in (g[2], g[3]):
                continue
            pid = str(r["player_id"])
            if r.get("player_name"):
                self.names[pid] = r["player_name"]
            sched[team].add(g[0])
            mins = _f(r.get("minutes"))
            if not (int(_f(r.get("played"))) and mins > 0):
                continue
            opp = g[3] if team == g[2] else g[2]
            vals = [_f(r.get(s)) for s in STATS]
            att = [_fn(r.get("fga")), _fn(r.get("fg3a")), _fn(r.get("fta"))]
            if gid in per[pid]:
                continue
            per[pid][gid] = (g[0], g[1], gid, team, opp, team == g[2], int(_f(r.get("starter"))), mins, vals, att)
            acc = allowed[opp].setdefault(gid, [g[0], g[1], [0.0] * len(STATS)])
            for i, v in enumerate(vals):
                acc[2][i] += v
            self.roster[(gid, team)].add(pid)
            league_rows.append((g[0], _band(mins), mins, vals, att))
        self.logs = {pid: _Log(list(rs.values())) for pid, rs in per.items()}
        self.team_pids: dict[str, set] = defaultdict(set)
        for (gid, t), ps in self.roster.items():
            self.team_pids[t] |= ps
        self.sched = {t: sorted(v) for t, v in sched.items()}
        # opponent allowed: per team sorted by date, with cumulative sums
        self.allowed = {}
        lg = []
        for t, m in allowed.items():
            rows = sorted(m.values(), key=lambda x: x[0])
            d = np.array([x[0] for x in rows], dtype=np.int64)
            v = np.array([x[2] for x in rows], dtype=float).reshape(len(rows), len(STATS))
            self.allowed[t] = (d, np.vstack([np.zeros(len(STATS)), np.cumsum(v, axis=0)]))
            lg.extend(rows)
        lg.sort(key=lambda x: x[0])
        self._lg_d = np.array([x[0] for x in lg], dtype=np.int64)
        self._lg_cum = np.vstack([np.zeros(len(STATS)), np.cumsum(np.array([x[2] for x in lg], dtype=float).reshape(len(lg), len(STATS)), axis=0)])
        # league per-minute priors by minutes band (cumulative over every earlier game)
        league_rows.sort(key=lambda x: x[0])
        self._pr = []
        for b in range(len(BANDS) - 1):
            rs = [x for x in league_rows if x[1] == b]
            d = np.array([x[0] for x in rs], dtype=np.int64)
            mins = np.concatenate([[0.0], np.cumsum([x[2] for x in rs])])
            vals = np.vstack([np.zeros(len(STATS)), np.cumsum(np.array([x[3] for x in rs], dtype=float).reshape(len(rs), len(STATS)), axis=0)])
            self._pr.append((d, mins, vals))
        # attempt priors (only rows that carry attempts): cumulative minutes, fga, fg3a, fta, pts, fg3m
        ar = [x for x in league_rows if not math.isnan(x[4][0]) and not math.isnan(x[4][1])]
        self._att_d = np.array([x[0] for x in ar], dtype=np.int64)
        a = np.array([[x[2], x[4][0], x[4][1], 0.0 if math.isnan(x[4][2]) else x[4][2], x[3][0], x[3][3]] for x in ar], dtype=float).reshape(len(ar), 6)
        self._att_cum = np.vstack([np.zeros(6), np.cumsum(a, axis=0)])
        self._key_cache: dict = {}
        self._def_cache: dict = {}
        # game totals per team (home + away score of every finished game), for the pace proxy
        tot: dict[str, list] = defaultdict(list)
        lgt = []
        for gid, g in games.items():
            hs, as_ = g.get("home_score"), g.get("away_score")
            if str(gid) in gm and hs not in (None, "") and as_ not in (None, ""):
                t = _f(hs) + _f(as_)
                d = gm[str(gid)][0]
                tot[g["home"]].append((d, t)); tot[g["away"]].append((d, t)); lgt.append((d, t))
        self._pace = {t: (np.array([x[0] for x in sorted(v)], dtype=np.int64),
                          np.concatenate([[0.0], np.cumsum([x[1] for x in sorted(v)])])) for t, v in tot.items()}
        lgt.sort()
        self._pace_lg = (np.array([x[0] for x in lgt], dtype=np.int64), np.concatenate([[0.0], np.cumsum([x[1] for x in lgt])]))

    # ------------------------------------------------------------------ helpers
    def _hist(self, pid: str, date) -> tuple[_Log | None, int]:
        lg = self.logs.get(str(pid))
        if lg is None:
            return None, 0
        return lg, int(np.searchsorted(lg.d, _to_date(date).toordinal(), side="left"))

    def league_rate(self, stat: str, band: int, date) -> float | None:
        o = _to_date(date).toordinal()
        d, mins, vals = self._pr[band]
        i = int(np.searchsorted(d, o, side="left"))
        if mins[i] > 0:
            return float(vals[i, _IDX[stat]] / mins[i])
        tot_m = sum(p[1][int(np.searchsorted(p[0], o, side="left"))] for p in self._pr)
        tot_v = sum(p[2][int(np.searchsorted(p[0], o, side="left")), _IDX[stat]] for p in self._pr)
        return float(tot_v / tot_m) if tot_m > 0 else None

    def opp_allowed(self, team: str, stat: str, date) -> tuple[float | None, int]:
        """(allowed per game this season before date, games)."""
        if team not in self.allowed:
            return None, 0
        o = _to_date(date).toordinal()
        d, cum = self.allowed[team]
        lo = int(np.searchsorted(d, _season_start(SC.season_of(_to_date(date))), side="left"))
        hi = int(np.searchsorted(d, o, side="left"))
        n = hi - lo
        return (float((cum[hi, _IDX[stat]] - cum[lo, _IDX[stat]]) / n) if n > 0 else None), n

    def league_allowed(self, stat: str, date) -> float | None:
        o = _to_date(date).toordinal()
        lo = int(np.searchsorted(self._lg_d, _season_start(SC.season_of(_to_date(date))), side="left"))
        hi = int(np.searchsorted(self._lg_d, o, side="left"))
        return float((self._lg_cum[hi, _IDX[stat]] - self._lg_cum[lo, _IDX[stat]]) / (hi - lo)) if hi > lo else None

    def defense_table(self, stat: str, date) -> dict[str, tuple[float, int, int]]:
        """team -> (allowed per game, rank 1 = stingiest, games) among teams with >= 5 games."""
        key = (_to_date(date).toordinal(), stat)
        if key not in self._def_cache:
            per = {}
            for t in self.allowed:
                a, n = self.opp_allowed(t, stat, date)
                if a is not None and n >= SC.MIN_DEF_GAMES:
                    per[t] = (a, n)
            order = sorted(per, key=lambda t: per[t][0])
            self._def_cache[key] = {t: (per[t][0], i + 1, per[t][1]) for i, t in enumerate(order)}
        return self._def_cache[key]

    def team_mpg(self, team: str, date) -> list[tuple[str, float, int]]:
        """[(pid, minutes per game, games)] for the team this season before date, >= 5 games, by mpg."""
        date = _to_date(date)
        key = (team, date.toordinal())
        if key not in self._key_cache:
            season = SC.season_of(date)
            out = []
            for pid in self.team_pids.get(team, ()):
                lg, i = self._hist(pid, date)
                if not i:
                    continue
                m = (lg.season[:i] == season) & (lg.team[:i] == team)
                n = int(m.sum())
                if n >= 5:
                    out.append((pid, float(lg.minutes[:i][m].mean()), n))
            out.sort(key=lambda x: -x[1])
            self._key_cache[key] = out
        return self._key_cache[key]

    def key_teammates(self, pid: str, team: str, date, top: int = KEY_MATES) -> list[str]:
        return [p for p, _, _ in self.team_mpg(team, date) if p != str(pid)][:top]

    def _resolve_mates(self, team: str, date, names) -> list[str]:
        """Teammate ids from ids or names, among players who played for ``team`` this season."""
        season = SC.season_of(_to_date(date))
        members = {}
        for p, _, _ in self.team_mpg(team, date):
            members[p] = p
            members[_norm(self.names.get(p, p))] = p
        out = []
        for x in names or ():
            x = str(x)
            pid = members.get(x) or members.get(_norm(x))
            if pid is None and x in self.logs:     # an id with < 5 games this season
                lg, i = self._hist(x, date)
                if i and ((lg.season[:i] == season) & (lg.team[:i] == team)).any():
                    pid = x
            if pid and pid not in out:
                out.append(pid)
        return out

    def _weights(self, lg: _Log, i: int, season: int, half_life: float, prev_w: float) -> np.ndarray:
        age = np.arange(i - 1, -1, -1, dtype=float)
        back = season - lg.season[:i]
        return np.power(0.5, age / half_life) * np.power(prev_w, back.astype(float))

    # ------------------------------------------------------------------ minutes
    def expected_minutes(self, pid: str, date, teammates_out=(), minutes_override=None) -> dict | None:
        lg, i = self._hist(pid, date)
        if lg is None or i < MIN_GAMES:
            return None
        date = _to_date(date)
        season = SC.season_of(date)
        if season - int(lg.season[i - 1]) > 1:
            return None              # no game this season or last: too stale to project
        P = self.params
        team = str(lg.team[i - 1])
        flags = []
        st = lg.starter[max(0, i - 5):i]
        role = "starter" if st.mean() >= 0.5 else "bench"
        prev_part = lg.starter[max(0, i - 13):max(0, i - 3)]
        if len(prev_part) >= 5 and i >= 8:
            prev_role = "starter" if prev_part.mean() >= 0.5 else "bench"
            last3 = "starter" if lg.starter[i - 3:i].mean() >= 0.5 else "bench"
            if last3 != prev_role:
                flags.append("role_change")
        cur_n = int((lg.season[:i] == season).sum())
        w = self._weights(lg, i, season, P["min_half_life"], P["min_prev_w"])
        mins = lg.minutes[:i]
        if "role_change" in flags and P["role_minutes"]:
            same = lg.starter[:i] == (1 if role == "starter" else 0)
            if same[-3:].sum() >= 2:
                w = w * same
        m = float((w * mins).sum() / w.sum())
        basis = (f"recency-weighted (half-life {P['min_half_life']:g} games), {cur_n} games this season"
                 if cur_n >= 3 else f"previous season decayed x{P['min_prev_w']:g} ({cur_n} games this season)")
        if "role_change" in flags and P["role_minutes"]:
            basis += f"; {role} games only (role change)"
        sched = self.sched.get(team, [])
        missed = bisect.bisect_left(sched, date.toordinal()) - bisect.bisect_right(sched, int(lg.d[i - 1]))
        if cur_n and season == int(lg.season[i - 1]) and missed >= RETURN_GAP:
            flags.append("returning_from_absence")
            m *= P["return_factor"]
            basis += f"; returning after {missed} team games x{P['return_factor']:g}"
        mates = self._resolve_mates(team, date, teammates_out)
        key = set(self.key_teammates(pid, team, date))
        kmates = [x for x in mates if x in key]
        fmin, frate, splits = self._mate_factors(lg, i, team, date, kmates)
        if kmates and fmin != 1.0:
            basis += f"; teammates out x{fmin:.3f}"
        m *= fmin
        if minutes_override is not None:
            m, basis = float(minutes_override), "override"
        if cur_n < MIN_GAMES:
            flags.append("low_sample")
        return dict(minutes=min(max(m, 0.0), MAX_MINUTES), basis=basis, role=role, flags=flags, team=team,
                    mates=mates, key_mates=kmates, rate_factor=frate, mate_splits=splits, games=i, cur_n=cur_n)

    def _mate_factors(self, lg: _Log, i: int, team: str, date: dt.date, mates: list[str]):
        """(minutes factor, per-stat rate factors, details) for key teammates out."""
        K = self.params["mate_k"]
        fmin, frate, out = 1.0, np.ones(len(STATS)), []
        if not mates or K is None or math.isinf(K):
            return fmin, frate, out
        on_team = lg.team[:i] == team
        if not on_team.any():
            return fmin, frate, out
        mins, vals, seas, d = lg.minutes[:i], lg.vals[:i], lg.season[:i], lg.d[:i]
        for m in mates:
            ml, mi = self._hist(m, date)
            if ml is None or not mi:
                continue
            with_m = np.array([g in ml.gidset for g in lg.gid[:i]]) & on_team
            first, trade = {}, {}
            for k in range(mi):
                s = int(ml.season[k])
                if ml.team[k] == team and s not in first:
                    first[s] = int(ml.d[k])
                elif ml.team[k] != team and s in first and s not in trade:
                    trade[s] = int(ml.d[k])
            valid = np.array([int(s) in first and dd >= first[int(s)] and dd < trade.get(int(s), 10 ** 9)
                              for s, dd in zip(seas, d)]) & on_team
            wo = valid & ~with_m
            n_w, n_wo = int(with_m.sum()), int(wo.sum())
            if not n_w or not n_wo:
                continue
            shrink = n_wo / (n_wo + K)
            recent = np.flatnonzero(valid)[-10:]
            share = float(wo[recent].mean()) if len(recent) else 0.0
            r_min = mins[wo].mean() / mins[with_m].mean()
            adj_min = r_min / (share * r_min + (1 - share))
            fmin *= 1 + (adj_min - 1) * shrink
            r_rate = (vals[wo].sum(0) / mins[wo].sum() + 1e-9) / (vals[with_m].sum(0) / mins[with_m].sum() + 1e-9)
            adj_rate = r_rate / (share * r_rate + (1 - share))
            frate = frate * (1 + (adj_rate - 1) * shrink)
            out.append(dict(pid=m, name=self.names.get(m, m), n_with=n_w, n_without=n_wo))
        lo, hi = FACTOR_CAP
        return float(min(max(fmin, lo), hi)), np.clip(frate, lo, hi), out

    # ------------------------------------------------------------------ rate
    def rate(self, pid: str, stat: str, date, exp_minutes: float) -> float | None:
        lg, i = self._hist(pid, date)
        if lg is None or i < MIN_GAMES:
            return None
        P = self.params
        season = SC.season_of(_to_date(date))
        prior = self.league_rate(stat, _band(exp_minutes), date)
        if prior is None:
            return None
        w = self._weights(lg, i, season, P["rate_half_life"][stat], P["rate_prev_w"][stat])
        mins = lg.minutes[:i]
        K = P["rate_k"][stat]
        k = _IDX[stat]
        if P.get("make_k") is not None and stat in ("pts", "fg3m"):
            r = self._attempt_rate(lg, i, w, stat, date, K, P["make_k"])
            if r is not None:
                return r
        return float(((w * lg.vals[:i, k]).sum() + K * prior) / ((w * mins).sum() + K))

    def _attempt_rate(self, lg: _Log, i: int, w: np.ndarray, stat: str, date, K: float, make_k: float) -> float | None:
        """Attempt volume per minute x make rate (points per true-shooting attempt for pts,
        3P% for fg3m), each shrunk toward the league before ``date``."""
        att = lg.att[:i]
        ok = ~np.isnan(att[:, 0]) & ~np.isnan(att[:, 1])
        if ok.sum() < MIN_GAMES:
            return None
        j = int(np.searchsorted(self._att_d, _to_date(date).toordinal(), side="left"))
        c = self._att_cum[j]           # minutes, fga, fg3a, fta, pts, fg3m
        if c[0] <= 0:
            return None
        w, mins, vals = w[ok], lg.minutes[:i][ok], lg.vals[:i][ok]
        fta = np.nan_to_num(att[ok, 2])
        if stat == "fg3m":
            vol, lvol, made, lpct = att[ok, 1], c[2] / c[0], vals[:, 3], (c[5] / c[2] if c[2] else None)
        else:
            vol, lvol, made, lpct = att[ok, 0] + 0.44 * fta, (c[1] + 0.44 * c[3]) / c[0], vals[:, 0], (c[4] / (c[1] + 0.44 * c[3]) if c[1] else None)
        if lpct is None:
            return None
        a_rate = ((w * vol).sum() + K * lvol) / ((w * mins).sum() + K)
        pct = ((w * made).sum() + make_k * lpct) / ((w * vol).sum() + make_k)
        return float(a_rate * pct)

    def opp_factor(self, opp: str, stat: str, date) -> float:
        K = self.params["opp_k"][stat]
        if opp is None or K is None or math.isinf(K):
            return 1.0
        a, n = self.opp_allowed(opp, stat, date)
        lg = self.league_allowed(stat, date)
        if a is None or not lg:
            return 1.0
        return 1 + (a / lg - 1) * (n / (n + K))

    def pace_factor(self, team: str | None, opp: str | None, date) -> float:
        """Expected game total relative to the league's this season (1.0 when off or unknown)."""
        K = self.params.get("pace_k")
        if K is None or not team or not opp:
            return 1.0
        date = _to_date(date)
        o, lo_d = date.toordinal(), _season_start(SC.season_of(date))

        def avg(d, cum):
            lo, hi = int(np.searchsorted(d, lo_d, side="left")), int(np.searchsorted(d, o, side="left"))
            return ((cum[hi] - cum[lo]) / (hi - lo), hi - lo) if hi > lo else (None, 0)
        lg, _n = avg(*self._pace_lg)
        a, na = avg(*self._pace[team]) if team in self._pace else (None, 0)
        b, nb = avg(*self._pace[opp]) if opp in self._pace else (None, 0)
        if not lg or a is None or b is None:
            return 1.0
        n = min(na, nb)
        return 1 + (((a + b) / 2) / lg - 1) * (n / (n + K))

    # ------------------------------------------------------------------ public
    def predict(self, pid: str, stat: str, date, opp: str | None = None, home: bool | None = None,
                teammates_out=(), minutes_override=None, injury_status: str | None = None) -> dict | None:
        if stat not in _IDX:
            raise ValueError(f"unknown stat {stat}")
        date = _to_date(date)
        if injury_status and str(injury_status).strip().lower().startswith("out"):
            return None
        em = self.expected_minutes(pid, date, teammates_out, minutes_override)
        if em is None:
            return None
        rate = self.rate(pid, stat, date, em["minutes"])
        if rate is None:
            return None
        k = _IDX[stat]
        of = self.opp_factor(opp, stat, date)
        of *= self.pace_factor(em["team"], opp, date)
        mean = max(rate * em["minutes"] * float(em["rate_factor"][k]) * of, 1e-6)
        var = mean + mean * mean / self.dispersion[stat]
        flags = list(em["flags"])
        if injury_status:
            flags.append(f"injury_{_norm(injury_status)}")
        lg, i = self._hist(pid, date)
        season = SC.season_of(date)
        vals = lg.vals[:i, k]
        cur = vals[lg.season[:i] == season]
        vs = vals[lg.opp[:i] == opp] if opp else vals[:0]
        dtab = self.defense_table(stat, date)
        od = dtab.get(opp) if opp else None
        allowed_pg, _n = self.opp_allowed(opp, stat, date) if opp else (None, 0)
        explain = dict(
            season=dict(avg=round(float(cur.mean()), 2) if len(cur) else None, n=int(len(cur))),
            last5=[float(x) for x in vals[-5:][::-1]],
            last10_avg=round(float(vals[-10:].mean()), 2),
            line_hits=None, line_hits_last10=None,
            vs_opp=dict(h=None, n=int(len(vs)), avg=round(float(vs.mean()), 2) if len(vs) else None),
            exp_minutes=round(em["minutes"], 1), minutes_basis=em["basis"], role=em["role"],
            opp_def=dict(rank=od[1] if od else None, teams=len(dtab),
                         allowed_pg=round(allowed_pg, 2) if allowed_pg is not None else None),
            teammates_out=[self.names.get(m, m) for m in em["mates"]],
            injury_status=injury_status, mean=round(mean, 2), sd=round(math.sqrt(var), 2), flags=flags,
        )
        return dict(pid=str(pid), stat=stat, date=date.isoformat(), opp=opp, home=home, mean=mean, var=var,
                    sd=math.sqrt(var), minutes=em["minutes"], games=em["games"], rate=rate, opp_factor=of,
                    rate_factor=float(em["rate_factor"][k]), version=VERSION, explain=explain)

    def prob(self, pred: dict, line: float, side: str) -> tuple[float, float]:
        """(P(win), P(push)) from the negative binomial with the fitted per-stat dispersion."""
        return dist.count_probs(pred["mean"], pred["var"], line, side)

    def explain_for_line(self, pred: dict, pid: str, stat: str, line: float, side: str, date, opp: str | None) -> dict:
        """Fill the line-dependent counts with exact numerators/denominators. A game that
        landed exactly on the line is a push: it is left out of h and n and counted in
        ``pushes``."""
        date = _to_date(date)
        lg, i = self._hist(pid, date)
        ex = pred["explain"]
        if lg is None:
            return ex
        k = _IDX[stat]
        season = SC.season_of(date)
        vals = lg.vals[:i, k]

        def count(xs):
            res = [SC.outcome(float(v), line, side) for v in xs]
            hit = [r for r in res if r is not None]
            return dict(h=int(sum(hit)), n=len(hit), pushes=len(res) - len(hit))

        ex["line_hits"] = count(vals[lg.season[:i] == season])
        ex["line_hits_last10"] = count(vals[-10:])
        vs = vals[lg.opp[:i] == opp] if opp else vals[:0]
        ex["vs_opp"] = dict(count(vs), avg=round(float(vs.mean()), 2) if len(vs) else None)
        ex["line"], ex["side"] = line, side
        ex["counts_note"] = "line_hits is this season, vs_opp is all seasons; pushes are excluded from h and n"
        return ex
