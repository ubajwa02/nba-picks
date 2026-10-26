"""Skeptic reproductions. Each test asserts the CORRECT behaviour; a failure = bug present."""
import datetime as dt, random, math
import pytest
from nbapicks import research as R, metrics as M
from nbapicks.settle import settle_leg, GameResult
from nbapicks.props import verify_prop_sides
from nbapicks import pipeline
from nbapicks.store import Store
import yaml


def _noise_recs(seed=3, n=6000):
    rnd = random.Random(seed)
    recs = []
    for i in range(n):
        f = rnd.uniform(0.2, 0.8)
        y = rnd.random() < f
        p = min(0.95, max(0.05, f + rnd.gauss(0, 0.15)))  # noisy model, no information beyond f
        recs.append(dict(selection="home", result="win" if y else "loss", prob=p, push=0.0, fair=f, price=1 / f * 0.96,
                         net=(1 / f * 0.96 - 1) if y else -1.0, season=2015 + i % 6))
    return recs


def test_explore_logloss_gate_is_not_tautological():
    # in-sample fitting of w makes the gain >= 0 by construction; out-of-fold + t >= 2 must reject a useless model
    recs = _noise_recs()
    oof = R.explore_oof(recs)
    gates = yaml.safe_load(open("config/gates.yaml"))["paper"]
    passes = (oof["gain"] or -1) > gates["explore_logloss_gain_vs_market"] and (oof["t"] or 0) >= gates["logloss_gain_min_t"]
    assert not passes, oof


def test_threshold_choice_handles_zero_roi_and_min_bets():
    recs = [dict(selection="home", result="win", prob=0.6, push=0.0, fair=0.5, price=2.0, net=1.0),
            dict(selection="home", result="loss", prob=0.6, push=0.0, fair=0.5, price=2.0, net=-1.0)]
    # ROI exactly 0.0 is a valid choice, not ranked as -9
    assert R.choose_threshold(recs, 1.0, [0.0], min_bets=1) == 0.0
    # too few bets: no threshold qualifies
    assert R.choose_threshold(recs, 1.0, [0.0], min_bets=100) is None


def test_suspended_game_voids_after_48h():
    g = dict(status="suspended", start_utc="2026-11-01T00:00:00Z")
    assert pipeline.effective_status(g, dt.datetime(2026, 11, 1, 12, tzinfo=dt.timezone.utc)) == "suspended"
    late = pipeline.effective_status(g, dt.datetime(2026, 11, 3, 1, tzinfo=dt.timezone.utc))
    assert settle_leg("spread", "home", -3.5, GameResult(late)) == "void"


def test_prop_side_dissenting_pair_stays_unverified():
    from nbapicks.props import verified_pairs, pair_key
    espn, b365 = [], []
    for i in range(10):
        name = f"Player{chr(65+i)}"
        over, under = (1.80, 2.05) if i < 9 else (2.05, 1.80)   # player J listed the other way round
        espn += [dict(market="prop", kind="current", player_name=name, stat="pts", line=19.5, selection="side0", price_dec=over),
                 dict(market="prop", kind="current", player_name=name, stat="pts", line=19.5, selection="side1", price_dec=under)]
        b365.append(dict(market="prop", player_name=name, stat="pts", line=19.5, price_dec=1.80, selection="over"))
    first_is_over, share, n = verify_prop_sides(espn, b365, min_n=8)
    ok = verified_pairs(espn, b365, first_is_over)
    assert first_is_over is True and len(ok) == 9
    assert pair_key(dict(player_name="PlayerJ", stat="pts", line=19.5)) not in ok
    # a pair with no bet365 reference is never verified
    assert pair_key(dict(player_name="Nobody", stat="pts", line=19.5)) not in ok


def test_stale_source_quote_is_aged_by_source_time(tmp_path):
    cfg = yaml.safe_load(open("config/nbapicks.yaml"))
    t0 = dt.datetime(2026, 11, 1, 12, tzinfo=dt.timezone.utc)
    ctx = pipeline.Ctx(t0, cfg, str(tmp_path))
    ctx.store.put("games", dict(game_id="g1", start_utc="2026-11-02T00:00:00Z", home="BOS", away="NY", status="scheduled",
                                observed_at="2026-11-01T12:00:00Z", source="espn"))
    row = dict(game_id="g1", market="prop", selection="side0", line=19.5, player_id="p1", stat="pts", price_dec=1.9,
               book="DraftKings", source="espn", kind="current", observed_at="x", source_updated_at="2026-11-01T06:00:00Z")
    pipeline.put_odds(ctx, [row])
    ctx.now = t0 + dt.timedelta(hours=5)
    pipeline.put_odds(ctx, [row])  # identical quote, source says it was last updated 11h ago
    r = list(pipeline.latest_quotes(ctx, "g1").values())[0]["side0"]
    assert r["as_of"] == "2026-11-01T06:00:00Z"   # the freshness gate sees the book's own time


def test_holdout_threshold_key_is_robust():
    bets = {str(t): {"t": t} for t in [0.0, 0.02, 0.03, 0.05, 0.08]}
    assert R.bets_at(bets, "0.030") == {"t": 0.03}
    with pytest.raises(KeyError):
        R.bets_at(bets, "0.04")


def test_line_quality_drops_in_game_and_impossible_lines():
    from nbapicks.backtest import clean_quotes
    def pair(book, ml_h, ml_a, sp, tot):
        return [dict(kind="close", market="ml", selection="home", line="", price_dec=ml_h),
                dict(kind="close", market="ml", selection="away", line="", price_dec=ml_a),
                dict(kind="close", market="spread", selection="home", line=sp, price_dec=1.91),
                dict(kind="close", market="spread", selection="away", line=-sp, price_dec=1.91),
                dict(kind="close", market="total", selection="over", line=tot, price_dec=1.91),
                dict(kind="close", market="total", selection="under", line=tot, price_dec=1.91)]
    books = {"A": pair("A", 1.59, 2.45, -25.5, 220.5),      # ML says ~-3.5, spread says -25.5: in-game
             "B": pair("B", 1.59, 2.45, -3.5, 221.0), "C": pair("C", 1.6, 2.4, -3.0, 220.0),
             "D": pair("D", 1.6, 2.4, -110.0, 236.5)}       # price in the line field; total far off consensus
    clean, drops = clean_quotes(books, "close")
    assert "spread" not in clean["A"] and "ml" not in clean["A"] and "total" in clean["A"]
    assert "spread" not in clean["D"] and "total" not in clean["D"]
    assert "spread" in clean["B"] and "spread" in clean["C"]
    assert drops["ml_spread_mismatch"] == 1 and drops["impossible_line"] == 1 and drops["total_off_consensus"] == 1


def test_bet365_milestones_keep_every_line_and_verify_dk_pairs(tmp_path):
    """NBA-033: milestone props are all 'over' rows; keying quotes without the line kept only one."""
    from nbapicks.props import verify_prop_sides, verified_pairs
    cfg = yaml.safe_load(open("config/nbapicks.yaml"))
    t0 = dt.datetime(2026, 11, 1, 12, tzinfo=dt.timezone.utc)
    ctx = pipeline.Ctx(t0, cfg, str(tmp_path))
    ctx.store.put("games", dict(game_id="g1", start_utc="2026-11-02T00:00:00Z", home="BOS", away="NY", status="scheduled",
                                observed_at="2026-11-01T12:00:00Z", source="espn"))
    rows = []
    for i in range(10):
        name = f"Player {chr(65 + i)}"
        for line, dec in ((14.5, 1.3), (19.5, 1.9), (24.5, 3.2)):
            rows.append(dict(game_id="g1", market="prop", selection="over", line=line, player_name=name, stat="pts",
                             price_dec=dec, book="bet365", source="moviodds", kind="current", observed_at="x"))
        rows += [dict(game_id="g1", market="prop", selection=s, line=19.5, player_id=f"p{i}", player_name=name,
                      stat="pts", price_dec=d, book="DraftKings", source="espn", kind="current", observed_at="x")
                 for s, d in (("side0", 1.95), ("side1", 1.87))]
    pipeline.put_odds(ctx, rows)
    q = pipeline.latest_quotes(ctx, "g1")
    b365 = [r for k, s in q.items() if k[0] == "bet365" for r in s.values()]
    dk = [r for k, s in q.items() if k[0] == "DraftKings" for r in s.values()]
    assert len(b365) == 30 and len(dk) == 20
    first, _, n = verify_prop_sides(dk, b365, min_n=8)
    assert n == 10 and first is False   # side1 (shorter price) is nearer bet365's over 1.9
    assert len(verified_pairs(dk, b365, first)) == 10
