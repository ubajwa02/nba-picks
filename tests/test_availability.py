import datetime as dt, random

import pytest

from nbapicks.models import availability as AV
from nbapicks.models.ratings import RatingsModel, RatingsParams, Game

D0 = dt.date(2023, 1, 1)


def _box(gid, pid, team, minutes, pts, played=1, **kw):
    r = dict(game_id=gid, player_id=pid, player_name=f"P{pid}", team=team, minutes=str(minutes), pts=str(pts),
             reb="0", ast="0", stl="0", blk="0", tov="0", played=str(played))
    r.update({k: str(v) for k, v in kw.items()})
    return r


def _season(n=12):
    """Team AAA plays every day; star '1' scores 30 in 36 min, then sits game 11; bench '2' 10 in 12 min."""
    games, rows = {}, []
    for i in range(n):
        gid = f"g{i}"
        games[gid] = dict(date=D0 + dt.timedelta(days=i), season=2023)
        if i == 10:
            rows.append(_box(gid, "1", "AAA", 0, "", played=0))
        else:
            rows.append(_box(gid, "1", "AAA", 36, 30 + i))
        rows.append(_box(gid, "2", "AAA", 12, 10))
    return games, rows


def test_production_metric():
    r = dict(pts="20", reb="10", ast="5", stl="2", blk="1", tov="3", fga="18")
    assert AV.production(r) == pytest.approx(20 + 4 + 3.5 + 2 + 0.7 - 3)   # fga is deliberately unused


def test_values_are_point_in_time():
    games, rows = _season()
    before = D0 + dt.timedelta(days=5)
    v = AV.player_values(rows, games, before)
    # 5 games (days 0-4) strictly before day 5: the star qualifies; values use nothing from day 5 on
    assert set(v) == {"1", "2"}
    assert 30 < v["1"] < 34
    v4 = AV.player_values(rows, games, D0 + dt.timedelta(days=4))
    assert v4 == {}                               # only 4 games: below min_games
    # changing a later game cannot change an earlier value
    rows2 = [dict(r, pts="99") if r["game_id"] == "g7" else r for r in rows]
    assert AV.player_values(rows2, games, before) == v
    # a previous season's games do not count
    games_prev = {k: dict(g, season=2022 if k in ("g0", "g1") else 2023) for k, g in games.items()}
    assert "1" not in AV.player_values(rows, games_prev, before, season=2023)


def test_regulars_and_missing_detection():
    games, rows = _season()
    ix = AV.BoxIndex(rows, games)
    day10 = D0 + dt.timedelta(days=10)
    regs = AV.expected_regulars(rows, games, "AAA", day10, season=2023)
    assert regs == {"1"}                          # 36 mpg; the bench player (12 mpg) is not a regular
    vals = AV.player_values(rows, games, day10, index=ix)
    val, names = AV.missing_value("AAA", vals, regs, played_ids=ix.played_ids("g10", "AAA"), names=ix.names)
    assert names == ["P1"] and val == pytest.approx(vals["1"])
    val, names = AV.missing_value("AAA", vals, regs, played_ids=ix.played_ids("g9", "AAA"), names=ix.names)
    assert (val, names) == (0.0, [])
    # live: injury report ids; a listed non-regular adds nothing
    assert AV.missing_value("AAA", vals, regs, out_ids=["2"])[0] == 0.0
    assert AV.missing_value("AAA", vals, regs, out_ids=["1"])[1] == ["1"]
    with pytest.raises(ValueError):
        AV.missing_value("AAA", vals, regs)


def test_attach_marks_coverage_and_games_without_box():
    from nbapicks.teams import TEAMS
    a, b = sorted(TEAMS)[:2]
    gs, rows = [], []
    for i in range(8):
        g = Game(f"x{i}", D0 + dt.timedelta(days=i), a, b, 100, 99); g.season = 2023; gs.append(g)
        for t, pid in ((a, "10"), (b, "20")):
            if i != 7 or t != a:
                rows.append(_box(g.game_id, pid, t, 34, 25))
    nobox = Game("y0", D0 + dt.timedelta(days=9), a, b, 100, 99); nobox.season = 2023; gs.append(nobox)
    cov = AV.attach(gs, rows)
    assert cov["2023"] == dict(games=9, games_with_box=8, games_with_feature=3)
    g7 = gs[7]
    assert g7.avail_known and g7.home_missing > 20 and g7.home_missing_names == ["P10"] and g7.away_missing == 0
    assert not gs[2].avail_known and gs[2].home_missing == 0          # too few earlier team games
    assert not nobox.avail_known and nobox.home_missing == 0


def _synth(beta=-0.15, seed=3, n_days=160):
    """Margins fall by `beta` per point of (home_missing - away_missing); totals by 0.2 per point missing."""
    rnd = random.Random(seed)
    from nbapicks.teams import TEAMS
    teams = sorted(TEAMS)
    true = {t: (i - 15) * 0.6 for i, t in enumerate(teams)}
    games = []
    for day in range(n_days):
        rnd.shuffle(teams)
        for i in range(0, 14, 2):
            h, a = teams[i], teams[i + 1]
            hm = rnd.choice([0, 0, 0, 15, 30]); am = rnd.choice([0, 0, 0, 15, 30])
            m = 2.5 + true[h] - true[a] + beta * (hm - am) + rnd.gauss(0, 11)
            tot = 225 - 0.2 * (hm + am) + rnd.gauss(0, 16)
            hs = int(round((tot + m) / 2)); as_ = int(round((tot - m) / 2))
            if hs == as_:
                hs += 1
            g = Game(f"s{day}-{i}", dt.date(2024, 10, 22) + dt.timedelta(days=day), h, a, hs, as_)
            g.home_missing, g.away_missing, g.avail_known = float(hm), float(am), True
            games.append(g)
    return games


def test_coefficient_sign_and_prediction_adjustment():
    games = _synth()
    as_of = games[-1].date + dt.timedelta(days=1)
    m = RatingsModel(RatingsParams(availability=True)).fit(games, as_of)
    assert m.avail_n == len(games)
    assert -0.25 < m.avail_m < -0.05            # missing home players reduce the home margin
    assert m.avail_t < 0                         # and the total
    t = sorted({g.home for g in games})
    p0 = m.predict(t[0], t[1])
    p1 = m.predict(t[0], t[1], home_missing=30.0)
    assert p1["mu_margin"] < p0["mu_margin"] and p1["mu_total"] < p0["mu_total"]
    assert p1["availability_adj"]["margin"] == pytest.approx(30 * m.avail_m)
    # only prior games are used: games on/after as_of are ignored
    early = games[0].date + dt.timedelta(days=60)
    m2 = RatingsModel(RatingsParams(availability=True)).fit(games, early)
    assert m2.avail_n == sum(g.date < early for g in games)


def test_shrinkage_pulls_toward_zero():
    games = _synth()
    as_of = games[-1].date + dt.timedelta(days=1)
    loose = RatingsModel(RatingsParams(availability=True, avail_ridge=0)).fit(games, as_of)
    tight = RatingsModel(RatingsParams(availability=True, avail_ridge=10000)).fit(games, as_of)
    assert abs(tight.avail_m) < abs(loose.avail_m)


def test_defaults_unchanged_when_availability_off():
    games = _synth()
    as_of = games[-1].date + dt.timedelta(days=1)
    assert RatingsParams().availability is False
    off = RatingsModel(RatingsParams()).fit(games, as_of)
    t = sorted({g.home for g in games})
    a, b = off.predict(t[0], t[1]), off.predict(t[0], t[1], home_missing=40.0, away_missing=0.0)
    assert a == b and "availability_adj" not in a and off.avail_m == 0.0
    # the feature on the games changes nothing either: same as a model fitted on games without it
    plain = [Game(g.game_id, g.date, g.home, g.away, g.home_score, g.away_score) for g in games]
    assert RatingsModel(RatingsParams()).fit(plain, as_of).predict(t[0], t[1]) == a


def test_unknown_feature_games_are_left_out_of_the_fit():
    games = _synth()
    for g in games:
        g.avail_known = False
    as_of = games[-1].date + dt.timedelta(days=1)
    m = RatingsModel(RatingsParams(availability=True)).fit(games, as_of)
    assert m.avail_n == 0 and m.avail_m == 0.0 and m.avail_t == 0.0
