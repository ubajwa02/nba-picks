"""Line shopping, cleaned re-spec (the "Path forward" written by the independent review of
exp-20261020-lineshop, team/reviews/2026-10-20-lineshop-skeptic.md, before any result of it existed).

Moneylines only, explore and validate seasons only. The holdout is never loaded.

    python -m tools.lineshop_respec --register     # write the spec to the registry (before any run)
    python -m tools.lineshop_respec                # run and record

Rules, numbered as in the review:
 1 drop non-books (betegy, Betradar, Fantasy911.com)
 2 one family per operator: same first word, plus any two books whose ML pairs are identical in >= 70%
   of the games they share that season
 3 drop any ML pair with overround under 1.5%
 4 the bet book's ML-implied spread is within 1.5 points of its own spread, and its own spread is within
   1 point of the median spread of the other families
 5 no bet when a sibling feed of the same family in that game prices the side >= 2% worse
 6 at most one side per game (the higher EV)
 7 "bet only at a FanDuel-like book" (BetfairSportsbook) is reported separately from "best of all books"
 8 the validate t must reach the registry-wide noise floor sqrt(2 ln N)
"""
from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from statistics import NormalDist, median

from nbapicks import metrics as M
from nbapicks import odds as O
from nbapicks.backtest import SIGMA_LINK, SPLITS, clean_quotes, load, split_of
from nbapicks.settle import GameResult, net_profit, settle_leg
from nbapicks.strategies.line_shop import family as name_family

EXP = "exp-20261117-lineshop-respec"
NON_BOOKS = {"betegy", "betradar", "fantasy911.com"}
FD_LIKE = "BetfairSportsbook"
THRESHOLDS = [0.0, 0.01, 0.02, 0.03, 0.05]
MIN_OVERROUND, ML_SPREAD_GAP, SPREAD_CONSENSUS_GAP, SIBLING_WORSE, SAME_SHARE = 0.015, 1.5, 1.0, 0.02, 0.70
MIN_FAMILIES = 3
ND = NormalDist()


def families(season_games: list[dict]) -> dict[str, str]:
    """book -> family for one season (rule 2)."""
    same, shared = defaultdict(int), defaultdict(int)
    books = set()
    for clean in season_games:
        ml = {b: (q["ml"]["home"][1], q["ml"]["away"][1]) for b, q in clean.items() if "ml" in q}
        books |= set(ml)
        bs = sorted(ml)
        for i, a in enumerate(bs):
            for b in bs[i + 1:]:
                shared[(a, b)] += 1
                same[(a, b)] += ml[a] == ml[b]
    parent = {b: b for b in books}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    byname = defaultdict(list)
    for b in books:
        byname[name_family(b)].append(b)
    for bs in byname.values():
        for b in bs[1:]:
            parent[find(b)] = find(bs[0])
    for (a, b), n in shared.items():
        if n >= 50 and same[(a, b)] / n >= SAME_SHARE:
            parent[find(a)] = find(b)
    return {b: find(b) for b in books}


def bets(games, lines, splits=("explore", "validate")) -> list[dict]:
    target = {s for k in splits for s in SPLITS[k]}
    assert not target & set(SPLITS["holdout"]), "holdout seasons must not be loaded"
    by_season = defaultdict(list)
    for g in games:
        if g.season in target and lines.get(g.game_id):
            books = {b: r for b, r in lines[g.game_id].items() if b.lower() not in NON_BOOKS}      # rule 1
            clean, _ = clean_quotes(books, "close")
            by_season[g.season].append((g, clean))
    out = []
    for season, rows in by_season.items():
        fam = families([c for _, c in rows])
        for g, clean in rows:
            res = GameResult("final", g.home_score, g.away_score)
            q = {}
            for b, qs in clean.items():
                if "ml" not in qs:
                    continue
                h, a = qs["ml"]["home"][1], qs["ml"]["away"][1]
                if 1 / h + 1 / a - 1 < MIN_OVERROUND:                                               # rule 3
                    continue
                q[b] = dict(h=h, a=a, fair=O.devig_power([h, a])[0], spread=(qs.get("spread") or {}).get("home", [None])[0])
            fam_fair, fam_spread = defaultdict(list), defaultdict(list)
            for b, x in q.items():
                fam_fair[fam[b]].append(x["fair"])
                if x["spread"] is not None:
                    fam_spread[fam[b]].append(x["spread"])
            if len(fam_fair) < MIN_FAMILIES:
                continue
            cands = []
            for b, x in q.items():
                others = [median(v) for k, v in fam_fair.items() if k != fam[b]]
                osp = [median(v) for k, v in fam_spread.items() if k != fam[b]]
                if len(others) < MIN_FAMILIES - 1 or x["spread"] is None or not osp:
                    continue
                p = min(max(x["fair"], 1e-4), 1 - 1e-4)
                if abs(-SIGMA_LINK * ND.inv_cdf(p) - x["spread"]) > ML_SPREAD_GAP or abs(x["spread"] - median(osp)) > SPREAD_CONSENSUS_GAP:
                    continue                                                                        # rule 4
                p0 = median(others)
                for side, fair, price, key in (("home", p0, x["h"], "h"), ("away", 1 - p0, x["a"], "a")):
                    sib = [q[s][key] for s in q if s != b and fam[s] == fam[b]]
                    if any(price / s - 1 >= SIBLING_WORSE for s in sib):                            # rule 5
                        continue
                    r = settle_leg("ml", side, None, res)
                    cands.append(dict(game_id=g.game_id, season=season, split=split_of(season), book=b, selection=side, price=price,
                                      fair=fair, ev=fair * price - 1, result=r, net=net_profit(r, price, 1.0)))
            for name, pool in (("all", cands), ("fd_like", [c for c in cands if c["book"] == FD_LIKE])):
                if pool:
                    out.append(dict(max(pool, key=lambda c: c["ev"]), scope=name))                  # rule 6
    return out


def stats(recs, thr):
    chosen = [r for r in recs if r["ev"] >= thr and r["result"] in ("win", "loss")]
    s = M.roi_summary([r["net"] for r in chosen], n_boot=500)
    s["mean_ev"] = sum(r["ev"] for r in chosen) / len(chosen) if chosen else None
    return s


def main(argv=None):
    from nbapicks.research import REG, append, commit, now
    import yaml
    ap = argparse.ArgumentParser(); ap.add_argument("--register", action="store_true"); a = ap.parse_args(argv)
    gates = yaml.safe_load(open("config/gates.yaml"))["paper"]
    reg = [json.loads(x) for x in open(REG) if x.strip()]
    n_tests = len({r.get("exp_id") for r in reg if r.get("exp_id")} | {EXP})
    floor = max(2.0, math.sqrt(2 * math.log(n_tests)))
    crit = dict(threshold_rule=f"best explore ROI among {THRESHOLDS} with >= {gates['explore_min_bets_for_threshold']} explore bets (scope all)",
                validate_roi=0.0, validate_min_bets=gates["validate_min_bets"], validate_t_min=round(floor, 2),
                fd_like="validate only (no BetfairSportsbook quotes in explore), at the threshold chosen for scope all; same three validate checks")
    if a.register:
        append(REG, dict(exp_id=EXP, step="registered", at=now(), commit=commit(), variant="lineshop-respec",
                         hypothesis="After the review's eight cleaning rules, a moneyline priced above the leave-one-out consensus still wins more "
                                    "than its price implies, at any book and at a FanDuel-like book.",
                         spec=__doc__, baseline="zero (break-even)", criteria=crit, splits=["explore", "validate"], holdout_touched=False,
                         registry_tests=n_tests))
        print("registered", EXP, crit); return
    assert any(r.get("exp_id") == EXP and r.get("step") == "registered" for r in reg), "register first"
    games, lines = load("data/history", seasons=sorted(set(SPLITS["explore"]) | set(SPLITS["validate"])))
    recs = bets(games, lines)
    ex = [r for r in recs if r["scope"] == "all" and r["split"] == "explore"]
    ok = [t for t in THRESHOLDS if stats(ex, t)["n"] >= gates["explore_min_bets_for_threshold"]]
    thr = max(ok, key=lambda t: stats(ex, t)["roi"]) if ok else None
    out = dict(threshold=thr, noise_floor_t=round(floor, 2))
    for scope in ("all", "fd_like"):
        for split in ("explore", "validate"):
            rs = [r for r in recs if r["scope"] == scope and r["split"] == split]
            out[f"{scope}:{split}"] = {str(t): stats(rs, t) for t in THRESHOLDS}
        v = out[f"{scope}:validate"].get(str(thr), {}) if thr is not None else {}
        out[f"{scope}:checks"] = dict(threshold_chosen=thr is not None, validate_roi=(v.get("roi") or -1) > 0,
                                      validate_min_bets=v.get("n", 0) >= gates["validate_min_bets"], validate_t=(v.get("t") or 0) >= floor)
        out[f"{scope}:passes"] = all(out[f"{scope}:checks"].values())
    append(REG, dict(exp_id=EXP, step="evaluated", at=now(), commit=commit(), results=out, holdout_touched=False,
                     decision={s: ("candidate_for_paper" if out[f"{s}:passes"] else "rejected") for s in ("all", "fd_like")}))
    L = ["# Line shopping, cleaned re-spec (moneylines)", "",
         f"`python -m tools.lineshop_respec`. Explore 2015-2020 and validate 2021-2023 only; holdout not loaded. Threshold chosen on explore: "
         f"{'none' if thr is None else format(thr, '.0%')}. Validate t must reach {floor:.2f} (noise floor over {n_tests} registry experiments).", "",
         "| scope | split | EV threshold | bets | ROI | 95% CI | t | mean EV |", "|---|---|---|---|---|---|---|---|"]
    for scope in ("all", "fd_like"):
        for split in ("explore", "validate"):
            for t, s in out[f"{scope}:{split}"].items():
                ci = s.get("roi_ci")
                L.append(f"| {scope} | {split} | {float(t):.0%}{' **chosen**' if thr is not None and float(t) == thr else ''} | {s['n']} | "
                         f"{'' if s.get('roi') is None else format(s['roi'] * 100, '+.1f') + '%'} | "
                         f"{'' if not ci else format(ci[0] * 100, '+.1f') + '% to ' + format(ci[1] * 100, '+.1f') + '%'} | "
                         f"{'' if s.get('t') is None else format(s['t'], '+.1f')} | {'' if s.get('mean_ev') is None else format(s['mean_ev'] * 100, '+.1f') + '%'} |")
        L.append(f"| {scope} | gate | | | | | | {'PASS' if out[f'{scope}:passes'] else 'fail'} {out[f'{scope}:checks']} |")
    open("reports/line_shop_respec.md", "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
