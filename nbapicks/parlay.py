"""Parlays and lotto parlays built only from legs that each qualified on their own.

Legs from the same game are dependent (an ML and the over move together), and
books price same-game parlays with their own correlation adjustment, so the
builder never combines legs from one game: cross-game legs are treated as
independent, which is the standard assumption for different NBA games.
`same_game_joint` estimates a same-game joint probability by simulation for
research use; it is not used to publish.
"""
from __future__ import annotations

import itertools
import math
import random

from . import odds as O


def joint_independent(probs: list[float]) -> float:
    return math.prod(probs)


def same_game_joint(legs: list[tuple[str, str, float | None]], mu_m: float, sd_m: float, mu_t: float, sd_t: float,
                    rho: float = 0.0, n: int = 20000, seed: int = 1) -> float:
    """P(all legs win) for legs on one game, simulating (margin, total) jointly.
    legs: (market, selection, line) with market in ml/spread/total. Pushes count as not-win."""
    rnd = random.Random(seed)
    hits = 0
    for _ in range(n):
        z1, z2 = rnd.gauss(0, 1), rnd.gauss(0, 1)
        m = round(mu_m + sd_m * z1)
        if m == 0:
            m = 1 if rnd.random() < 0.5 else -1
        t = round(mu_t + sd_t * (rho * z1 + math.sqrt(1 - rho * rho) * z2))
        ok = True
        for market, sel, line in legs:
            side_m = m if sel == "home" else -m
            if market == "ml":
                ok = side_m > 0
            elif market == "spread":
                ok = side_m + line > 0
            elif market == "total":
                ok = (t > line) if sel == "over" else (t < line)
            if not ok:
                break
        hits += ok
    return hits / n


def build(legs: list, cfg: dict, kind: str = "parlay") -> list[dict]:
    """legs: qualifying straight Candidates (decision eligible). Returns parlay dicts
    sorted by EV, capped by targets/limits. Legs with push risk are excluded
    (a push changes the payout) unless the push probability is negligible."""
    mk = cfg["markets"][kind]
    if not mk.get("enabled"):
        return []
    usable = [c for c in legs if c.push < 0.005 and c.prob > 0]
    out = []
    sizes = range(2, mk["max_legs"] + 1) if kind == "parlay" else range(3, mk["max_legs"] + 1)
    for k in sizes:
        for combo in itertools.combinations(usable, k):
            if len({c.game_id for c in combo}) < k:
                continue  # same-game legs: dependent, excluded
            p = joint_independent([c.prob for c in combo])
            dec = O.parlay_decimal([c.price_dec for c in combo])
            if kind == "lotto" and dec < mk["min_decimal"]:
                continue
            if kind == "parlay" and dec >= cfg["markets"]["lotto"]["min_decimal"]:
                continue
            ev = O.ev_binary(p, dec)
            if ev >= mk["min_ev"]:
                out.append(dict(kind=kind, legs=combo, prob=p, price_dec=dec, ev=ev))
    out.sort(key=lambda x: -x["ev"])
    chosen, used = [], set()
    for pz in out:
        ids = {id(c) for c in pz["legs"]}
        if ids & used and kind == "parlay":
            continue  # do not stack the same leg into several parlays
        chosen.append(pz); used |= ids
        if len(chosen) >= cfg["targets"][kind]:
            break
    return chosen
