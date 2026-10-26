"""Player-prop model (research status) and prop-side verification.

Model: expected minutes x per-minute rate, with a negative-binomial outcome whose
variance comes from the player's own game-to-game spread. Uses only games before
the prediction date. Deliberately simple; it is a baseline for challengers.
"""
from __future__ import annotations

import statistics
from collections import defaultdict

from . import odds as O
from .models import dist

STATS = ("pts", "reb", "ast", "fg3m")


class PropModel:
    version = "props-v0"

    def __init__(self, box_rows: list[dict], window: int = 15, min_games: int = 5):
        """box_rows: dicts with player_id, date (sortable), minutes, played, and stat columns.
        Must already be restricted to games before the prediction date."""
        self.window, self.min_games = window, min_games
        by = defaultdict(list)
        for r in box_rows:
            if int(r.get("played") or 0) and float(r.get("minutes") or 0) > 0:
                by[str(r["player_id"])].append(r)
        self.recent = {pid: sorted(rs, key=lambda r: r["date"])[-window:] for pid, rs in by.items()}

    def expected_minutes(self, pid: str) -> float | None:
        rs = self.recent.get(str(pid))
        if not rs or len(rs) < self.min_games:
            return None
        return statistics.mean(float(r["minutes"]) for r in rs)

    def predict(self, pid: str, stat: str, minutes: float | None = None) -> dict | None:
        rs = self.recent.get(str(pid))
        if not rs or len(rs) < self.min_games:
            return None
        mins = [float(r["minutes"]) for r in rs]
        vals = [float(r[stat] or 0) for r in rs]
        rate = sum(vals) / sum(mins)
        m = minutes if minutes is not None else statistics.mean(mins)
        mean = rate * m
        var = statistics.pvariance(vals) if len(vals) > 1 else mean
        return dict(mean=mean, var=max(var, mean * 1.05), minutes=m, games=len(rs))

    def prob(self, pred: dict, line: float, side: str) -> tuple[float, float]:
        return dist.count_probs(pred["mean"], pred["var"], line, side)


def verify_prop_sides(espn_rows: list[dict], bet365_rows: list[dict], min_n: int = 20, min_agree: float = 0.9):
    """Decide whether ESPN's first-listed prop side is the Over, using bet365 milestone
    prices ('20+ points' == over 19.5) as an independent reference. Returns
    (first_is_over: bool | None, agreement, n). None means not verified."""
    ref = {}
    for r in bet365_rows:
        if r.get("market") == "prop" and r.get("player_name"):
            ref[(_norm(r["player_name"]), r["stat"], r["line"])] = 1 / r["price_dec"]
    pairs = defaultdict(dict)
    for r in espn_rows:
        if r.get("market") == "prop" and r.get("kind") == "current" and r.get("player_name"):
            pairs[(_norm(r["player_name"]), r["stat"], r["line"])][r["selection"]] = r["price_dec"]
    votes = []
    for k, sides in pairs.items():
        if k not in ref or set(sides) != {"side0", "side1"}:
            continue
        p0, p1 = O.devig_multiplicative([sides["side0"], sides["side1"]])
        target = ref[k]  # bet365 implied P(over), with margin
        votes.append(abs(p0 - target) < abs(p1 - target))
    n = len(votes)
    if n < min_n:
        return None, None, n
    share = sum(votes) / n
    if share >= min_agree:
        return True, share, n
    if share <= 1 - min_agree:
        return False, 1 - share, n
    return None, max(share, 1 - share), n


def verified_pairs(espn_rows: list[dict], bet365_rows: list[dict], first_is_over: bool | None) -> set:
    """Keys (player, stat, line) whose own bet365 comparison agrees with the game-level
    mapping. A pair with no bet365 reference, or one that votes the other way, is not in
    the set and stays unverified (never priced, settled void)."""
    if first_is_over is None:
        return set()
    ref = {(_norm(r["player_name"]), r["stat"], r["line"]): 1 / r["price_dec"]
           for r in bet365_rows if r.get("market") == "prop" and r.get("player_name")}
    pairs = defaultdict(dict)
    for r in espn_rows:
        if r.get("market") == "prop" and r.get("kind") == "current" and r.get("player_name"):
            pairs[(_norm(r["player_name"]), r["stat"], r["line"])][r["selection"]] = r["price_dec"]
    out = set()
    for k, sides in pairs.items():
        if k not in ref or set(sides) != {"side0", "side1"}:
            continue
        p0, p1 = O.devig_multiplicative([sides["side0"], sides["side1"]])
        if (abs(p0 - ref[k]) < abs(p1 - ref[k])) == first_is_over:
            out.add(k)
    return out


def pair_key(r: dict) -> tuple:
    return (_norm(r.get("player_name") or ""), r.get("stat"), r.get("line"))


def _norm(name: str) -> str:
    return "".join(ch for ch in name.lower() if ch.isalpha())
