"""How the learning gate behaves on seasons where the truth is known (nbapicks/learn.py).

Synthetic seasons are built from the real graded slates (their sizes, prices and prop model
estimates, drawn with replacement). Results are then drawn from a known truth, and the loop is
replayed slate by slate exactly as `learn.run` does: refit on the past, judge, apply to the next.

  python -m tools.learn_gate_sim [--seasons 100] [--slates 160] [--seed 1] [--only NAME] [--cache DIR]

Scenarios (log-odds in brackets):
  market is right       results follow the fair chance exactly
  under by 1/2/3 points Overs win that much less often than the fair chance says (-0.04/-0.08/-0.12)
  model knows 15%       the truth sits 15% of the way from the market to the prop model
  bias that ends        Overs 3 points too high for the first 60 slates, then the market is right

Per scenario it prints how often a correction was put in force during the season, when, how often
it was later dropped, and what applying it did to log loss (positive = it helped).

The refits are the slow part (about 2.5 seconds a season). With --cache they are stored per
scenario, so a change to the gate (config/gates.yaml `learning`, or learn.judge) can be replayed
on the same seasons in seconds. A change to the corrections themselves needs a new cache.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os

import numpy as np

from nbapicks import config as C
from nbapicks import learn as L

SCENARIOS = {
    "market is right": dict(),
    "under by 1 point": dict(a=-0.04),
    "under by 2 points": dict(a=-0.08),
    "under by 3 points": dict(a=-0.12),
    "model knows 15%": dict(c=0.15),
    "bias that ends": dict(a=-0.12, until=60),
}


def season(real: list[list[dict]], n_slates: int, rng, a=0.0, c=0.0, until=None) -> L.Table:
    rows = []
    for i in rng.integers(0, len(real), n_slates):
        k = len(rows) and rows[-1]["slate"] + 1
        for r in real[i]:
            z = float(L._logit(r["p_mkt"]))
            zm = float(L._logit(r["p_model"])) if r["p_model"] is not None else z
            truth = z + (a if until is None or k < until else 0.0) + c * (zm - z)
            rows.append(dict(r, slate=k, over=int(rng.random() < L._sig(truth)), model_version="sim" if r["p_model"] is not None else None))
    return L.Table(rows)


def scored(t: L.Table) -> dict:
    """{correction: [(slate number, props, log loss saved, score)]}: every refit of a season, the slow part."""
    return {name: [list(p) for p in d["per"]] for name, d in L.walk_forward(t).items()}


def replay(per: dict, gate: dict, until: int | None = None) -> dict:
    """The loop slate by slate: before slate k the gate sees slates < k; what is in force is applied to k.
    `until`: the slate from which the truth changed, to count what happened after it."""
    rows = {n: {int(p[0]): p for p in d} for n, d in per.items()}
    last = max((k for d in rows.values() for k in d), default=-1)
    incumbent, first, drops, on, gain, props, on_after, gain_after, props_after = None, None, 0, 0, 0.0, 0, 0, 0.0, 0
    for k in range(last + 2):
        stats = {n: L.summarise([p for i, p in sorted(d.items()) if i < k]) for n, d in rows.items()}
        now, _ = L.judge(stats, gate, incumbent)
        if now and first is None:
            first = k
        if incumbent and not now:
            drops += 1
        incumbent = now
        if now and k in rows[now]:
            on += 1
            gain += rows[now][k][2]
            props += rows[now][k][1]
            if until is not None and k >= until:
                on_after += 1
                gain_after += rows[now][k][2]
                props_after += rows[now][k][1]
    return dict(first=first, drops=drops, slates_on=on, gain=gain, props=props, end=incumbent,
                slates_on_after=on_after, gain_after=gain_after, props_after=props_after,
                all_props=sum(p[1] for p in max(rows.values(), key=len).values()) if rows else 0)


def seasons(name: str, real: list[list[dict]], n: int, n_slates: int, seed: int, cache: str | None) -> list[dict]:
    path = cache and os.path.join(cache, f"{name.replace(' ', '_').replace('%', '')}_{n}x{n_slates}_seed{seed}_v{L.VERSION}.json")
    if path and os.path.exists(path):
        with open(path) as fh:
            return json.load(fh)
    rng = np.random.default_rng(seed)
    out = [scored(season(real, n_slates, rng, **SCENARIOS[name])) for _ in range(n)]
    if path:
        os.makedirs(cache, exist_ok=True)
        with open(path, "w") as fh:
            json.dump(out, fh)
    return out


def summary(name: str, res: list[dict], n_slates: int) -> dict:
    on = [r for r in res if r["first"] is not None]
    props, gain = sum(r["props"] for r in res), sum(r["gain"] for r in res)
    out = {"scenario": name, "seasons": len(res), "seasons_with_a_correction": len(on),
           "first_put_in_force_after_slates_median": float(np.median([r["first"] for r in on])) if on else None,
           "share_of_slates_in_force": round(sum(r["slates_on"] for r in res) / (len(res) * n_slates), 3),
           "seasons_with_a_drop": sum(r["drops"] > 0 for r in res),
           "in_force_at_season_end": sum(r["end"] is not None for r in res),
           "log_loss_saved_per_prop_while_in_force": round(gain / props, 6) if props else None,
           "log_loss_saved_per_prop_over_the_season": round(gain / max(1, sum(r["all_props"] for r in res)), 6)}
    if SCENARIOS[name].get("until") is not None:
        pa = sum(r["props_after"] for r in res)
        out["slates_in_force_after_the_change_mean"] = round(float(np.mean([r["slates_on_after"] for r in res])), 1)
        out["log_loss_saved_per_prop_in_force_after_the_change"] = round(sum(r["gain_after"] for r in res) / pa, 6) if pa else None
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seasons", type=int, default=100)
    ap.add_argument("--slates", type=int, default=160)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--only")
    ap.add_argument("--cache", help="directory for the refits of each scenario (reused when present)")
    a = ap.parse_args()
    from nbapicks.pipeline import Ctx
    ctx = Ctx(dt.datetime.now(dt.timezone.utc), C.load())
    rows = L.graded(ctx.store, ctx.tz, L.first_slate(ctx.today))
    real = [[r for r in rows if r["slate"] == s] for s in sorted({r["slate"] for r in rows})]
    gate = L.gates()
    print(json.dumps(dict(real_slates=len(real), real_props=len(rows), seasons=a.seasons, slates=a.slates, gate=gate)))
    for name, sc in SCENARIOS.items():
        if a.only and a.only != name:
            continue
        res = [replay(per, gate, sc.get("until")) for per in seasons(name, real, a.seasons, a.slates, a.seed, a.cache)]
        print(json.dumps(summary(name, res, a.slates)))


if __name__ == "__main__":
    main()
