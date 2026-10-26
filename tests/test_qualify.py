import copy, datetime as dt
import pytest
from nbapicks import config
from nbapicks.qualify import Candidate, judge, portfolio
from nbapicks import parlay

NOW = dt.datetime(2026, 10, 21, 18, 0, tzinfo=dt.timezone.utc)
CFG = config.load()


def cfg(status="paper", **kw):
    c = copy.deepcopy(CFG)
    for m in c["markets"].values():
        m["status"] = status
    return c


def cand(**kw):
    base = dict(game_id="g1", start_utc="2026-10-21T23:00:00Z", home="ORL", away="ATL", market="ml",
                selection="home", line=None, price_dec=2.0, book="DraftKings",
                price_observed_at="2026-10-21T17:30:00Z", prob=0.56, fair=0.5)
    base.update(kw)
    return Candidate(**base)


def test_eligible_when_everything_checks_out():
    c = judge(cand(), cfg(), NOW, [], {})
    assert c.decision == "eligible" and c.ev == pytest.approx(0.12)
    assert c.min_price_dec == pytest.approx(1 + (0.03 + 0.44) / 0.56)


def test_research_status_is_never_eligible():
    assert judge(cand(), cfg("research"), NOW, [], {}).decision == "watch"


@pytest.mark.parametrize("kw,expect,why", [
    (dict(price_dec=None), "reject", "no valid price"),
    (dict(price_observed_at="2026-10-21T10:00:00Z"), "reject", "stale"),
    (dict(price_observed_at=None), "reject", "stale"),
    (dict(flags="side_unverified"), "reject", "not verified"),
    (dict(start_utc="2026-10-21T17:00:00Z"), "reject", "started"),
    (dict(prob=0.50), "reject", "below"),
    (dict(prob=0.51), "watch", "below"),
    (dict(prob=0.70), "hold", "gap"),           # model 70% vs market 50%
    (dict(start_utc="2026-10-21T18:10:00Z"), "hold", "to tip"),
])
def test_gates(kw, expect, why):
    c = judge(cand(**kw), cfg(), NOW, [], {})
    assert c.decision == expect and any(why in r for r in c.reasons), c.reasons


def test_unresolved_key_injury_holds_but_bench_player_does_not():
    inj = [dict(player_id="7", player_name="Star", team="ORL", status="Questionable"),
           dict(player_id="8", player_name="Bench", team="ATL", status="Questionable")]
    c = judge(cand(), cfg(), NOW, inj, {"7": 34.0, "8": 9.0})
    assert c.decision == "hold" and any("Star" in r for r in c.reasons) and not any("Bench" in r for r in c.reasons)


def test_prop_player_out_rejected():
    inj = [dict(player_id="7", player_name="Star", team="ORL", status="Out")]
    c = judge(cand(market="prop", selection="over", line=20.5, player_id="7", player_name="Star", stat="pts"),
              cfg(), NOW, inj, {})
    assert c.decision == "reject"


def test_portfolio_caps_and_same_side():
    c = cfg()
    ml = judge(cand(), c, NOW, [], {})
    sp = judge(cand(market="spread", line=-2.5, prob=0.57, fair=0.5), c, NOW, [], {})
    others = [judge(cand(game_id=f"g{i}", prob=0.56), c, NOW, [], {}) for i in range(2, 10)]
    out = portfolio([ml, sp] + others, c)
    chosen = [x for x in out if x.decision == "eligible"]
    assert len(chosen) == c["targets"]["straight"]
    # ML and spread on ORL in the same game: only one survives
    assert sum(1 for x in chosen if x.game_id == "g1") == 1
    assert all(x.stake == c["stakes"]["straight"] for x in chosen)
    assert sum(x.stake for x in chosen) <= c["risk"]["max_units_per_day"]


def test_no_forced_picks():
    out = portfolio([judge(cand(prob=0.45), cfg(), NOW, [], {})], cfg())
    assert not [x for x in out if x.decision == "eligible"]


def test_parlays_cross_game_only_and_ev_from_joint():
    c = cfg()
    legs = [judge(cand(game_id=f"g{i}", prob=0.57), c, NOW, [], {}) for i in range(3)]
    legs.append(judge(cand(game_id="g0", market="total", selection="over", line=230.5, prob=0.57, fair=0.5), c, NOW, [], {}))
    ps = parlay.build([l for l in legs if l.decision == "eligible"], c, "parlay")
    assert ps and all(len({l.game_id for l in p["legs"]}) == len(p["legs"]) for p in ps)
    p = ps[0]
    assert p["prob"] == pytest.approx(0.57 ** len(p["legs"]))
    assert p["ev"] == pytest.approx(p["prob"] * p["price_dec"] - 1)
    assert len(ps) <= c["targets"]["parlay"]


def test_same_game_simulation_shows_dependence():
    # home ML and home -5.5 are strongly dependent: joint >> product
    joint = parlay.same_game_joint([("ml", "home", None), ("spread", "home", -5.5)], 4, 12, 225, 18)
    pml = parlay.same_game_joint([("ml", "home", None)], 4, 12, 225, 18)
    psp = parlay.same_game_joint([("spread", "home", -5.5)], 4, 12, 225, 18)
    assert joint == pytest.approx(psp, abs=0.01) and joint > pml * psp + 0.1
