import datetime as dt, random
import pytest
from nbapicks.models.ratings import RatingsModel, RatingsParams, Game, add_rest_days


def synth(n_days=150, seed=1):
    rnd = random.Random(seed)
    from nbapicks.teams import TEAMS
    teams = sorted(TEAMS)
    true = {t: (i - 15) * 0.8 for i, t in enumerate(teams)}
    games, d0 = [], dt.date(2024, 10, 22)
    gid = 0
    for day in range(n_days):
        rnd.shuffle(teams)
        for i in range(0, 14, 2):
            h, a = teams[i], teams[i + 1]
            m = 2.5 + true[h] - true[a] + rnd.gauss(0, 12)
            tot = 225 + rnd.gauss(0, 18)
            hs = int(round((tot + m) / 2)); as_ = int(round((tot - m) / 2))
            if hs == as_:
                hs += 1
            games.append(Game(str(gid), d0 + dt.timedelta(days=day), h, a, hs, as_)); gid += 1
    return games, true


def test_recovers_strength_and_hca_without_lookahead():
    games, true = synth()
    as_of = games[-1].date
    m = RatingsModel(RatingsParams(half_life_days=500)).fit(games, as_of)
    r = m.ratings()
    best, worst = max(true, key=true.get), min(true, key=true.get)
    assert r[best] > r[worst] + 10
    pred = m.predict(best, worst)
    assert pred["hca"] == pytest.approx(2.5, abs=1.2)
    assert 215 < pred["mu_total"] < 235
    # games on as_of itself were excluded from the fit
    assert m.n_games == sum(1 for g in games if g.date < as_of)


def test_refuses_with_too_little_data():
    games, _ = synth(n_days=5)
    m = RatingsModel().fit(games, games[-1].date + dt.timedelta(days=1))
    assert not m.ready()
    with pytest.raises(RuntimeError):
        m.predict("BOS", "NY")


def test_rest_days():
    gs = [Game("1", dt.date(2025, 1, 1), "BOS", "NY", 1, 0), Game("2", dt.date(2025, 1, 2), "NY", "MIA", 1, 0)]
    add_rest_days(gs)
    assert gs[1].home_rest == 1 and gs[1].away_rest is None


def test_probabilities_are_coherent():
    games, _ = synth()
    m = RatingsModel().fit(games, games[-1].date)
    pred = m.predict("BOS", "NY")
    ph, _ = RatingsModel.prob(pred, "ml", "home", None)
    pa, _ = RatingsModel.prob(pred, "ml", "away", None)
    assert ph + pa == pytest.approx(1)
    w, p = RatingsModel.prob(pred, "spread", "home", -round(pred["mu_margin"]) - 0.5)
    assert 0.4 < w < 0.6


def test_total_trend_does_not_extrapolate_across_the_offseason():
    import datetime as dt, random
    from nbapicks.models.ratings import Game, RatingsModel, RatingsParams
    from nbapicks.teams import TEAMS
    rnd = random.Random(1); teams = sorted(TEAMS); games = []; gid = 0
    for day in range(170):                      # a season whose scoring drifts down late (playoff-like)
        d = dt.date(2025, 10, 21) + dt.timedelta(days=day)
        base = 116 - 6 * day / 170
        rnd.shuffle(teams)
        for i in range(0, 10, 2):
            games.append(Game(f"g{gid}", d, teams[i], teams[i + 1], int(base + rnd.gauss(0, 10)), int(base + rnd.gauss(0, 10)))); gid += 1
    m = RatingsModel(RatingsParams(total_trend=True)).fit(games, dt.date(2026, 10, 20))   # 130 days after the last game
    mu = m.predict(teams[0], teams[1])["mu_total"]
    assert 210 < mu < 230, mu       # near the latest level (~220), not extrapolated far below it
