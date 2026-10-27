"""Posted leans: the picks actually shown to people (split-card props and model leans),
recorded in data/ledger/posted_leans.jsonl and graded from the games/box ledgers.

Grading is recomputed from the ledgers on every run (never typed in by hand), so a lean
stays pending until its game is final and, for props, the player's box row is stored.
"""
from __future__ import annotations

import json
import os

from .odds import american_to_decimal
from .settle import GameResult, net_profit, settle_leg
from .store import stable_id

LEANS = "posted_leans.jsonl"
KEYS = ("slate", "game_id", "market", "selection", "line", "player_id", "stat")


def lean_id(l: dict) -> str:
    return stable_id(*(l.get(k) for k in KEYS))


def load(root: str) -> list[dict]:
    p = os.path.join(root, "ledger", LEANS)
    return [json.loads(x) for x in open(p) if x.strip()] if os.path.exists(p) else []


def add(root: str, lean: dict) -> bool:
    """Append a lean once (append-only; same key twice is a no-op)."""
    lean = dict(lean, lean_id=lean_id(lean))
    if any(x["lean_id"] == lean["lean_id"] for x in load(root)):
        return False
    os.makedirs(os.path.join(root, "ledger"), exist_ok=True)
    with open(os.path.join(root, "ledger", LEANS), "a") as fh:
        fh.write(json.dumps(lean, sort_keys=True) + "\n")
    return True


def grade(leans: list[dict], games: dict, box: dict) -> list[dict]:
    """games: game_id -> latest game row; box: (game_id, player_id) -> box row."""
    out = []
    for l in leans:
        g = games.get(l["game_id"])
        res = GameResult(g["status"], g.get("home_score"), g.get("away_score")) if g else GameResult("scheduled")
        stat_v = played = None
        if l["market"] == "prop":
            b = box.get((l["game_id"], str(l["player_id"])))
            if b:
                played, stat_v = bool(b["played"]), b.get(l["stat"])
            elif g and g["status"] == "final" and any(k[0] == l["game_id"] for k in box):
                played = False
        r = settle_leg(l["market"], l["selection"], l.get("line"), res, stat_v, played)
        dec = american_to_decimal(l["price_american"])
        out.append(dict(l, result=r, stat_value=stat_v, price_dec=dec, net_units=net_profit(r, dec, l.get("stake", 1.0)),
                        score=f"{g['away']} {g.get('away_score')} @ {g['home']} {g.get('home_score')}" if g else None,
                        matchup=f"{g['away']} @ {g['home']}" if g else None))
    return out


def record(graded: list[dict]) -> dict:
    s = [g for g in graded if g["result"] in ("win", "loss", "push")]
    return dict(n=len(graded), settled=len(s), wins=sum(g["result"] == "win" for g in s),
                losses=sum(g["result"] == "loss" for g in s), pushes=sum(g["result"] == "push" for g in s),
                pending=sum(g["result"] == "pending" for g in graded),
                units=round(sum(g["net_units"] or 0 for g in s), 3))
