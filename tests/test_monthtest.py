import datetime as dt, json, os, random

import pytest

from nbapicks import monthtest as MT
from nbapicks.history import BOX_COLS, GAME_COLS, ODDS_COLS, write_csv

ROOT = os.path.dirname(os.path.dirname(__file__))
CFG = os.path.join(ROOT, "config", "nbapicks.yaml")
RUN_KEYS = {"name", "kind", "market", "model_version", "baseline", "split", "period", "staking", "selection_rule",
            "price_basis", "eligible", "bets", "wins", "losses", "pushes", "voids", "hit_rate", "avg_prob",
            "avg_price_dec", "avg_implied", "units_staked", "net_units", "net_dollars", "roi", "roi_ci",
            "logloss_model", "logloss_baseline", "logloss_market", "brier_model", "brier_market", "calibration",
            "coverage", "notes"}


def make_hist(d, season=2022, start=dt.date(2021, 10, 20), days=110, box=False, seed=5):
    from nbapicks.teams import TEAMS
    rnd = random.Random(seed)
    teams = sorted(TEAMS)
    true = {t: (i - 15) * 0.7 for i, t in enumerate(teams)}
    games, odds, boxes = [], [], []
    for k in range(days):
        day = start + dt.timedelta(days=k)
        rnd.shuffle(teams)
        for i in range(0, 14, 2):
            h, a = teams[i], teams[i + 1]
            m = 2.5 + true[h] - true[a] + rnd.gauss(0, 12)
            tot = 224 + rnd.gauss(0, 18)
            hs, as_ = int(round((tot + m) / 2)), int(round((tot - m) / 2))
            if hs == as_:
                hs += 1
            gid = f"{season}{k:03d}{i:02d}"
            games.append(dict(game_id=gid, season=season, season_type="regular", start_utc=f"{day}T23:30Z", home=h,
                              away=a, status="final", home_score=hs, away_score=as_))
            spread = round(-(2.5 + true[h] - true[a]) * 2) / 2
            ph = 1 / (1 + 10 ** (spread / 13))
            for sel, line, price in (("home", "", round(1 / (ph * 1.024), 3)), ("away", "", round(1 / ((1 - ph) * 1.024), 3))):
                odds.append(dict(game_id=gid, book="DraftKings", kind="close", market="ml", selection=sel, line=line,
                                 price_dec=price, flags="final_quote_untimed"))
            for sel, line in (("home", spread), ("away", -spread)):
                odds.append(dict(game_id=gid, book="DraftKings", kind="close", market="spread", selection=sel, line=line,
                                 price_dec=1.91, flags="final_quote_untimed"))
            for sel in ("over", "under"):
                odds.append(dict(game_id=gid, book="DraftKings", kind="close", market="total", selection=sel, line=224.5,
                                 price_dec=1.91, flags="final_quote_untimed"))
            if box:
                for t in (h, a):
                    for j in range(6):
                        out = rnd.random() < 0.1
                        boxes.append(dict(game_id=gid, player_id=f"{t}{j}", player_name=f"{t} {j}", team=t, starter=1,
                                          minutes=0 if out else 30, pts="" if out else 15, reb=5, ast=3, fg3m=1, stl=1,
                                          blk=0, tov=2, played=0 if out else 1))
    write_csv(f"{d}/games_{season}.csv.gz", GAME_COLS, games)
    write_csv(f"{d}/odds_{season}.csv.gz", ODDS_COLS, odds)
    if box:
        write_csv(f"{d}/box_{season}.csv.gz", BOX_COLS, boxes)


def registry(path):
    with open(path, "w") as fh:
        fh.write(json.dumps(dict(exp_id="exp-1-trend", step="registered", variant="trend")) + "\n")
        fh.write(json.dumps(dict(exp_id="exp-1-trend", step="evaluated", results={
            "ml": {"blend_w": 0.3}, "spread": {"blend_w": 0.0}, "total": {"blend_w": 0.2}})) + "\n")
    return str(path)


def test_schema_and_runs(tmp_path):
    make_hist(tmp_path)
    reg = registry(tmp_path / "exp.jsonl")
    out = tmp_path / "rep" / "backtest_games"
    rep = MT.main(["--start", "2022-01-25", "--end", "2022-02-06", "--variants", "trend,avail", "--hist", str(tmp_path),
                   "--registry", reg, "--config", CFG, "--out", str(out)])
    on_disk = json.load(open(str(out) + ".json"))
    assert set(on_disk) == {"generated_at", "commit", "runs"}
    assert os.path.exists(str(out) + ".md")
    runs = on_disk["runs"]
    # trend: raw + blend for 3 markets x 2 kinds; avail: raw only (no experiment registered)
    assert len(runs) == 12 + 6
    for r in runs:
        assert RUN_KEYS <= set(r), RUN_KEYS - set(r)
        assert r["kind"] == "games" and r["split"] == "validate" and r["staking"] == "flat 1u per bet (1u = $100)"
        assert r["period"] == {"start": "2022-01-25", "end": "2022-02-06"}
    close = [r for r in runs if r["price_kind"] == "close"]
    assert all(r["eligible"] > 0 and r["logloss_market"] is not None for r in close)
    for r in close:
        assert r["bets"] == r["wins"] + r["losses"] + r["pushes"] + r["voids"]
        assert r["net_dollars"] == pytest.approx(100 * r["net_units"], abs=0.01)
        if r["bets"] > 1:   # a single bet has no bootstrap interval
            assert r["roi"] == pytest.approx(r["net_units"] / r["units_staked"]) and len(r["roi_ci"]) == 2
        assert sum(c["n"] for c in r["calibration"]) == r["n_games_scored"]
    # no opening lines: nothing scored, ROI stays null (never filled from assumed odds)
    opens = [r for r in runs if r["price_kind"] == "open"]
    assert all(r["eligible"] == 0 and r["roi"] is None and r["price_basis"] == "none" for r in opens)
    # w = 0 blend equals the market: no bets, zero log-loss gain
    sb = next(r for r in close if r["variant"] == "trend" and r["market"] == "spread" and r["pricing"] == "blend")
    assert sb["bets"] == 0 and sb["logloss_model"] == pytest.approx(sb["logloss_market"])
    # avail is compared with trend on the same games; this hist has no box scores: feature 0, avail == trend
    ar = next(r for r in close if r["variant"] == "avail" and r["market"] == "ml")
    tr = next(r for r in close if r["variant"] == "trend" and r["market"] == "ml" and r["pricing"] == "raw")
    assert ar["baseline"].startswith("trend") and ar["logloss_baseline"] == pytest.approx(tr["logloss_model"])
    assert ar["logloss_model"] == pytest.approx(tr["logloss_model"])
    assert ar["coverage"]["availability"]["games_with_feature"] == 0
    assert any("upper bound" in n for n in ar["notes"])
    assert rep["runs"] == runs


def test_availability_used_when_box_present(tmp_path):
    make_hist(tmp_path, box=True)
    rep = MT.build(str(tmp_path), dt.date(2022, 1, 25), dt.date(2022, 1, 31), ["avail"],
                   registry=str(tmp_path / "none.jsonl"), config_path=CFG)
    r = next(r for r in rep["runs"] if r["market"] == "ml" and r["price_kind"] == "close")
    assert r["coverage"]["availability"]["games_with_feature"] > 0


def test_holdout_refused(tmp_path, capsys):
    make_hist(tmp_path, season=2025, start=dt.date(2024, 10, 22), days=5)
    with pytest.raises(SystemExit) as e:
        MT.main(["--start", "2024-10-22", "--end", "2024-10-26", "--hist", str(tmp_path), "--config", CFG,
                 "--out", str(tmp_path / "x")])
    assert e.value.code == 2 and "holdout" in capsys.readouterr().err
    assert not os.path.exists(str(tmp_path / "x.json"))
    with pytest.raises(MT.HoldoutRefused):
        MT.build(str(tmp_path), dt.date(2025, 3, 1), dt.date(2025, 3, 2), ["trend"], config_path=CFG)
    # explicitly allowed
    assert 2025 in MT.check_holdout(str(tmp_path), dt.date(2024, 10, 22), dt.date(2024, 10, 26), allow=True)
    # a validate-season date is fine
    assert MT.check_holdout(str(tmp_path), dt.date(2023, 2, 1), dt.date(2023, 2, 28), allow=False) == {2023}


def test_frozen_weights_takes_latest_evaluated(tmp_path):
    p = tmp_path / "e.jsonl"
    rows = [dict(exp_id="a", step="registered", variant="trend"),
            dict(exp_id="a", step="evaluated", results={"ml": {"blend_w": 0.1}}),
            dict(exp_id="b", step="registered", variant="trend"),
            dict(exp_id="b", step="evaluated", results={"ml": {"blend_w": 0.2}, "spread": {"blend_w": 0.0}}),
            dict(exp_id="c", step="registered", variant="rest"),
            dict(exp_id="c", step="evaluated", results={"ml": {"blend_w": 0.9}})]
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    assert MT.frozen_weights(str(p), "trend") == ({"ml": 0.2, "spread": 0.0}, "b")
    assert MT.frozen_weights(str(p), "avail") == ({}, None)
