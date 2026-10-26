"""Pick review: for each graded posted lean, line up what we knew before the game (model prob vs
book implied, EV, split-card splits and sample sizes, rest/injury notes, closing-line movement)
against the result, then group by those inputs to look for patterns.

Descriptive only. The sample is tiny; nothing here is evidence of an edge, and it never feeds
gates or thresholds. Split cards are archived in data/ledger/split_cards.jsonl because
data/state/split_cards_latest.json only holds today's.
"""
from __future__ import annotations

import json
import os
from collections import defaultdict

from .odds import american_to_decimal

ARCHIVE = "split_cards.jsonl"
SMALL_N = 10  # a split with fewer games than this is "small sample"


def _card_key(c: dict) -> tuple:
    return (str(c.get("game_id")), str(c.get("player_id")), c.get("stat"), c.get("side"), float(c.get("line") or 0))


def archive_cards(root: str, cards: list[dict]) -> int:
    """Append today's split cards once each (keyed by game/player/stat/side/line)."""
    p = os.path.join(root, "ledger", ARCHIVE)
    seen = {_card_key(json.loads(x)) for x in open(p) if x.strip()} if os.path.exists(p) else set()
    new = [c for c in cards if _card_key(c) not in seen and not seen.add(_card_key(c))]
    if new:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "a") as fh:
            for c in new:
                fh.write(json.dumps({k: v for k, v in c.items() if k != "text"}, sort_keys=True) + "\n")
    return len(new)


def load_cards(root: str) -> dict:
    p = os.path.join(root, "ledger", ARCHIVE)
    return {_card_key(c): c for c in (json.loads(x) for x in open(p) if x.strip())} if os.path.exists(p) else {}


def closing_implied(odds: list[dict], lean: dict, start_utc: str | None) -> float | None:
    """Mean implied prob of the last pre-start quote per book for the lean's exact side and line."""
    if not start_utc:
        return None
    last = {}
    for o in odds:
        if (o.get("game_id") != lean["game_id"] or o.get("market") != lean["market"]
                or o.get("selection") != lean["selection"] or o["observed_at"] >= start_utc.replace("Z", ":00Z")[:20]
                or not o.get("price_dec")):
            continue
        if lean["market"] == "prop" and (o.get("stat") != lean.get("stat") or o.get("player_name") != lean.get("player_name")):
            continue
        if lean.get("line") is not None and o.get("line") != lean["line"]:
            continue
        if lean["market"] == "ml" and o.get("line") is not None:
            continue
        b = o.get("book")
        if b not in last or o["observed_at"] > last[b]["observed_at"]:
            last[b] = o
    if not last:
        return None
    return sum(1 / o["price_dec"] for o in last.values()) / len(last)


def _pred_for(preds: list[dict], l: dict) -> dict | None:
    m = [p for p in preds if p["game_id"] == l["game_id"] and p["market"] == l["market"]
         and p["selection"] == l["selection"] and p.get("line") == l.get("line")
         and str(p.get("player_id")) == str(l.get("player_id")) and p.get("stat") == l.get("stat")]
    return max(m, key=lambda p: p["created_at"]) if m else None


def enrich(graded: list[dict], preds: list[dict], games: dict, odds: list[dict], cards: dict) -> list[dict]:
    out = []
    for l in graded:
        if l.get("result") not in ("win", "loss", "push"):
            continue
        implied = 1 / american_to_decimal(l["price_american"])
        r = dict(slate=l["slate"], label=l["label"], market=l["market"], stat=l.get("stat"), source=l.get("source"),
                 result=l["result"], net=l.get("net_units") or 0.0, prob=l.get("prob"), implied=round(implied, 4),
                 gap=round((l.get("prob") or 0) - implied, 4), price_american=l["price_american"])
        r["ev"] = round(l["prob"] * american_to_decimal(l["price_american"]) - 1, 4) if l.get("prob") is not None else None
        p = _pred_for(preds, l)
        if p:
            inp = p.get("inputs") or {}
            inp = json.loads(inp) if isinstance(inp, str) else inp
            r["rest"] = [inp.get("away_rest"), inp.get("home_rest")] if "home_rest" in inp else None
            r["injury_flag"] = "injury" in (p.get("reason") or "")
            l = dict(l, player_name=p.get("player_name"))
        c = cards.get((str(l["game_id"]), str(l.get("player_id")), l.get("stat"), l["selection"], float(l.get("line") or 0)))
        if c:
            l = dict(l, player_name=l.get("player_name") or c.get("player"))
            sp = {s["split"]: s for s in c.get("splits") or []}
            r["splits"] = {k: f"{v['hits']}/{v['n']}" for k, v in sp.items()}
            r["season_n"] = (sp.get("season") or {}).get("n")
            # opening week: no or tiny current-season split, so the card leans on career/past seasons
            r["small_sample"] = (sp.get("season") or {}).get("n", 0) < SMALL_N
            r["prob_raw"] = c.get("prob_raw")
        ci = closing_implied(odds, l, (games.get(l["game_id"]) or {}).get("start_utc"))
        r["close_implied"] = round(ci, 4) if ci is not None else None
        r["clv"] = round(ci - implied, 4) if ci is not None else None  # >0: market moved toward our side
        out.append(r)
    return out


def _grp(rows, key):
    g = defaultdict(list)
    for r in rows:
        k = key(r)
        if k is not None:
            g[k].append(r)
    return {k: dict(n=len(v), wins=sum(r["result"] == "win" for r in v), losses=sum(r["result"] == "loss" for r in v),
                    units=round(sum(r["net"] for r in v), 3)) for k, v in sorted(g.items())}


def _ev_b(ev):
    return None if ev is None else "EV<10%" if ev < 0.10 else "EV 10-25%" if ev < 0.25 else "EV>=25%"


def _gap_b(g):
    return "gap<5pts" if g < 0.05 else "gap 5-15pts" if g < 0.15 else "gap>=15pts"


def _clv_b(r):
    c = r.get("clv")
    return None if c is None else "moved toward us" if c > 0.005 else "moved away" if c < -0.005 else "flat"


def build(rows: list[dict], scorecard: dict | None = None) -> dict:
    groups = dict(by_market=_grp(rows, lambda r: r["market"]), by_stat=_grp(rows, lambda r: r.get("stat")),
                  by_ev=_grp(rows, lambda r: _ev_b(r["ev"])), by_gap=_grp(rows, lambda r: _gap_b(r["gap"])),
                  by_clv=_grp(rows, _clv_b),
                  by_sample=_grp([r for r in rows if r["market"] == "prop" and "splits" in r],
                                 lambda r: "small-sample splits" if r.get("small_sample") else "fuller splits"))
    sc = scorecard or {}
    wider = dict(n=sc.get("n"), brier=sc.get("brier"), by_ev=sc.get("by_ev"), by_decision=sc.get("by_decision"))
    rev_f = findings(rows, groups)
    b = wider.get("brier") or {}
    if b.get("n"):
        rev_f.append(f"Wider settled predictions (n={b['n']}): model Brier {b['model']} vs book {b['market']} (lower is better).")
    return dict(n=len(rows), note="Descriptive only: tiny sample (one or two slates), no inference. "
                "Implied = 1/price incl. vig. CLV = closing implied minus our implied (positive = line moved our way).",
                groups=groups, rows=sorted(rows, key=lambda r: (r["slate"], r["label"]), reverse=True),
                findings=rev_f, wider=wider)


def findings(rows: list[dict], g: dict) -> list[str]:
    if not rows:
        return []
    f = []
    w = sum(r["result"] == "win" for r in rows); lo = sum(r["result"] == "loss" for r in rows)
    f.append(f"{w}-{lo} on {len(rows)} graded posted picks, {sum(r['net'] for r in rows):+.2f}u. Far too few to judge.")
    for name, d in (("market", g["by_market"]), ("model-vs-book gap", g["by_gap"]), ("closing-line move", g["by_clv"]),
                    ("prop split sample", g["by_sample"])):
        if len(d) > 1:
            f.append(f"By {name}: " + "; ".join(f"{k} {v['wins']}-{v['losses']} ({v['units']:+.2f}u)" for k, v in d.items()) + ".")
    return f


def markdown(rev: dict, today: str) -> str:
    out = [f"# Pick review (cumulative, as of {today})", "", rev["note"], ""]
    out += [f"- {x}" for x in rev["findings"]] + [""]
    for slate in sorted({r["slate"] for r in rev["rows"]}, reverse=True):
        out += [f"## {slate}", "", "| Pick | Result | Units | Prob | Implied | EV | CLV | Splits |", "|---|---|---|---|---|---|---|---|"]
        for r in [r for r in rev["rows"] if r["slate"] == slate]:
            sp = ", ".join(f"{k} {v}" for k, v in (r.get("splits") or {}).items() if k in ("season", "last10", "career"))
            ev = "" if r["ev"] is None else f"{r['ev']:+.2f}"
            clv = "" if r["clv"] is None else f"{r['clv']:+.3f}"
            out.append(f"| {r['label']} | {r['result']} | {(r['net'] or 0):+.2f} | {'n/a' if r.get('prob') is None else format(r['prob'], '.3f')} | {'n/a' if r.get('implied') is None else format(r['implied'], '.3f')} | {ev} | {clv} | {sp} |")
        out.append("")
    return "\n".join(out)
