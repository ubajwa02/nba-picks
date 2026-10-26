"""Scoring and performance metrics. Pure functions, tested in tests/test_metrics.py."""
from __future__ import annotations

import math
import random


def brier(probs: list[float], outcomes: list[int]) -> float:
    _same_len(probs, outcomes)
    return sum((p - y) ** 2 for p, y in zip(probs, outcomes)) / len(probs)


def log_loss(probs: list[float], outcomes: list[int], eps: float = 1e-12) -> float:
    _same_len(probs, outcomes)
    s = 0.0
    for p, y in zip(probs, outcomes):
        p = min(max(p, eps), 1 - eps)
        s -= y * math.log(p) + (1 - y) * math.log(1 - p)
    return s / len(probs)


def calibration(probs: list[float], outcomes: list[int], bins: int = 10) -> list[dict]:
    """Equal-width bins. Each row: range, n, mean predicted, observed rate, 95% Wilson interval."""
    rows = []
    for b in range(bins):
        lo, hi = b / bins, (b + 1) / bins
        idx = [i for i, p in enumerate(probs) if lo <= p < hi or (b == bins - 1 and p == 1.0)]
        if not idx:
            continue
        n = len(idx); k = sum(outcomes[i] for i in idx)
        rows.append(dict(lo=lo, hi=hi, n=n, predicted=sum(probs[i] for i in idx) / n, observed=k / n,
                         ci=wilson(k, n)))
    return rows


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    r = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - r) / d, (c + r) / d)


def roi_summary(nets: list[float], stakes: list[float] | None = None, n_boot: int = 2000, seed: int = 7) -> dict:
    """Units won, ROI on stake, bootstrap 95% CI for ROI, t-stat of mean net per bet."""
    n = len(nets)
    stakes = stakes or [1.0] * n
    if n == 0:
        return dict(n=0, units=0.0, staked=0.0, roi=None, roi_ci=None, t=None)
    staked = sum(stakes); units = sum(nets)
    mean = units / n
    sd = math.sqrt(sum((x - mean) ** 2 for x in nets) / (n - 1)) if n > 1 else 0.0
    t = mean / (sd / math.sqrt(n)) if sd > 0 else None
    rnd = random.Random(seed)
    boots = []
    for _ in range(n_boot if n > 1 else 0):
        idx = [rnd.randrange(n) for _ in range(n)]
        s = sum(stakes[i] for i in idx)
        boots.append(sum(nets[i] for i in idx) / s if s else 0.0)
    boots.sort()
    ci = (boots[int(0.025 * len(boots))], boots[int(0.975 * len(boots)) - 1]) if boots else None
    return dict(n=n, units=units, staked=staked, roi=units / staked if staked else None, roi_ci=ci, t=t)


def drawdown(nets: list[float]) -> dict:
    peak = cum = 0.0; mdd = 0.0
    streak = longest = 0
    for x in nets:
        cum += x
        peak = max(peak, cum)
        mdd = min(mdd, cum - peak)
        if x < 0:
            streak += 1; longest = max(longest, streak)
        elif x > 0:
            streak = 0
    return dict(max_drawdown=mdd, longest_losing_streak=longest, final=cum)


def noise_floor(n_variants: int) -> float:
    """Expected max |t| among N null variants: sqrt(2 ln N) (house rule)."""
    return math.sqrt(2 * math.log(max(n_variants, 2)))


def _same_len(a, b):
    if len(a) != len(b) or not a:
        raise ValueError("need equal, non-empty sequences")
