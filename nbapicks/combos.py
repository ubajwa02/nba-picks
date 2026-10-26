"""Combination props (points+rebounds+assists and friends), research only.

No feed we use lists prices for combinations, so these are projections, never picks:
nothing here can produce an EV, a qualified pick or a Discord alert. The probability comes
from the player's own recent games (empirical, so the correlation between the stats is
kept as it happened), each game's totals scaled to the minutes now expected."""
from __future__ import annotations

COMBOS = {"pra": ("pts", "reb", "ast"), "pr": ("pts", "reb"), "pa": ("pts", "ast"), "ra": ("reb", "ast")}
MIN_GAMES = 10
RECENT = 20


def combo_value(row: dict, combo: str) -> float | None:
    vals = [row.get(s) for s in COMBOS[combo]]
    return None if any(v is None for v in vals) else float(sum(vals))


def combo_probability(games: list[dict], combo: str, line: float, side: str, expected_minutes: float | None = None) -> dict:
    """games: the player's box rows, oldest first. Returns probs for `side` ('over'/'under'),
    with pushes split out, or a refusal reason when the history is too thin."""
    played = [g for g in games if g.get("played") and (g.get("minutes") or 0) > 0 and combo_value(g, combo) is not None][-RECENT:]
    if len(played) < MIN_GAMES:
        return dict(ok=False, reason=f"only {len(played)} recent games, need {MIN_GAMES}", research_only=True)
    vals = []
    for g in played:
        v = combo_value(g, combo)
        if expected_minutes and g["minutes"] > 0:
            v *= min(expected_minutes / g["minutes"], 1.5)   # per-minute rate, capped so one short game cannot dominate
        vals.append(v)
    n = len(vals)
    over = sum(v > line for v in vals) / n
    push = sum(v == line for v in vals) / n
    under = 1 - over - push
    return dict(ok=True, n=n, prob=over if side == "over" else under, prob_push=push,
                mean=sum(vals) / n, research_only=True, priced=False)
