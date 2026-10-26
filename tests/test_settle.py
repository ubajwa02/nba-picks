import pytest
from nbapicks.settle import (GameResult, settle_leg, net_profit, settle_parlay,
                             WIN, LOSS, PUSH, VOID, PENDING)

F = lambda h, a: GameResult("final", h, a)


def test_moneyline():
    assert settle_leg("ml", "home", None, F(110, 100)) == WIN
    assert settle_leg("ml", "away", None, F(110, 100)) == LOSS
    with pytest.raises(ValueError):
        settle_leg("ml", "home", None, F(100, 100))


def test_spread_including_push():
    assert settle_leg("spread", "home", -3.5, F(104, 100)) == WIN
    assert settle_leg("spread", "home", -4, F(104, 100)) == PUSH
    assert settle_leg("spread", "home", -4.5, F(104, 100)) == LOSS
    assert settle_leg("spread", "away", +4.5, F(104, 100)) == WIN
    assert settle_leg("spread", "away", +4, F(104, 100)) == PUSH


def test_total():
    assert settle_leg("total", "over", 220.5, F(111, 110)) == WIN
    assert settle_leg("total", "under", 221, F(111, 110)) == PUSH
    assert settle_leg("total", "under", 221.5, F(111, 110)) == WIN


def test_status_handling():
    assert settle_leg("ml", "home", None, GameResult("postponed")) == VOID
    assert settle_leg("ml", "home", None, GameResult("in_progress", 50, 40)) == PENDING
    assert settle_leg("ml", "home", None, GameResult("scheduled")) == PENDING
    with pytest.raises(ValueError):
        settle_leg("teaser", "home", 1, F(1, 0))


def test_props():
    g = F(100, 90)
    assert settle_leg("prop", "over", 24.5, g, stat_value=25, played=True) == WIN
    assert settle_leg("prop", "over", 25, g, stat_value=25, played=True) == PUSH
    assert settle_leg("prop", "under", 24.5, g, stat_value=None, played=False) == VOID
    assert settle_leg("prop", "under", 24.5, g, stat_value=None, played=True) == PENDING


def test_net_profit():
    assert net_profit(WIN, 2.5, 1) == 1.5
    assert net_profit(LOSS, 2.5, 1) == -1
    assert net_profit(PUSH, 2.5, 1) == 0
    assert net_profit(VOID, 2.5, 1) == 0
    assert net_profit(PENDING, 2.5, 1) is None


def test_parlay():
    assert settle_parlay([(WIN, 2.0), (WIN, 1.5)], 1) == (WIN, 2.0, 3.0)
    assert settle_parlay([(WIN, 2.0), (LOSS, 1.5)], 1)[0] == LOSS
    assert settle_parlay([(WIN, 2.0), (PUSH, 1.9)], 1) == (WIN, 1.0, 2.0)
    assert settle_parlay([(VOID, 2.0), (PUSH, 1.9)], 1) == (PUSH, 0.0, 1.0)
    assert settle_parlay([(WIN, 2.0), (PENDING, 1.9)], 1)[0] == PENDING
    assert settle_parlay([(PENDING, 2.0), (LOSS, 1.9)], 1)[0] == LOSS
