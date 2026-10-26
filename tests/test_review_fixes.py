"""Regression tests for fixes made after the 2026-10-20 reviews (team/reviews/)."""
import datetime as dt, json, os
import pytest
from nbapicks import pipeline, config
from nbapicks.sources import espn
from tests.test_e2e import env, NOW  # noqa: F401

HDR = "wager_id,corrects,placed_at,book,game_id,market,selection,line,price_american,price_dec,stake,units,player_id,stat,legs,result,net,notes\n"


def _w(root, rows):
    os.makedirs(f"{root}/manual", exist_ok=True)
    open(f"{root}/manual/wagers.csv", "w").write(HDR + "".join(r + "\n" for r in rows))


def _final(env_):
    root, cfg, state = env_
    ctx = pipeline.Ctx(NOW, cfg, root); pipeline.ingest(ctx); ctx.save_state()
    gids = [g["game_id"] for g in ctx.store.q("SELECT game_id FROM games ORDER BY game_id")]
    state["final"] = True
    return root, cfg, gids


def test_correction_replaces_wager_and_manual_result_settles(env):
    root, cfg, gids = _final(env)
    _w(root, [f"w1,,2026-10-21T17:00:00Z,FanDuel,{gids[0]},ml,home,,-140,,2,1,,,,,,typo",
              f"w2,w1,2026-10-21T17:00:00Z,FanDuel,{gids[0]},ml,home,,-120,,2,1,,,,,,fixed price",
              f"w3,,2026-10-21T17:05:00Z,FanDuel,,parlay,home,,+600,,0.5,0.5,,,{gids[0]} ml home; {gids[1]} ml home,loss,,3 legs",
              f"w4,,2026-10-21T17:06:00Z,FanDuel,{gids[1]},ml,away,,+150,,1,1,,,,cashout,0.4,cashed out"])
    c = pipeline.Ctx(NOW + dt.timedelta(hours=14), cfg, root); pipeline.ingest(c); pipeline.settle(c)
    ev = {(e["wager_id"], e["type"]): e for e in c.store.q("SELECT * FROM wager_events")}
    assert ("w1", "corrected") in ev and ("w1", "settled") not in ev
    assert ev[("w2", "settled")]["result"] in ("win", "loss")
    assert ev[("w3", "settled")]["result"] == "loss" and ev[("w3", "settled")]["net"] == -0.5
    assert ev[("w4", "settled")]["result"] == "cashout" and ev[("w4", "settled")]["net"] == 0.4
    from nbapicks.dashboard import export
    data = json.load(open(export(c, str(c.root) + "/site")["path"]))
    assert data["actual"]["summary"]["n"] == 3      # the corrected w1 does not count


def test_bad_rows_are_reported_not_fatal(env):
    root, cfg, gids = _final(env)
    _w(root, [f",,2026-10-21T17:00:00Z,FanDuel,{gids[0]},total,over,,-110,,1,1,,,,,,no line",
              f",,2026-10-21T17:00:00Z,FanDuel,{gids[0]},ml,Magic,,-110,,1,1,,,,,,team name",
              f",,2026-10-21T17:00:00Z,FanDuel,{gids[0]},ml,home,,-110,,1,1,,,,maybe,,bad result"])
    c = pipeline.Ctx(NOW + dt.timedelta(hours=14), cfg, root); out = pipeline.import_wagers(c)
    assert out["wager_errors"] == 3 and sum("wagers.csv line" in n for n in c.notes) == 3


def test_wager_after_8pm_eastern_belongs_to_that_nights_slate(env):
    root, cfg, gids = _final(env)
    c = pipeline.Ctx(NOW, cfg, root)
    w = dict(placed_at="2026-10-22T01:30:00Z", game_id=None)
    assert pipeline.wager_slate(c, w, {}) == "2026-10-21"


def test_odds_seen_is_pruned_for_old_games(env):
    root, cfg, state = env
    c = pipeline.Ctx(NOW, cfg, root); pipeline.ingest(c)
    n = len(c.seen); assert n > 0
    c.now = NOW + dt.timedelta(days=4)
    assert pipeline.prune_seen(c) == n and not c.seen


def test_espn_parser_rejects_price_in_line_field_and_maps_status():
    d = {"items": [{"provider": {"name": "ESPN BET"}, "homeTeamOdds": {"close": {"pointSpread": {"american": "-110"}, "spread": {"american": "-110"}}},
                    "awayTeamOdds": {"close": {"pointSpread": {"american": "+110"}, "spread": {"american": "-110"}}}},
                   {"provider": {"name": "Draft Kings"}, "homeTeamOdds": {"close": {"moneyLine": {"american": "-150"}}},
                    "awayTeamOdds": {"close": {"moneyLine": {"american": "+130"}}}}]}
    rows = espn.parse_core_odds(d, "g", "t", game_final=True)
    assert not [r for r in rows if r["market"] == "spread"]
    assert {r["book"] for r in rows} == {"DraftKings"}
    assert espn._status({"name": "STATUS_SOMETHING_NEW", "state": "post", "completed": True}) == "final"
    assert espn._status({"name": "STATUS_SOMETHING_NEW", "state": "post", "completed": False}) == "unknown"


def test_config_requires_every_market_and_known_timezone():
    c = config.load()
    del c["markets"]["lotto"]; c["timezone"] = "Mars/Olympus"
    with pytest.raises(config.ConfigError) as e:
        config.validate(c)
    assert "lotto" in str(e.value) and "Mars" in str(e.value)


def test_promoted_market_without_frozen_weight_refuses_to_price(env, monkeypatch, tmp_path):
    root, cfg, state = env
    p = tmp_path / "c.json"; p.write_text(json.dumps({"model_id": "x"}))
    monkeypatch.setattr(pipeline, "CHAMPION", str(p))
    with pytest.raises(RuntimeError):
        pipeline.frozen_blend(cfg, "ml")
    cfg["markets"]["ml"]["status"] = "research"
    assert pipeline.frozen_blend(cfg, "ml") is None


def test_early_read_of_a_later_slate(env):
    root, cfg, state = env
    early = NOW - dt.timedelta(hours=20)            # the evening before the 2026-10-21 slate
    c = pipeline.Ctx(early, cfg, root, slate=dt.date(2026, 10, 21))
    pipeline.ingest(c)
    s = pipeline.predict(c)
    assert s["slate"] == "2026-10-21" and s["games"] == 11
