"""Weekly cycle: champion/challenger gates for the prop estimator, forward demotion, gated promotion."""
import json, os, shutil
import pytest
from nbapicks import weekly
from nbapicks.store import Store

ROOT = os.path.dirname(os.path.dirname(__file__))


@pytest.fixture
def repo(tmp_path, monkeypatch):
    os.makedirs(tmp_path / "config"); os.makedirs(tmp_path / "data" / "research")
    shutil.copy(os.path.join(ROOT, "config", "gates.yaml"), tmp_path / "config" / "gates.yaml")
    (tmp_path / "data" / "research" / "champion.json").write_text(json.dumps({"model_id": "ratings-v1-trend"}))
    (tmp_path / "data" / "research" / "experiments.jsonl").write_text("")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_judge_props_needs_every_stat_to_gain_with_t():
    res = {"paired": {"pts": dict(challenger="props-v1", n=900, gain=0.004, t=3.1),
                      "fg3m": dict(challenger="props-v1", n=800, gain=0.002, t=2.4)}}
    assert weekly.judge_props(res, "props-v0", "props-v1", {"logloss_gain_min_t": 2.0})["passes"]
    res["paired"]["fg3m"]["t"] = 1.2
    v = weekly.judge_props(res, "props-v0", "props-v1", {"logloss_gain_min_t": 2.0})
    assert not v["passes"] and v["per_stat"]["fg3m"]["ok"] is False
    assert not weekly.judge_props({}, "props-v0", "props-v1", {})["passes"]     # no evidence -> no pass


def _settled_props(store, n, prob, win_rate, model="props-v1"):
    store.put("games", dict(game_id="g", start_utc="2026-10-21T23:00:00Z", home="A", away="B", status="final",
                            observed_at="2026-11-01T12:00:00Z", source="t"))
    for i in range(n):
        pid = f"p{i}"
        store.put("predictions", dict(pred_id=pid, created_at="2026-10-21T15:00:00Z", origin="model", provider="t",
                                      model_version=model, category="straight", game_id="g", market="prop", selection="over",
                                      line=10.5, prob=prob, decision="watch", reason="x"))
        store.put("pred_events", dict(event_id=f"e{i}", pred_id=pid, at="x", type="settled",
                                      result="win" if i < n * win_rate else "loss", net_units=0))


def test_forward_check_demotes_a_badly_calibrated_prop_model(repo):
    json.dump({"model_id": "x", "props": {"model_id": "props-v1"}}, open("data/research/champion.json", "w"))
    s = Store(None)
    _settled_props(s, 160, 0.70, 0.45)
    gates = weekly._gates()
    out = weekly.forward_prop_check(s, gates)
    assert out["action"] == "demoted to props-v0"
    assert json.load(open("data/research/champion.json"))["props"]["model_id"] == "props-v0"
    assert "demote" in open("data/research/decisions.jsonl").read()


def test_forward_check_keeps_a_calibrated_model_and_needs_a_sample(repo):
    json.dump({"model_id": "x", "props": {"model_id": "props-v1"}}, open("data/research/champion.json", "w"))
    s = Store(None)
    _settled_props(s, 160, 0.60, 0.60)
    assert weekly.forward_prop_check(s, weekly._gates())["action"] == "none"
    s2 = Store(None)
    _settled_props(s2, 20, 0.90, 0.10)
    assert weekly.forward_prop_check(s2, weekly._gates())["action"].startswith("none")


def test_forward_check_ignores_predictions_from_before_the_model_was_reinstated(repo):
    json.dump({"model_id": "x", "props": {"model_id": "props-v1", "since": "2026-11-27"}}, open("data/research/champion.json", "w"))
    s = Store(None)
    _settled_props(s, 160, 0.70, 0.45)           # badly calibrated, but created 2026-10-21, before `since`
    out = weekly.forward_prop_check(s, weekly._gates())
    assert out["action"].startswith("none") and out["n"] == 0


def test_promotion_needs_a_passing_evaluation_and_a_review_file(repo):
    with pytest.raises(SystemExit):
        weekly.promote("props-v1", "team/reviews/missing.md")
    os.makedirs("team/reviews"); open("team/reviews/r.md", "w").write("PASS")
    with pytest.raises(SystemExit):                       # no evaluation yet
        weekly.promote("props-v1", "team/reviews/r.md")
    open("data/research/experiments.jsonl", "a").write(json.dumps(dict(exp_id="exp-1-prop-props-v1", step="evaluated",
                                                                         decision="rejected")) + "\n")
    with pytest.raises(SystemExit):                       # evaluated but failed
        weekly.promote("props-v1", "team/reviews/r.md")
    open("data/research/experiments.jsonl", "a").write(json.dumps(dict(exp_id="exp-2-prop-props-v1", step="evaluated",
                                                                         decision="candidate")) + "\n")
    assert weekly.promote("props-v1", "team/reviews/r.md") == "promoted props-v1"
    ch = json.load(open("data/research/champion.json"))
    assert ch["props"]["model_id"] == "props-v1" and ch["model_id"] == "ratings-v1-trend"
    assert "market status unchanged" in open("data/research/decisions.jsonl").read()


def test_judge_props_reads_propbacktest_runs_with_the_conservative_t():
    res = {"runs": [dict(model_version="props-v1", market="prop:pts",
                         coverage={"paired_vs_props-v0": dict(n=1000, gain=0.02, t=9.0, t_day_cluster=1.5)}),
                    dict(model_version="props-v0", market="prop:pts", coverage={})]}
    v = weekly.judge_props(res, "props-v0", "props-v1", {"logloss_gain_min_t": 2.0})
    assert v["per_stat"]["pts"]["t"] == 1.5 and not v["passes"]
