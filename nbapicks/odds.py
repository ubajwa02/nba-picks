"""Odds arithmetic. Every function here is pure and covered by tests/test_odds.py.

Conventions: decimal odds O include the stake (O=2.0 is even money). EV and ROI
are per 1 unit staked. Probabilities are in [0, 1].
"""
from __future__ import annotations

import math


def american_to_decimal(a: float) -> float:
    if a is None or a == 0 or -100 < a < 100:
        raise ValueError(f"invalid American odds: {a!r}")
    return 1 + (a / 100 if a > 0 else 100 / -a)


def decimal_to_american(o: float) -> int:
    if o is None or o <= 1:
        raise ValueError(f"invalid decimal odds: {o!r}")
    return int(round((o - 1) * 100)) if o >= 2 else int(round(-100 / (o - 1)))


def implied_prob(o: float) -> float:
    """Break-even win probability for a win-or-lose bet at decimal odds o."""
    if o <= 1:
        raise ValueError(f"invalid decimal odds: {o!r}")
    return 1 / o


def ev_binary(p: float, o: float) -> float:
    """Expected net profit per unit: p(O-1) - (1-p) == pO - 1."""
    _check_p(p)
    return p * (o - 1) - (1 - p)


def ev_with_push(p_win: float, p_push: float, o: float) -> float:
    """EV per unit when a push returns the stake (spreads/totals on whole lines)."""
    _check_p(p_win); _check_p(p_push)
    if p_win + p_push > 1 + 1e-9:
        raise ValueError("p_win + p_push > 1")
    p_loss = 1 - p_win - p_push
    return p_win * (o - 1) - p_loss


def min_decimal_for_edge(p_win: float, edge: float, p_push: float = 0.0) -> float:
    """Smallest decimal price at which EV per unit >= edge.

    Solves p_win*(O-1) - p_loss = edge  ->  O = 1 + (edge + p_loss) / p_win.
    This is the number printed on a card as "bet only at this price or better".
    """
    _check_p(p_win)
    if p_win <= 0:
        return math.inf
    p_loss = 1 - p_win - p_push
    return 1 + (edge + p_loss) / p_win


def devig_multiplicative(odds: list[float]) -> list[float]:
    """Remove the bookmaker margin by normalising implied probabilities."""
    imp = [implied_prob(o) for o in odds]
    s = sum(imp)
    return [x / s for x in imp]


def devig_power(odds: list[float], tol: float = 1e-10) -> list[float]:
    """Power method: find k with sum(imp_i ** k) == 1. Corrects favourite-longshot bias
    better than normalisation for two-way NBA markets."""
    imp = [implied_prob(o) for o in odds]
    lo, hi = 0.5, 3.0
    for _ in range(200):
        k = (lo + hi) / 2
        s = sum(x ** k for x in imp)
        if abs(s - 1) < tol:
            break
        if s > 1:
            lo = k
        else:
            hi = k
    return [x ** k for x in imp]


def overround(odds: list[float]) -> float:
    return sum(implied_prob(o) for o in odds) - 1


def parlay_decimal(legs: list[float]) -> float:
    out = 1.0
    for o in legs:
        if o <= 1:
            raise ValueError(f"invalid leg odds {o}")
        out *= o
    return out


def _check_p(p: float) -> None:
    # tolerate float rounding from normalised distributions (1 + 2e-16)
    if p is None or math.isnan(p) or not (-1e-9 <= p <= 1 + 1e-9):
        raise ValueError(f"probability out of range: {p!r}")
