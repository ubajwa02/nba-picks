"""Situational betting rules (backlog NBA-025): simple, pre-listed game contexts bet flat at
the closing price of the first clean book in the fixed priority list. Every rule is listed
here before any result is seen; a rule passes only if validate ROI > 0 with >= 150 bets and
a t statistic at least the noise floor sqrt(2 ln N) for the N rules tested."""
from __future__ import annotations

import datetime as dt
import json

from .. import metrics as M
from ..backtest import BOOK_PRIORITY, SPLITS, clean_quotes, load, split_of
from ..settle import GameResult, net_profit, settle_leg


def _early(g):   # first 21 days of the regular season
    return g.date.month in (10, 11) and (g.date - dt.date(g.date.year, 10, 15)).days < 28


RULES = {
    # name: (market, selection, condition(game, quotes) -> bool)
    "home_dog_ml": ("ml", "home", lambda g, q: q["ml"]["home"][1] > 2.0),
    "away_b2b_home_spread": ("spread", "home", lambda g, q: g.away_rest == 1 and (g.home_rest or 0) >= 2),
    "home_b2b_away_spread": ("spread", "away", lambda g, q: g.home_rest == 1 and (g.away_rest or 0) >= 2),
    "fade_big_fav_spread": ("spread", None, lambda g, q: abs(q["spread"]["home"][0]) >= 10),   # bet the underdog
    "both_b2b_under": ("total", "under", lambda g, q: g.home_rest == 1 and g.away_rest == 1),
    "early_season_over": ("total", "over", lambda g, q: _early(g)),
    "early_season_dog_spread": ("spread", None, lambda g, q: _early(g)),
    "road_fav_ml": ("ml", "away", lambda g, q: q["ml"]["away"][1] < 2.0),
}


def run(hist="data/history", splits=("explore", "validate")):
    games, lines = load(hist)
    target = {s for k in splits for s in SPLITS[k]}
    out = []
    for g in games:
        if g.season not in target or not lines.get(g.game_id):
            continue
        clean, _ = clean_quotes(lines[g.game_id], "close")
        res = GameResult("final", g.home_score, g.away_score)
        for name, (market, sel, cond) in RULES.items():
            book = next((b for b in BOOK_PRIORITY if market in clean.get(b, {})), None)
            if not book:
                continue
            q = clean[book]
            try:
                if not cond(g, q):
                    continue
            except KeyError:
                continue          # the rule needs a market this book does not quote
            s = sel
            if s is None:         # underdog side of the spread
                s = "away" if q["spread"]["home"][0] < 0 else "home"
            line, price, _ = q[market][s]
            r = settle_leg(market, s, line, res)
            out.append(dict(rule=name, split=split_of(g.season), season=g.season, result=r, net=net_profit(r, price, 1.0)))
    return out


def main():
    import yaml
    from ..research import REG, append, commit, now
    gates = yaml.safe_load(open("config/gates.yaml"))["paper"]
    floor = M.noise_floor(len(RULES))
    exp_id = f"exp-{dt.date.today():%Y%m%d}-situational"
    append(REG, dict(exp_id=exp_id, step="registered", at=now(), commit=commit(), variant="situational",
                     hypothesis="Simple game contexts (rest, home dogs, big favourites, early season) are mispriced at the close.",
                     rules=list(RULES), baseline="zero (break-even)", splits=["explore", "validate"],
                     criteria=dict(validate_roi=0.0, validate_min_bets=gates["validate_min_bets"], validate_t_min=round(floor, 2),
                                   explore_roi=0.0)))
    recs = run()
    res = {}
    for name in RULES:
        e = M.roi_summary([r["net"] for r in recs if r["rule"] == name and r["split"] == "explore" and r["result"] != "pending"], n_boot=500)
        v = M.roi_summary([r["net"] for r in recs if r["rule"] == name and r["split"] == "validate" and r["result"] != "pending"], n_boot=500)
        checks = dict(explore_roi=(e["roi"] or -1) > 0, validate_roi=(v["roi"] or -1) > 0,
                      validate_min_bets=v["n"] >= gates["validate_min_bets"], validate_t=(v["t"] or 0) >= floor)
        res[name] = dict(explore=e, validate=v, checks=checks, passes_paper_gate=all(checks.values()), configs_searched=1)
    append(REG, dict(exp_id=exp_id, step="evaluated", at=now(), commit=commit(), results=res,
                     decision={k: ("candidate_for_paper" if v["passes_paper_gate"] else "rejected") for k, v in res.items()},
                     reviewer="pending-independent-review"))
    L = ["# Situational rules", "", f"Flat 1 unit at the closing price of the first clean book in the priority list. Noise floor for {len(RULES)} rules: t >= {floor:.2f}.", "",
         "| rule | explore bets | explore ROI (t) | validate bets | validate ROI | 95% CI | t | gate |", "|---|---|---|---|---|---|---|---|"]
    for k, r in res.items():
        e, v = r["explore"], r["validate"]
        pc = lambda x: "" if x is None else f"{x*100:+.1f}%"
        L.append(f"| {k} | {e['n']} | {pc(e['roi'])} ({(e['t'] or 0):+.1f}) | {v['n']} | {pc(v['roi'])} | "
                 f"{'' if not v.get('roi_ci') else f'{v['roi_ci'][0]*100:+.1f}% to {v['roi_ci'][1]*100:+.1f}%'} | {(v['t'] or 0):+.1f} | {'PASS' if r['passes_paper_gate'] else 'fail'} |")
    open("reports/situational.md", "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
