import datetime as dt

from nbapicks import validate as V

NOW = dt.datetime(2026, 10, 26, 18, 0, tzinfo=dt.timezone.utc)


def box(pid, team="BOS", **kw):
    r = dict(game_id="g1", player_id=pid, team=team, minutes=30.0, pts=10, reb=4, ast=3, fg3m=1, fga=8, played=1)
    r.update(kw)
    return r


def test_box_clean_game_passes():
    rows, bad = V.validate_box_rows([box("1"), box("2", team="NY")], "g1")
    assert len(rows) == 2 and not bad


def test_box_rejects_impossible_duplicate_and_missing_id():
    rows, bad = V.validate_box_rows([box("1"), box("1"), box("2", team="NY", pts=140), box("None", team="NY"), box("3", team="NY")], "g1")
    assert [r["player_id"] for r in rows] == ["1", "3"]
    assert len(bad) == 3


def test_box_schema_change_and_empty_feed_are_problems():
    rows, bad = V.validate_box_rows([{"game_id": "g1", "player_id": "1"}], "g1")
    assert rows == [] and "schema change" in bad[0]
    assert V.validate_box_rows([], "g1")[0] == []
    assert V.validate_box_rows([], "g1")[1]


def test_box_must_cover_two_teams():
    rows, bad = V.validate_box_rows([box("1"), box("2")], "g1")
    assert rows == [] and "1 teams" in bad[-1]


def test_games_dropped_for_bad_time_same_team_or_final_without_score():
    g = dict(game_id="a", home="BOS", away="NY", start_utc="2026-10-26T23:00Z", status="scheduled")
    rows, bad = V.validate_games([g, dict(g, game_id="b", start_utc="soon"), dict(g, game_id="c", away="BOS"),
                                  dict(g, game_id="d", status="final"), dict(g)])
    assert [r["game_id"] for r in rows] == ["a"] and len(bad) == 3


def test_empty_injury_feed_is_never_read_as_healthy():
    rows, bad = V.validate_injuries([], NOW)
    assert rows == [] and bad == ["injury feed returned no rows"]


def test_injury_rows_need_player_team_status_and_no_future_date():
    ok = dict(player_id="9", player_name="A", team="BOS", status="Out", source_date="2026-10-26T10:00Z")
    rows, bad = V.validate_injuries([ok, dict(ok, player_id="None"), dict(ok, status="?"), dict(ok, source_date="2026-12-01T00:00Z")], NOW)
    assert rows == [ok] and len(bad) == 3


def test_odds_rows_need_keys_and_a_plausible_price():
    ok = dict(game_id="g", market="prop", observed_at="t", price_dec=1.9)
    rows, bad = V.validate_odds([ok, dict(ok, price_dec=0.5), dict(ok, game_id="")])
    assert rows == [ok] and len(bad) == 2
