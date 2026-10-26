"""Player-prop split cards (NBA-032): how often a player cleared THIS exact line, split
by context, each with its sample size, then one shrunken probability.

Why: the owner reads props as "Curry over 30.5 - how often has he done that, vs whom,
when rested, without Draymond?". A card answers with counts, never bare percentages,
and the combined number is shrunk so a 3-for-3 split cannot dominate.

Point-in-time: every function takes a ``date`` and only looks at games strictly before
it (the slate day in US/Eastern). Research/watchlist only - nothing here qualifies a bet.

Known limits: box scores carry no positions, so "opponent defence vs the stat" is the
opponent's allowed-per-game of that stat to all players (rank 1 = allows least);
"usage" is proxied by minutes (no possessions data).
"""
from __future__ import annotations

import datetime as dt
import math
from collections import defaultdict
from dataclasses import dataclass, field
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
STATS = ("pts", "reb", "ast", "fg3m")
DEFAULT_K = 40.0        # prior strength (pseudo-games); k=40 chosen on explore 2023 (exp-20261021-splitcard)
# Platt calibration fitted on explore 2023 synthetic-line events only (k=40): the raw card is
# overconfident in the tails. Synthetic lines != real prices; refit once NBA-031 lines accrue.
CALIB = dict(a=0.0235, b=0.7852, fitted_on="exp-20261021-splitcard explore (2023, before 2023-01-15)")
MIN_DEF_GAMES = 5       # an opponent needs this many games before its defence rank is used


@dataclass(slots=True)
class G:
    """One game a player actually played (minutes > 0)."""
    date: dt.date
    game_id: str
    team: str
    opp: str
    home: bool
    minutes: float
    stats: dict
    rest: int | None = None   # days off since the player's previous game (0 = back-to-back)


@dataclass
class Index:
    logs: dict = field(default_factory=dict)          # player_id -> [G] sorted by date
    names: dict = field(default_factory=dict)         # player_id -> name
    rosters: dict = field(default_factory=dict)       # (game_id, team) -> set of player_ids who played
    team_games: dict = field(default_factory=dict)    # team -> [(date, game_id)] sorted
    allowed: dict = field(default_factory=dict)       # team -> [(date, {stat: total allowed})] sorted
    _def_cache: dict = field(default_factory=dict)


def et_day(start_utc: str) -> dt.date:
    """Slate day: games are grouped by US/Eastern date, matching the pipeline."""
    t = dt.datetime.fromisoformat(start_utc.replace("Z", "+00:00"))
    return t.astimezone(ET).date()


def season_of(d: dt.date) -> int:
    """ESPN season year (2023 = 2022-23); seasons start in October."""
    return d.year + 1 if d.month >= 8 else d.year


def build_index(box_rows: list[dict], games: dict[str, dict]) -> Index:
    """box_rows: game_id, player_id, team, minutes, played, stat columns.
    games: game_id -> {start_utc, home, away}. Rows of unknown games are dropped."""
    idx = Index()
    logs = defaultdict(list)
    allowed = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    for r in box_rows:
        g = games.get(str(r["game_id"]))
        team = r.get("team")
        if not g or not team or team not in (g["home"], g["away"]):
            continue
        d = et_day(g["start_utc"])
        opp = g["away"] if team == g["home"] else g["home"]
        mins = float(r.get("minutes") or 0)
        played = int(float(r.get("played") or 0)) and mins > 0
        stats = {s: float(r.get(s) or 0) for s in STATS}
        pid = str(r["player_id"])
        idx.names[pid] = r.get("player_name") or pid
        acc = allowed[opp][(d, str(r["game_id"]))]
        for s in STATS:
            acc[s] += stats[s] if played else 0.0
        if not played:
            continue
        idx.rosters.setdefault((str(r["game_id"]), team), set()).add(pid)
        logs[pid].append(G(d, str(r["game_id"]), team, opp, team == g["home"], mins, stats))
    for pid, gs in logs.items():
        gs.sort(key=lambda x: x.date)
        prev = None
        for x in gs:
            x.rest = None if prev is None or (x.date - prev).days > 30 else (x.date - prev).days - 1
            prev = x.date
        idx.logs[pid] = gs
    tg = defaultdict(set)
    for (gid, team) in idx.rosters:
        tg[team].add((et_day(games[gid]["start_utc"]), gid))
    idx.team_games = {t: sorted(v) for t, v in tg.items()}
    idx.allowed = {t: sorted(((d, dict(v)) for (d, _), v in m.items()), key=lambda x: x[0]) for t, m in allowed.items()}
    return idx


def history(idx: Index, pid: str, date: dt.date) -> list[G]:
    """The player's games strictly before ``date`` - the only data a card may use."""
    return [g for g in idx.logs.get(str(pid), []) if g.date < date]


def defense_ranks(idx: Index, date: dt.date, stat: str) -> dict[str, tuple[float, int, int]]:
    """team -> (allowed per game this season, rank 1 = stingiest, games), before ``date``."""
    key = (date, stat)
    if key in idx._def_cache:
        return idx._def_cache[key]
    season = season_of(date)
    per = {}
    for t, rows in idx.allowed.items():
        vals = [v[stat] for d, v in rows if d < date and season_of(d) == season]
        if len(vals) >= MIN_DEF_GAMES:
            per[t] = (sum(vals) / len(vals), len(vals))
    order = sorted(per, key=lambda t: per[t][0])
    out = {t: (per[t][0], i + 1, per[t][1]) for i, t in enumerate(order)}
    idx._def_cache[key] = out
    return out


def def_tier(rank: int | None, teams: int) -> str | None:
    """Thirds of the league: tough / middle / soft defence against this stat."""
    if rank is None or teams < 3:
        return None
    third = teams / 3
    return "tough" if rank <= third else ("middle" if rank <= 2 * third else "soft")


def key_teammates(idx: Index, pid: str, team: str, date: dt.date, top: int = 3, min_games: int = 5) -> list[str]:
    """Top-``top`` teammates by average minutes (usage proxy) this season before ``date``."""
    season = season_of(date)
    mins = defaultdict(list)
    for d, gid in idx.team_games.get(team, []):
        if d >= date or season_of(d) != season:
            continue
        for mate in idx.rosters.get((gid, team), ()):
            if mate == str(pid):
                continue
            g = next((x for x in idx.logs[mate] if x.game_id == gid), None)
            if g:
                mins[mate].append(g.minutes)
    ranked = sorted((m for m in mins if len(mins[m]) >= min_games), key=lambda m: -sum(mins[m]) / len(mins[m]))
    return ranked[:top]


def mates_in_last_game(idx: Index, team: str, mates: list[str], date: dt.date) -> dict[str, bool]:
    """Point-in-time proxy for 'is the teammate playing': did he play the team's previous game.
    Callers with a pregame injury report should pass that status instead."""
    prev = [gid for d, gid in idx.team_games.get(team, []) if d < date]
    roster = idx.rosters.get((prev[-1], team), set()) if prev else set()
    return {m: m in roster for m in mates}


def outcome(value: float, line: float, side: str) -> int | None:
    """1 hit, 0 miss, None push (pushes are left out of every count)."""
    if value == line:
        return None
    return int(value > line) if side == "over" else int(value < line)


def _count(gs: list[G], stat: str, line: float, side: str) -> tuple[int, int]:
    res = [o for g in gs if (o := outcome(g.stats[stat], line, side)) is not None]
    return sum(res), len(res)


def rest_bucket(rest: int | None) -> str | None:
    return None if rest is None else ("b2b" if rest == 0 else ("1 day" if rest == 1 else "2+ days"))


def split_counts(idx: Index, pid: str, stat: str, line: float, side: str, date: dt.date, opp: str, home: bool,
                 mates_status: dict[str, bool] | None = None, team: str | None = None) -> dict[str, tuple[int, int]]:
    """Every split as (hits, n) over the exact line, using only games before ``date``.
    Splits with no games are omitted; the caller sees n for each one."""
    hist = history(idx, pid, date)
    if not hist:
        return {}
    season = season_of(date)
    team = team or hist[-1].team
    out: dict[str, tuple[int, int]] = {}
    this = [g for g in hist if season_of(g.date) == season]
    groups = {
        "career": hist, "season": this, "last5": hist[-5:], "last10": hist[-10:],
        f"vs {opp}": [g for g in hist if g.opp == opp],
        "home" if home else "away": [g for g in hist if g.home == home],
        f"month {date.month} past seasons": [g for g in hist if g.date.month == date.month and season_of(g.date) < season],
    }
    last = hist[-1].date
    gap = (date - last).days
    rb = rest_bucket(gap - 1 if gap <= 30 else None)
    if rb:
        groups[f"rest {rb}"] = [g for g in hist if rest_bucket(g.rest) == rb]
    ranks = defense_ranks(idx, date, stat)
    tier = def_tier(ranks.get(opp, (0, None, 0))[1], len(ranks))
    if tier:
        tiers = []
        for g in hist:
            r = defense_ranks(idx, g.date, stat)
            if def_tier(r.get(g.opp, (0, None, 0))[1], len(r)) == tier:
                tiers.append(g)
        groups[f"opp defence {tier}"] = tiers
    if mates_status is None:
        mates = key_teammates(idx, pid, team, date)
        mates_status = mates_in_last_game(idx, team, mates, date)
    for m, playing in mates_status.items():
        with_m = [g for g in hist if g.team == team and m in idx.rosters.get((g.game_id, team), ())]
        without = [g for g in hist if g.team == team and m not in idx.rosters.get((g.game_id, team), ())]
        nm = idx.names.get(m, m)
        groups[f"{'with' if playing else 'without'} {nm}"] = with_m if playing else without
    for name, gs in groups.items():
        h, n = _count(gs, stat, line, side)
        if n:
            out[name] = (h, n)
    return out


def shrink(h: int, n: int, prior: float, k: float) -> float:
    """Beta-binomial posterior mean with a Beta(k*prior, k*(1-prior)) prior."""
    return (h + k * prior) / (n + k)


def _logit(p: float) -> float:
    p = min(max(p, 1e-4), 1 - 1e-4)
    return math.log(p / (1 - p))


def baseline(counts: dict[str, tuple[int, int]], k: float = DEFAULT_K) -> float:
    """Season rate shrunk toward the career rate, which is itself shrunk toward 0.5."""
    ch, cn = counts.get("career", (0, 0))
    pc = shrink(ch, cn, 0.5, 2.0)
    sh, sn = counts.get("season", (0, 0))
    return shrink(sh, sn, pc, k)


def combine(counts: dict[str, tuple[int, int]], k: float = DEFAULT_K) -> float | None:
    """One probability: baseline log-odds plus the n-weighted average of each split's
    shrunken log-odds deviation. Averaging (not summing) stops correlated splits
    (last5 is inside last10 is inside season) from being counted several times."""
    if not counts.get("career"):
        return None
    p0 = baseline(counts, k)
    num = den = 0.0
    for name, (h, n) in counts.items():
        if name in ("career", "season"):
            continue
        w = n / (n + k)
        num += w * (_logit(shrink(h, n, p0, k)) - _logit(p0))
        den += w
    z = _logit(p0) + (num / max(den, 1.0))
    return 1 / (1 + math.exp(-z))


def calibrate(p: float, a: float = CALIB["a"], b: float = CALIB["b"]) -> float:
    """Platt map sigmoid(a + b*logit(p)); b < 1 pulls overconfident tails toward the middle."""
    return 1 / (1 + math.exp(-(a + b * _logit(p))))


def calibrate_tailcap(p: float, lo: float = 0.2, hi: float = 0.8, **kw) -> float:
    """Platt, but in the tails (raw p < lo or > hi) never let calibration push p further
    from 0.5 than the raw estimate: guards against inflating longshots (NBA-034)."""
    c = calibrate(p, **kw)
    if p < lo or p > hi:
        if abs(c - 0.5) > abs(p - 0.5):
            return p
    return c


def fit_isotonic(ps: list[float], ys: list[int], bins: int = 20) -> list[tuple[float, float]]:
    """Pool-adjacent-violators on quantile bins: returns (upper_edge, rate) steps that are
    non-decreasing. Binning first keeps steps from chasing single events."""
    pairs = sorted(zip(ps, ys))
    n = len(pairs)
    blocks = []  # [sum_y, count, upper_edge]
    for b in range(bins):
        chunk = pairs[b * n // bins:(b + 1) * n // bins]
        if chunk:
            blocks.append([sum(y for _, y in chunk), len(chunk), chunk[-1][0]])
    out: list[list[float]] = []
    for blk in blocks:
        out.append(blk)
        while len(out) > 1 and out[-2][0] / out[-2][1] > out[-1][0] / out[-1][1]:
            y2, c2, e2 = out.pop()
            out[-1][0] += y2; out[-1][1] += c2; out[-1][2] = e2
    return [(e, y / c) for y, c, e in out]


def apply_isotonic(p: float, steps: list[tuple[float, float]]) -> float:
    for edge, rate in steps:
        if p <= edge:
            return min(max(rate, 1e-4), 1 - 1e-4)
    return min(max(steps[-1][1], 1e-4), 1 - 1e-4)


def card(idx: Index, pid: str, stat: str, line: float, side: str, date: dt.date, opp: str, home: bool,
         price_dec: float | None = None, fair_prob: float | None = None, k: float = DEFAULT_K,
         mates_status: dict[str, bool] | None = None, team: str | None = None, book: str | None = None,
         price_observed_at: str | None = None) -> dict | None:
    """The split card for one offered prop side: splits with n, combined probability,
    implied probability and EV (watchlist information only, never a qualification)."""
    counts = split_counts(idx, pid, stat, line, side, date, opp, home, mates_status, team)
    prob = combine(counts, k)
    if prob is None:
        return None
    implied = 1 / price_dec if price_dec else None
    cal = calibrate(prob)
    return dict(status="research", book=book if price_dec else None, price_observed_at=price_observed_at if price_dec else None,
                player_id=str(pid), player=idx.names.get(str(pid), str(pid)), stat=stat, line=line, side=side,
                date=date.isoformat(), opp=opp, home=home,
                splits=[dict(split=s, hits=h, n=n, rate=round(h / n, 3)) for s, (h, n) in counts.items()],
                prob_raw=round(prob, 4), prob=round(cal, 4), implied=round(implied, 4) if implied else None,
                fair=round(fair_prob, 4) if fair_prob is not None else None,
                ev=round(cal * price_dec - 1, 4) if price_dec else None, k=k)


def card_text(c: dict) -> str:
    """One line per card for the run report: every split shows hits/n."""
    parts = ", ".join(f"{s['split']} {s['hits']}/{s['n']}" for s in c["splits"])
    ev = f" EV {c['ev']:+.3f} @ {c.get('book') or '?'}" if c.get("ev") is not None else ""
    imp = f" vs {c.get('book') or '?'} implied {c['implied']:.3f}" if c.get("implied") else ""
    return f"[{c['status']}] {c['player']} {c['side']} {c['line']} {c['stat']} ({'vs' if c['home'] else '@'} {c['opp']}): p={c['prob']:.3f} (raw {c['prob_raw']:.3f}){imp}{ev} | {parts}"
