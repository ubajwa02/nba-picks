"""Line shopping: bet a side only where one book's price beats the consensus of the others.

Consensus fair probability for a side = median over the OTHER book families of each
family's de-vigged probability at the same line (a book never votes on its own price).
EV vs consensus = fair * price - 1. Moneylines everywhere; spreads and totals only at
half-point lines (no push), and only books quoting the modal line for that game.

This is the experiment for backlog NBA-024. It uses history closing lines, which for
legacy seasons are untimed final quotes, so an apparent edge can come from one book's
line being stale rather than beatable; that is why validation needs significance and why
forward results with timed prices decide promotion.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from collections import defaultdict
from statistics import median

from .. import metrics as M
from .. import odds as O
from ..backtest import SPLITS, clean_quotes, load, split_of
from ..settle import GameResult, net_profit, settle_leg

MIN_FAMILIES = 3          # the book plus at least two other families


def family(book: str) -> str:
    """Caesars state books, 'Caesar's' and 'Caesars Sportsbook' share one price; count them once."""
    b = re.sub(r"[^a-z0-9 ]", "", book.lower())
    return b.split()[0] if b else book


def bets_for_game(g, books: dict, kind: str = "close") -> list[dict]:
    clean, _ = clean_quotes(books, kind)
    res = GameResult("final", g.home_score, g.away_score)
    out = []
    for market in ("ml", "spread", "total"):
        quotes = {b: qs[market] for b, qs in clean.items() if market in qs}
        if market != "ml":
            key = "home" if market == "spread" else "over"
            lines = [q[key][0] for q in quotes.values()]
            if not lines:
                continue
            modal = max(set(lines), key=lines.count)
            if modal == int(modal):
                continue                          # whole line: pushes; skipped for clean EV
            quotes = {b: q for b, q in quotes.items() if q[key][0] == modal}
        sides = ("home", "away") if market != "total" else ("over", "under")
        fam_fair = defaultdict(list)
        for b, q in quotes.items():
            f = (O.devig_power if market == "ml" else O.devig_multiplicative)([q[sides[0]][1], q[sides[1]][1]])
            fam_fair[family(b)].append(f[0])
        fam_fair = {k: median(v) for k, v in fam_fair.items()}
        if len(fam_fair) < MIN_FAMILIES:
            continue
        for b, q in quotes.items():
            others = [v for k, v in fam_fair.items() if k != family(b)]
            if len(others) < MIN_FAMILIES - 1:
                continue
            p0 = median(others)
            for s, p in ((sides[0], p0), (sides[1], 1 - p0)):
                line, price = q[s][0], q[s][1]
                r = settle_leg(market, s, line, res)
                out.append(dict(game_id=g.game_id, season=g.season, split=split_of(g.season), date=str(g.date),
                                market=market, book=b, selection=s, line=line, price=price, fair=p,
                                ev=p * price - 1, result=r, net=net_profit(r, price, 1.0)))
    return out


def best_per_side(recs: list[dict]) -> list[dict]:
    """One bet per game side: the book with the highest EV (what a shopper would take)."""
    best = {}
    for r in recs:
        k = (r["game_id"], r["market"], r["selection"])
        if k not in best or r["ev"] > best[k]["ev"]:
            best[k] = r
    return list(best.values())


def stats(recs, thr):
    chosen = [r for r in recs if r["ev"] >= thr and r["result"] in ("win", "loss", "push")]
    s = M.roi_summary([r["net"] for r in chosen], n_boot=500)
    s["mean_ev"] = sum(r["ev"] for r in chosen) / len(chosen) if chosen else None
    return s


def run(hist="data/history", splits=("explore", "validate")) -> list[dict]:
    games, lines = load(hist)
    target = {s for k in splits for s in SPLITS[k]}
    recs = []
    for g in games:
        if g.season in target and lines.get(g.game_id):
            recs += bets_for_game(g, lines[g.game_id])
    return best_per_side(recs)


THRESHOLDS = [0.0, 0.01, 0.02, 0.03, 0.05]


def main(argv=None):
    from ..research import REG, append, commit, now, choose_threshold_rows
    import yaml
    ap = argparse.ArgumentParser(); ap.parse_args(argv)
    gates = yaml.safe_load(open("config/gates.yaml"))["paper"]
    exp_id = f"exp-{dt.date.today():%Y%m%d}-lineshop"
    crit = dict(validate_roi_at_threshold=0.0, validate_min_bets=gates["validate_min_bets"], validate_t_min=2.0,
                threshold_rule=f"best explore ROI among {THRESHOLDS} with >= {gates['explore_min_bets_for_threshold']} bets")
    append(REG, dict(exp_id=exp_id, step="registered", at=now(), commit=commit(), variant="lineshop",
                     hypothesis="A side priced above the leave-one-out consensus of other books (EV vs consensus >= threshold) "
                                "wins more than its price implies; flat 1u at that book's closing price is profitable.",
                     baseline="zero (break-even)", metrics=["flat-1u ROI and t by market"], criteria=crit,
                     splits=["explore", "validate"]))
    recs = run()
    out = {}
    for market in ("ml", "spread", "total"):
        ex = [r for r in recs if r["split"] == "explore" and r["market"] == market]
        va = [r for r in recs if r["split"] == "validate" and r["market"] == market]
        thr = choose_threshold_rows(ex, THRESHOLDS, gates["explore_min_bets_for_threshold"], stats)
        e = {str(t): stats(ex, t) for t in THRESHOLDS}; v = {str(t): stats(va, t) for t in THRESHOLDS}
        vb = v[str(thr)] if thr is not None else {}
        checks = dict(threshold_chosen=thr is not None, validate_roi=(vb.get("roi") or -1) > 0,
                      validate_min_bets=vb.get("n", 0) >= crit["validate_min_bets"], validate_t=(vb.get("t") or 0) >= 2.0)
        out[market] = dict(threshold=thr, explore=e, validate=v, checks=checks, passes_paper_gate=all(checks.values()),
                           configs_searched=len(THRESHOLDS))
    append(REG, dict(exp_id=exp_id, step="evaluated", at=now(), commit=commit(), results=out,
                     decision={m: ("candidate_for_paper" if out[m]["passes_paper_gate"] else "rejected") for m in out},
                     reviewer="pending-independent-review"))
    write_report(out)
    print(json.dumps({m: dict(thr=r["threshold"], passes=r["passes_paper_gate"]) for m, r in out.items()}))


def write_report(out):
    L = ["# Line shopping vs leave-one-out consensus", "",
         f"Generated {dt.datetime.now(dt.timezone.utc):%Y-%m-%dT%H:%M:%SZ}. One bet per game side at the book with the highest EV "
         "against the median de-vigged price of the other book families; flat 1 unit at that book's closing price. "
         "Legacy closing quotes are untimed, so a 'beatable' price may be a stale one.", "",
         "| market | split | EV threshold | bets | ROI | 95% CI | t | mean EV |", "|---|---|---|---|---|---|---|---|"]
    for m, r in out.items():
        for split in ("explore", "validate"):
            for t, s in r[split].items():
                mark = " **chosen**" if r["threshold"] is not None and abs(float(t) - r["threshold"]) < 1e-9 else ""
                ci = s.get("roi_ci")
                L.append(f"| {m} | {split} | {float(t):.0%}{mark} | {s['n']} | {'' if s.get('roi') is None else f'{s['roi']*100:+.1f}%'} | "
                         f"{'' if not ci else f'{ci[0]*100:+.1f}% to {ci[1]*100:+.1f}%'} | {'' if s.get('t') is None else f'{s['t']:+.1f}'} | "
                         f"{'' if s.get('mean_ev') is None else f'{s['mean_ev']*100:+.1f}%'} |")
        L.append(f"| {m} | gate | | | | | | {'PASS' if r['passes_paper_gate'] else 'fail'} {r['checks']} |")
    open("reports/line_shop.md", "w").write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
