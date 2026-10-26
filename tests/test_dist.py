import pytest
from nbapicks.models import dist


def test_margin_symmetry_and_ml():
    w, p = dist.margin_probs(0.0, 12.0, 0.0)
    assert p == 0 and w == pytest.approx(0.5, abs=1e-9)
    assert dist.ml_prob(5, 12) == pytest.approx(1 - dist.ml_prob(5, 12, "away"), abs=1e-12)
    assert dist.ml_prob(5, 12) > 0.6


def test_spread_push_and_complement():
    w, p = dist.margin_probs(3.0, 12.0, -3.0, "home")
    wa, pa = dist.margin_probs(3.0, 12.0, 3.0, "away")
    assert p > 0.02 and p == pytest.approx(pa)
    assert w + p + wa == pytest.approx(1.0)
    w, p = dist.margin_probs(3.0, 12.0, -3.5)
    assert p == 0 and w == pytest.approx(0.5, abs=0.02)


def test_total():
    w, p = dist.total_probs(225, 18, 225.5, "over")
    assert p == 0 and w == pytest.approx(0.49, abs=0.02)
    o, po = dist.total_probs(225, 18, 225, "over"); u, pu = dist.total_probs(225, 18, 225, "under")
    assert o + u + po == pytest.approx(1) and po == pu


def test_count_probs():
    o, p = dist.count_probs(20.0, 40.0, 19.5)
    u, _ = dist.count_probs(20.0, 40.0, 19.5, "under")
    assert p == 0 and o + u == pytest.approx(1)
    assert o == pytest.approx(0.5, abs=0.05)
    o, p = dist.count_probs(2.0, 2.0, 2)
    assert p > 0.2
