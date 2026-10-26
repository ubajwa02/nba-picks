import pathlib
"""End-to-end on captured real responses with the network replaced by fixtures:
ingest -> predict/qualify -> publish (dry run) -> results -> settle -> recap -> export,
then a second pass to prove nothing duplicates."""
import copy, datetime as dt, json, os, random
import pytest
from nbapicks import config, pipeline
from nbapicks.history import write_csv, GAME_COLS
from nbapicks.sources import espn, moviodds
from nbapicks.teams import TEAMS

F = os.path.join(os.path.dirname(__file__), "fixtures")
load = lambda n: json.load(open(os.path.join(F, n)))
NOW = dt.datetime(2026, 10, 21, 16, 0, tzinfo=dt.timezone.utc)


def synth_history(root):
    rnd = random.Random(3); teams = sorted(TEAMS); rows = []; gid = 0
    for day in range(160):
        d = dt.date(2025, 10, 22) + dt.timedelta(days=day)
        rnd.shuffle(teams)
        for i in range(0, 12, 2):
            hs, as_ = rnd.randint(95, 130), rnd.randint(95, 130)
            if hs == as_:
                hs += 1
            rows.append(dict(game_id=f"h{gid}", season=2026, season_type="regular", start_utc=f"{d}T23:00Z",
                             home=teams[i], away=teams[i + 1], status="final", home_score=hs, away_score=as_)); gid += 1
    write_csv(f"{root}/history/games_2026.csv.gz", GAME_COLS, rows)


@pytest.fixture
def env(tmp_path, monkeypatch):
    root = str(tmp_path / "data")
    synth_history(root)
    state = {"final": False}
    pre = load("espn_scoreboard_pre_20261021.json")

    def scoreboard(day):
        if day != dt.date(2026, 10, 21):
            return {"events": []}
        d = copy.deepcopy(pre)
        if state["final"]:
            for i, ev in enumerate(d["events"]):
                ev["status"]["type"]["name"] = "STATUS_FINAL"; ev["status"]["type"]["state"] = "post"
                for c in ev["competitions"][0]["competitors"]:
                    c["score"] = str(110 + i if c["homeAway"] == "home" else 104)
        return d
    monkeypatch.setattr(espn, "fetch_scoreboard", scoreboard)
    monkeypatch.setattr(espn, "fetch_core_odds", lambda gid: load("espn_core_odds_pre.json"))
    monkeypatch.setattr(espn, "fetch_propbets", lambda gid, p="100": load("espn_propbets_pre.json"))
    monkeypatch.setattr(espn, "fetch_athlete_name", lambda ref: "CJ McCollum")
    monkeypatch.setattr(espn, "fetch_injuries", lambda: load("espn_injuries.json"))
    monkeypatch.setattr(espn, "fetch_summary", lambda gid: load("espn_summary_final.json"))
    monkeypatch.setattr(moviodds, "fetch_nba", lambda: load("moviodds_nba.json"))
    champ = tmp_path / "champion.json"   # promoted markets need a frozen blend weight; 1.0 = the raw model
    champ.write_text(json.dumps(dict(model_id="test", params={"total_trend": True},
                                     markets={m: dict(blend_w=1.0) for m in ("ml", "spread", "total", "prop")})))
    monkeypatch.setattr(pipeline, "CHAMPION", str(champ))
    cfg = config.load()
    for m in cfg["markets"].values():
        m["status"] = "paper"
    cfg["quality"]["max_odds_age_minutes"] = 10 ** 6
    return root, cfg, state


def test_full_day(env, tmp_path):
    root, cfg, state = env
    ctx = pipeline.Ctx(NOW, cfg, root)
    ing = pipeline.ingest(ctx)
    assert ing["games_new"] == 11 and ing["odds_snaps"] > 0 and ing["injury_obs"] > 0
    assert ctx.health["espn_odds"]["consecutive_failures"] == 0
    s = pipeline.predict(ctx)
    assert s["model_ready"] and s["games"] == 11
    # NBA-032 split cards are written as watchlist info; NBA-031 prop lines are archived with fetch time
    sc = json.loads((pathlib.Path(root) / "state" / "split_cards_latest.json").read_text())
    assert sc["status"].startswith("research") and s["split_cards"] == len(sc["cards"])
    props = ctx.store.q("SELECT * FROM odds WHERE market = 'prop'")
    assert props and all(r["observed_at"] for r in props)
    preds = ctx.store.q("SELECT * FROM predictions")
    assert preds and all(p["decision"] and p["reason"] for p in preds)
    # every eligible pick obeys the caps
    elig = [p for p in preds if p["decision"] == "eligible" and p["category"] == "straight"]
    assert len(elig) <= cfg["targets"]["straight"]
    assert sum(p["stake_units"] for p in elig) <= cfg["risk"]["max_units_per_day"]
    # unverified prop sides never become picks
    assert not [p for p in preds if p["market"] == "prop" and p["decision"] == "eligible" and p["selection"].startswith("side")]
    par = [p for p in preds if p["category"] in ("parlay", "lotto")]
    assert sum(p["stake_units"] for p in par if p["category"] == "parlay") <= cfg["risk"]["max_parlay_units_per_day"]
    assert sum(p["stake_units"] for p in par if p["category"] == "lotto") <= cfg["risk"]["max_lotto_units_per_day"]
    for p in par:
        legs = json.loads(p["legs"])
        assert len({l["pred_id"] for l in legs}) == len(legs)
        assert p["prob"] == pytest.approx(__import__("math").prod(l["prob"] for l in legs))
    st = pipeline.publish_picks(ctx)
    assert st == "dry_run"
    assert pipeline.publish_picks(ctx) == "already_dry_run"
    pub = ctx.store.one("SELECT * FROM publications WHERE kind = 'picks'")
    assert "NBA Picks" in pub["detail"]
    ctx.save_state()

    # games finish; a later run settles and recaps
    state["final"] = True
    later = pipeline.Ctx(NOW + dt.timedelta(hours=14), cfg, root)
    pipeline.ingest(later)
    assert later.store.one("SELECT count(*) n FROM games WHERE status = 'final'")["n"] == 11
    out = pipeline.settle(later)
    assert sum(out.get(k, 0) for k in ("win", "loss", "push", "void")) > 0
    # settlement is written once
    assert pipeline.settle(later).get("win", 0) == 0
    r = pipeline.recap(later, "2026-10-21")
    assert r == "dry_run"
    from nbapicks.dashboard import export
    e = export(later, str(tmp_path / "site"))
    data = json.load(open(e["path"]))
    assert data["config"]["dry_run"] is True
    assert data["theoretical"]["summary"]["n"] == len([p for p in data["published"] if p["result"] != "pending"])
    assert data["actual"]["summary"]["n"] == 0          # no wager log: no actual results invented
    pub_straight = [p for p in data["published"] if p["category"] == "straight" and p["result"] != "pending"]
    assert data["paper"]["summary"]["n"] >= len(pub_straight)

    # predictions are immutable in the ledger files
    # the ledger on disk replays to the same state, and predictions were never rewritten
    from nbapicks.store import Store
    s2 = Store(root)
    assert s2.one("SELECT count(*) n FROM predictions")["n"] == len(preds)
    import glob
    lines = [l for f in glob.glob(f"{root}/ledger/predictions*.jsonl") + glob.glob(f"{root}/ledger/predictions/*.jsonl")
             for l in open(f).read().splitlines() if l.strip()]
    assert len(lines) == len(preds)


def test_wager_log_is_the_only_actual_source(env):
    root, cfg, state = env
    ctx = pipeline.Ctx(NOW, cfg, root)
    pipeline.ingest(ctx)
    gid = ctx.store.q("SELECT game_id FROM games")[0]["game_id"]
    os.makedirs(f"{root}/manual", exist_ok=True)
    with open(f"{root}/manual/wagers.csv", "w") as fh:
        fh.write("placed_at,book,game_id,market,selection,line,price_american,price_dec,stake,units,pred_id,player_id,stat,notes\n")
        fh.write(f"2026-10-21T17:00:00Z,FanDuel,{gid},ml,home,,-140,,10,1,,,,test\n")
    state["final"] = True
    later = pipeline.Ctx(NOW + dt.timedelta(hours=14), cfg, root)
    pipeline.ingest(later)
    out = pipeline.settle(later)
    assert out["wagers_new"] == 1 and out["wagers_settled"] == 1
    w = later.store.one("SELECT * FROM wager_events")
    assert w["result"] == "win" and w["net"] == pytest.approx(10 * 100 / 140)


def test_signals_import_settle_and_provider_stats(env, tmp_path):
    root, cfg, state = env
    ctx = pipeline.Ctx(NOW, cfg, root)
    os.makedirs(f"{root}/manual", exist_ok=True)
    with open(f"{root}/manual/signals.csv", "w") as fh:
        fh.write('provider,posted_at,text,channel\n')
        fh.write('SharpGuy,2026-10-21T15:00:00Z,"Magic ML -140 1u\nHawks Magic o235.5 -110\nLakers -3.5",picks\n')
        fh.write('SharpGuy,2026-10-21T15:05:00Z,"gm all",picks\n')
    out = pipeline.ingest(ctx)
    assert out["signals_raw_new"] == 2 and out["signals_picks"] == 2 and out["signals_ambiguous"] == 1
    sig = ctx.store.q("SELECT * FROM predictions WHERE origin = 'signal'")
    assert {(p["market"], p["selection"]) for p in sig} == {("ml", "home"), ("total", "over")}
    raw = ctx.store.one("SELECT * FROM signals_raw WHERE parse_status = 'ambiguous'")
    assert "no odds stated" in raw["parse_error"]
    assert pipeline.ingest(ctx).get("signals_raw_new", 0) == 0     # idempotent
    ctx.save_state()
    state["final"] = True
    later = pipeline.Ctx(NOW + dt.timedelta(hours=14), cfg, root)
    pipeline.ingest(later); pipeline.settle(later)
    from nbapicks.dashboard import export
    data = json.load(open(export(later, str(tmp_path / "site"))["path"]))
    p = data["providers"]["SharpGuy"]
    assert p["picks"] == 2 and p["settled"] == 2 and p["wins"] + p["losses"] == 2
    assert data["theoretical"]["summary"]["n"] == 0 or all(r.get("pred_id") not in [s["pred_id"] for s in sig] for r in data["published"])


def test_diagnostics_runs_on_settled_ledger(env, tmp_path, monkeypatch):
    root, cfg, state = env
    ctx = pipeline.Ctx(NOW, cfg, root)
    pipeline.ingest(ctx); pipeline.predict(ctx); ctx.save_state()
    state["final"] = True
    later = pipeline.Ctx(NOW + dt.timedelta(hours=14), cfg, root)
    pipeline.ingest(later); pipeline.settle(later)
    monkeypatch.chdir(tmp_path)
    os.makedirs("config"); import shutil
    shutil.copy(os.path.join(os.path.dirname(F), "..", "config", "gates.yaml"), "config/gates.yaml")
    from nbapicks.diagnose import run
    out = run(later)
    assert set(out["markets"]) <= {"ml", "spread", "total"} and out["queued"] <= 3
    assert os.path.exists("reports/diagnostics.md") and os.path.exists("data/research/queue.yaml")
