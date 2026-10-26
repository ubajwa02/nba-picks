"""Does the pace proxy help props-v1? Scored on the VALIDATE window only (2025-10-01..2026-01-31).

    python tools/pace_experiment.py [pace_k ...]

Per stat: mean squared error of the projected mean, and the paired difference in negative-binomial
log-likelihood of the actual count against pace off, with its t statistic. The holdout is never
touched (propbacktest refuses it). Nothing here changes the champion; a result only decides
whether a challenger is worth registering."""
import datetime as dt
import math
import sys

import numpy as np

sys.path.insert(0, ".")
from nbapicks import propbacktest as PB
from nbapicks.models import props_v1 as V1

START, END = dt.date(2025, 10, 1), dt.date(2026, 1, 31)


def nb_logpmf(y, mean, r):
    return (math.lgamma(y + r) - math.lgamma(r) - math.lgamma(y + 1)
            + r * math.log(r / (r + mean)) + y * math.log(mean / (r + mean)))


def main(ks):
    hist = PB.load_history(refresh=True)
    base = V1.PropModelV1(hist["rows"], hist["games"])
    events, cov = PB.build_events(base, hist, START, END, sample=2)
    print(f"{len(events)} validate events (1-in-2 hash subsample)")
    res = {}
    for k in [None] + ks:
        m = V1.PropModelV1(hist["rows"], hist["games"], params={"pace_k": k})
        for s in V1.STATS:
            ll, se = [], []
            for ev in events:
                p = m.predict(ev["pid"], s, ev["date"], ev["opp"], ev["home"], teammates_out=ev["mates_out"])
                if p is None:
                    ll.append(math.nan); se.append(math.nan); continue
                ll.append(nb_logpmf(ev["y"][s], p["mean"], m.dispersion[s])); se.append((ev["y"][s] - p["mean"]) ** 2)
            res[(k, s)] = (np.array(ll), np.array(se))
    for s in V1.STATS:
        l0, e0 = res[(None, s)]
        for k in ks:
            l1, e1 = res[(k, s)]
            ok = ~np.isnan(l0) & ~np.isnan(l1)
            d = l1[ok] - l0[ok]
            t = d.mean() / (d.std(ddof=1) / math.sqrt(len(d)))
            print(f"{s:5s} pace_k={k:<4} n={ok.sum()} mse {np.nanmean(e0[ok]):.4f} -> {np.nanmean(e1[ok]):.4f}  "
                  f"loglik gain/event {d.mean():+.5f} (t={t:+.2f})")


if __name__ == "__main__":
    main([float(x) for x in sys.argv[1:]] or [10.0, 30.0])
