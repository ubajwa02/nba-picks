"""Evidence for reports/red_week_2026-11.md: how the prop model's win chances held up on every graded
prop prediction in the ledger, and how the posted picks did. Read-only; forward data only (the props
holdout 2026-02-01..2026-06-30 is not touched).

    python -m tools.red_week_analysis
"""
from __future__ import annotations

import collections
import json
import math
import os
from math import comb

from nbapicks import leans as LN
from nbapicks import track
from nbapicks.settle import GameResult, settle_leg

ROOT = "data"


def _jsonl(path):
    return [json.loads(x) for x in open(path) if x.strip()] if os.path.exists(path) else []


def graded_predictions(root: str = ROOT) -> list[dict]:
    """One row per (game, player, stat, line, side, book): the latest pre-tip prediction, graded from the box."""
    games = {g["game_id"]: g for g in _jsonl(f"{root}/ledger/games.jsonl")}
    box = {(b["game_id"], str(b["player_id"])): b for b in _jsonl(f"{root}/ledger/player_games.jsonl")}
    best: dict = {}
    d = f"{root}/ledger/predictions"
    for f in sorted(os.listdir(d)):
        for line in open(os.path.join(d, f)):
            if '"prop"' not in line:
                continue
            p = json.loads(line)
            if p.get("market") != "prop" or p.get("category") != "straight" or p.get("selection") not in ("over", "under"):
                continue
            g = games.get(p["game_id"])
            if not g or p["created_at"] >= g["start_utc"] or p.get("prob") is None or not p.get("price_dec"):
                continue
            k = (p["game_id"], str(p["player_id"]), p["stat"], p["line"], p["selection"], p["book"])
            if k not in best or p["created_at"] > best[k]["created_at"]:
                best[k] = p
    out = []
    for p in best.values():
        g = games[p["game_id"]]
        b = box.get((p["game_id"], str(p["player_id"])))
        if g["status"] != "final" or not b or not b["played"]:
            continue
        r = settle_leg("prop", p["selection"], p["line"], GameResult(g["status"], g.get("home_score"), g.get("away_score")), b.get(p["stat"]), True)
        if r not in ("win", "loss"):
            continue
        i = p["inputs"] if isinstance(p.get("inputs"), dict) else json.loads(p.get("inputs") or "{}")
        ex = i.get("explain") or {}
        out.append(dict(mv=p.get("model_version"), book=p["book"], prob=p["prob"], dec=p["price_dec"], win=int(r == "win"),
                        basis=i.get("price_basis"), fair=i.get("fair"), sel=p["selection"], day=g["start_utc"][:10],
                        l10=(ex.get("line_hits_last10") or {}).get("n") or 0,
                        flags=list(ex.get("flags") or []) + list(i.get("quality_flags") or [])))
    return out


def old_rule(r: dict) -> bool:
    """The pick rule in force until 2026-11-17: model win chance >= 60%, price >= 1.50, 5+ recent games."""
    return r["prob"] >= 0.6 and r["dec"] >= 1.5 and r["l10"] >= 5 and not any(k in f for f in r["flags"] for k in ("milestone", "side_unverified"))


def _row(name, x):
    n = len(x)
    if not n:
        return f"| {name} | 0 | | | | |"
    m, h = sum(r["prob"] for r in x) / n, sum(r["win"] for r in x) / n
    be, roi = sum(1 / r["dec"] for r in x) / n, sum(r["win"] * r["dec"] - 1 for r in x) / n
    return f"| {name} | {n} | {m:.1%} | {h:.1%} | {be:.1%} | {roi:+.1%} |"


def _cdf(k, n, p):
    return sum(comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k + 1))


def main():
    rows = graded_predictions()
    head = "| group | n | model said | hit | break-even at recorded price | ROI at recorded price |\n|---|---|---|---|---|---|"
    for mv in ("props-v0", "props-v1"):
        dk = [r for r in rows if r["mv"] == mv and r["book"] == "DraftKings"]
        print(f"\n### {mv}, DraftKings lines, by model win chance\n\n{head}")
        for lo in (0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8):
            print(_row(f"{lo:.0%}-{lo + 0.05:.0%}", [r for r in dk if lo <= r["prob"] < lo + 0.05]))
        pool = [r for r in dk if old_rule(r)]
        print(f"\n### {mv}: every prop the old pick rule could have chosen\n\n{head}")
        print(_row("all", pool))
        print(_row("side known (labelled)", [r for r in pool if r["basis"] == "labelled"]))
        print(_row("side unknown (worse price of the pair recorded)", [r for r in pool if r["basis"] == "conservative"]))
        ll = lambda ps, ys: -sum(y * math.log(min(max(p, 1e-4), 1 - 1e-4)) + (1 - y) * math.log(1 - min(max(p, 1e-4), 1 - 1e-4)) for p, y in zip(ps, ys)) / len(ys)
        lab = [r for r in dk if r["fair"] is not None]
        if dk:
            print(f"\nlog loss on all {len(dk)} DraftKings props: model {ll([r['prob'] for r in dk], [r['win'] for r in dk]):.4f}, coin flip {math.log(2):.4f}")
        if lab:
            print(f"log loss where the market fair price is known (n={len(lab)}): model {ll([r['prob'] for r in lab], [r['win'] for r in lab]):.4f}, "
                  f"market {ll([r['fair'] for r in lab], [r['win'] for r in lab]):.4f}")
    games = {g["game_id"]: g for g in _jsonl(f"{ROOT}/ledger/games.jsonl")}
    box = {(b["game_id"], str(b["player_id"])): b for b in _jsonl(f"{ROOT}/ledger/player_games.jsonl")}
    leans = track.grade(track.load(ROOT), games, box)
    tickets = LN.grade_tickets(LN.load_tickets(ROOT), games, box, leans, {"parlay": 1.0, "lotto": 1.0})
    print("\n### Posted picks by period\n\n| period | straights | units | model said | P(this few wins) at the pool's 53.7% | tickets | ticket units |\n|---|---|---|---|---|---|---|")
    for name, a, b in (("Oct 20 - Nov 1 (props-v1)", "2026-10-20", "2026-11-01"), ("Nov 2 - Nov 10 (props-v0)", "2026-11-02", "2026-11-10"),
                       ("Nov 11 - Nov 16 (props-v0)", "2026-11-11", "2026-11-16")):
        x = [l for l in leans if l["market"] == "prop" and a <= l["slate"] <= b and l["result"] in ("win", "loss")]
        t = [k for k in tickets if a <= k["slate"] <= b and k["result"] in ("win", "loss")]
        w = sum(l["result"] == "win" for l in x)
        print(f"| {name} | {w}-{len(x) - w} | {sum(l['net_units'] for l in x):+.2f} | {sum(l['prob'] for l in x) / len(x):.1%} | {_cdf(w, len(x), 0.537):.3f} | "
              f"{sum(k['result'] == 'win' for k in t)}-{sum(k['result'] == 'loss' for k in t)} | {sum(k['net_units'] for k in t):+.2f} |")


if __name__ == "__main__":
    main()
