import copy, json, os

import pytest

from nbapicks import history as H

F = os.path.join(os.path.dirname(__file__), "fixtures")
PB = json.load(open(os.path.join(F, "espn_propbets_pre.json")))
TIP = "2026-10-21T23:00Z"          # fixture items were last updated 2026-10-19


def test_prop_rows_pair_the_two_listed_sides():
    rows = H.prop_rows(PB, "401909834", "2026-10-22T00:00:00Z", {"4066320": "Player X"}, TIP)
    assert len(rows) == 60          # 30 pairs x (current, open)
    cur = [r for r in rows if r["player_id"] == "4066320" and r["stat"] == "pts" and r["kind"] == "current"]
    assert len(cur) == 1
    r = cur[0]
    assert (r["line"], r["price0_dec"], r["price1_dec"]) == (18.5, 1.87, 1.90)
    assert r["side_label"] == "unknown" and r["player_name"] == "Player X" and r["flags"] == ""
    assert r["source_updated_at"] == "2026-10-19T03:13:00Z"
    op = next(x for x in rows if x["player_id"] == "4066320" and x["stat"] == "pts" and x["kind"] == "open")
    assert (op["line"], op["price0_dec"], op["price1_dec"]) == (17.5, 1.80, 1.97)
    assert set(H.PROP_COLS) >= set(r)
    # both listed prices of a pair are a two-way market: implied probabilities sum above 1 (the vig)
    assert all(1.0 < 1 / x["price0_dec"] + 1 / x["price1_dec"] < 1.15 for x in rows)


def test_prop_rows_flag_untimed_final():
    d = copy.deepcopy(PB)
    d["items"][0]["lastUpdated"] = "2026-10-22T02:00Z"     # after tip
    del d["items"][2]["lastUpdated"]                       # missing
    rows = H.prop_rows(d, "g", "t", {}, TIP)
    flagged = {(r["player_id"], r["stat"]) for r in rows if r["flags"] == "untimed_final"}
    first = d["items"][0]["athlete"]["$ref"].split("/athletes/")[1].split("?")[0]
    third = d["items"][2]["athlete"]["$ref"].split("/athletes/")[1].split("?")[0]
    assert (first, "pts") in flagged and (third, "pts") in flagged
    assert len(flagged) == 2


def test_prop_rows_skip_unpaired_side():
    d = copy.deepcopy(PB)
    d["items"] = d["items"][:1]
    assert H.prop_rows(d, "g", "t", {}, TIP) == []


def test_backfill_props_writes_csv_and_summary(tmp_path):
    out = str(tmp_path)
    finals = [dict(game_id="A", start_utc=TIP), dict(game_id="B", start_utc=TIP), dict(game_id="C", start_utc=TIP)]
    # names for A come from the season box file, for C from one summary call
    H.write_csv(f"{out}/box_2027.csv.gz", H.BOX_COLS, [dict(game_id="A", player_id="4066320", player_name="From Box")])
    calls = []

    def fetch(gid, prov):
        calls.append((gid, prov))
        if gid == "A" and prov == "100":
            return PB
        if gid == "C" and prov == "58":
            return PB
        return {"count": 0, "items": []}

    def summary(gid):
        assert gid == "C"
        return {"boxscore": {"players": [{"team": {"abbreviation": "ORL"}, "statistics": [{"labels": ["MIN", "PTS"],
                "athletes": [{"athlete": {"id": "4066320", "displayName": "From Summary"}, "stats": ["30", "20"]}]}]}]}}

    s = H.backfill_props(2027, out, workers=2, fetch=fetch, summary_fetch=summary, finals=finals)
    assert ("A", "58") not in calls and ("B", "58") in calls and ("C", "58") in calls
    assert s["games"] == 3 and s["games_with_props"] == 2 and s["rows"] == 120 and s["errors"] == 0
    assert s["games_by_book"] == {"DraftKings": 1, "ESPN BET": 1} and s["games_with_empty_propbets"] == 1
    assert "1 of 3" in s["finding"]
    rows = H.read_csv(f"{out}/props_2027.csv.gz")
    assert list(rows[0]) == H.PROP_COLS
    names = {(r["game_id"], r["player_name"]) for r in rows if r["player_id"] == "4066320"}
    assert names == {("A", "From Box"), ("C", "From Summary")}


def test_backfill_props_empty_season_is_a_finding(tmp_path):
    finals = [dict(game_id="A", start_utc=TIP)]
    s = H.backfill_props(2020, str(tmp_path), workers=1, fetch=lambda g, p: {"items": []}, finals=finals)
    assert s["games_with_props"] == 0 and s["rows"] == 0 and s["errors"] == 0
    assert "no propBets" in s["finding"] and "not a fetch failure" in s["finding"]
    assert H.read_csv(f"{tmp_path}/props_2020.csv.gz") == []


def test_fetch_errors_are_counted_not_raised(tmp_path):
    def boom(gid, prov):
        raise RuntimeError("503")
    s = H.backfill_props(2027, str(tmp_path), workers=1, fetch=boom, finals=[dict(game_id="A", start_utc=TIP)])
    assert s["errors"] == 2 and s["rows"] == 0
    assert "fetch errors" in s["finding"] and "not a fetch failure" not in s["finding"]


def test_backfill_workflow_inputs_and_single_job_for_given_seasons():
    import yaml
    root = os.path.dirname(os.path.dirname(__file__))
    wf = yaml.safe_load(open(os.path.join(root, ".github", "workflows", "nba-backfill.yml")))
    inputs = wf[True]["workflow_dispatch"]["inputs"]
    assert inputs["props"]["default"] == "no" and inputs["seasons"]["default"] == ""
    assert "only" in inputs["box"]["description"]
    job = wf["jobs"]["backfill"]
    assert job["strategy"]["matrix"]["group"] == "${{ fromJSON(needs.plan.outputs.groups) }}"
    run = job["steps"][2]["run"]
    assert "--props" in run and "--box-only" in run
    assert "inputs.seasons ||" not in json.dumps(wf)   # the old 5x-same-seasons matrix bug
