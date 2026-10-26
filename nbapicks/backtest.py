"""Walk-forward backtest of game-market models against real closing (and opening) lines.

For every game day D the model is refit on games strictly before D, then priced
against the line ESPN recorded for one representative sportsbook. Nothing from
D or later reaches the fit. Splits are fixed in advance (see SPLITS) and the
holdout is only scored by `--holdout`, once, after choices are frozen on explore.

Outputs per-bet rows (for audit) and a summary by split x market x variant.
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import math
import os
from collections import defaultdict

from . import metrics as M
from . import odds as O
from .history import read_csv
from .models.ratings import Game, RatingsModel, RatingsParams, add_rest_days
from .settle import GameResult, settle_leg, net_profit

# seasons are ESPN years (2015 = 2014-15). Fixed before any result was seen.
SPLITS = {"explore": range(2015, 2021), "validate": range(2021, 2024), "holdout": range(2024, 2027)}
BOOK_PRIORITY = ["DraftKings", "Draft Kings", "ESPN BET", "Caesars Sportsbook", "Caesars", "MGM", "BetMGM",
                 "Westgate", "BOVADA.lv", "BETONLINE.ag", "5Dimes.eu", "PinnacleSports.com", "Unibet", "SugarHouse"]


def split_of(season: int) -> str:
    for k, r in SPLITS.items():
        if season in r:
            return k
    return "other"


def load(hist_dir: str, seasons: list[int] | None = None):
    games, lines = [], defaultdict(dict)
    for path in sorted(glob.glob(f"{hist_dir}/games_*.csv.gz")):
        s = int(path.split("_")[-1].split(".")[0])
        if seasons and s not in seasons:
            continue
        for r in read_csv(path):
            if r["status"] != "final":
                continue
            d = dt.datetime.fromisoformat(r["start_utc"].replace("Z", "+00:00"))
            # US slate date: shift UTC back 6h so late tips stay on the local day
            day = (d - dt.timedelta(hours=6)).date()
            g = Game(r["game_id"], day, r["home"], r["away"], int(r["home_score"]), int(r["away_score"]))
            g.season = s
            games.append(g)
        op = path.replace("games_", "odds_")
        if os.path.exists(op):
            for r in read_csv(op):
                lines[r["game_id"]].setdefault(r["book"], []).append(r)
    add_rest_days(games)
    return games, lines


# Line-quality rules (Skeptic review 2026-10-20, finding 1). Legacy ESPN quotes are untimed and some
# are in-game lines; these rules drop quotes that cannot be pre-game prices. Thresholds come from the
# clean seasons (2014-17, 2021-22), where ML-implied and quoted spreads differ by <= 10 points in
# 99.9% of games.
SIGMA_LINK = 12.6
MAX_ML_SPREAD_GAP = 10.0          # points between the ML-implied spread and the quoted spread
MAX_DEV_FROM_MEDIAN = {"spread": 4.0, "total": 6.0, "ml": 0.15}   # points (prob for ML), with >= 3 books
MAX_ABS_SPREAD, TOTAL_RANGE = 40.0, (150.0, 300.0)


def _ml_home_prob(q):
    return O.devig_power([q["home"][1], q["away"][1]])[0]


def clean_quotes(books: dict, kind: str) -> tuple[dict, dict]:
    """{book: {market: pair}} of quotes that pass the line-quality rules, plus drop counts."""
    from statistics import NormalDist, median
    nd = NormalDist()
    out, dropped = {}, defaultdict(int)
    for b, rows in books.items():
        qs = {}
        for m in ("ml", "spread", "total"):
            q = market_pair(rows, kind, m)
            if not q:
                continue
            if m == "spread" and abs(q["home"][0]) > MAX_ABS_SPREAD:
                dropped["impossible_line"] += 1; continue
            if m == "total" and not TOTAL_RANGE[0] <= q["over"][0] <= TOTAL_RANGE[1]:
                dropped["impossible_line"] += 1; continue
            qs[m] = q
        if "ml" in qs and "spread" in qs:
            p = min(max(_ml_home_prob(qs["ml"]), 1e-4), 1 - 1e-4)
            if abs(-SIGMA_LINK * nd.inv_cdf(p) - qs["spread"]["home"][0]) > MAX_ML_SPREAD_GAP:
                del qs["ml"], qs["spread"]          # one of the two is not a pre-game price; keep neither
                dropped["ml_spread_mismatch"] += 1
        if qs:
            out[b] = qs
    for m in ("spread", "total", "ml"):
        vals = {b: (qs[m]["home"][0] if m == "spread" else qs[m]["over"][0] if m == "total" else _ml_home_prob(qs[m]))
                for b, qs in out.items() if m in qs}
        if len(vals) >= 3:
            med = median(vals.values())
            for b, v in vals.items():
                if abs(v - med) > MAX_DEV_FROM_MEDIAN[m]:
                    del out[b][m]; dropped[f"{m}_off_consensus"] += 1
    return out, dropped


def pick_book(books: dict) -> tuple[str, list] | tuple[None, None]:
    for b in BOOK_PRIORITY:
        if b in books:
            return b, books[b]
    for b, rows in sorted(books.items()):
        return b, rows
    return None, None


def market_pair(rows, kind: str, market: str):
    """Two-sided quote {selection: (line, price)} for one kind/market, or None."""
    q = {}
    for r in rows:
        if r["kind"] == kind and r["market"] == market and r["price_dec"]:
            q[r["selection"]] = (float(r["line"]) if r["line"] not in ("", None) else None, float(r["price_dec"]),
                                 r.get("flags") or "")
    need = ("home", "away") if market in ("ml", "spread") else ("over", "under")
    if not all(s in q for s in need):
        return None
    if market == "spread" and q["home"][0] is not None and q["away"][0] is not None and abs(q["home"][0] + q["away"][0]) > 1e-9:
        return None  # inconsistent pair
    if market == "total" and q["over"][0] != q["under"][0]:
        return None
    return q


def run(hist_dir: str, variants: dict[str, RatingsParams], splits: list[str], thresholds: list[float],
        blend_w: float | None = None, start: dt.date | None = None, end: dt.date | None = None) -> dict:
    """Walk-forward over the seasons of `splits`, or over the days start..end (inclusive) when given.
    Variants with availability=True get the player-availability feature from data/history/box_*;
    seasons without box scores get 0 for it and are counted in out['coverage']['availability']."""
    games, lines = load(hist_dir)  # all seasons: earlier seasons warm the ratings
    by_day = defaultdict(list)
    for g in games:
        by_day[g.date].append(g)
    if start or end:
        lo, hi = start or dt.date.min, end or dt.date.max
        target = {g.season for g in games if lo <= g.date <= hi}
    else:
        lo, hi = dt.date.min, dt.date.max
        target = {s for k in splits for s in SPLITS[k]}
    out = {"variants": {}, "bets": [], "line_quality": defaultdict(int), "coverage": {}}
    if any(getattr(p, "availability", False) for p in variants.values()):
        from .models import availability as AV
        cov = AV.attach(games, AV.read_box(hist_dir))
        out["coverage"]["availability"] = {k: v for k, v in cov.items() if k in {str(s) for s in target}}
        out["coverage"]["availability_note"] = AV.LEAKAGE_NOTE
        out["coverage"]["seasons_without_box"] = sorted(int(k) for k, v in out["coverage"]["availability"].items()
                                                        if not v["games_with_box"])
    for vname, params in variants.items():
        model = RatingsModel(params)
        recs = []
        for day in sorted(by_day):
            if not lo <= day <= hi:
                continue
            todays = [g for g in by_day[day] if g.season in target]
            if not todays:
                continue
            model.fit(games, day)
            if not model.ready():
                continue
            for g in todays:
                books = lines.get(g.game_id, {})
                if not books:
                    continue
                pred = model.predict(g.home, g.away, g.home_rest, g.away_rest, g.home_missing, g.away_missing)
                res = GameResult("final", g.home_score, g.away_score)
                for kind in ("close", "open"):
                    clean, drops = clean_quotes(books, kind)
                    for k, v in drops.items():
                        out["line_quality"][f"{g.season}|{kind}|{k}"] += v
                    for market in ("ml", "spread", "total"):
                        # first book in the fixed priority list that has a clean quote for this market
                        book = next((b for b in BOOK_PRIORITY if market in clean.get(b, {})), None) \
                            or next((b for b in sorted(clean) if market in clean[b]), None)
                        if not book:
                            continue
                        q = clean[book][market]
                        sels = list(q)
                        prices = [q[s][1] for s in sels]
                        fair = O.devig_power(prices) if market == "ml" else O.devig_multiplicative(prices)
                        for s, f in zip(sels, fair):
                            line, price, flags = q[s]
                            p, push = RatingsModel.prob(pred, market, s, line)
                            if blend_w is not None:
                                p = _blend(p, f, blend_w, push)
                            ev = O.ev_with_push(p, push, price)
                            r = settle_leg(market, s, line, res)
                            recs.append(dict(variant=vname, split=split_of(g.season), season=g.season, date=str(day),
                                             game_id=g.game_id, book=book, kind=kind, market=market, selection=s,
                                             line=line, price=price, fair=f, prob=p, push=push, ev=ev, result=r,
                                             net=net_profit(r, price, 1.0), assumed_price="price_assumed" in flags,
                                             mu_margin=pred["mu_margin"], mu_total=pred["mu_total"],
                                             avail_known=g.avail_known, home_missing=g.home_missing,
                                             away_missing=g.away_missing))
        out["variants"][vname] = summarize(recs, thresholds)
        out["bets"].extend(recs)
    return out


def _blend(p, fair, w, push):
    # blend on the win-vs-not scale; push mass kept from the model
    eps = 1e-6
    lp = math.log(max(p, eps) / max(1 - p - push, eps)); lf = math.log(max(fair, eps) / max(1 - fair, eps))
    z = w * lp + (1 - w) * lf
    q = 1 / (1 + math.exp(-z))
    return q * (1 - push)


def summarize(recs: list[dict], thresholds: list[float]) -> dict:
    res = {}
    groups = defaultdict(list)
    for r in recs:
        groups[(r["split"], r["kind"], r["market"])].append(r)
    for (split, kind, market), rs in sorted(groups.items()):
        key = f"{split}|{kind}|{market}"
        decided = [r for r in rs if r["result"] in ("win", "loss")]
        # probability quality on one side per game (home / over) to avoid double counting
        one = [r for r in decided if r["selection"] in ("home", "over")]
        ys = [1 if r["result"] == "win" else 0 for r in one]
        entry = dict(n_games=len(one))
        if one:
            entry.update(model_logloss=M.log_loss([r["prob"] / max(1e-9, 1 - r["push"]) for r in one], ys),
                         market_logloss=M.log_loss([r["fair"] for r in one], ys),
                         model_brier=M.brier([r["prob"] / max(1e-9, 1 - r["push"]) for r in one], ys),
                         market_brier=M.brier([r["fair"] for r in one], ys))
        bets = {}
        for t in thresholds:
            chosen = [r for r in rs if r["ev"] >= t and r["result"] != "pending"]
            nets = [r["net"] for r in chosen]
            s = M.roi_summary(nets)
            s.update(M.drawdown(nets))
            s["win_rate"] = (sum(1 for r in chosen if r["result"] == "win") / len(chosen)) if chosen else None
            s["mean_ev"] = (sum(r["ev"] for r in chosen) / len(chosen)) if chosen else None
            bets[str(t)] = s
        entry["bets"] = bets
        res[key] = entry
    return res


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--hist", default="data/history")
    ap.add_argument("--splits", default="explore")
    ap.add_argument("--out", default="reports/backtest")
    a = ap.parse_args(argv)
    variants = {"base": RatingsParams()}
    res = run(a.hist, variants, a.splits.split(","), [0.0, 0.02, 0.03, 0.05])
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(res["variants"], open(a.out + ".json", "w"), indent=1, default=str)
    print(json.dumps(res["variants"], indent=1, default=str)[:5000])


if __name__ == "__main__":
    main()
