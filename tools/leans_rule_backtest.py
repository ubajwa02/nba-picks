"""Before/after backtest of the daily lean rule on stored candidates (research only, no network).

    python -m tools.leans_rule_backtest [--from 2026-10-22] [--to 2026-11-15] [--detail 2026-11-08:2026-11-14]

For each slate it takes the prop candidates written that UTC day up to 22:30Z (the posting window),
runs `leans.pick_leans` under the OLD rule (min_decimal 1.5, no edge floor, most likely first) and the
NEW rule from config/nbapicks.yaml, and grades both from the stored box scores at the quoted price.
Slates with no stored candidates are skipped (say so in the report): the result is a replay of the
rule on what the pipeline had in its ledger, not a promise about future results.
"""
from __future__ import annotations

import argparse
import copy
import glob
import json
import os
from collections import defaultdict

from nbapicks import leans as LN
from nbapicks.config import load as load_config

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OLD = dict(min_decimal=1.5, min_edge=0.0, rank="prob")


def _jl(path):
    with open(path) as fh:
        for line in fh:
            if line.strip():
                yield json.loads(line)


def _dec(a):
    return 1 + a / 100 if a > 0 else 1 + 100 / -a


def grade(lean, box):
    g = box.get((lean["game_id"], lean["player_id"]))
    if not g or not g.get("played"):
        return "void", 0.0
    act = g.get(lean["stat"])
    if act is None or act == lean["line"]:
        return "push", 0.0
    won = (act > lean["line"]) == (lean["selection"] == "over")
    return ("win", _dec(lean["price_american"]) - 1) if won else ("loss", -1.0)


def slates(preds_dir, lo, hi):
    by = defaultdict(list)
    for f in sorted(glob.glob(os.path.join(preds_dir, "*.jsonl"))):
        for p in _jl(f):
            if p.get("market") != "prop" or p.get("prob") is None:
                continue
            day, t = p["created_at"][:10], p["created_at"][11:19]
            if lo <= day <= hi and t <= "22:30:00":
                by[day].append(p)
    return by


def run(lo, hi, detail=None):
    cfg_new = load_config(os.path.join(ROOT, "config", "nbapicks.yaml"))
    cfg_old = copy.deepcopy(cfg_new)
    cfg_old["leans"].update(OLD)
    box = {(r["game_id"], r["player_id"]): r for r in _jl(os.path.join(ROOT, "data/ledger/player_games.jsonl"))}
    posted = defaultdict(list)
    for r in _jl(os.path.join(ROOT, "data/ledger/posted_leans.jsonl")):
        if r["market"] == "prop":
            posted[r["slate"]].append(r)
    by = slates(os.path.join(ROOT, "data/ledger/predictions"), lo, hi)
    tot = {"old": [0, 0, 0.0], "new": [0, 0, 0.0], "posted": [0, 0, 0.0]}
    lines = []
    for day in sorted(set(by) | {d for d in posted if lo <= d <= hi}):
        row = {}
        picks = {}
        if day in by:
            picks["old"] = LN.pick_leans(by[day], cfg_old, day, "9999")
            picks["new"] = LN.pick_leans(by[day], cfg_new, day, "9999")
        picks["posted"] = posted.get(day, [])
        out = []
        for k in ("old", "new", "posted"):
            if k not in picks:
                out.append(f"{k}: no stored candidates")
                continue
            w = l = 0
            u = 0.0
            for lean in picks[k]:
                res, net = grade(lean, box)
                w += res == "win"
                l += res == "loss"
                u += net
            tot[k][0] += w
            tot[k][1] += l
            tot[k][2] += u
            out.append(f"{k}: {w}-{l} {u:+.2f}u")
        lines.append(f"{day}  " + " | ".join(out))
        if detail and detail[0] <= day <= detail[1] and "new" in picks:
            for k in ("old", "new"):
                for lean in picks[k]:
                    res, net = grade(lean, box)
                    lines.append(f"      {k:3} {lean['label']:38} {lean['price_american']:>5} p={lean['prob']:.3f} {res} {net:+.2f}")
    lines.append("TOTAL " + " | ".join(f"{k}: {v[0]}-{v[1]} {v[2]:+.2f}u" for k, v in tot.items()))
    return "\n".join(lines)


def posted_filter(lo, hi):
    """Which already-posted leans the NEW floor (price cap + edge) would have dropped. Used for slates whose
    candidates are not stored (the new EV ranking cannot be replayed there; this can only remove picks)."""
    cfg = load_config(os.path.join(ROOT, "config", "nbapicks.yaml"))["leans"]
    box = {(r["game_id"], r["player_id"]): r for r in _jl(os.path.join(ROOT, "data/ledger/player_games.jsonl"))}
    out, kept, dropped = [], [0, 0, 0.0], [0, 0, 0.0]
    for r in _jl(os.path.join(ROOT, "data/ledger/posted_leans.jsonl")):
        if r["market"] != "prop" or not (lo <= r["slate"] <= hi):
            continue
        dec = _dec(r["price_american"])
        keep = dec >= cfg["min_decimal"] and r["prob"] - 1 / dec >= cfg["min_edge"]
        res, net = grade(r, box)
        t = kept if keep else dropped
        t[0] += res == "win"
        t[1] += res == "loss"
        t[2] += net
        if not keep:
            out.append(f"  dropped {r['slate']} {r['label']:38} {r['price_american']:>5} p={r['prob']:.3f} edge={r['prob'] - 1 / dec:+.3f} {res} {net:+.2f}")
    out.append(f"POSTED {lo}..{hi}: kept {kept[0]}-{kept[1]} {kept[2]:+.2f}u | dropped {dropped[0]}-{dropped[1]} {dropped[2]:+.2f}u")
    return "\n".join(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="lo", default="2026-10-22")
    ap.add_argument("--to", dest="hi", default="2026-11-15")
    ap.add_argument("--detail", default="")
    a = ap.parse_args()
    d = tuple(a.detail.split(":")) if a.detail else None
    print(run(a.lo, a.hi, d))
    print()
    print(posted_filter(a.lo, a.hi))
