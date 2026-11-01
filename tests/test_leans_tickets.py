import os

from nbapicks import leans as LN
from nbapicks.config import load as load_config


def _lean(i, game, prob=0.66, price=-120):
    return dict(label=f"Player {i} Over 5.5 Rebounds", game_id=game, prob=prob, price_american=price, slate="2026-10-27", player=f"p{i}")


def test_always_two_parlays_and_a_lotto_from_different_games():
    cfg = load_config(os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "nbapicks.yaml"))
    legs = [_lean(i, f"g{i}", prob=0.7 - i * 0.02) for i in range(1, 7)]
    tickets, notes = LN.build_tickets(legs, cfg, "2026-10-27")
    parlays = [t for t in tickets if t["kind"] == "parlay"]
    lotto = [t for t in tickets if t["kind"] == "lotto"]
    assert len(parlays) == 2 and len(lotto) == 1
    for t in tickets:
        assert len({l["game_id"] for l in t["legs"]}) == len(t["legs"]) and t["research"] and "ev" in t
    assert parlays[0]["prob"] >= parlays[1]["prob"] and len(lotto[0]["legs"]) >= 3


def test_small_pool_reuses_legs_and_says_so():
    cfg = load_config(os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "nbapicks.yaml"))
    tickets, notes = LN.build_tickets([_lean(i, f"g{i}") for i in range(1, 4)], cfg, "2026-10-27")
    assert len([t for t in tickets if t["kind"] == "parlay"]) == 2 and any("share" in n for n in notes)


def test_too_few_props_builds_nothing_and_says_why():
    cfg = load_config(os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "nbapicks.yaml"))
    tickets, notes = LN.build_tickets([_lean(1, "g1")], cfg, "2026-10-27")
    assert tickets == [] and notes


def test_winning_parlay_pays_the_combined_price_on_one_unit():
    from nbapicks.settle import settle_parlay
    from nbapicks.odds import american_to_decimal
    legs = [("win", american_to_decimal(-196)), ("win", american_to_decimal(-175))]
    result, net, eff = settle_parlay(legs, 1.0)
    assert result == "win" and abs(net - 1.3732) < 0.01          # about +137, not the sum of the legs' profits


def _pred(pid, game, prob=0.66, price=1.6, injury=None, flags=(), seen="2026-10-31T20:00:00Z"):
    return dict(market="prop", category="straight", selection="over", decision="reject", reason="EV +0.6% below 5% threshold",
                prob=prob, price_dec=price, line=2.5, player_id=pid, player_name=f"P{pid}", stat="reb", game_id=game,
                start_utc="2026-10-31T23:00Z", price_observed_at=seen,
                inputs=dict(quality_flags=list(flags), explain=dict(injury_status=injury, line_hits_last10=dict(n=10), flags=[])))


def test_leans_skip_unresolved_injury_even_when_reason_is_only_ev():
    """2026-10-31: Ty Jerome (Day-To-Day) was posted because judge() kept only the EV reason; he did not play."""
    cfg = load_config(os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "nbapicks.yaml"))
    preds = [_pred("1", "g1", injury="Day-To-Day", flags=["injury_daytoday"]), _pred("2", "g2"), _pred("3", "g3", injury="Out")]
    out = LN.pick_leans(preds, cfg, "2026-10-31", "2026-10-31T21:00:00Z")
    assert [l["player_id"] for l in out] == ["2"]


def test_leans_skip_quotes_older_than_the_freshness_rule():
    cfg = load_config(os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "nbapicks.yaml"))
    preds = [_pred("1", "g1", seen="2026-10-31T17:00:00Z"), _pred("2", "g2", seen="2026-10-31T20:30:00Z")]
    out = LN.pick_leans(preds, cfg, "2026-10-31", "2026-10-31T21:00:00Z")
    assert [l["player_id"] for l in out] == ["2"]
