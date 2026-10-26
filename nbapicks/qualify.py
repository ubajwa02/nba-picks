"""Candidate qualification: data-quality gates, edge threshold, skeptic challenge,
market status and portfolio risk. Every candidate leaves with exactly one
decision (eligible | watch | hold | reject) and the reasons that produced it.

Order matters: a candidate is judged on data first, then price, then challenge,
then status, then portfolio. Nothing here forces a pick; an empty slate is a
valid outcome.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

from . import odds as O


@dataclass
class Candidate:
    game_id: str
    start_utc: str
    home: str
    away: str
    market: str            # ml | spread | total | prop
    selection: str         # home | away | over | under
    line: float | None
    price_dec: float | None
    book: str
    price_observed_at: str | None
    prob: float            # model P(win)
    push: float = 0.0      # model P(push)
    fair: float | None = None   # de-vigged market P(win) from the same book
    player_id: str | None = None
    player_name: str | None = None
    stat: str | None = None
    team: str | None = None       # the team a prop player is on / the side for ml/spread
    flags: str = ""
    model_version: str = ""
    inputs: dict = field(default_factory=dict)
    # outputs
    ev: float | None = None
    min_price_dec: float | None = None
    decision: str = "reject"
    reasons: list = field(default_factory=list)
    stake: float = 0.0
    category: str = "straight"

    @property
    def label(self) -> str:
        if self.market == "ml":
            return f"{self.home if self.selection == 'home' else self.away} ML"
        if self.market == "spread":
            t = self.home if self.selection == "home" else self.away
            return f"{t} {self.line:+g}"
        if self.market == "total":
            return f"{self.away}@{self.home} {self.selection.title()} {self.line:g}"
        return f"{self.player_name} {self.selection.title()} {self.line:g} {self.stat}"

    @property
    def side_team(self) -> str | None:
        if self.market in ("ml", "spread"):
            return self.home if self.selection == "home" else self.away
        return None


def _age_min(ts: str | None, now: dt.datetime) -> float | None:
    if not ts:
        return None
    t = dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return (now - t).total_seconds() / 60


def judge(c: Candidate, cfg: dict, now: dt.datetime, injuries: list[dict], key_minutes: dict[str, float],
          other_book_lines: list[float] | None = None) -> Candidate:
    q, mk = cfg["quality"], cfg["markets"].get(c.market, {})
    R = c.reasons
    if not mk.get("enabled", False):
        R.append("market disabled"); c.decision = "reject"; return c
    # ---- data quality (reject) ----
    if c.price_dec is None or c.price_dec <= 1:
        R.append("no valid price"); c.decision = "reject"; return c
    for bad in ("side_unverified", "price_assumed", "milestone_one_sided"):
        if bad in (c.flags or ""):
            R.append(f"price mapping not verified ({bad})"); c.decision = "reject"; return c
    age = _age_min(c.price_observed_at, now)
    if age is None or age > q["max_odds_age_minutes"]:
        R.append(f"stale odds ({'unknown age' if age is None else f'{age:.0f} min old'})"); c.decision = "reject"; return c
    tip = dt.datetime.fromisoformat(c.start_utc.replace("Z", "+00:00"))
    mins_to_tip = (tip - now).total_seconds() / 60
    if mins_to_tip <= 0:
        R.append("game started"); c.decision = "reject"; return c
    # ---- price ----
    c.ev = O.ev_with_push(c.prob, c.push, c.price_dec)
    c.min_price_dec = O.min_decimal_for_edge(c.prob, mk["min_ev"], c.push)
    hold = []
    if mins_to_tip < q["min_minutes_before_tip"]:
        hold.append(f"{mins_to_tip:.0f} min to tip")
    # ---- injuries ----
    unresolved = set(q["unresolved_statuses"])
    teams = {c.home, c.away}
    for inj in injuries:
        if inj.get("team") not in teams or inj.get("status") not in unresolved:
            continue
        mins = key_minutes.get(str(inj.get("player_id")))
        is_subject = c.market == "prop" and str(inj.get("player_id")) == str(c.player_id)
        if is_subject or (mins is not None and mins >= q["key_player_min_minutes"]):
            hold.append(f"unresolved injury: {inj['player_name']} ({inj['status']})")
    if c.market == "prop" and c.player_id and any(str(i.get("player_id")) == str(c.player_id) and i.get("status") == "Out" for i in injuries):
        R.append("player listed Out"); c.decision = "reject"; return c
    # ---- threshold ----
    if c.ev < mk["min_ev"]:
        R.append(f"EV {c.ev:+.1%} below {mk['min_ev']:.0%} threshold")
        c.decision = "watch" if c.ev >= mk["min_ev"] / 2 and not hold else "reject"
        return c
    # ---- skeptic challenge ----
    if c.fair is not None:
        cond = c.prob / max(1e-9, 1 - c.push)
        gap = cond - c.fair
        if abs(gap) > q["max_model_market_gap"]:
            hold.append(f"model {cond:.0%} vs market {c.fair:.0%}: gap {gap:+.0%} exceeds {q['max_model_market_gap']:.0%} (likely missing information)")
    if c.ev > q["max_ev"]:
        hold.append(f"EV {c.ev:+.1%} implausibly large")
    if other_book_lines and c.line is not None and c.market in ("spread", "total", "prop"):
        spread = max(other_book_lines + [c.line]) - min(other_book_lines + [c.line])
        if spread > q["max_line_disagreement"]:
            hold.append(f"books disagree on the line by {spread:g}")
    if hold:
        R.extend(hold); c.decision = "hold"; return c
    # ---- model status ----
    status = mk.get("status", "research")
    if status == "research":
        R.append(f"EV {c.ev:+.1%} clears threshold, but the {c.market} model is in research (not validated)")
        c.decision = "watch"; return c
    R.append(f"EV {c.ev:+.1%} >= {mk['min_ev']:.0%}; checks passed ({status})")
    c.decision = "eligible"
    return c


def portfolio(cands: list[Candidate], cfg: dict, probation: set | None = None) -> list[Candidate]:
    """Apply stake, per-game, same-side, daily and target caps to eligible straights.
    Highest EV first; anything cut is moved to 'hold' with the rule that cut it."""
    r, st, tg = cfg["risk"], cfg["stakes"], cfg["targets"]
    eligible = sorted([c for c in cands if c.decision == "eligible" and c.category == "straight"],
                      key=lambda c: -c.ev)
    per_game: dict[str, float] = {}
    sides: dict[tuple, int] = {}
    players: dict[str, int] = {}
    game_props: dict[str, int] = {}
    probation = probation or set()
    total = 0.0; n = 0
    for c in eligible:
        stake = st["straight"]
        key = (c.game_id, c.side_team or c.selection if c.market != "prop" else (c.player_id, c.stat))
        why = None
        if n >= tg["straight"]:
            why = f"daily straight target ({tg['straight']}) reached"
        elif per_game.get(c.game_id, 0) + stake > r["max_units_per_game"]:
            why = f"max {r['max_units_per_game']}u per game"
        elif c.market in ("ml", "spread") and sides.get((c.game_id, c.side_team), 0) >= r["max_same_team_exposures"]:
            why = "already exposed to this side (ML and spread are the same bet twice)"
        elif c.market == "prop" and players.get(c.player_id, 0) >= r.get("max_props_per_player", 1):
            why = "already have a pick on this player (his props are correlated)"
        elif c.market == "prop" and game_props.get(c.game_id, 0) >= r.get("max_props_per_game", 2):
            why = f"max {r.get('max_props_per_game', 2)} props per game (shared pace and blowout risk)"
        elif c.market in probation:
            why = f"{c.market} is on probation (demotion gate tripped; see data/research/queue.yaml)"
        elif total + stake > r["max_units_per_day"]:
            why = f"max {r['max_units_per_day']}u per day"
        if why:
            c.decision = "hold"; c.reasons.append(f"risk: {why}"); continue
        c.stake = stake
        per_game[c.game_id] = per_game.get(c.game_id, 0) + stake
        if c.market in ("ml", "spread"):
            sides[(c.game_id, c.side_team)] = sides.get((c.game_id, c.side_team), 0) + 1
        if c.market == "prop":
            players[c.player_id] = players.get(c.player_id, 0) + 1
            game_props[c.game_id] = game_props.get(c.game_id, 0) + 1
        total += stake; n += 1
    return cands
