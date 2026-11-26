"""Export everything the dashboard shows into site/data.json.

Every number comes from the ledger (data/ledger via Store), the pipeline's state files
(data/state), the research registry (data/research), the reports/ folder or config. Nothing
here invents a value: an empty ledger produces empty sections, a missing explanation field
is exported as "not available".

data.json sections (schema 2):
  meta          when it was built, last successful run per step, failures, staleness warnings
  today         today's games, qualified picks, current candidate set, decision counts, yesterday's record
  picks_by_day  today and the previous 5 slates: qualified, research parlays/lottos, all other candidates
  performance   one block per population (never summed): qualified, all model predictions (1u each),
                posted leans, Discord/external signals, actual wagers; plus calibration vs the market
  players       today's player props grouped by player, team model vs market, prop split cards
  valuation     model probability vs price for today, plus the EV help text
  backtests     every reports/backtest_*.json (docs/CONTRACTS.md section 2), passed through
  research      champion (game + props), experiments, gates, decisions, diagnostics, queue
  settings      config (no secrets), model versions, source health, runs, publications, team files
  compat        nothing; the top-level keys config/theoretical/paper/actual/published/providers are
                kept for older readers and tests

Theoretical results (model rows at recorded prices) and actual results (rows in the user's
wager log) are computed separately and never summed together.
"""
from __future__ import annotations

import datetime as dt
import glob
import json
import os
from collections import Counter, defaultdict

import yaml

from . import metrics as M
from .pipeline import Ctx, iso, jload, pause_state, slate_of
from .settle import net_profit

SITE = "site"
MAX_BYTES = 2_000_000
PREV_SLATES = 5            # picks_by_day: today + this many earlier slates
CAND_CAP = 300             # other model candidates kept per slate (sorted: watch, hold, reject; EV high first)
PLAYER_PROP_CAP = 30       # props kept per player
VALUATION_CAP = 300
SPLIT_CARD_CAP = 400
DOLLARS_PER_UNIT = 100
NA = "not available"
SETTLED = ("win", "loss", "push", "void", "cashout")

STAT_LABEL = {"pts": "Points", "reb": "Rebounds", "ast": "Assists", "fg3m": "Made Three-Pointers", "stl": "Steals",
              "blk": "Blocks", "tov": "Turnovers", "pra": "Points + Rebounds + Assists", "pr": "Points + Rebounds",
              "pa": "Points + Assists", "ra": "Rebounds + Assists"}
MARKET_LABEL = {"ml": "Moneyline", "spread": "Spread", "total": "Total Points", "prop": "Player Prop",
                "parlay": "Parlay", "lotto": "Lotto"}
DECISION_ORDER = {"eligible": 0, "watch": 1, "hold": 2, "reject": 3, "info": 4}

POPULATIONS = {
    "qualified": ("Qualified picks",
                  "Model predictions that passed every check (decision 'eligible'), each candidate counted once per "
                  "slate (latest version before tip), at the recommended stake."),
    "all_model": ("All model predictions (hypothetical, 1u each)",
                  "Every model candidate with a valid price and probability, whatever its decision, counted once per "
                  "slate (latest version before tip) and settled at 1 unit flat. Nobody bet these."),
    "posted_leans": ("Posted leans",
                     "Leans actually posted to the thread (data/ledger/posted_leans.jsonl), graded from final scores and "
                     "box scores, at their posted stake (1u unless stated)."),
    "signals": ("Discord / external signals",
                "Picks imported from data/manual/signals.csv (origin 'signal'), settled like model rows and tracked "
                "per provider. Never mixed into the model's record."),
    "wagers": ("Actual wagers",
               "Bets you logged in data/manual/wagers.csv. Real money; never added to any theoretical population. "
               "Dollar figures are the amounts in your log; units use the log's units column (or stake / $100)."),
}

VALUATION_HELP = [
    ["Model probability", "The model's estimated chance that the bet wins, from its own inputs (team ratings for "
                          "game markets, the player's recent distribution for props). For spreads, totals and props "
                          "a separate push probability is kept."],
    ["Implied probability", "1 / decimal price. It includes the book's margin (vig), so the two sides of a market "
                            "add up to more than 100%."],
    ["De-vigged (fair) probability", "The book's two-sided prices rescaled so they add up to 100%. Shown only when "
                                     "both sides were quoted. It is the market's estimate without the margin."],
    ["Expected value (EV)", "EV per 1 unit staked = p × (d − 1) − (1 − p), where p is the model probability and d "
                            "the decimal price. When a push is possible, the push probability returns the stake and "
                            "is left out of both terms."],
    ["Minimum price for edge", "The lowest decimal price at which EV still clears the market's EV threshold. A "
                               "price shorter than this is not worth taking under the model."],
    ["Pushes and voids", "A push (the result lands exactly on the line) or a void (player did not play, game "
                         "cancelled) returns the stake: zero units, counted apart from wins and losses."],
    ["Price basis", "'conservative' means the book did not label which side each price belonged to; the worse of "
                    "the two prices was used, so EV and ROI are lower bounds."],
    ["What +EV means", "+EV is a theoretical expectation under the model, not a guarantee. It is only as good as the "
                       "model's probability, which has not yet passed its validation gates."],
]


# ------------------------------------------------------------------ small helpers
def _yaml(path, default):
    try:
        with open(path) as fh:
            return yaml.safe_load(fh) or default
    except (FileNotFoundError, yaml.YAMLError):
        return default


def _jsonl(path, tail: int | None = None) -> list[dict]:
    if not os.path.exists(path):
        return []
    out = []
    with open(path) as fh:
        lines = [l for l in fh.read().splitlines() if l.strip()]
    for l in lines[-tail:] if tail else lines:
        try:
            out.append(json.loads(l))
        except ValueError:
            continue
    return out


def _text(path, cap=20000):
    try:
        with open(path) as fh:
            return fh.read()[:cap]
    except FileNotFoundError:
        return None


def _t(s):
    if not s:
        return None
    try:
        s = str(s).replace("Z", "+00:00")
        t = dt.datetime.fromisoformat(s)
        return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)
    except ValueError:
        return None


def _minutes(a, b):
    ta, tb = _t(a) if isinstance(a, str) else a, _t(b) if isinstance(b, str) else b
    return round((tb - ta).total_seconds() / 60, 1) if ta and tb else None


def american(dec):
    if not dec or dec <= 1:
        return None
    return round((dec - 1) * 100) if dec >= 2 else -round(100 / (dec - 1))


def _r(x, n=4):
    return None if x is None else round(float(x), n)


def stat_label(stat):
    return STAT_LABEL.get(stat or "", (stat or "").replace("_", " ").title() or "Stat")


def pick_label(market, selection, line, stat=None, home=None, away=None, category="straight", n_legs=0):
    """Readable label: 'Over 19.5 Points', 'BOS Moneyline', 'BOS -3.5 Spread', 'Over 224.5 Total Points'."""
    if category in ("parlay", "lotto"):
        return f"{category.title()} ({n_legs} legs)"
    side = {"over": "Over", "under": "Under"}.get(selection)
    ln = f"{line:g}" if isinstance(line, (int, float)) else (str(line) if line is not None else "")
    team = home if selection == "home" else away if selection == "away" else selection
    if market == "prop":
        return f"{side or 'Unverified side'} {ln} {stat_label(stat)}".replace("  ", " ").strip()
    if market == "ml":
        return f"{team} Moneyline"
    if market == "spread":
        sl = f"{line:+g}" if isinstance(line, (int, float)) else ln
        return f"{team} {sl} Spread"
    if market == "total":
        return f"{side or selection} {ln} Total Points"
    return " ".join(str(x) for x in (market, selection, ln) if x)


def _hn(o, unit="games"):
    if not isinstance(o, dict) or not o.get("n"):
        return NA
    h, n = o.get("h") or 0, o["n"]
    return f"{h}/{n} {unit} ({round(100 * h / n)}%)"


def _num(x, d=1):
    return NA if x is None else f"{float(x):.{d}f}"


def explain_items(market: str, ex) -> list | None:
    """'Why this pick?' lines built only from inputs.explain. Missing fields say 'not available'."""
    if not isinstance(ex, dict) or not ex:
        return None
    if market == "prop":
        season = ex.get("season") if isinstance(ex.get("season"), dict) else {}
        last5 = ex.get("last5")
        vs = ex.get("vs_opp") if isinstance(ex.get("vs_opp"), dict) else None
        od = ex.get("opp_def") if isinstance(ex.get("opp_def"), dict) else None
        tm = ex.get("teammates_out")
        inj_present = "injury_status" in ex
        items = [
            ["Season average", f"{_num(season.get('avg'))} (n={season.get('n')} games)" if season.get("avg") is not None else NA],
            ["Last 5 games (newest first)", ", ".join(_num(v, 0) if float(v).is_integer() else _num(v) for v in last5)
             if isinstance(last5, list) and last5 else NA],
            ["Last 10 average", _num(ex.get("last10_avg"))],
            ["Cleared this exact line", _hn(ex.get("line_hits"))],
            ["Cleared this line, last 10", _hn(ex.get("line_hits_last10"))],
            ["Vs this opponent", (_hn(vs) + (f", avg {_num(vs.get('avg'))}" if vs.get("avg") is not None else ""))
             if vs and vs.get("n") else NA],
            ["Expected minutes", (_num(ex.get("exp_minutes")) + (f" ({ex['minutes_basis']})" if ex.get("minutes_basis") else ""))
             if ex.get("exp_minutes") is not None else NA],
            ["Role", {"starter": "Starter", "bench": "Bench"}.get(ex.get("role"), NA)],
            ["Teammates out", (", ".join(map(str, tm)) or "none listed") if isinstance(tm, list) else NA],
            ["Injury status", (ex.get("injury_status") or "none reported") if inj_present else NA],
            ["Opponent defence rank", (f"{od.get('rank')} of {od.get('teams')}"
                                       + (f" ({_num(od.get('allowed_pg'))} allowed per game)" if od.get("allowed_pg") is not None else ""))
             if od and od.get("rank") is not None else NA],
            ["Model mean / sd", f"{_num(ex.get('mean'))} / {_num(ex.get('sd'))}" if ex.get("mean") is not None else NA],
        ]
        if ex.get("flags"):
            items.append(["Flags", ", ".join(map(str, ex["flags"]))])
        return items
    hm, am_ = ex.get("home_missing"), ex.get("away_missing")
    return [
        ["Model home margin", _num(ex.get("mu_margin"))],
        ["Model total points", _num(ex.get("mu_total"))],
        ["Home rest (days)", NA if ex.get("home_rest") is None else str(ex["home_rest"])],
        ["Away rest (days)", NA if ex.get("away_rest") is None else str(ex["away_rest"])],
        ["Home players missing", (", ".join(map(str, hm)) or "none listed") if isinstance(hm, list) else NA],
        ["Away players missing", (", ".join(map(str, am_)) or "none listed") if isinstance(am_, list) else NA],
        ["Availability adjustment", _num(ex.get("availability_adj"), 2)],
    ]


def ckey(r: dict) -> tuple:
    """Candidate identity inside a slate: a moved game line is the same candidate; a prop line is not."""
    if r["category"] != "straight":
        return (r["category"], tuple(sorted(l.get("key") or l.get("label") or "" for l in (r.get("legs") or []))))
    return (r["origin"], r["provider"], r["game_id"], r["market"], r["selection"], r["player_id"] or r["player"],
            r["stat"], r["book"], r["line"] if r["market"] == "prop" else None)


def latest_per_key(rows: list[dict], before_tip_only: bool = False) -> list[dict]:
    """Keep the latest version of each candidate per slate (created before tip when the tip is known)."""
    groups = defaultdict(list)
    for r in rows:
        groups[(r["slate"], ckey(r))].append(r)
    out = []
    for vs in groups.values():
        vs.sort(key=lambda r: r["created_at"] or "")
        tip = _t(vs[0].get("start_utc"))
        pre = [v for v in vs if not tip or (_t(v["created_at"]) or tip) <= tip]
        if before_tip_only and not pre:
            continue
        out.append(dict((pre or vs)[-1], versions=len(vs)))
    return out


# ------------------------------------------------------------------ performance math
def kpis(rows: list[dict]) -> dict:
    """W-L-P-V, pending, hit rate, units staked/net, $ at $100/u, ROI. Pending is never a loss.
    Units staked and ROI use win/loss (and cash-out) rows only: pushes and voids return the stake."""
    c = Counter(r.get("result") or "pending" for r in rows)
    scored = [r for r in rows if r.get("result") in ("win", "loss", "cashout")]
    staked = sum(r.get("stake") or 0 for r in scored)
    net = sum(r.get("net") or 0 for r in rows if r.get("result") in SETTLED)
    w, l = c.get("win", 0), c.get("loss", 0)
    has_dollars = rows and all(r.get("dollars") is not None for r in rows if r.get("result") in SETTLED)
    dollars = sum(r["dollars"] for r in rows if r.get("result") in SETTLED) if has_dollars else net * DOLLARS_PER_UNIT
    return dict(n=len(rows), wins=w, losses=l, pushes=c.get("push", 0), voids=c.get("void", 0), cashouts=c.get("cashout", 0),
                pending=sum(v for k, v in c.items() if k not in SETTLED), settled=sum(c.get(k, 0) for k in SETTLED),
                hit_rate=_r(w / (w + l)) if w + l else None, units_staked=_r(staked), net_units=_r(net),
                net_dollars=_r(dollars, 2), roi=_r(net / staked) if staked else None)


def block(rows: list[dict], population: str) -> dict:
    title, desc = POPULATIONS[population]
    k = kpis(rows)
    scored = sorted([r for r in rows if r.get("result") in ("win", "loss", "cashout")], key=lambda r: r.get("slate") or "")
    ci = None
    if len(scored) > 1:
        ci = M.roi_summary([r.get("net") or 0 for r in scored], [r.get("stake") or 0 for r in scored]).get("roi_ci")

    def by(key):
        g = defaultdict(list)
        for r in rows:
            g[key(r) or "unknown"].append(r)
        return {str(a): kpis(v) for a, v in sorted(g.items(), key=lambda kv: str(kv[0]))}

    wl = [r for r in rows if r.get("result") in ("win", "loss") and r.get("prob") is not None]
    buckets = M.calibration([float(r["prob"]) for r in wl], [int(r["result"] == "win") for r in wl], 10) if wl else []
    dd = M.drawdown([r.get("net") or 0 for r in scored]) if scored else {}
    return dict(population=population, title=title, description=desc, **k, roi_ci=list(ci) if ci else None,
                by_market=by(lambda r: r.get("market") or r.get("category")),
                by_category=by(lambda r: r.get("category") or "straight"),
                by_bucket=[dict(lo=_r(b["lo"], 2), hi=_r(b["hi"], 2), n=b["n"], predicted=_r(b["predicted"]),
                                observed=_r(b["observed"]), ci=[_r(x) for x in b["ci"]]) for b in buckets],
                by_day=by(lambda r: r.get("slate")),
                by_model_version=by(lambda r: r.get("model_version")),
                advanced=dict(max_drawdown_units=_r(dd.get("max_drawdown")), longest_losing_streak=dd.get("longest_losing_streak")),
                # compat for older readers: n counts every settled row
                summary=dict(n=k["settled"], units=k["net_units"], staked=k["units_staked"], roi=k["roi"]))


def _perf_row(r: dict, flat: bool) -> dict:
    """A prediction row as a performance row: stake 1u flat (flat=True) or its recommended stake."""
    stake = 1.0 if flat else (r.get("stake_units") or 1.0)
    res = r["status"]
    if res not in SETTLED:
        net = None
    elif r["category"] == "straight":
        net = net_profit(res, r.get("_price") or r["price_dec"], stake) if r.get("price_dec") else 0.0
    else:   # parlay/lotto: the settled event's net, rescaled to this stake
        ev_stake = r.get("_event_stake") or r.get("stake_units") or 1.0
        net = (r.get("_event_net") or 0.0) * stake / ev_stake
    return dict(result=res, stake=stake, net=net, prob=r.get("prob"), market=r.get("market") or r["category"],
                category=r["category"], slate=r["slate"], model_version=r.get("model_version"), pred_id=r["pred_id"],
                label=r.get("label"), provider=r.get("provider"))


# ------------------------------------------------------------------ export
TOP_PLAYERS = 10
TOP_PROPS_PER_PLAYER = 3
_JUNK_FLAGS = ("milestone", "side_unverified")


def top_players(plist: list[dict], n: int = TOP_PLAYERS, per: int = TOP_PROPS_PER_PLAYER) -> list[dict]:
    """The dashboard's player view: the n players whose best prop is the most likely to hit,
    each with their `per` best. A prop counts only with a verified two-sided price (no milestone
    ladders, no side-unverified rows), a price of at least 1.50 decimal (not a near-certain
    one-sided quote) and at least 5 of the last 10 games to judge the line against."""
    out = []
    for p in plist:
        good = [x for x in p["props"]
                if x["prob"] is not None and (x["price_dec"] or 0) >= 1.5
                and not any(k in f for f in x["flags"] for k in _JUNK_FLAGS)
                and ((x.get("line_hits_last10") or {}).get("n") or 0) >= 5]
        good.sort(key=lambda x: -x["prob"])
        if good:
            out.append(dict(p, props=good[:per], props_total=len(good), capped=len(good) > per, best_prob=good[0]["prob"]))
    out.sort(key=lambda p: -p["best_prob"])
    return out[:n]


def export(ctx: Ctx, out_dir: str = SITE, max_bytes: int = MAX_BYTES) -> dict:
    s, tz, now = ctx.store, ctx.tz, ctx.now
    cfg = ctx.cfg
    today = ctx.today.isoformat()
    max_age = (cfg.get("quality") or {}).get("max_odds_age_minutes")
    games = {g["game_id"]: g for g in s.q("SELECT * FROM games")}
    events = s.q("SELECT * FROM pred_events")
    settled = {e["pred_id"]: e for e in events if e["type"] == "settled"}
    published = {e["pred_id"] for e in events if e["type"] == "published"}
    paper_ids = {e["pred_id"] for e in events if e["type"] == "note" and "paper_record" in (e["data"] or "")}
    preds = s.q("SELECT * FROM predictions")
    by_id = {p["pred_id"]: p for p in preds}
    team_of = {}
    for b in s.q("SELECT player_id, team, observed_at FROM player_games ORDER BY observed_at"):
        if b.get("team"):
            team_of[str(b["player_id"])] = b["team"]
    last = jload(f"{ctx.root}/state/last_predict.json", {}) or {}

    def row(p):
        g = games.get(p["game_id"]) or {}
        e = settled.get(p["pred_id"])
        try:
            inputs = json.loads(p["inputs"] or "{}") or {}
        except ValueError:
            inputs = {}
        legs = None
        if p["legs"]:
            try:
                legs = []
                for l in json.loads(p["legs"]):
                    lp = by_id.get(l.get("pred_id"))
                    lg = games.get(lp["game_id"]) if lp else None
                    lab = pick_label(lp["market"], lp["selection"], lp["line"], lp["stat"], (lg or {}).get("home"),
                                     (lg or {}).get("away")) if lp else l.get("label")
                    if lp and lp["player_name"]:
                        lab = f"{lp['player_name']} {lab}"
                    legs.append(dict(pred_id=l.get("pred_id"), label=lab, price_dec=_r(l.get("price_dec")),
                                     price_american=american(l.get("price_dec")), prob=_r(l.get("prob")),
                                     key="|".join(str(x) for x in ((lp or {}).get("game_id"), (lp or {}).get("market"),
                                                                  (lp or {}).get("selection"), (lp or {}).get("player_id"),
                                                                  (lp or {}).get("stat"), (lp or {}).get("line")))
                                     if lp else l.get("label")))
            except ValueError:
                legs = None
        flags = inputs.get("quality_flags") or []
        if isinstance(flags, str):
            flags = [f for f in flags.split(",") if f]
        basis = inputs.get("price_basis")
        price = p["price_dec"] if p["price_dec"] and p["price_dec"] > 1 else None
        team = None
        if p["market"] in ("ml", "spread"):
            team = g.get("home") if p["selection"] == "home" else g.get("away") if p["selection"] == "away" else None
        elif p["market"] == "prop" and p["player_id"]:
            team = team_of.get(str(p["player_id"]))
        opp = (g.get("away") if team == g.get("home") else g.get("home") if team == g.get("away") else None) if team and g else None
        status = e["result"] if e else "pending"
        stake = p["stake_units"] if (p["decision"] == "eligible" and p["stake_units"]) else 1.0
        ev_data = {}
        if e and e["data"]:
            try:
                ev_data = json.loads(e["data"]) or {}
            except ValueError:
                ev_data = {}
        ret = None
        if status in SETTLED:
            if p["category"] == "straight":
                ret = net_profit(status, price, stake) if price else 0.0
            else:
                ret = (e["net_units"] or 0.0) * stake / (ev_data.get("stake") or p["stake_units"] or 1.0)
        ex = inputs.get("explain")
        lab = pick_label(p["market"], p["selection"], p["line"], p["stat"], g.get("home"), g.get("away"), p["category"],
                         len(legs or []))
        slate = slate_of(g["start_utc"], tz) if g.get("start_utc") else slate_of(p["created_at"], tz)
        return dict(
            pred_id=p["pred_id"], created_at=p["created_at"], run_id=p["run_id"], slate=slate, origin=p["origin"],
            provider=p["provider"], category=p["category"], game_id=p["game_id"],
            matchup=f"{g.get('away', '?')} @ {g.get('home', '?')}" if g else None, home=g.get("home"), away=g.get("away"),
            start_utc=g.get("start_utc"), game_status=g.get("status"),
            market=p["market"], market_label=MARKET_LABEL.get(p["market"] or p["category"], p["market"]),
            selection=p["selection"], line=p["line"], player=p["player_name"], player_id=p["player_id"], stat=p["stat"],
            stat_label=stat_label(p["stat"]) if p["stat"] else None, team=team, opponent=opp, label=lab,
            book=p["book"], price_dec=_r(price), price_american=american(price), price_observed_at=p["price_observed_at"],
            price_age_at_pred_min=_minutes(p["price_observed_at"], p["created_at"]),
            prob=_r(p["prob"]), prob_push=_r(p["prob_push"]), implied=_r(1 / price) if price else None,
            fair=_r(inputs.get("fair")), ev=_r(p["ev"]), min_price_dec=_r(p["min_price_dec"]),
            min_price_american=american(p["min_price_dec"]), edge_threshold=p["edge_threshold"],
            price_basis=basis, conservative=basis == "conservative" or "conservative_price" in flags,
            quality_flags=flags, decision=p["decision"], reason=p["reason"], model_version=p["model_version"],
            market_status=inputs.get("status"), published=p["pred_id"] in published, status=status,
            stake_units=p["stake_units"], hyp_stake_units=stake,
            to_win_units=_r(stake * (price - 1)) if price else None,
            return_units=_r(ret), return_dollars=_r(ret * DOLLARS_PER_UNIT, 2) if ret is not None else None,
            legs=legs, why=explain_items(p["market"], ex), explain_present=isinstance(ex, dict) and bool(ex),
            _event_net=e["net_units"] if e else None,
            _event_stake=ev_data.get("stake"), _price=price)

    rows = [row(p) for p in preds]
    model_rows = [r for r in rows if r["origin"] == "model"]

    # ---------------- performance populations (never summed)
    qual = latest_per_key([r for r in model_rows if r["decision"] == "eligible"], before_tip_only=True)
    allm = latest_per_key([r for r in model_rows if r["prob"] is not None and r["price_dec"]
                           and (r["category"] != "straight" or r["selection"] in ("home", "away", "over", "under"))],
                          before_tip_only=True)
    pop_rows = dict(qualified=[_perf_row(r, flat=False) for r in qual], all_model=[_perf_row(r, flat=True) for r in allm])
    sc = live_scorecard(ctx, games, preds, settled,
                        "reports/scorecard_live.md" if out_dir == SITE else f"{out_dir}/scorecard_live.md")
    leans = ((sc or {}).get("leans") or {}).get("rows") or []
    pop_rows["posted_leans"] = [dict(result=l.get("result") or "pending", stake=l.get("stake", 1.0), net=l.get("net_units"),
                                     prob=l.get("prob"), market=l.get("market"), category="straight", slate=l.get("slate"),
                                     model_version=l.get("source"), label=l.get("label")) for l in leans]
    sig = [r for r in rows if r["origin"] == "signal"]
    pop_rows["signals"] = [_perf_row(r, flat=False) for r in sig]
    wag = s.q("""SELECT w.*, e.result, e.net FROM wagers w
                 LEFT JOIN wager_events e ON e.wager_id = w.wager_id AND e.type = 'settled'
                 WHERE NOT EXISTS (SELECT 1 FROM wager_events c WHERE c.wager_id = w.wager_id AND c.type = 'corrected')""")
    from .pipeline import wager_slate
    wrows = []
    for w in wag:
        units = w["units"] if w["units"] else w["stake"] / DOLLARS_PER_UNIT
        k = units / w["stake"] if w["stake"] else 0
        wrows.append(dict(result=w["result"] or "pending", stake=units, net=w["net"] * k if w["net"] is not None else None,
                          dollars=w["net"], prob=None, market=w["market"], category="parlay" if w["legs"] else "straight",
                          slate=wager_slate(ctx, w, games), model_version=None, book=w["book"]))
    pop_rows["wagers"] = wrows
    performance = {k: block(v, k) for k, v in pop_rows.items()}
    performance["posted_leans"]["rows"] = sorted(leans, key=lambda l: l.get("slate") or "", reverse=True)[:300]
    performance["posted_leans"]["record"] = (sc.get("leans") or {}).get("record")
    by_prov = defaultdict(list)
    for r in pop_rows["signals"]:
        by_prov[r["provider"]].append(r)
    performance["signals"]["by_provider"] = {k: kpis(v) for k, v in sorted(by_prov.items())}
    # each signal next to the model's own view of the same bet (pred_events note 'model_compare')
    cmp_ev = {}
    for e in s.q("SELECT pred_id, data FROM pred_events WHERE type = 'note' AND data LIKE '%model_compare%' ORDER BY at"):
        cmp_ev[e["pred_id"]] = json.loads(e["data"])["model_compare"]
    vs = []
    for r, pr in zip(sig, pop_rows["signals"]):
        m = cmp_ev.get(r["pred_id"]) or {}
        vs.append(dict(provider=r.get("provider"), slate=r.get("slate"), label=pr.get("label") or r.get("label"),
                       price_dec=r.get("price_dec"), result=pr["result"], net=pr.get("net"),
                       model_prob=m.get("model_prob"), model_ev=m.get("model_ev_at_signal_price"),
                       model_decision=m.get("model_decision"), qualifies=m.get("independently_qualifies"),
                       model_after_signal=m.get("model_view_after_signal"), compared=bool(m)))
    performance["signals"]["vs_model"] = sorted(vs, key=lambda x: x["slate"] or "", reverse=True)[:300]
    performance["signals"]["model_agrees"] = kpis([pr for pr, v in zip(pop_rows["signals"], vs) if (v["model_ev"] or -1) >= 0])
    performance["signals"]["parse_status"] = {r["parse_status"]: r["n"] for r in
                                              s.q("SELECT parse_status, count(*) n FROM signals_raw GROUP BY parse_status")}
    # calibration vs the market: model log loss next to the de-vigged market's, where a fair price exists
    cal_mkt = {}
    for m in sorted({r["market"] for r in allm if r["category"] == "straight"}):
        xs = [r for r in allm if r["market"] == m and r["category"] == "straight" and r["status"] in ("win", "loss")]
        if not xs:
            continue
        ys = [int(r["status"] == "win") for r in xs]
        ps = [min(1.0, r["prob"] / max(1e-9, 1 - (r["prob_push"] or 0))) for r in xs]
        fx = [(r["fair"], y) for r, y in zip(xs, ys) if r["fair"] is not None]
        fp = [(p, y) for r, p, y in zip(xs, ps, ys) if r["fair"] is not None]
        cal_mkt[m] = dict(n=len(xs), logloss_model=_r(M.log_loss(ps, ys)), brier_model=_r(M.brier(ps, ys)),
                          n_with_fair=len(fx),
                          logloss_model_on_fair_rows=_r(M.log_loss([p for p, _ in fp], [y for _, y in fp])) if fp else None,
                          logloss_market=_r(M.log_loss([f for f, _ in fx], [y for _, y in fx])) if fx else None,
                          brier_market=_r(M.brier([f for f, _ in fx], [y for _, y in fx])) if fx else None)
    performance["calibration_vs_market"] = cal_mkt
    try:   # descriptive report; a malformed lean must not take the whole dashboard down
        performance["review"] = pick_review(ctx, games, preds, sc,
                                            "reports/pick_review.md" if out_dir == SITE else f"{out_dir}/pick_review.md")
    except Exception as ex:  # noqa: BLE001
        performance["review"] = dict(error=f"{type(ex).__name__}: {ex}"[:300])
    performance["scorecard"] = {k: v for k, v in (sc or {}).items() if k not in ("rows", "leans")}
    performance["notes"] = [
        "Each population is computed on its own and never added to another; actual wagers are real money, the rest are theoretical.",
        "A high hit rate is not an edge: favourites win often and still lose money at short prices. Look at ROI and calibration.",
        f"$ figures for theoretical populations are units × ${DOLLARS_PER_UNIT}. ROI = net units / units staked on win/loss rows.",
    ]

    # ---------------- picks by day (latest version per candidate per slate)
    latest = latest_per_key(model_rows)
    slates = sorted({r["slate"] for r in model_rows if r["slate"] <= today}, reverse=True)
    slates = [today] + [x for x in slates if x != today][:PREV_SLATES]
    picks_by_day = []
    for sl in slates:
        rs = [r for r in latest if r["slate"] == sl]
        quald = sorted([r for r in rs if r["category"] == "straight" and r["decision"] == "eligible"],
                       key=lambda r: -(r["ev"] or -9))
        research = [r for r in rs if r["category"] in ("parlay", "lotto")]
        other = sorted([r for r in rs if r["category"] == "straight" and r["decision"] != "eligible"],
                       key=lambda r: (DECISION_ORDER.get(r["decision"], 9), -(r["ev"] if r["ev"] is not None else -9)))
        picks_by_day.append(dict(
            date=sl, is_today=sl == today, qualified=quald, research=research, candidates=other[:CAND_CAP],
            candidates_total=len(other), candidates_capped=len(other) > CAND_CAP,
            counts=dict(Counter(r["decision"] for r in rs)), record=kpis([_perf_row(r, flat=False) for r in quald]),
            games=sorted({r["matchup"] for r in rs if r["matchup"]})))

    # ---------------- today
    tg = sorted([g for g in games.values() if slate_of(g["start_utc"], tz) == today], key=lambda g: g["start_utc"])
    if "pred_ids" in last and isinstance(last.get("pred_ids"), list):
        ids = set(last["pred_ids"])
        cur = [r for r in rows if r["pred_id"] in ids]
        cur_src = "last_predict.pred_ids"
    else:
        cur = [r for r in rows if last.get("run_id") and r["run_id"] == last.get("run_id")]
        cur_src = "last_predict.run_id"
    cur = [r for r in cur if r["slate"] == today and r["origin"] == "model"]
    prev = sorted({r["slate"] for r in model_rows if r["slate"] < today}, reverse=True)
    yday = prev[0] if prev else None
    games_today = []
    for g in tg:
        gc = [r for r in cur if r["game_id"] == g["game_id"]]
        games_today.append(dict(game_id=g["game_id"], start_utc=g["start_utc"], home=g["home"], away=g["away"],
                                status=g["status"], home_score=g["home_score"] if g["status"] != "scheduled" else None,
                                away_score=g["away_score"] if g["status"] != "scheduled" else None,
                                candidates=len(gc), qualified=sum(r["decision"] == "eligible" for r in gc)))
    today_sec = dict(
        date=today, games=games_today, game_count=len(tg),
        qualified=sorted([r for r in cur if r["decision"] == "eligible" and r["category"] == "straight"],
                         key=lambda r: -(r["ev"] or -9)),
        research=[r for r in cur if r["category"] in ("parlay", "lotto")],
        leans=sorted([l for l in leans if l.get("slate") == today], key=lambda l: l.get("label") or ""),
        # DraftKings links per scheduled game (site convenience; see espn.parse_dk_links)
        dk_links={gid: dict(event_url=v.get("event_url"), outcomes=v.get("outcomes") or [])
                  for gid, v in (jload(f"{ctx.root}/state/dk_links.json", {}) or {}).items()
                  if any(g["game_id"] == gid and g["status"] == "scheduled" for g in tg)},
        # DraftKings + FanDuel bet-slip links incl. props (The Odds API; empty without ODDS_API_KEY)
        book_links={gid: v.get("books") or {}
                    for gid, v in (jload(f"{ctx.root}/state/book_links.json", {}) or {}).items()
                    if any(g["game_id"] == gid and g["status"] == "scheduled" for g in tg)},
        candidate_ids=[r["pred_id"] for r in cur], candidate_count=len(cur), candidate_source=cur_src,
        decision_counts=dict(Counter(r["decision"] for r in cur)),
        predict_run=dict(run_id=last.get("run_id"), slate=last.get("slate"), model=last.get("model"),
                         games=last.get("games"), candidates_judged=last.get("candidates"), written=last.get("written"),
                         decisions=last.get("decisions"), eligible=last.get("eligible"), parlays=last.get("parlays")),
        overview=dict(date=yday,
                      qualified=kpis([x for x in pop_rows["qualified"] if x["slate"] == yday]) if yday else None,
                      all_model=kpis([x for x in pop_rows["all_model"] if x["slate"] == yday]) if yday else None))

    # ---------------- players and teams (today)
    trows = [r for r in latest if r["slate"] == today]
    players = defaultdict(list)
    for r in trows:
        if r["market"] == "prop" and r["category"] == "straight":
            players[r["player_id"] or r["player"]].append(r)
    plist = []
    for pid, rs in players.items():
        props = []
        for r in sorted(rs, key=lambda r: -(r["prob"] if r["prob"] is not None else -1)):
            ex = {}
            try:
                ex = (json.loads(by_id[r["pred_id"]]["inputs"] or "{}") or {}).get("explain") or {}
            except ValueError:
                pass
            age = _minutes(r["price_observed_at"], now)
            season = ex.get("season") if isinstance(ex.get("season"), dict) else {}
            props.append(dict(pred_id=r["pred_id"], stat=r["stat"], stat_label=r["stat_label"], line=r["line"],
                              side=r["selection"], label=r["label"], book=r["book"], price_dec=r["price_dec"],
                              price_american=r["price_american"], prob=r["prob"], implied=r["implied"], fair=r["fair"],
                              ev=r["ev"], decision=r["decision"], reason=r["reason"], status=r["status"],
                              line_hits=ex.get("line_hits"), line_hits_last10=ex.get("line_hits_last10"),
                              last5=ex.get("last5"), season_avg=season.get("avg"), season_n=season.get("n"),
                              vs_opp=ex.get("vs_opp"), exp_minutes=ex.get("exp_minutes"), role=ex.get("role"),
                              flags=sorted(set((ex.get("flags") or []) + (r["quality_flags"] or []))),
                              conservative=r["conservative"], price_age_min=age,
                              stale=(age is None or (max_age is not None and age > max_age))))
        r0 = rs[0]
        plist.append(dict(player=r0["player"], player_id=r0["player_id"], team=r0["team"], opponent=r0["opponent"],
                          matchup=r0["matchup"], game_id=r0["game_id"], start_utc=r0["start_utc"],
                          props=props[:PLAYER_PROP_CAP], props_total=len(props), capped=len(props) > PLAYER_PROP_CAP,
                          best_prob=max((p["prob"] for p in props if p["prob"] is not None), default=None)))
    plist = top_players(plist)
    teams = sorted([dict(game_id=r["game_id"], matchup=r["matchup"], market=r["market"], label=r["label"], line=r["line"],
                         book=r["book"], price_dec=r["price_dec"], price_american=r["price_american"], prob=r["prob"],
                         implied=r["implied"], fair=r["fair"], gap=_r(r["prob"] - r["fair"]) if r["prob"] is not None and r["fair"] is not None else None,
                         ev=r["ev"], decision=r["decision"])
                    for r in trows if r["market"] in ("ml", "spread", "total") and r["category"] == "straight"],
                   key=lambda x: (x["matchup"] or "", x["market"], x["label"]))
    cards = [c for c in (jload(f"{ctx.root}/state/split_cards_latest.json", {}) or {}).get("cards", []) if c.get("date") == today]
    players_sec = dict(max_odds_age_minutes=max_age, players=plist, teams=[], prop_split_cards=[],
                       prop_split_cards_total=0, prop_props_cap=TOP_PROPS_PER_PLAYER)

    # ---------------- valuation (today)
    val = sorted([r for r in trows if r["category"] == "straight" and r["price_dec"]],
                 key=lambda r: -(r["ev"] if r["ev"] is not None else -9))
    valuation = dict(rows=[dict(pred_id=r["pred_id"], label=r["label"], player=r["player"], team=r["team"], matchup=r["matchup"],
                                market=r["market"], market_label=r["market_label"], book=r["book"], price_dec=r["price_dec"],
                                price_american=r["price_american"], prob=r["prob"], prob_push=r["prob_push"],
                                implied=r["implied"], fair=r["fair"], ev=r["ev"], min_price_dec=r["min_price_dec"],
                                min_price_american=r["min_price_american"], edge_threshold=r["edge_threshold"],
                                price_basis=r["price_basis"], conservative=r["conservative"], decision=r["decision"])
                           for r in val[:VALUATION_CAP]],
                     total=len(val), capped=len(val) > VALUATION_CAP, help=VALUATION_HELP)

    # ---------------- backtests, research
    backtests = []
    for path in sorted(glob.glob("reports/backtest_*.json")):
        d = jload(path, None)
        if not isinstance(d, dict):
            backtests.append(dict(file=path, error="not a JSON object", runs=[]))
            continue
        backtests.append(dict(file=path, generated_at=d.get("generated_at"), commit=d.get("commit"),
                              runs=d.get("runs") if isinstance(d.get("runs"), list) else []))
    champ = jload("data/research/champion.json", {}) or {}
    research = dict(
        champion=dict(game={k: v for k, v in champ.items() if k != "props"}, props=champ.get("props")),
        experiments=_jsonl("data/research/experiments.jsonl")[-60:],
        gates=_yaml("config/gates.yaml", {}),
        decisions=_jsonl("data/research/decisions.jsonl")[-100:],
        diagnostics=_text("reports/diagnostics.md"),
        queue=_yaml("data/research/queue.yaml", {}),
        calibration=cal_mkt)

    # ---------------- settings, runs, meta
    runs_all = _jsonl(f"{ctx.root}/state/runs.jsonl")
    last_ok, last_fail = {}, {}
    for r in runs_all:
        for k, v in (r.get("steps") or {}).items():
            if v.get("status") == "completed":
                last_ok[k] = r.get("at")
            elif v.get("status") == "failed":
                last_fail[k] = dict(at=r.get("at"), error=str(v.get("error") or "")[:500])
    failing = {k: v for k, v in last_fail.items() if (v["at"] or "") > (last_ok.get(k) or "")}
    pub_cfg = cfg.get("publishing") or {}
    config_out = dict(timezone=tz, markets=cfg.get("markets"), stakes=cfg.get("stakes"), targets=cfg.get("targets"),
                      risk=cfg.get("risk"), quality=cfg.get("quality"), execution=cfg.get("execution"),
                      publishing={k: pub_cfg.get(k) for k in ("dry_run", "publish_paper", "max_prediction_age_minutes",
                                                              "research_watchlist") if k in pub_cfg},
                      dry_run=pub_cfg.get("dry_run"), publish_paper=pub_cfg.get("publish_paper"))
    mv = defaultdict(lambda: dict(n=0, first=None, last=None))
    for p in preds:
        if p["origin"] != "model":
            continue
        v = mv[p["model_version"] or "unknown"]
        v["n"] += 1
        v["first"] = min(v["first"] or p["created_at"], p["created_at"])
        v["last"] = max(v["last"] or p["created_at"], p["created_at"])
    sc_rows = _yaml("team/scorecards.yaml", []) or []
    for x in sc_rows if isinstance(sc_rows, list) else []:
        if isinstance(x, dict):
            b = str(x.get("basis") or "") + str(x.get("evidence") or "")
            x["evidence_linked"] = "team/reviews" in b or "http" in b
    workflows = []
    for path in sorted(glob.glob(".github/workflows/*.yml")):
        w = _yaml(path, {}) or {}
        on = w.get("on", w.get(True, {})) or {}
        on = on if isinstance(on, dict) else {k: None for k in (on if isinstance(on, list) else [on])}
        workflows.append(dict(file=os.path.basename(path), name=w.get("name"),
                              schedule=[c.get("cron") for c in (on.get("schedule") or []) if isinstance(c, dict)],
                              manual="workflow_dispatch" in on,
                              push_paths=((on.get("push") or {}).get("paths") if isinstance(on.get("push"), dict) else None)))
    settings = dict(
        config=config_out,
        model_versions=dict(champion_game=champ.get("model_id"), champion_props=(champ.get("props") or {}).get("model_id"),
                            seen=dict(sorted(mv.items()))),
        source_health=ctx.health or {}, sources=_yaml("docs/sources.yaml", []),
        runs=[dict(at=r.get("at"), ok=r.get("ok"), steps={k: (v or {}).get("status") for k, v in (r.get("steps") or {}).items()},
                   errors={k: str(v.get("error"))[:300] for k, v in (r.get("steps") or {}).items() if (v or {}).get("error")},
                   notes=(r.get("notes") or [])[:3]) for r in runs_all[-30:]],
        publications=s.q("SELECT pub_id, kind, slate_date, at, status FROM publications ORDER BY at DESC LIMIT 60"),
        team=dict(roles=_yaml("team/roles.yaml", []), backlog=_yaml("team/backlog.yaml", []), scorecards=sc_rows,
                  scorecards_note="Self-reported scores; see team/reviews for evidence unless a row links its own."),
        commands=dict(trigger=(_text("ops/trigger") or "").splitlines()[:1], workflows=workflows),
        counts=dict(predictions=len(preds), games=len(games), odds_snapshots=s.one("SELECT count(*) n FROM odds")["n"],
                    injuries=s.one("SELECT count(*) n FROM injuries")["n"], wagers=len(wag), signals=len(sig)))

    warnings = []
    odds_today = s.one("SELECT max(observed_at) t FROM odds WHERE game_id IN (%s)" % ",".join("?" * len(tg)),
                       [g["game_id"] for g in tg]) if tg else None
    odds_age = _minutes(odds_today["t"], now) if odds_today and odds_today.get("t") else None
    upcoming = [g for g in tg if g["status"] == "scheduled"]
    stale_odds = bool(upcoming) and (odds_age is None or (max_age is not None and odds_age > max_age))
    if stale_odds:
        warnings.append(f"Odds for today's games are {'missing' if odds_age is None else f'{odds_age:.0f} minutes old'} "
                        f"(limit {max_age} min): today's prices may be out of date.")
    ingest_age = _minutes(last_ok.get("ingest"), now)
    stale_ingest = ingest_age is None or ingest_age > 360
    if stale_ingest:
        warnings.append("No successful ingest in the last 6 hours." if ingest_age is not None else "No successful ingest recorded.")
    failed_sources = {k: dict(consecutive_failures=v.get("consecutive_failures"), last_error=v.get("last_error"),
                              detail=v.get("last_error_detail"))
                      for k, v in (ctx.health or {}).items() if (v or {}).get("consecutive_failures")}
    if failed_sources:
        warnings.append("Failing data sources: " + ", ".join(sorted(failed_sources)) + ".")
    last_run = runs_all[-1] if runs_all else None
    if last_run and not last_run.get("ok"):
        warnings.append("The last run had a failed step: " + ", ".join(
            k for k, v in (last_run.get("steps") or {}).items() if (v or {}).get("status") == "failed") + ".")
    meta = dict(schema=2, generated_at=iso(now), today=today, timezone=tz, last_success=last_ok,
                last_failed=[dict(step=k, **v) for k, v in sorted(failing.items())],
                last_run=dict(at=last_run.get("at"), ok=last_run.get("ok")) if last_run else None,
                stale=dict(odds=stale_odds, odds_age_minutes=odds_age, max_odds_age_minutes=max_age,
                           ingest=stale_ingest, ingest_age_minutes=ingest_age, failed_sources=failed_sources),
                warnings=warnings, paused=pause_state(f"{ctx.root}/state") or ({"source": "config", "reason": "pause: true in config"} if ctx.cfg.get("pause") else None), dry_run=pub_cfg.get("dry_run"),
                market_status={m: (v or {}).get("status") for m, v in (cfg.get("markets") or {}).items()},
                caps=dict(slates=1 + PREV_SLATES, candidates_per_slate=CAND_CAP, props_per_player=PLAYER_PROP_CAP,
                          valuation_rows=VALUATION_CAP, split_cards=SPLIT_CARD_CAP, max_bytes=max_bytes),
                capped=[])

    # ---------------- compat keys (older readers, tests/test_e2e.py)
    pub_rows = [r for r in rows if r["published"]]
    paper_rows = [_perf_row(r, flat=True) for r in rows if r["pred_id"] in paper_ids]
    providers = {}
    for name, rs in by_prov.items():
        k = kpis(rs)
        providers[name] = dict(picks=k["n"], settled=k["settled"], wins=k["wins"], losses=k["losses"], units=k["net_units"],
                               roi=k["roi"], markets=sorted({r["market"] for r in rs if r["market"]}))

    def compat(rs):
        k = kpis(rs)
        return dict(summary=dict(n=k["settled"], units=k["net_units"], staked=k["units_staked"], roi=k["roi"]),
                    wins=k["wins"], losses=k["losses"], pushes=k["pushes"] + k["voids"], pending=k["pending"])

    from . import leans as LN
    all_t = sorted(sc.get("tickets") or [], key=lambda t: t["slate"], reverse=True)
    # rows = tickets that were posted; tracked = built and graded but never shown as picks (config tickets.post)
    tickets = dict(rows=[t for t in all_t if not t.get("tracked_only")][:300],
                   tracked=[t for t in all_t if t.get("tracked_only")][:300],
                   posting=bool((ctx.cfg.get("tickets") or {}).get("post", True)),
                   notes=LN.load_notes(ctx.root))
    data = dict(
        meta=meta, tickets=tickets, today=today_sec, picks_by_day=picks_by_day, performance=performance, players=players_sec,
        valuation=valuation, backtests=backtests, research=research, settings=settings,
        generated_at=meta["generated_at"], config=config_out,
        theoretical=compat([_perf_row(r, flat=False) for r in pub_rows]),
        paper=compat(paper_rows + pop_rows["posted_leans"]), actual=compat(wrows),
        published=[dict({k: v for k, v in r.items() if not k.startswith("_") and k != "why"}, result=r["status"])
                   for r in sorted(pub_rows, key=lambda r: r["created_at"], reverse=True)[:200]],
        providers=providers)
    _strip_private(data)
    blob = _fit(data, max_bytes)
    os.makedirs(out_dir, exist_ok=True)
    with open(f"{out_dir}/data.json", "w") as fh:
        fh.write(blob)
    return dict(path=f"{out_dir}/data.json", bytes=len(blob.encode()), published=len(pub_rows),
                capped=data["meta"]["capped"])


def _strip_private(o):
    if isinstance(o, dict):
        for k in [k for k in o if isinstance(k, str) and k.startswith("_")]:
            del o[k]
        for v in o.values():
            _strip_private(v)
    elif isinstance(o, list):
        for v in o:
            _strip_private(v)


def _dump(data):
    return json.dumps(data, default=str, separators=(",", ":"))


def _fit(data: dict, max_bytes: int) -> str:
    """Trim the longest lists until data.json fits; every trim is recorded in meta.capped for the page."""
    blob = _dump(data)
    steps = [("split cards", lambda n: _cap_list(data["players"], "prop_split_cards", n)),
             ("model candidates per slate", lambda n: [_cap_list(d, "candidates", n) for d in data["picks_by_day"]]),
             ("props per player", lambda n: [_cap_list(p, "props", n) for p in data["players"]["players"]]),
             ("valuation rows", lambda n: _cap_list(data["valuation"], "rows", n)),
             ("posted leans rows", lambda n: _cap_list(data["performance"]["posted_leans"], "rows", n)),
             ("experiments", lambda n: _cap_list(data["research"], "experiments", n))]
    for name, fn in steps:
        n = 200
        while len(blob.encode()) > max_bytes and n >= 0:
            fn(n)
            data["meta"]["capped"] = [c for c in data["meta"]["capped"] if c["what"] != name] + [dict(what=name, kept=n)]
            blob = _dump(data)
            n = n // 2 if n > 1 else -1
    return blob


def _cap_list(d: dict, key: str, n: int):
    if isinstance(d.get(key), list) and len(d[key]) > n:
        d[key] = d[key][:n]
        if "candidates" == key:
            d["candidates_capped"] = True
        if key == "props":
            d["capped"] = True


def live_scorecard(ctx: Ctx, games: dict, preds: list, settled: dict, report: str = "reports/scorecard_live.md") -> dict:
    """Refreshed on every export: settled predictions vs their probabilities, plus posted leans."""
    from . import scorecard as SCR, track
    box = {(r["game_id"], r["player_id"]): r for r in ctx.store.q("SELECT * FROM player_games")}
    leans = track.grade(track.load(ctx.root), games, box)
    sc = SCR.build(preds, settled)
    sc["leans"] = dict(record=track.record(leans), rows=leans)
    from . import leans as LN
    sc["tickets"] = LN.grade_tickets(LN.load_tickets(ctx.root), games, box, leans, ctx.cfg["stakes"])
    if report:
        os.makedirs(os.path.dirname(report), exist_ok=True)
        with open(report, "w") as fh:
            fh.write(SCR.markdown(sc, sc["leans"]["record"], leans))
    return sc


def pick_review(ctx: Ctx, games: dict, preds: list, sc: dict, report: str | None = None) -> dict:
    """Graded posted leans vs their pre-game inputs (descriptive; see nbapicks/review.py)."""
    from . import review as RV
    RV.archive_cards(ctx.root, (jload(os.path.join(ctx.root, "state", "split_cards_latest.json"), {}) or {}).get("cards") or [])
    odds = ctx.store.q("SELECT * FROM odds")
    rows = RV.enrich((sc or {}).get("leans", {}).get("rows") or [], preds, games, odds, RV.load_cards(ctx.root))
    rev = RV.build(rows, sc)
    if report:
        os.makedirs(os.path.dirname(report), exist_ok=True)
        with open(report, "w") as fh:
            fh.write(RV.markdown(rev, ctx.now.date().isoformat()))
    return rev
