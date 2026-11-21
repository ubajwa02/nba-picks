"""Daily picks, parlays and lotto: what the system posts each slate (research only).

Rule since 2026-11-17 (decision in data/research/decisions.jsonl, written before any result):

  why     The prop model has no measured skill beyond the book's price. On 10,174 graded DraftKings
          props it called 60-65% and they hit 54%; ranking by its win chance bought -150 to -190
          favourites at no edge (reports/red_week_2026-11.md). So the model no longer chooses picks.
  picks   A prop is a pick when FanDuel pays more than the fair price. The fair chance is the
          DraftKings two-way price for the same player, stat and line, from the same odds response,
          with the margin removed (optionally blended with the model: `leans.model_weight`, 0 until a
          model passes the gates). Edge = fair chance x FanDuel decimal price - 1. A pick needs
          edge >= markets.prop.min_ev (the pre-registered 5%), a FanDuel price of at least
          `min_decimal`, a quote no older than quality.max_odds_age_minutes, at least
          quality.min_minutes_before_tip to tip, and no injury or source problem on the player or
          game. Ranked by edge, one per player, `per_game` per game, at most `max_leans`.
          The pick is recorded and graded at the FanDuel price.
  refresh Later runs before tip re-check each posted pick (nbapicks/pipeline.refresh_leans) and record
          whether it still stands. A pick is never deleted or regraded: the note is advice for anyone
          who has not bet yet.
  parlays 2 picks-pool legs from different games whose combined edge is >= markets.parlay.min_ev.
  lotto   3..max_legs legs from different games paying >= min_decimal with edge >= its min_ev.
          With `leans.tickets_require_edge: false` the older always-post rule applies instead.
Fewer than the ceiling, or nothing at all, is normal: every ceiling is a maximum and the reason for a
shortfall is stored and shown.
"""
from __future__ import annotations

import datetime as dt
import itertools
import json
import math
import os

from . import odds as O
from . import propsides as PS
from . import track
from .odds import decimal_to_american
from .settle import settle_parlay
from .store import stable_id

TICKETS = "posted_tickets.jsonl"
NOTES = "ticket_notes.json"
SOURCE = "fd_price_edge"
BOOK, REF_BOOK = "FanDuel", "DraftKings"
BOOK_KEY, REF_KEY = "fanduel", "draftkings"
# Reasons on a prediction row that stop a pick whatever the price says. The model's own price reasons
# (stale ESPN quote, EV below threshold, model-market gap) do not: the price comes from the odds feed.
BLOCKERS = ("unresolved injury", "listed Out", "injury report", "critical source failing", "player not",
            "player not identified", "game started", "market disabled")


def _inputs(p: dict) -> dict:
    x = p.get("inputs")
    if isinstance(x, str):
        try:
            return json.loads(x or "{}")
        except ValueError:
            return {}
    return x or {}


def _t(s: str) -> dt.datetime:
    return dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))


def norm_name(s: str) -> str:
    from .sources.oddsapi import norm_name as n
    return n(s)


def blockers(p: dict) -> list[str]:
    """The parts of a prediction row's reason that stop a pick (injuries, identity, sources)."""
    parts = [x.strip() for x in str(p.get("reason") or "").split(";") if x.strip()]
    return [x for x in parts if any(k in x for k in BLOCKERS)]


def lean_label(p: dict) -> str:
    name = p.get("player_name") or p.get("player") or "?"
    return f"{name} {p['selection'][0]}{p['line']:g} {p['stat']}"


def blend(fair: float, model: float | None, w: float) -> float:
    """Market fair chance moved toward the model by weight w, on the log-odds scale. w = 0 is the market."""
    if not w or model is None or not 0 < model < 1 or not 0 < fair < 1:
        return fair
    z = (1 - w) * math.log(fair / (1 - fair)) + w * math.log(model / (1 - model))
    return 1 / (1 + math.exp(-z))


def price_edges(preds: list[dict], quotes: list[dict], cfg: dict, now_iso: str, blocks: dict | None = None) -> list[dict]:
    """Every FanDuel prop side that can be compared with the reference book, with its edge and any
    reason it cannot be a pick. One row per (game, player, stat, line, side); not yet filtered or ranked.

    preds: this run's prop prediction rows (they carry player ids, tip times and injury holds).
    quotes: two-way quotes {game_id, book, player (normalised), stat, line, over, under, at}.
    blocks: {"players": {player_id: reason}, "games": {game_id: [reasons]}} from the current injury report
            (pipeline.lean_blocks); a prediction row's reason only names injuries when its own EV cleared.
    """
    blocks = blocks or {}
    q, lc = cfg["quality"], cfg["leans"]
    w = float(lc.get("model_weight") or 0.0)
    now = _t(now_iso)
    who: dict[tuple, dict] = {}                 # (game, player, stat) -> identity, blockers, model rows by line/side
    for p in preds:
        if p.get("market") != "prop" or p.get("category", "straight") != "straight" or not p.get("stat"):
            continue
        name = p.get("player_name") or p.get("player") or ""
        k = (str(p["game_id"]), norm_name(name), p["stat"])
        d = who.setdefault(k, dict(player_id=None, player_name=name, start_utc=p.get("start_utc"), blockers=[], model={},
                                   model_version=p.get("model_version")))
        if p.get("player_id") and not d["player_id"]:
            d["player_id"] = str(p["player_id"])
        for b in blockers(p):
            if b not in d["blockers"]:
                d["blockers"].append(b)
        if p.get("prob") is not None and p.get("line") is not None and p.get("selection") in ("over", "under"):
            d["model"][(float(p["line"]), p["selection"])] = p["prob"]
    by: dict[tuple, dict] = {}
    for r in quotes:
        by.setdefault((str(r["game_id"]), r["player"], r["stat"], float(r["line"])), {})[r["book"]] = r
    out = []
    for (gid, player, stat, line), books in sorted(by.items()):
        fd, ref = books.get(BOOK_KEY), books.get(REF_KEY)
        if not fd or not ref:
            continue                            # no FanDuel market, or nothing to measure it against at this line
        if not PS.plausible_pair(fd["over"], fd["under"]) or not PS.plausible_pair(ref["over"], ref["under"]):
            continue                            # an alt-ladder rung or a broken pair: not a two-way market
        d = who.get((gid, player, stat))
        fair_over = O.devig_multiplicative([ref["over"], ref["under"]])[0]
        for side, fair in (("over", fair_over), ("under", 1 - fair_over)):
            mp = (d or {}).get("model", {}).get((line, side))
            prob = blend(fair, mp, w)
            price = fd[side]
            why = []
            if not d or not d["player_id"]:
                why.append("player not matched to today's predictions")
            else:
                why += d["blockers"]
                for b in [(blocks.get("players") or {}).get(d["player_id"])] + list((blocks.get("games") or {}).get(gid) or []):
                    if b and b not in why:
                        why.append(b)
                start = d.get("start_utc")
                if not start or _t(start) <= now:
                    why.append("game started")
                elif (_t(start) - now).total_seconds() / 60 < q["min_minutes_before_tip"]:
                    why.append("too close to tip")
            age = (now - _t(fd["at"])).total_seconds() / 60 if fd.get("at") else None
            if age is None or age > q["max_odds_age_minutes"]:
                why.append("FanDuel quote is stale")
            if price < lc["min_decimal"]:
                why.append(f"FanDuel price under {decimal_to_american(lc['min_decimal'])}")
            edge = O.ev_binary(prob, price)
            if edge > q["max_ev"]:
                why.append(f"edge {edge:+.1%} implausibly large (likely a stale or wrong quote)")
            out.append(dict(game_id=gid, player=player, player_id=(d or {}).get("player_id"),
                            player_name=(d or {}).get("player_name") or player.title(), stat=stat, line=line, selection=side,
                            price_dec=price, prob=prob, fair=fair, edge=edge, ref_price_dec=ref[side], model_prob=mp,
                            model_version=(d or {}).get("model_version"), quoted_at=fd.get("at"), why_not=why))
    return out


def pick_leans(preds: list[dict], cfg: dict, slate: str, now_iso: str, quotes: list[dict] | None = None,
               pool: bool = False, taken_games=(), taken_players=(), blocks: dict | None = None) -> list[dict]:
    """The posted picks: FanDuel props whose price beats the fair price by the threshold, ranked by edge.
    pool=True returns the wider list parlays and the lotto draw from (edge >= `pool_min_edge`).
    Without quotes there is no FanDuel price to post at, so there are no picks."""
    lc = cfg["leans"]
    min_edge = float(lc.get("pool_min_edge", 0.025)) if pool else float(cfg["markets"]["prop"]["min_ev"])
    per_game_max = 4 if pool else int(lc.get("per_game", 1))
    cap = 18 if pool else int(lc["max_leans"])
    out, per_game, players = [], {}, {str(x) for x in taken_players}
    for g in taken_games:
        per_game[str(g)] = per_game.get(str(g), 0) + 1
    rows = [r for r in price_edges(preds, quotes or [], cfg, now_iso, blocks) if not r["why_not"] and r["edge"] >= min_edge]
    for r in sorted(rows, key=lambda r: (-r["edge"], r["player"], r["stat"], r["selection"])):
        if len(out) >= cap:
            break
        if r["player_id"] in players or per_game.get(r["game_id"], 0) >= per_game_max:
            continue
        players.add(r["player_id"])
        per_game[r["game_id"]] = per_game.get(r["game_id"], 0) + 1
        out.append(dict(game_id=r["game_id"], label=lean_label(r), line=r["line"], market="prop", player_id=r["player_id"],
                        price_american=decimal_to_american(r["price_dec"]), prob=round(r["prob"], 4), selection=r["selection"],
                        slate=slate, source=SOURCE, stake=cfg["stakes"]["straight"], stat=r["stat"],
                        book=BOOK, edge=round(r["edge"], 4), fair=round(r["fair"], 4), ref_book=REF_BOOK,
                        ref_price_american=decimal_to_american(r["ref_price_dec"]), model=r["model_version"],
                        model_prob=None if r["model_prob"] is None else round(r["model_prob"], 4), quoted_at=r["quoted_at"]))
    return out


def best_edge_note(preds: list[dict], quotes: list[dict], cfg: dict, now_iso: str, blocks: dict | None = None) -> str:
    """One sentence on how close the slate came, shown when nothing (or little) is posted."""
    rows = price_edges(preds, quotes or [], cfg, now_iso, blocks)
    ok = [r for r in rows if not r["why_not"]]
    need = cfg["markets"]["prop"]["min_ev"]
    if not rows:
        return "No FanDuel prop could be compared with DraftKings on the same line today."
    if not ok:
        return f"{len(rows)} FanDuel prop prices were compared with DraftKings; none passed the injury, timing and price checks."
    b = max(ok, key=lambda r: r["edge"])
    return (f"{len(ok)} FanDuel prop prices were compared with DraftKings' fair price. The best edge was {b['edge']:+.1%} "
            f"({lean_label(b)} at {decimal_to_american(b['price_dec']):+d}); a pick needs {need:+.0%}.")


def _combos(legs: list[dict], sizes) -> list[dict]:
    out = []
    for k in sizes:
        for combo in itertools.combinations(legs, k):
            if len({c["game_id"] for c in combo}) < k:
                continue                  # same-game legs are dependent: never combined
            dec = O.parlay_decimal([O.american_to_decimal(c["price_american"]) for c in combo])
            p = math.prod(c["prob"] for c in combo)
            out.append(dict(legs=combo, price_dec=dec, prob=p, ev=O.ev_binary(p, dec)))
    return out


def _leg(l: dict) -> dict:
    keys = ("lean_id", "label", "prob", "price_american", "game_id", "market", "selection", "line", "player_id", "stat", "slate")
    extra = {k: l[k] for k in ("book", "edge", "fair") if l.get(k) is not None}
    return {k: l.get(k) for k in keys} | {"stake": 1.0} | extra


def build_tickets(legs: list[dict], cfg: dict, slate: str, exclude_players=()) -> tuple[list[dict], list[str]]:
    """Parlays and one lotto from different-game legs of the pool, no leg used twice.

    With `leans.tickets_require_edge` (the default) a ticket is built only when its combined edge at the
    posted prices clears its market's min_ev (and the lotto its minimum payout), best edge first; otherwise
    nothing is posted and the note says why. With it off the older owner rule applies: always the daily
    target, highest win chance first, real edge shown even when negative."""
    legs = [dict(l, lean_id=l.get("lean_id") or track.lean_id(l)) for l in legs
            if str(l.get("player_id")) not in {str(x) for x in exclude_players}]
    notes, out = [], []
    want = cfg["targets"]["parlay"]
    lm, pm = cfg["markets"]["lotto"], cfg["markets"]["parlay"]
    strict = bool(cfg.get("leans", {}).get("tickets_require_edge", True))
    rank = (lambda c: (-c["ev"], -c["prob"])) if strict else (lambda c: -c["prob"])
    if len(legs) < 2:
        if strict:
            return [], ["No parlays or lotto today: fewer than two props had a FanDuel price far enough above the fair price."]
        return [], [f"Only {len(legs)} eligible prop{'s' if len(legs) != 1 else ''} today, so no parlays or lotto could be built."]
    pairs = sorted([c for c in _combos(legs, (2,)) if not strict or c["ev"] >= pm["min_ev"]], key=rank)
    used, chosen = set(), []
    for c in pairs:
        ids = {l["lean_id"] for l in c["legs"]}
        if ids & used:
            continue
        chosen.append(c); used |= ids
        if len(chosen) >= want:
            break
    if len(chosen) < want:
        notes.append((f"{len(chosen)} of {want} parlays posted: no other pair of different-game props had a combined edge of "
                      f"{pm['min_ev']:.0%} or more at FanDuel's prices.") if strict else
                     f"Only {len(chosen)} of {want} parlays could be built from today's eligible props.")
    lotto = []
    lotto_legs = [l for l in legs if l["lean_id"] not in used]      # a lotto never reuses a parlay leg
    for size in range(min(lm["max_legs"], len(lotto_legs)), 2, -1):
        cs = _combos(lotto_legs, (size,))
        big = [c for c in cs if c["price_dec"] >= lm["min_decimal"] and (not strict or c["ev"] >= lm["min_ev"])]
        if strict:
            if big:
                lotto = sorted(big, key=rank)[:cfg["targets"]["lotto"]]
                break
            continue
        if big or cs:
            lotto = sorted(big or cs, key=rank)[:cfg["targets"]["lotto"]]
            if not big:
                notes.append(f"The lotto pays {lotto[0]['price_dec']:.1f}x, under the usual {lm['min_decimal']:g}x target, "
                             f"because no larger payout was available from today's eligible props.")
            break
    if not lotto:
        notes.append((f"No lotto today: no set of 3 or more different-game props paid {lm['min_decimal']:g}x with a combined edge of "
                      f"{lm['min_ev']:.0%} or more.") if strict else
                     "No lotto today: fewer than 3 eligible props in different games left after the parlays (no player is reused).")
    for kind, tickets in (("parlay", chosen), ("lotto", lotto)):
        for c in tickets:
            ids = sorted(l["lean_id"] for l in c["legs"])
            out.append(dict(ticket_id=stable_id(slate, kind, *ids), slate=slate, kind=kind, price_dec=round(c["price_dec"], 4),
                            price_american=decimal_to_american(c["price_dec"]), prob=round(c["prob"], 4), ev=round(c["ev"], 4),
                            stake=cfg["stakes"][kind], research=True, legs=[_leg(l) for l in c["legs"]]))
    return out, notes


# ---- ledger ----
def load_tickets(root: str) -> list[dict]:
    p = os.path.join(root, "ledger", TICKETS)
    return [json.loads(x) for x in open(p) if x.strip()] if os.path.exists(p) else []


def replace_slate_tickets(root: str, slate: str, tickets: list[dict]) -> None:
    """Swap a slate's tickets built under a superseded rule (no research flag) for the current ones."""
    keep = [t for t in load_tickets(root) if t["slate"] != slate or t.get("research")]
    have = {t["ticket_id"] for t in keep}
    with open(os.path.join(root, "ledger", TICKETS), "w") as fh:
        for t in keep + [t for t in tickets if t["ticket_id"] not in have]:
            fh.write(json.dumps(t, sort_keys=True) + "\n")


def add_ticket(root: str, t: dict) -> bool:
    if any(x["ticket_id"] == t["ticket_id"] for x in load_tickets(root)):
        return False
    os.makedirs(os.path.join(root, "ledger"), exist_ok=True)
    with open(os.path.join(root, "ledger", TICKETS), "a") as fh:
        fh.write(json.dumps(t, sort_keys=True) + "\n")
    return True


def load_notes(root: str) -> dict:
    p = os.path.join(root, "state", NOTES)
    try:
        return json.load(open(p))
    except (FileNotFoundError, ValueError):
        return {}


def save_notes(root: str, slate: str, notes: list[str]) -> None:
    d = load_notes(root)
    d[slate] = notes
    os.makedirs(os.path.join(root, "state"), exist_ok=True)
    with open(os.path.join(root, "state", NOTES), "w") as fh:
        json.dump(d, fh, indent=1, sort_keys=True)


def grade_tickets(tickets: list[dict], games: dict, box: dict, leans: list[dict] | None = None, stakes: dict | None = None) -> list[dict]:
    """Each ticket's result from its legs graded against the final box scores: any loss loses, any pending
    waits, a pushed or void leg drops out of the payout (settle.settle_parlay)."""
    by_id = {(l.get("lean_id") or track.lean_id(l)): l for l in leans or []}
    out = []
    for t in tickets:
        # tickets written before legs carried their full definition: fill it from the posted lean
        t = dict(t, legs=[dict(by_id.get(l["lean_id"], {}), **l) if "market" not in l else l for l in t["legs"]])
        graded = track.grade(t["legs"], games, box)
        res = [(g["result"] or "pending", O.american_to_decimal(g["price_american"])) for g in graded]
        stake = (stakes or {}).get(t["kind"], t["stake"])      # history is restated at the current stake
        result, net, eff = settle_parlay(res, stake)
        legs = [dict(l, result=g["result"] or "pending", stat_value=g["stat_value"]) for l, g in zip(t["legs"], graded)]
        out.append(dict(t, legs=legs, stake=stake, result=result, net_units=net))
    return out
