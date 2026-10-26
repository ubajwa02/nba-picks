"""Game-market backtest over a date range (typically one month), per docs/CONTRACTS.md section 2.

    python -m nbapicks.monthtest --start 2023-02-01 --end 2023-02-28 --variants trend,avail

Walk-forward with backtest.run: every game day the model is refit on games strictly before that
day, then priced against the cleaned closing line (backtest.clean_quotes) and, where ESPN has
one, the opening line. For each variant x market (ml/spread/total) x price kind (close/open) the
report has a 'raw' run (model probability) and, when the research registry holds an evaluated
experiment for the variant, a 'blend' run with that experiment's frozen blend weight for the
market (never refit here). A side is bet when its EV >= the market's min_ev in
config/nbapicks.yaml, flat 1 unit (1u = $100). Log loss and Brier are on one side per game
(home / over) against the de-vigged price of the same book.

Dates inside the holdout seasons (backtest.SPLITS['holdout']) are refused unless --holdout.
Writes reports/backtest_games.json and reports/backtest_games.md.
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import os
from collections import Counter, defaultdict

import yaml

from . import metrics as M
from .backtest import BOOK_PRIORITY, SPLITS, clean_quotes, load, run, split_of
from .history import read_csv
from .odds import ev_with_push
from .research import REG, VARIANTS, _blend, commit, now

MARKETS = ("ml", "spread", "total")
KINDS = ("close", "open")
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


class HoldoutRefused(SystemExit):
    pass


def season_of_date(d: dt.date) -> int:
    """ESPN season year of a calendar day (season 2023 = 2022-23), for days without games."""
    return d.year + 1 if d.month >= 10 else d.year


def seasons_in_range(hist_dir: str, start: dt.date, end: dt.date) -> set[int]:
    """Seasons of the games in [start, end] (from games_*.csv.gz) plus the calendar rule."""
    out = set()
    d = start
    while d <= end:
        out.add(season_of_date(d)); d += dt.timedelta(days=1)
    lo, hi = (start - dt.timedelta(days=1)).isoformat(), (end + dt.timedelta(days=2)).isoformat()
    for path in glob.glob(os.path.join(hist_dir, "games_*.csv.gz")):
        s = int(path.split("_")[-1].split(".")[0])
        if s in out:
            continue
        for r in read_csv(path):
            if lo <= r["start_utc"][:10] <= hi:
                day = (dt.datetime.fromisoformat(r["start_utc"].replace("Z", "+00:00")) - dt.timedelta(hours=6)).date()
                if start <= day <= end:
                    out.add(s); break
    return out


def check_holdout(hist_dir: str, start: dt.date, end: dt.date, allow: bool) -> set[int]:
    seasons = seasons_in_range(hist_dir, start, end)
    bad = sorted(seasons & set(SPLITS["holdout"]))
    if bad and not allow:
        raise HoldoutRefused(f"refused: {start}..{end} falls in holdout season(s) {bad}; the holdout is scored once "
                             f"per frozen candidate. Pass --holdout to do that deliberately.")
    return seasons


def frozen_weights(registry: str, variant: str) -> tuple[dict, str | None]:
    """{market: w} from the latest 'evaluated' experiment of `variant`, and its exp_id."""
    if not os.path.exists(registry):
        return {}, None
    reg_variant, latest = {}, None
    for line in open(registry):
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("step") == "registered" and rec.get("variant"):
            reg_variant[rec["exp_id"]] = rec["variant"]
        elif rec.get("step") == "evaluated" and reg_variant.get(rec.get("exp_id")) == variant:
            ws = {m: r["blend_w"] for m, r in (rec.get("results") or {}).items()
                  if m in MARKETS and isinstance(r, dict) and r.get("blend_w") is not None}
            if ws:
                latest = (ws, rec["exp_id"])
    return latest if latest else ({}, None)


def _pwin(r: dict, w: float | None) -> float:
    """Win probability of a side record, raw or blended (push mass kept from the model)."""
    if w is None:
        return r["prob"]
    return _blend(r["prob"] / max(1e-9, 1 - r["push"]), r["fair"], w) * (1 - r["push"])


def score(recs: list[dict], min_ev: float, w: float | None, baseline_probs: dict | None = None) -> dict:
    """Contract fields for one run. recs: backtest side records of one variant/market/kind."""
    scored = [r for r in recs if r["result"] != "pending"]
    bets = []
    for r in scored:
        p = _pwin(r, w)
        ev = ev_with_push(p, r["push"], r["price"])
        if ev >= min_ev:
            bets.append((r, p, ev))
    nets = [r["net"] for r, _, _ in bets]
    s = M.roi_summary(nets)
    res = Counter(r["result"] for r, _, _ in bets)
    wins, losses = res["win"], res["loss"]
    out = dict(eligible=len(scored), bets=len(bets), wins=wins, losses=losses, pushes=res["push"], voids=res["void"],
               hit_rate=wins / (wins + losses) if wins + losses else None,
               avg_prob=sum(p for _, p, _ in bets) / len(bets) if bets else None,
               avg_price_dec=sum(r["price"] for r, _, _ in bets) / len(bets) if bets else None,
               avg_implied=sum(1 / r["price"] for r, _, _ in bets) / len(bets) if bets else None,
               avg_ev=sum(e for _, _, e in bets) / len(bets) if bets else None,
               units_staked=float(len(bets)), net_units=float(sum(nets)), net_dollars=round(100.0 * sum(nets), 2),
               roi=s["roi"], roi_ci=list(s["roi_ci"]) if s["roi_ci"] else None, roi_t=s["t"])
    one = [r for r in scored if r["selection"] in ("home", "over") and r["result"] in ("win", "loss")]
    ys = [1 if r["result"] == "win" else 0 for r in one]
    if one:
        pm = [_pwin(r, w) / max(1e-9, 1 - r["push"]) for r in one]
        pf = [r["fair"] for r in one]
        out.update(logloss_model=M.log_loss(pm, ys), logloss_market=M.log_loss(pf, ys),
                   brier_model=M.brier(pm, ys), brier_market=M.brier(pf, ys),
                   calibration=[{k: c[k] for k in ("lo", "hi", "n", "predicted", "observed")}
                                for c in M.calibration(pm, ys, 10)])
        if baseline_probs is not None:
            pairs = [(baseline_probs[(r["game_id"], r["market"], r["kind"])], y)
                     for r, y in zip(one, ys) if (r["game_id"], r["market"], r["kind"]) in baseline_probs]
            out["logloss_baseline"] = M.log_loss([p for p, _ in pairs], [y for _, y in pairs]) if len(pairs) == len(one) else None
        else:
            out["logloss_baseline"] = out["logloss_market"]
        out["n_games_scored"] = len(one)
    else:
        out.update(logloss_model=None, logloss_market=None, brier_model=None, brier_market=None, calibration=[],
                   logloss_baseline=None, n_games_scored=0)
    return out


def _period_name(start: dt.date, end: dt.date) -> str:
    if start.year == end.year and start.month == end.month:
        return f"{MONTHS[start.month - 1]} {start.year}"
    return f"{start} to {end}"


def line_coverage(hist_dir: str, start: dt.date, end: dt.date) -> dict:
    """Per kind: games in the period, games with a clean quote per market, quotes dropped and why
    (ESPN BET 2022-23 counted apart: it carries the American price in the spread/total line field)."""
    games, lines = load(hist_dir)
    period = [g for g in games if start <= g.date <= end]
    out = {"games": len(period), "seasons": sorted({g.season for g in period})}
    for kind in KINDS:
        k = dict(games_with_any_quote=0, games_with_clean=dict.fromkeys(MARKETS, 0), dropped=Counter(),
                 espn_bet_impossible_lines=0, chosen_book=Counter())
        for g in period:
            books = lines.get(g.game_id, {})
            if any(r["kind"] == kind for rows in books.values() for r in rows):
                k["games_with_any_quote"] += 1
            clean, drops = clean_quotes(books, kind)
            k["dropped"].update(drops)
            if "ESPN BET" in books:
                k["espn_bet_impossible_lines"] += clean_quotes({"ESPN BET": books["ESPN BET"]}, kind)[1].get("impossible_line", 0)
            for m in MARKETS:
                book = next((b for b in BOOK_PRIORITY if m in clean.get(b, {})), None) \
                    or next((b for b in sorted(clean) if m in clean[b]), None)
                if book:
                    k["games_with_clean"][m] += 1
                    k["chosen_book"][f"{m}:{book}"] += 1
        k["dropped"], k["chosen_book"] = dict(k["dropped"]), dict(k["chosen_book"])
        out[kind] = k
    return out


def build(hist_dir: str, start: dt.date, end: dt.date, variants: list[str], allow_holdout: bool = False,
          registry: str = REG, config_path: str = "config/nbapicks.yaml") -> dict:
    check_holdout(hist_dir, start, end, allow_holdout)
    cfg = yaml.safe_load(open(config_path))
    min_ev = {m: float(cfg["markets"][m]["min_ev"]) for m in MARKETS}
    params = {v: VARIANTS[v][0] for v in variants}
    res = run(hist_dir, params, [], [0.0], start=start, end=end)
    cov = line_coverage(hist_dir, start, end)
    avail_cov = (res.get("coverage") or {}).get("availability")
    by = defaultdict(list)
    for r in res["bets"]:
        by[(r["variant"], r["market"], r["kind"])].append(r)
    seasons = cov["seasons"]
    split = "/".join(sorted({split_of(s) for s in seasons})) or "none"
    period = dict(start=str(start), end=str(end))
    pname = _period_name(start, end)
    legacy = any(s <= 2023 for s in seasons)
    runs = []
    for v in variants:
        weights, exp_id = frozen_weights(registry, v)
        p = params[v]
        pricings = [("raw", None)] + ([("blend", exp_id)] if weights else [])
        for market in MARKETS:
            for kind in KINDS:
                recs = by.get((v, market, kind), [])
                for pricing, src in pricings:
                    w = weights.get(market) if pricing == "blend" else None
                    if pricing == "blend" and w is None:
                        continue
                    base_name, base_probs = "de-vigged market (same book, same price kind)", None
                    if v != "trend" and "trend" in variants:
                        tw = frozen_weights(registry, "trend")[0].get(market) if pricing == "blend" else None
                        if pricing == "raw" or tw is not None:
                            base_name = f"trend ({pricing}{'' if tw is None else f', w={tw:.2f}'})"
                            base_probs = {(r["game_id"], r["market"], r["kind"]): _pwin(r, tw) / max(1e-9, 1 - r["push"])
                                          for r in by.get(("trend", market, kind), [])
                                          if r["selection"] in ("home", "over")}
                    s = score(recs, min_ev[market], w, base_probs)
                    notes = []
                    if pricing == "blend":
                        notes.append(f"Blend weight w={w:.2f} frozen from {src} (fit on explore seasons; not refit here)."
                                     + (" w=0 makes the blend the de-vigged market, so no side can clear a positive EV "
                                        "threshold and bets are 0 by construction." if w == 0 else ""))
                    else:
                        notes.append("Raw model probabilities (no blending with the market).")
                    if kind == "close" and legacy:
                        notes.append("Seasons up to 2022-23 carry one untimed final quote per book (flag "
                                     "final_quote_untimed), used as the closing line.")
                    if kind == "open" and not recs:
                        notes.append("No opening lines in ESPN's history for this period (open + close exist from "
                                     "2023-24); nothing to score.")
                    if 2023 in seasons and (kind == "close" or cov[kind]["espn_bet_impossible_lines"]):
                        n_eb = cov[kind]["espn_bet_impossible_lines"]
                        notes.append("ESPN BET 2022-23 puts the American price in the spread/total line field (e.g. "
                                     f"spread -115.0); clean_quotes drops those as impossible lines ({n_eb} ESPN BET "
                                     "book-quotes in this period), and DraftKings is priced first in any case.")
                    if p.availability:
                        notes.append(res["coverage"].get("availability_note") or "")
                    coverage = dict(games_in_period=cov["games"], games_with_clean_quote=cov[kind]["games_with_clean"][market],
                                    games_with_any_quote=cov[kind]["games_with_any_quote"],
                                    quotes_dropped_all_markets=cov[kind]["dropped"],
                                    books_used={b.split(":", 1)[1]: n for b, n in cov[kind]["chosen_book"].items()
                                                if b.startswith(market + ":")},
                                    games_not_priced_model_not_ready=cov[kind]["games_with_clean"][market] - len({r["game_id"] for r in recs}),
                                    price_assumed_sides=sum(1 for r in recs if r.get("assumed_price")))
                    if p.availability:
                        coverage["availability"] = dict(
                            games_with_feature=len({r["game_id"] for r in recs if r.get("avail_known")}),
                            games_without_feature=len({r["game_id"] for r in recs if not r.get("avail_known")}),
                            season_coverage=avail_cov)
                    mv = f"ratings-v1-{v}" + ("" if pricing == "raw" else f"+blend(w={w:.2f})")
                    runs.append(dict(
                        name=f"{v} {market} {kind} {pricing}, {pname} ({split})", kind="games", market=market,
                        model_version=mv, baseline=base_name, split=split, period=period,
                        staking="flat 1u per bet (1u = $100)",
                        selection_rule=f"EV >= {min_ev[market]:.0%} at the recorded {kind} price (min_ev of config/nbapicks.yaml)",
                        price_basis=("closing (untimed)" if kind == "close" else "opening (untimed)") if recs else "none",
                        variant=v, price_kind=kind, pricing=pricing, blend_w=w,
                        **s, coverage=coverage, notes=notes))
    return {"generated_at": now(), "commit": commit(), "runs": runs}


def _f(x, pct=False, d=4):
    if x is None:
        return ""
    return f"{x * 100:+.1f}%" if pct else f"{x:.{d}f}"


def write_md(rep: dict, path: str) -> None:
    runs = rep["runs"]
    if not runs:
        open(path, "w").write("# Game-market backtest\n\nNo runs.\n"); return
    r0 = runs[0]
    L = [f"# Game-market backtest: {r0['period']['start']} to {r0['period']['end']} ({r0['split']})", "",
         f"Generated {rep['generated_at']} at commit `{rep['commit']}` by `python -m nbapicks.monthtest`.", "",
         "Walk-forward: every game day each variant is refit on games strictly before that day and priced against "
         "the cleaned line of one book (DraftKings first, fixed priority list). A side is bet when EV >= the market's "
         "min_ev (config/nbapicks.yaml), flat 1u = $100. Log loss and Brier are one side per game (home/over) against "
         "the de-vigged price of the same book; 'gain vs mkt' = market minus model (positive = model better). "
         "'raw' = model probability; 'blend' = logit blend with the market using the weight frozen in the research "
         "registry (not refit).", "",
         "| variant | market | kind | pricing | games | bets | W-L-P | hit % | ROI | 95% CI | net $ | logloss model | logloss mkt | gain vs mkt | baseline | logloss baseline |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in runs:
        if r["eligible"] == 0:
            continue
        ci = r["roi_ci"]
        gain = (r["logloss_market"] - r["logloss_model"]) if r["logloss_model"] is not None else None
        pricing = r["pricing"] + ("" if r["blend_w"] is None else f" w={r['blend_w']:.2f}")
        hit = "" if r["hit_rate"] is None else f"{r['hit_rate'] * 100:.1f}%"
        L.append(f"| {r['variant']} | {r['market']} | {r['price_kind']} | {pricing} | "
                 f"{r['n_games_scored']} | {r['bets']} | {r['wins']}-{r['losses']}-{r['pushes']} | {hit} | "
                 f"{_f(r['roi'], True)} | {'' if not ci else f'{ci[0]*100:+.1f}% to {ci[1]*100:+.1f}%'} | "
                 f"{r['net_dollars']:+.0f} | {_f(r['logloss_model'])} | {_f(r['logloss_market'])} | "
                 f"{'' if gain is None else f'{gain:+.4f}'} | {r['baseline']} | {_f(r['logloss_baseline'])} |")
    empty = sorted({f"{r['variant']} {r['market']} {r['price_kind']}" for r in runs if r["eligible"] == 0})
    L += ["", "## Coverage", ""]
    for kind in KINDS:
        rk = {r["market"]: r["coverage"] for r in runs if r["price_kind"] == kind}
        if not rk:
            continue
        c0 = next(iter(rk.values()))
        per = "; ".join(f"{m} {c['games_with_clean_quote']} (books {c['books_used'] or 'none'}, model not ready "
                        f"{c['games_not_priced_model_not_ready']})" for m, c in rk.items())
        L.append(f"- {kind}: {c0['games_in_period']} games in the period, {c0['games_with_any_quote']} with any {kind} quote. "
                 f"Games with a clean quote: {per}. Book-level quotes dropped by clean_quotes (all markets): "
                 f"{c0['quotes_dropped_all_markets'] or 'none'}.")
    av = next((r["coverage"]["availability"] for r in runs if "availability" in r["coverage"] and r["eligible"]), None)
    if av:
        L.append(f"- availability feature ('avail'): known for {av['games_with_feature']} games, 0 for "
                 f"{av['games_without_feature']} (no box score or fewer than 5 earlier team games this season).")
    if empty:
        L.append(f"- nothing to score (no quotes of that kind): {', '.join(empty)}.")
    notes = []
    for r in runs:
        for n in r["notes"]:
            if n not in notes:
                notes.append(n)
    L += ["", "## Notes", ""] + [f"- {n}" for n in notes] + [
        "- One month is a small sample: a few hundred sides per market. ROI intervals are wide and the "
        "log-loss differences are not tested for significance here; use the research runner for decisions.", ""]
    open(path, "w").write("\n".join(L))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--start", required=True, type=dt.date.fromisoformat)
    ap.add_argument("--end", required=True, type=dt.date.fromisoformat)
    ap.add_argument("--variants", default="trend,avail")
    ap.add_argument("--hist", default="data/history")
    ap.add_argument("--registry", default=REG)
    ap.add_argument("--config", default="config/nbapicks.yaml")
    ap.add_argument("--out", default="reports/backtest_games")
    ap.add_argument("--holdout", action="store_true", help="allow dates inside the holdout seasons (scored once)")
    a = ap.parse_args(argv)
    if a.end < a.start:
        ap.error("--end is before --start")
    names = [v for v in a.variants.split(",") if v]
    unknown = [v for v in names if v not in VARIANTS]
    if unknown:
        ap.error(f"unknown variants {unknown}; have {sorted(VARIANTS)}")
    try:
        rep = build(a.hist, a.start, a.end, names, a.holdout, a.registry, a.config)
    except HoldoutRefused as e:
        ap.exit(2, f"{e}\n")
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out + ".json", "w") as fh:
        json.dump(rep, fh, indent=1, default=str)
    write_md(rep, a.out + ".md")
    for r in rep["runs"]:
        print(f"{r['name']}: bets {r['bets']} roi {_f(r['roi'], True)} logloss model {_f(r['logloss_model'])} "
              f"market {_f(r['logloss_market'])}")
    return rep


if __name__ == "__main__":
    main()
