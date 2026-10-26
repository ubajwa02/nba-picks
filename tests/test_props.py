import pytest
from nbapicks.props import PropModel, verify_prop_sides


def rows(pid, pts, mins=30.0):
    return [dict(player_id=pid, date=f"2026-01-{i+1:02d}", minutes=mins, played=1, pts=p, reb=5, ast=3, fg3m=1)
            for i, p in enumerate(pts)]


def test_prop_model_mean_and_minutes_scaling():
    m = PropModel(rows("1", [20, 22, 18, 24, 16, 20]))
    p = m.predict("1", "pts")
    assert p["mean"] == pytest.approx(20) and p["games"] == 6
    assert m.predict("1", "pts", minutes=15)["mean"] == pytest.approx(10)
    o, push = m.prob(p, 19.5, "over")
    assert 0.45 < o < 0.6 and push == 0
    assert m.predict("2", "pts") is None                       # unknown player
    assert PropModel(rows("3", [10, 12])).predict("3", "pts") is None   # too few games


def test_side_verification():
    espn, b365 = [], []
    for i in range(30):
        name = f"Player {chr(65 + i % 26)}{chr(65 + i // 26)}"
        espn += [dict(market="prop", kind="current", player_name=name, stat="pts", line=19.5, selection="side0", price_dec=1.6),
                 dict(market="prop", kind="current", player_name=name, stat="pts", line=19.5, selection="side1", price_dec=2.4)]
        b365.append(dict(market="prop", player_name=name, stat="pts", line=19.5, price_dec=1.62))  # over is the favourite
    first_is_over, agree, n = verify_prop_sides(espn, b365)
    assert first_is_over is True and agree == 1.0 and n == 30
    assert verify_prop_sides(espn[:10], b365)[0] is None       # too few to verify
