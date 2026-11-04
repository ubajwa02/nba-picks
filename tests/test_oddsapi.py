"""The Odds API bet-slip links (site convenience). Offline: synthetic payloads in the documented v4 shape."""
import pytest
from nbapicks import http
from nbapicks.sources import oddsapi

EVENT = {"id": "e1", "home_team": "Los Angeles Clippers", "away_team": "Miami Heat", "commence_time": "2026-11-05T03:30:00Z",
         "bookmakers": [
             {"key": "draftkings", "markets": [
                 {"key": "player_rebounds", "outcomes": [
                     {"name": "Over", "description": "Brook Lopez", "point": 4.5, "price": -147,
                      "link": "https://sportsbook.draftkings.com/event/1?outcomes=abc", "sid": "abc"},
                     {"name": "Under", "description": "Brook Lopez", "point": 4.5, "price": 120, "link": None}]},
                 {"key": "spreads", "outcomes": [
                     {"name": "Los Angeles Clippers", "point": 5.5, "price": -110,
                      "link": "https://sportsbook.draftkings.com/event/1?outcomes=h"},
                     {"name": "Miami Heat", "point": -5.5, "price": -110,
                      "link": "https://evil.example/x"}]}]},
             {"key": "fanduel", "markets": [
                 {"key": "player_threes", "outcomes": [
                     {"name": "Over", "description": "P.J. Washington Jr.", "point": 1.5, "price": -150,
                      "link": "https://sportsbook.fanduel.com/addToBetslip?marketId=42.1&selectionId=7", "sid": "7"}]},
                 {"key": "h2h", "outcomes": [
                     {"name": "Miami Heat", "price": 180, "link": "https://sportsbook.fanduel.com/addToBetslip?marketId=42.2&selectionId=8"}]}]},
             {"key": "betmgm", "markets": []}]}


def test_parse_event_links_props_and_game_lines():
    out = oddsapi.parse_event_links(EVENT, "LAC", "MIA")
    assert set(out) == {"draftkings", "fanduel"}
    dk = out["draftkings"]
    assert dk == [dict(link="https://sportsbook.draftkings.com/event/1?outcomes=abc", sid="abc", market="prop", stat="reb",
                       player="brook lopez", selection="over", line=4.5),
                  dict(link="https://sportsbook.draftkings.com/event/1?outcomes=h", sid=None, market="spread",
                       selection="home", line=5.5)]   # no-link and off-host outcomes dropped
    fd = {o["market"]: o for o in out["fanduel"]}
    assert fd["prop"]["player"] == "pj washington" and fd["prop"]["stat"] == "fg3m"
    assert fd["ml"]["selection"] == "away" and fd["ml"]["line"] is None


def test_match_events_by_teams_and_time():
    games = [dict(game_id="401", home="LAC", away="MIA", start_utc="2026-11-05T03:30Z"),
             dict(game_id="402", home="BOS", away="NY", start_utc="2026-11-05T00:00Z")]
    assert oddsapi.match_events([EVENT], games) == {"401": "e1"}
    late = dict(EVENT, commence_time="2026-11-06T03:30:00Z")
    assert oddsapi.match_events([late], games) == {}


def test_norm_name():
    assert oddsapi.norm_name("Nikola Jokić") == "nikola jokic"
    assert oddsapi.norm_name("Karl-Anthony Towns") == "karl anthony towns"


def test_key_is_redacted_from_errors(monkeypatch):
    def boom(url, **kw):
        raise http.FetchError(url, 401, "Unauthorized")
    monkeypatch.setattr(oddsapi, "get_json", boom)
    with pytest.raises(http.FetchError) as e:
        oddsapi.fetch_events("SECRETKEY123")
    assert "SECRETKEY123" not in str(e.value) and "***" in str(e.value)


def test_off_without_key(monkeypatch, tmp_path):
    from nbapicks import pipeline
    monkeypatch.delenv("ODDS_API_KEY", raising=False)
    called = []
    monkeypatch.setattr(oddsapi, "fetch_events", lambda k: called.append(k) or [])

    class C:
        root = str(tmp_path)
    pipeline.book_links(C(), [dict(game_id="1")], set(), "now")
    assert not called and not (tmp_path / "state" / "book_links.json").exists()


def test_book_links_fetches_today_and_respects_refresh(monkeypatch, tmp_path):
    import datetime as dt, json
    from nbapicks import pipeline
    monkeypatch.setenv("ODDS_API_KEY", "k")
    calls = []
    monkeypatch.setattr(oddsapi, "fetch_events", lambda k: [EVENT])
    monkeypatch.setattr(oddsapi, "fetch_event_links", lambda k, eid: calls.append(eid) or EVENT)
    g = dict(game_id="401", home="LAC", away="MIA", start_utc="2026-11-05T03:30Z")

    class C:
        root, tz, cfg, notes, health = str(tmp_path), "America/New_York", {}, [], {}
        now = dt.datetime(2026, 11, 4, 22, 0, tzinfo=dt.timezone.utc)
        today = dt.date(2026, 11, 4)
        ok = lambda self, *a: None
        fail = lambda self, s, e: (_ for _ in ()).throw(e)
    c = C()
    pipeline.book_links(c, [g], {"401"}, "2026-11-04T22:00:00Z")
    pipeline.book_links(c, [g], {"401"}, "2026-11-04T22:00:00Z")   # within refresh window: no second call
    assert calls == ["e1"]
    saved = json.load(open(tmp_path / "state" / "book_links.json"))
    assert saved["401"]["books"]["fanduel"][0]["stat"] == "fg3m"
