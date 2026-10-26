import datetime as dt
import random

import pytest

from nbapicks.models import props_v1 as V1
from nbapicks.models.props_v1 import PropModelV1

START = dt.date(2023, 11, 1)
OPPS = ["BBB", "CCC", "DDD", "EEE"]


def synth(n=40, mate_out=(), seed=1, start=START):
    """Team AAA plays every second day. P1's minutes and points jump in games where his
    teammate M1 sits (indices in ``mate_out``)."""
    rnd = random.Random(seed)
    games, rows = {}, []
    for i in range(n):
        d = start + dt.timedelta(days=2 * i)
        gid = f"g{i}"
        opp = OPPS[i % 4]
        games[gid] = dict(start_utc=f"{d.isoformat()}T23:00Z", home="AAA", away=opp)
        out = i in mate_out
        rows.append(dict(game_id=gid, player_id="p1", player_name="Pat One", team="AAA", starter=1,
                         minutes=36 if out else 28, pts=26 if out else 14 + rnd.randint(-1, 1), reb=5, ast=4,
                         fg3m=2, played=1))
        rows.append(dict(game_id=gid, player_id="m1", player_name="Max Mate", team="AAA", starter=1,
                         minutes=0 if out else 34, pts=0 if out else 22, reb=6, ast=5, fg3m=3, played=0 if out else 1))
        for k in range(3):
            rows.append(dict(game_id=gid, player_id=f"a{k}", player_name=f"A Guy{k}", team="AAA", starter=int(k < 2),
                             minutes=20 - k, pts=8 + k, reb=3, ast=2, fg3m=1, played=1))
        for k in range(5):
            rows.append(dict(game_id=gid, player_id=f"{opp}{k}", player_name=f"{opp} Guy{k}", team=opp, starter=int(k < 3),
                             minutes=30 - 2 * k, pts=12 + (3 if opp == "EEE" else 0), reb=4, ast=3, fg3m=1, played=1))
    return rows, games


def day(i):
    return START + dt.timedelta(days=2 * i)


def test_leakage_future_games_never_change_prediction():
    rows, games = synth(30)
    d = day(20)
    base = PropModelV1([r for r in rows], games).predict("p1", "pts", d, "BBB", True)
    # rewrite every game on/after d with absurd values: prediction must be identical
    later = {gid for gid, g in games.items() if g["start_utc"][:10] >= d.isoformat()}
    rows2 = [dict(r, pts=99, minutes=48, reb=30) if r["game_id"] in later else r for r in rows]
    extra = dict(start_utc=f"{d.isoformat()}T23:30Z", home="AAA", away="CCC")
    games2 = dict(games, gx=extra)
    rows2.append(dict(game_id="gx", player_id="p1", player_name="Pat One", team="AAA", starter=1, minutes=48, pts=80,
                      reb=1, ast=1, fg3m=9, played=1))
    other = PropModelV1(rows2, games2).predict("p1", "pts", d, "BBB", True)
    assert other["mean"] == pytest.approx(base["mean"])
    assert other["var"] == pytest.approx(base["var"])
    assert other["explain"] == base["explain"]


def test_abstains_under_five_games():
    rows, games = synth(10)
    m = PropModelV1(rows, games)
    assert m.predict("p1", "pts", day(4), "BBB", True) is None      # 4 earlier games
    assert m.predict("p1", "pts", day(5), "BBB", True) is not None  # 5 earlier games
    assert m.predict("nobody", "pts", day(9), "BBB", True) is None


def test_teammates_out_raises_minutes_and_mean():
    rows, games = synth(40, mate_out={3, 7, 11, 15, 19, 23, 27})
    m = PropModelV1(rows, games, params={"mate_k": 5.0})
    d = day(30)
    assert m.key_teammates("p1", "AAA", d)[0] == "m1"
    base = m.predict("p1", "pts", d, "BBB", True)
    out = m.predict("p1", "pts", d, "BBB", True, teammates_out=["Max Mate"])
    assert out["minutes"] > base["minutes"]
    assert out["mean"] > base["mean"]
    assert out["explain"]["teammates_out"] == ["Max Mate"]
    # shrinkage: a huge K means (almost) no change
    m2 = PropModelV1(rows, games, params={"mate_k": 1e9})
    assert m2.predict("p1", "pts", d, "BBB", True, teammates_out=["m1"])["mean"] == pytest.approx(base["mean"], rel=1e-3)
    # an unknown or non-key name changes nothing
    assert m.predict("p1", "pts", d, "BBB", True, teammates_out=["Someone Else"])["mean"] == pytest.approx(base["mean"])


def test_prob_sums_to_one_and_pushes():
    rows, games = synth(20)
    m = PropModelV1(rows, games)
    p = m.predict("p1", "pts", day(15), "BBB", True)
    for line in (13.5, 14.0, 20.0):
        ow, op = m.prob(p, line, "over")
        uw, up = m.prob(p, line, "under")
        assert op == pytest.approx(up)
        assert ow + uw + op == pytest.approx(1.0, abs=1e-9)
        assert (op > 0) == (line == int(line))


def test_explain_counts_exact_with_pushes():
    rows, games = synth(12)
    vals = [10, 12, 12, 15, 9, 12, 20, 12, 11, 13, 14, 30]
    for r in rows:
        if r["player_id"] == "p1":
            r["pts"] = vals[int(r["game_id"][1:])]
    m = PropModelV1(rows, games)
    d = day(11)
    p = m.predict("p1", "pts", d, "EEE", True)
    ex = m.explain_for_line(p, "p1", "pts", 12, "over", d, "EEE")
    prior = vals[:11]
    assert ex["line_hits"] == dict(h=sum(v > 12 for v in prior), n=sum(v != 12 for v in prior), pushes=4)
    assert ex["line_hits_last10"] == dict(h=sum(v > 12 for v in prior[-10:]), n=sum(v != 12 for v in prior[-10:]),
                                          pushes=sum(v == 12 for v in prior[-10:]))
    vs = [v for i, v in enumerate(prior) if OPPS[i % 4] == "EEE"]   # games 3 and 7
    assert ex["vs_opp"]["n"] == sum(v != 12 for v in vs) and ex["vs_opp"]["pushes"] == sum(v == 12 for v in vs)
    assert ex["vs_opp"]["avg"] == pytest.approx(sum(vs) / len(vs), abs=0.01)
    assert ex["last5"] == [float(x) for x in prior[::-1][:5]]
    under = m.explain_for_line(dict(p, explain=dict(p["explain"])), "p1", "pts", 12, "under", d, "EEE")["line_hits"]
    assert under["h"] == sum(v < 12 for v in prior) and under["n"] == ex["line_hits"]["n"]
    assert "pushes are excluded" in ex["counts_note"]


def test_explain_keys_follow_contract():
    rows, games = synth(20)
    p = PropModelV1(rows, games).predict("p1", "reb", day(15), "EEE", True, injury_status="Questionable")
    need = {"season", "last5", "last10_avg", "line_hits", "line_hits_last10", "vs_opp", "exp_minutes", "minutes_basis",
            "role", "opp_def", "teammates_out", "injury_status", "mean", "sd", "flags"}
    assert need <= set(p["explain"])
    assert set(p["explain"]["opp_def"]) == {"rank", "teams", "allowed_pg"}
    assert p["explain"]["role"] == "starter" and "injury_questionable" in p["explain"]["flags"]
    assert {"mean", "var", "sd", "minutes", "games", "explain"} <= set(p)


def test_override_injury_out_and_opponent_direction():
    rows, games = synth(30)
    m = PropModelV1(rows, games, params={"opp_k": {"pts": 0.0}})
    d = day(25)
    assert m.predict("p1", "pts", d, "BBB", True, minutes_override=20)["minutes"] == 20
    assert m.predict("p1", "pts", d, "BBB", True, minutes_override=20)["explain"]["minutes_basis"] == "override"
    assert m.predict("p1", "pts", d, "BBB", True, injury_status="Out") is None
    # AAA's players score the same against everyone, but EEE players score more against AAA;
    # use an EEE player: opponent AAA allows the same as others, so check AAA vs a soft defence instead
    soft = m.predict("p1", "pts", d, "BBB", True)
    assert m.opp_factor("AAA", "pts", d) > 1.0        # AAA allows more pts than league average (EEE's boost)
    assert soft["opp_factor"] == pytest.approx(m.opp_factor("BBB", "pts", d))


def test_returning_from_absence_flag_and_previous_season_fallback():
    rows, games = synth(30)
    rows = [r for r in rows if not (r["player_id"] == "a0" and 10 <= int(r["game_id"][1:]) < 20)]
    m = PropModelV1(rows, games)
    p = m.predict("a0", "pts", day(20), "BBB", True)   # a0 missed 10 team games before game 20
    assert p is not None
    p2 = m.predict("a0", "pts", day(15), "BBB", True)
    assert "returning_from_absence" in p2["explain"]["flags"]


def test_attempt_path_when_columns_present():
    rows, games = synth(20)
    for r in rows:
        r["fga"], r["fg3a"], r["fta"] = 10, 5, 2
    d = day(15)
    m = PropModelV1(rows, games, params={"make_k": 50.0})
    p_att = m.predict("p1", "fg3m", d, "BBB", True)
    m_off = PropModelV1(rows, games)
    p_off = m_off.predict("p1", "fg3m", d, "BBB", True)
    assert p_att is not None and p_att["mean"] > 0
    assert p_att["rate"] != pytest.approx(p_off["rate"])
    # missing columns (empty strings) fall back to the plain rate
    for r in rows:
        r["fga"] = ""
    assert PropModelV1(rows, games, params={"make_k": 50.0}).predict("p1", "fg3m", d, "BBB", True)["rate"] == pytest.approx(p_off["rate"])


def test_constants_have_every_stat():
    for k in ("rate_half_life", "rate_prev_w", "rate_k", "opp_k"):
        assert set(V1.PARAMS[k]) == set(V1.STATS)
    assert set(V1.DISPERSION) == set(V1.STATS) and all(v > 0 for v in V1.DISPERSION.values())
