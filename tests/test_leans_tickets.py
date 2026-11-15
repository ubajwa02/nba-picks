import os

from nbapicks import leans as LN
from nbapicks.config import load as load_config


def _lean(i, game, prob=0.66, price=-120):
    return dict(label=f"Player {i} Over 5.5 Rebounds", game_id=game, prob=prob, price_american=price, slate="2026-10-27", player=f"p{i}")


def test_always_two_parlays_and_a_lotto_from_different_games():
    cfg = load_config(os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "nbapicks.yaml"))
    legs = [_lean(i, f"g{i}", prob=0.7 - i * 0.02) for i in range(1, 11)]
    tickets, notes = LN.build_tickets(legs, cfg, "2026-10-27")
    parlays = [t for t in tickets if t["kind"] == "parlay"]
    lotto = [t for t in tickets if t["kind"] == "lotto"]
    assert len(parlays) == 2 and len(lotto) == 1
    for t in tickets:
        assert len({l["game_id"] for l in t["legs"]}) == len(t["legs"]) and t["research"] and "ev" in t
    assert parlays[0]["prob"] >= parlays[1]["prob"] and len(lotto[0]["legs"]) >= 3
    ids = [l["lean_id"] for t in tickets for l in t["legs"]]
    assert len(ids) == len(set(ids))              # no leg is reused across parlays or the lotto


def test_small_pool_never_reuses_legs_and_says_so():
    cfg = load_config(os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "nbapicks.yaml"))
    tickets, notes = LN.build_tickets([_lean(i, f"g{i}") for i in range(1, 4)], cfg, "2026-10-27")
    assert len([t for t in tickets if t["kind"] == "parlay"]) == 1 and any("No lotto" in n for n in notes)


def test_tickets_skip_straight_players_and_fanduel_filter_drops_unbettable():
    cfg = load_config(os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "nbapicks.yaml"))
    legs = [dict(_lean(i, f"g{i}", prob=0.7 - i * 0.01), player_id=str(i)) for i in range(1, 11)]
    tickets, _ = LN.build_tickets(legs, cfg, "2026-10-27", exclude_players={"1", "2"})
    used = {l["player_id"] for t in tickets for l in t["legs"]}
    assert used and not used & {"1", "2"}
    preds = [dict(market="prop", category="straight", selection="over", game_id="g1", player_id="9", player_name="No Market",
                  stat="reb", line=5.5, prob=0.7, price_dec=1.7, decision="bet", inputs="{}"),
             dict(market="prop", category="straight", selection="over", game_id="g1", player_id="8", player_name="Has Market",
                  stat="reb", line=5.5, prob=0.68, price_dec=1.7, decision="bet", inputs="{}")]
    ok = lambda p: p["player_name"] == "Has Market"
    got = LN.pick_leans(preds, cfg, "2026-10-27", "2026-10-27T00:00:00Z", pool=True, fd_ok=ok)
    assert [g["player_id"] for g in got] in ([], ["8"])
    assert "9" not in [g["player_id"] for g in got]


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


def _pred(i, game, prob, dec, model="props-v0", stat="reb", sel="under"):
    return dict(market="prop", category="straight", selection=sel, decision="watch", prob=prob, price_dec=dec, line=4.5,
                player_id=f"p{i}", player_name=f"P{i}", stat=stat, game_id=game, model_version=model,
                inputs={"explain": {"line_hits_last10": {"n": 10}}})


def _cfg():
    return load_config(os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "nbapicks.yaml"))


def test_lean_rule_drops_heavy_juice_and_thin_edges_and_ranks_by_ev():
    preds = [
        _pred(1, "g1", 0.70, 1.52),   # -192: over the -150 price cap
        _pred(2, "g2", 0.64, 1.62),   # edge 0.64-0.617=0.023: below the 4-point floor
        _pred(3, "g3", 0.66, 1.80),   # edge 0.104, EV +0.188
        _pred(4, "g4", 0.62, 1.95),   # edge 0.107, EV +0.209: more EV, lower probability
    ]
    out = LN.pick_leans(preds, _cfg(), "2026-11-15", "9999")
    assert [x["player_id"] for x in out] == ["p4", "p3"]


def test_lean_source_tags_the_model_that_produced_it():
    out = LN.pick_leans([_pred(1, "g1", 0.66, 1.80, model="props-v0")], _cfg(), "2026-11-15", "9999")
    assert out[0]["source"] == "props_v0"
    out = LN.pick_leans([_pred(1, "g1", 0.66, 1.80, model="props-v1")], _cfg(), "2026-11-15", "9999")
    assert out[0]["source"] == "props_v1"


def test_parlay_pool_still_ranks_by_probability_with_no_edge_floor():
    preds = [_pred(1, "g1", 0.70, 1.30), _pred(2, "g2", 0.55, 1.90)]
    pool = LN.pick_leans(preds, _cfg(), "2026-11-15", "9999", pool=True)
    assert [x["player_id"] for x in pool][0] == "p1"
