"""Settlement rules. Pure functions; see tests/test_settle.py.

Rules follow common North American sportsbook practice (FanDuel house rules
summarised, not quoted - confirm against the book for edge cases):
- Game markets need the game to finish (overtime counts). Postponed or
  cancelled games are void.
- Spread/total landing exactly on the line is a push (stake returned).
- Player props: a player who does not play is void. A prop on a whole-number
  line that lands exactly is a push.
- Parlays: a losing leg loses the parlay. Void/push legs drop out (price 1.0).
  If every leg drops out the parlay is a push.
"""
from __future__ import annotations

from dataclasses import dataclass

WIN, LOSS, PUSH, VOID, PENDING = "win", "loss", "push", "void", "pending"
FINAL_STATES = {"final"}
VOID_STATES = {"postponed", "cancelled", "canceled", "suspended_void"}
MARKETS = {"ml", "spread", "total", "prop"}


@dataclass(frozen=True)
class GameResult:
    status: str               # scheduled | in_progress | final | postponed | cancelled
    home_score: int | None = None
    away_score: int | None = None


def settle_leg(market: str, selection: str, line: float | None, game: GameResult,
               stat_value: float | None = None, played: bool | None = None) -> str:
    """Return win/loss/push/void/pending for one straight bet.

    selection: ml/spread -> 'home'|'away'; total/prop -> 'over'|'under'.
    line: spread from the selection's point of view (e.g. -3.5), total line, prop line.
    """
    if market not in MARKETS:
        raise ValueError(f"unsupported market {market!r}")
    st = (game.status or "").lower()
    if st in VOID_STATES:
        return VOID
    if st not in FINAL_STATES:
        return PENDING
    if market == "prop":
        if played is False:
            return VOID
        if stat_value is None:
            return PENDING  # final game but stat not yet ingested
        return _over_under(selection, stat_value, line)
    if game.home_score is None or game.away_score is None:
        return PENDING
    margin = game.home_score - game.away_score
    if market == "ml":
        if margin == 0:
            raise ValueError("NBA games cannot finish tied")
        if selection not in ("home", "away"):
            raise ValueError(selection)
        won = margin > 0 if selection == "home" else margin < 0
        return WIN if won else LOSS
    if market == "spread":
        if line is None:
            raise ValueError("spread needs a line")
        side_margin = margin if selection == "home" else -margin
        adj = side_margin + line
        return WIN if adj > 0 else LOSS if adj < 0 else PUSH
    return _over_under(selection, game.home_score + game.away_score, line)


def _over_under(selection: str, value: float, line: float | None) -> str:
    if line is None:
        raise ValueError("over/under needs a line")
    if selection not in ("over", "under"):
        raise ValueError(selection)
    if value == line:
        return PUSH
    return WIN if (value > line) == (selection == "over") else LOSS


def net_profit(result: str, decimal_odds: float, stake: float) -> float | None:
    """Net units won/lost. None while pending."""
    if result == PENDING:
        return None
    if result == WIN:
        return stake * (decimal_odds - 1)
    if result == LOSS:
        return -stake
    return 0.0


def settle_parlay(legs: list[tuple[str, float]], stake: float) -> tuple[str, float | None, float]:
    """legs: [(result, decimal_odds)]. Returns (result, net, effective_decimal)."""
    if not legs:
        raise ValueError("empty parlay")
    results = [r for r, _ in legs]
    if LOSS in results:
        return LOSS, -stake, 0.0
    if PENDING in results:
        return PENDING, None, 0.0
    eff = 1.0
    for r, o in legs:
        if r == WIN:
            eff *= o
    if all(r in (PUSH, VOID) for r in results):
        return PUSH, 0.0, 1.0
    return WIN, stake * (eff - 1), eff
