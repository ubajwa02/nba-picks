import json, os
from nbapicks.sources import moviodds

F = os.path.join(os.path.dirname(__file__), "fixtures")
GAMES = [dict(game_id="g1", home="DET", away="BOS", start_utc="2026-10-20T19:00Z"),
         dict(game_id="g2", home="ORL", away="ATL", start_utc="2026-10-21T23:00Z")]


def test_parse_game_lines_and_props():
    d = json.load(open(os.path.join(F, "moviodds_nba.json")))
    rows, problems = moviodds.parse(d, GAMES, "2026-10-20T00:05Z")
    g1 = [r for r in rows if r["game_id"] == "g1"]
    ml = {r["selection"]: r for r in g1 if r["market"] == "ml"}
    assert set(ml) == {"home", "away"} and abs(ml["away"]["price_dec"] - 1.8475) < 1e-3
    sp = {r["selection"]: r["line"] for r in g1 if r["market"] == "spread"}
    assert sp["away"] == -1.5 and sp["home"] == 1.5           # BOS -1.5 at DET
    tot = [r for r in g1 if r["market"] == "total"]
    assert {r["selection"] for r in tot} == {"over", "under"} and all(r["line"] == 221.5 for r in tot)
    props = [r for r in g1 if r["market"] == "prop"]
    assert props and all(r["flags"] == "milestone_one_sided" and r["line"] % 1 == 0.5 for r in props)
    assert all(r["book"] == "bet365" for r in rows)
    # NY/PHI and SA/OKC are not in GAMES: reported, not guessed
    assert any("Knicks" in p or "76ers" in p for p in problems)


def test_unmapped_when_kickoff_far_apart():
    m = {"home": "DET Pistons", "away": "BOS Celtics", "kickoff_utc": "2026-11-20T19:00:00Z"}
    assert moviodds.match_game(m, GAMES) is None
