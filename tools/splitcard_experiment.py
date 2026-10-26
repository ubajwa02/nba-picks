"""exp-20261021-splitcard: calibration of split-card P(over) on synthetic lines (within 2023).
Pre-registered in data/research/experiments.jsonl. Prints a JSON summary."""
from __future__ import annotations

import csv, datetime as dt, gzip, json, math, statistics, sys
from collections import defaultdict

sys.path.insert(0, ".")
from nbapicks import splitcard as SC

CUT = dt.date(2023, 1, 15)
KS = (10.0, 20.0, 40.0)
TH = 0.58


def rd(p):
    with gzip.open(p, "rt") as f:
        return list(csv.DictReader(f))


def main():
    games = {g["game_id"]: g for g in rd("data/history/games_2023.csv.gz") if g["season_type"] == "regular"}
    idx = SC.build_index(rd("data/history/box_2023.csv.gz"), games)
    ev = []
    for pid, gs in idx.logs.items():
        for i in range(10, len(gs)):
            g = gs[i]
            mates = SC.key_teammates(idx, pid, g.team, g.date)
            ms = SC.mates_in_last_game(idx, g.team, mates, g.date)
            for st in SC.STATS:
                line = math.floor(statistics.median(x.stats[st] for x in gs[i - 10:i])) + 0.5
                c = SC.split_counts(idx, pid, st, line, "over", g.date, g.opp, g.home, ms, g.team)
                y = int(g.stats[st] > line)
                h10, n10 = c["last10"]; hs, ns = c.get("season", (0, 0))
                row = dict(split="explore" if g.date < CUT else "validate", y=y, cl=(pid, g.date.isoformat()),
                           l10=(h10 + 1) / (n10 + 2), sea=(hs + 1) / (ns + 2))
                for k in KS:
                    row[k] = SC.combine(c, k)
                ev.append(row)
    def brier(rs, f): return sum((r[f] - r["y"]) ** 2 for r in rs) / len(rs)
    def ll(rs, f): return -sum(math.log(min(max(r[f] if r["y"] else 1 - r[f], 1e-6), 1)) for r in rs) / len(rs)
    def flagged(rs, f):
        hits = defaultdict(list)
        for r in rs:
            if r[f] >= TH: hits[r["cl"]].append(r["y"])
            elif r[f] <= 1 - TH: hits[r["cl"]].append(1 - r["y"])
        xs = [v for vs in hits.values() for v in vs]
        n = len(xs); p = sum(xs) / n if n else float("nan")
        t_naive = (p - 0.524) / math.sqrt(p * (1 - p) / n) if n else None
        # cluster-robust (player-day) variance of the mean
        resid = [sum(v - p for v in vs) for vs in hits.values()]
        var = sum(e * e for e in resid) / n ** 2
        t_cl = (p - 0.524) / math.sqrt(var) if var else None
        return dict(n=n, clusters=len(hits), hit=round(p, 4), t_naive=round(t_naive, 2), t_cluster=round(t_cl, 2))
    def calib(rs, f):
        b = defaultdict(list)
        for r in rs: b[min(int(r[f] * 10), 9)].append(r)
        return {f"{d/10:.1f}": dict(n=len(v), pred=round(sum(r[f] for r in v) / len(v), 3), obs=round(sum(r["y"] for r in v) / len(v), 3)) for d, v in sorted(b.items())}
    out = {"events": len(ev)}
    exp = [r for r in ev if r["split"] == "explore"]; val = [r for r in ev if r["split"] == "validate"]
    out["explore_k_brier"] = {str(k): round(brier(exp, k), 5) for k in KS}
    kbest = min(KS, key=lambda k: brier(exp, k)); out["k_chosen"] = kbest
    for name, rs in (("explore", exp), ("validate", val)):
        out[name] = dict(n=len(rs), base_rate=round(sum(r["y"] for r in rs) / len(rs), 4),
                         **{f: dict(brier=round(brier(rs, f), 5), logloss=round(ll(rs, f), 5)) for f in ("l10", "sea", kbest)}.items() and {str(f): dict(brier=round(brier(rs, f), 5), logloss=round(ll(rs, f), 5)) for f in ("l10", "sea", kbest)},
                         flagged=flagged(rs, kbest), flagged_l10=flagged(rs, "l10"))
        # paired t on per-event Brier difference vs each baseline (naive; ignores clustering)
        for b in ("l10", "sea"):
            d = [(r[kbest] - r["y"]) ** 2 - (r[b] - r["y"]) ** 2 for r in rs]
            out[name][f"brier_diff_t_vs_{b}"] = round(statistics.mean(d) / (statistics.stdev(d) / math.sqrt(len(d))), 2)
    # diagnostic (post-hoc, not a new config): flagged hit rate by side; the x.5-above-median
    # synthetic line makes 'over' the minority outcome, so unders win by construction
    for name, rs in (("explore", exp), ("validate", val)):
        o = [r["y"] for r in rs if r[kbest] >= TH]; u = [1 - r["y"] for r in rs if r[kbest] <= 1 - TH]
        out[name]["flagged_by_side"] = dict(over=dict(n=len(o), hit=round(sum(o) / max(len(o), 1), 4)),
                                            under=dict(n=len(u), hit=round(sum(u) / max(len(u), 1), 4)))
    # Platt fit on EXPLORE only (review 2026-10-21): p_cal = sigmoid(a + b*logit(p)); applied to validate
    import numpy as np
    z = np.array([SC._logit(r[kbest]) for r in exp]); y = np.array([r["y"] for r in exp], float)
    a, b = 0.0, 1.0
    for _ in range(50):
        q = 1 / (1 + np.exp(-(a + b * z))); w = q * (1 - q)
        g = np.array([(q - y).sum(), ((q - y) * z).sum()])
        H = np.array([[w.sum(), (w * z).sum()], [(w * z).sum(), (w * z * z).sum()]])
        a, b = np.array([a, b]) - np.linalg.solve(H, g)
    out["platt_explore"] = dict(a=round(float(a), 4), b=round(float(b), 4))
    for r in val:
        r["cal"] = 1 / (1 + math.exp(-(a + b * SC._logit(r[kbest]))))
    out["validate"]["calibrated"] = dict(brier=round(brier(val, "cal"), 5), logloss=round(ll(val, "cal"), 5),
                                         calibration=calib(val, "cal"))
    out["validate"]["calibration"] = calib(val, kbest)
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
