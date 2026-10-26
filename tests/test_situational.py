import datetime as dt
from nbapicks.models.ratings import Game
from nbapicks.strategies.situational import RULES, _early


def test_rules_fire_on_their_conditions():
    g = Game("g", dt.date(2018, 11, 1), "BOS", "NY", 100, 110); g.home_rest, g.away_rest = 1, 1
    q = {"ml": {"home": (None, 2.4, ""), "away": (None, 1.6, "")}, "spread": {"home": (4.5, 1.9, ""), "away": (-4.5, 1.9, "")}}
    assert RULES["home_dog_ml"][2](g, q) and RULES["road_fav_ml"][2](g, q) and RULES["both_b2b_under"][2](g, q)
    assert not RULES["fade_big_fav_spread"][2](g, q)
    assert _early(g) and not _early(Game("h", dt.date(2019, 1, 5), "BOS", "NY", 1, 2))
