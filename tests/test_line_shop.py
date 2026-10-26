import datetime as dt
from nbapicks.models.ratings import Game
from nbapicks.strategies.line_shop import bets_for_game, best_per_side, family


def _ml(h, a):
    return [dict(kind="close", market="ml", selection="home", line="", price_dec=h),
            dict(kind="close", market="ml", selection="away", line="", price_dec=a)]


def test_family_groups_caesars_variants():
    assert family("Caesars Sportsbook (New Jersey)") == family("Caesar's") == family("Caesars") == "caesars"


def test_outlier_book_is_priced_against_the_others_only():
    g = Game("g", dt.date(2018, 1, 1), "BOS", "NY", 110, 100); g.season = 2018
    books = {"A": _ml(1.5, 2.7), "B": _ml(1.52, 2.65), "C": _ml(1.5, 2.7), "D": _ml(1.5, 3.2)}   # D's away price is generous
    bets = best_per_side(bets_for_game(g, books))
    away = next(b for b in bets if b["selection"] == "away")
    assert away["book"] == "D" and away["ev"] > 0.1 and away["result"] == "loss" and away["net"] == -1.0
    home = next(b for b in bets if b["selection"] == "home")
    assert home["ev"] < 0.01


def test_needs_three_book_families():
    g = Game("g", dt.date(2018, 1, 1), "BOS", "NY", 110, 100); g.season = 2018
    books = {"Caesars": _ml(1.5, 2.7), "Caesar's": _ml(1.5, 2.7), "D": _ml(1.5, 3.2)}
    assert bets_for_game(g, books) == []
