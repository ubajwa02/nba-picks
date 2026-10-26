"""Daily leans, parlays and lotto: the picks the system posts each slate (research only).

Rule, fixed here and in config/nbapicks.yaml `leans:` and never tuned on results:
  leans   props-v1 prop predictions for today's slate with a verified over/under side, a price of at
          least `min_decimal`, at least `min_last10` games of recent history and no milestone or
          side-unverified flag; probability >= `min_prob`; one per player, `per_game` per game; the
          `max_leans` most likely. Posted once per slate. Nothing is posted when a critical source is
          failing, the injury report is stale, or the global pause is on.
  parlays 2..`max_legs` leans from different games (independent product), priced below the lotto
          threshold, model EV >= the parlay min_ev, no lean reused across parlays; most likely first,
          up to targets.parlay.
  lotto   3..`max_legs` leans from different games priced at >= min_decimal with model EV >= its min_ev;
          the single most likely one.
Fewer than the ceiling is normal: each ceiling is a maximum, and the reason for any shortfall is stored.
"""
from __future__ import annotations

import itertools
import json
import math
import os

from . import odds as O
from . import track
from .odds import decimal_to_american
from .settle import settle_parlay
from .store import stable_id

TICKETS = "posted_tickets.jsonl"
NOTES = "ticket_notes.json"
JUNK_FLAGS = ("milestone", "side_unverified")


def _inputs(p: dict) -> dict:
    x = p.get("inputs")
    if isinstance(x, str):
        try:
            return json.loads(x or "{}")
        except ValueError:
            return {}
    return x or {}


SOFT = ("low sample", "below", "no model estimate: too little")


def _clean_decision(p: dict) -> bool:
    """Qualified or watchlist, or held/rejected only for a soft reason (a thin season sample or an edge
    under the threshold). Injury, stale-data, price-mapping, side and source problems always exclude."""
    if p.get("decision") in ("eligible", "watch"):
        return True
    parts = [x.strip() for x in str(p.get("reason") or "").split(";") if x.strip()]
    return bool(parts) and all(any(k in x for k in SOFT) for x in parts)


def lean_label(p: dict) -> str:
    name = p.get("player_name") or p.get("player") or "?"
    return f"{name} {p['selection'][0]}{p['line']:g} {p['stat']}"


def pick_leans(preds: list[dict], cfg: dict, slate: str, now_iso: str) -> list[dict]:
    lc = cfg["leans"]
    best: dict[tuple, dict] = {}
    for p in preds:
        if p.get("market") != "prop" or p.get("category") != "straight" or p.get("selection") not in ("over", "under"):
            continue
        if not _clean_decision(p):
            continue
        if p.get("prob") is None or not p.get("price_dec") or p["price_dec"] < lc["min_decimal"] or p.get("line") is None:
            continue
        if p["prob"] < lc["min_prob"] or not p.get("player_id") or not p.get("stat"):
            continue
        if p.get("start_utc") and p["start_utc"] <= now_iso:
            continue                      # already started
        ex = _inputs(p).get("explain") or {}
        flags = list(ex.get("flags") or []) + list(_inputs(p).get("quality_flags") or [])
        if any(k in f for f in flags for k in JUNK_FLAGS):
            continue
        if ((ex.get("line_hits_last10") or {}).get("n") or 0) < lc["min_last10"]:
            continue
        k = (p["game_id"], p["player_id"], p["stat"], p["line"], p["selection"])
        if k not in best or p["price_dec"] > best[k]["price_dec"]:
            best[k] = p
    per_player: dict[str, dict] = {}
    for p in best.values():
        if p["player_id"] not in per_player or p["prob"] > per_player[p["player_id"]]["prob"]:
            per_player[p["player_id"]] = p
    out, per_game = [], {}
    for p in sorted(per_player.values(), key=lambda p: -p["prob"]):
        if per_game.get(p["game_id"], 0) >= lc["per_game"]:
            continue
        per_game[p["game_id"]] = per_game.get(p["game_id"], 0) + 1
        out.append(dict(game_id=p["game_id"], label=lean_label(p), line=p["line"], market="prop", player_id=str(p["player_id"]),
                        price_american=decimal_to_american(p["price_dec"]), prob=round(p["prob"], 4), selection=p["selection"],
                        slate=slate, source="props_v1", stake=cfg["stakes"]["straight"], stat=p["stat"]))
        if len(out) >= lc["max_leans"]:
            break
    return out


def _combos(leans: list[dict], sizes) -> list[dict]:
    out = []
    for k in sizes:
        for combo in itertools.combinations(leans, k):
            if len({c["game_id"] for c in combo}) < k:
                continue                  # same-game legs are dependent: never combined
            dec = O.parlay_decimal([O.american_to_decimal(c["price_american"]) for c in combo])
            p = math.prod(c["prob"] for c in combo)
            out.append(dict(legs=combo, price_dec=dec, prob=p, ev=O.ev_binary(p, dec)))
    return out


def build_tickets(leans: list[dict], cfg: dict, slate: str) -> tuple[list[dict], list[str]]:
    """Parlays and the lotto from today's leans, plus plain-language reasons for any shortfall."""
    leans = [dict(l, lean_id=l.get("lean_id") or track.lean_id(l)) for l in leans]
    notes, out = [], []
    pm, lm = cfg["markets"]["parlay"], cfg["markets"]["lotto"]
    cap = int(cfg["risk"]["max_parlay_units_per_day"] // cfg["stakes"]["parlay"])
    want = min(cfg["targets"]["parlay"], cap)
    if len(leans) < 2:
        notes.append(f"Only {len(leans)} lean{'s' if len(leans) != 1 else ''} posted today, so no parlays could be built.")
    cands = [c for c in _combos(leans, range(2, pm["max_legs"] + 1)) if c["price_dec"] < lm["min_decimal"] and c["ev"] >= pm["min_ev"]]
    used, chosen = set(), []
    for c in sorted(cands, key=lambda c: -c["prob"]):
        ids = {l["lean_id"] for l in c["legs"]}
        if ids & used:
            continue
        chosen.append(c); used |= ids
        if len(chosen) >= want:
            break
    if len(leans) >= 2 and len(chosen) < cfg["targets"]["parlay"]:
        notes.append(f"{len(chosen)} of {cfg['targets']['parlay']} parlays posted: only these combinations of different-game legs "
                     f"cleared the {pm['min_ev']:.0%} model edge without reusing a leg.")
    lot = [c for c in _combos(leans, range(3, lm["max_legs"] + 1)) if c["price_dec"] >= lm["min_decimal"] and c["ev"] >= lm["min_ev"]]
    lotto = sorted(lot, key=lambda c: -c["prob"])[:cfg["targets"]["lotto"]]
    if not lotto:
        notes.append(f"No lotto today: no 3 to {lm['max_legs']}-leg combination paid at least {lm['min_decimal']:g}x "
                     f"with a {lm['min_ev']:.0%} model edge.")
    for kind, tickets in (("parlay", chosen), ("lotto", lotto)):
        for c in tickets:
            ids = sorted(l["lean_id"] for l in c["legs"])
            out.append(dict(ticket_id=stable_id(slate, kind, *ids), slate=slate, kind=kind, price_dec=round(c["price_dec"], 4),
                            price_american=decimal_to_american(c["price_dec"]), prob=round(c["prob"], 4), ev=round(c["ev"], 4),
                            stake=cfg["stakes"][kind],
                            legs=[dict(lean_id=l["lean_id"], label=l["label"], prob=l["prob"], price_american=l["price_american"],
                                       game_id=l["game_id"]) for l in c["legs"]]))
    return out, notes


# ---- ledger ----
def load_tickets(root: str) -> list[dict]:
    p = os.path.join(root, "ledger", TICKETS)
    return [json.loads(x) for x in open(p) if x.strip()] if os.path.exists(p) else []


def add_ticket(root: str, t: dict) -> bool:
    if any(x["ticket_id"] == t["ticket_id"] for x in load_tickets(root)):
        return False
    os.makedirs(os.path.join(root, "ledger"), exist_ok=True)
    with open(os.path.join(root, "ledger", TICKETS), "a") as fh:
        fh.write(json.dumps(t, sort_keys=True) + "\n")
    return True


def load_notes(root: str) -> dict:
    p = os.path.join(root, "state", NOTES)
    try:
        return json.load(open(p))
    except (FileNotFoundError, ValueError):
        return {}


def save_notes(root: str, slate: str, notes: list[str]) -> None:
    d = load_notes(root)
    d[slate] = notes
    os.makedirs(os.path.join(root, "state"), exist_ok=True)
    with open(os.path.join(root, "state", NOTES), "w") as fh:
        json.dump(d, fh, indent=1, sort_keys=True)


def grade_tickets(tickets: list[dict], graded_leans: list[dict]) -> list[dict]:
    """Each ticket's result from its legs' graded results: any loss loses, any pending waits, a pushed
    or void leg drops out of the payout (settle.settle_parlay)."""
    by_id = {(l.get("lean_id") or track.lean_id(l)): l for l in graded_leans}
    out = []
    for t in tickets:
        legs, res = [], []
        for l in t["legs"]:
            g = by_id.get(l["lean_id"]) or {}
            r = g.get("result") or "pending"
            legs.append(dict(l, result=r, stat_value=g.get("stat_value")))
            res.append((r, O.american_to_decimal(l["price_american"])))
        result, net, eff = settle_parlay(res, t["stake"])
        out.append(dict(t, legs=legs, result=result, net_units=net))
    return out
