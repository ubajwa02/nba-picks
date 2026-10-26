import pytest
from nbapicks.signals import parse_line


@pytest.mark.parametrize("text,expect", [
    ("Lakers -3.5 (-110) 2u", dict(market="spread", team="LAL", line=-3.5, american=-110, units=2.0)),
    ("BOS ML +120", dict(market="ml", team="BOS", american=120)),
    ("Knicks moneyline -150", dict(market="ml", team="NY", american=-150)),
    ("LAL/BOS o224.5 -110", dict(market="total", selection="over", line=224.5, american=-110)),
    ("Celtics Heat under 210 (-105)", dict(market="total", selection="under", line=210.0)),
    ("Jayson Tatum o27.5 pts -115", dict(market="prop", selection="over", line=27.5, stat="pts", player_name="Jayson Tatum")),
    ("Warriors +4 even", dict(market="spread", team="GS", line=4.0, american=100.0)),
])
def test_parse(text, expect):
    p = parse_line(text)
    assert p is not None
    for k, v in expect.items():
        assert p[k] == v, (k, p)


@pytest.mark.parametrize("text", ["gm all, card soon 🔥", "Lakers looking good tonight", "", "Tail or fade?"])
def test_not_picks(text):
    assert parse_line(text) is None


def test_missing_odds_are_not_invented():
    assert parse_line("Lakers -3.5")["american"] is None
