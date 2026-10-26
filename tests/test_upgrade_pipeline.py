"""Upgrade (2026-10-22): prop side pricing, versioned candidate ledger, research parlays,
signal-vs-model comparison, partitioned predictions."""
import datetime as dt, glob, json, os
import pytest
from nbapicks import pipeline, propsides as PS, signals, odds as O
from nbapicks.store import Store
from tests.test_e2e import env, NOW, load  # noqa: F401  (fixture)


# ---- prop sides -------------------------------------------------------------------------
def test_bracket_from_ladder():
    lad = [(14.5, 0.80), (19.5, 0.45), (24.5, 0.20)]
    assert PS.bracket(lad, 19.5) == (0.45, 0.45)
    assert PS.bracket(lad, 16.5) == (0.45, 0.80)      # between 15+ and 20+
    assert PS.bracket(lad, 30.5) == (0.0, 0.20)       # above the ladder: only an upper bound
    assert PS.bracket([], 10.5) is None


def test_label_pair_picks_the_side_inside_the_bracket():
    lad = [(14.5, 0.85), (19.5, 0.50)]
    # side1 is the favourite (~62%); P(over 16.5) must lie in [0.42, 0.87]: both fit -> no exact match -> None
    assert PS.label_pair(2.4, 1.55, lad, 16.5) is None or PS.label_pair(2.4, 1.55, lad, 16.5) in ("side0", "side1")
    lad2 = [(14.5, 0.95), (19.5, 0.80)]                # strongly over-ish at 16.5: [0.72, 0.97]
    assert PS.label_pair(4.0, 1.22, lad2, 16.5) == "side1"   # side1 de-vigs to ~0.77
    assert PS.label_pair(1.22, 4.0, lad2, 16.5) == "side0"
    assert PS.label_pair(1.91, 1.91, lad2, 16.5) is None     # too close to tell apart
    assert PS.label_pair(4.0, 1.22, None, 16.5) is None


def test_conservative_price_is_the_worse_of_the_pair():
    sides = {"side0": dict(price_dec=1.80), "side1": dict(price_dec=2.05)}
    p = PS.price_sides(sides, None)
    assert p["over"] == (1.80, None, "conservative") and p["under"] == (1.80, None, "conservative")
    q = PS.price_sides(sides, "side1")
    assert q["over"][0] == 2.05 and q["under"][0] == 1.80 and q["over"][2] == "labelled"
    assert abs(q["over"][1] + q["under"][1] - 1) < 1e-9
    # EV at the conservative price is a lower bound on EV at the true price
    assert O.ev_binary(0.6, 1.80) <= O.ev_binary(0.6, 2.05)



def test_plausible_pair_rejects_ladder_rungs():
    assert PS.plausible_pair(1.91, 1.91) and PS.plausible_pair(1.80, 2.02)
    assert not PS.plausible_pair(15.0, 26.0) and not PS.plausible_pair(2.5, 2.5)   # sums 0.10 and 0.80
    assert not PS.plausible_pair(1.2, 1.3) and not PS.plausible_pair(1.0, 2.0)

# ---- ledger versioning ------------------------------------------------------------------
def test_rerun_with_same_inputs_writes_nothing_and_lists_the_same_set(env):
    root, cfg, state = env
    ctx = pipeline.Ctx(NOW, cfg, root)
    pipeline.ingest(ctx); ctx.save_state()
    s1 = pipeline.predict(ctx)
    n1 = ctx.store.one("SELECT count(*) n FROM predictions")["n"]
    ids1 = json.load(open(f"{root}/state/last_predict.json"))["pred_ids"]
    s2 = pipeline.predict(pipeline.Ctx(NOW + dt.timedelta(minutes=5), cfg, root))
    n2 = Store(root).one("SELECT count(*) n FROM predictions")["n"]
    ids2 = json.load(open(f"{root}/state/last_predict.json"))["pred_ids"]
    assert s1["written"] > 0 and s2["written"] == 0 and n1 == n2
    assert set(ids1) == set(ids2) and len(ids1) == len(set(ids1))


def test_every_candidate_is_recorded_including_props_without_estimates(env):
    root, cfg, state = env
    ctx = pipeline.Ctx(NOW, cfg, root)
    pipeline.ingest(ctx)
    s = pipeline.predict(ctx)
    preds = ctx.store.q("SELECT * FROM predictions WHERE origin = 'model' AND category = 'straight'")
    props = [p for p in preds if p["market"] == "prop"]
    assert props, "DraftKings props must be recorded now (they were all dropped before)"
    # no placeholder probabilities: a prop without an estimate has prob NULL and says why
    for p in props:
        if p["prob"] is None:
            assert p["decision"] == "reject" and "no model estimate" in p["reason"]
        inp = json.loads(p["inputs"])
        assert inp["price_basis"] in ("labelled", "conservative")
        assert abs(inp["implied"] - 1 / p["price_dec"]) < 1e-3
    # both sides of a DraftKings pair are candidates, with readable over/under selections
    assert {p["selection"] for p in props} <= {"over", "under"}
    assert sum(s["decisions"].values()) == s["candidates"]


def test_predictions_are_partitioned_by_month(env):
    root, cfg, state = env
    ctx = pipeline.Ctx(NOW, cfg, root)
    pipeline.ingest(ctx); pipeline.predict(ctx)
    assert glob.glob(f"{root}/ledger/predictions/2026-10.jsonl")
    assert not os.path.exists(f"{root}/ledger/predictions.jsonl")


def test_legacy_flat_prediction_file_still_replays(tmp_path):
    root = str(tmp_path)
    os.makedirs(f"{root}/ledger")
    rec = dict(pred_id="legacy1", created_at="2026-10-20T15:00:00Z", origin="model", provider="nbapicks",
               category="straight", decision="watch", reason="x")
    open(f"{root}/ledger/predictions.jsonl", "w").write(json.dumps(rec) + "\n")
    s = Store(root)
    assert s.one("SELECT pred_id FROM predictions")["pred_id"] == "legacy1"
    s.put("predictions", dict(rec, pred_id="new1", created_at="2026-10-23T15:00:00Z"))
    assert Store(root).one("SELECT count(*) n FROM predictions")["n"] == 2
    assert os.path.exists(f"{root}/ledger/predictions/2026-10.jsonl")


def test_publish_uses_the_current_candidate_set(env):
    root, cfg, state = env
    ctx = pipeline.Ctx(NOW, cfg, root)
    pipeline.ingest(ctx); pipeline.predict(ctx)
    assert pipeline.publish_picks(ctx) == "dry_run"
    cur = set(json.load(open(f"{root}/state/last_predict.json"))["pred_ids"])
    noted = {e["pred_id"] for e in ctx.store.q("SELECT pred_id FROM pred_events WHERE type = 'note'")}
    assert noted <= cur


# ---- parlays ---------------------------------------------------------------------------
class _C:
    def __init__(self, gid, ev, prob, price, decision="watch", market="ml"):
        self.game_id, self.ev, self.prob, self.price_dec, self.decision = gid, ev, prob, price, decision
        self.market, self.category, self.push, self.label, self.inputs = market, "straight", 0.0, f"leg {gid}", {}


def test_research_parlays_only_from_legs_that_cleared_their_threshold(env):
    root, cfg, state = env
    ctx = pipeline.Ctx(NOW, cfg, root)
    legs = [_C("g1", 0.06, 0.55, 2.0), _C("g2", 0.07, 0.56, 1.95), _C("g3", 0.01, 0.52, 1.95), _C("g1", 0.08, 0.5, 2.2)]
    out = pipeline.build_parlays(ctx, legs, cfg)
    assert out and all(len({c.game_id for c in pz["legs"]}) == len(pz["legs"]) for pz in out)   # never same game
    assert all("g3" not in {c.game_id for c in pz["legs"]} for pz in out)                     # below its own threshold
    for pz in out:
        p = 1.0
        for c in pz["legs"]:
            p *= c.prob
        assert abs(pz["prob"] - p) < 1e-12 and abs(pz["ev"] - (p * pz["price_dec"] - 1)) < 1e-9
    assert sum(pz["kind"] == "parlay" for pz in out) <= cfg["targets"]["parlay"]


def test_no_parlay_when_no_leg_qualifies(env):
    root, cfg, state = env
    ctx = pipeline.Ctx(NOW, cfg, root)
    assert pipeline.build_parlays(ctx, [_C("g1", 0.0, 0.5, 1.9), _C("g2", -0.02, 0.5, 1.9)], cfg) == []


# ---- signals ----------------------------------------------------------------------------
def test_signal_is_compared_with_the_model_but_kept_separate(env):
    root, cfg, state = env
    ctx = pipeline.Ctx(NOW, cfg, root)
    pipeline.ingest(ctx); pipeline.predict(ctx)
    m = ctx.store.q("SELECT * FROM predictions WHERE origin = 'model' AND market = 'ml' AND prob IS NOT NULL")[0]
    ctx.store.put("predictions", dict(pred_id="sig1", created_at="2026-10-21T17:00:00Z", origin="signal", provider="disc",
                                      category="straight", game_id=m["game_id"], market="ml", selection=m["selection"],
                                      line=None, price_dec=2.1, book="as stated", decision="info", reason="imported signal",
                                      stake_units=1.0))
    r = signals.compare_with_model(ctx)
    assert r["compared"] == 1
    ev = ctx.store.q("SELECT data FROM pred_events WHERE pred_id = 'sig1' AND type = 'note'")
    d = json.loads(ev[0]["data"])["model_compare"]
    assert abs(d["model_ev_at_signal_price"] - O.ev_with_push(d["model_prob"], 0.0, 2.1)) < 1e-9
    assert signals.compare_with_model(ctx)["compared"] == 0                     # idempotent
    assert ctx.store.one("SELECT origin FROM predictions WHERE pred_id = 'sig1'")["origin"] == "signal"


# ---- portfolio correlation caps ----------------------------------------------------------
def test_portfolio_caps_props_per_player_and_game_and_probation():
    from nbapicks import config
    from nbapicks.qualify import Candidate, portfolio
    cfg = config.load()
    mk = lambda gid, pid, stat, ev, market="prop": Candidate(game_id=gid, start_utc="2026-10-21T23:00Z", home="A", away="B",
        market=market, selection="over", line=10.5, price_dec=2.0, book="DraftKings", price_observed_at=None, prob=0.6,
        player_id=pid, stat=stat, ev=ev, decision="eligible")
    cs = [mk("g1", "p1", "pts", 0.20), mk("g1", "p1", "reb", 0.15), mk("g1", "p2", "pts", 0.12), mk("g1", "p3", "pts", 0.11),
          mk("g2", "p4", "ast", 0.10), mk("g3", None, None, 0.09, market="total")]
    portfolio(cs, cfg, probation={"total"})
    assert [c.decision for c in cs] == ["eligible", "hold", "eligible", "hold", "eligible", "hold"]
    assert "correlated" in cs[1].reasons[-1] and "per game" in cs[3].reasons[-1] and "probation" in cs[5].reasons[-1]


def test_failed_ingest_skips_predict_and_fails_the_run(env, monkeypatch, tmp_path):
    from nbapicks.sources import espn
    root, cfg, state = env
    def boom(day):
        raise OSError("network down")
    monkeypatch.setattr(espn, "fetch_scoreboard", boom)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(pipeline.C, "load", lambda: cfg)
    monkeypatch.setattr(pipeline, "Ctx", lambda now, c, slate=None: _Ctx(now, c, root))
    rc = pipeline.main(["ingest", "predict", "export", "--now", "2026-10-21T16:00:00Z"])
    rep = json.loads(open(f"{tmp_path}/data/state/runs.jsonl").read().splitlines()[-1])
    assert rc == 1 and rep["steps"]["ingest"]["status"] == "failed" and rep["steps"]["predict"]["status"] == "skipped"


_Ctx = pipeline.Ctx


# ---- global pause -----------------------------------------------------------------------
def test_global_pause_blocks_new_recommendations_but_not_ingest_or_settle(env, monkeypatch, tmp_path):
    root, cfg, state = env
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(pipeline.C, "load", lambda: cfg)
    monkeypatch.setattr(pipeline, "Ctx", lambda now, c, slate=None: _Ctx(now, c, root))
    os.makedirs(f"{root}/state", exist_ok=True)
    open(f"{root}/state/PAUSED", "w").write(json.dumps({"reason": "odds feed failing validation"}))
    assert pipeline.pause_state(f"{root}/state")["reason"] == "odds feed failing validation"
    rc = pipeline.main(["ingest", "predict", "publish", "settle", "--now", "2026-10-21T16:00:00Z"])
    rep = json.loads(open(f"{root}/state/runs.jsonl").read().splitlines()[-1])
    assert rc == 0 and rep["steps"]["ingest"]["status"] == "completed" and rep["steps"]["settle"]["status"] == "completed"
    assert rep["steps"]["predict"]["status"] == "skipped" and "global pause" in rep["steps"]["predict"]["reason"]
    assert rep["steps"]["publish"]["status"] == "skipped" and rep["paused"]["reason"].startswith("odds feed")
    assert Store(root).one("SELECT count(*) n FROM predictions")["n"] == 0
    os.remove(f"{root}/state/PAUSED")                         # resuming is deliberate: remove the file
    assert pipeline.pause_state(f"{root}/state") is None
