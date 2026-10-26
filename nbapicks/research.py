"""Experiment runner and registry: pre-registered hypotheses, walk-forward results,
gate evaluation and an explicit decision record.

Every experiment row in data/research/experiments.jsonl is written in two steps:
'registered' (hypothesis, variant, baseline, criteria; before any result) and
'evaluated' (metrics and the gate outcome). Rows are append-only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import subprocess
from collections import defaultdict

import yaml

from . import metrics as M
from .backtest import run, SPLITS
from .models.ratings import RatingsParams

REG = "data/research/experiments.jsonl"


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def commit() -> str:
    """HEAD, marked '-dirty' when the code or config that produce results has uncommitted edits."""
    try:
        head = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
        dirty = subprocess.check_output(["git", "status", "--porcelain", "--", "nbapicks", "config"], text=True).strip()
        return head + ("-dirty" if dirty else "")
    except Exception:
        return "unknown"


GRID = [i / 20 for i in range(0, 21)]


def _one(recs):
    return [r for r in recs if r["selection"] in ("home", "over") and r["result"] in ("win", "loss")]


def paired_gain(recs: list[dict], w: float) -> dict:
    """Per-game log-loss difference market - blend (positive = blend better), with its t statistic.
    With w = 0 the blend is the market: the gain is exactly zero and t is undefined (None)."""
    if w == 0:
        return dict(n=len(_one(recs)), gain=0.0, t=None)
    diffs = []
    for r in _one(recs):
        y = r["result"] == "win"
        pb = _blend(r["prob"] / max(1e-9, 1 - r["push"]), r["fair"], w)
        ll = lambda p: -math.log(max(1e-12, p if y else 1 - p))
        diffs.append(ll(r["fair"]) - ll(pb))
    n = len(diffs)
    if n < 2:
        return dict(n=n, gain=None, t=None)
    m = sum(diffs) / n
    sd = math.sqrt(sum((d - m) ** 2 for d in diffs) / (n - 1))
    return dict(n=n, gain=m, t=(m / (sd / math.sqrt(n))) if sd > 0 else 0.0)


def explore_oof(recs: list[dict]) -> dict:
    """Leave-one-season-out on explore: w is fit on the other seasons and scored on the held
    one, so an uninformative model cannot show a positive gain just by fitting w in-sample."""
    seasons = sorted({r["season"] for r in recs})
    pooled = []
    for s in seasons:
        w, _ = blend_fit([r for r in recs if r["season"] != s])
        pooled += [(r, w) for r in recs if r["season"] == s]
    diffs = []
    for r, w in pooled:
        if r["selection"] in ("home", "over") and r["result"] in ("win", "loss"):
            y = r["result"] == "win"
            pb = _blend(r["prob"] / max(1e-9, 1 - r["push"]), r["fair"], w)
            ll = lambda p: -math.log(max(1e-12, p if y else 1 - p))
            diffs.append(ll(r["fair"]) - ll(pb))
    n = len(diffs)
    if n < 2:
        return dict(n=n, gain=None, t=None)
    m = sum(diffs) / n
    sd = math.sqrt(sum((d - m) ** 2 for d in diffs) / (n - 1))
    return dict(n=n, gain=m, t=(m / (sd / math.sqrt(n))) if sd > 0 else 0.0)


def choose_threshold(recs, w, thresholds, min_bets):
    """Best explore ROI among thresholds with at least min_bets bets (None if none qualify)."""
    best = None
    for t in thresholds:
        b = bet_stats(recs, w, t)
        if b["n"] < min_bets or b["roi"] is None:
            continue
        if best is None or (b["roi"], -t) > best[0]:
            best = ((b["roi"], -t), t)
    return best[1] if best else None


def choose_threshold_rows(recs, thresholds, min_bets, stats_fn):
    """Generic version of choose_threshold for strategies that score rows directly."""
    best = None
    for t in thresholds:
        b = stats_fn(recs, t)
        if b["n"] < min_bets or b.get("roi") is None:
            continue
        if best is None or (b["roi"], -t) > best[0]:
            best = ((b["roi"], -t), t)
    return best[1] if best else None


def bets_at(bets: dict, thr) -> dict:
    """Look a threshold up by value, not by its string spelling ('0.03' == '0.030')."""
    for k, v in bets.items():
        if abs(float(k) - float(thr)) < 1e-9:
            return v
    raise KeyError(f"threshold {thr} was not evaluated; have {sorted(bets)}")


def append(path: str, rec: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a") as fh:
        fh.write(json.dumps(rec, sort_keys=True, default=str) + "\n")


def blend_fit(recs: list[dict], grid=None) -> tuple[float, dict]:
    """Choose the model weight w in logit-space blending that minimises log loss
    (one side per game) on the given records. Returns (w, {w: logloss})."""
    grid = grid or GRID
    one = [r for r in recs if r["selection"] in ("home", "over") and r["result"] in ("win", "loss")]
    ys = [1 if r["result"] == "win" else 0 for r in one]
    out = {}
    for w in grid:
        ps = [_blend(r["prob"] / max(1e-9, 1 - r["push"]), r["fair"], w) for r in one]
        out[w] = M.log_loss(ps, ys)
    best = min(out, key=out.get)
    return best, out


def _blend(p, f, w):
    e = 1e-6
    z = w * math.log(max(p, e) / max(1 - p, e)) + (1 - w) * math.log(max(f, e) / max(1 - f, e))
    return 1 / (1 + math.exp(-z))


def bet_stats(recs, w, thr):
    """Flat 1u at the recorded price on every side whose blended EV >= thr."""
    from .odds import ev_with_push
    nets, wins, losses = [], 0, 0
    for r in recs:
        if r["result"] == "pending":
            continue
        p = _blend(r["prob"] / max(1e-9, 1 - r["push"]), r["fair"], w) * (1 - r["push"])
        if ev_with_push(p, r["push"], r["price"]) >= thr:
            nets.append(r["net"]); wins += r["result"] == "win"; losses += r["result"] == "loss"
    s = M.roi_summary(nets, n_boot=500); s.update(M.drawdown(nets))
    s.update(wins=wins, losses=losses, win_rate=wins / (wins + losses) if wins + losses else None)
    return s


def evaluate(recs, w, thresholds):
    one = [r for r in recs if r["selection"] in ("home", "over") and r["result"] in ("win", "loss")]
    ys = [1 if r["result"] == "win" else 0 for r in one]
    if not one:
        return {}
    pm = [r["prob"] / max(1e-9, 1 - r["push"]) for r in one]
    pb = [_blend(p, r["fair"], w) for p, r in zip(pm, one)]
    pf = [r["fair"] for r in one]
    ll_m, ll_b, ll_f = M.log_loss(pm, ys), M.log_loss(pb, ys), M.log_loss(pf, ys)
    return dict(n_games=len(one), logloss_model=ll_m, logloss_blend=ll_b, logloss_market=ll_f,
                gain_blend_vs_market=ll_f - ll_b, brier_blend=M.brier(pb, ys), brier_market=M.brier(pf, ys),
                calibration_blend=M.calibration(pb, ys, 10),
                bets={str(t): bet_stats(recs, w, t) for t in thresholds})


VARIANTS = {
    "base": (RatingsParams(), "Baseline: 60-day half-life ridge ratings, fixed sigmas."),
    "trend": (RatingsParams(total_trend=True), "A linear scoring trend in the points model removes the low bias of totals (league scoring rises within and across seasons)."),
    "rest": (RatingsParams(total_trend=True, rest_features=True), "Back-to-back indicators add information the ratings miss."),
    "hl30": (RatingsParams(total_trend=True, half_life_days=30), "Faster decay (30-day half-life) tracks form better."),
    "hl120": (RatingsParams(total_trend=True, half_life_days=120), "Slower decay (120-day half-life) reduces noise."),
    "avail": (RatingsParams(total_trend=True, availability=True),
              "Missing regulars (>= 20 mpg over the team's last 10 games) move the margin and total beyond what "
              "time-weighted team ratings already carry: the value of absent players (recency-weighted box game "
              "score, models/availability.py) with coefficients fitted on prior games only improves log loss "
              "over 'trend'. Caveat: in backtests absence is read from the game's box score (includes late "
              "scratches), live from the pregame injury report, so backtest gains are an upper bound. Box "
              "scores exist only for seasons with box files (2023-2026 at registration); elsewhere the "
              "feature is 0 and the variant equals 'trend'."),
}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--variants", default=",".join(VARIANTS))
    ap.add_argument("--hist", default="data/history")
    ap.add_argument("--holdout", action="store_true", help="score the frozen candidate on the holdout, once")
    ap.add_argument("--candidate", default=None, help="variant:market:w:thr for --holdout")
    ap.add_argument("--from-queue", action="store_true", help="run the challengers listed in data/research/queue.yaml")
    a = ap.parse_args(argv)
    gates = yaml.safe_load(open("config/gates.yaml"))
    thresholds = [0.0, 0.02, 0.03, 0.05, 0.08]
    os.makedirs("reports", exist_ok=True)
    if a.holdout:
        return holdout(a, gates, thresholds)
    names = a.variants.split(",")
    if a.from_queue:
        q = (yaml.safe_load(open("data/research/queue.yaml")) or {}).get("queue", []) if os.path.exists("data/research/queue.yaml") else []
        names = [x["variant"] for x in q if x["variant"] in VARIANTS][:3]
        if not names:
            print("queue empty or no runnable challengers"); return
    summary, coverages = {}, {}
    for name in names:
        params, hyp = VARIANTS[name]
        exp_id = f"exp-{dt.date.today():%Y%m%d}-{name}"
        append(REG, dict(exp_id=exp_id, step="registered", at=now(), commit=commit(), hypothesis=hyp,
                         variant=name, params=params.to_dict(), baseline="de-vigged closing line (market) and 'base'",
                         metrics=["logloss vs market (one side per game)", "flat-1u ROI at close", "calibration"],
                         criteria=gates["paper"], splits=["explore", "validate"]))
        res = run(a.hist, {name: params}, ["explore", "validate"], thresholds)
        write_line_quality(res["line_quality"])
        coverage = res.get("coverage") or {}
        by = defaultdict(list)
        for r in res["bets"]:
            if r["kind"] == "close":
                by[(r["split"], r["market"])].append(r)
        out = {}
        for market in ("ml", "spread", "total"):
            ex, va = by.get(("explore", market), []), by.get(("validate", market), [])
            g = gates["paper"]
            w, grid = blend_fit(ex)
            thr_choice = choose_threshold(ex, w, thresholds, g["explore_min_bets_for_threshold"]) if ex else None
            e_ex, e_va = evaluate(ex, w, thresholds), evaluate(va, w, thresholds)
            oof, pv = explore_oof(ex), paired_gain(va, w)
            vb = bets_at(e_va["bets"], thr_choice) if thr_choice is not None and e_va.get("bets") else {}
            checks = {
                "explore_oof_logloss_gain": (oof["gain"] or -1) > g["explore_logloss_gain_vs_market"]
                                            and (oof["t"] or 0) >= g["logloss_gain_min_t"],
                "validate_logloss_gain": (pv["gain"] or -1) > g["validate_logloss_gain_vs_market"]
                                         and (pv["t"] or 0) >= g["logloss_gain_min_t"],
                "threshold_chosen": thr_choice is not None,
                "validate_roi": ((vb.get("roi") if vb.get("roi") is not None else -1) > g["validate_roi_at_threshold"]),
                "validate_min_bets": (vb.get("n", 0) >= g["validate_min_bets"]),
            }
            out[market] = dict(blend_w=w, threshold=thr_choice, explore=e_ex, validate=e_va, explore_oof=oof,
                               validate_paired=pv, checks=checks, passes_paper_gate=all(checks.values()),
                               configs_searched=len(GRID) * len(thresholds))
        append(REG, dict(exp_id=exp_id, step="evaluated", at=now(), commit=commit(), results=out, coverage=coverage,
                         decision={m: ("candidate_for_paper" if out[m]["passes_paper_gate"] else "rejected") for m in out},
                         reviewer="pending-independent-review"))
        summary[name] = out
        if coverage.get("availability"):
            coverages[name] = coverage
    json.dump(summary, open("reports/research_latest.json", "w"), indent=1, default=str)
    write_report(summary, gates, coverages)


def holdout(a, gates, thresholds):
    name, market, w, thr = a.candidate.split(":")
    params, hyp = VARIANTS[name]
    res = run(a.hist, {name: params}, ["holdout"], thresholds)
    recs = [r for r in res["bets"] if r["kind"] == "close" and r["market"] == market]
    opens = [r for r in res["bets"] if r["kind"] == "open" and r["market"] == market]
    n_variants = configs_tried()
    e = evaluate(recs, float(w), thresholds); eo = evaluate(opens, float(w), thresholds)
    b = bets_at(e["bets"], thr)
    floor = M.noise_floor(n_variants)
    g = gates["live"]
    checks = {"holdout_roi": (b["roi"] or -1) > g["holdout_roi_at_threshold"],
              "holdout_t": (b["t"] or 0) >= floor, "holdout_min_bets": b["n"] >= g["holdout_min_bets"]}
    rec = dict(exp_id=f"holdout-{dt.date.today():%Y%m%d}-{name}-{market}", step="holdout", at=now(), commit=commit(),
               candidate=a.candidate, n_variants_tried=n_variants, noise_floor=floor, close=e, open=eo, checks=checks,
               passes_holdout=all(checks.values()))
    append(REG, rec)
    print(json.dumps(rec, indent=1, default=str)[:4000])


RAW_MODEL_CONFIGS = 12   # reports/backtest_raw_model.md: 3 markets x 4 thresholds, run before the registry


def configs_tried() -> int:
    """Every (variant, market, weight, threshold) combination ever evaluated: the N in the
    holdout noise floor sqrt(2 ln N). Rows written before configs_searched was recorded
    are counted at the full grid (21 weights x 5 thresholds per market)."""
    n = RAW_MODEL_CONFIGS
    for line in open(REG):
        rec = json.loads(line)
        if rec.get("step") == "evaluated":
            n += sum(m.get("configs_searched", 105) for m in rec["results"].values())
    return n


def write_line_quality(lq: dict) -> None:
    by = defaultdict(lambda: defaultdict(int))
    for k, v in lq.items():
        season, kind, why = k.split("|")
        by[(int(season), kind)][why] += v
    whys = sorted({w for d in by.values() for w in d})
    L = ["# History line quality", "", "Quotes dropped before any model is scored (rules in `nbapicks/backtest.py`, `clean_quotes`). "
         "Counts are book-level quotes, per season (ESPN year) and quote kind.", "",
         "| season | kind | " + " | ".join(whys) + " |", "|---|---|" + "---|" * len(whys)]
    for (season, kind), d in sorted(by.items()):
        L.append(f"| {season} | {kind} | " + " | ".join(str(d.get(w, 0)) for w in whys) + " |")
    open("reports/line_quality.md", "w").write("\n".join(L) + "\n")


def write_report(summary, gates, coverages=None):
    L = ["# Model research: walk-forward results", "",
         f"Generated {now()} at commit `{commit()}`. Splits (ESPN season years): explore {gates['splits']['explore']}, "
         f"validate {gates['splits']['validate']}; holdout {gates['splits']['holdout']} untouched.", "",
         "Each variant is refit every game day on games before that day and priced against one sportsbook's "
         "closing line (DraftKings where ESPN has it, else the next book in a fixed priority list). "
         "'Blend' mixes model and de-vigged market in logit space with a weight chosen on explore only. "
         "Log-loss gain is market minus blend (positive = blend better). ROI is flat 1 unit at the closing price.", "",
         "Explore gain is scored leave-one-season-out (w fit on the other explore seasons); validate gain uses the explore w. "
         "Each gain is the mean per-game log-loss improvement over the de-vigged close with its paired t statistic; the gate needs t >= "
         f"{gates['paper']['logloss_gain_min_t']}. The EV threshold is the best explore ROI among thresholds with at least "
         f"{gates['paper']['explore_min_bets_for_threshold']} explore bets.", "",
         "| variant | market | w | thr | explore gain (t) | validate gain (t) | validate bets | validate win % | validate ROI | 95% CI | paper gate |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    notes = []
    for v, c in (coverages or {}).items():
        notes.append(f"'{v}': {c.get('availability_note', '')} Seasons without box scores (feature = 0): "
                     f"{c.get('seasons_without_box') or 'none'}.")
    for v, out in summary.items():
        for m, r in out.items():
            vb = bets_at(r["validate"]["bets"], r["threshold"]) if r["threshold"] is not None and r["validate"].get("bets") else {}
            ci = vb.get("roi_ci")
            eo, vp = r["explore_oof"], r["validate_paired"]
            L.append(f"| {v} | {m} | {r['blend_w']:.2f} | {'none' if r['threshold'] is None else r['threshold']} | {_g(eo)} | {_g(vp, r['blend_w'])} | "
                     f"{vb.get('n', 0)} | {_wr(r, vb)} | {_pct(vb.get('roi'))} | "
                     f"{'' if not ci else f'{ci[0]*100:+.1f}% to {ci[1]*100:+.1f}%'} | {'PASS' if r['passes_paper_gate'] else 'fail'} |")
    L += ["", "A weight of 0.00 means the model added nothing over the closing price on explore: the blend is the market itself, "
          "and any ROI is the bookmaker margin.", ""] + [f"- {n}" for n in notes] + ([""] if notes else [])
    open("reports/research_latest.md", "w").write("\n".join(L) + "\n")


def _g(d, w=None):
    if w == 0:
        return "0 (w = 0)"
    return "" if d.get("gain") is None else f"{d['gain']:+.4f} ({d['t']:+.1f})"


def _pct(x):
    return "" if x is None else f"{x*100:+.1f}%"


def _wr(r, vb):
    return "" if vb.get("win_rate") is None else f"{vb['win_rate']*100:.1f}% ({vb['wins']}-{vb['losses']})"


if __name__ == "__main__":
    main()
