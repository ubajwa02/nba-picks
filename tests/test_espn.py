import json, os
import pytest
from nbapicks.sources import espn

F = os.path.join(os.path.dirname(__file__), "fixtures")
load = lambda n: json.load(open(os.path.join(F, n)))
T = "2026-10-20T12:00:00Z"


def test_scoreboard_final_and_pre():
    games, _ = espn.parse_scoreboard(load("espn_scoreboard_final_20250301.json"), T)
    g = next(g for g in games if g["game_id"] == "401705426")
    assert (g["home"], g["away"], g["status"], g["home_score"], g["away_score"]) == ("CHA", "WSH", "final", 100, 113)
    pre, _ = espn.parse_scoreboard(load("espn_scoreboard_pre_20261021.json"), T)
    assert len(pre) == 11 and all(x["status"] == "scheduled" and x["home_score"] is None for x in pre)
    assert pre[0]["home"] == "ORL" and pre[0]["away"] == "ATL" and pre[0]["season"] == 2027


def test_core_odds_current_with_open():
    rows = espn.parse_core_odds(load("espn_core_odds_pre.json"), "401909834", T)
    dk = [r for r in rows if r["book"] == "DraftKings"]
    cur = {(r["market"], r["selection"]): r for r in dk if r["kind"] == "current"}
    assert cur[("ml", "home")]["price_dec"] == pytest.approx(1 + 100 / 142)
    assert cur[("ml", "away")]["price_dec"] == pytest.approx(2.2)
    assert cur[("spread", "home")]["line"] == -2.5 and cur[("spread", "away")]["line"] == 2.5
    assert cur[("total", "over")]["line"] == 235.5
    op = {(r["market"], r["selection"]): r for r in dk if r["kind"] == "open"}
    assert op[("total", "over")]["line"] == 232.5 and op[("ml", "home")]["price_dec"] == pytest.approx(1 + 100 / 135)


def test_core_odds_old_season_flags_untimed():
    rows = espn.parse_core_odds(load("espn_core_odds_2019.json"), "401071601", T, game_final=True)
    assert rows and all(r["kind"] == "close" and "final_quote_untimed" in r["flags"] for r in rows)
    assert not any(r["book"] in ("consensus", "numberfire", "teamrankings", "accuscore") for r in rows)
    assert all(r["price_dec"] > 1 for r in rows)


def test_core_odds_2025_close():
    rows = espn.parse_core_odds(load("espn_core_odds_final_401705426.json"), "401705426", T, game_final=True)
    close = {(r["market"], r["selection"]): r for r in rows if r["kind"] == "close" and r["book"] == "ESPN BET"}
    assert close[("spread", "home")]["line"] == -3.5 and close[("spread", "away")]["line"] == 3.5
    assert close[("ml", "away")]["price_dec"] == pytest.approx(2.45)
    assert close[("spread", "home")]["flags"] is None  # a real, labelled close
    assert not any(r["kind"] == "current" for r in rows)
    opn = {(r["market"], r["selection"]): r for r in rows if r["kind"] == "open" and r["book"] == "ESPN BET"}
    assert opn[("spread", "away")]["line"] == 4.5


def test_props_are_marked_unverified():
    rows = espn.parse_propbets(load("espn_propbets_pre.json"), "401909834", "DraftKings", T, {"4066320": "X"})
    r = [x for x in rows if x["player_id"] == "4066320" and x["stat"] == "pts" and x["kind"] == "current"]
    assert {x["selection"] for x in r} == {"side0", "side1"} and all(x["line"] == 18.5 for x in r)
    assert all("side_unverified" in x["flags"] for x in rows)
    assert {x["stat"] for x in rows} <= {"pts", "ast", "reb", "fg3m"}


def test_injuries():
    rows = espn.parse_injuries(load("espn_injuries.json"), T)
    assert rows and all(r["status"] and r["player_name"] for r in rows)
    assert any(r["player_name"] == "Mouhamed Gueye" and r["status"] == "Out" for r in rows)


def test_boxscore():
    rows = espn.parse_boxscore(load("espn_summary_final.json"), "401705426", T)
    assert len({r["team"] for r in rows}) == 2
    played = [r for r in rows if r["played"]]
    assert played and all(r["pts"] is not None and r["minutes"] is not None for r in played)
    # team points add up to the final score
    by = {}
    for r in played:
        by[r["team"]] = by.get(r["team"], 0) + r["pts"]
    assert by == {"CHA": 100, "WSH": 113}


def test_propbets_without_athlete_are_skipped():
    from nbapicks.sources import espn
    d = {"items": [{"type": {"name": "Total Points"}, "odds": {"total": {"value": "220.5"}}}]}
    assert espn.parse_propbets(d, "g", "DraftKings", "t", {}) == []


def test_boxscore_shot_volume_and_plus_minus():
    rows = espn.parse_boxscore(load("espn_summary_final.json"), "401705426", T)
    m = next(r for r in rows if r["player_name"] == "Khris Middleton")
    assert (m["fga"], m["fg3a"], m["fta"], m["oreb"], m["dreb"], m["plus_minus"]) == (9, 3, 6, 1, 4, 1)
    played = [r for r in rows if r["played"]]
    assert all(isinstance(r["plus_minus"], int) for r in played)
    assert all(r["oreb"] + r["dreb"] == r["reb"] for r in played)
    assert all(r["fga"] >= r["fg3a"] >= r["fg3m"] for r in played)
    # plus-minus sums to five times the final margin (five players on the floor at all times)
    pm = {}
    for r in played:
        pm[r["team"]] = pm.get(r["team"], 0) + r["plus_minus"]
    assert pm == {"WSH": 5 * 13, "CHA": -5 * 13}
    dnp = [r for r in rows if not r["played"]]
    assert dnp and all(r["fga"] is None and r["plus_minus"] is None for r in dnp)


def test_old_box_files_without_new_columns_still_read(tmp_path):
    import csv, gzip
    from nbapicks.history import BOX_COLS, read_csv, write_csv
    old = BOX_COLS[:BOX_COLS.index("played") + 1]
    p = tmp_path / "box_2023.csv.gz"
    with gzip.open(p, "wt", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=old); w.writeheader()
        w.writerow({c: "1" for c in old})
    r = read_csv(str(p))[0]
    assert r["pts"] == "1" and "fga" not in r
    rows = espn.parse_boxscore(load("espn_summary_final.json"), "401705426", T)
    write_csv(str(tmp_path / "box_new.csv.gz"), BOX_COLS, rows)
    back = read_csv(str(tmp_path / "box_new.csv.gz"))
    assert BOX_COLS[-6:] == ["fga", "fg3a", "fta", "oreb", "dreb", "plus_minus"]
    assert back[0]["fga"] == "9" and back[0]["plus_minus"] == "1"


def test_dk_links_from_core_odds():
    lk = espn.parse_dk_links(load("espn_core_odds_pre.json"))
    assert lk["event_url"] == "https://sportsbook.draftkings.com/event/34520235"   # affiliate gateway dropped
    oc = {(o["market"], o["selection"]): o for o in lk["outcomes"]}
    assert oc[("ml", "home")]["outcome_id"] == "0ML85871430_1" and oc[("ml", "home")]["line"] is None
    # lines decoded from the id agree with the parsed DraftKings quote (home -2.5, total 235.5)
    assert oc[("spread", "home")]["line"] == -2.5 and oc[("spread", "away")]["line"] == 2.5
    assert oc[("total", "over")]["line"] == 235.5 and oc[("total", "under")]["outcome_id"].startswith("0OU")


def test_dk_links_reject_foreign_or_odd_urls():
    def item(href, rel):
        return {"items": [{"provider": {"name": "Draft Kings"}, "links": [{"href": href, "rel": [rel]}]}]}
    assert espn.parse_dk_links(item("https://evil.example/event/1?outcomes=0ML1_1", "home")) is None
    assert espn.parse_dk_links({"items": [{"provider": {"name": "ESPN BET"}}]}) is None
    lk = espn.parse_dk_links(item("https://sportsbook.draftkings.com/event/9?outcomes=0OU1O2350_1", "home"))
    assert lk == {"event_url": "https://sportsbook.draftkings.com/event/9", "outcomes": []}   # market mismatch dropped
