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


def pick_leans(preds: list[dict], cfg: dict, slate: str, now_iso: str, pool: bool = False) -> list[dict]:
    """The posted leans (strict rule), or with pool=True the wider list of clean, not-started props
    ranked by win chance that parlays and the lotto draw from (they must always be built)."""
    lc = dict(cfg["leans"])
    if pool:
        lc.update(min_prob=0.50, min_decimal=1.15, min_last10=0, per_game=4, max_leans=18)
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


def _combos(legs: list[dict], sizes) -> list[dict]:
    out = []
    for k in sizes:
        for combo in itertools.combinations(legs, k):
            if len({c["game_id"] for c in combo}) < k:
                continue                  # same-game legs are dependent: never combined
            dec = O.parlay_decimal([O.american_to_decimal(c["price_american"]) for c in combo])
            p = math.prod(c["prob"] for c in combo)
            out.append(dict(legs=combo, price_dec=dec, prob=p, ev=O.ev_binary(p, dec)))
    return out


def _leg(l: dict) -> dict:
    keys = ("lean_id", "label", "prob", "price_american", "game_id", "market", "selection", "line", "player_id", "stat", "slate")
    return {k: l.get(k) for k in keys} | {"stake": 1.0}


def build_tickets(legs: list[dict], cfg: dict, slate: str) -> tuple[list[dict], list[str]]:
    """Always the daily target of parlays and one lotto, each the highest win-chance combination of
    different-game legs from the pool. Research only: the real EV is stored and shown, even when negative.
    Parlays prefer legs not used by another parlay; they reuse a leg only when the pool is too small."""
    legs = [dict(l, lean_id=l.get("lean_id") or track.lean_id(l)) for l in legs]
    notes, out = [], []
    want = cfg["targets"]["parlay"]
    lm = cfg["markets"]["lotto"]
    if len(legs) < 2:
        return [], [f"Only {len(legs)} eligible prop{'s' if len(legs) != 1 else ''} today, so no parlays or lotto could be built."]
    pairs = sorted(_combos(legs, (2,)), key=lambda c: -c["prob"])
    used, chosen = set(), []
    for c in pairs:
        ids = {l["lean_id"] for l in c["legs"]}
        if ids & used:
            continue
        chosen.append(c); used |= ids
        if len(chosen) >= want:
            break
    if len(chosen) < want:                                     # too few distinct legs: reuse, best first
        for c in pairs:
            if c not in chosen:
                chosen.append(c)
            if len(chosen) >= want:
                break
        notes.append("Parlays share some legs today because too few eligible props were available.")
    if len(chosen) < want:
        notes.append(f"Only {len(chosen)} of {want} parlays could be built from today's eligible props.")
    lotto = []
    for size in range(min(lm["max_legs"], len(legs)), 2, -1):
        cs = _combos(legs, (size,))
        big = [c for c in cs if c["price_dec"] >= lm["min_decimal"]]
        if big or cs:
            lotto = sorted(big or cs, key=lambda c: -c["prob"])[:cfg["targets"]["lotto"]]
            if not big:
                notes.append(f"The lotto pays {lotto[0]['price_dec']:.1f}x, under the usual {lm['min_decimal']:g}x target, "
                             f"because no larger payout was available from today's eligible props.")
            break
    if not lotto:
        notes.append("No lotto today: fewer than 3 eligible props in different games.")
    for kind, tickets in (("parlay", chosen), ("lotto", lotto)):
        for c in tickets:
            ids = sorted(l["lean_id"] for l in c["legs"])
            out.append(dict(ticket_id=stable_id(slate, kind, *ids), slate=slate, kind=kind, price_dec=round(c["price_dec"], 4),
                            price_american=decimal_to_american(c["price_dec"]), prob=round(c["prob"], 4), ev=round(c["ev"], 4),
                            stake=cfg["stakes"][kind], research=True, legs=[_leg(l) for l in c["legs"]]))
    return out, notes


# ---- ledger ----
def load_tickets(root: str) -> list[dict]:
    p = os.path.join(root, "ledger", TICKETS)
    return [json.loads(x) for x in open(p) if x.strip()] if os.path.exists(p) else []


def replace_slate_tickets(root: str, slate: str, tickets: list[dict]) -> None:
    """Swap a slate's tickets built under a superseded rule (no research flag) for the current ones."""
    keep = [t for t in load_tickets(root) if t["slate"] != slate or t.get("research")]
    have = {t["ticket_id"] for t in keep}
    with open(os.path.join(root, "ledger", TICKETS), "w") as fh:
        for t in keep + [t for t in tickets if t["ticket_id"] not in have]:
            fh.write(json.dumps(t, sort_keys=True) + "\n")


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


def grade_tickets(tickets: list[dict], games: dict, box: dict, leans: list[dict] | None = None, stakes: dict | None = None) -> list[dict]:
    """Each ticket's result from its legs graded against the final box scores: any loss loses, any pending
    waits, a pushed or void leg drops out of the payout (settle.settle_parlay)."""
    by_id = {(l.get("lean_id") or track.lean_id(l)): l for l in leans or []}
    out = []
    for t in tickets:
        # tickets written before legs carried their full definition: fill it from the posted lean
        t = dict(t, legs=[dict(by_id.get(l["lean_id"], {}), **l) if "market" not in l else l for l in t["legs"]])
        graded = track.grade(t["legs"], games, box)
        res = [(g["result"] or "pending", O.american_to_decimal(g["price_american"])) for g in graded]
        stake = (stakes or {}).get(t["kind"], t["stake"])      # history is restated at the current stake
        result, net, eff = settle_parlay(res, stake)
        legs = [dict(l, result=g["result"] or "pending", stat_value=g["stat_value"]) for l, g in zip(t["legs"], graded)]
        out.append(dict(t, legs=legs, stake=stake, result=result, net_units=net))
    return out
