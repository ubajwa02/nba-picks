import csv
import datetime as dt
import gzip
import json
import os
import random

import pytest

from nbapicks import cache
from nbapicks import propbacktest as PB
from nbapicks.models.props_v1 import PropModelV1

START = dt.date(2023, 11, 1)
OPPS = ["BBB", "CCC", "DDD", "EEE"]
SPLITS = {"explore": (dt.date.min, dt.date(2024, 6, 30)), "validate": (dt.date(2024, 10, 1), dt.date(2025, 1, 31)),
          "holdout": (dt.date(2025, 2, 1), dt.date(2025, 6, 30))}
RUN_KEYS = {"name", "kind", "market", "model_version", "baseline", "split", "period", "staking", "selection_rule",
            "price_basis", "eligible", "bets", "wins", "losses", "pushes", "voids", "hit_rate", "avg_prob",
            "avg_price_dec", "avg_implied", "units_staked", "net_units", "net_dollars", "roi", "roi_ci",
            "logloss_model", "logloss_baseline", "logloss_market", "brier_model", "brier_market", "calibration",
            "coverage", "notes"}


def _write(path, rows):
    with gzip.open(path, "wt", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def make_hist(tmp_path, n=40, seed=3, props=False):
    rnd = random.Random(seed)
    games, box = [], []
    for i in range(n):
        d = START + dt.timedelta(days=2 * i)
        gid = f"40{i:04d}"
        opp = OPPS[i % 4]
        games.append(dict(game_id=gid, season=2024, season_type="regular", start_utc=f"{d.isoformat()}T23:00Z",
                          home="AAA", away=opp, status="final", home_score=110, away_score=100))
        for k in range(6):
            mins = 34 - 3 * k + rnd.randint(-3, 3)
            box.append(dict(game_id=gid, player_id=f"A{k}", player_name=f"Aaa Player{k}", team="AAA", starter=int(k < 5),
                            minutes=mins, pts=max(0, int(mins * 0.6) + rnd.randint(-6, 6)), reb=rnd.randint(1, 9),
                            ast=rnd.randint(0, 7), fg3m=rnd.randint(0, 4), stl=0, blk=0, tov=1, played=1))
            box.append(dict(game_id=gid, player_id=f"{opp}{k}", player_name=f"{opp} Player{k}", team=opp, starter=int(k < 5),
                            minutes=mins, pts=max(0, int(mins * 0.5) + rnd.randint(-6, 6)), reb=rnd.randint(1, 9),
                            ast=rnd.randint(0, 7), fg3m=rnd.randint(0, 4), stl=0, blk=0, tov=1, played=1))
    games.append(dict(game_id="40999", season=2024, season_type="regular", start_utc="2024-03-01T23:00Z", home="AAA",
                      away="BBB", status="postponed", home_score="", away_score=""))
    _write(tmp_path / "games_2024.csv.gz", games)
    _write(tmp_path / "box_2024.csv.gz", box)
    if props:
        pr = []
        for g in games[20:40]:
            for k in range(3):
                pr.append(dict(game_id=g["game_id"], player_id=f"A{k}", player_name=f"Aaa Player{k}", stat="pts",
                               line=14.5 + k, price0_dec=1.95, price1_dec=1.80, side_label="unknown", kind="current", observed_at="2024-10-22T20:00Z",
                               source_updated_at=g["start_utc"].replace("23:00Z", "18:00Z")))
                # a post-start observation must be ignored
                pr.append(dict(game_id=g["game_id"], player_id=f"A{k}", player_name=f"Aaa Player{k}", stat="pts",
                               line=40.5, price0_dec=1.9, price1_dec=1.9, side_label="unknown", kind="current", observed_at="2024-10-22T20:00Z",
                               source_updated_at=g["start_utc"].replace("23:00Z", "23:30Z")))
        _write(tmp_path / "props_2024.csv.gz", pr)
    return tmp_path


def test_cache_hit_refresh_and_invalidation(tmp_path):
    src = tmp_path / "src.txt"
    src.write_text("a")
    calls = []

    def compute():
        calls.append(1)
        return {"v": len(calls)}
    kw = dict(cache_dir=str(tmp_path / "c"))
    assert cache.cached("f", {"p": 1}, [str(src)], compute, **kw) == {"v": 1}
    assert cache.cached("f", {"p": 1}, [str(src)], compute, **kw) == {"v": 1}      # hit
    assert len(calls) == 1
    assert cache.cached("f", {"p": 2}, [str(src)], compute, **kw) == {"v": 2}      # params change
    assert cache.cached("f", {"p": 1}, [str(src)], compute, refresh=True, **kw) == {"v": 3}
    assert cache.cached("f", {"p": 1}, [str(src)], compute, **kw) == {"v": 3}      # refreshed entry reused
    src.write_text("b")
    assert cache.cached("f", {"p": 1}, [str(src)], compute, **kw) == {"v": 4}      # source changed
    assert cache.cached("f", {"p": 1}, [str(src)], compute, version=99, **kw) == {"v": 5}
    assert cache.cached("j", [1], [str(src)], lambda: {"x": 1}, fmt="json", **kw) == {"x": 1}
    assert not [f for f in os.listdir(tmp_path / "c") if f.endswith(".part")]


def test_conservative_and_labelled_prices():
    assert PB.prices(dict(p0=1.95, p1=1.80, side_label="unknown")) == (1.80, 1.80, "conservative pair")
    assert PB.prices(dict(p0=1.95, p1=1.80, side_label="over")) == (1.95, 1.80, "timestamped pregame")
    assert PB.prices(dict(p0=1.95, p1=1.80, side_label="under")) == (1.80, 1.95, "timestamped pregame")


def test_real_lines_latest_pregame_only():
    """Backfilled quotes are fetched after the game: pregame-ness comes from the book's own update
    time (source_updated_at). A current quote updated at/after tip may be in-game and is dropped;
    the opening line is used only when no pregame current quote exists."""
    games = {"g1": dict(start_utc="2024-01-01T23:00Z")}
    base = dict(game_id="g1", player_id="1", stat="pts", observed_at="2024-10-22T20:00Z")
    rows = [dict(base, line="20.5", price0_dec="1.9", price1_dec="1.9", side_label="unknown", kind="open",
                 source_updated_at="2024-01-01T22:00Z"),
            dict(base, line="21.5", price0_dec="1.87", price1_dec="1.95", side_label="over", kind="current",
                 source_updated_at="2024-01-01T20:00Z"),
            dict(base, line="30.5", price0_dec="1.9", price1_dec="1.9", side_label="unknown", kind="current",
                 source_updated_at="2024-01-01T23:05Z")]
    rec = PB.real_lines(rows, games)[("g1", "1", "pts")]
    assert rec["line"] == 21.5 and rec["side_label"] == "over"
    only_open = PB.real_lines([rows[0], rows[2]], games)[("g1", "1", "pts")]
    assert only_open["line"] == 20.5 and only_open["kind"] == "open"
    assert ("g1", "1", "pts") not in PB.real_lines([rows[2]], games)       # in-game quote only: no line



def test_real_lines_drops_implausible_pairs_and_picks_the_line_nearest_even():
    """Alt-ladder rungs listed as a pair (15.0 / 26.0) are not a two-way market: pricing them as one
    invented the fg3m 'edge' (review 2026-10-22). Among same-time quotes the main line is the one
    whose de-vigged price is nearest 50/50, not the one whose two prices are closest to each other."""
    games = {"g1": dict(start_utc="2024-01-01T23:00Z")}
    base = dict(game_id="g1", player_id="1", stat="fg3m", observed_at="2024-10-22T20:00Z", side_label="unknown",
                kind="open", source_updated_at="2024-01-01T22:00Z")
    longshots = dict(base, line="6.5", price0_dec="15.0", price1_dec="26.0")
    assert ("g1", "1", "fg3m") not in PB.real_lines([longshots], games)
    main = dict(base, line="2.5", price0_dec="1.80", price1_dec="2.02")
    skew = dict(base, line="3.5", price0_dec="3.10", price1_dec="1.36")
    assert PB.real_lines([skew, longshots, main], games)[("g1", "1", "fg3m")]["line"] == 2.5

def test_bets_ev_threshold_and_push():
    rows = [dict(probs={"m": (0.60, 0.0)}, price_over=1.9, price_under=1.9, result=1),   # EV over 0.14 -> win
            dict(probs={"m": (0.52, 0.0)}, price_over=1.9, price_under=1.9, result=0),   # EV 0.0 / -0.09 -> no bet
            dict(probs={"m": (0.20, 0.0)}, price_over=1.9, price_under=1.9, result=0),   # under EV 0.52 -> win
            dict(probs={"m": (0.30, 0.10)}, price_over=1.9, price_under=1.9, result=None)]  # under EV .2 -> push
    b = PB._bets(rows, "m")
    assert [x["side"] for x in b] == ["over", "under", "under"]
    assert [x["result"] for x in b] == ["win", "win", "push"]
    assert b[0]["net"] == pytest.approx(0.9) and b[2]["net"] == 0.0


def test_refuses_holdout():
    with pytest.raises(PB.HoldoutRefused):
        PB.split_of(dt.date(2026, 1, 15), dt.date(2026, 2, 15))
    with pytest.raises(PB.HoldoutRefused):
        PB.run_backtest("2026-03-01", "2026-03-31", ["props-v1"], ["pts"], use_cache=False)
    assert PB.main(["--start", "2026-02-01", "--end", "2026-02-28", "--out", "/nonexistent/x.json"]) == 2
    assert PB.split_of(dt.date(2026, 2, 1), dt.date(2026, 2, 28), holdout=True) == "holdout"
    assert PB.split_of(dt.date(2026, 1, 1), dt.date(2026, 1, 31)) == "validate"
    assert PB.split_of(dt.date(2024, 1, 1), dt.date(2024, 1, 31)) == "explore"
    with pytest.raises(ValueError):
        PB.split_of(dt.date(2025, 6, 1), dt.date(2025, 11, 1))


def test_report_schema_synthetic_lines(tmp_path):
    h = make_hist(tmp_path)
    rep = PB.run_backtest("2024-01-01", "2024-01-31", ["props-v0", "splitcard", "props-v1"], ["pts", "reb"],
                          hist_dir=str(h), use_cache=False, splits=SPLITS)
    assert set(rep) == {"generated_at", "commit", "runs"}
    assert len(rep["runs"]) == 2 * 4        # 4 models (naive added as v0's baseline) x 2 stats
    for r in rep["runs"]:
        assert set(r) == RUN_KEYS
        assert r["split"] == "explore" and r["kind"] == "props" and r["price_basis"] == "none"
        assert r["roi"] is None and r["roi_ci"] is None and r["bets"] == 0 and r["logloss_market"] is None
        assert len(r["calibration"]) == 10 and sum(c["n"] for c in r["calibration"]) == r["eligible"] > 0
        assert r["logloss_model"] is not None
    v1 = next(r for r in rep["runs"] if r["model_version"] == "props-v1" and r["market"] == "prop:pts")
    assert v1["baseline"] == "props-v0" and v1["coverage"]["paired_vs_props-v0"]["n"] == v1["eligible"]
    md = tmp_path / "r.json"
    PB.merge_report(str(md), rep)
    PB.write_md(str(md).replace(".json", ".md"), json.load(open(md)))
    assert "props-v1" in open(str(md).replace(".json", ".md")).read()


def test_report_real_lines_conservative_pricing(tmp_path):
    h = make_hist(tmp_path, props=True)
    rep = PB.run_backtest("2024-01-01", "2024-02-29", ["props-v0", "props-v1"], ["pts"],
                          hist_dir=str(h), use_cache=False, splits=SPLITS)
    for r in rep["runs"]:
        assert r["price_basis"] == "conservative pair"
        assert r["coverage"]["lines"] == "real pregame lines"
        assert r["logloss_market"] is None        # sides unlabelled: no de-vigged market probability
        if r["bets"]:
            assert r["avg_price_dec"] == pytest.approx(1.80)
            assert r["units_staked"] == r["bets"] and r["roi"] is not None
            assert r["net_dollars"] == pytest.approx(r["net_units"] * 100)
    assert any(r["eligible"] > 0 for r in rep["runs"])


def test_backtest_uses_only_earlier_games(tmp_path):
    h = make_hist(tmp_path)
    hist = PB.load_history(str(h), use_cache=False)
    v1 = PropModelV1(hist["rows"], hist["games"])
    d = dt.date(2024, 1, 18)
    ev, _ = PB.build_events(v1, hist, d, d, ["pts"])
    assert ev
    a = PB.score(hist, ev, ["props-v0", "splitcard", "props-v1", "naive"], ["pts"], v1)
    # change every stat on/after d: the outcomes change, the probabilities must not
    gids = {e["gid"] for e in ev}
    later = {g for g, x in hist["games"].items() if x["start_utc"][:10] >= d.isoformat()}
    rows2 = [dict(r, pts=str(int(float(r["pts"])) + 50)) if r["game_id"] in later else r for r in hist["rows"]]
    hist2 = dict(hist, rows=rows2)
    v1b = PropModelV1(rows2, hist["games"])
    ev2, _ = PB.build_events(v1b, hist2, d, d, ["pts"])
    b = PB.score(hist2, ev2, ["props-v0", "splitcard", "props-v1", "naive"], ["pts"], v1b)
    assert {e["gid"] for e in ev2} == gids
    for x, y in zip(a, b):
        assert x["value"] + 50 == y["value"] and x["line"] == y["line"]
        for m in x["probs"]:
            assert x["probs"][m] == pytest.approx(y["probs"][m])


def test_run_backtest_cache_roundtrip(tmp_path, monkeypatch):
    h = make_hist(tmp_path)
    monkeypatch.setattr(cache, "CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setattr(cache.cached, "__kwdefaults__", dict(cache.cached.__kwdefaults__, cache_dir=str(tmp_path / "cache")))
    before = dict(cache.stats)
    r1 = PB.run_backtest("2024-01-01", "2024-01-15", ["props-v1"], ["pts"], hist_dir=str(h), splits=SPLITS)
    r2 = PB.run_backtest("2024-01-01", "2024-01-15", ["props-v1"], ["pts"], hist_dir=str(h), splits=SPLITS)
    assert cache.stats["hits"] == before["hits"] + 1           # scored events served from the cache
    assert [r["logloss_model"] for r in r1["runs"]] == [r["logloss_model"] for r in r2["runs"]]
    misses = cache.stats["misses"]
    PB.run_backtest("2024-01-01", "2024-01-15", ["props-v1"], ["pts"], hist_dir=str(h), splits=SPLITS, refresh=True)
    assert cache.stats["misses"] == misses + 2
