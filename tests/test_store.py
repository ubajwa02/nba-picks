import json, os
import pytest
from nbapicks.store import Store, LedgerError, stable_id

G = dict(game_id="g1", season=2027, start_utc="2026-10-21T23:00Z", home="ORL", away="ATL",
         status="scheduled", observed_at="2026-10-20T10:00Z", source="espn")
P = dict(pred_id="p1", created_at="2026-10-21T15:00Z", origin="model", provider="nbapicks",
         model_version="ratings-v1", category="straight", game_id="g1", market="ml", selection="home",
         price_dec=1.7, book="DraftKings", prob=0.62, ev=0.054, decision="eligible", reason="ev>=thr")


def test_roundtrip_and_replay(tmp_path):
    s = Store(str(tmp_path))
    assert s.put("games", G) == "new"
    assert s.put("games", G) == "same"           # idempotent
    assert s.put("predictions", P) == "new"
    assert s.put("games", {**G, "status": "final", "home_score": 110, "away_score": 100}) == "updated"
    s2 = Store(str(tmp_path))                     # replay from disk
    assert s2.one("SELECT status FROM games")["status"] == "final"
    assert s2.one("SELECT prob FROM predictions")["prob"] == 0.62
    lines = open(tmp_path / "ledger" / "games.jsonl").read().splitlines()
    assert len(lines) == 2  # both observations kept, nothing overwritten


def test_predictions_are_immutable(tmp_path):
    s = Store(str(tmp_path))
    s.put("games", G); s.put("predictions", P)
    with pytest.raises(LedgerError):
        s.put("predictions", {**P, "prob": 0.7})
    assert s.put("predictions", P) == "same"


def test_constraints_block_bad_records(tmp_path):
    s = Store(str(tmp_path))
    with pytest.raises(Exception):  # FK: game does not exist
        s.put("predictions", P)
    s.put("games", G)
    with pytest.raises(Exception):
        s.put("predictions", {**P, "prob": 1.4})
    with pytest.raises(Exception):
        s.put("odds", dict(snap_id="o1", game_id="g1", market="ml", selection="home", price_dec=0.9,
                           book="x", source="y", kind="current", observed_at="2026-10-20T10:00Z"))
    with pytest.raises(LedgerError):
        s.put("games", {**G, "bogus": 1})
    # nothing invalid reached disk
    assert not os.path.exists(tmp_path / "ledger" / "predictions.jsonl")
    assert not os.path.exists(tmp_path / "ledger" / "odds")


def test_partitioned_odds(tmp_path):
    s = Store(str(tmp_path)); s.put("games", G)
    o = dict(snap_id=stable_id("a"), game_id="g1", market="ml", selection="home", price_dec=1.7,
             book="DraftKings", source="espn", kind="current", observed_at="2026-10-20T10:00Z")
    s.put("odds", o)
    assert os.path.exists(tmp_path / "ledger" / "odds" / "2026-10-20.jsonl")  # one file per day
    assert Store(str(tmp_path)).one("SELECT count(*) n FROM odds")["n"] == 1


def test_daily_partitions_keep_old_month_files(tmp_path):
    """Files stay far below GitHub's 100 MB limit: new odds/predictions rows go to a day file, the
    month file already on disk is never appended to again, and a restart replays both."""
    from nbapicks.store import partition_key, partition_order
    s = Store(str(tmp_path)); s.put("games", G)
    d = tmp_path / "ledger" / "predictions"
    os.makedirs(d)
    old = {**P, "pred_id": "old1", "created_at": "2026-11-03T10:00Z"}
    (d / "2026-11.jsonl").write_text(json.dumps(old) + "\n")       # written by the monthly code
    size = os.path.getsize(d / "2026-11.jsonl")
    s = Store(str(tmp_path))
    s.put("predictions", {**P, "pred_id": "new1", "created_at": "2026-11-11T01:00:00Z"})
    s.put("predictions", {**P, "pred_id": "new2", "created_at": "2026-11-12T01:00:00Z"})
    assert s.put("predictions", old) == "same"                      # replayed row is not re-appended
    assert sorted(os.listdir(d)) == ["2026-11-11.jsonl", "2026-11-12.jsonl", "2026-11.jsonl"]
    assert os.path.getsize(d / "2026-11.jsonl") == size
    s2 = Store(str(tmp_path))
    assert [r["pred_id"] for r in s2.q("SELECT pred_id FROM predictions ORDER BY created_at")] == ["old1", "new1", "new2"]
    assert [os.path.basename(f) for f in s2._files("predictions")] == ["2026-11.jsonl", "2026-11-11.jsonl", "2026-11-12.jsonl"]
    # pred_events: monthly from now on, the flat pred_events.jsonl is still replayed
    (tmp_path / "ledger" / "pred_events.jsonl").write_text(
        json.dumps(dict(event_id="e0", pred_id="old1", at="2026-11-04T04:00:00Z", type="settled", result="win", net_units=1.0)) + "\n")
    s3 = Store(str(tmp_path))
    s3.put("pred_events", dict(event_id="e1", pred_id="new1", at="2026-11-12T04:00:00Z", type="settled", result="loss", net_units=-1.0))
    assert os.path.exists(tmp_path / "ledger" / "pred_events" / "2026-11.jsonl")
    assert Store(str(tmp_path)).one("SELECT count(*) n FROM pred_events")["n"] == 2
    assert partition_key("2026-11-10T23:04:08Z", True) == "2026-11-10" and partition_key("2026-11-10", False) == "2026-11"
    assert partition_key(None, True) == "unknown" and partition_key("garbage", False) == "unknown"
    assert sorted(["2026-12-01.jsonl", "2026-11.jsonl", "2026-10.jsonl", "2026-11-02.jsonl"], key=partition_order) == \
        ["2026-10.jsonl", "2026-11.jsonl", "2026-11-02.jsonl", "2026-12-01.jsonl"]


def test_corrupt_ledger_reports_location(tmp_path):
    os.makedirs(tmp_path / "ledger")
    (tmp_path / "ledger" / "games.jsonl").write_text(json.dumps(G) + "\n{not json\n")
    with pytest.raises(LedgerError, match="games.jsonl:2"):
        Store(str(tmp_path))


def test_v2_player_games_columns_and_old_ledger_replay(tmp_path):
    from nbapicks.store import MIGRATIONS
    assert len(MIGRATIONS) >= 2
    # a ledger line written before v2 (no shot columns) replays and reads back with NULLs
    d = tmp_path / "ledger"; d.mkdir()
    (d / "games.jsonl").write_text(json.dumps(G) + "\n")
    old = dict(game_id="g1", player_id="7", player_name="A", team="ORL", starter=1, minutes=30.0, pts=20,
               reb=5, ast=3, fg3m=2, stl=1, blk=0, tov=2, played=1, observed_at="2026-10-22T03:00Z")
    (d / "player_games.jsonl").write_text(json.dumps(old) + "\n")
    s = Store(str(tmp_path))
    r = s.one("SELECT * FROM player_games")
    assert r["pts"] == 20 and r["fga"] is None and r["plus_minus"] is None
    assert s.one("PRAGMA user_version")["user_version"] == len(MIGRATIONS)
    # a v2 row with the new columns is accepted and persisted
    assert s.put("player_games", {**old, "player_id": "8", "fga": 15, "fg3a": 6, "fta": 4, "oreb": 1,
                                  "dreb": 4, "plus_minus": -7}) == "new"
    s2 = Store(str(tmp_path))
    assert s2.one("SELECT plus_minus, fga FROM player_games WHERE player_id = '8'") == {"plus_minus": -7, "fga": 15}
