"""The learning loop: score every finished slate, refit, and change nothing until the evidence is in.

Every DraftKings prop is a question the market answers with a price and the game answers with a
result. With the sides labelled (nbapicks/sideorder.py) every graded pair can be scored, about 340
a slate. After each settle that grades something new, `run` does five things and writes
data/research/learned.json, reports/learning_latest.md and one line in data/research/learning_log.jsonl:

  market       how well the raw fair chance (the last pair before tip, margin removed) predicted results.
  corrections  a fixed list of small corrections to that fair chance. Each is refitted on all earlier
               slates and scored on the next slate, which it has not seen (walk-forward):
                 shift          one constant on the log-odds (an Over or Under bias)
                 shift_slope    constant and slope (favourites over- or under-priced)
                 stat_shift     a constant per stat, pulled toward a common one
                 recent_shift   one constant, recent slates weighted more (half-life 10 slates)
                 model:<v>      the market plus a weight on prop model <v>'s disagreement with it
               All are shrunk toward "the market is right", so with little data they do nothing.
  gate         a correction is put in force only when, on slates it had not seen, (a) its adjustments
               leaned the right way by `activate_z` standard errors, (b) applying it lowered log loss,
               over all those slates and over their newer half, and (c) there are `min_slates` such
               slates and `min_pairs` props. It is dropped when (a) falls under `keep_z` or (b) fails.
               At most one is in force: recent_shift when it passes, because it lets go soonest
               when a bias ends, unless another that passes explains clearly more (`judge`).
               The numbers are in config/gates.yaml (`learning`).
  rules        a fixed list of simple pick rules graded at the last price before tip, so "would this
               have paid" has a standing answer with its error bar.
  picks        the posted prop picks against later prices of the same bet (closing-line value).

`adjust(active(state, today), fair, ...)` applies the correction in force to a fair chance and is
the identity when none is. Nothing here changes a pick by itself: a pick rule has to call `adjust`.
The loop never reads the props holdout window of config/gates.yaml or anything before it.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import os

import numpy as np

from . import propsides as PS
from . import sideorder as SO
from . import track
from .metrics import noise_floor
from .odds import american_to_decimal, decimal_to_american, devig_multiplicative
from .sources import espn

STATE = "learned.json"
LOG = "learning_log.jsonl"
REPORT = "learning_latest.md"
VERSION = 1                     # bump when the corrections or the scoring change: forces a refit
HISTORY_DAYS = 240              # about one season of slates
STALE_DAYS = 30                 # a correction with no graded slate for this long is not applied
HOLDOUT_END = dt.date(2026, 6, 30)   # used when config/gates.yaml cannot be read
MIN_TRAIN_SLATES = 5            # a correction is first scored after this many slates to learn from
STATS = ("pts", "reb", "ast", "fg3m")
RECENT_HALF_LIFE = 10.0         # slates: in recent_shift a result counts half as much after this many newer slates
# Priors, as ridge penalties on the log-odds scale. One even-money result carries 0.25 of information
# about a constant, so 125 says "as if 500 results had already shown the market to be right".
L_SHIFT, L_SLOPE, L_STAT, L_MODEL = 125.0, 20.0, 375.0, 90.0
GATE = dict(min_slates=15, min_pairs=3000, activate_z=3.0, keep_z=2.0, min_gain=0.0, richer=1.5, rule_min_bets=300)
MIN_EV = 0.05                   # the prop edge threshold of config markets.prop.min_ev


def _logit(p):
    p = np.clip(np.asarray(p, float), 1e-4, 1 - 1e-4)
    return np.log(p / (1 - p))


def _sig(z):
    return 1 / (1 + np.exp(-np.asarray(z, float)))


def _t(s: str) -> dt.datetime:
    return dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))


def _gates_file(path: str) -> dict:
    try:
        import yaml
        with open(path) as fh:
            return yaml.safe_load(fh) or {}
    except FileNotFoundError:
        return {}


def gates(path: str = "config/gates.yaml") -> dict:
    """The `learning` gate: the built-in numbers, overridden by config/gates.yaml where it has them."""
    return {**GATE, **(_gates_file(path).get("learning") or {})}


def first_slate(today: dt.date, path: str = "config/gates.yaml") -> str:
    """The earliest slate the loop may read: HISTORY_DAYS back, and never the props holdout window
    (props.splits.holdout in config/gates.yaml) or anything before it."""
    end = (((_gates_file(path).get("props") or {}).get("splits") or {}).get("holdout") or {}).get("end") or HOLDOUT_END
    if not isinstance(end, dt.date):
        end = dt.date.fromisoformat(str(end))
    return max(today - dt.timedelta(days=HISTORY_DAYS), end + dt.timedelta(days=1)).isoformat()


# ---------------------------------------------------------------- the graded table
def graded(store, tz: str, since: str) -> list[dict]:
    """Every graded DraftKings pair (the last one stored before tip) with the prop model's last
    pre-tip P(over) at that line, if it had one. Sides are by listing order, so call this only
    while that order is confirmed (sideorder.status)."""
    pairs = [r for r in SO.closing_pairs(store, tz, since) if r["over"] is not None]
    if not pairs:
        return []
    tips = {g["game_id"]: _t(g["start_utc"]) for g in store.q("SELECT game_id, start_utc FROM games")}
    want = {(r["game_id"], r["player_id"], r["stat"], r["line"]) for r in pairs}
    model: dict[tuple, tuple] = {}
    for p in store.q("SELECT game_id, player_id, stat, line, prob, prob_push, model_version, created_at FROM predictions "
                     "WHERE origin = 'model' AND market = 'prop' AND category = 'straight' AND selection = 'over' "
                     "AND book = 'DraftKings' AND prob IS NOT NULL AND created_at >= ?",
                     [(dt.date.fromisoformat(since) - dt.timedelta(days=4)).isoformat()]):
        k = (p["game_id"], str(p["player_id"]), p["stat"], p["line"])
        if k not in want or _t(p["created_at"]) >= tips[p["game_id"]]:
            continue                                    # another line, or priced after tip
        if k not in model or p["created_at"] > model[k][0]:
            model[k] = (p["created_at"], p["prob"] / max(1e-9, 1 - (p["prob_push"] or 0)), p["model_version"])
    out = []
    for r in pairs:
        m = model.get((r["game_id"], r["player_id"], r["stat"], r["line"]))
        out.append(dict(slate=r["slate"], game_id=r["game_id"], player_id=r["player_id"], stat=r["stat"], line=r["line"],
                        p_mkt=r["p_first"], price_over=r["price_first"], price_under=r["price_second"], over=r["over"],
                        lead_h=(tips[r["game_id"]] - _t(r["at"])).total_seconds() / 3600,
                        p_model=m[1] if m else None, model_version=m[2] if m else None))
    return out


class Table:
    """The graded rows as arrays, slates numbered in date order."""

    def __init__(self, rows: list[dict]):
        self.slates = sorted({r["slate"] for r in rows})
        ix = {s: i for i, s in enumerate(self.slates)}
        self.s = np.array([ix[r["slate"]] for r in rows], int)
        self.y = np.array([r["over"] for r in rows], float)
        self.z = _logit([r["p_mkt"] for r in rows])                 # the market's log-odds of the Over
        self.stat = np.array([r["stat"] for r in rows])
        self.has_model = np.array([r.get("p_model") is not None for r in rows], bool)
        self.zm = _logit([r["p_model"] if r.get("p_model") is not None else 0.5 for r in rows])
        self.version = np.array([r.get("model_version") or "" for r in rows])
        self.over_dec = np.array([r["price_over"] for r in rows], float)
        self.under_dec = np.array([r["price_under"] for r in rows], float)
        self.lead_h = np.array([r.get("lead_h", np.nan) for r in rows], float)


# ---------------------------------------------------------------- corrections
def _fit(X, y, offset, lam, prior, w=None):
    """Penalised logistic regression with an offset, by Newton steps: maximise
    sum w (y log p + (1 - y) log(1 - p)) - 1/2 sum lam (b - prior)^2 with p = sig(offset + X b)."""
    prior = np.asarray(prior, float)
    b, lam = prior.copy(), np.asarray(lam, float)
    w = np.ones(len(y)) if w is None else w
    for _ in range(60):
        p = _sig(offset + X @ b)
        g = X.T @ (w * (y - p)) - lam * (b - prior)
        H = (X * (w * p * (1 - p))[:, None]).T @ X + np.diag(lam)
        step = np.linalg.solve(H, g)
        b = b + step
        if np.abs(step).max() < 1e-9:
            break
    return b


def _design(name: str, t: Table, idx):
    """(X, offset, penalties, prior) of a correction on the rows idx."""
    one, z = np.ones(len(idx)), t.z[idx]
    if name in ("shift", "recent_shift"):
        return one[:, None], z, [L_SHIFT], [0.0]
    if name == "shift_slope":
        return np.column_stack([one, z]), np.zeros(len(idx)), [L_SHIFT, L_SLOPE], [0.0, 1.0]
    if name == "stat_shift":
        return (np.column_stack([one] + [(t.stat[idx] == s).astype(float) for s in STATS]), z,
                [L_SHIFT] + [L_STAT] * len(STATS), [0.0] * (1 + len(STATS)))
    if name.startswith("model:"):
        return np.column_stack([one, t.zm[idx] - z]), z, [L_SHIFT, L_MODEL], [0.0, 0.0]
    raise ValueError(name)


def _rows_for(name: str, t: Table):
    """Rows a correction can use: all of them, or the ones its model version priced."""
    if name.startswith("model:"):
        return np.flatnonzero(t.has_model & (t.version == name.split(":", 1)[1]))
    return np.arange(len(t.y))


def fit(name: str, t: Table, idx, now: int | None = None) -> np.ndarray:
    """The correction's parameters from the rows idx; `now` is the slate number it will be used on."""
    X, off, lam, prior = _design(name, t, idx)
    w = None
    if name == "recent_shift":
        w = 0.5 ** (((len(t.slates) if now is None else now) - t.s[idx]) / RECENT_HALF_LIFE)
    return _fit(X, t.y[idx], off, lam, prior, w)


CORRECTIONS = ["shift", "shift_slope", "stat_shift", "recent_shift"]      # plus one model:<version> per prop model seen
PREFER = "recent_shift"         # of the corrections that pass, this one is used unless another explains clearly more (judge)


def names(t: Table) -> list[str]:
    return CORRECTIONS + [f"model:{v}" for v in sorted({str(v) for v in t.version[t.has_model]})]


def _ll(p, y):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def walk_forward(t: Table) -> dict:
    """Each correction fitted on the slates before a slate and scored on it. Per correction:
    `per` = [(slate number, props, log loss saved in total, score)] for every slate it was scored on,
    where score = sum of adjustment x (result - market chance): positive when the adjustments leaned
    the way the results went. `params` are fitted on everything, for use on the next slate."""
    p0 = _sig(t.z)
    base, resid = _ll(p0, t.y), t.y - p0
    out = {}
    for name in names(t):
        rows = _rows_for(name, t)
        s = t.s[rows]
        per = []
        for i in np.unique(s):
            tr, te = rows[s < i], rows[s == i]
            if len(np.unique(t.s[tr])) < MIN_TRAIN_SLATES:
                continue
            X, off, _, _ = _design(name, t, te)
            eta = off + X @ fit(name, t, tr, now=int(i))
            per.append((int(i), len(te), float((base[te] - _ll(_sig(eta), t.y[te])).sum()), float(((eta - t.z[te]) * resid[te]).sum())))
        final = fit(name, t, rows) if len(np.unique(s)) >= MIN_TRAIN_SLATES else None
        out[name] = dict(per=per, params=None if final is None else [round(float(x), 5) for x in final], trained_on=int(len(rows)))
    return out


def summarise(per: list[tuple]) -> dict:
    """Out-of-sample summary of one correction from its per-slate rows.
    gain: log loss saved per prop, with a day-clustered standard error and t.
    z: the summed score over the root of its summed squares by slate. With no real effect this is
    about standard normal; it measures direction only, so it has about twice the power of gain_t.
    older/newer: gain on the first and second half of the slates."""
    k = len(per)
    if not k:
        return dict(slates=0, n=0, gain=None, gain_se=None, gain_t=None, z=None, older=None, newer=None, slates_better=0)
    n, G, U = (np.array([p[j] for p in per], float) for j in (1, 2, 3))
    N = n.sum()
    gain = G.sum() / N
    se = float(np.sqrt(((G - n * gain) ** 2).sum() * k / (k - 1)) / N) if k > 1 else None
    uu = float((U ** 2).sum())
    h = k // 2
    return dict(slates=k, n=int(N), gain=float(gain), gain_se=se, gain_t=float(gain / se) if se else None,
                z=float(U.sum() / math.sqrt(uu)) if uu > 0 else None,
                older=float(G[:h].sum() / n[:h].sum()) if h else None, newer=float(G[h:].sum() / n[h:].sum()),
                slates_better=int((G > 0).sum()))


def judge(stats: dict, gate: dict, incumbent: str | None) -> tuple[str | None, dict]:
    """(the correction in force or None, a verdict per correction).

    Which of the corrections that pass is used: PREFER (recent_shift), because a bias that is real
    can still end and it is the one that follows it; unless another has saved at least `richer` times
    as much log loss per prop on unseen slates, which means it explains more than a plain bias does
    (a model that knows something, a bias in one stat only). When PREFER does not pass, the
    incumbent stays while it clears the keep bar, otherwise the one with the most evidence."""
    floor = noise_floor(len(stats))
    ok, verdicts = [], {}
    for name, s in stats.items():
        bar = max(gate["keep_z"] if name == incumbent else gate["activate_z"], floor)
        why = []
        if s["slates"] < gate["min_slates"] or s["n"] < gate["min_pairs"]:
            why.append(f"needs {gate['min_slates']} unseen slates and {gate['min_pairs']:,} props (has {s['slates']} and {s['n']:,})")
        if s["z"] is None or s["z"] < bar:
            why.append(f"evidence {0 if s['z'] is None else s['z']:+.2f} is under {bar:.2f}")
        if s["gain"] is None or s["gain"] <= gate["min_gain"]:
            why.append("it did not lower log loss on unseen slates")
        elif s["newer"] is None or s["newer"] <= gate["min_gain"]:
            why.append("no gain on the newer half of the unseen slates")
        if why:
            verdicts[name] = "not in force: " + "; ".join(why)
        else:
            ok.append((s["z"], name))
    passing = [n for _, n in ok]
    if PREFER in passing:
        richer = [n for n in passing if n != PREFER and stats[n]["gain"] >= gate["richer"] * stats[PREFER]["gain"]]
        active = max(richer, key=lambda n: (stats[n]["gain"], n)) if richer else PREFER
    else:
        active = incumbent if incumbent in passing else (max(ok)[1] if ok else None)
    for _, n in ok:
        verdicts[n] = "in force" if n == active else f"passes, but {active} is in force"
    return active, verdicts


def active(state: dict | None, today: dt.date | None = None) -> dict | None:
    """The correction in force, or None: nothing passed the gate, or (given today) the last graded
    slate is more than STALE_DAYS old, as after a summer."""
    a = (state or {}).get("active")
    if not a:
        return None
    if today is not None:
        try:
            if (today - dt.date.fromisoformat(state.get("through"))).days > STALE_DAYS:
                return None
        except (TypeError, ValueError):
            return None
    return a


def adjust(a: dict | None, fair: float, stat: str | None = None, model_prob: float | None = None,
           model_version: str | None = None) -> float:
    """The fair chance of the Over after the correction `a` (from `active`). Unchanged when there is
    none or it cannot be applied (a model correction without that model's estimate). The Under is
    1 minus this."""
    if not a or fair is None or not 0 < fair < 1:
        return fair
    name, b = a["learner"], a["params"]
    z = float(_logit(fair))
    if name in ("shift", "recent_shift"):
        return float(_sig(z + b[0]))
    if name == "shift_slope":
        return float(_sig(b[0] + b[1] * z))
    if name == "stat_shift":
        return float(_sig(z + b[0] + (b[1 + STATS.index(stat)] if stat in STATS else 0.0)))
    if name.startswith("model:"):
        if model_prob is None or not 0 < model_prob < 1 or model_version != name.split(":", 1)[1]:
            return fair
        return float(_sig(z + b[0] + b[1] * (float(_logit(model_prob)) - z)))
    return fair


# ---------------------------------------------------------------- the market, the rules, the picks
def _mean_se(v, cluster) -> tuple[float | None, float | None]:
    """Mean of v and its standard error clustered by `cluster` (a slate's props share a night)."""
    v = np.asarray(v, float)
    if not len(v):
        return None, None
    mean = float(v.mean())
    _, inv = np.unique(np.asarray(cluster), return_inverse=True)
    k = int(inv.max()) + 1
    if k < 2:
        return mean, None
    dev = np.bincount(inv, weights=v) - np.bincount(inv) * mean
    return mean, float(np.sqrt((dev ** 2).sum() * k / (k - 1)) / len(v))


def market_fit(t: Table) -> dict:
    """How the raw fair chance did: log loss, the Over rate against it, and the constant and slope
    that would have fitted best (0 and 1 mean the price was right on average), day-clustered."""
    n, p = len(t.y), _sig(t.z)
    X = np.column_stack([np.ones(n), t.z])
    tiny = [1e-6, 1e-6]                                 # keeps the fit defined when every pair has the same price
    b = _fit(X, t.y, np.zeros(n), tiny, [0.0, 1.0])
    q = _sig(X @ b)
    Hi = np.linalg.inv((X * (q * (1 - q))[:, None]).T @ X + np.diag(tiny))
    S = np.zeros((2, 2))
    for i in np.unique(t.s):
        sc = X[t.s == i].T @ (t.y[t.s == i] - q[t.s == i])
        S += np.outer(sc, sc)
    k = len(t.slates)
    se = np.sqrt(np.diag(Hi @ S @ Hi) * k / max(k - 1, 1))
    gap, gap_se = _mean_se(t.y - p, t.s)
    lead = t.lead_h[~np.isnan(t.lead_h)]
    return dict(pairs=n, slates=k, logloss=round(float(_ll(p, t.y).mean()), 5), over_rate=round(float(t.y.mean()), 4),
                fair_over=round(float(p.mean()), 4), over_minus_fair=round(gap, 4),
                over_minus_fair_se=None if gap_se is None else round(gap_se, 4),
                shift=round(float(b[0]), 4), shift_se=round(float(se[0]), 4), slope=round(float(b[1]), 3), slope_se=round(float(se[1]), 3),
                median_hours_before_tip=round(float(np.median(lead)), 1) if len(lead) else None)


RULES = (["every Over", "every Under"] + [f"every {s} Under" for s in STATS] +
         ["the favourite (fair chance 55% or more)", "the underdog (fair chance 45% or less)",
          "model edge of 5% or more at the price", "model 60% or more at -200 or longer (the pick rule on main)",
          "the same, within 10 points of the market"])


def _rule_bets(t: Table) -> dict:
    """name -> [(rows, True when the bet is the Over)] for the fixed list RULES."""
    p_mkt = _sig(t.z)
    pm = np.where(t.has_model, _sig(t.zm), np.nan)
    ev_o, ev_u = pm * t.over_dec - 1, (1 - pm) * t.under_dec - 1
    with np.errstate(invalid="ignore"):                 # comparisons with "no model estimate" are False
        lean_o = (pm >= 0.60) & (t.over_dec >= 1.5)
        lean_u = ((1 - pm) >= 0.60) & (t.under_dec >= 1.5) & ~lean_o
        near = np.abs(pm - p_mkt) <= 0.10
        best_o = (ev_o >= MIN_EV) & (ev_o >= ev_u)
        best_u = (ev_u >= MIN_EV) & (ev_u > ev_o)
    every = np.ones(len(t.y), bool)
    bets = [[(every, True)], [(every, False)]] + [[(t.stat == s, False)] for s in STATS] + [
        [(p_mkt >= 0.55, True), (p_mkt <= 0.45, False)], [(p_mkt <= 0.45, True), (p_mkt >= 0.55, False)],
        [(best_o, True), (best_u, False)], [(lean_o, True), (lean_u, False)], [(lean_o & near, True), (lean_u & near, False)]]
    return dict(zip(RULES, bets))


def rules(t: Table, gate: dict) -> dict:
    """Flat 1 unit on every prop a rule would take, at the last price before tip."""
    bets = _rule_bets(t)
    bar = max(gate["activate_z"], noise_floor(len(bets)))
    last10 = len(t.slates) - 10
    out = {}
    for name, parts in bets.items():
        net = np.concatenate([np.where((t.y[m] == 1) == is_over, (t.over_dec if is_over else t.under_dec)[m] - 1, -1.0) for m, is_over in parts])
        where = np.concatenate([t.s[m] for m, _ in parts])
        price = np.concatenate([(t.over_dec if is_over else t.under_dec)[m] for m, is_over in parts])
        n = len(net)
        roi, se = _mean_se(net, where)
        tt = roi / se if se else None
        recent = net[where >= last10]
        out[name] = dict(bets=n, hit=round(float((net > 0).mean()), 4) if n else None, avg_price=round(float(price.mean()), 3) if n else None,
                         roi=None if roi is None else round(roi, 4), se=None if se is None else round(se, 4),
                         t=None if tt is None else round(tt, 2),
                         roi_last10=round(float(recent.mean()), 4) if len(recent) else None, bets_last10=int(len(recent)),
                         flag=bool(tt is not None and n >= gate["rule_min_bets"] and tt >= bar))
    return out


def _american(dec: float) -> float:
    """A decimal price rounded the way it is shown and recorded (American), back in decimal."""
    return american_to_decimal(decimal_to_american(dec))


def pair_history(store, game_id: str, player_id: str, stat: str) -> list[tuple]:
    """The DraftKings two-way quotes stored for one player prop before tip, oldest first:
    [(observed_at, line, over price, under price)], a new entry whenever a price or the line changed."""
    g = store.one("SELECT start_utc FROM games WHERE game_id = ?", [game_id])
    if not g:
        return []
    tip, cur, out = _t(g["start_utc"]), {}, []
    for r in store.q("SELECT line, selection, price_dec, observed_at, book FROM odds WHERE game_id = ? AND market = 'prop' "
                     "AND player_id = ? AND stat = ? AND kind = 'current' AND source = 'espn' AND selection IN ('side0', 'side1') "
                     "ORDER BY observed_at", [game_id, player_id, stat]):
        if r["line"] is None or not r["price_dec"] or espn.canon_book(r["book"]) not in SO.BOOKS or _t(r["observed_at"]) >= tip:
            continue
        cur[(r["line"], r["selection"])] = r["price_dec"]
        a, b = cur.get((r["line"], "side0")), cur.get((r["line"], "side1"))
        if a and b and PS.plausible_pair(a, b):
            if out and out[-1][:2] == (r["observed_at"], r["line"]):
                out[-1] = (r["observed_at"], r["line"], a, b)
            else:
                out.append((r["observed_at"], r["line"], a, b))
    return out


def picks_clv(store, leans: list[dict], since: str) -> dict:
    """Posted prop picks against later DraftKings prices of the same bet, by source.

    A pick is matched to the DraftKings quote it was posted on: of the stored quotes at its line
    that show its DraftKings price, the last one stored by the time the slate's picks went out,
    else the first one. Its DraftKings price is `ref_price_american` when the pick was taken at
    another book, else the recorded price. Before the sides were labelled the recorded price was
    the worse of the pair whichever side that was, so either side may show it, and the pick's real
    price is the quote's price for its own side.
    The pick is then compared with the last quote stored at the same line before tip, when there
    is a later one:
      move    DraftKings' price for the pick's side when posted over its later price, minus 1.
              Above 0 means DraftKings shortened that side afterwards: the market came toward the pick.
      value   the price taken times the later fair chance, minus 1: what the pick was worth per unit
              if the later price was right. A pick with no edge is worth the book margin.
    A change of the main line is counted and not compared: DraftKings moves between neighbouring
    lines (Over 2.5 at -170, then Under 3.5 at -170) without changing its view."""
    out_at: dict[str, str] = {}
    for p in store.q("SELECT slate_date, at FROM publications WHERE kind = 'picks' ORDER BY at"):
        out_at.setdefault(p["slate_date"], p["at"])
    rows = []
    for l in leans:
        if l.get("market") != "prop" or l.get("selection") not in ("over", "under") or not l.get("price_american") \
                or l.get("line") is None or str(l.get("slate")) < since:
            continue
        over = l["selection"] == "over"
        mine, ref = (2 if over else 3), l.get("ref_price_american")
        hist = pair_history(store, l["game_id"], str(l.get("player_id")), l.get("stat"))
        shows = [i for i, h in enumerate(hist) if h[1] == l["line"] and (
            decimal_to_american(h[mine]) == ref if ref is not None
            else l["price_american"] in (decimal_to_american(h[2]), decimal_to_american(h[3])))]
        when = l.get("posted_at") or out_at.get(l["slate"]) or l.get("quoted_at")
        by_then = [i for i in shows if when and _t(hist[i][0]) <= _t(when)]
        i = by_then[-1] if by_then else (shows[0] if shows else None)
        row = dict(source=l.get("source") or "unknown", slate=l["slate"], priced=i is not None)
        if i is not None:
            dk = hist[i][mine]
            taken = american_to_decimal(l["price_american"]) if ref is not None else _american(dk)
            row["repriced"] = ref is None and decimal_to_american(dk) != l["price_american"]
            row["line_changed"] = hist[-1][1] != l["line"]
            later = [h for h in hist[i + 1:] if h[1] == l["line"]]
            if later:
                last = later[-1]
                row.update(move=_american(dk) / _american(last[mine]) - 1,
                           value=taken * devig_multiplicative([last[2], last[3]])[0 if over else 1] - 1,
                           margin=1 / (1 / last[2] + 1 / last[3]) - 1)
        rows.append(row)
    r4 = lambda x: None if x is None else round(x, 4)       # noqa: E731
    out = {}
    for src in ["all"] + sorted({r["source"] for r in rows}):
        rs = [r for r in rows if src in ("all", r["source"])]
        cmp_ = [r for r in rs if "move" in r]
        move, move_se = _mean_se([r["move"] for r in cmp_], [r["slate"] for r in cmp_])
        value, value_se = _mean_se([r["value"] for r in cmp_], [r["slate"] for r in cmp_])
        out[src] = dict(picks=len(rs), priced=sum(r["priced"] for r in rs), repriced=sum(r.get("repriced", False) for r in rs),
                        later=len(cmp_), toward=sum(r["move"] > 1e-9 for r in cmp_), same=sum(abs(r["move"]) <= 1e-9 for r in cmp_),
                        away=sum(r["move"] < -1e-9 for r in cmp_), move=r4(move), move_se=r4(move_se), value=r4(value),
                        value_se=r4(value_se), margin=r4(float(np.mean([r["margin"] for r in cmp_])) if cmp_ else None),
                        line_changed=sum(r.get("line_changed", False) for r in rs))
    return out


# ---------------------------------------------------------------- state, report, run
def load(root: str) -> dict:
    try:
        with open(os.path.join(root, "research", STATE)) as fh:
            return json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _log(root: str, entry: dict) -> None:
    """One line per graded slate in the learning log: what the loop believed once that slate was in,
    so its decisions can be checked later against what it knew. A slate is graded over several runs
    as its games finish; its line is the last of them."""
    path = os.path.join(root, "research", LOG)
    try:
        with open(path) as fh:
            lines = [x for x in fh.read().splitlines() if x.strip()]
    except FileNotFoundError:
        lines = []
    try:
        if lines and json.loads(lines[-1]).get("through") == entry["through"]:
            lines.pop()
    except json.JSONDecodeError:
        pass                                            # a damaged last line is kept as it is
    with open(path + ".tmp", "w") as fh:
        fh.write("\n".join(lines + [json.dumps(entry, sort_keys=True)]) + "\n")
    os.replace(path + ".tmp", path)


def _f(x, spec: str, none: str = "n/a") -> str:
    return none if x is None else format(x, spec)


def _pct(x, digits: int = 1) -> str:
    return "n/a" if x is None else f"{x * 100:+.{digits}f}%"


def report_md(st: dict) -> str:
    m, a, g = st["market"], st.get("active"), st["gate"]
    out = ["# What the system has learned from its own results", "",
           "Written by `nbapicks/learn.py` after every settle that grades something new. How it works: `docs/LEARNING.md`.", "",
           f"**Through {st['through']}: {m['pairs']:,} graded DraftKings props on {m['slates']} slates.**", ""]
    if a:
        out += [f"**A correction is in force: `{a['learner']}`, since {a['since']}.** It cleared the gate on slates it had not seen "
                "and stays only while it keeps doing so.", ""]
    else:
        out += ["**No correction is in force.** The DraftKings price with the margin removed is still the best estimate here: "
                "nothing tested below beat it reliably on slates it had not seen.", ""]
    out += ["## How good the market price was", "",
            "The fair chance is the last pair of prices stored before tip with the book's margin removed"
            + (f" (half of them within {m['median_hours_before_tip']:g} hours of tip)." if m.get("median_hours_before_tip") is not None else "."), "",
            f"- Overs won {m['over_rate']:.1%}. The fair chance said {m['fair_over']:.1%}: a difference of {m['over_minus_fair'] * 100:+.1f} points"
            + (f" (standard error {m['over_minus_fair_se'] * 100:.1f})." if m.get("over_minus_fair_se") is not None else "."),
            f"- Best-fitting constant {m['shift']:+.3f} (se {m['shift_se']:.3f}) and slope {m['slope']:.2f} (se {m['slope_se']:.2f}) on the log-odds. "
            "0 and 1 would mean the price was right on average. This is measured on the same slates it is fitted on, "
            "so it flatters any pattern; the table below is the honest test.",
            f"- Log loss of the fair chance: {m['logloss']:.4f} (a coin flip scores 0.6931).", "",
            "## Corrections, scored on slates they had not seen", "",
            "Each correction is refitted before every slate on the earlier slates only, then scored on that slate. "
            "Evidence is how many standard errors its adjustments leaned the way the results went (about 0 when it knows nothing). "
            "Gain is the log loss it saved per prop against the plain fair chance (above 0 is better).", "",
            "| correction | unseen slates | props | evidence | gain | gain, older half | gain, newer half | slates it helped | status |",
            "|---|---|---|---|---|---|---|---|---|"]
    for name in sorted(st["learners"], key=lambda n: (CORRECTIONS.index(n) if n in CORRECTIONS else len(CORRECTIONS), n)):
        d = st["learners"][name]
        out.append(f"| {name} | {d['slates']} | {d['n']:,} | {_f(d['z'], '+.2f')} | {_f(d['gain'], '+.5f')} | {_f(d['older'], '+.5f')} | "
                   f"{_f(d['newer'], '+.5f')} | {d['slates_better']} of {d['slates']} | {d['verdict']} |")
    out += ["", f"The gate: evidence of {max(g['activate_z'], st['noise_floor']):.2f} or more on at least {g['min_slates']} unseen slates and "
                f"{g['min_pairs']:,} props, with a gain overall and on the newer half. A correction in force is dropped when its evidence "
                f"falls under {max(g['keep_z'], st['noise_floor']):.2f} or the gain goes. The bar is 3 and not 2 because it is checked after every slate. "
                f"When several pass, `{PREFER}` is used, because it lets go soonest when a bias ends, unless another saved "
                f"{g['richer']:g} times as much per prop.", "",
            "## Simple rules at the last price before tip", "",
            "Flat 1 unit on every prop a rule would take. Nothing is fitted, so every slate counts. "
            "ROI is profit per unit staked; t is ROI over its day-clustered standard error.", "",
            "| rule | bets | won | average price | ROI | se | t | ROI, last 10 slates |", "|---|---|---|---|---|---|---|---|"]
    for name in [n for n in RULES if n in st["rules"]] + sorted(set(st["rules"]) - set(RULES)):
        r = st["rules"][name]
        out.append(f"| {name}{' **(clears the bar)**' if r['flag'] else ''} | {r['bets']:,} | {_f(r['hit'], '.1%')} | {_f(r['avg_price'], '.2f')} | "
                   f"{_pct(r['roi'])} | {_f(None if r['se'] is None else r['se'] * 100, '.1f')} | {_f(r['t'], '+.2f')} | "
                   f"{_pct(r['roi_last10'])} on {r['bets_last10']:,} |")
    flagged = [n for n in RULES if st["rules"].get(n, {}).get("flag")]
    out += ["", (f"Clears the bar (t of 3 or more on {g['rule_min_bets']} or more bets): " + "; ".join(flagged)
                 + ". That earns a forward test, not a promotion." if flagged else
                 f"No rule clears the bar (t of 3 or more on {g['rule_min_bets']} or more bets)."), "",
            "## Posted picks against later prices", "",
            "Each posted prop pick is matched to the DraftKings quote it was posted on and compared with the last quote stored "
            "at the same line before tip, when there is a later one. The market coming toward a pick after it is posted is the "
            "earliest sign of a real edge. Move is DraftKings' price for the pick's side when posted against its later price "
            "(above 0: that side got shorter). Value is what the pick was worth per unit if the later price was right; "
            "a pick with no edge is worth the book margin.", "",
            "| source | picks | matched to a quote | with a later price | market moved toward / not / away | average move | "
            "value at the later fair chance | book margin there | main line changed |", "|---|---|---|---|---|---|---|---|---|"]
    for src in ["all"] + sorted(set(st["picks"]) - {"all"}):
        c = st["picks"][src]
        se = {k: "" if c[k] is None else f" (se {c[k] * 100:.1f})" for k in ("move_se", "value_se")}
        out.append(f"| {src} | {c['picks']} | {c['priced']} | {c['later']} | {c['toward']} / {c['same']} / {c['away']} | "
                   f"{_pct(c['move'])}{se['move_se']} | {_pct(c['value'])}{se['value_se']} | {_pct(c['margin'])} | {c['line_changed']} |")
    out += ["", "A change of the main line is counted but not compared: DraftKings moves between neighbouring lines "
                "(Over 2.5 at -170, then Under 3.5 at -170) without changing its view."]
    if st["picks"]["all"]["repriced"]:
        out += [f"{st['picks']['all']['repriced']} picks were recorded at the price of the other side (before the sides were labelled); "
                "their own side's price is used here."]
    if st.get("changes"):
        out += ["", "## Changes", ""] + [f"- {c['at']}: {c['what']}" for c in st["changes"]]
    return "\n".join(out) + "\n"


def run(ctx, force: bool = False) -> dict:
    """Score, refit and store. Costs two counts when nothing new was graded or posted."""
    root, gate = ctx.root, gates()
    old = load(root)
    leans = track.load(root)
    mark = [VERSION, ctx.store.one("SELECT count(*) n FROM games WHERE status = 'final'")["n"],
            ctx.store.one("SELECT count(*) n FROM player_games")["n"], len(leans), gate]
    if not force and old.get("mark") == mark:
        return dict(status="unchanged", through=old.get("through"), active=(old.get("active") or {}).get("learner"))
    order = SO.status(SO.load(root), ctx.today)
    if order != "confirmed":
        return dict(status=f"skipped: prop sides are {order or 'not measured yet'}, so results cannot be matched to a side")
    since = first_slate(ctx.today)
    rows = graded(ctx.store, ctx.tz, since)
    if len({r["slate"] for r in rows}) <= MIN_TRAIN_SLATES:
        return dict(status=f"skipped: {len({r['slate'] for r in rows})} graded slates, the loop starts after {MIN_TRAIN_SLATES}")
    t = Table(rows)
    wf = walk_forward(t)
    stats = {name: summarise(d["per"]) for name, d in wf.items()}
    was = (old.get("active") or {}).get("learner")
    now_active, verdicts = judge(stats, gate, was)
    learners = {name: dict({k: (round(v, 6) if isinstance(v, float) else v) for k, v in stats[name].items()},
                           params=wf[name]["params"], trained_on=wf[name]["trained_on"], verdict=verdicts[name]) for name in wf}
    changes = list(old.get("changes") or [])
    if now_active != was:
        what = (f"{now_active} put in force (evidence {stats[now_active]['z']:+.2f} on {stats[now_active]['n']:,} unseen props)" if now_active
                else f"{was} dropped ({verdicts.get(was, 'it is no longer fitted')})")
        changes.append(dict(at=ctx.now.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), what=what))
        ctx.notes.append(f"learning: {what}")
    st = dict(version=VERSION, mark=mark, through=t.slates[-1], market=market_fit(t), learners=learners, gate=gate,
              noise_floor=round(noise_floor(len(learners)), 3),
              active=None if not now_active else dict(learner=now_active, params=wf[now_active]["params"],
                                                      since=old["active"]["since"] if now_active == was else t.slates[-1]),
              rules=rules(t, gate), picks=picks_clv(ctx.store, leans, since), changes=changes[-30:])
    path = os.path.join(root, "research", STATE)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path + ".tmp", "w") as fh:
        json.dump(st, fh, indent=1, sort_keys=True)
    os.replace(path + ".tmp", path)
    rep = os.path.join(os.path.dirname(os.path.abspath(root)), "reports")
    os.makedirs(rep, exist_ok=True)
    with open(os.path.join(rep, REPORT), "w") as fh:
        fh.write(report_md(st))
    _log(root, dict(through=st["through"], pairs=st["market"]["pairs"], active=now_active,
                    market={k: st["market"][k] for k in ("logloss", "over_minus_fair", "shift", "slope")},
                    evidence={n: d["z"] for n, d in learners.items()}, gain={n: d["gain"] for n, d in learners.items()}))
    return dict(status="updated", through=st["through"], pairs=st["market"]["pairs"], active=now_active)


if __name__ == "__main__":      # python -m nbapicks.learn: refit now and print the report
    from . import config as C
    from .pipeline import Ctx
    c = Ctx(dt.datetime.now(dt.timezone.utc), C.load())
    print(json.dumps(run(c, force=True)))
    print(open(os.path.join("reports", REPORT)).read())
