"""Which DraftKings prop price is the Over: read it from the listing order, and keep checking it.

ESPN lists every DraftKings prop line as two prices and does not say which one is the Over.
Until 2026-11-17 a pair was labelled only where bet365 milestone prices could bracket it (about a
quarter of pairs); every other pair was recorded at the worse of its two prices with no fair
value, and when the bet365 feed stopped answering (2026-11-16) no pair was labelled at all.

Measured on 2026-11-17 (docs/SIDE_ORDER.md): the first price listed is the Over.
  - 24 of 24 pairs of one game equal the labelled DraftKings prices of a second feed, to the cent;
  - 2,297 of the 2,374 pairs the bet365 ladder could label agree (96.8%; the rest are near-even
    pairs, where the ladder cannot tell the sides apart);
  - results: "went over" rises with the first-listed side's fair chance at slope 1.05 (se 0.10) on
    8,155 graded closing pairs over 24 slates. A random order gives 0, a reversed order -1.

The order is a habit of a feed and not a contract, so it is used only while the evidence holds:

  results   after every settle the slope is measured again on the trailing 1, 3, 10 and 30 slates
            (`refresh`, data/state/side_order.json, reports/side_order.md). A window whose slope
            plus three standard errors is under 0.75 marks the order "failed". A slope three standard
            errors above zero on 300 or more pairs marks it "confirmed". Results older than 60 days
            do not count, so a new season starts "unconfirmed", and a "confirmed" that has not seen
            a graded slate for 14 days is not relied on (`status`).
  same run  before pricing, the model's P(over) is ranked against the first-listed fair chance over
            the slate's pairs (`run_check`). That rank correlation was 0.32 to 0.66 on every slate
            and above zero in all 164 games; a random order gives 0, a reversed one the negative.
  labelled  when a labelled feed answers and votes the other way for a game
            (props.verify_prop_sides), that game's pairs are not labelled at all.

A pair is labelled by order only with evidence for it (results confirmed, or a strong same-run
agreement) and none against it. Otherwise it falls back to the bet365 ladder or the conservative
price, exactly as before (nbapicks/propsides.py). `prop_sides.listing_order: off` in the config
turns the rule off.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import os
from collections import defaultdict
from zoneinfo import ZoneInfo

from . import odds as O
from . import propsides as PS
from .props import STATS
from .sources import espn

BOOKS = ("DraftKings",)                 # books whose ESPN listing order has been measured
STATE = "side_order.json"
REPORT = "side_order.md"
WINDOWS = (1, 3, 10, 30)                # trailing slates
MAX_AGE_DAYS = 60                       # older results say nothing about today's feed
STALE_DAYS = 14                         # a "confirmed" not refreshed by a graded slate for this long is not relied on
MIN_PAIRS, CONFIRM_PAIRS = 100, 300     # pairs a window needs to be judged / to confirm
FLOOR, FAIL_Z, CONFIRM_Z = 0.75, 3.0, 3.0
GAME_MIN_N, SLATE_MIN_N, STRONG_MIN_N = 12, 40, 100
SLATE_MIN_R, STRONG_R = 0.15, 0.25


def _t(s: str) -> dt.datetime:
    return dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))


# ---------------------------------------------------------------- closing pairs and results
def closing_pairs(store, tz: str, since: str | None = None, books=BOOKS) -> list[dict]:
    """The last two-way quote before tip for every player prop of a finished game, with the result.

    One row per (game, player, stat): the line that changed last before tip and both prices at
    it, in listing order. `over` is 1 or 0, or None when the player did not play, the box score
    is not in yet, or the stat landed exactly on the line. `since` is a slate date (inclusive).
    A quote is stored only when it changes, so a line that moved away and came back at the same
    prices is missed and the line in between is used; that pair was still on offer before tip.
    """
    zone = ZoneInfo(tz)
    games = {}
    for g in store.q("SELECT game_id, start_utc FROM games WHERE status = 'final'"):
        tip = _t(g["start_utc"])
        slate = tip.astimezone(zone).date().isoformat()
        if since is None or slate >= since:
            games[g["game_id"]] = (tip, slate)
    if not games:
        return []
    floor = (min(t for t, _ in games.values()) - dt.timedelta(days=4)).strftime("%Y-%m-%dT%H:%M:%SZ")
    last: dict[tuple, dict] = {}
    for r in store.q("SELECT game_id, player_id, player_name, stat, line, selection, price_dec, observed_at, book FROM odds "
                     "WHERE market = 'prop' AND kind = 'current' AND source = 'espn' AND selection IN ('side0', 'side1') "
                     "AND observed_at >= ? ORDER BY observed_at", [floor]):
        g = games.get(r["game_id"])
        if not g or not r["player_id"] or r["line"] is None or not r["price_dec"] or espn.canon_book(r["book"]) not in books:
            continue
        if _t(r["observed_at"]) >= g[0]:
            continue                                    # quoted after tip: not a pre-game price
        d = last.setdefault((r["game_id"], str(r["player_id"]), r["stat"]), dict(name=None, line=None, at=None, prices={}))
        d["line"], d["at"], d["name"] = r["line"], r["observed_at"], r["player_name"] or d["name"]
        d["prices"][(r["line"], r["selection"])] = r["price_dec"]
    box = {(b["game_id"], str(b["player_id"])): b
           for b in store.q("SELECT game_id, player_id, played, pts, reb, ast, fg3m FROM player_games")}
    have_box = {k[0] for k in box}
    out = []
    for (gid, pid, stat), d in last.items():
        a, b = d["prices"].get((d["line"], "side0")), d["prices"].get((d["line"], "side1"))
        if stat not in STATS or a is None or b is None or not PS.plausible_pair(a, b):
            continue
        row = box.get((gid, pid))
        played = bool(row["played"]) if row else (False if gid in have_box else None)
        value = row.get(stat) if row and played else None
        over = None if value is None or value == d["line"] else int(value > d["line"])
        out.append(dict(slate=games[gid][1], game_id=gid, player_id=pid, player_name=d["name"], stat=stat, line=d["line"],
                        price_first=a, price_second=b, p_first=O.devig_multiplicative([a, b])[0], at=d["at"],
                        played=played, value=value, over=over))
    out.sort(key=lambda r: (r["slate"], r["game_id"], r["player_id"], r["stat"]))
    return out


def slope(rows: list[dict]) -> tuple[float, float, int] | None:
    """Least-squares slope of "went over" on the first-listed side's fair chance over graded pairs:
    (slope, standard error, pairs). 1 means the first price is the Over, 0 that the order carries
    no information, -1 that the first price is the Under. The standard error is the larger of the
    game-clustered one (a game's props move together) and the plain one."""
    pts = [(r["p_first"], r["over"], r["game_id"]) for r in rows if r.get("over") is not None]
    n = len(pts)
    if n < 3:
        return None
    mx, my = sum(p for p, _, _ in pts) / n, sum(y for _, y, _ in pts) / n
    sxx = sum((p - mx) ** 2 for p, _, _ in pts)
    if sxx <= 0:
        return None
    f = sum((p - mx) * (y - my) for p, y, _ in pts) / sxx
    score, sse = defaultdict(float), 0.0
    for p, y, g in pts:
        e = y - my - f * (p - mx)
        score[g] += (p - mx) * e
        sse += e * e
    k = len(score)
    se_cluster = math.sqrt(sum(s * s for s in score.values()) * k / max(k - 1, 1)) / sxx
    se_plain = math.sqrt(sse / max(n - 2, 1) / sxx)
    return f, max(se_cluster, se_plain), n


def measure(pairs: list[dict]) -> dict:
    """Results-based status of the listing order: "confirmed", "failed" or "unconfirmed"."""
    rows = [r for r in pairs if r.get("over") is not None]
    slates = sorted({r["slate"] for r in rows})
    windows, failed, widest = [], [], None
    for k in WINDOWS:
        take = slates[-k:]
        if not take or (windows and len(take) == windows[-1]["slates"]):
            continue                                    # no more history than the window before it
        res = slope([r for r in rows if r["slate"] >= take[0]])
        if res is None:
            continue
        f, se, n = res
        verdict = "thin" if n < MIN_PAIRS else "fail" if f + FAIL_Z * se < FLOOR else "ok"
        w = dict(slates=len(take), first=take[0], last=take[-1], pairs=n, slope=round(f, 3), se=round(se, 3), verdict=verdict)
        windows.append(w)
        if verdict == "fail":
            failed.append(w)
        if n >= CONFIRM_PAIRS:
            widest = w
    if failed:
        w = failed[0]
        status = "failed"
        why = (f"slope {w['slope']:+.2f} (se {w['se']:.2f}) on the last {w['slates']} slate(s), {w['pairs']:,} pairs: "
               f"the first-listed price no longer behaves like the Over")
    elif widest and widest["slope"] - CONFIRM_Z * widest["se"] > 0:
        status = "confirmed"
        why = f"slope {widest['slope']:+.2f} (se {widest['se']:.2f}) on {widest['pairs']:,} graded pairs over {widest['slates']} slates"
    else:
        status = "unconfirmed"
        why = "too few recent graded pairs to tell" if not widest else \
            f"slope {widest['slope']:+.2f} (se {widest['se']:.2f}) on {widest['pairs']:,} pairs is not clearly above zero"
    return dict(book=BOOKS[0], status=status, why=why, through=slates[-1] if slates else None, pairs=len(rows), windows=windows,
                rule=dict(windows=list(WINDOWS), max_age_days=MAX_AGE_DAYS, fail=f"slope + {FAIL_Z:g} se < {FLOOR:g} on >= {MIN_PAIRS} pairs",
                          confirm=f"slope - {CONFIRM_Z:g} se > 0 on >= {CONFIRM_PAIRS} pairs"))


# ---------------------------------------------------------------- same-run check
def _ranks(v: list[float]) -> list[float]:
    idx = sorted(range(len(v)), key=v.__getitem__)
    r, i = [0.0] * len(v), 0
    while i < len(idx):
        j = i
        while j + 1 < len(idx) and v[idx[j + 1]] == v[idx[i]]:
            j += 1
        for k in range(i, j + 1):
            r[idx[k]] = (i + j) / 2 + 1                 # ties share the average rank
        i = j + 1
    return r


def rank_corr(pairs: list[tuple[float, float]]) -> float | None:
    """Spearman rank correlation of (x, y) pairs; None when it is undefined."""
    n = len(pairs)
    if n < 3:
        return None
    a, b = _ranks([p[0] for p in pairs]), _ranks([p[1] for p in pairs])
    ma, mb = sum(a) / n, sum(b) / n
    saa, sbb = sum((x - ma) ** 2 for x in a), sum((y - mb) ** 2 for y in b)
    if saa <= 0 or sbb <= 0:
        return None
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / math.sqrt(saa * sbb)


def run_check(by_game: dict[str, list[tuple[float, float]]]) -> dict:
    """Does the model's P(over) move with the first-listed fair chance on this run?

    by_game: game_id -> [(fair chance of the first-listed side, model P(over))], one per pair that
    has a model estimate. Returns {"slate": {n, r, verdict}, "games": {game_id: {n, r, verdict}}}
    with verdict "thin" (too few pairs to say), "against", "agree" or, for the slate, "strong".
    """
    def one(pairs, min_n, against):
        n, r = len(pairs), rank_corr(pairs)
        if n < min_n or r is None:
            return dict(n=n, r=None if r is None else round(r, 3), verdict="thin")
        return dict(n=n, r=round(r, 3), verdict="against" if against(r) else "agree")
    games = {gid: one(p, GAME_MIN_N, lambda r: r <= 0) for gid, p in by_game.items()}
    slate = one([x for p in by_game.values() for x in p], SLATE_MIN_N, lambda r: r < SLATE_MIN_R)
    if slate["verdict"] == "agree" and slate["n"] >= STRONG_MIN_N and slate["r"] >= STRONG_R:
        slate["verdict"] = "strong"
    return dict(slate=slate, games=games)


def decide(mode: str, status: str | None, slate: dict) -> tuple[bool, str]:
    """(label by listing order on this run?, why). Needs evidence for the order and none against it."""
    if mode != "auto":
        return False, "listing order is off in the config (prop_sides.listing_order)"
    if status == "failed":
        return False, "results contradict the listing order (data/state/side_order.json)"
    if slate["verdict"] == "against":
        return False, f"the model and the first-listed prices disagree on this run (rank correlation {slate['r']:+.2f} on {slate['n']} pairs)"
    if status == "confirmed":
        return True, "confirmed by results"
    if slate["verdict"] == "strong":
        return True, f"not yet confirmed by results; strong agreement on this run (rank correlation {slate['r']:+.2f} on {slate['n']} pairs)"
    return False, "not yet confirmed by results, and too little agreement on this run to rely on"


# ---------------------------------------------------------------- state and report
def load(root: str) -> dict:
    try:
        with open(os.path.join(root, "state", STATE)) as fh:
            return json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def status(state: dict, today: dt.date) -> str | None:
    """The stored results status, unless it has gone stale. A "confirmed" whose last graded slate is
    more than STALE_DAYS old (settle stopped running, or a long break) says nothing about today's
    feed and reads as "unconfirmed". "failed" stays until a refresh clears it."""
    st, through = state.get("status"), state.get("through")
    if st == "confirmed" and (not through or (today - dt.date.fromisoformat(through)).days > STALE_DAYS):
        return "unconfirmed"
    return st


def _by_week(rows: list[dict]) -> list[dict]:
    weeks = defaultdict(list)
    for r in rows:
        weeks[dt.date.fromisoformat(r["slate"]).strftime("%G-W%V")].append(r)
    out = []
    for wk in sorted(weeks):
        res = slope(weeks[wk])
        if res:
            out.append(dict(week=wk, slates=len({r["slate"] for r in weeks[wk]}), pairs=res[2], slope=round(res[0], 2), se=round(res[1], 2)))
    return out


def report_md(state: dict, weeks: list[dict]) -> str:
    L = ["# DraftKings prop sides: is the first price listed the Over?", "",
         "Written by `nbapicks/sideorder.py` after every settle. How the rule works and what it replaced: `docs/SIDE_ORDER.md`.", "",
         f"**Status: {state['status']}** through {state['through'] or 'no graded slate yet'} ({state['why']}).", "",
         "The slope is how fast \"went over\" rises with the first-listed side's fair chance on graded closing pairs. "
         "1 means the first price is the Over, 0 means the order says nothing, -1 means it is the Under.", "",
         "| last slates | from | to | pairs | slope | se | verdict |", "|---|---|---|---|---|---|---|"]
    L += [f"| {w['slates']} | {w['first']} | {w['last']} | {w['pairs']:,} | {w['slope']:+.2f} | {w['se']:.2f} | {w['verdict']} |"
          for w in state["windows"]]
    L += ["", f"Fail: {state['rule']['fail']}. Confirm: {state['rule']['confirm']}. "
              f"Only the last {state['rule']['max_age_days']} days of results count.", "",
          "## By week", "", "| week | slates | pairs | slope | se |", "|---|---|---|---|---|"]
    L += [f"| {w['week']} | {w['slates']} | {w['pairs']:,} | {w['slope']:+.2f} | {w['se']:.2f} |" for w in weeks]
    if state.get("changes"):
        L += ["", "## Status changes", ""] + [f"- {c['at']}: {c['from']} -> {c['to']} ({c['why']})" for c in state["changes"]]
    return "\n".join(L) + "\n"


def refresh(ctx) -> dict:
    """Measure the order on results again and store it. Run by `settle`; writes only when it changed."""
    since = (ctx.today - dt.timedelta(days=MAX_AGE_DAYS)).isoformat()
    pairs = closing_pairs(ctx.store, ctx.tz, since)
    new = measure(pairs)
    old = load(ctx.root)
    changes = list(old.get("changes") or [])
    if old.get("status") and old["status"] != new["status"]:
        at = ctx.now.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        changes.append({"at": at, "from": old["status"], "to": new["status"], "why": new["why"]})
        ctx.notes.append(f"prop side order: {old['status']} -> {new['status']} ({new['why']})")
    new["changes"] = changes[-20:]
    if new != old:
        path = os.path.join(ctx.root, "state", STATE)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path + ".tmp", "w") as fh:
            json.dump(new, fh, indent=1, sort_keys=True)
        os.replace(path + ".tmp", path)
        rep = os.path.join(os.path.dirname(os.path.abspath(ctx.root)), "reports")
        os.makedirs(rep, exist_ok=True)
        with open(os.path.join(rep, REPORT), "w") as fh:
            fh.write(report_md(new, _by_week([r for r in pairs if r["over"] is not None])))
    return dict(status=new["status"], through=new["through"], pairs=new["pairs"])


if __name__ == "__main__":      # python -m nbapicks.sideorder: measure now and print the report
    from . import config as C
    from .pipeline import Ctx
    c = Ctx(dt.datetime.now(dt.timezone.utc), C.load())
    print(json.dumps(refresh(c)))
    print(open(os.path.join("reports", REPORT)).read())
