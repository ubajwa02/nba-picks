import os

from nbapicks import leans as LN
from nbapicks.config import load as load_config


def _lean(i, game, prob=0.66, price=-120):
    return dict(label=f"Player {i} Over 5.5 Rebounds", game_id=game, prob=prob, price_american=price, slate="2026-10-27", player=f"p{i}")


def test_tickets_use_distinct_games_and_report_shortfall():
    cfg = load_config(os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "nbapicks.yaml"))
    tickets, notes = LN.build_tickets([_lean(1, "g1"), _lean(2, "g2"), _lean(3, "g3")], cfg, "2026-10-27")
    for t in tickets:
        assert len({l["game_id"] for l in t["legs"]}) == len(t["legs"])
        assert 2 <= len(t["legs"]) <= 3 or t["kind"] == "lotto"
    parlays = [t for t in tickets if t["kind"] == "parlay"]
    assert len(parlays) < 3 and any("parlays posted" in n for n in notes)


def test_too_few_leans_builds_nothing_and_says_why():
    cfg = load_config(os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "nbapicks.yaml"))
    tickets, notes = LN.build_tickets([_lean(1, "g1")], cfg, "2026-10-27")
    assert tickets == [] and notes
