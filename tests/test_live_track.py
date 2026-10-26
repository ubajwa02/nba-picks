"""Synthetic data only: boxes step, posted-lean grading, live scorecard."""
import datetime as dt

from nbapicks import pipeline, scorecard, track
from nbapicks import config as C

NOW = dt.datetime(2026, 10, 22, 12, tzinfo=dt.timezone.utc)


def _sb(gid, status="STATUS_FINAL", completed=True):
    comp = dict(id=gid, date="2026-10-22T00:00Z", competitors=[dict(homeAway="home", score="110", team=dict(abbreviation="LAC", id="12")),
                             dict(homeAway="away", score="100", team=dict(abbreviation="SAC", id="23"))])
    return dict(events=[dict(id=gid, date="2026-10-22T00:00Z", season=dict(year=2027, type=2),
                     status=dict(type=dict(name=status, completed=completed, state="post" if completed else "in")), competitions=[comp])])


SUMMARY = dict(boxscore=dict(players=[dict(team=dict(abbreviation="LAC"), statistics=[dict(
    labels=["MIN", "PTS", "REB", "AST", "3PT", "STL", "BLK", "TO"],
    athletes=[dict(athlete=dict(id="1", displayName="Synthetic A"), starter=True, stats=["30", "21", "7", "3", "2-5", "1", "0", "2"]),
              dict(athlete=dict(id="2", displayName="Synthetic B"), didNotPlay=True, stats=[])])]),
    dict(team=dict(abbreviation="SAC"), statistics=[dict(
        labels=["MIN", "PTS", "REB", "AST", "3PT", "STL", "BLK", "TO"],
        athletes=[dict(athlete=dict(id="3", displayName="Synthetic C"), starter=True, stats=["28", "12", "5", "2", "1-4", "0", "0", "1"])])])]))


def test_boxes_appends_once(tmp_path):
    ctx = pipeline.Ctx(NOW, C.load(), str(tmp_path), slate=dt.date(2026, 10, 21))
    calls = []
    fs = lambda gid: calls.append(gid) or SUMMARY
    r = pipeline.boxes(ctx, fetch_scoreboard=lambda d: _sb("g1"), fetch_summary=fs)
    assert r.get("box_rows") == 3 and r.get("box_games") == 1
    rows = {x["player_id"]: x for x in ctx.store.q("SELECT * FROM player_games")}
    assert rows["1"]["pts"] == 21 and rows["1"]["fg3m"] == 2 and rows["2"]["played"] == 0
    again = pipeline.Ctx(NOW, C.load(), str(tmp_path), slate=dt.date(2026, 10, 21))
    r2 = pipeline.boxes(again, fetch_scoreboard=lambda d: _sb("g1"), fetch_summary=fs)
    assert r2.get("box_rows", 0) == 0 and len(calls) == 1
    assert again.store.one("SELECT count(*) n FROM player_games")["n"] == 3


def test_boxes_skips_unfinished(tmp_path):
    ctx = pipeline.Ctx(NOW, C.load(), str(tmp_path), slate=dt.date(2026, 10, 21))
    r = pipeline.boxes(ctx, fetch_scoreboard=lambda d: _sb("g2", "STATUS_IN_PROGRESS", False),
                       fetch_summary=lambda g: (_ for _ in ()).throw(AssertionError("fetched")))
    assert r["not_final"] >= 1 and not r.get("box_rows")


def test_leans_grade_from_box(tmp_path):
    root = str(tmp_path)
    base = dict(slate="2026-10-21", game_id="g1", stake=1.0)
    assert track.add(root, dict(base, market="prop", selection="over", line=19.5, price_american=105, player_id="1", stat="pts"))
    assert not track.add(root, dict(base, market="prop", selection="over", line=19.5, price_american=105, player_id="1", stat="pts"))
    track.add(root, dict(base, market="prop", selection="over", line=2.5, price_american=-130, player_id="2", stat="ast"))
    track.add(root, dict(base, market="spread", selection="home", line=-10.5, price_american=-110, player_id=None, stat=None))
    track.add(root, dict(base, market="ml", selection="away", line=None, price_american=150, player_id=None, stat=None, game_id="g9"))
    games = {"g1": dict(status="final", home="LAC", away="SAC", home_score=110, away_score=100)}
    box = {("g1", "1"): dict(played=1, pts=21), ("g1", "2"): dict(played=0, ast=None)}
    g = track.grade(track.load(root), games, box)
    assert [x["result"] for x in g] == ["win", "void", "loss", "pending"]
    assert abs(g[0]["net_units"] - 1.05) < 1e-9
    rec = track.record(g)
    assert (rec["wins"], rec["losses"], rec["pending"], rec["units"]) == (1, 1, 1, 0.05)


def test_scorecard_dedups_and_buckets():
    mk = lambda pid, t, prob, dec, ev, m="ml": dict(pred_id=pid, created_at=t, category="straight", game_id="g", market=m,
                                                   selection="home", line=None, prob=prob, price_dec=dec, ev=ev, decision="watch")
    preds = [mk("a", "2026-10-20T01", 0.6, 2.0, 0.2), mk("b", "2026-10-20T05", 0.65, 1.8, 0.17),
             mk("c", "2026-10-21T01", 0.45, 2.5, 0.12, "prop"), mk("old", "2026-10-01", 0.5, 2.0, 0.0, "total")]
    settled = {k: dict(result=r, net_units=n) for k, r, n in (("a", "win", 1), ("b", "win", 0.8), ("c", "loss", -1), ("old", "win", 1))}
    sc = scorecard.build(preds, settled)
    assert sc["n"] == 2 and {r["pred_id"] for r in sc["rows"]} == {"b", "c"}
    assert sc["brier"]["model"] == round(((0.65 - 1) ** 2 + 0.45 ** 2) / 2, 4)
    assert sc["brier"]["market"] == round(((1 / 1.8 - 1) ** 2 + 0.4 ** 2) / 2, 4)
    assert sc["by_market"]["prop"]["units"] == -1 and sc["by_ev"]["EV>=15%"]["wins"] == 1
    assert "Descriptive only" in scorecard.markdown(sc)
