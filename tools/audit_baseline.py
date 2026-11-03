"""Independent re-grade of the posted record and the live prop population (read-only audit).

    python tools/audit_baseline.py            # prints the tables in docs/BASELINE_2026-11-01.md

Reads only data/ledger/*.jsonl and data/state/runs.jsonl. It does not import the settlement or
dashboard code on purpose: results are recomputed from the raw games and box-score ledgers with
the house rules written out below, so a bug in nbapicks.settle or nbapicks.dashboard cannot hide
here. Nothing is written.

Definitions
- Settled = win, loss or push. Voids (player did not play, game postponed) are excluded.
- ROI = net units / units staked on settled bets (pushes count as staked, return 0).
- Price = the price stored on the posted lean (american). For leans with price_basis
  'conservative' this is the worse of the two unlabelled DraftKings prices (a lower bound).
- 'Lean-rule pool' = every clean props-v1 prediction (latest version before tip, best price per
  side) with model p >= 0.60, decimal >= 1.50 and >= 5 recent games: the population the daily
  rule draws from. It is wider than what was posted (max 6 a day, 1 per player, 2 per game).
"""
from __future__ import annotations

import collections
import datetime as dt
import json
import math
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
LEDGER = os.path.join(ROOT, "ledger")
JUNK = ("milestone", "side_unverified")


def _rows(path):
    return [json.loads(x) for x in open(path) if x.strip()] if os.path.exists(path) else []


def _t(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def _dec(a):
    return 1 + a / 100 if a > 0 else 1 + 100 / abs(a)


def load():
    games = {}
    for g in _rows(os.path.join(LEDGER, "games.jsonl")):
        if g["game_id"] not in games or g["observed_at"] >= games[g["game_id"]]["observed_at"]:
            games[g["game_id"]] = g
    box = {}
    for b in _rows(os.path.join(LEDGER, "player_games.jsonl")):
        k = (b["game_id"], str(b["player_id"]))
        if k not in box or b["observed_at"] >= box[k]["observed_at"]:
            box[k] = b
    preds = []
    pdir = os.path.join(LEDGER, "predictions")
    for f in sorted(os.listdir(pdir)) if os.path.isdir(pdir) else []:
        preds += _rows(os.path.join(pdir, f))
    return games, box, preds


def grade(l, games, box):
    """win/loss/push/void/pending for one leg, from the raw ledgers."""
    g = games.get(l["game_id"])
    if not g:
        return "pending"
    st = (g.get("status") or "").lower()
    if st in ("postponed", "cancelled", "canceled", "suspended_void"):
        return "void"
    if st != "final":
        return "pending"
    if l["market"] == "prop":
        b = box.get((l["game_id"], str(l["player_id"])))
        if b is None:
            return "void" if any(k[0] == l["game_id"] for k in box) else "pending"
        if not b["played"]:
            return "void"
        v = b.get(l["stat"])
        if v is None:
            return "pending"
        return "push" if v == l["line"] else "win" if (v > l["line"]) == (l["selection"] == "over") else "loss"
    m = g["home_score"] - g["away_score"]
    if l["market"] == "ml":
        return "win" if (m > 0) == (l["selection"] == "home") else "loss"
    if l["market"] == "spread":
        a = (m if l["selection"] == "home" else -m) + l["line"]
        return "win" if a > 0 else "loss" if a < 0 else "push"
    tot = g["home_score"] + g["away_score"]
    return "push" if tot == l["line"] else "win" if (tot > l["line"]) == (l["selection"] == "over") else "loss"


def net(result, dec, stake=1.0):
    return stake * (dec - 1) if result == "win" else -stake if result == "loss" else 0.0


def summary(rows, name, w=30):
    s = [r for r in rows if r["result"] in ("win", "loss", "push")]
    n = len(s)
    c = collections.Counter(r["result"] for r in rows)
    if not n:
        return f"| {name} | 0 | - | - | - | - | - | - |"
    u = sum(r["net"] for r in s)
    staked = sum(r.get("stake", 1.0) for r in s)
    m = u / staked
    sd = math.sqrt(sum((r["net"] - m) ** 2 for r in s) / max(1, n - 1))
    hit = c["win"] / max(1, c["win"] + c["loss"])
    pred = sum(r["prob"] for r in s) / n
    imp = sum(1 / r["dec"] for r in s) / n
    return (f"| {name} | {n} | {c['win']}-{c['loss']}-{c['push']} (void {c['void']}, pending {c['pending']}) | {hit:.1%} | "
            f"{pred:.1%} / {imp:.1%} | {u:+.2f} | {m:+.1%} | ±{1.96 * sd / math.sqrt(n):.1%} |")


HDR = ("| group | settled | W-L-P | hit | model p / implied | net units | ROI | 95% half-width |\n"
       "|---|---|---|---|---|---|---|---|")


def posted(games, box, preds):
    leans = _rows(os.path.join(LEDGER, "posted_leans.jsonl"))
    runs = _rows(os.path.join(ROOT, "state", "runs.jsonl"))
    post_at = {}
    for r in runs:
        res = ((r.get("steps") or {}).get("leans") or {}).get("result") or {}
        if isinstance(res, dict) and res.get("posted"):
            post_at[r["steps"]["predict"]["result"]["slate"]] = r["at"]
    props = [p for p in preds if p.get("market") == "prop"]
    out = []
    for l in leans:
        l = dict(l, stake=l.get("stake", 1.0))
        d = _dec(l["price_american"])
        r = grade(l, games, box)
        row = dict(l, result=r, dec=d, net=net(r, d, l["stake"]), ev_at_post=None, decision=None, basis=None,
                   quote_age=None, injury=None)
        at = post_at.get(l["slate"])
        if l.get("source") == "props_v1" and at:
            m = [p for p in props if p["created_at"] <= at and p["game_id"] == l["game_id"]
                 and str(p.get("player_id")) == str(l["player_id"]) and p.get("stat") == l["stat"]
                 and p.get("line") == l["line"] and p["selection"] == l["selection"]
                 and abs(p["price_dec"] - d) < 0.005 and abs(p["prob"] - l["prob"]) < 0.0005]
            if m:
                p = max(m, key=lambda p: p["created_at"])
                ex = (p.get("inputs") or {}).get("explain") or {}
                row.update(ev_at_post=p.get("ev"), decision=p.get("decision"), basis=(p.get("inputs") or {}).get("price_basis"),
                           quote_age=(_t(at) - _t(p["price_observed_at"])).total_seconds() / 60 if p.get("price_observed_at") else None,
                           injury=ex.get("injury_status"))
        out.append(row)
    return out


def pool(games, box, preds):
    """Lean-rule pool: latest pre-tip version per (game, player, stat, line, side, book), best book per side."""
    last = {}
    for p in preds:
        if p.get("market") != "prop" or p.get("category") != "straight" or p.get("prob") is None or not p.get("price_dec"):
            continue
        g = games.get(p["game_id"])
        if g and g.get("start_utc") and _t(p["created_at"]) > _t(g["start_utc"]):
            continue
        k = (p["game_id"], str(p.get("player_id")), p.get("stat"), p.get("line"), p["selection"], p["book"])
        if k not in last or p["created_at"] > last[k]["created_at"]:
            last[k] = p
    best = {}
    for p in last.values():
        inp = p.get("inputs") or {}
        ex = inp.get("explain") or {}
        flags = list(ex.get("flags") or []) + list(inp.get("quality_flags") or [])
        if any(j in f for f in flags for j in JUNK):
            continue
        if p["prob"] < 0.60 or p["price_dec"] < 1.50 or ((ex.get("line_hits_last10") or {}).get("n") or 0) < 5:
            continue
        k = (p["game_id"], str(p.get("player_id")), p.get("stat"), p.get("line"), p["selection"])
        if k not in best or p["price_dec"] > best[k]["price_dec"]:
            best[k] = p
    out = []
    for p in best.values():
        leg = dict(market="prop", game_id=p["game_id"], player_id=p.get("player_id"), stat=p["stat"], line=p["line"],
                   selection=p["selection"])
        r = grade(leg, games, box)
        out.append(dict(leg, result=r, prob=p["prob"], dec=p["price_dec"], net=net(r, p["price_dec"]),
                        ev=p["prob"] * p["price_dec"] - 1))
    return out


def main():
    games, box, preds = load()
    P = posted(games, box, preds)
    print("## Posted leans (1u each, graded from raw ledgers)\n")
    print(HDR)
    print(summary(P, "all posted leans"))
    for src in ("model_lean", "split_card", "props_v1"):
        print(summary([r for r in P if r.get("source") == src], f"source {src}"))
    V = [r for r in P if r.get("source") == "props_v1"]
    for st in ("pts", "reb", "ast", "fg3m"):
        print(summary([r for r in V if r["stat"] == st], f"props_v1 {st}"))
    for se in ("over", "under"):
        print(summary([r for r in V if r["selection"] == se], f"props_v1 {se}"))
    for lo, hi, n in ((1.0, 1.6, "< 1.60"), (1.6, 1.8, "1.60-1.79"), (1.8, 99, ">= 1.80")):
        print(summary([r for r in V if lo <= r["dec"] < hi], f"props_v1 decimal {n}"))
    print(summary([r for r in V if (r["ev_at_post"] or -1) >= 0.05], "props_v1 EV >= 5% at post"))
    print(summary([r for r in V if (r["ev_at_post"] if r["ev_at_post"] is not None else -1) < 0.05], "props_v1 EV < 5% at post"))
    for b in ("labelled", "conservative"):
        print(summary([r for r in V if r["basis"] == b], f"props_v1 price {b}"))
    ev = [r["ev_at_post"] for r in V if r["ev_at_post"] is not None]
    dc = collections.Counter(r["decision"] for r in V)
    print(f"\nprops_v1 leans: {len(V)}; own qualification decision at posting {dict(dc)}; "
          f"EV at post >= 5%: {sum(e >= 0.05 for e in ev)}, < 0: {sum(e < 0 for e in ev)}, mean {sum(ev) / max(1, len(ev)):+.1%}")
    print("quote older than 120 min at posting:", [(r["slate"], r["label"], round(r["quote_age"])) for r in V if (r["quote_age"] or 0) > 120])
    print("player listed with an injury status at posting:", [(r["slate"], r["label"], r["injury"], r["result"]) for r in V if r["injury"]])

    T = _rows(os.path.join(LEDGER, "posted_tickets.jsonl"))
    by_id = {l["lean_id"]: l for l in _rows(os.path.join(LEDGER, "posted_leans.jsonl"))}
    print("\n## Parlays and lotto (as recorded stake, and restated at 1u)\n")
    agg = collections.defaultdict(lambda: collections.Counter())
    for t in T:
        legs = [dict(by_id.get(l["lean_id"], {}), **l) if "market" not in l else l for l in t["legs"]]
        rs = [grade(l, games, box) for l in legs]
        eff = math.prod(_dec(l["price_american"]) for l, r in zip(legs, rs) if r == "win")
        res = "loss" if "loss" in rs else "pending" if "pending" in rs else "push" if all(r in ("push", "void") for r in rs) else "win"
        a = agg[t["kind"]]
        a[res] += 1
        if res in ("win", "loss", "push"):
            a["staked_rec"] += t["stake"]
            a["net_rec"] += net(res, eff, t["stake"])
            a["net_1u"] += net(res, eff, 1.0)
            a["n"] += 1
            a["ev_sum"] += t["ev"]
    for k, a in agg.items():
        print(f"- {k}: {a['n']} settled, {a['win']}-{a['loss']}-{a['push']}, pending {a['pending']}; "
              f"recorded stake {a['net_rec']:+.2f}u on {a['staked_rec']:g}u; restated 1u {a['net_1u']:+.2f}u on {a['n']}u "
              f"(ROI {a['net_1u'] / max(1, a['n']):+.1%}); mean model EV {a['ev_sum'] / max(1, a['n']):+.1%}")

    Q = pool(games, box, preds)
    print("\n## Lean-rule pool: every clean props-v1 side the rule could pick (calibration evidence)\n")
    print(HDR)
    print(summary(Q, "pool"))
    for lo, hi in ((0.60, 0.65), (0.65, 0.70), (0.70, 0.80), (0.80, 1.01)):
        print(summary([r for r in Q if lo <= r["prob"] < hi], f"model p {lo:.2f}-{hi:.2f}"))
    for lo, hi, n in ((-9, 0, "EV < 0"), (0, 0.05, "EV 0-5%"), (0.05, 0.15, "EV 5-15%"), (0.15, 9, "EV >= 15%")):
        print(summary([r for r in Q if lo <= r["ev"] < hi], n))
    for st in ("pts", "reb", "ast", "fg3m"):
        print(summary([r for r in Q if r["stat"] == st], st))
    for se in ("over", "under"):
        print(summary([r for r in Q if r["selection"] == se], se))
    return 0


if __name__ == "__main__":
    sys.exit(main())
