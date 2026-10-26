import math
import pytest
from nbapicks import odds


def test_american_decimal_roundtrip():
    assert odds.american_to_decimal(-110) == pytest.approx(1.909090909)
    assert odds.american_to_decimal(150) == pytest.approx(2.5)
    assert odds.american_to_decimal(100) == 2.0
    for a in (-500, -110, 100, 120, 450):
        assert odds.decimal_to_american(odds.american_to_decimal(a)) == a


@pytest.mark.parametrize("bad", [0, 50, -99, None])
def test_invalid_american(bad):
    with pytest.raises(ValueError):
        odds.american_to_decimal(bad)


def test_implied_and_ev():
    o = odds.american_to_decimal(-110)
    assert odds.implied_prob(o) == pytest.approx(0.5238095)
    # EV formula and ROI formula are the same thing for a binary bet
    for p in (0.4, 0.5238095, 0.6):
        assert odds.ev_binary(p, o) == pytest.approx(p * o - 1)
    assert odds.ev_binary(odds.implied_prob(o), o) == pytest.approx(0, abs=1e-12)
    assert odds.ev_binary(0.55, 2.0) == pytest.approx(0.10)


def test_ev_with_push():
    # 50% win, 10% push, 40% loss at even money: 0.5 - 0.4 = +0.10
    assert odds.ev_with_push(0.5, 0.1, 2.0) == pytest.approx(0.10)
    with pytest.raises(ValueError):
        odds.ev_with_push(0.7, 0.4, 2.0)


def test_min_price_for_edge():
    o = odds.min_decimal_for_edge(0.55, 0.03)
    assert odds.ev_binary(0.55, o) == pytest.approx(0.03)
    o2 = odds.min_decimal_for_edge(0.5, 0.0, p_push=0.1)
    assert odds.ev_with_push(0.5, 0.1, o2) == pytest.approx(0.0, abs=1e-12)
    assert odds.min_decimal_for_edge(0.0, 0.03) == math.inf


def test_devig():
    o = [odds.american_to_decimal(-110)] * 2
    assert odds.devig_multiplicative(o) == pytest.approx([0.5, 0.5])
    fav, dog = odds.american_to_decimal(-300), odds.american_to_decimal(240)
    m = odds.devig_multiplicative([fav, dog]); pw = odds.devig_power([fav, dog])
    assert sum(m) == pytest.approx(1) and sum(pw) == pytest.approx(1, abs=1e-8)
    assert pw[0] > m[0]  # power method shades toward the favourite
    assert odds.overround(o) == pytest.approx(0.047619, abs=1e-5)


def test_parlay():
    assert odds.parlay_decimal([2.0, 2.0, 1.5]) == 6.0
    with pytest.raises(ValueError):
        odds.parlay_decimal([2.0, 1.0])


def test_rounding_tolerance_but_real_errors_raise():
    # regression: a normalised integer distribution produced 1.0000000000000002
    assert odds.ev_with_push(1.0000000000000002, 0.0, 1.5) == pytest.approx(0.5)
    with pytest.raises(ValueError):
        odds.ev_binary(1.01, 2.0)
