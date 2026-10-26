"""exp-20261022-propcalib (NBA-034): compare prop calibrators fitted on explore, scored on validate.
Same synthetic-line setup as tools/splitcard_experiment.py. Pre-registered in experiments.jsonl."""
from __future__ import annotations

import json, math, statistics, sys
from collections import defaultdict

sys.path.insert(0, ".")
import tools.splitcard_experiment as E  # reuse data loading
from nbapicks import splitcard as SC
import datetime as dt, statistics as st


def events():
    games = {g["game_id"]: g for g in E.rd("data/history/games_2023.csv.gz") if g["season_type"] == "regular"}
    idx = SC.build_index(E.rd("data/history/box_2023.csv.gz"), games)
    ev = []
    for pid, gs in idx.logs.items():
        for i in range(10, len(gs)):
            g = gs[i]
            ms = SC.mates_in_last_game(idx, g.team, SC.key_teammates(idx, pid, g.team, g.date), g.date)
            for s in SC.STATS:
                line = math.floor(st.median(x.stats[s] for x in gs[i - 10:i])) + 0.5
                c = SC.split_counts(idx, pid, s, line, "over", g.date, g.opp, g.home, ms, g.team)
                p = SC.combine(c, 40.0)
                if p is None:
                    continue
                ev.append(dict(val=g.date >= E.CUT, y=int(g.stats[s] > line), raw=p))
    return ev


def ll1(p, y):
    p = min(max(p, 1e-6), 1 - 1e-6)
    return -math.log(p if y else 1 - p)


def main():
    ev = events()
    exp = [r for r in ev if not r["val"]]; val = [r for r in ev if r["val"]]
    steps = SC.fit_isotonic([r["raw"] for r in exp], [r["y"] for r in exp], bins=20)
    f = {"identity": lambda p: p, "platt": SC.calibrate, "platt_tailcap": SC.calibrate_tailcap,
         "isotonic": lambda p: SC.apply_isotonic(p, steps)}
    out = {"n_explore": len(exp), "n_validate": len(val), "isotonic_steps": len(steps)}
    tails = [r for r in val if r["raw"] < 0.2 or r["raw"] > 0.8]
    out["n_validate_tail"] = len(tails)
    for name, fn in f.items():
        d = [ll1(fn(r["raw"]), r["y"]) - ll1(SC.calibrate(r["raw"]), r["y"]) for r in val]
        m = statistics.mean(d); se = statistics.stdev(d) / math.sqrt(len(d)) if any(d) else 0
        dec = defaultdict(list)
        for r in tails:
            dec[min(int(r["raw"] * 10), 9)].append(r)
        tail_err = statistics.mean(abs(statistics.mean(fn(r["raw"]) for r in v) - statistics.mean(r["y"] for r in v))
                                   for v in dec.values()) if dec else None
        out[name] = dict(validate_ll=round(statistics.mean(ll1(fn(r["raw"]), r["y"]) for r in val), 5),
                         gain_vs_platt=round(-m, 6), t=round(-m / se, 2) if se else None,
                         tail_mean_abs_err=round(tail_err, 4) if tail_err is not None else None,
                         tail_decile_n={str(k): len(v) for k, v in sorted(dec.items())})
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
