import datetime as dt, json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ops"))
import picks_target as P

NY = P.NY


def test_defaults_without_games():
    assert P.target(dt.datetime(2026, 11, 6, 12, tzinfo=NY), None) == 16 * 60 + 30      # Friday
    assert P.target(dt.datetime(2026, 11, 7, 9, tzinfo=NY), None) == 11 * 60            # Saturday


def test_early_tip_moves_picks_earlier_with_floor():
    fri = dt.datetime(2026, 11, 6, 9, tzinfo=NY)
    assert P.target(fri, 19 * 60) == 16 * 60 + 30            # 7 PM tip: unchanged
    assert P.target(fri, 15 * 60) == 13 * 60                 # holiday 3 PM tip: 1 PM
    assert P.target(fri, 12 * 60) == 10 * 60                 # noon tip: floor 10:00
    assert P.target(dt.datetime(2026, 11, 7, 9, tzinfo=NY), 15 * 60 + 30) == 11 * 60   # weekend never later than 11


def test_first_tip_from_ledger(tmp_path):
    p = tmp_path / "games.jsonl"
    rows = [dict(game_id="1", start_utc="2026-11-06T20:00Z", status="scheduled"),     # 15:00 ET
            dict(game_id="1", start_utc="2026-11-07T00:00Z", status="scheduled"),     # rescheduled: last wins (19:00)
            dict(game_id="2", start_utc="2026-11-06T23:30Z", status="scheduled"),     # 18:30
            dict(game_id="3", start_utc="2026-11-06T17:00Z", status="postponed"),
            dict(game_id="4", start_utc="2026-11-07T17:00Z", status="scheduled")]     # tomorrow
    p.write_text("".join(json.dumps(r) + "\n" for r in rows))
    assert P.first_tip_minute(str(p), dt.date(2026, 11, 6)) == 18 * 60 + 30
    assert P.first_tip_minute(str(tmp_path / "missing.jsonl"), dt.date(2026, 11, 6)) is None
