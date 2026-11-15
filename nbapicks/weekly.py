"""Weekly improvement cycle (GitHub Actions, no LLM): evaluate, diagnose, test challengers,
promote only through pre-registered gates plus a recorded independent review, demote
automatically.

    python -m nbapicks.weekly                 # the scheduled cycle
    python -m nbapicks.weekly --promote props-v1 --review team/reviews/<file>.md

Steps
1. Live diagnostics on settled predictions (nbapicks.diagnose): calibration, drift, segments,
   at most three queued hypotheses, market probation when the demotion gate trips.
2. Game-market challengers from the queue (nbapicks.research --from-queue), walk-forward,
   explore/validate only.
3. Prop-model challengers on the pre-registered validate window (config/gates.yaml props),
   registered before evaluation, scored against the champion on the same events.
4. Forward check of the prop model in use: if its settled live predictions are badly
   calibrated (demotion gate), fall back to props-v0 and record why.
5. reports/weekly_latest.md and the dashboard export.

Promotion never happens inside the scheduled cycle: a challenger that passes is marked
'candidate'; `--promote` applies it only when the latest evaluation passed and a review
file is named (the review is the independent check the gates require).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os

import yaml

from . import metrics as M
from .research import REG, append, commit, now

CHAMP = "data/research/champion.json"
DECISIONS = "data/research/decisions.jsonl"
PROP_CHALLENGERS = ("props-v1",)


def _gates():
    return yaml.safe_load(open("config/gates.yaml"))


def _champ():
    try:
        return json.load(open(CHAMP))
    except FileNotFoundError:
        return {}


def prop_challengers(stats=("pts", "fg3m", "reb", "ast"), today: dt.date | None = None) -> dict:
    """Score champion vs challengers on the validate window (never the holdout)."""
    from .propbacktest import run_backtest
    g = (_gates().get("props") or {})
    val = g.get("validate") or {}
    start, end = str(val.get("start", "2025-10-01")), str(val.get("end", "2026-01-31"))
    champ = (_champ().get("props") or {}).get("model_id", "props-v0")
    out = {}
    for ch in PROP_CHALLENGERS:
        if ch == champ:
            continue
        exp_id = f"exp-{(today or dt.date.today()):%Y%m%d}-prop-{ch}"
        append(REG, dict(exp_id=exp_id, step="registered", at=now(), commit=commit(), variant=ch, baseline=champ,
                         hypothesis=f"{ch} estimates prop outcomes better than {champ} (paired log loss on the same events)",
                         criteria=g.get("paper") or {}, splits=["validate"], window=[start, end]))
        res = run_backtest(start, end, [champ, ch], list(stats))
        verdict = judge_props(res, champ, ch, g.get("paper") or {})
        append(REG, dict(exp_id=exp_id, step="evaluated", at=now(), commit=commit(), results=verdict,
                         decision="candidate" if verdict["passes"] else "rejected", reviewer="pending-independent-review"))
        out[ch] = verdict
    return out


def judge_props(res: dict, champ: str, ch: str, gate: dict) -> dict:
    """Per stat: paired log-loss gain of the challenger over the champion with its t statistic.
    Passes when every stat with events shows gain > 0 and t >= the gate's minimum."""
    min_t = gate.get("logloss_gain_min_t", 2.0)
    pairs = res.get("paired") or {}
    per = {}
    for stat, p in pairs.items():
        if p.get("challenger") != ch:
            continue
        per[stat] = dict(n=p.get("n"), gain=p.get("gain"), t=p.get("t"),
                         ok=(p.get("gain") or 0) > 0 and (p.get("t") or 0) >= min_t)
    for r in res.get("runs") or []:   # nbapicks.propbacktest: paired stats live in each run's coverage
        pv = (r.get("coverage") or {}).get(f"paired_vs_{champ}")
        if r.get("model_version") != ch or not pv or pv.get("gain") is None:
            continue
        ts = [t for t in (pv.get("t"), pv.get("t_day_cluster")) if t is not None]
        t = min(ts) if ts else None          # the more conservative of naive and day-clustered t
        per[str(r.get("market", "")).replace("prop:", "")] = dict(n=pv.get("n"), gain=pv["gain"], t=t,
                                                                  ok=pv["gain"] > 0 and (t or 0) >= min_t)
    if not per:   # fall back to run-level log losses when the backtest reports no paired stats
        by = {}
        for r in res.get("runs") or []:
            by.setdefault(r.get("market"), {})[r.get("model_version")] = r
        for mkt, d in by.items():
            if champ in d and ch in d and d[ch].get("logloss_model") is not None:
                gain = d[champ]["logloss_model"] - d[ch]["logloss_model"]
                per[mkt] = dict(n=d[ch].get("eligible"), gain=gain, t=None, ok=False)
    return dict(champion=champ, challenger=ch, per_stat=per, min_t=min_t,
                passes=bool(per) and all(v["ok"] for v in per.values()))


def forward_prop_check(store, gates: dict) -> dict:
    """Demote the prop model in use when its settled live predictions miss the calibration gate."""
    d = gates["demotion"]
    rows = store.q("""SELECT p.prob, p.prob_push, p.model_version, e.result FROM predictions p
                      JOIN pred_events e ON e.pred_id = p.pred_id AND e.type = 'settled'
                      WHERE p.origin = 'model' AND p.market = 'prop' AND p.prob IS NOT NULL
                      ORDER BY e.at, p.pred_id""")   # time order: "last N" must mean the newest N
    champ = _champ()
    cur = (champ.get("props") or {}).get("model_id", "props-v0")
    # Bin-error noise: a perfectly calibrated model scores ~0.065 on 150 props in 10 bins (above the 0.06 gate), so the
    # calibration gate needs its own, larger sample (2026-11-15; the 150-prop window falsely demoted props-v1 on 2026-11-02).
    need = d.get("calibration_min_settled", d["rolling_settled"])
    rs = [r for r in rows if r["model_version"] == cur and r["result"] in ("win", "loss")][-need:]
    if len(rs) < need:
        return dict(model=cur, n=len(rs), action="none (too few settled)")
    ps = [r["prob"] / max(1e-9, 1 - (r["prob_push"] or 0)) for r in rs]
    ys = [1 if r["result"] == "win" else 0 for r in rs]
    cal = M.calibration(ps, ys, 10)
    err = sum(abs(b["predicted"] - b["observed"]) * b["n"] for b in cal) / len(rs)
    out = dict(model=cur, n=len(rs), calibration_error=err, threshold=d["calibration_error_above"], action="none")
    if err > d["calibration_error_above"] and cur != "props-v0":
        champ["props"] = dict(model_id="props-v0", since=dt.date.today().isoformat(),
                              reason=f"automatic demotion: {cur} live calibration error {err:.3f} > {d['calibration_error_above']} over {len(rs)} settled")
        json.dump(champ, open(CHAMP, "w"), indent=1)
        append(DECISIONS, dict(at=now(), by="weekly cycle (automatic)", decision=f"demote prop model {cur} -> props-v0",
                               evidence=f"calibration error {err:.3f} over last {len(rs)} settled props", review="demotion needs no vote"))
        out["action"] = "demoted to props-v0"
    return out


def promote(model: str, review: str) -> str:
    """Apply a prop-model promotion: the latest evaluation of `model` passed and a review file exists."""
    if not review or not os.path.exists(review):
        raise SystemExit(f"promotion needs an independent review file; {review!r} not found")
    last = None
    for line in open(REG):
        r = json.loads(line)
        if r.get("step") == "evaluated" and str(r.get("exp_id", "")).endswith(f"prop-{model}"):
            last = r
    if not last or last.get("decision") != "candidate":
        raise SystemExit(f"no passing evaluation of {model} in {REG}")
    champ = _champ()
    prev = (champ.get("props") or {}).get("model_id", "props-v0")
    champ["props"] = dict(model_id=model, since=dt.date.today().isoformat(), experiment=last["exp_id"],
                          reason=f"passed the props gate on validate ({last['exp_id']}); review {review}. "
                                 "Probability estimator only: prop market status is unchanged (research).")
    json.dump(champ, open(CHAMP, "w"), indent=1)
    append(DECISIONS, dict(at=now(), by="Prop research", decision=f"prop estimator {prev} -> {model} (market status unchanged)",
                           evidence=last["exp_id"], review=review))
    return f"promoted {model}"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--promote")
    ap.add_argument("--review")
    ap.add_argument("--skip-games", action="store_true")
    a = ap.parse_args(argv)
    if a.promote:
        print(promote(a.promote, a.review)); return 0
    from . import config as C
    from .pipeline import Ctx
    from .diagnose import run as diagnose
    report = dict(at=now(), commit=commit())
    ctx = Ctx(dt.datetime.now(dt.timezone.utc), C.load())
    report["diagnostics"] = diagnose(ctx)
    gates = _gates()
    report["forward_prop_check"] = forward_prop_check(ctx.store, gates)
    if not a.skip_games:
        from .research import main as research
        try:
            research(["--from-queue"])
            report["game_challengers"] = "ran queued challengers (see reports/research_latest.md)"
        except SystemExit:
            report["game_challengers"] = "queue empty"
    try:
        report["prop_challengers"] = prop_challengers()
    except Exception as e:   # record, do not hide
        report["prop_challengers"] = dict(error=f"{type(e).__name__}: {e}")
    os.makedirs("reports", exist_ok=True)
    json.dump(report, open("reports/weekly_latest.json", "w"), indent=1, default=str)
    L = [f"# Weekly cycle {report['at']} (commit {report['commit']})", ""]
    dg = report["diagnostics"]
    L.append(f"- Diagnostics: {dg.get('findings', 0)} findings, {dg.get('queued', 0)} queued, probation: {dg.get('probation') or 'none'}")
    fp = report["forward_prop_check"]
    L.append(f"- Prop model in use: {fp['model']} ({fp['n']} settled live props checked): {fp['action']}")
    L.append(f"- Game challengers: {report.get('game_challengers', 'skipped')}")
    for ch, v in (report["prop_challengers"] or {}).items():
        if isinstance(v, dict) and "per_stat" in v:
            parts = ", ".join(f"{s}: gain {x['gain']:+.4f}" + (f" (t {x['t']:.1f})" if x.get("t") is not None else "")
                              for s, x in v["per_stat"].items() if x.get("gain") is not None)
            L.append(f"- Prop challenger {ch} vs {v['champion']}: {'PASSES (candidate; needs review to promote)' if v['passes'] else 'rejected'}; {parts}")
        else:
            L.append(f"- Prop challengers: {v}")
    open("reports/weekly_latest.md", "w").write("\n".join(L) + "\n")
    print("\n".join(L))
    from .dashboard import export
    export(Ctx(dt.datetime.now(dt.timezone.utc), C.load()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
