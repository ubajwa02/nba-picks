"""DraftKings prop sides by listing order (nbapicks/sideorder.py): the results check, the same-run
check, the decision, and the wiring into predict and settle."""
import datetime as dt, json, os, random
import pytest
from nbapicks import pipeline, sideorder as SO
from nbapicks.store import Store
from tests.test_e2e import env, NOW  # noqa: F401  (fixture)


# ---- helpers ------------------------------------------------------------------------------
def graded(n_slates=6, per_game=40, games=4, order="over_first", seed=7):
    """Synthetic graded closing pairs: the Over really wins with its fair chance; `order` says
    whether the first-listed price is the Over, the Under, or a coin flip per pair."""
    rnd = random.Random(seed)
    rows = []
    for s in range(n_slates):
        slate = (dt.date(2026, 11, 1) + dt.timedelta(days=s)).isoformat()
        for g in range(games):
            for i in range(per_game):
                p_over = min(0.9, max(0.1, rnd.gauss(0.5, 0.09)))
                over = int(rnd.random() < p_over)
                first_is_over = {"over_first": True, "under_first": False}.get(order, rnd.random() < 0.5)
                rows.append(dict(slate=slate, game_id=f"g{s}-{g}", player_id=str(i), stat="pts", line=10.5,
                                 p_first=p_over if first_is_over else 1 - p_over, over=over))
    return rows


def put_state(root, status, through="2026-10-20"):
    os.makedirs(f"{root}/state", exist_ok=True)
    json.dump(dict(status=status, through=through, changes=[]), open(f"{root}/state/{SO.STATE}", "w"))


def dk_props(ctx):
    rows = ctx.store.q("SELECT * FROM predictions WHERE market = 'prop' AND book = 'DraftKings' AND category = 'straight'")
    return [dict(r, inputs=json.loads(r["inputs"])) for r in rows]


# ---- rank correlation and the same-run check -----------------------------------------------
def test_rank_corr():
    assert SO.rank_corr([(1, 10), (2, 20), (3, 35)]) == pytest.approx(1.0)
    assert SO.rank_corr([(1, 30), (2, 20), (3, 10)]) == pytest.approx(-1.0)
    assert SO.rank_corr([(1, 1), (2, 1), (3, 1)]) is None          # no variation: undefined
    assert SO.rank_corr([(1, 2), (2, 1)]) is None                  # too few
    assert SO.rank_corr([(1, 1), (1, 2), (2, 3), (2, 4)]) == pytest.approx(0.894, abs=1e-3)   # ties share a rank


def _pairs(n, sign, seed):
    rnd = random.Random(seed)
    out = []
    for _ in range(n):
        m = rnd.gauss(0.5, 0.1)                 # the model's P(over)
        f = 0.5 + sign * (m - 0.5) * 0.5 + rnd.gauss(0, 0.03)     # first-listed fair chance
        out.append((f, m))
    return out


def test_run_check_reads_agreement_and_disagreement():
    agree = SO.run_check({"a": _pairs(60, +1, 1), "b": _pairs(60, +1, 2)})
    assert agree["slate"]["verdict"] == "strong" and agree["slate"]["n"] == 120
    assert all(g["verdict"] == "agree" for g in agree["games"].values())
    flipped = SO.run_check({"a": _pairs(60, -1, 1), "b": _pairs(60, -1, 2)})
    assert flipped["slate"]["verdict"] == "against" and all(g["verdict"] == "against" for g in flipped["games"].values())
    one_bad = SO.run_check({"a": _pairs(80, +1, 1), "b": _pairs(20, -1, 2)})
    assert one_bad["games"]["a"]["verdict"] == "agree" and one_bad["games"]["b"]["verdict"] == "against"
    thin = SO.run_check({"a": _pairs(5, +1, 1)})
    assert thin["slate"]["verdict"] == "thin" and thin["games"]["a"]["verdict"] == "thin"
    assert SO.run_check({})["slate"] == dict(n=0, r=None, verdict="thin")
    small = SO.run_check({"a": _pairs(50, +1, 3)})                # agreement, but too few pairs to count as strong
    assert small["slate"]["verdict"] == "agree"


def test_decide_needs_evidence_for_and_none_against():
    strong, agree = dict(n=300, r=0.42, verdict="strong"), dict(n=60, r=0.3, verdict="agree")
    against, thin = dict(n=300, r=-0.4, verdict="against"), dict(n=0, r=None, verdict="thin")
    assert SO.decide("auto", "confirmed", strong)[0] and SO.decide("auto", "confirmed", thin)[0]
    assert SO.decide("auto", None, strong)[0] and SO.decide("auto", "unconfirmed", strong)[0]
    assert not SO.decide("auto", None, agree)[0] and not SO.decide("auto", "unconfirmed", thin)[0]
    assert not SO.decide("auto", "confirmed", against)[0]          # this run argues against it
    assert not SO.decide("auto", "failed", strong)[0]              # results argue against it
    assert not SO.decide("off", "confirmed", strong)[0]
    assert all(isinstance(SO.decide(m, s, v)[1], str) and SO.decide(m, s, v)[1]
               for m in ("auto", "off") for s in (None, "confirmed", "failed") for v in (strong, against, thin))


# ---- the results check ---------------------------------------------------------------------
def test_slope_is_one_for_over_first_and_minus_one_for_under_first():
    f, se, n = SO.slope(graded(order="over_first"))
    assert n == 960 and abs(f - 1) < 3 * se and se < 0.25
    f2, se2, _ = SO.slope(graded(order="under_first"))
    assert f2 == pytest.approx(-f) and se2 == pytest.approx(se)
    assert SO.slope([]) is None and SO.slope(graded(n_slates=1, games=1, per_game=2)) is None    # too few to fit


def test_measure_confirms_fails_or_waits():
    ok = SO.measure(graded(order="over_first"))
    assert ok["status"] == "confirmed" and ok["through"] == "2026-11-06" and ok["pairs"] == 960
    assert [w["slates"] for w in ok["windows"]] == [1, 3, 6]       # 10 and 30 would repeat the 6 slates there are
    assert all(w["verdict"] == "ok" for w in ok["windows"])
    bad = SO.measure(graded(order="under_first"))
    assert bad["status"] == "failed" and any(w["verdict"] == "fail" for w in bad["windows"])
    coin = SO.measure(graded(n_slates=12, order="random"))
    assert coin["status"] in ("failed", "unconfirmed")            # never "confirmed" on a meaningless order
    assert SO.measure(graded(n_slates=12, order="random", seed=11))["status"] != "confirmed"
    few = SO.measure(graded(n_slates=1, games=1, per_game=30))
    assert few["status"] == "unconfirmed" and few["windows"][0]["verdict"] == "thin"
    assert SO.measure([])["status"] == "unconfirmed" and SO.measure([])["through"] is None


def test_a_flip_in_the_feed_is_caught_within_days():
    rows = graded(n_slates=20, order="over_first")
    slates = sorted({r["slate"] for r in rows})
    for r in rows:
        if r["slate"] >= slates[-3]:                               # the feed reverses for the last three slates
            r["p_first"] = 1 - r["p_first"]
    assert SO.measure(rows)["status"] == "failed"
    assert SO.measure([r for r in rows if r["slate"] < slates[-3]])["status"] == "confirmed"


# ---- closing pairs from the ledger ---------------------------------------------------------
def _odds(s, gid, pid, stat, line, sel, price, at, book="DraftKings"):
    s.put("odds", dict(snap_id=f"{gid}{pid}{stat}{line}{sel}{at}", game_id=gid, market="prop", selection=sel, line=line,
                       player_id=pid, player_name=f"P{pid}", stat=stat, price_dec=price, book=book, source="espn",
                       kind="current", observed_at=at, flags="side_unverified"))


def test_closing_pairs_take_the_last_line_before_tip_and_join_the_result():
    s = Store(None)
    s.put("games", dict(game_id="g1", season=2027, season_type="regular", start_utc="2026-11-05T00:00Z", home="A", away="B",
                        status="final", home_score=100, away_score=90, observed_at="2026-11-05T04:00:00Z", source="espn"))
    s.put("games", dict(game_id="g2", season=2027, season_type="regular", start_utc="2026-11-06T00:00Z", home="C", away="D",
                        status="scheduled", observed_at="2026-11-05T04:00:00Z", source="espn"))
    # p1 points: the line moves 19.5 -> 20.5 before tip; a quote after tip must be ignored
    for sel, a, b in (("side0", 1.90, 1.95), ("side1", 1.90, 1.87)):
        _odds(s, "g1", "p1", "pts", 19.5, sel, a, "2026-11-04T15:00:00Z")
        _odds(s, "g1", "p1", "pts", 20.5, sel, b, "2026-11-04T22:00:00Z")
        _odds(s, "g1", "p1", "pts", 22.5, sel, 1.5, "2026-11-05T00:30:00Z")
    _odds(s, "g1", "p2", "reb", 7.0, "side0", 2.10, "2026-11-04T15:00:00Z")      # lands on the line: a push
    _odds(s, "g1", "p2", "reb", 7.0, "side1", 1.74, "2026-11-04T15:00:00Z")
    _odds(s, "g1", "p3", "ast", 4.5, "side0", 1.80, "2026-11-04T15:00:00Z")      # did not play
    _odds(s, "g1", "p3", "ast", 4.5, "side1", 2.00, "2026-11-04T15:00:00Z")
    _odds(s, "g1", "p4", "pts", 9.5, "side0", 15.0, "2026-11-04T15:00:00Z")      # not a two-way market
    _odds(s, "g1", "p4", "pts", 9.5, "side1", 26.0, "2026-11-04T15:00:00Z")
    _odds(s, "g1", "p5", "pts", 9.5, "side0", 1.90, "2026-11-04T15:00:00Z")      # one side only
    _odds(s, "g1", "p6", "pts", 9.5, "side0", 1.90, "2026-11-04T15:00:00Z", book="ESPN BET")   # order not measured for this book
    _odds(s, "g1", "p6", "pts", 9.5, "side1", 1.90, "2026-11-04T15:00:00Z", book="ESPN BET")
    _odds(s, "g2", "p1", "pts", 19.5, "side0", 1.90, "2026-11-05T15:00:00Z")     # game not final
    _odds(s, "g2", "p1", "pts", 19.5, "side1", 1.90, "2026-11-05T15:00:00Z")
    for pid, played, pts, reb, ast in (("p1", 1, 24, 5, 3), ("p2", 1, 10, 7, 2), ("p3", 0, 0, 0, 0)):
        s.put("player_games", dict(game_id="g1", player_id=pid, player_name=f"P{pid}", team="A", starter=1, minutes=30.0,
                                   pts=pts, reb=reb, ast=ast, fg3m=1, played=played, observed_at="2026-11-05T04:00:00Z"))
    rows = {(r["player_id"], r["stat"]): r for r in SO.closing_pairs(s, "America/Toronto")}
    assert set(rows) == {("p1", "pts"), ("p2", "reb"), ("p3", "ast")}
    p1 = rows[("p1", "pts")]
    assert p1["line"] == 20.5 and (p1["price_first"], p1["price_second"]) == (1.95, 1.87) and p1["over"] == 1
    assert p1["slate"] == "2026-11-04" and p1["p_first"] == pytest.approx((1 / 1.95) / (1 / 1.95 + 1 / 1.87))
    assert rows[("p2", "reb")]["over"] is None and rows[("p2", "reb")]["value"] == 7        # push
    assert rows[("p3", "ast")]["over"] is None and rows[("p3", "ast")]["played"] is False   # void
    assert SO.closing_pairs(s, "America/Toronto", since="2026-11-05") == []


# ---- wiring ------------------------------------------------------------------------------
def test_without_evidence_nothing_changes(env):
    root, cfg, state = env
    ctx = pipeline.Ctx(NOW, cfg, root)
    pipeline.ingest(ctx)
    s = pipeline.predict(ctx)
    assert s["prop_side_order"]["used"] is False and s["prop_side_order"]["results"] is None
    props = dk_props(ctx)
    assert props and all(p["inputs"].get("side_basis") in (None, "bet365_ladder", "bet365_pair") for p in props)
    assert sum(p["inputs"]["price_basis"] == "conservative" for p in props) > len(props) * 0.9
    assert all(v["order"].startswith("not used") for v in s["prop_side_check"].values())


def test_confirmed_order_prices_every_pair_at_its_own_price(env):
    root, cfg, state = env
    put_state(root, "confirmed")
    ctx = pipeline.Ctx(NOW, cfg, root)
    pipeline.ingest(ctx)
    s = pipeline.predict(ctx)
    assert s["prop_side_order"] == dict(used=True, why="confirmed by results", results="confirmed",
                                        run=dict(n=0, r=None, verdict="thin"))
    props = dk_props(ctx)
    assert props and all(p["inputs"]["price_basis"] == "labelled" and p["inputs"]["side_basis"] == "listing_order" for p in props)
    assert all("conservative_price" not in p["inputs"]["quality_flags"] for p in props)
    assert all(v["order"] == "listing_order" and v["pairs_conservative"] == 0 for v in s["prop_side_check"].values())
    quotes = {}
    for r in ctx.store.q("SELECT * FROM odds WHERE market = 'prop' AND book = 'DraftKings' AND kind = 'current'"):
        quotes[(r["game_id"], r["player_id"], r["stat"], r["line"], r["selection"])] = r["price_dec"]
    for p in props:                                    # over = the first price listed, under = the second
        k = (p["game_id"], p["player_id"], p["stat"], p["line"])
        assert p["price_dec"] == quotes[k + ("side0" if p["selection"] == "over" else "side1",)]
    pair = {}
    for p in props:
        pair.setdefault((p["game_id"], p["player_id"], p["stat"], p["line"]), {})[p["selection"]] = p["inputs"]["fair"]
    assert all(set(v) == {"over", "under"} and v["over"] + v["under"] == pytest.approx(1) for v in pair.values())


@pytest.mark.parametrize("how", ["failed", "off", "run_against", "game_against", "labelled_feed_against"])
def test_any_evidence_against_puts_pairs_back_on_the_conservative_price(env, monkeypatch, how):
    root, cfg, state = env
    put_state(root, "failed" if how == "failed" else "confirmed")
    if how == "off":
        cfg["prop_sides"] = dict(listing_order=False)      # what YAML makes of a bare `off`
    against = dict(n=200, r=-0.4, verdict="against")
    if how == "run_against":
        monkeypatch.setattr(SO, "run_check", lambda by_game: dict(slate=against, games={}))
    if how == "game_against":
        monkeypatch.setattr(SO, "run_check", lambda by_game: dict(slate=dict(n=200, r=0.4, verdict="strong"),
                                                                   games={g: against for g in by_game}))
    if how == "labelled_feed_against":
        monkeypatch.setattr(pipeline, "verify_prop_sides", lambda *a, **k: (False, 0.95, 20))
        monkeypatch.setattr(pipeline, "verified_pairs", lambda *a, **k: set())
    ctx = pipeline.Ctx(NOW, cfg, root)
    pipeline.ingest(ctx)
    s = pipeline.predict(ctx)
    props = dk_props(ctx)
    assert props and not any(p["inputs"].get("side_basis") == "listing_order" for p in props)
    assert all(v["order"].startswith("not used: ") for v in s["prop_side_check"].values())
    if how == "labelled_feed_against":                 # the two sources contradict each other: no label at all
        assert all(p["inputs"]["price_basis"] == "conservative" for p in props)
        assert s["prop_side_order"]["used"] is True
    else:
        assert s["prop_side_order"]["used"] is (how == "game_against")


def test_settle_measures_the_order_and_writes_state_and_report_once(env, tmp_path):
    root, cfg, state = env
    ctx = pipeline.Ctx(NOW, cfg, root)
    pipeline.ingest(ctx); pipeline.predict(ctx); ctx.save_state()
    state["final"] = True
    later = pipeline.Ctx(NOW + dt.timedelta(hours=14), cfg, root)
    pipeline.ingest(later)
    out = pipeline.settle(later)
    assert out["prop_side_order"] in ("confirmed", "unconfirmed", "failed")
    st = SO.load(root)
    assert st["status"] == out["prop_side_order"] and st["book"] == "DraftKings" and st["changes"] == []
    rep = tmp_path / "reports" / SO.REPORT
    assert rep.exists() and "Status:" in rep.read_text()
    before = (os.stat(f"{root}/state/{SO.STATE}").st_mtime_ns, rep.stat().st_mtime_ns)
    assert SO.refresh(later)["status"] == st["status"]            # nothing new: nothing rewritten
    assert before == (os.stat(f"{root}/state/{SO.STATE}").st_mtime_ns, rep.stat().st_mtime_ns)


def test_a_status_change_is_recorded_and_noted(env, tmp_path):
    root, cfg, state = env
    put_state(root, "confirmed")
    ctx = pipeline.Ctx(NOW, cfg, root)                  # an empty ledger: nothing graded, so not confirmed any more
    r = SO.refresh(ctx)
    st = SO.load(root)
    assert r["status"] == st["status"] == "unconfirmed"
    assert [(c["from"], c["to"]) for c in st["changes"]] == [("confirmed", "unconfirmed")]
    assert any("confirmed -> unconfirmed" in n for n in ctx.notes)
    assert "Status changes" in (tmp_path / "reports" / SO.REPORT).read_text()


def test_a_broken_check_never_blocks_settlement(env, monkeypatch):
    root, cfg, state = env
    ctx = pipeline.Ctx(NOW, cfg, root)
    pipeline.ingest(ctx)
    monkeypatch.setattr(SO, "refresh", lambda c: (_ for _ in ()).throw(RuntimeError("boom")))
    out = pipeline.settle(ctx)
    assert "prop_side_order" not in out and any("prop side order check failed" in n for n in ctx.notes)


def test_a_stale_confirmation_is_not_relied_on(env):
    today = dt.date(2026, 10, 21)
    assert SO.status(dict(status="confirmed", through="2026-10-20"), today) == "confirmed"
    assert SO.status(dict(status="confirmed", through="2026-10-01"), today) == "unconfirmed"     # 20 days without a graded slate
    assert SO.status(dict(status="confirmed"), today) == "unconfirmed"
    assert SO.status(dict(status="failed", through="2026-09-01"), today) == "failed"             # stays until a refresh clears it
    assert SO.status({}, today) is None
    root, cfg, state = env
    put_state(root, "confirmed", through="2026-09-30")
    ctx = pipeline.Ctx(NOW, cfg, root)
    pipeline.ingest(ctx)
    s = pipeline.predict(ctx)
    assert s["prop_side_order"]["used"] is False and s["prop_side_order"]["results"] == "unconfirmed"


def test_config_accepts_auto_and_off_only():
    from nbapicks import config
    c = config.load()
    assert c["prop_sides"]["listing_order"] == "auto"
    for ok in ("auto", "off", True, False):
        c["prop_sides"] = dict(listing_order=ok); config.validate(c)
    c["prop_sides"] = dict(listing_order="sometimes")
    with pytest.raises(config.ConfigError):
        config.validate(c)
    del c["prop_sides"]; config.validate(c)                 # absent: the default is auto
