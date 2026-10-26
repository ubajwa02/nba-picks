"""Walk-forward player-prop backtest (props-v0, split card, naive, props-v1).

    python -m nbapicks.propbacktest --start 2026-01-01 --end 2026-01-31 \
        --models props-v0,splitcard,props-v1 --stats pts,fg3m,reb,ast
    python -m nbapicks.propbacktest --fit          # fit props-v1 constants on explore

Every prediction for slate day D uses only games whose US/Eastern day is before D:
props-v0 is rebuilt each day from the earlier rows; props-v1 and the split card bisect
their per-player logs at D. Splits come from config/gates.yaml ``props``; a period that
touches the holdout is refused unless ``--holdout`` is passed.

Lines: real lines from data/history/props_<season>.csv.gz when that file exists (latest
pregame observation per player/stat; unlabelled sides are priced at the worse of the pair,
"conservative pair"); otherwise synthetic lines floor(median of the player's previous 10
games) + 0.5 with probability quality only (ROI fields null, price_basis "none").
"""
from __future__ import annotations

import argparse
import bisect
import csv
import datetime as dt
import glob
import gzip
import json
import math
import os
import statistics
import sys
import zlib
from collections import defaultdict

import numpy as np
import yaml

from . import cache, metrics
from . import odds as O
from . import propsides as PS
from . import splitcard as SC
from .models import dist
from .models import props_v1 as V1
from .props import PropModel

MODELS = ("props-v0", "splitcard", "props-v1", "naive")
STATS = ("pts", "reb", "ast", "fg3m")
MIN_PRIOR = 10          # prior games needed for the synthetic line (median of the last 10)
MIN_MPG = 10.0          # subsample: >= 10 minutes per game over the last 10 (point in time)
EV_MIN = 0.05
UNIT = 100.0
CODE_FILES = ["nbapicks/propbacktest.py", "nbapicks/models/props_v1.py", "nbapicks/props.py",
              "nbapicks/splitcard.py", "nbapicks/models/dist.py", "config/gates.yaml"]
BASELINE = {"props-v1": "props-v0", "splitcard": "props-v0", "naive": "props-v0", "props-v0": "naive"}
NAIVE = "naive season hit rate (season shrunk to career shrunk to 0.5, k=40)"


class HoldoutRefused(RuntimeError):
    pass


# ---------------------------------------------------------------- splits
def load_splits(path: str = "config/gates.yaml") -> dict[str, tuple[dt.date, dt.date | None]]:
    g = yaml.safe_load(open(path))["props"]["splits"]
    out = {}
    for k, v in g.items():
        out[k] = (dt.date.fromisoformat(str(v["start"])) if v.get("start") else dt.date.min,
                  dt.date.fromisoformat(str(v["end"])) if v.get("end") else dt.date.max)
    return out


def split_of(start: dt.date, end: dt.date, holdout: bool = False, splits: dict | None = None) -> str:
    """Name of the split that contains [start, end]. Refuses any period that touches the
    holdout unless ``holdout`` is True, and any period that straddles two splits."""
    sp = splits or load_splits()
    hs, he = sp["holdout"]
    if start <= he and end >= hs and not holdout:
        raise HoldoutRefused(f"{start}..{end} overlaps the props holdout {hs}..{he}; pass --holdout to score it (once per frozen candidate)")
    if end < start:
        raise ValueError("end before start")
    for name, (a, b) in sp.items():
        if a <= start and end <= b:
            return name
    if start > he:
        return "forward"
    raise ValueError(f"{start}..{end} straddles two splits; run each split separately")


# ---------------------------------------------------------------- data
def _read(path: str) -> list[dict]:
    with gzip.open(path, "rt") as fh:
        return list(csv.DictReader(fh))


def _box_files(hist_dir: str) -> list[str]:
    return sorted(glob.glob(os.path.join(hist_dir, "box_*.csv.gz")))


def _sources(hist_dir: str) -> list[str]:
    fs = _box_files(hist_dir)
    fs += [f.replace("box_", "games_") for f in fs]
    fs += sorted(glob.glob(os.path.join(hist_dir, "props_*.csv.gz")))
    return fs + CODE_FILES


def load_history(hist_dir: str = "data/history", use_cache: bool = True, refresh: bool = False) -> dict:
    """Box rows of every season with a box file, the final games of those seasons, and real
    prop lines when props_<season>.csv.gz exists."""
    def compute():
        rows, games, lines = [], {}, {}
        for bf in _box_files(hist_dir):
            season = int(os.path.basename(bf)[4:8])
            for g in _read(bf.replace("box_", "games_")):
                if g.get("status") == "final" and g.get("start_utc"):
                    games[g["game_id"]] = dict(start_utc=g["start_utc"], home=g["home"], away=g["away"],
                                               season_type=g.get("season_type"), season=season,
                                               home_score=g.get("home_score"), away_score=g.get("away_score"))
            for r in _read(bf):
                if r["game_id"] in games:
                    r["date"] = games[r["game_id"]]["start_utc"]
                    rows.append(r)
            pf = os.path.join(hist_dir, f"props_{season}.csv.gz")
            if os.path.exists(pf):
                lines[season] = real_lines(_read(pf), games)
        rows.sort(key=lambda r: (SC.et_day(r["date"]), r["game_id"]))
        return dict(rows=rows, games=games, lines=lines)
    if not use_cache:
        return compute()
    return cache.cached("propbt-history", dict(hist_dir=hist_dir), _sources(hist_dir), compute, refresh=refresh)


def real_lines(rows: list[dict], games: dict) -> dict:
    """(game_id, player_id, stat) -> the latest pregame line with its two prices. With
    several lines at that time the one whose prices are closest to even is the main line."""
    best: dict = {}
    for r in rows:
        g = games.get(str(r.get("game_id")))
        if not g or not r.get("line"):
            continue
        # observed_at is when the backfill fetched it (after the game); the time that matters is
        # when the book last changed the price (source_updated_at). A 'current' quote last updated
        # at/after tip may be an in-game line and is dropped. An 'open' quote is the opening line,
        # posted before the game by definition; it ranks below any pregame current quote.
        upd = r.get("source_updated_at") or ""
        tip = _iso(g["start_utc"])
        if r.get("kind") == "open":
            when = "0000-open"
        elif upd and _iso(upd) < tip:
            when = _iso(upd)
        else:
            continue     # not provably pregame
        try:
            p0, p1, line = float(r["price0_dec"]), float(r["price1_dec"]), float(r["line"])
        except (TypeError, ValueError):
            continue
        if not PS.plausible_pair(p0, p1):
            continue     # not a two-way market at this line (alt-ladder rungs): see propsides
        lab = (r.get("side_label") or "unknown").lower()
        k = (str(r["game_id"]), str(r["player_id"]), r["stat"])
        rec = dict(line=line, p0=p0, p1=p1, side_label=lab if lab in ("over", "under") else "unknown",
                   observed_at=when, kind=r.get("kind"), book=r.get("book"))
        cur = best.get(k)
        # main line: among quotes of the same time, the pair whose de-vigged price is nearest 50/50
        if cur is None or rec["observed_at"] > cur["observed_at"] or (
                rec["observed_at"] == cur["observed_at"] and _balance(p0, p1) < _balance(cur["p0"], cur["p1"])):
            best[k] = rec
    return best


def _balance(p0: float, p1: float) -> float:
    """Distance of the de-vigged first-side probability from 0.5."""
    return abs((1 / p0) / (1 / p0 + 1 / p1) - 0.5)


def _iso(t: str) -> str:
    """'2025-10-23T04:51Z' -> '2025-10-23T04:51:00+00:00' so it compares with start_utc strings."""
    t = t.replace("Z", "+00:00")
    return dt.datetime.fromisoformat(t).astimezone(dt.timezone.utc).isoformat()


def prices(rec: dict) -> tuple[float, float, str]:
    """(over price, under price, price basis). Unlabelled sides: both sides get the worse
    price of the pair, so EV and ROI are lower bounds."""
    if rec["side_label"] == "over":
        return rec["p0"], rec["p1"], "timestamped pregame"
    if rec["side_label"] == "under":
        return rec["p1"], rec["p0"], "timestamped pregame"
    w = min(rec["p0"], rec["p1"])
    return w, w, "conservative pair"


# ---------------------------------------------------------------- events
def build_events(m: V1.PropModelV1, hist: dict, start: dt.date, end: dt.date, stats=STATS,
                 season_types=("regular", "playin", "post"), sample: int = 1) -> tuple[list[dict], dict]:
    """One event per played player-game in [start, end] with >= MIN_PRIOR earlier games and
    >= MIN_MPG over the last 10. ``sample`` > 1 keeps a deterministic 1-in-n hash subsample."""
    games = hist["games"]
    cov = defaultdict(int)
    out = []
    by_game = defaultdict(list)
    for r in hist["rows"]:
        g = games[r["game_id"]]
        if g.get("season_type") not in season_types:
            continue
        d = SC.et_day(g["start_utc"])
        if start <= d <= end:
            by_game[r["game_id"]].append(r)
    for gid, rs in sorted(by_game.items(), key=lambda kv: games[kv[0]]["start_utc"]):
        g = games[gid]
        d = SC.et_day(g["start_utc"])
        cov["games"] += 1
        for r in rs:
            pid = str(r["player_id"])
            lg = m.logs.get(pid)
            if lg is None:
                continue          # never played
            i = int(np.searchsorted(lg.d, d.toordinal(), side="left"))
            if i >= len(lg.d) or lg.d[i] != d.toordinal() or lg.gid[i] != gid:
                continue          # DNP in this game
            cov["player_games"] += 1
            if i < MIN_PRIOR:
                cov["dropped_lt10_prior_games"] += 1
                continue
            if lg.minutes[i - 10:i].mean() < MIN_MPG:
                cov["dropped_lt10_mpg"] += 1
                continue
            if sample > 1 and zlib.crc32(f"{pid}:{gid}".encode()) % sample:
                continue
            team = str(lg.team[i])
            opp = g["away"] if team == g["home"] else g["home"]
            key = V1.PropModelV1.key_teammates(m, pid, team, d)
            roster = m.roster.get((gid, team), set())
            ev = dict(gid=gid, pid=pid, team=team, opp=opp, home=team == g["home"], date=d,
                      season=SC.season_of(d), minutes=float(lg.minutes[i]), key_mates=key,
                      mates_out=[k for k in key if k not in roster], y={}, line={}, synthetic={})
            for s in stats:
                k = V1._IDX[s]
                ev["y"][s] = float(lg.vals[i, k])
                ev["synthetic"][s] = math.floor(statistics.median(lg.vals[i - 10:i, k])) + 0.5
            out.append(ev)
    cov["events"] = len(out)
    cov["players"] = len({e["pid"] for e in out})
    return out, dict(cov)


# ---------------------------------------------------------------- scoring
def _cond(pw: float, pp: float) -> float:
    """P(over | no push)."""
    return pw / (1 - pp) if pp < 1 else 0.5


def score(hist: dict, events: list[dict], models, stats, v1: V1.PropModelV1) -> list[dict]:
    """Per (event, stat): line, outcome and each model's P(over), P(push)."""
    rows_by_day = hist["rows"]
    days = [SC.et_day(r["date"]).toordinal() for r in rows_by_day]
    idx = SC.build_index(rows_by_day, hist["games"]) if ("splitcard" in models or "naive" in models) else None
    v0_day, v0 = None, None
    out = []
    for ev in events:
        lines_season = hist["lines"].get(ev["season"])
        if "props-v0" in models and ev["date"] != v0_day:
            v0_day = ev["date"]
            v0 = PropModel(rows_by_day[:bisect.bisect_left(days, v0_day.toordinal())])
        mates_status = {mm: mm not in ev["mates_out"] for mm in ev["key_mates"]}
        for s in stats:
            if lines_season is not None:
                rec = lines_season.get((ev["gid"], ev["pid"], s))
                if rec is None:
                    continue
                line = rec["line"]
                po, pu, basis = prices(rec)
            else:
                rec, line, po, pu, basis = None, ev["synthetic"][s], None, None, "none"
            y = ev["y"][s]
            row = dict(gid=ev["gid"], pid=ev["pid"], date=ev["date"], stat=s, line=line, value=y,
                       result=None if y == line else int(y > line), price_over=po, price_under=pu,
                       price_basis=basis, side_label=rec["side_label"] if rec else None, probs={})
            if "props-v1" in models:
                pr = v1.predict(ev["pid"], s, ev["date"], ev["opp"], ev["home"], teammates_out=ev["mates_out"])
                if pr is not None:
                    row["probs"]["props-v1"] = v1.prob(pr, line, "over")
            if "props-v0" in models:
                pr = v0.predict(ev["pid"], s)
                if pr is not None:
                    row["probs"]["props-v0"] = v0.prob(pr, line, "over")
            if idx is not None:
                c = SC.split_counts(idx, ev["pid"], s, line, "over", ev["date"], ev["opp"], ev["home"], mates_status, ev["team"])
                if c.get("career"):
                    if "splitcard" in models:
                        row["probs"]["splitcard"] = (SC.calibrate(SC.combine(c)), 0.0)
                    if "naive" in models:
                        row["probs"]["naive"] = (SC.baseline(c), 0.0)
            out.append(row)
    return out


def _bets(rows: list[dict], model: str) -> list[dict]:
    """Flat 1u bets where model EV >= 5% at the price used (better EV side if both)."""
    bets = []
    for r in rows:
        if r["price_over"] is None or model not in r["probs"]:
            continue
        pw, pp = r["probs"][model]
        pu = max(0.0, 1 - pw - pp)
        evs = [("over", pw * r["price_over"] + pp - 1, pw, r["price_over"]),
               ("under", pu * r["price_under"] + pp - 1, pu, r["price_under"])]
        side, ev, p, price = max(evs, key=lambda x: x[1])
        if ev < EV_MIN:
            continue
        if r["result"] is None:
            net, res = 0.0, "push"
        else:
            won = r["result"] == (1 if side == "over" else 0)
            net, res = (price - 1 if won else -1.0), ("win" if won else "loss")
        bets.append(dict(side=side, p=p, price=price, net=net, result=res))
    return bets


def _calib10(ps: list[float], ys: list[int]) -> list[dict]:
    rows = {round(c["lo"], 1): c for c in metrics.calibration(ps, ys, 10)} if ps else {}
    out = []
    for b in range(10):
        c = rows.get(round(b / 10, 1))
        out.append(dict(lo=round(b / 10, 1), hi=round((b + 1) / 10, 1), n=c["n"] if c else 0,
                        predicted=round(c["predicted"], 4) if c else None, observed=round(c["observed"], 4) if c else None))
    return out


def _ll(p: float, y: int) -> float:
    p = min(max(p, 1e-12), 1 - 1e-12)
    return -math.log(p if y else 1 - p)


def paired(rows: list[dict], a: str, b: str) -> dict:
    """Log-loss gain of ``a`` over ``b`` on the same events (positive = a better): naive
    paired t and a t clustered by slate day (players on one night share game script)."""
    d = [_ll(_cond(*r["probs"][b]), r["result"]) - _ll(_cond(*r["probs"][a]), r["result"]) for r in rows]
    n = len(d)
    if n < 3:
        return dict(n=n, gain=None, t=None, t_day_cluster=None)
    mean = statistics.mean(d)
    sd = statistics.stdev(d)
    by = defaultdict(float)
    for r, x in zip(rows, d):
        by[r["date"]] += x - mean
    var_cl = sum(v * v for v in by.values()) / n ** 2
    return dict(n=n, gain=round(mean, 6), t=round(mean / (sd / math.sqrt(n)), 2) if sd else None,
                t_day_cluster=round(mean / math.sqrt(var_cl), 2) if var_cl else None, days=len(by))


def make_runs(scored: list[dict], models, stats, start, end, split, cov: dict) -> list[dict]:
    runs = []
    for s in stats:
        rs = [r for r in scored if r["stat"] == s]
        common = [r for r in rs if r["result"] is not None and all(mm in r["probs"] for mm in models)]
        pushes = sum(1 for r in rs if r["result"] is None)
        basis_set = {r["price_basis"] for r in rs}
        basis = "conservative pair" if "conservative pair" in basis_set else (basis_set.pop() if len(basis_set) == 1 else "none")
        real = basis != "none"
        ys = [r["result"] for r in common]
        mk = None
        if real:
            fair = []
            for r in common:
                if r["side_label"] in ("over", "under"):
                    fair.append(O.devig_multiplicative([r["price_over"], r["price_under"]])[0])
                else:
                    fair = None
                    break
            mk = fair
        for mname in models:
            ps = [_cond(*r["probs"][mname]) for r in common]
            base = BASELINE[mname]
            have_base = base in models
            cv = dict(cov, stat_events=len(rs), pushes_excluded=pushes, scored_common=len(common),
                      abstained={mm: sum(1 for r in rs if mm not in r["probs"]) for mm in models},
                      subsample=f"players with >= {MIN_PRIOR} prior games and >= {MIN_MPG:g} mpg over their last 10 (point in time); every such player-game, DNPs excluded",
                      lines="real pregame lines" if real else "synthetic floor(median of previous 10 games)+0.5; P(over) scored")
            if have_base and common:
                cv[f"paired_vs_{base}"] = paired(common, mname, base)
            bets = _bets(common, mname) if real else []
            settled = [b for b in bets if b["result"] != "push"]
            wins = sum(1 for b in bets if b["result"] == "win")
            nets = [b["net"] for b in bets]
            rsum = metrics.roi_summary(nets) if bets else None
            notes = [
                "Walk-forward: each slate day uses only games before it (US/Eastern day).",
                "teammates_out = key teammates (top 3 by minutes this season) absent from this game's box: a proxy for the pregame injury report that includes late scratches.",
                "Only player-games the player actually played are scored (a DNP would void a real bet).",
                f"All models scored on the same {len(common)} events (pushes and any model abstention excluded).",
            ]
            if not real:
                notes.append("No historical prices for these lines: ROI fields are null (never filled from assumed odds); probability quality only.")
            if mname == "splitcard":
                notes.append("splitcard = nbapicks.splitcard.combine (k=40) with its explore-fitted Platt calibration.")
            if mname == "naive":
                notes.append(f"naive = {NAIVE}.")
            pv = cv.get(f"paired_vs_{base}")
            if pv and pv.get("gain") is not None:
                notes.append(f"log-loss gain vs {base} {pv['gain']:+.5f} on n={pv['n']}, paired t={pv['t']} (day-clustered t={pv['t_day_cluster']}).")
            per = f"{start.isoformat()}..{end.isoformat()}"
            runs.append({
                "name": f"{mname} {s} over/under, {per} ({split})",
                "kind": "props", "market": f"prop:{s}", "model_version": mname,
                "baseline": base if have_base else "none",
                "split": split, "period": {"start": start.isoformat(), "end": end.isoformat()},
                "staking": "flat 1u per bet (1u = $100)",
                "selection_rule": (f"EV >= {EV_MIN:.0%} at the price used (worse price of the pair when sides are unlabelled)"
                                   if real else "none: synthetic lines carry no price, probability quality only"),
                "price_basis": basis, "eligible": len(common),
                "bets": len(bets), "wins": wins, "losses": len(settled) - wins,
                "pushes": len(bets) - len(settled), "voids": 0,
                "hit_rate": round(wins / len(settled), 4) if settled else None,
                "avg_prob": round(statistics.mean(b["p"] for b in bets), 4) if bets else None,
                "avg_price_dec": round(statistics.mean(b["price"] for b in bets), 4) if bets else None,
                "avg_implied": round(statistics.mean(1 / b["price"] for b in bets), 4) if bets else None,
                "units_staked": float(len(bets)), "net_units": round(sum(nets), 4),
                "net_dollars": round(sum(nets) * UNIT, 2),
                "roi": round(rsum["roi"], 4) if rsum and rsum["roi"] is not None else None,
                "roi_ci": [round(x, 4) for x in rsum["roi_ci"]] if rsum and rsum["roi_ci"] else None,
                "logloss_model": round(metrics.log_loss(ps, ys), 5) if common else None,
                "logloss_baseline": round(metrics.log_loss([_cond(*r["probs"][base]) for r in common], ys), 5) if common and have_base else None,
                "logloss_market": round(metrics.log_loss(mk, ys), 5) if mk else None,
                "brier_model": round(metrics.brier(ps, ys), 5) if common else None,
                "brier_market": round(metrics.brier(mk, ys), 5) if mk else None,
                "calibration": _calib10(ps, ys),
                "coverage": cv, "notes": notes,
            })
    return runs


def _commit() -> str:
    try:
        from .research import commit
        return commit()
    except Exception:
        return "unknown"


def run_backtest(start, end, models=("props-v0", "splitcard", "props-v1", "naive"), stats=STATS,
                 hist_dir: str = "data/history", use_cache: bool = True, holdout: bool = False,
                 refresh: bool = False, splits: dict | None = None) -> dict:
    """Walk-forward backtest of the given models on [start, end]; returns the report dict
    (docs/CONTRACTS.md §2). Raises HoldoutRefused for a holdout period without ``holdout``."""
    start, end = V1._to_date(start), V1._to_date(end)
    split = split_of(start, end, holdout, splits)
    models = [m for m in MODELS if m in models]
    for m in models:
        if BASELINE[m] not in models:
            models.append(BASELINE[m])
    models = [m for m in MODELS if m in models]
    stats = [s for s in STATS if s in stats]

    def compute():
        hist = load_history(hist_dir, use_cache, refresh)
        v1 = V1.PropModelV1(hist["rows"], hist["games"])
        events, cov = build_events(v1, hist, start, end, stats)
        scored = score(hist, events, models, stats, v1)
        return dict(scored=scored, cov=cov)
    params = dict(start=start, end=end, models=models, stats=stats, min_prior=MIN_PRIOR, min_mpg=MIN_MPG,
                  hist_dir=hist_dir, params=V1.PARAMS, disp=V1.DISPERSION)
    res = (cache.cached("propbt-scored", params, _sources(hist_dir), compute, refresh=refresh)
           if use_cache else compute())
    runs = make_runs(res["scored"], models, stats, start, end, split, res["cov"])
    return {"generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "commit": _commit(), "runs": runs}


# ---------------------------------------------------------------- fitting (explore only)
FIT_START = dict(min_half_life=7.0, min_prev_w=0.25, role_minutes=False, return_factor=1.0,
                 rate_half_life={s: 20.0 for s in STATS}, rate_prev_w={s: 0.5 for s in STATS},
                 rate_k={s: 100.0 for s in STATS}, opp_k={s: math.inf for s in STATS}, mate_k=math.inf, make_k=None)
GRID = dict(min_half_life=[1, 1.5, 2, 3, 4, 5, 7, 10, 14, 20, 30], min_prev_w=[0.02, 0.05, 0.1, 0.25, 0.5, 1.0],
            role_minutes=[False, True],
            rate_half_life=[5, 10, 15, 20, 30, 40, 60, 80, 160, 320], rate_prev_w=[0.1, 0.25, 0.5, 0.75, 1.0],
            rate_k=[5, 10, 25, 50, 100, 200, 400, 800, 1600], opp_k=[0, 5, 10, 20, 40, 80, 160, math.inf],
            mate_k=[1, 2, 5, 10, 20, 40, 80, math.inf])


def _nb_ll(y: np.ndarray, mu: np.ndarray, r: float) -> float:
    lg = np.frompyfunc(math.lgamma, 1, 1)
    p = r / (r + mu)
    return float(np.mean((lg(y + r) - math.lgamma(r) - lg(y + 1)).astype(float) + r * np.log(p) + y * np.log1p(-p)))


def fit(hist_dir: str = "data/history", use_cache: bool = True, refresh: bool = False, sample: int = 3,
        log=print) -> dict:
    """Choose every props-v1 weight on the explore split (events before the explore end,
    regular season, 1-in-``sample`` hash subsample) by coordinate search on mean squared
    error; then the NB dispersion per stat by maximum likelihood."""
    sp = load_splits()
    ex_end = sp["explore"][1]
    hist = load_history(hist_dir, use_cache, refresh)
    rows = [r for r in hist["rows"] if SC.et_day(r["date"]) <= ex_end]     # explore data only
    m = V1.PropModelV1(rows, hist["games"])
    m.params = _copy(FIT_START)
    events, cov = build_events(m, dict(hist, rows=rows), dt.date(2000, 1, 1), ex_end, STATS, ("regular",), sample)
    n0 = len(events)
    events = [e for e in events if m.expected_minutes(e["pid"], e["date"]) is not None]
    cov["dropped_stale_no_game_this_or_last_season"] = n0 - len(events)
    cov["events"] = len(events)
    log(f"explore events {len(events)} {cov}")
    y_min = np.array([e["minutes"] for e in events])
    Y = {s: np.array([e["y"][s] for e in events]) for s in STATS}
    trace = []

    def em_all():
        return [m.expected_minutes(e["pid"], e["date"]) for e in events]

    def mse_min():
        em = em_all()
        return float(np.mean((np.array([x["minutes"] for x in em]) - y_min) ** 2))

    def coord(keys, objective, stat=None, passes=2):
        best = objective()
        for _ in range(passes):
            for k in keys:
                cur = m.params[k][stat] if stat else m.params[k]
                for v in GRID[k]:
                    if v == cur:
                        continue
                    _set(m.params, k, v, stat)
                    sc = objective()
                    trace.append(dict(param=k, stat=stat, value=v, score=sc))
                    if sc < best - 1e-12:
                        best, cur = sc, v
                    else:
                        _set(m.params, k, cur, stat)
                log(f"  {k}{'/' + stat if stat else ''} -> {cur} ({best:.5f})")
        return best

    out = dict(explore_end=ex_end.isoformat(), sample=f"1-in-{sample} hash of (player, game)", coverage=cov)
    out["minutes_mse"] = coord(["min_half_life", "min_prev_w", "role_minutes"], mse_min)
    em = em_all()
    ret = [(x["minutes"], a) for x, a in zip(em, y_min) if "returning_from_absence" in x["flags"]]
    m.params["return_factor"] = round(sum(a for _, a in ret) / sum(p for p, _ in ret), 3) if ret else 1.0
    out["return_events"] = len(ret)
    em = em_all()
    em_m = np.array([x["minutes"] for x in em])
    out["minutes_mse_final"] = float(np.mean((em_m - y_min) ** 2))
    out["rate_mse"], out["opp_mse"] = {}, {}
    for s in STATS:
        def obj_rate(s=s):
            r = np.array([m.rate(e["pid"], s, e["date"], x["minutes"]) for e, x in zip(events, em)])
            return float(np.mean((r * y_min - Y[s]) ** 2))
        out["rate_mse"][s] = coord(["rate_half_life", "rate_prev_w", "rate_k"], obj_rate, s)
        rate = np.array([m.rate(e["pid"], s, e["date"], x["minutes"]) for e, x in zip(events, em)])
        ratio, n = [], []
        for e in events:
            a, k = m.opp_allowed(e["opp"], s, e["date"])
            lgv = m.league_allowed(s, e["date"])
            ok = a is not None and lgv
            ratio.append(a / lgv if ok else 1.0)
            n.append(k if ok else 0)
        ratio, n = np.array(ratio), np.array(n, float)
        scores = {}
        for K in GRID["opp_k"]:
            f = np.ones_like(ratio) if math.isinf(K) else 1 + (ratio - 1) * (n / np.maximum(n + K, 1e-9))
            scores[str(K)] = float(np.mean((rate * y_min * f - Y[s]) ** 2))
        bestK = min(GRID["opp_k"], key=lambda K: scores[str(K)])
        m.params["opp_k"][s] = bestK
        out["opp_mse"][s] = scores
        log(f"  opp_k/{s} -> {bestK}")
    # teammates out: events with a key teammate absent
    mev = [i for i, e in enumerate(events) if e["mates_out"]]
    out["mate_events"] = len(mev)
    var = {s: float(np.var(Y[s][mev])) for s in STATS}
    var_m = float(np.var(y_min[mev]))

    def obj_mate():
        tot = 0.0
        ms = []
        for i in mev:
            e = events[i]
            preds = [m.predict(e["pid"], s, e["date"], e["opp"], e["home"], teammates_out=e["mates_out"]) for s in STATS]
            ms.append([p["mean"] for p in preds] + [preds[0]["minutes"]])
        ms = np.array(ms)
        for j, s in enumerate(STATS):
            tot += float(np.mean((ms[:, j] - Y[s][mev]) ** 2)) / var[s]
        return tot + float(np.mean((ms[:, -1] - y_min[mev]) ** 2)) / var_m
    out["mate_scores"] = {}
    for K in GRID["mate_k"]:
        m.params["mate_k"] = K
        out["mate_scores"][str(K)] = obj_mate()
    m.params["mate_k"] = min(GRID["mate_k"], key=lambda K: out["mate_scores"][str(K)])
    log(f"  mate_k -> {m.params['mate_k']}")
    # dispersion: NB maximum likelihood given final means
    out["dispersion_ll"] = {}
    disp = {}
    for s in STATS:
        mu = np.array([max(m.predict(e["pid"], s, e["date"], e["opp"], e["home"], teammates_out=e["mates_out"])["mean"], 1e-6)
                       for e in events])
        grid = np.exp(np.linspace(math.log(0.5), math.log(2000), 61))
        lls = [_nb_ll(Y[s], mu, r) for r in grid]
        j = int(np.argmax(lls))
        fine = np.exp(np.linspace(math.log(grid[max(j - 1, 0)]), math.log(grid[min(j + 1, 60)]), 41))
        fl = [_nb_ll(Y[s], mu, r) for r in fine]
        disp[s] = round(float(fine[int(np.argmax(fl))]), 2)
        out["dispersion_ll"][s] = dict(r=disp[s], mean_ll=round(max(fl), 5), poisson_like_ll=round(_nb_ll(Y[s], mu, 1e6), 5))
        out.setdefault("mean_mse_final", {})[s] = float(np.mean((mu - Y[s]) ** 2))
        log(f"  dispersion/{s} -> {disp[s]}")
    out["params"] = _jsonable(m.params)
    out["dispersion"] = disp
    out["trace"] = _jsonable(trace)
    return out


def _set(P, k, v, stat):
    if stat:
        P[k][stat] = v
    else:
        P[k] = v


def _copy(p):
    return {k: dict(v) if isinstance(v, dict) else v for k, v in p.items()}


def _jsonable(x):
    if isinstance(x, dict):
        return {k: _jsonable(v) for k, v in x.items()}
    if isinstance(x, list):
        return [_jsonable(v) for v in x]
    if isinstance(x, float) and math.isinf(x):
        return "inf"
    return x


# ---------------------------------------------------------------- reports
def merge_report(path: str, rep: dict, fresh: bool = False) -> dict:
    """Replace runs with the same name, keep the others (so several periods share a file)."""
    old = []
    if not fresh and os.path.exists(path):
        try:
            old = json.load(open(path)).get("runs", [])
        except Exception:
            old = []
    names = {r["name"] for r in rep["runs"]}
    rep = dict(rep, runs=[r for r in old if r["name"] not in names] + rep["runs"])
    with open(path, "w") as fh:
        json.dump(rep, fh, indent=1, default=str)
    return rep


def write_md(path: str, rep: dict) -> None:
    lines = ["# Prop backtest (walk-forward)", "",
             f"Generated {rep['generated_at']} at commit {rep['commit']} by `python -m nbapicks.propbacktest`. "
             "Machine-readable: reports/backtest_props.json (docs/CONTRACTS.md §2).", ""]
    per = defaultdict(list)
    for r in rep["runs"]:
        per[(r["split"], r["period"]["start"], r["period"]["end"])].append(r)
    for (split, a, b), rs in sorted(per.items(), key=lambda kv: (kv[0][1], kv[0][2])):
        basis = {r["price_basis"] for r in rs}
        lines += [f"## {a} .. {b} ({split}); price basis: {', '.join(sorted(basis))}", "",
                  "| stat | model | n | log loss | Brier | baseline | gain vs baseline | paired t (day-clustered) | bets | ROI |",
                  "|---|---|---|---|---|---|---|---|---|---|"]
        for r in sorted(rs, key=lambda r: (r["market"], MODELS.index(r["model_version"]))):
            pv = r["coverage"].get(f"paired_vs_{r['baseline']}") or {}
            g = f"{pv['gain']:+.5f}" if pv.get("gain") is not None else "-"
            t = f"{pv.get('t')} ({pv.get('t_day_cluster')})" if pv.get("t") is not None else "-"
            roi = f"{r['roi']:+.1%}" if r["roi"] is not None else "null"
            lines.append(f"| {r['market'][5:]} | {r['model_version']} | {r['eligible']} | {r['logloss_model']} | {r['brier_model']} | "
                         f"{r['baseline']} | {g} | {t} | {r['bets']} | {roi} |")
        cov = rs[0]["coverage"]
        lines += ["", f"Coverage: {cov.get('games')} games, {cov.get('player_games')} player-games played, "
                      f"{cov.get('events')} scored per stat after the subsample ({cov.get('subsample')}); "
                      f"dropped {cov.get('dropped_lt10_prior_games', 0)} with < {MIN_PRIOR} prior games and "
                      f"{cov.get('dropped_lt10_mpg', 0)} under {MIN_MPG:g} mpg. Lines: {cov.get('lines')}.", ""]
    lines += ["Positive gain = lower log loss than the baseline on the same events. "
              "ROI is null where no historical price exists; it is never filled from assumed odds.", ""]
    with open(path, "w") as fh:
        fh.write("\n".join(lines))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--start")
    ap.add_argument("--end")
    ap.add_argument("--models", default="props-v0,splitcard,props-v1,naive")
    ap.add_argument("--stats", default=",".join(STATS))
    ap.add_argument("--hist-dir", default="data/history")
    ap.add_argument("--out", default="reports/backtest_props.json")
    ap.add_argument("--refresh", action="store_true", help="ignore and overwrite cached results")
    ap.add_argument("--no-cache", action="store_true")
    ap.add_argument("--holdout", action="store_true", help="allow a period in the props holdout (once per frozen candidate)")
    ap.add_argument("--fresh", action="store_true", help="overwrite the report instead of merging runs by name")
    ap.add_argument("--fit", action="store_true", help="fit props-v1 constants on explore; writes reports/props_v1_fit.json")
    a = ap.parse_args(argv)
    if a.fit:
        res = fit(a.hist_dir, not a.no_cache, a.refresh)
        res["generated_at"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        res["commit"] = _commit()
        with open("reports/props_v1_fit.json", "w") as fh:
            json.dump(res, fh, indent=1, default=str)
        print(json.dumps({k: res[k] for k in ("params", "dispersion")}, indent=1, default=str))
        return 0
    if not (a.start and a.end):
        ap.error("--start and --end are required (or --fit)")
    try:
        rep = run_backtest(a.start, a.end, a.models.split(","), a.stats.split(","), a.hist_dir,
                           not a.no_cache, a.holdout, a.refresh)
    except HoldoutRefused as e:
        print(f"refused: {e}", file=sys.stderr)
        return 2
    rep = merge_report(a.out, rep, a.fresh)
    write_md(a.out.replace(".json", ".md"), rep)
    for r in rep["runs"]:
        pv = r["coverage"].get(f"paired_vs_{r['baseline']}") or {}
        print(f"{r['name']}: n={r['eligible']} ll={r['logloss_model']} base={r['logloss_baseline']} gain={pv.get('gain')} t={pv.get('t')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
