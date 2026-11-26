"""The daily workflow: ingest -> predict/qualify -> publish -> settle -> recap -> export.

Run as `python -m nbapicks.pipeline <steps...>`. Each step is idempotent and
safe to re-run: ingestion de-duplicates, predictions are keyed by run, Discord
messages are keyed by slate, settlement events are written once per prediction.
A step that fails is recorded in data/state/runs.jsonl and the next step still
runs when it does not depend on it.
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import logging
import os
import traceback
from collections import defaultdict
from zoneinfo import ZoneInfo

from . import config as C
from . import discord, leans as LN, odds as O, parlay as PZ, propsides as PS, splitcard as SC, validate
from .history import read_csv
from .models.ratings import Game, RatingsModel, RatingsParams, add_rest_days
from .props import STATS, PropModel, _norm, pair_key, verified_pairs, verify_prop_sides
from .qualify import Candidate, judge, portfolio
from .settle import GameResult, settle_leg, net_profit, settle_parlay
from .sources import espn, moviodds, oddsapi
from .store import Store, stable_id

log = logging.getLogger("nbapicks")
DATA = "data"
STATE = f"{DATA}/state"
CHAMPION = f"{DATA}/research/champion.json"


def parse_t(s: str) -> dt.datetime:
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def iso(t: dt.datetime) -> str:
    return t.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def slate_of(start_utc: str, tz: str) -> str:
    return dt.datetime.fromisoformat(start_utc.replace("Z", "+00:00")).astimezone(ZoneInfo(tz)).date().isoformat()


def jload(path, default):
    try:
        with open(path) as fh:
            return json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def jsave(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(obj, fh, indent=1, sort_keys=True, default=str)
    os.replace(tmp, path)


class Ctx:
    def __init__(self, now: dt.datetime, cfg: dict, root: str = DATA, slate: dt.date | None = None):
        self.now, self.cfg, self.root = now, cfg, root
        self.store = Store(root)
        self.tz = cfg["timezone"]
        # slate overrides the local date for an early read of a later slate; prices stay real-time
        self.today = slate or now.astimezone(ZoneInfo(self.tz)).date()
        self.health = jload(f"{root}/state/source_health.json", {})
        self.seen = jload(f"{root}/state/odds_seen.json", {})
        self.athletes = jload(f"{root}/ref/athletes.json", {})
        self.notes: list[str] = []

    def ok(self, source, detail=""):
        h = self.health.setdefault(source, {})
        h.update(last_ok=iso(self.now), last_detail=detail, consecutive_failures=0)

    def fail(self, source, err):
        h = self.health.setdefault(source, {})
        h.update(last_error=iso(self.now), last_error_detail=str(err)[:300],
                 consecutive_failures=h.get("consecutive_failures", 0) + 1)
        self.notes.append(f"{source}: {str(err)[:120]}")

    def save_state(self):
        jsave(f"{self.root}/state/source_health.json", self.health)
        jsave(f"{self.root}/state/odds_seen.json", self.seen)
        jsave(f"{self.root}/ref/athletes.json", self.athletes)


# ------------------------------------------------------------------ ingest
def odds_key(r: dict) -> str:
    """Game lines move, so their key excludes the line. Props add it: a bet365 milestone ladder
    is several 'over' rows for one player/stat that must not overwrite each other (NBA-033)."""
    k = "|".join(str(r.get(k) or "") for k in ("game_id", "market", "selection", "player_id", "player_name", "stat", "book", "source", "kind"))
    return k + f"|{r.get('line')}" if r.get("market") == "prop" else k


def put_odds(ctx: Ctx, rows: list[dict]) -> int:
    """Store a snapshot only when line or price changed; always refresh last_seen."""
    n = 0
    now = iso(ctx.now)
    rows, bad = validate.validate_odds(rows)
    if bad:
        ctx.notes.append(f"odds_validation: {len(bad)} rows rejected, e.g. {bad[0]}")
    for r in rows:
        k = odds_key(r)
        prev = ctx.seen.get(k)
        sig = [r.get("line"), round(r["price_dec"], 4) if r.get("price_dec") else None, r.get("suspended")]
        if not prev or prev["sig"] != sig:
            rec = dict(r); rec["snap_id"] = stable_id(k, sig, now)
            ctx.store.put("odds", rec); n += 1
            ctx.seen[k] = dict(sig=sig, first_seen=now, last_seen=now, snap_id=rec["snap_id"])
        else:
            prev["last_seen"] = now
        if r.get("source_updated_at"):
            ctx.seen[k]["source_updated_at"] = r["source_updated_at"]
    return n


def book_links(ctx: Ctx) -> dict:
    """DraftKings + FanDuel bet-slip links (props included) from The Odds API, for the site only.

    Off without ODDS_API_KEY. Runs before export, after leans/tickets exist, and fetches only
    what today's posted picks need: for each game with a not-yet-started pick or parlay leg,
    only the markets those picks use, each (game, market) once per day. That keeps a typical
    slate around 10 credits, inside the free 500/month tier (see sources/oddsapi.py).
    """
    key = oddsapi.api_key()
    if not key:
        return dict(status="off")
    from . import leans as LN, track
    today = ctx.today.isoformat()
    need: dict[str, set] = defaultdict(set)
    rows = [l for l in track.load(ctx.root) if l.get("slate") == today]
    rows += [leg for t in LN.load_tickets(ctx.root) if t.get("slate") == today and not t.get("tracked_only")
             for leg in t.get("legs") or []]
    for r in rows:
        mk = oddsapi.market_key(r)
        if mk and r.get("game_id"):
            need[str(r["game_id"])].add(mk)
    games = {g["game_id"]: g for g in ctx.store.q("SELECT game_id, home, away, start_utc FROM games")}
    path = f"{ctx.root}/state/book_links.json"
    cache = {k: v for k, v in jload(path, {}).items() if v.get("slate") == today}
    todo = {}
    for gid, mks in need.items():
        g = games.get(gid)
        if not g or dt.datetime.fromisoformat(g["start_utc"].replace("Z", "+00:00")) <= ctx.now:
            continue
        miss = sorted(mks - set((cache.get(gid) or {}).get("markets") or []))
        if miss:
            todo[gid] = miss
    out = dict(games_needed=len(need), fetched=0)
    if not todo:
        return out
    try:
        ev = oddsapi.match_events(oddsapi.fetch_events(key), [games[g] for g in todo])
        for gid, miss in todo.items():
            if gid not in ev:
                continue
            g = games[gid]
            books = oddsapi.parse_event_links(oddsapi.fetch_event_links(key, ev[gid], miss), g["home"], g["away"])
            c = cache.setdefault(gid, dict(slate=today, markets=[], books={}))
            c["markets"] = sorted(set(c["markets"]) | set(miss))
            for book, outs in books.items():
                c["books"][book] = [o for o in c["books"].get(book, []) if oddsapi.market_key(o) not in miss] + outs
            c["observed_at"] = iso(ctx.now)
            out["fetched"] += 1
        ctx.ok("oddsapi_links", f"{out['fetched']} games")
    except Exception as e:
        ctx.fail("oddsapi_links", e)
    jsave(path, cache)
    return out


def ingest(ctx: Ctx) -> dict:
    now = iso(ctx.now)
    out = defaultdict(int)
    games = []
    for d in (ctx.today - dt.timedelta(days=1), ctx.today, ctx.today + dt.timedelta(days=1)):
        try:
            gs, _ = espn.parse_scoreboard(espn.fetch_scoreboard(d), now)
            games += [g for g in gs if g["season_type"] in ("regular", "post", "playin")]
            ctx.ok("espn_scoreboard")
        except Exception as e:
            ctx.fail("espn_scoreboard", e)
    games, bad = validate.validate_games(games)
    if bad:
        ctx.fail("espn_scoreboard", "; ".join(bad[:3]))
    for g in games:
        prev = ctx.store.one("SELECT status, home_score, away_score, start_utc FROM games WHERE game_id = ?", [g["game_id"]])
        if prev and (prev["status"], prev["home_score"], prev["away_score"], prev["start_utc"]) == (g["status"], g["home_score"], g["away_score"], g["start_utc"]):
            continue
        out["games_" + ctx.store.put("games", g)] += 1
    # box scores for finished games we have not stored yet
    for g in games:
        if g["status"] == "final" and not ctx.store.one("SELECT 1 FROM player_games WHERE game_id = ?", [g["game_id"]]):
            try:
                rows, bad = validate.validate_box_rows(espn.parse_boxscore(espn.fetch_summary(g["game_id"]), g["game_id"], now), g["game_id"])
                if bad:
                    out["box_rows_rejected"] += len(bad)
                    ctx.fail("espn_boxscore", "; ".join(bad[:3]))
                if rows:
                    out["box_rows"] += ctx.store.put_many("player_games", rows)["new"]
                    if not bad:
                        ctx.ok("espn_boxscore")
            except Exception as e:
                ctx.fail("espn_boxscore", e)
    upcoming = [g for g in games if g["status"] == "scheduled"
                and 0 < (dt.datetime.fromisoformat(g["start_utc"].replace("Z", "+00:00")) - ctx.now).total_seconds() < 36 * 3600]
    # DraftKings bet-slip links for the site cards (state, not ledger: overwritten each run)
    dk_path = f"{ctx.root}/state/dk_links.json"
    keep = {g["game_id"] for g in games}
    dk_links = {k: v for k, v in jload(dk_path, {}).items() if not keep or k in keep}
    for g in upcoming:
        try:
            core = espn.fetch_core_odds(g["game_id"])
            out["odds_snaps"] += put_odds(ctx, espn.parse_core_odds(core, g["game_id"], now))
            ctx.ok("espn_odds")
            try:
                lk = espn.parse_dk_links(core)
                if lk:
                    dk_links[g["game_id"]] = dict(lk, observed_at=now)
            except Exception as e:   # links are a convenience; never fail the odds step for them
                ctx.notes.append(f"dk_links {g['game_id']}: {e}")
        except Exception as e:
            ctx.fail("espn_odds", e)
        if slate_of(g["start_utc"], ctx.tz) == ctx.today.isoformat():
            try:
                pb = espn.fetch_propbets(g["game_id"], "100")
                for it in pb.get("items", []):
                    if "athlete" not in it:
                        continue   # team-level or special props carry no athlete; not priced
                    aid = it["athlete"]["$ref"].split("/athletes/")[1].split("?")[0]
                    if aid not in ctx.athletes:
                        ctx.athletes[aid] = espn.fetch_athlete_name(it["athlete"]["$ref"]) or aid
                out["prop_snaps"] += put_odds(ctx, espn.parse_propbets(pb, g["game_id"], "DraftKings", now, ctx.athletes))
                ctx.ok("espn_props")
            except Exception as e:
                ctx.fail("espn_props", e)
    jsave(dk_path, dk_links)
    try:
        inj, bad = validate.validate_injuries(espn.parse_injuries(espn.fetch_injuries(), now), ctx.now)
        if bad and not inj:
            raise ValueError("; ".join(bad[:3]))   # keep the previous injuries_latest.json; it goes stale and holds picks
        if bad:
            ctx.notes.append("espn_injuries: " + "; ".join(bad[:3]))
        jsave(f"{ctx.root}/state/injuries_latest.json", dict(observed_at=now, rows=inj))
        new = {}
        for r in inj:
            # one ledger row per distinct (player, status, report date, detail); re-listing is not new
            r["obs_id"] = stable_id(r["player_id"], r["status"], r["source_date"], r["detail"])
            if r["obs_id"] not in new and not ctx.store.one("SELECT 1 FROM injuries WHERE obs_id = ?", [r["obs_id"]]):
                new[r["obs_id"]] = r
        out["injury_obs"] = ctx.store.put_many("injuries", new.values())["new"]
        ctx.ok("espn_injuries", f"{len(inj)} listed")
    except Exception as e:
        ctx.fail("espn_injuries", e)
    try:
        from .signals import import_csv
        out.update({f"signals_{k}": v for k, v in import_csv(ctx).items() if v})
    except Exception as e:
        ctx.fail("signals_import", e)
    try:
        rows, problems = moviodds.parse(moviodds.fetch_nba(), games, now)
        out["bet365_snaps"] = put_odds(ctx, rows)
        ctx.ok("moviodds", f"{len(rows)} quotes; {len(problems)} unmapped")
    except Exception as e:
        ctx.fail("moviodds", e)
    out["odds_keys_pruned"] = prune_seen(ctx)
    failed = sorted({n.split(":")[0] for n in ctx.notes if n.split(":")[0] in CRITICAL_SOURCES})
    if "espn_scoreboard" in failed and not games:
        # nothing fresh to price: a prediction run on stale data must not look like a normal run
        raise IngestFailed(f"critical sources failed: {', '.join(failed)}")
    if failed:
        out["degraded"] = failed
    return dict(out)


CRITICAL_SOURCES = ("espn_scoreboard", "espn_odds", "espn_injuries")


class IngestFailed(RuntimeError):
    pass


def prune_seen(ctx: Ctx, keep_days: int = 2) -> int:
    """Forget de-dup keys of games that started more than keep_days ago (the snapshots
    stay in the ledger), so state/odds_seen.json does not grow all season."""
    cutoff = ctx.now - dt.timedelta(days=keep_days)
    start = {g["game_id"]: g["start_utc"] for g in ctx.store.q("SELECT game_id, start_utc FROM games")}
    drop = []
    for k, v in ctx.seen.items():
        gid = k.split("|")[0]
        t = start.get(gid)
        if (t and parse_t(t) < cutoff) or (not t and parse_t(v["last_seen"]) < cutoff):
            drop.append(k)
    for k in drop:
        del ctx.seen[k]
    return len(drop)


def boxes(ctx: Ctx, fetch_scoreboard=None, fetch_summary=None) -> dict:
    """Box scores for the final games of ctx.today's slate (--slate). Rows are append-only and
    de-duplicated by (game_id, player_id); a game whose box is already stored is not refetched."""
    fsb, fsum = fetch_scoreboard or espn.fetch_scoreboard, fetch_summary or espn.fetch_summary
    now, out = iso(ctx.now), defaultdict(int)
    games = []
    for d in (ctx.today, ctx.today + dt.timedelta(days=1)):   # late tips fall on the next UTC date
        try:
            games += [g for g in espn.parse_scoreboard(fsb(d), now)[0] if slate_of(g["start_utc"], ctx.tz) == ctx.today.isoformat()]
            ctx.ok("espn_scoreboard")
        except Exception as e:
            ctx.fail("espn_scoreboard", e)
    for g in {g["game_id"]: g for g in games}.values():
        prev = ctx.store.one("SELECT status, home_score, away_score FROM games WHERE game_id = ?", [g["game_id"]])
        if not prev or (prev["status"], prev["home_score"], prev["away_score"]) != (g["status"], g["home_score"], g["away_score"]):
            ctx.store.put("games", g); out["games_updated"] += 1
        if g["status"] != "final":
            out["not_final"] += 1
            continue
        if ctx.store.one("SELECT 1 FROM player_games WHERE game_id = ?", [g["game_id"]]):
            out["already_stored"] += 1
            continue
        try:
            rows, bad = validate.validate_box_rows(espn.parse_boxscore(fsum(g["game_id"]), g["game_id"], now), g["game_id"])
            if bad:
                out["box_rows_rejected"] += len(bad)
                ctx.fail("espn_boxscore", "; ".join(bad[:3]))
            if rows:
                out["box_rows"] += ctx.store.put_many("player_games", rows)["new"]
                out["box_games"] += 1
                if not bad:
                    ctx.ok("espn_boxscore")
        except Exception as e:
            ctx.fail("espn_boxscore", e)
    return dict(out)


def catchup(ctx: Ctx, days: int = 7) -> dict:
    """Refresh results and box scores for the last `days` slates, so a gap in the schedule
    (a paused or unreachable repo) does not leave finished games unsettled."""
    out = defaultdict(int)
    today = ctx.today
    for back in range(1, days + 1):
        ctx.today = today - dt.timedelta(days=back)
        for k, v in boxes(ctx).items():
            out[k] += v
    ctx.today = today
    return dict(out)


# ------------------------------------------------------------------ model inputs
def history_games(ctx: Ctx, seasons_back: int = 3) -> list[Game]:
    gs = {}
    files = sorted(glob.glob(f"{ctx.root}/history/games_*.csv.gz"))[-seasons_back:]
    for p in files:
        for r in read_csv(p):
            if r["status"] == "final":
                gs[r["game_id"]] = Game(r["game_id"], _day(r["start_utc"]), r["home"], r["away"], int(r["home_score"]), int(r["away_score"]))
    for r in ctx.store.q("SELECT * FROM games WHERE status = 'final'"):
        gs[r["game_id"]] = Game(r["game_id"], _day(r["start_utc"]), r["home"], r["away"], r["home_score"], r["away_score"])
    out = sorted(gs.values(), key=lambda g: (g.date, g.game_id))
    add_rest_days(out)
    return out


def _day(start_utc):
    return (dt.datetime.fromisoformat(start_utc.replace("Z", "+00:00")) - dt.timedelta(hours=6)).date()


def box_rows(ctx: Ctx, before: dt.date) -> list[dict]:
    dates = {}
    rows = []
    for p in sorted(glob.glob(f"{ctx.root}/history/box_*.csv.gz"))[-2:]:   # this and last season (props-v1 decays the prior one)
        g = {r["game_id"]: r["start_utc"] for r in read_csv(p.replace("box_", "games_"))}
        for r in read_csv(p):
            if r["game_id"] in g:
                r["date"] = g[r["game_id"]]; rows.append(r)
    st = {r["game_id"]: r["start_utc"] for r in ctx.store.q("SELECT game_id, start_utc FROM games")}
    for r in ctx.store.q("SELECT * FROM player_games"):
        r["date"] = st.get(r["game_id"], ""); rows.append(r)
    return [r for r in rows if r["date"] and _day(r["date"]) < before]


def safe_split_cards(ctx: Ctx, cands: list) -> list[dict]:
    """Split cards are watchlist info only: a failure is logged and must never block the run."""
    try:
        return prop_split_cards(ctx, cands)
    except Exception as e:
        log.warning("split cards failed: %s", e)
        return []


def prop_split_cards(ctx: Ctx, cands: list) -> list[dict]:
    """NBA-032 split cards for every offered prop line (watchlist info only; never changes
    a decision). Sides whose over/under order is unverified get an 'over' card with no price."""
    props = [c for c in cands if c.market == "prop" and c.player_id and c.stat in SC.STATS and c.line is not None]
    if not props:
        return []
    games, rows = {}, []
    for p in sorted(glob.glob(f"{ctx.root}/history/games_*.csv.gz")):
        games.update({r["game_id"]: r for r in read_csv(p)})
    games.update({g["game_id"]: g for g in ctx.store.q("SELECT game_id, start_utc, home, away FROM games")})
    for p in sorted(glob.glob(f"{ctx.root}/history/box_*.csv.gz")):
        rows.extend(read_csv(p))
    rows.extend(ctx.store.q("SELECT * FROM player_games"))
    idx = SC.build_index(rows, games)
    out, done = [], set()
    for c in props:
        side = c.selection if c.selection in ("over", "under") else "over"
        key = (c.player_id, c.stat, c.line, side)
        if key in done:
            continue
        done.add(key)
        hist = SC.history(idx, c.player_id, ctx.today)
        if not hist:
            continue
        team = hist[-1].team
        if team not in (c.home, c.away):
            continue  # traded or stale: the card would describe the wrong team
        priced = c.selection in ("over", "under")
        card = SC.card(idx, c.player_id, c.stat, c.line, side, ctx.today, c.away if team == c.home else c.home,
                       team == c.home, price_dec=c.price_dec if priced else None, fair_prob=c.fair if priced else None,
                       book=c.book if priced else None, price_observed_at=c.price_observed_at if priced else None)
        if card:
            card["game_id"] = c.game_id
            card["text"] = SC.card_text(card)
            out.append(card)
    return out


def champion_params() -> tuple[str, RatingsParams]:
    ch = jload(CHAMPION, {})
    p = ch.get("params") or {"total_trend": True}
    return ch.get("model_id", "ratings-v1-trend"), RatingsParams(**p)


def frozen_blend(cfg: dict, market: str) -> float | None:
    """Model weight of the frozen candidate that passed the gates for this market.
    Research markets use raw model probabilities (they are never published as picks);
    paper and live markets must use exactly what was validated."""
    if cfg["markets"][market]["status"] == "research":
        return None
    m = (jload(CHAMPION, {}).get("markets") or {}).get(market)
    if not m or "blend_w" not in m:
        raise RuntimeError(f"{market} is {cfg['markets'][market]['status']} but champion.json has no frozen blend_w for it")
    return float(m["blend_w"])


def blend(p: float, fair: float, w: float, push: float) -> float:
    from .backtest import _blend
    return _blend(p, fair, w, push)


def latest_quotes(ctx: Ctx, game_id: str) -> dict:
    """{(book, market, player, stat[, line]): {selection: row}} of current quotes with last_seen time.
    Props carry the line in the key: bet365 milestones ('20+', '25+') are all 'over' rows for one
    player/stat, and keying without the line kept only the last one, so no bet365 reference ever
    lined up with a DraftKings pair (NBA-033)."""
    out = defaultdict(dict)
    for k, v in ctx.seen.items():
        parts = k.split("|")
        if parts[0] != game_id or parts[8] != "current":
            continue
        row = ctx.store.one("SELECT * FROM odds WHERE snap_id = ?", [v["snap_id"]])
        if not row:
            continue
        row["last_seen"] = v["last_seen"]
        row["book"] = espn.canon_book(row["book"])
        row["as_of"] = v["last_seen"]
        src = v.get("source_updated_at") or row.get("source_updated_at")
        if src:
            try:
                if parse_t(src) < parse_t(row["as_of"]):
                    row["as_of"] = iso(parse_t(src))
            except ValueError:
                pass
        key = (row["book"], row["market"], row.get("player_id") or row.get("player_name"), row.get("stat"))
        if row["market"] == "prop":
            key += (row.get("line"),)
        out[key][row["selection"]] = row
    return out


# ------------------------------------------------------------------ predict
class PropEstimator:
    """One interface over the prop models, so predict() uses whichever model champion.json
    names under 'props' (props-v0 by default). Every estimate carries its explain block."""

    def __init__(self, ctx: Ctx, boxes: list[dict], games: dict):
        from .propexplain import Logs
        self.logs = Logs(boxes, games)
        ch = jload(f"{ctx.root}/research/champion.json", {}).get("props") or jload(CHAMPION, {}).get("props") or {}
        self.version = ch.get("model_id", "props-v0")
        self.v1 = None
        if self.version == "props-v1":
            try:
                from .models.props_v1 import PropModelV1
                self.v1 = PropModelV1(boxes, games, params=ch.get("params"))
            except Exception as e:   # a broken challenger must never stop the run: fall back, say so
                log.warning("props-v1 unavailable (%s); using props-v0", e)
                ctx.notes.append(f"props-v1 unavailable: {str(e)[:100]}")
                self.version = "props-v0"
        self.v0 = PropModel(boxes)

    def expected_minutes(self, pid):
        return self.v0.expected_minutes(pid)

    def predict(self, pid, stat, date, opp, home, teammates_out=(), injury_status=None):
        if pid is None or stat not in STATS:
            return None
        if self.v1 is not None:
            return self.v1.predict(pid, stat, date, opp, home, teammates_out=list(teammates_out), injury_status=injury_status)
        pp = self.v0.predict(pid, stat)
        if pp is None:
            return None
        return dict(pp, sd=pp["var"] ** 0.5)

    def prob(self, pred, line, side):
        return (self.v1 or self.v0).prob(pred, line, side)

    def explain(self, pred, pid, stat, line, side, date, opp, teammates_out_names, injury_status):
        from .propexplain import explain
        e = explain(self.logs, pid, stat, line, side, date, opp)
        if self.v1 is not None:
            try:
                e.update({k: v for k, v in (self.v1.explain_for_line(pred, pid, stat, line, side, date, opp) or {}).items()
                          if v is not None})
            except Exception as ex:
                e.setdefault("flags", []).append(f"explain_v1_failed: {str(ex)[:60]}")
            for k, v in (pred.get("explain") or {}).items():
                e.setdefault(k, v)
        e.update(mean=round(pred["mean"], 2), sd=round(pred.get("sd") or pred["var"] ** 0.5, 2),
                 exp_minutes=round(pred["minutes"], 1) if pred.get("minutes") is not None else None,
                 minutes_basis=(pred.get("explain") or {}).get("minutes_basis") or f"average of last {pred.get('games')} games",
                 teammates_out=teammates_out_names, injury_status=injury_status)
        return e


def _injury_maps(inj: list[dict]):
    """player_id -> status; team -> [(player_id, name)] listed Out or Doubtful."""
    status, out = {}, defaultdict(list)
    for r in inj:
        pid = str(r.get("player_id"))
        status[pid] = r.get("status")
        if r.get("status") in ("Out", "Doubtful") and r.get("team"):
            out[r["team"]].append((pid, r.get("player_name")))
    return status, out


def candidate_key(c: Candidate) -> tuple:
    return (c.game_id, c.market, c.selection, c.line, c.book, c.player_id or c.player_name, c.stat)


def version_id(c: Candidate) -> str:
    """A prediction is versioned by what it says, not by when it ran: a rerun on the same
    prices and probabilities writes nothing; a new price, line, probability or decision
    writes a new version."""
    return stable_id("v2", *candidate_key(c), round(c.price_dec, 4) if c.price_dec else None,
                     None if c.prob is None else round(c.prob, 3), c.decision, c.model_version, round(c.stake or 0, 2))


def predict(ctx: Ctx) -> dict:
    cfg = ctx.cfg
    slate = ctx.today.isoformat()
    run_id = f"run-{iso(ctx.now)}"
    games = [g for g in ctx.store.q("SELECT * FROM games WHERE status = 'scheduled'")
             if slate_of(g["start_utc"], ctx.tz) == slate and parse_t(g["start_utc"]) > ctx.now]
    model_id, params = champion_params()
    hist = history_games(ctx)
    model = RatingsModel(params).fit(hist, ctx.today)
    inj_doc = jload(f"{ctx.root}/state/injuries_latest.json", {})
    inj = inj_doc.get("rows", [])
    inj_age = (ctx.now - parse_t(inj_doc["observed_at"])).total_seconds() / 60 if inj_doc.get("observed_at") else None
    inj_status, inj_out = _injury_maps(inj)
    boxes = box_rows(ctx, ctx.today)
    gmap = {}
    for p in sorted(glob.glob(f"{ctx.root}/history/games_*.csv.gz"))[-2:]:
        gmap.update({r["game_id"]: r for r in read_csv(p)})
    gmap.update({g["game_id"]: g for g in ctx.store.q("SELECT game_id, start_utc, home, away FROM games")})
    pm = PropEstimator(ctx, boxes, gmap)
    name_pid = {_norm(r["player_name"]): str(r["player_id"]) for r in boxes if r.get("player_name")}
    key_minutes = {pid: m for pid in pm.v0.recent if (m := pm.expected_minutes(pid)) is not None}
    last_rest = {}
    for g in hist:
        last_rest[g.home] = g.date; last_rest[g.away] = g.date
    cands: list[Candidate] = []
    side_check = {}
    stale_inj = inj_age is None or inj_age > cfg["quality"].get("max_injury_age_minutes", 240)
    conflicts = validate.team_conflicts(inj, lambda p: pm.logs.team_of(p, ctx.today))
    failing = validate.failing_sources(ctx.health, CRITICAL_SOURCES, ctx.now)

    def prop_cand(g, book, sel, line, price, fair, basis, pid, name, stat, r, extra_flags=""):
        team = pm.logs.team_of(pid, ctx.today) if pid else None
        opp = (g["away"] if team == g["home"] else g["home"]) if team in (g["home"], g["away"]) else None
        mates = [(p, n) for p, n in inj_out.get(team, []) if p != str(pid)] if team else []
        flags = ",".join(x for x in [(r.get("flags") or "").replace("side_unverified", ""), extra_flags,
                                     "conservative_price" if basis == "conservative" else "",
                                     "injury_report_stale" if stale_inj else "",
                                     "player_team_unknown" if pid and not opp else ""] if x)
        pred = pm.predict(pid, stat, ctx.today, opp, team == g["home"], teammates_out=[p for p, _ in mates],
                          injury_status=inj_status.get(str(pid))) if pid and opp else None
        base = dict(game_id=g["game_id"], start_utc=g["start_utc"], home=g["home"], away=g["away"], market="prop",
                    selection=sel, line=line, price_dec=price, book=book, price_observed_at=r["as_of"],
                    player_id=pid, player_name=name, stat=stat, team=team, flags=flags, model_version=pm.version)
        if pred is None:
            c = Candidate(prob=None, **base)
            c.decision = "reject"
            c.reasons.append("no model estimate: " + ("player not matched to a team in this game" if pid and not opp
                                                       else "too little player history" if pid else "player not identified"))
            c.inputs = dict(snap_id=r["snap_id"], price_basis=basis, implied=round(1 / price, 4), quality_flags=flags.split(",") if flags else [])
            return c
        prob, push = pm.prob(pred, line, sel)
        ex = pm.explain(pred, pid, stat, line, sel, ctx.today, opp, [n for _, n in mates], inj_status.get(str(pid)))
        c = Candidate(prob=prob, push=push, fair=fair, **base)
        c.inputs = dict(snap_id=r["snap_id"], price_basis=basis, implied=round(1 / price, 4), explain=ex,
                        quality_flags=[f for f in flags.split(",") if f] + ex.get("flags", []))
        c = judge(c, cfg, ctx.now, inj, key_minutes)
        if c.decision in ("eligible", "watch"):
            why = None
            if "low_sample" in ex.get("flags", []):
                why = "fewer than 10 games this season (low sample)"
            elif not 0.03 <= prob <= 0.97:
                why = f"model probability {prob:.0%} is implausibly extreme for a prop"
            elif stale_inj:
                why = "injury report missing or stale"
            elif pid and str(pid) in conflicts:
                why = "injury report lists {} but box scores list {}".format(*conflicts[str(pid)])
            elif failing:
                why = "critical source failing: " + ", ".join(failing)
            if why:
                c.decision = "hold"; c.reasons.append(why)
        return c

    for g in games:
        quotes = latest_quotes(ctx, g["game_id"])
        espn_props = [r for (b, m, *_), sides in quotes.items() if m == "prop" and b == "DraftKings" for r in sides.values()]
        b365_props = [r for (b, m, *_), sides in quotes.items() if m == "prop" and b == "bet365" for r in sides.values()]
        first_is_over, agree, n = verify_prop_sides(espn_props, b365_props, min_n=8)
        ok_pairs = verified_pairs(espn_props, b365_props, first_is_over)
        lad = PS.ladders(b365_props)
        labelled = defaultdict(int)
        implausible = 0
        hr = (ctx.today - last_rest[g["home"]]).days if g["home"] in last_rest else None
        ar = (ctx.today - last_rest[g["away"]]).days if g["away"] in last_rest else None
        pred = model.predict(g["home"], g["away"], hr, ar) if model.ready() else None
        name_pid_g = dict(name_pid, **{_norm(r["player_name"]): str(r["player_id"]) for r in
                                       sorted(espn_props, key=lambda r: str(r.get("player_id")))   # deterministic
                                       if r.get("player_name") and r.get("player_id")})
        for qkey, sides in quotes.items():
            book, market, player, stat = qkey[:4]
            if book not in cfg["execution"]["reference_books"]:
                continue
            if market in ("ml", "spread", "total"):
                if pred is None:
                    continue
                need = ("home", "away") if market != "total" else ("over", "under")
                if not all(s in sides for s in need):
                    continue
                fair = (O.devig_power if market == "ml" else O.devig_multiplicative)([sides[s]["price_dec"] for s in need])
                others = [r["line"] for (b2, m2, *_), s2 in quotes.items() if m2 == market and b2 != book
                          for sel, r in s2.items() if sel == need[0] and r.get("line") is not None]
                for s, f in zip(need, fair):
                    r = sides[s]
                    p, push = RatingsModel.prob(pred, market, s, r["line"])
                    w = frozen_blend(cfg, market)
                    if w is not None:
                        p = blend(p, f, w, push)
                    c = Candidate(game_id=g["game_id"], start_utc=g["start_utc"], home=g["home"], away=g["away"], market=market,
                                  selection=s, line=r["line"], price_dec=r["price_dec"], book=book, price_observed_at=r["as_of"],
                                  prob=p, push=push, fair=f, flags=r.get("flags") or "", model_version=model_id,
                                  inputs=dict(mu_margin=round(pred["mu_margin"], 2), mu_total=round(pred["mu_total"], 1),
                                              sigma_margin=pred["sigma_margin"], sigma_total=pred["sigma_total"],
                                              home_rest=hr, away_rest=ar, games_in_fit=pred["n_games"], snap_id=r["snap_id"],
                                              price_basis="labelled", implied=round(1 / r["price_dec"], 4),
                                              explain=dict(mu_margin=round(pred["mu_margin"], 2), mu_total=round(pred["mu_total"], 1),
                                                           home_rest=hr, away_rest=ar,
                                                           home_missing=[nm for _, nm in inj_out.get(g["home"], [])],
                                                           away_missing=[nm for _, nm in inj_out.get(g["away"], [])],
                                                           availability_adj=None)))
                    cands.append(judge(c, cfg, ctx.now, inj, key_minutes, others))
            elif market == "prop" and book == "bet365":
                # A bet365 milestone 'N+' is stored as over N-0.5: the side is explicit, no mapping needed.
                r = sides.get("over")
                if r is None or stat not in STATS:
                    continue
                pid = name_pid_g.get(_norm(r.get("player_name") or ""))
                cands.append(prop_cand(g, book, "over", r["line"], r["price_dec"], None, "labelled", pid,
                                       r.get("player_name"), stat, r))
            elif market == "prop" and book == "DraftKings":
                if set(sides) != {"side0", "side1"} or stat not in STATS:
                    continue
                r0 = sides["side0"]
                line = r0["line"]
                if not PS.plausible_pair(r0["price_dec"], sides["side1"]["price_dec"]):
                    implausible += 1     # not a two-way market at this line: not priced
                    continue
                label = None
                if pair_key(r0) in ok_pairs:
                    label = "side0" if first_is_over else "side1"
                else:
                    label = PS.label_pair(r0["price_dec"], sides["side1"]["price_dec"],
                                          lad.get((_norm(r0.get("player_name") or ""), stat)), line)
                labelled[label is not None] += 1
                priced = PS.price_sides(sides, label)
                for sel in ("over", "under"):
                    price, fair, basis = priced[sel]
                    src = sides[label] if label and sel == "over" else sides[{"side0": "side1", "side1": "side0"}[label]] if label else r0
                    cands.append(prop_cand(g, book, sel, line, price, fair, basis, str(player) if player else None,
                                           r0.get("player_name"), stat, src))
        side_check[g["game_id"]] = dict(first_is_over=first_is_over, agreement=agree, n=n, pairs_verified=len(ok_pairs),
                                        pairs_labelled=labelled[True], pairs_conservative=labelled[False],
                                        pairs_implausible=implausible)
    if failing:
        for c in cands:
            if c.decision in ("eligible", "watch"):
                c.decision = "hold"
                c.reasons.append("critical source failing: " + ", ".join(failing))
    # best price per (game, market, selection, player, stat) across reference books and lines
    best = {}
    rank = {"eligible": 4, "watch": 3, "hold": 2, "reject": 1}
    for c in cands:
        k = (c.game_id, c.market, c.selection, c.player_id or c.player_name, c.stat)
        if k not in best or (rank[c.decision], c.ev or -9) > (rank[best[k].decision], best[k].ev or -9):
            best[k] = c
    import yaml
    try:
        probation = {x["market"] for x in (yaml.safe_load(open(f"{ctx.root}/research/queue.yaml")) or {}).get("probation") or []}
    except FileNotFoundError:
        probation = set()
    portfolio(list(best.values()), cfg, probation)
    status = {m: v["status"] for m, v in cfg["markets"].items()}
    publishable = [c for c in best.values() if c.decision == "eligible" and c.category == "straight"]
    # write every candidate (immutable, versioned by content)
    written, pred_ids = 0, []
    seen_keys = {}
    for c in cands:
        k = candidate_key(c)
        if k in seen_keys:
            c.pred_id = seen_keys[k]   # the same quote seen twice (e.g. two snapshots): one record
            continue
        pid = version_id(c)
        seen_keys[k] = c.pred_id = pid
        pred_ids.append(pid)
        if ctx.store.one("SELECT 1 FROM predictions WHERE pred_id = ?", [pid]):
            continue
        rec = dict(pred_id=pid, created_at=iso(ctx.now), origin="model", provider="nbapicks", model_version=c.model_version,
                   category="straight", game_id=c.game_id, market=c.market, selection=c.selection, line=c.line,
                   player_id=c.player_id, player_name=c.player_name, stat=c.stat, price_dec=c.price_dec, book=c.book,
                   price_observed_at=c.price_observed_at, price_source="espn" if c.book != "bet365" else "moviodds",
                   prob=c.prob, prob_push=c.push, ev=c.ev, edge_threshold=cfg["markets"][c.market]["min_ev"],
                   min_price_dec=c.min_price_dec, decision=c.decision, reason="; ".join(c.reasons) or c.decision,
                   stake_units=c.stake or None, inputs=dict(c.inputs, fair=c.fair, status=status[c.market]), run_id=run_id)
        written += ctx.store.put("predictions", rec) == "new"
    # parlays and lotto: built from straights that cleared their own EV threshold (eligible, or watch while the
    # market is in research). Research combinations are recorded and settled, never published as picks.
    parlays = build_parlays(ctx, list(best.values()), cfg)
    for pz in parlays:
        legs = [dict(pred_id=c.pred_id, label=c.label, price_dec=c.price_dec, prob=c.prob, game_id=c.game_id,
                     price_basis=c.inputs.get("price_basis")) for c in pz["legs"]]
        all_eligible = all(c.decision == "eligible" for c in pz["legs"])
        live = status[pz["kind"]] != "research" and all_eligible
        pid = stable_id("v2", pz["kind"], [l["pred_id"] for l in legs], round(pz["price_dec"], 4), live)
        pred_ids.append(pid)
        if ctx.store.one("SELECT 1 FROM predictions WHERE pred_id = ?", [pid]):
            continue
        ctx.store.put("predictions", dict(
            pred_id=pid, created_at=iso(ctx.now), origin="model", provider="nbapicks", model_version=model_id + "+" + pm.version,
            category=pz["kind"], price_dec=pz["price_dec"], prob=pz["prob"], ev=pz["ev"],
            edge_threshold=cfg["markets"][pz["kind"]]["min_ev"], decision="eligible" if live else "watch",
            reason=(f"{len(legs)} legs from different games; joint probability = product of leg probabilities "
                    f"(different games treated as independent); EV {pz['ev']:+.1%} at the combined price"
                    + ("" if live else f"; research only ({pz['kind']} market in {status[pz['kind']]}"
                       + ("" if all_eligible else ", legs not all qualified") + ")")),
            run_id=run_id, stake_units=cfg["stakes"][pz["kind"]], legs=legs,
            inputs=dict(status=status[pz["kind"]], joint_method="independent cross-game product",
                        price_basis="conservative" if any(l["price_basis"] == "conservative" for l in legs) else "labelled")))
        written += 1
    counts = defaultdict(int)
    for c in cands:
        counts[f"{c.market}:{c.decision}"] += 1
    cards = safe_split_cards(ctx, cands)
    jsave(f"{ctx.root}/state/split_cards_latest.json", dict(slate=slate, run_id=run_id, status="research/watchlist only",
                                                         cards=cards))
    summary = dict(run_id=run_id, slate=slate, games=len(games), model=model_id, prop_model=pm.version, model_ready=model.ready(),
                   candidates=len(cands), written=written, decisions=dict(counts), prop_side_check=side_check,
                   eligible=len(publishable), parlays=sum(p["kind"] == "parlay" for p in parlays),
                   lottos=sum(p["kind"] == "lotto" for p in parlays), split_cards=len(cards),
                   injuries_observed_at=inj_doc.get("observed_at"), pred_ids=pred_ids)
    jsave(f"{ctx.root}/state/last_predict.json", summary)
    return {k: v for k, v in summary.items() if k != "pred_ids"}


def fd_filter(ctx: Ctx, preds: list[dict], slate: str):
    """(predicate, note): keep only props FanDuel offers on the exact player/stat/side/line.

    Needs ODDS_API_KEY. Asks only for the games and markets of today's candidate pool, once per
    game per day (cached in state/fd_props.json). Without a key, or if the feed fails, returns
    (None, note) and nothing is filtered, and the note says so.
    """
    key = oddsapi.api_key()
    if not key:
        return None, "FanDuel availability was not checked (no odds key), so some picks may not be bettable there."
    path = f"{ctx.root}/state/fd_props.json"
    cache = jload(path, {})
    if cache.get("slate") != slate:
        cache = dict(slate=slate, games={}, props=[], prices={})
    cache.setdefault("prices", {})
    pool = LN.pick_leans(preds, ctx.cfg, slate, iso(ctx.now), pool=True)
    games = {g["game_id"]: g for g in ctx.store.q("SELECT game_id, home, away, start_utc FROM games")}
    need: dict[str, set] = defaultdict(set)
    for r in pool:
        mk = oddsapi.market_key(r)
        if mk:
            need[str(r["game_id"])].add(mk)
    todo = {g: sorted(m - set(cache["games"].get(g) or [])) for g, m in need.items() if g in games}
    todo = {g: m for g, m in todo.items() if m}
    try:
        if todo:
            ev = oddsapi.match_events(oddsapi.fetch_events(key), [games[g] for g in todo])
            props = {tuple(x) for x in cache["props"]}
            for gid, mks in todo.items():
                if gid not in ev:
                    continue
                books = oddsapi.parse_event_links(oddsapi.fetch_event_links(key, ev[gid], mks), games[gid]["home"], games[gid]["away"])
                props |= oddsapi.fd_prop_set(books)
                cache["prices"].update(oddsapi.fd_prop_prices(books))
                cache["games"][gid] = sorted(set(cache["games"].get(gid) or []) | set(mks))
            cache["props"] = sorted(props)
            jsave(path, cache)
            ctx.ok("oddsapi_fd", f"{len(todo)} games")
    except Exception as e:
        ctx.fail("oddsapi_fd", e)
        return None, "FanDuel availability could not be checked (odds feed error), so some picks may not be bettable there."
    have = {tuple(x) for x in cache["props"]}
    checked = set(cache["games"])

    def fd_ok(p: dict) -> bool:
        if str(p["game_id"]) not in checked:
            return False                # no FanDuel data for this game: not bettable as far as we know
        return (oddsapi.norm_name(p.get("player_name") or p.get("player") or ""), p["stat"], p["selection"], float(p["line"])) in have
    return fd_ok, ""


def _log_fd_prices(ctx: Ctx, leans: list[dict], preds: list[dict], slate: str) -> None:
    """Experiment (2026-11-25): store the FanDuel American price seen when a lean is posted, so real
    price and closing-line value can be measured later. Never raises; posting must not depend on it."""
    try:
        prices = jload(f"{ctx.root}/state/fd_props.json", {}).get("prices") or {}
        names = {(str(p["game_id"]), str(p["player_id"])): oddsapi.norm_name(p.get("player_name") or p.get("player") or "") for p in preds}
        rows = []
        for l in leans:
            nm = names.get((str(l["game_id"]), str(l["player_id"])), "")
            rows.append(dict(slate=slate, at=iso(ctx.now), label=l["label"], game_id=l["game_id"], player_id=l["player_id"],
                             stat=l["stat"], side=l["selection"], line=l["line"], dk_price_american=l["price_american"],
                             fd_price_american=prices.get(f'{nm}|{l["stat"]}|{l["selection"]}|{float(l["line"])}'), stage="posted"))
        if rows:
            with open(f"{ctx.root}/ledger/fd_prices.jsonl", "a") as f:
                for r in rows:
                    f.write(json.dumps(r, sort_keys=True) + "\n")
    except Exception as e:
        ctx.fail("fd_price_log", e)


def log_fd_closing(ctx: Ctx) -> dict:
    """Experiment (2026-11-25): for today's posted leans whose game tips off within 40 minutes, store the
    FanDuel American price once (stage 'close'), next to the 'posted' row, so closing-line value is measurable.
    Runs inside the 'leans' step on every runner pass; never raises and never blocks posting."""
    try:
        key = oddsapi.api_key()
        slate = ctx.today.isoformat()
        if not key:
            return dict(close_logged=0, skipped="no odds key")
        path = f"{ctx.root}/ledger/fd_prices.jsonl"
        done = set()
        if os.path.exists(path):
            for x in open(path):
                r = json.loads(x)
                if r.get("stage") == "close" and r.get("slate") == slate:
                    done.add((str(r["game_id"]), str(r["player_id"]), r["stat"], r["side"], float(r["line"])))
        games = {g["game_id"]: g for g in ctx.store.q("SELECT game_id, home, away, start_utc FROM games")}
        due = {}
        for l in LN.track.load(ctx.root):
            if l.get("slate") != slate or str(l["game_id"]) not in {str(k) for k in games}:
                continue
            g = games[next(k for k in games if str(k) == str(l["game_id"]))]
            mins = (parse_t(g["start_utc"]) - ctx.now).total_seconds() / 60 if g.get("start_utc") else None
            if mins is None or not (0 <= mins <= 40):
                continue
            if (str(l["game_id"]), str(l["player_id"]), l["stat"], l["selection"], float(l["line"])) in done:
                continue
            due.setdefault(str(g["game_id"]), (g, []))[1].append(l)
        if not due:
            return dict(close_logged=0)
        ev = oddsapi.match_events(oddsapi.fetch_events(key), [g for g, _ in due.values()])
        n = 0
        with open(path, "a") as fh:
            for gid, (g, ls) in due.items():
                if gid not in ev:
                    continue
                mks = sorted({oddsapi.market_key(l) for l in ls} - {None})
                prices = oddsapi.fd_prop_prices(oddsapi.parse_event_links(oddsapi.fetch_event_links(key, ev[gid], mks), g["home"], g["away"]))
                names = {(str(p["game_id"]), str(p["player_id"])): oddsapi.norm_name(p.get("player_name") or p.get("player") or "")
                         for p in ctx.store.q("SELECT game_id, player_id, player_name FROM predictions WHERE market = 'prop' AND game_id = ?", (g["game_id"],))}
                for l in ls:
                    nm = names.get((gid, str(l["player_id"])), "")
                    fh.write(json.dumps(dict(slate=slate, at=iso(ctx.now), label=l["label"], game_id=l["game_id"], player_id=l["player_id"],
                                             stat=l["stat"], side=l["selection"], line=l["line"], stage="close",
                                             fd_price_american=prices.get(f'{nm}|{l["stat"]}|{l["selection"]}|{float(l["line"])}')),
                                        sort_keys=True) + "\n")
                    n += 1
        return dict(close_logged=n)
    except Exception as e:
        ctx.fail("fd_price_log", e)
        return dict(close_logged=0, error=str(e)[:120])


def post_leans(ctx: Ctx) -> dict:
    """Post today's leans, parlays and lotto once per slate (nbapicks/leans.py has the rule)."""
    slate = ctx.today.isoformat()
    last = jload(f"{ctx.root}/state/last_predict.json", {})
    if last.get("slate") != slate or not last.get("games"):
        return dict(posted=0, skipped="no prediction run for today's slate")
    if any(l.get("slate") == slate for l in LN.track.load(ctx.root)):
        if any(t["slate"] == slate and t.get("research") for t in LN.load_tickets(ctx.root)):
            return dict(posted=0, skipped="today's leans are already posted")
        return _rebuild_tickets(ctx, slate, last)
    failing = validate.failing_sources(ctx.health, CRITICAL_SOURCES, ctx.now)
    inj = jload(f"{ctx.root}/state/injuries_latest.json", {})
    inj_age = (ctx.now - parse_t(inj["observed_at"])).total_seconds() / 60 if inj.get("observed_at") else None
    if failing or inj_age is None or inj_age > ctx.cfg["quality"]["max_injury_age_minutes"]:
        why = "critical source failing: " + ", ".join(failing) if failing else "the injury report is missing or stale"
        LN.save_notes(ctx.root, slate, [f"No picks posted today: {why}."])
        return dict(posted=0, skipped=why)
    games = {g["game_id"]: g for g in ctx.store.q("SELECT game_id, start_utc FROM games")}
    cur = set(last.get("pred_ids") or [])
    preds = []
    for p in ctx.store.q("SELECT * FROM predictions WHERE category = 'straight' AND market = 'prop'"):
        if p["pred_id"] in cur:
            preds.append(dict(p, start_utc=(games.get(p["game_id"]) or {}).get("start_utc")))
    fd_ok, fd_note = fd_filter(ctx, preds, slate)
    leans = LN.pick_leans(preds, ctx.cfg, slate, iso(ctx.now), fd_ok=fd_ok)
    _log_fd_prices(ctx, leans, preds, slate)
    for l in leans:
        LN.track.add(ctx.root, l)
    leans = [dict(l, lean_id=LN.track.lean_id(l)) for l in leans]
    tickets, notes = LN.build_tickets(LN.pick_leans(preds, ctx.cfg, slate, iso(ctx.now), pool=True, fd_ok=fd_ok), ctx.cfg, slate,
                                      exclude_players={l["player_id"] for l in leans})
    tickets = _mark_tracked(ctx, tickets)
    try:        # research-only feature log: reads the store, writes its own file, can never change a pick
        from . import researchlog
        pool_rows = LN.pick_leans(preds, ctx.cfg, slate, iso(ctx.now), pool=True, fd_ok=fd_ok)
        researchlog.log_features(ctx, pool_rows, preds, slate, {str(l["player_id"]) for l in leans})
    except Exception as e:
        ctx.fail("research_log", e)
    if fd_note:
        notes = [fd_note] + notes
    if not leans:
        notes = ["No props cleared today's pick rule (win chance, price, recent history and data checks), so no straight picks were posted."] + notes
    for t in tickets:
        LN.add_ticket(ctx.root, t)
    LN.save_notes(ctx.root, slate, notes)
    return dict(posted=len(leans), parlays=sum(t["kind"] == "parlay" for t in tickets), lottos=sum(t["kind"] == "lotto" for t in tickets))


def tickets_posted(cfg: dict) -> bool:
    """config tickets.post: false keeps the parlays and lotto as a tracked-only record (owner 2026-11-25)."""
    return bool((cfg.get("tickets") or {}).get("post", True))


def _mark_tracked(ctx: Ctx, tickets: list[dict]) -> list[dict]:
    if tickets_posted(ctx.cfg):
        return tickets
    return [dict(t, tracked_only=True) for t in tickets]


def _rebuild_tickets(ctx: Ctx, slate: str, last: dict) -> dict:
    """Today's leans stand; the parlays and lotto are rebuilt under the always-post rule."""
    games = {g["game_id"]: g for g in ctx.store.q("SELECT game_id, start_utc FROM games")}
    cur = set(last.get("pred_ids") or [])
    preds = [dict(p, start_utc=(games.get(p["game_id"]) or {}).get("start_utc"))
             for p in ctx.store.q("SELECT * FROM predictions WHERE category = 'straight' AND market = 'prop'") if p["pred_id"] in cur]
    fd_ok, fd_note = fd_filter(ctx, preds, slate)
    straight_players = {str(l["player_id"]) for l in LN.track.load(ctx.root) if l.get("slate") == slate}
    tickets, notes = LN.build_tickets(LN.pick_leans(preds, ctx.cfg, slate, iso(ctx.now), pool=True, fd_ok=fd_ok), ctx.cfg, slate,
                                      exclude_players=straight_players)
    tickets = _mark_tracked(ctx, tickets)
    if fd_note:
        notes = [fd_note] + notes
    LN.replace_slate_tickets(ctx.root, slate, tickets)
    LN.save_notes(ctx.root, slate, notes)
    return dict(posted=0, parlays=sum(t["kind"] == "parlay" for t in tickets), lottos=sum(t["kind"] == "lotto" for t in tickets))


def build_parlays(ctx: Ctx, best: list[Candidate], cfg: dict) -> list[dict]:
    """Up to targets.parlay parlays and targets.lotto lottos per run, within the daily unit caps.
    Legs: straights with a model probability whose own EV cleared their market threshold."""
    legs = [c for c in best if c.category == "straight" and c.prob is not None and c.decision in ("eligible", "watch")
            and c.ev is not None and c.ev >= cfg["markets"][c.market]["min_ev"]]
    legs = sorted(legs, key=lambda c: -c.ev)[:12]   # bounded search: 12 legs -> at most 792 five-leg combos
    out = []
    caps = {"parlay": cfg["risk"]["max_parlay_units_per_day"], "lotto": cfg["risk"]["max_lotto_units_per_day"]}
    for kind in ("parlay", "lotto"):
        used = 0.0
        for pz in PZ.build(legs, cfg, kind):
            stake = cfg["stakes"][kind]
            if used + stake > caps[kind] + 1e-9:
                break
            used += stake
            out.append(pz)
    return out


# ------------------------------------------------------------------ publish / settle / recap
def _pick_view(ctx, p: dict) -> dict:
    g = ctx.store.one("SELECT * FROM games WHERE game_id = ?", [p["game_id"]]) or {}
    c = Candidate(game_id=p["game_id"], start_utc=g.get("start_utc", ""), home=g.get("home", "?"), away=g.get("away", "?"),
                  market=p["market"], selection=p["selection"], line=p["line"], price_dec=p["price_dec"], book=p["book"],
                  price_observed_at=p["price_observed_at"], prob=p["prob"], player_name=p.get("player_name"), stat=p.get("stat"))
    t = dt.datetime.fromisoformat(p["price_observed_at"].replace("Z", "+00:00")).astimezone(ZoneInfo(ctx.tz))
    inputs = json.loads(p["inputs"] or "{}")
    return dict(label=c.label, away=c.away, home=c.home, start_utc=c.start_utc, book=p["book"], price_dec=p["price_dec"],
                price_time=t.strftime("%-I:%M %p ET"), prob=p["prob"], ev=p["ev"], stake=p["stake_units"] or 0,
                min_price_dec=p["min_price_dec"], pred_id=p["pred_id"], model_version=p["model_version"],
                status=inputs.get("status"))


def publish_picks(ctx: Ctx) -> str:
    slate = ctx.today.isoformat()
    last = jload(f"{ctx.root}/state/last_predict.json", {})
    if last.get("slate") != slate:
        return "skipped: no prediction run for today's slate"
    if not last.get("games"):
        return "skipped: no games on today's slate"
    run_at = parse_t(last["run_id"][4:])
    if (ctx.now - run_at).total_seconds() > 60 * ctx.cfg["publishing"]["max_prediction_age_minutes"]:
        return f"skipped: last prediction run {last['run_id'][4:]} is too old to publish (predict must run first)"
    current = last.get("pred_ids")
    if current is None:   # summaries written before predictions were versioned
        current = [p["pred_id"] for p in ctx.store.q("SELECT pred_id FROM predictions WHERE run_id = ?", [last["run_id"]])]
    cur = set(current)
    preds = [p for p in ctx.store.q("SELECT * FROM predictions WHERE decision = 'eligible'") if p["pred_id"] in cur]
    allow = {"live"} | ({"paper"} if ctx.cfg["publishing"]["publish_paper"] else set())
    preds = [p for p in preds if json.loads(p["inputs"] or "{}").get("status") in allow]
    straights = [_pick_view(ctx, p) for p in preds if p["category"] == "straight"]
    parl = []
    for p in preds if tickets_posted(ctx.cfg) else []:
        if p["category"] in ("parlay", "lotto"):
            legs = json.loads(p["legs"])
            parl.append(dict(kind=p["category"], legs=legs, leg_labels=[l["label"] for l in legs], price_dec=p["price_dec"],
                             prob=p["prob"], ev=p["ev"], stake=p["stake_units"], pred_id=p["pred_id"],
                             status=json.loads(p["inputs"] or "{}").get("status")))
    d = last.get("decisions", {})
    held = sum(v for k, v in d.items() if k.endswith(":hold")); watch = sum(v for k, v in d.items() if k.endswith(":watch"))
    why = (f"{held} held by data, injury or skeptic checks; {watch} on the research watchlist "
           f"(models not yet validated)." if not straights else "")
    msg = discord.picks_message(slate, straights, parl, ctx.cfg, last.get("candidates", 0), why)
    st = discord.publish(ctx.store, "picks", slate, msg, ctx.cfg, iso(ctx.now))
    # the paper record: every eligible or watchlist straight from the publishing run, 1u flat,
    # scored like a pick but never shown as one (research-only, never sent to Discord)
    if st not in ("sent", "dry_run"):
        return st   # already published (or failed): the record for this slate is not re-written
    for p in [p for p in ctx.store.q("SELECT pred_id FROM predictions WHERE category = 'straight' AND decision IN ('eligible', 'watch')")
              if p["pred_id"] in cur]:
        put_event_once(ctx, dict(event_id=stable_id(p["pred_id"], "paper"), pred_id=p["pred_id"], at=iso(ctx.now),
                                 type="note", data=dict(paper_record=True)))
    if st in ("sent", "dry_run"):
        for p in preds:
            ctx.store.put("pred_events", dict(event_id=stable_id(p["pred_id"], "published", st), pred_id=p["pred_id"],
                                              at=iso(ctx.now), type="published", data=dict(mode=st)))
    return st


def put_event_once(ctx: Ctx, ev: dict) -> bool:
    if ctx.store.one("SELECT 1 FROM pred_events WHERE event_id = ?", [ev["event_id"]]):
        return False
    ctx.store.put("pred_events", ev)
    return True


SUSPENDED_VOID_HOURS = 48   # a suspended game not completed within 48h of tip is void (book rules)


def effective_status(g: dict, now: dt.datetime) -> str:
    if g["status"] == "suspended" and (now - parse_t(g["start_utc"])).total_seconds() > SUSPENDED_VOID_HOURS * 3600:
        return "suspended_void"
    return g["status"]


def settle(ctx: Ctx) -> dict:
    out = defaultdict(int)
    done = {r["pred_id"] for r in ctx.store.q("SELECT pred_id FROM pred_events WHERE type = 'settled'")}
    games = {g["game_id"]: g for g in ctx.store.q("SELECT * FROM games")}
    box = {(r["game_id"], r["player_id"]): r for r in ctx.store.q("SELECT * FROM player_games")}
    results = {}
    preds = ctx.store.q("SELECT * FROM predictions ORDER BY category = 'straight' DESC")
    for p in preds:
        if p["pred_id"] in done:
            continue
        if p["category"] == "straight":
            g = games.get(p["game_id"])
            if not g:
                continue
            res = GameResult(effective_status(g, ctx.now), g["home_score"], g["away_score"])
            stat_v = played = None
            if p["market"] == "prop":
                b = box.get((p["game_id"], p["player_id"]))
                if b:
                    played = bool(b["played"]); stat_v = b.get(p["stat"])
                elif g["status"] == "final" and any(k[0] == p["game_id"] for k in box):
                    played = False  # box score in, player absent from it
            if p["selection"] not in ("home", "away", "over", "under"):
                r = "void" if g["status"] == "final" else "pending"   # unverified prop side: never scored
            else:
                r = settle_leg(p["market"], p["selection"], p["line"], res, stat_v, played)
            results[p["pred_id"]] = (r, p["price_dec"])
        else:
            legs = json.loads(p["legs"])
            leg_res = [results.get(l["pred_id"]) or _settled(ctx, l["pred_id"]) for l in legs]
            if any(x is None for x in leg_res):
                continue
            r, net, _ = settle_parlay(leg_res, p["stake_units"] or 1)
        if r == "pending":
            continue
        stake = p["stake_units"] or 1.0
        net = net_profit(r, p["price_dec"], stake) if p["category"] == "straight" else net
        ctx.store.put("pred_events", dict(event_id=stable_id(p["pred_id"], "settled"), pred_id=p["pred_id"], at=iso(ctx.now),
                                          type="settled", result=r, net_units=net, data=dict(stake=stake)))
        out[r] += 1
    out.update(import_wagers(ctx))
    try:
        from .signals import compare_with_model
        out.update({f"signals_{k}": v for k, v in compare_with_model(ctx).items() if v})
    except Exception as e:
        ctx.fail("signals_compare", e)
    return dict(out)


def _settled(ctx, pred_id):
    e = ctx.store.one("SELECT result FROM pred_events WHERE pred_id = ? AND type = 'settled'", [pred_id])
    p = ctx.store.one("SELECT price_dec FROM predictions WHERE pred_id = ?", [pred_id])
    return (e["result"], p["price_dec"]) if e and p else None


WAGER_CORE = ("placed_at", "book", "game_id", "market", "selection", "line", "price_american", "price_dec",
              "stake", "player_id", "stat", "legs")
MANUAL_RESULTS = ("win", "loss", "push", "void", "cashout")


def wager_slate(ctx: Ctx, w: dict, games: dict) -> str:
    """The slate a wager belongs to: its game's local date, else when it was placed (local time)."""
    g = games.get(w.get("game_id"))
    if g:
        return slate_of(g["start_utc"], ctx.tz)
    return slate_of(w["placed_at"] if w["placed_at"].endswith("Z") or "+" in w["placed_at"][10:] else w["placed_at"] + "Z", ctx.tz)


def import_wagers(ctx: Ctx) -> dict:
    """data/manual/wagers.csv is the user's own log of bets actually placed. Only rows
    there count as actual wagers. A row is identified by its wager_id column, or else by
    a hash of its core fields, so adding columns or editing notes never duplicates a bet.
    A row whose 'corrects' column names another wager_id replaces that wager (the old one
    gets a 'corrected' event and stops counting). 'result' (+ 'net' for cash-outs) settles
    a wager by hand: needed for parlays, cash-outs and anything the box score cannot settle."""
    import csv
    path = f"{ctx.root}/manual/wagers.csv"
    out = defaultdict(int)
    if not os.path.exists(path):
        return {}
    games = {g["game_id"]: g for g in ctx.store.q("SELECT * FROM games")}
    manual = {}
    with open(path) as fh:
        for i, row in enumerate(csv.DictReader(fh), 2):
            row = {k: (v or "").strip() for k, v in row.items() if k}
            if not row.get("placed_at") or row["placed_at"].startswith("#"):
                continue
            try:
                wid = row.get("wager_id") or stable_id(*[row.get(k, "") for k in WAGER_CORE])
                price = float(row["price_dec"]) if row.get("price_dec") else O.american_to_decimal(float(row["price_american"]))
                market, sel = row["market"].lower(), row["selection"].lower()
                line = float(row["line"]) if row.get("line") else None
                if market in ("spread", "total", "prop") and line is None:
                    raise ValueError(f"{market} needs a line")
                if market in ("ml", "spread") and sel not in ("home", "away"):
                    raise ValueError(f"selection for {market} must be home or away, got {sel!r}")
                if market in ("total", "prop") and sel not in ("over", "under"):
                    raise ValueError(f"selection for {market} must be over or under, got {sel!r}")
                if market == "prop" and not (row.get("player_id") and row.get("stat")):
                    raise ValueError("prop needs player_id and stat")
                parse_t(row["placed_at"] if row["placed_at"][-1] == "Z" or "+" in row["placed_at"][10:] else row["placed_at"] + "Z")
                rec = dict(wager_id=wid, pred_id=row.get("pred_id") or None, placed_at=row["placed_at"],
                           book=row.get("book") or "FanDuel", game_id=row.get("game_id") or None, market=market,
                           selection=sel, line=line, player_id=row.get("player_id") or None, stat=row.get("stat") or None,
                           price_dec=price, stake=float(row["stake"]), units=float(row["units"]) if row.get("units") else None,
                           legs=row.get("legs") or None, notes=row.get("notes") or None, confirmed_by="user:data/manual/wagers.csv")
                if rec["pred_id"] and not ctx.store.one("SELECT 1 FROM predictions WHERE pred_id = ?", [rec["pred_id"]]):
                    rec["pred_id"] = None
                if rec["game_id"] and rec["game_id"] not in games:
                    rec["game_id"] = None
                if not ctx.store.one("SELECT 1 FROM wagers WHERE wager_id = ?", [wid]):
                    out["wagers_" + ctx.store.put("wagers", rec)] += 1
                old = row.get("corrects")
                if old and ctx.store.one("SELECT 1 FROM wagers WHERE wager_id = ?", [old]):
                    eid = stable_id(old, "corrected", wid)
                    if not ctx.store.one("SELECT 1 FROM wager_events WHERE event_id = ?", [eid]):
                        ctx.store.put("wager_events", dict(event_id=eid, wager_id=old, at=iso(ctx.now), type="corrected",
                                                           data=dict(replaced_by=wid)))
                if row.get("result"):
                    r = row["result"].lower()
                    if r not in MANUAL_RESULTS:
                        raise ValueError(f"result must be one of {MANUAL_RESULTS}")
                    if r == "cashout" and not row.get("net"):
                        raise ValueError("cashout needs net")
                    manual[wid] = (r, float(row["net"]) if row.get("net") else None)
            except Exception as e:
                out["wager_errors"] += 1
                ctx.notes.append(f"wagers.csv line {i} skipped: {e}")
    box = {(r["game_id"], r["player_id"]): r for r in ctx.store.q("SELECT * FROM player_games")}
    for w in ctx.store.q("SELECT * FROM wagers"):
        events = {e["type"] for e in ctx.store.q("SELECT type FROM wager_events WHERE wager_id = ?", [w["wager_id"]])}
        if "settled" in events or "corrected" in events:
            continue
        try:
            if w["wager_id"] in manual:
                r, net = manual[w["wager_id"]]
                net = net if net is not None else net_profit(r, w["price_dec"], w["stake"])
                how = "manual"
            else:
                g = games.get(w["game_id"])
                if not g or w["market"] not in ("ml", "spread", "total", "prop"):
                    continue   # parlays and unlinked bets settle by hand ('result' column)
                stat_v = played = None
                if w["market"] == "prop":
                    b = box.get((w["game_id"], w["player_id"]))
                    if b:
                        played, stat_v = bool(b["played"]), b.get(w["stat"])
                    elif g["status"] == "final" and any(k[0] == w["game_id"] for k in box):
                        played = False
                r = settle_leg(w["market"], w["selection"], w["line"],
                               GameResult(effective_status(g, ctx.now), g["home_score"], g["away_score"]), stat_v, played)
                if r == "pending":
                    continue
                net, how = net_profit(r, w["price_dec"], w["stake"]), "box score"
            ctx.store.put("wager_events", dict(event_id=stable_id(w["wager_id"], "settled"), wager_id=w["wager_id"], at=iso(ctx.now),
                                               type="settled", result=r,
                                               net=net, data=dict(how=how, cashout=r == "cashout")))
            out["wagers_settled"] += 1
        except Exception as e:
            out["wager_errors"] += 1
            ctx.notes.append(f"wager {w['wager_id']} not settled: {e}")
    return dict(out)


def recap(ctx: Ctx, slate: str | None = None) -> str:
    slate = slate or (ctx.today - dt.timedelta(days=1)).isoformat()
    pub = ctx.store.q("""SELECT p.* FROM predictions p JOIN pred_events e ON e.pred_id = p.pred_id AND e.type = 'published'""")
    rows = []
    for p in pub:
        when = (ctx.store.one("SELECT start_utc FROM games WHERE game_id = ?", [p["game_id"]])["start_utc"]
                if p["category"] == "straight" else p["created_at"])
        if slate_of(when, ctx.tz) != slate:
            continue
        s = ctx.store.one("SELECT result, net_units FROM pred_events WHERE pred_id = ? AND type = 'settled'", [p["pred_id"]])
        label = _pick_view(ctx, p)["label"] if p["category"] == "straight" else f"{p['category'].title()} ({len(json.loads(p['legs']))} legs)"
        rows.append(dict(label=label, price_dec=p["price_dec"], result=s["result"] if s else "pending",
                         net=s["net_units"] if s else None, stake=p["stake_units"] or 1))
    gmap = {g["game_id"]: g for g in ctx.store.q("SELECT * FROM games")}
    wagers = []
    for w in ctx.store.q("""SELECT w.*, e.net FROM wagers w LEFT JOIN wager_events e ON e.wager_id = w.wager_id AND e.type = 'settled'
                            WHERE NOT EXISTS (SELECT 1 FROM wager_events c WHERE c.wager_id = w.wager_id AND c.type = 'corrected')"""):
        if wager_slate(ctx, w, gmap) == slate:
            wagers.append(w)
    games = [g for g in gmap.values() if slate_of(g["start_utc"], ctx.tz) == slate]
    if not games and not rows and not wagers:
        return "skipped: no games on that slate"
    done = ("final", "postponed", "cancelled", "suspended_void")
    if any(effective_status(g, ctx.now) not in done for g in games):
        return "skipped: slate not finished"
    msg = discord.recap_message(slate, rows, wagers, ctx.notes[:3])
    return discord.publish(ctx.store, "recap", slate, msg, ctx.cfg, iso(ctx.now))


# ------------------------------------------------------------------ main
STEPS = ("ingest", "boxes", "catchup", "predict", "publish", "leans", "settle", "recap", "diagnose", "export")


PAUSE_FILE = "PAUSED"


def pause_state(state_dir: str = None) -> dict | None:
    """Global pause: data/state/PAUSED (any contents; JSON {"reason": ...} is shown) or config `pause: true`.
    While paused no new recommendation is produced or published; ingest, settle, export still run.
    Resuming is deliberate: delete the file (or set pause false) once the health checks pass."""
    path = os.path.join(state_dir or STATE, PAUSE_FILE)
    if os.path.exists(path):
        raw = open(path).read().strip()
        try:
            info = json.loads(raw) if raw else {}
        except ValueError:
            info = {"reason": raw[:200]}
        return dict(source=path, reason=info.get("reason") or "paused by operator", since=info.get("since"))
    return None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("steps", nargs="+", choices=STEPS + ("all",))
    ap.add_argument("--now", help="ISO time to run as (replays, tests)")
    ap.add_argument("--slate", help="YYYY-MM-DD: price this slate now (an early read of tomorrow's games)")
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    now = dt.datetime.fromisoformat(a.now.replace("Z", "+00:00")) if a.now else dt.datetime.now(dt.timezone.utc)
    cfg = C.load()
    ctx = Ctx(now, cfg, slate=dt.date.fromisoformat(a.slate) if a.slate else None)
    steps = STEPS if "all" in a.steps else a.steps
    report = dict(at=iso(now), steps={}, ok=True)
    for s in steps:
        if s in ("predict", "publish", "leans") and report["steps"].get("ingest", {}).get("status") == "failed":
            report["steps"][s] = dict(status="skipped", reason="ingest failed: no fresh games/odds to price")
            report["ok"] = False
            continue
        if s in ("predict", "publish", "leans") and (pause_state(f"{ctx.root}/state") or cfg.get("pause")):
            pz = pause_state(f"{ctx.root}/state") or dict(source="config", reason="pause: true in config")
            report["steps"][s] = dict(status="skipped", reason=f"global pause: {pz['reason']}")
            report["paused"] = pz
            continue
        try:
            if s == "ingest":
                r = ingest(ctx)
            elif s == "boxes":
                r = boxes(ctx)
            elif s == "catchup":
                r = catchup(ctx)
            elif s == "predict":
                r = predict(ctx)
            elif s == "publish":
                r = publish_picks(ctx)
            elif s == "leans":
                r = post_leans(ctx)
                if isinstance(r, dict):
                    r = dict(r, **log_fd_closing(ctx))
            elif s == "settle":
                r = settle(ctx)
            elif s == "recap":
                r = recap(ctx)
            elif s == "diagnose":
                from .diagnose import run as diag
                r = diag(ctx)
            else:
                from .dashboard import export
                try:
                    links = book_links(ctx)
                except Exception as e:   # links are a convenience; never block the export
                    links = dict(error=str(e)[:200])
                r = export(ctx)
                if isinstance(r, dict):
                    r = dict(r, book_links=links)
            report["steps"][s] = dict(status="completed", result=r)
        except Exception as e:
            report["ok"] = False
            report["steps"][s] = dict(status="failed", error=f"{type(e).__name__}: {e}", trace=traceback.format_exc()[-1500:])
            log.exception("step %s failed", s)
    report["notes"] = ctx.notes
    ctx.save_state()
    os.makedirs(STATE, exist_ok=True)
    with open(f"{STATE}/runs.jsonl", "a") as fh:
        fh.write(json.dumps(report, default=str) + "\n")
    print(json.dumps(report, indent=1, default=str)[:6000])
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
