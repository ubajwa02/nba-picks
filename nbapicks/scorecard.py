"""Live scorecard: how settled predictions did against their own probabilities and the book.

Descriptive only. The sample is days old and tiny; nothing here is evidence of an edge.
Predictions are re-issued on every run, so each (game, market, side, line, player, stat)
is counted once, using its latest pre-settlement row.
"""
from __future__ import annotations

import json
from collections import defaultdict

PROB_BUCKETS = [(0.0, 0.4, "<40%"), (0.4, 0.5, "40-50%"), (0.5, 0.6, "50-60%"), (0.6, 0.7, "60-70%"), (0.7, 1.01, ">=70%")]
EV_BUCKETS = [(-9, 0.0, "EV<0"), (0.0, 0.05, "EV 0-5%"), (0.05, 0.15, "EV 5-15%"), (0.15, 9, "EV>=15%")]


def rows(preds: list[dict], settled: dict, since: str = "2026-10-20") -> list[dict]:
    latest = {}
    for p in sorted(preds, key=lambda p: p["created_at"]):
        if p.get("category") != "straight" or p["created_at"] < since or p["pred_id"] not in settled:
            continue
        e = settled[p["pred_id"]]
        if e["result"] not in ("win", "loss") or p.get("prob") is None or not p.get("price_dec"):
            continue
        k = (p["game_id"], p["market"], p["selection"], p.get("line"), p.get("player_id"), p.get("stat"))
        latest[k] = dict(pred_id=p["pred_id"], game_id=p["game_id"], market=p["market"], selection=p["selection"],
                         line=p.get("line"), player=p.get("player_name"), stat=p.get("stat"), decision=p.get("decision"),
                         prob=p["prob"], implied=1 / p["price_dec"], ev=p.get("ev"), price_dec=p["price_dec"],
                         result=e["result"], y=int(e["result"] == "win"), net=e.get("net_units") or 0.0)
    return list(latest.values())


def _group(rs, key):
    g = defaultdict(list)
    for r in rs:
        g[key(r)].append(r)
    return {k: dict(n=len(v), wins=sum(r["y"] for r in v), win_rate=round(sum(r["y"] for r in v) / len(v), 3),
                    units=round(sum(r["net"] for r in v), 3)) for k, v in sorted(g.items())}


def _bucket(v, bs):
    for lo, hi, lab in bs:
        if lo <= v < hi:
            return lab
    return bs[-1][2]


def build(preds: list[dict], settled: dict, since: str = "2026-10-20") -> dict:
    rs = rows(preds, settled, since)
    n = len(rs)
    cal = []
    for *_, b in PROB_BUCKETS:
        v = [r for r in rs if _bucket(r["prob"], PROB_BUCKETS) == b]
        if v:
            cal.append(dict(bucket=b, n=len(v), predicted=round(sum(r["prob"] for r in v) / len(v), 3),
                            market=round(sum(r["implied"] for r in v) / len(v), 3),
                            actual=round(sum(r["y"] for r in v) / len(v), 3)))
    brier = dict(model=round(sum((r["prob"] - r["y"]) ** 2 for r in rs) / n, 4) if n else None,
                 market=round(sum((r["implied"] - r["y"]) ** 2 for r in rs) / n, 4) if n else None, n=n)
    ev_b = _group([r for r in rs if r["ev"] is not None], lambda r: _bucket(r["ev"], EV_BUCKETS))
    return dict(since=since, n=n, note="Descriptive only: tiny sample, no inference. Market prob = 1/price (includes vig).",
                brier=brier, calibration=cal, by_ev=ev_b, by_market=_group(rs, lambda r: r["market"]),
                by_decision=_group(rs, lambda r: r["decision"]), rows=sorted(rs, key=lambda r: -(r["ev"] or 0)))


def markdown(sc: dict, leans: dict | None = None, lean_rows: list | None = None) -> str:
    L = ["# Live scorecard", "", f"Settled predictions since {sc['since']}: **{sc['n']}** (deduplicated). {sc['note']}", ""]
    b = sc["brier"]
    L += [f"Brier: model {b['model']} vs market-implied {b['market']} (n={b['n']}; lower is better).", "",
          "## Calibration", "", "| prob bucket | n | predicted | market | actual |", "|---|---|---|---|---|"]
    L += [f"| {c['bucket']} | {c['n']} | {c['predicted']:.3f} | {c['market']:.3f} | {c['actual']:.3f} |" for c in sc["calibration"]]
    for title, key in (("By EV bucket", "by_ev"), ("By market", "by_market"), ("By decision", "by_decision")):
        L += ["", f"## {title}", "", "| group | n | wins | win rate | units |", "|---|---|---|---|---|"]
        L += [f"| {k} | {v['n']} | {v['wins']} | {v['win_rate']:.3f} | {v['units']:+.2f} |" for k, v in sc[key].items()]
    if leans is not None:
        L += ["", "## Posted leans (1u flat)", "",
              f"Record {leans['wins']}-{leans['losses']}-{leans['pushes']}, {leans['units']:+.2f}u, pending {leans['pending']}.", "",
              "| slate | lean | price | stat/score | result | units |", "|---|---|---|---|---|---|"]
        for l in lean_rows or []:
            what = l.get("label") or f"{l['market']} {l['selection']} {l.get('line')}"
            sv = l["stat_value"] if l["market"] == "prop" else l.get("score")
            L.append(f"| {l['slate']} | {what} | {l['price_american']:+d} | {sv} | {l['result']} | "
                     f"{(l['net_units'] or 0):+.2f} |")
    L += ["", "## Rows", "", "| market | pick | decision | model p | book p | EV | result |", "|---|---|---|---|---|---|---|"]
    for r in sc["rows"]:
        pick = f"{r['player'] or ''} {r['stat'] or ''} {r['selection']} {r['line'] if r['line'] is not None else ''}".strip()
        ev = f"{r['ev']:+.3f}" if r["ev"] is not None else "-"
        L.append(f"| {r['market']} | {pick} ({r['game_id']}) | {r['decision']} | {r['prob']:.3f} | {r['implied']:.3f} | {ev} | {r['result']} |")
    return "\n".join(L) + "\n"
