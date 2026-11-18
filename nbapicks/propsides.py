"""Which DraftKings prop price is the Over? (NBA-033 follow-up)

ESPN lists every DraftKings prop line as two prices without saying which one is the
Over. The old game-level vote (is the first-listed side the Over?) never reached its
90% bar (76-86% on 2026-10-22), so every DraftKings prop was rejected and the prop
model produced nothing on the market that matters most.

Two honest ways to price a side without guessing:

1. Ladder labelling. bet365 milestone props ("20+ points" = Over 19.5) are labelled.
   P(over) falls as the line rises, so the bet365 ladder brackets P(over L) for any DK
   line L between two milestones. If exactly one DK side's de-vigged probability is
   consistent with that bracket (and the two sides differ enough to tell apart), that
   side is the Over. Otherwise the pair stays unlabelled.

2. Conservative price. For an unlabelled pair, whichever side we pick was offered at
   one of the two prices, so the worse (lower) decimal price is a price we certainly
   could have had or better. EV and ROI computed at it are lower bounds. No price is
   invented; the record says price_basis = "conservative".

Since 2026-11-17 there is a third, and it comes first: ESPN lists the DraftKings Over before the
Under. nbapicks/sideorder.py holds the evidence and the checks that must keep passing; while they
do, every pair is labelled by its listing order and the two ways above are only the fallback.
"""
from __future__ import annotations

import math
from collections import defaultdict

from . import odds as O

MIN_SEPARATION = 0.06   # |p0 - p1| below this: sides too close to tell apart (and the price barely matters)
# bet365 milestone prices are one-sided and include margin, so 1/price overstates P(over) by
# roughly the margin: the lower bound gets wide slack, the upper bound (already loose) a little.
SLACK_LOW, SLACK_HIGH = 0.08, 0.02
# A real over/under pair at one line has implied probabilities that add to a little over 1
# (the book's margin). Alt-ladder rungs listed as a "pair" can add to far less (15.0 / 26.0
# sums to 0.10); pricing those as a two-way market invents edge, so they are not markets.
PAIR_OVERROUND = (0.99, 1.20)


def plausible_pair(p0: float, p1: float) -> bool:
    """True when two decimal prices can be the two sides of one line."""
    if not p0 or not p1 or p0 <= 1 or p1 <= 1:
        return False
    lo, hi = PAIR_OVERROUND
    return lo <= 1 / p0 + 1 / p1 <= hi


def _norm(name: str) -> str:
    return "".join(ch for ch in (name or "").lower() if ch.isalpha())


def _logit(p):
    p = min(max(p, 1e-4), 1 - 1e-4)
    return math.log(p / (1 - p))


def _sig(z):
    return 1 / (1 + math.exp(-z))


def ladders(bet365_rows: list[dict]) -> dict:
    """(player_norm, stat) -> sorted [(line, implied P(over) incl. margin)] from bet365 milestone 'over' rows."""
    out = defaultdict(dict)
    for r in bet365_rows:
        if r.get("market") != "prop" or r.get("selection") != "over" or not r.get("price_dec") or r.get("line") is None:
            continue
        out[(_norm(r.get("player_name")), r.get("stat"))][float(r["line"])] = 1 / float(r["price_dec"])
    return {k: sorted(v.items()) for k, v in out.items()}


def bracket(ladder: list[tuple[float, float]], line: float) -> tuple[float, float] | None:
    """Bounds on P(over line) implied by the ladder: exact match -> (q, q); between two
    milestones -> (q_high_line, q_low_line); outside the ladder -> one-sided bound."""
    lo_bound, hi_bound = 0.0, 1.0
    for l, q in ladder:
        if abs(l - line) < 1e-9:
            return (q, q)
        if l < line:
            hi_bound = min(hi_bound, q)      # a lower line is at least as likely to go over
        else:
            lo_bound = max(lo_bound, q)      # a higher line is at most as likely
    if lo_bound == 0.0 and hi_bound == 1.0:
        return None
    return (lo_bound, hi_bound)


def label_pair(price0: float, price1: float, ladder: list[tuple[float, float]] | None, line: float) -> str | None:
    """'side0' or 'side1' (the Over), or None when it cannot be told apart honestly."""
    if not ladder:
        return None
    b = bracket(ladder, line)
    if b is None:
        return None
    p0, p1 = O.devig_multiplicative([price0, price1])
    if abs(p0 - p1) < MIN_SEPARATION:
        return None
    lo, hi = b[0] - SLACK_LOW, b[1] + SLACK_HIGH
    ok0, ok1 = lo <= p0 <= hi, lo <= p1 <= hi
    if ok0 and not ok1:
        return "side0"
    if ok1 and not ok0:
        return "side1"
    if ok0 and ok1 and b[0] == b[1]:
        # exact milestone: nearest side wins only if clearly nearer
        d0, d1 = abs(p0 - b[0]), abs(p1 - b[0])
        if abs(d0 - d1) >= MIN_SEPARATION:
            return "side0" if d0 < d1 else "side1"
    return None


def price_sides(sides: dict, label: str | None) -> dict:
    """{'over': (price, fair, basis), 'under': (...)} for a DK pair {'side0': row, 'side1': row}.
    Labelled: each side its own price and de-vigged fair. Unlabelled: both sides at the
    worse price, fair unknown (None)."""
    d0, d1 = sides["side0"]["price_dec"], sides["side1"]["price_dec"]
    if label in ("side0", "side1"):
        f0, f1 = O.devig_multiplicative([d0, d1])
        over_is0 = label == "side0"
        return {"over": (d0 if over_is0 else d1, f0 if over_is0 else f1, "labelled"),
                "under": (d1 if over_is0 else d0, f1 if over_is0 else f0, "labelled")}
    worst = min(d0, d1)
    return {"over": (worst, None, "conservative"), "under": (worst, None, "conservative")}
