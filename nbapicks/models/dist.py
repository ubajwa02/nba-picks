"""Discrete outcome distributions for NBA scores.

Margins and totals are integers and margins are never 0, so probabilities for
whole-number lines (pushes) come from an integer distribution, not a continuous
normal. P(k) is proportional to the normal density at k; margin 0 is removed and
the rest renormalised (overtime resolves ties).
"""
from __future__ import annotations

import math
from functools import lru_cache

SQ2PI = math.sqrt(2 * math.pi)


def _pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / SQ2PI


def norm_cdf(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


@lru_cache(maxsize=20000)
def _int_dist(mu: float, sigma: float, no_zero: bool) -> tuple[tuple[int, ...], tuple[float, ...]]:
    lo, hi = int(math.floor(mu - 7 * sigma)), int(math.ceil(mu + 7 * sigma))
    ks = [k for k in range(lo, hi + 1) if not (no_zero and k == 0)]
    w = [_pdf((k - mu) / sigma) for k in ks]
    s = sum(w)
    return tuple(ks), tuple(x / s for x in w)


def margin_probs(mu: float, sigma: float, line: float, side: str = "home") -> tuple[float, float]:
    """(P(win), P(push)) for a spread bet; line from the side's view (home -3.5 -> -3.5).
    line=0 with no push possible is the moneyline."""
    mu = round(mu, 2); sigma = round(sigma, 2)
    ks, ps = _int_dist(mu, sigma, True)
    win = push = 0.0
    for k, p in zip(ks, ps):
        m = k if side == "home" else -k
        v = m + line
        if v > 0:
            win += p
        elif v == 0:
            push += p
    return win, push


def ml_prob(mu: float, sigma: float, side: str = "home") -> float:
    return margin_probs(mu, sigma, 0.0, side)[0]


def total_probs(mu: float, sigma: float, line: float, side: str = "over") -> tuple[float, float]:
    mu = round(mu, 2); sigma = round(sigma, 2)
    ks, ps = _int_dist(mu, sigma, False)
    win = push = 0.0
    for k, p in zip(ks, ps):
        if k == line:
            push += p
        elif (k > line) == (side == "over"):
            win += p
    return win, push


def count_probs(mean: float, var: float, line: float, side: str = "over") -> tuple[float, float]:
    """Player counting stats (points, rebounds...): negative binomial when overdispersed,
    Poisson otherwise. Returns (P(win), P(push))."""
    if mean <= 0:
        return (0.0, 0.0) if side == "over" else (1.0, 0.0)
    var = max(var, mean * 1.0001)
    r = mean * mean / (var - mean)
    p = r / (r + mean)
    # pmf via log-gamma for stability
    k_max = int(mean + 12 * math.sqrt(var)) + 5
    lg = math.lgamma
    pmf = [math.exp(lg(k + r) - lg(r) - lg(k + 1) + r * math.log(p) + k * math.log(1 - p)) for k in range(k_max)]
    s = sum(pmf)
    win = push = 0.0
    for k, q in enumerate(pmf):
        q /= s
        if k == line:
            push += q
        elif (k > line) == (side == "over"):
            win += q
    return win, push
