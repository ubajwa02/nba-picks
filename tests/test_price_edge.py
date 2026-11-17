"""The 2026-11-17 pick rule: a pick is a FanDuel prop priced above the DraftKings fair price."""
import copy
import datetime as dt
import json
import os

import pytest

from nbapicks import leans as LN
from nbapicks import pipeline, track
from nbapicks.config import load as load_config
from nbapicks.odds import american_to_decimal as dec
from nbapicks.sources import oddsapi

HERE = os.path.dirname(__file__)
NOW = "2026-11-17T21:30:00Z"
TIP = "2026-11-18T00:40:00Z"


@pytest.fixture
def cfg():
    return load_config(os.path.join(os.path.dirname(HERE), "config", "nbapicks.yaml"))


def pred(pid, name, game="g1", stat="pts", line=20.5, prob=0.5, reason="EV -3.0% below 5% threshold", sel="over"):
    return dict(market="prop", category="straight", game_id=game, player_id=pid, player_name=name, stat=stat, line=line,
                selection=sel, prob=prob, price_dec=1.9, decision="reject", reason=reason, start_utc=TIP, model_version="props-v0")


def quote(name, fd, dk, game="g1", stat="pts", line=20.5, at=NOW):
    """fd, dk: (over, under) American prices."""
    return [dict(game_id=game, book=b, player=oddsapi.norm_name(name), stat=stat, line=line, over=dec(o), under=dec(u), at=at)
            for b, (o, u) in (("fanduel", fd), ("draftkings", dk))]


def test_real_response_parses_to_two_way_decimal_quotes():
    d = json.load(open(os.path.join(HERE, "fixtures", "oddsapi_event_props_20261117.json")))
    rows = oddsapi.parse_event_prices(d)
    assert {r["book"] for r in rows} == {"fanduel", "draftkings"} and {r["stat"] for r in rows} == {"pts", "reb"}
    hart = {r["book"]: r for r in rows if r["player"] == "josh hart" and r["stat"] == "reb" and r["line"] == 5.5}
    assert hart["fanduel"]["under"] == 2.18 and hart["draftkings"]["over"] == round(1 + 100 / 134, 4)
    assert all(r["over"] > 1 and r["under"] > 1 for r in rows)


def test_a_pick_needs_fanduel_to_pay_five_percent_over_the_fair_price(cfg):
    preds = [pred("1", "Good Price"), pred("2", "Fair Price", game="g2"), pred("3", "Model Loves", game="g3", prob=0.95)]
    quotes = (quote("Good Price", (+112, -140), (-110, -110))            # fair 50%, FanDuel 2.12: edge +6%
              + quote("Fair Price", (+100, -122), (-110, -110), game="g2")       # edge 0%
              + quote("Model Loves", (-110, -110), (-110, -110), game="g3"))     # the model says 95%; the price says no edge
    got = LN.pick_leans(preds, cfg, "2026-11-17", NOW, quotes)
    assert [g["player_id"] for g in got] == ["1"]
    g = got[0]
    assert g["book"] == "FanDuel" and g["price_american"] == 112 and g["selection"] == "over" and g["source"] == LN.SOURCE
    assert abs(g["prob"] - 0.5) < 1e-6 and abs(g["edge"] - 0.06) < 1e-6 and g["model"] == "props-v0"
    assert LN.pick_leans(preds, cfg, "2026-11-17", NOW, None) == []          # no FanDuel price, no pick


def test_picks_rank_by_edge_one_per_game_one_per_player(cfg):
    preds = [pred("1", "A One"), pred("2", "B Two"), pred("3", "C Three", game="g2"), pred("3", "C Three", game="g2", stat="reb", line=7.5)]
    quotes = (quote("A One", (+112, -140), (-110, -110)) + quote("B Two", (+118, -145), (-110, -110))
              + quote("C Three", (+114, -140), (-110, -110), game="g2")
              + quote("C Three", (+116, -140), (-110, -110), game="g2", stat="reb", line=7.5))
    got = LN.pick_leans(preds, cfg, "2026-11-17", NOW, quotes)
    assert [(g["player_id"], g["stat"]) for g in got] == [("2", "pts"), ("3", "reb")]     # best edge per game
    assert got[0]["edge"] > got[1]["edge"]


def test_checks_that_stop_a_pick(cfg):
    q = quote("Solo Man", (+112, -140), (-110, -110))
    ok = [pred("1", "Solo Man")]
    assert len(LN.pick_leans(ok, cfg, "2026-11-17", NOW, q)) == 1
    assert LN.pick_leans([pred("1", "Solo Man", reason="unresolved injury: Solo Man (Questionable)")], cfg, "2026-11-17", NOW, q) == []
    assert LN.pick_leans(ok, cfg, "2026-11-17", NOW, q, blocks=dict(players={"1": "player listed Out"})) == []
    assert LN.pick_leans(ok, cfg, "2026-11-17", NOW, q, blocks=dict(games={"g1": ["unresolved injury: Star (GTD)"]})) == []
    assert LN.pick_leans([pred("9", "Other Guy")], cfg, "2026-11-17", NOW, q) == []                       # not in today's predictions
    assert LN.pick_leans(ok, cfg, "2026-11-17", NOW, quote("Solo Man", (+112, -140), (-110, -110), at="2026-11-17T18:00:00Z")) == []   # stale
    assert LN.pick_leans(ok, cfg, "2026-11-17", "2026-11-18T00:30:00Z", quote("Solo Man", (+112, -140), (-110, -110), at="2026-11-18T00:29:00Z")) == []  # 10 min to tip
    assert LN.pick_leans(ok, cfg, "2026-11-17", NOW, quote("Solo Man", (+160, -200), (-110, -110))) == []     # +30%: a wrong quote, not an edge
    assert LN.pick_leans(ok, cfg, "2026-11-17", NOW, quote("Solo Man", (+2500, +1400), (-110, -110))) == []   # not a two-way pair
    short = quote("Solo Man", (-215, +170), (-300, +230))                                                 # edge, but under -200
    assert LN.pick_leans(ok, cfg, "2026-11-17", NOW, short) == []
    assert LN.pick_leans(ok, cfg, "2026-11-17", NOW, [x for x in q if x["book"] == "fanduel"]) == []          # nothing to compare with


def test_model_weight_blends_on_log_odds_and_is_zero_by_default(cfg):
    assert cfg["leans"]["model_weight"] == 0.0
    assert LN.blend(0.5, 0.9, 0.0) == 0.5 and LN.blend(0.5, None, 0.5) == 0.5
    assert 0.5 < LN.blend(0.5, 0.9, 0.25) < 0.9


def test_tickets_need_a_combined_edge_and_say_so(cfg):
    fair = [dict(label=f"P{i} o5.5 reb", game_id=f"g{i}", prob=0.5, price_american=-110, slate="2026-11-17", player_id=str(i))
            for i in range(1, 8)]
    tickets, notes = LN.build_tickets(fair, cfg, "2026-11-17")
    assert tickets == [] and any("parlays" in n for n in notes) and any("lotto" in n.lower() for n in notes)
    good = [dict(l, price_american=+112) for l in fair]                       # each leg +6%: parlay +12%, 4 legs +26%
    tickets, notes = LN.build_tickets(good, cfg, "2026-11-17")
    assert sum(t["kind"] == "parlay" for t in tickets) == 2 and sum(t["kind"] == "lotto" for t in tickets) == 1
    assert all(t["ev"] >= 0.05 for t in tickets)
    legacy = copy.deepcopy(cfg); legacy["leans"]["tickets_require_edge"] = False
    tickets, _ = LN.build_tickets(fair, legacy, "2026-11-17")
    assert sum(t["kind"] == "parlay" for t in tickets) == 2               # the older owner rule is still available


def test_recheck_is_recorded_and_never_changes_the_pick_or_its_grade(tmp_path):
    root = str(tmp_path)
    lean = dict(game_id="g1", label="A One o20.5 pts", line=20.5, market="prop", player_id="1", price_american=112, prob=0.5,
                selection="over", slate="2026-11-17", source=LN.SOURCE, stake=1.0, stat="pts", book="FanDuel", edge=0.06)
    assert track.add(root, lean)
    lid = track.lean_id(lean)
    track.add_event(root, dict(lean_id=lid, at="2026-11-17T23:30:00Z", state="ok", reason="still stands at +110", price_american=110, edge=0.05))
    track.add_event(root, dict(lean_id=lid, at="2026-11-17T23:55:00Z", state="skip", reason="player listed Out", price_american=None, edge=None))
    assert track.latest_events(root)[lid]["state"] == "skip"
    games = {"g1": dict(status="final", home="AAA", away="BBB", home_score=100, away_score=90)}
    box = {("g1", "1"): dict(played=1, pts=25)}
    g = track.grade(track.load(root), games, box)[0]
    assert g["result"] == "win" and abs(g["net_units"] - 1.12) < 1e-9 and g["price_american"] == 112      # graded at the posted FanDuel price


def _ctx(tmp_path, monkeypatch, now=NOW):
    cfg = load_config(os.path.join(os.path.dirname(HERE), "config", "nbapicks.yaml"))
    root = str(tmp_path / "data")
    os.makedirs(f"{root}/state", exist_ok=True)
    monkeypatch.setenv("ODDS_API_KEY", "k")
    ctx = pipeline.Ctx(dt.datetime.fromisoformat(now.replace("Z", "+00:00")), cfg, root)
    for src in pipeline.CRITICAL_SOURCES:
        ctx.ok(src)
    for gid, home, away in (("g1", "TOR", "NY"), ("g2", "SA", "DET")):
        ctx.store.put("games", dict(game_id=gid, season=2027, season_type="regular", start_utc=TIP, home=home, away=away, home_id="1",
                                    away_id="2", status="scheduled", home_score=None, away_score=None, observed_at=now, source="t"))
    return ctx


def _seed(ctx, preds):
    ids = []
    for i, p in enumerate(preds):
        row = dict(pred_id=f"p{i}", created_at=NOW, origin="model", provider="nbapicks", model_version="props-v0", category="straight",
                   game_id=p["game_id"], market="prop", selection=p["selection"], line=p["line"], player_id=p["player_id"],
                   player_name=p["player_name"], stat=p["stat"], price_dec=1.9, book="DraftKings", price_observed_at=NOW, price_source="espn",
                   prob=p["prob"], prob_push=0.0, ev=-0.03, edge_threshold=0.05, min_price_dec=2.1, decision="reject", reason=p["reason"],
                   stake_units=0.0, legs=None, inputs="{}", run_id="r1")
        ctx.store.put("predictions", row); ids.append(row["pred_id"])
    pipeline.jsave(f"{ctx.root}/state/last_predict.json", dict(slate=ctx.today.isoformat(), games=2, pred_ids=ids))
    pipeline.jsave(f"{ctx.root}/state/injuries_latest.json", dict(observed_at=NOW, rows=[]))


def _feed(monkeypatch, prices, calls):
    """prices: {event id: {(player, market key): (fd_over, fd_under, dk_over, dk_under)}} American, line 20.5."""
    monkeypatch.setattr(oddsapi, "fetch_events", lambda k: [dict(id="e1", home_team="Toronto Raptors", away_team="New York Knicks", commence_time=TIP),
                                                            dict(id="e2", home_team="San Antonio Spurs", away_team="Detroit Pistons", commence_time=TIP)])
    def links(key, eid, mks):
        calls.append((eid, tuple(mks)))
        books = []
        for bk, (io, iu) in (("fanduel", (0, 1)), ("draftkings", (2, 3))):
            markets = []
            for mk in mks:
                outs = []
                for (player, m), pr in prices.get(eid, {}).items():
                    if m == mk:
                        outs += [dict(name="Over", description=player, price=pr[io], point=20.5), dict(name="Under", description=player, price=pr[iu], point=20.5)]
                markets.append(dict(key=mk, outcomes=outs))
            books.append(dict(key=bk, markets=markets))
        return dict(bookmakers=books)
    monkeypatch.setattr(oddsapi, "fetch_event_links", links)


def test_post_once_at_fanduel_prices_then_recheck_before_tip(tmp_path, monkeypatch):
    ctx = _ctx(tmp_path, monkeypatch)
    _seed(ctx, [pred("1", "A One"), pred("2", "B Two", game="g2"), pred("3", "C Three", game="g2")])
    prices = {"e1": {("A One", "player_points"): (+112, -140, -110, -110)},
              "e2": {("B Two", "player_points"): (-110, -110, -110, -110), ("C Three", "player_points"): (-105, -115, -110, -110)}}
    calls = []
    _feed(monkeypatch, prices, calls)
    monkeypatch.setattr(pipeline, "box_rows", lambda ctx, before: [])
    r = pipeline.post_leans(ctx)
    assert r["posted"] == 1 and r["parlays"] == 0 and r["lottos"] == 0
    posted = track.load(ctx.root)
    assert [(l["label"], l["price_american"], l["book"]) for l in posted] == [("A One o20.5 pts", 112, "FanDuel")]
    notes = LN.load_notes(ctx.root)[ctx.today.isoformat()]
    assert any("compared" in n for n in notes) and any("lotto" in n.lower() for n in notes)
    ledger = [json.loads(x) for x in open(f"{ctx.root}/ledger/fd_quotes/2026-11.jsonl")]
    assert {q["book"] for q in ledger} == {"fanduel", "draftkings"} and len(ledger) == 6          # every quote fetched is stored
    spent = sum(len(m) for _, m in calls)
    assert spent <= ctx.cfg["leans"]["fd_credits_per_slate"]
    # a later run re-checks the pick at the new price: it is advice only, the posted pick does not change
    ctx.save_state()
    later = pipeline.Ctx(ctx.now + dt.timedelta(hours=2), ctx.cfg, ctx.root)
    prices["e1"][("A One", "player_points")] = (-125, +100, -120, -102)        # FanDuel shortened below the fair price
    calls.clear()
    r2 = pipeline.post_leans(later)
    assert r2["posted"] == 0 and r2["rechecked"] == 1 and r2["skip"] == 1 and calls == [("e1", ("player_points",))]
    assert track.load(ctx.root) == posted
    ev = track.latest_events(ctx.root)[posted[0]["lean_id"]]
    assert ev["state"] == "skip" and ev["price_american"] == -125 and "below the fair price" in ev["reason"]


def test_no_edge_posts_nothing_and_says_how_close_it_was(tmp_path, monkeypatch):
    ctx = _ctx(tmp_path, monkeypatch)
    _seed(ctx, [pred("1", "A One", prob=0.9), pred("2", "B Two", game="g2", prob=0.8)])
    _feed(monkeypatch, {"e1": {("A One", "player_points"): (-108, -112, -110, -110)},
                        "e2": {("B Two", "player_points"): (-110, -110, -110, -110)}}, [])
    monkeypatch.setattr(pipeline, "box_rows", lambda ctx, before: [])
    r = pipeline.post_leans(ctx)
    assert r["posted"] == 0 and track.load(ctx.root) == [] and LN.load_tickets(ctx.root) == []
    note = LN.load_notes(ctx.root)[ctx.today.isoformat()][0]
    assert note.startswith("No straight pick today") and "best edge" in note
    ctx.save_state()
    assert pipeline.post_leans(pipeline.Ctx(ctx.now + dt.timedelta(hours=1), ctx.cfg, ctx.root))["posted"] == 0   # decided once


def test_feed_error_posts_nothing_and_may_retry(tmp_path, monkeypatch):
    ctx = _ctx(tmp_path, monkeypatch)
    _seed(ctx, [pred("1", "A One")])
    monkeypatch.setattr(oddsapi, "fetch_events", lambda k: (_ for _ in ()).throw(RuntimeError("429")))
    monkeypatch.setattr(pipeline, "box_rows", lambda ctx, before: [])
    r = pipeline.post_leans(ctx)
    assert r["posted"] == 0 and "FanDuel" in r["skipped"] and track.load(ctx.root) == []
    _feed(monkeypatch, {"e1": {("A One", "player_points"): (+112, -140, -110, -110)}}, [])
    assert pipeline.post_leans(ctx)["posted"] == 1
