"""Post-settlement diagnostics: calibration, drift and error segments over the
live ledger, turned into prioritised research hypotheses.

This is the automatic half of the improvement loop. It never edits a model or a
setting. It writes reports/diagnostics.md and data/research/queue.yaml, the
list of challenger experiments the weekly research job may run (bounded), and
flags markets for probation when the demotion gate in config/gates.yaml trips.
"""
from __future__ import annotations

import datetime as dt
import json
import os
from collections import defaultdict

import yaml

from . import metrics as M
from .pipeline import Ctx, iso

# challengers that can be generated from a finding; each maps to research.VARIANTS
PLAYBOOK = {
    "overconfident": ("blend toward market / wider sigma", "A model weight below the current blend or a larger sigma fixes overconfidence seen live."),
    "totals_bias": ("trend", "Scoring drift: totals are biased; a time trend in the points model removes it."),
    "rest_effect": ("rest", "Back-to-back games explain part of the error."),
    "slow_adapt": ("hl30", "Early-season errors are large; faster decay adapts sooner."),
    "noisy": ("hl120", "Errors are noise-dominated; slower decay stabilises ratings."),
}


def run(ctx: Ctx) -> dict:
    gates = yaml.safe_load(open("config/gates.yaml"))
    s = ctx.store
    rows = s.q("""SELECT p.*, e.result, e.net_units FROM predictions p
                  JOIN pred_events e ON e.pred_id = p.pred_id AND e.type = 'settled'
                  WHERE p.origin = 'model' AND p.category = 'straight'""")
    by_m = defaultdict(list)
    for r in rows:
        if r["result"] in ("win", "loss") and r["selection"] in ("home", "over") and r["prob"] is not None:
            by_m[r["market"]].append(r)
    findings, out = [], {}
    for m, rs in by_m.items():
        rs.sort(key=lambda r: r["created_at"])
        ps = [r["prob"] / max(1e-9, 1 - (r["prob_push"] or 0)) for r in rs]
        ys = [1 if r["result"] == "win" else 0 for r in rs]
        cal = M.calibration(ps, ys, 10)
        err = sum(abs(b["predicted"] - b["observed"]) * b["n"] for b in cal) / max(1, len(rs))
        fair = [json.loads(r["inputs"] or "{}").get("fair") for r in rs]
        mk_ll = M.log_loss([f for f in fair if f is not None], [y for f, y in zip(fair, ys) if f is not None]) if any(fair) else None
        half = len(rs) // 2
        drift = (M.brier(ps[half:], ys[half:]) - M.brier(ps[:half], ys[:half])) if half >= 30 else None
        out[m] = dict(n=len(rs), calibration_error=err, logloss=M.log_loss(ps, ys), market_logloss=mk_ll, brier_drift=drift)
        if len(rs) >= 50:
            over = sum(1 for b in cal for _ in [0] if (b["predicted"] - 0.5) * (b["observed"] - b["predicted"]) < 0) / max(1, len(cal))
            if over > 0.6:
                findings.append(("overconfident", m, f"{over:.0%} of populated bins are more extreme than outcomes"))
            if mk_ll is not None and out[m]["logloss"] > mk_ll:
                findings.append(("overconfident", m, "live log loss is worse than the de-vigged market"))
            if drift is not None and drift > 0.01:
                findings.append(("slow_adapt", m, f"Brier worsened by {drift:.3f} between halves"))
        if m == "total" and len(rs) >= 50:
            bias = sum(ys) / len(ys) - sum(ps) / len(ps)
            if abs(bias) > 0.04:
                findings.append(("totals_bias", m, f"overs hit {bias:+.1%} vs predicted"))
    # demotion gate on the published (theoretical) record
    demote = []
    d = gates["demotion"]
    pub = s.q("""SELECT p.market, e.net_units FROM predictions p JOIN pred_events e ON e.pred_id = p.pred_id AND e.type = 'settled'
                 JOIN pred_events x ON x.pred_id = p.pred_id AND x.type = 'published' ORDER BY e.at""")
    pm = defaultdict(list)
    for r in pub:
        pm[r["market"]].append(r["net_units"] or 0)
    for m, nets in pm.items():
        last = nets[-d["rolling_settled"]:]
        if len(last) >= d["rolling_settled"] and sum(last) / len(last) < d["rolling_roi_below"]:
            demote.append((m, f"rolling ROI {sum(last)/len(last):+.1%} over {len(last)}"))
    for m, o in out.items():
        if o["n"] >= 100 and o["calibration_error"] > d["calibration_error_above"]:
            demote.append((m, f"calibration error {o['calibration_error']:.3f}"))
    # queue: one experiment per distinct finding, highest information first, never more than 3 a week
    queue = []
    seen = set()
    for kind, m, why in findings:
        if kind in seen:
            continue
        seen.add(kind)
        variant, hyp = PLAYBOOK[kind]
        queue.append(dict(kind=kind, market=m, evidence=why, variant=variant, hypothesis=hyp, added=iso(ctx.now)))
    queue = queue[:3]
    os.makedirs("data/research", exist_ok=True)
    yaml.safe_dump(dict(updated=iso(ctx.now), queue=queue, probation=[dict(market=m, reason=r) for m, r in demote]),
                   open("data/research/queue.yaml", "w"), sort_keys=False)
    L = [f"# Live diagnostics ({iso(ctx.now)})", ""]
    if not out:
        L.append("No settled model predictions yet. Diagnostics start once games settle.")
    for m, o in out.items():
        L.append(f"- **{m}**: {o['n']} settled, calibration error {o['calibration_error']:.3f}, log loss {o['logloss']:.4f}"
                 + (f" (market {o['market_logloss']:.4f})" if o["market_logloss"] else "")
                 + (f", Brier drift {o['brier_drift']:+.4f}" if o["brier_drift"] is not None else ""))
    L += ["", "## Findings"] + ([f"- {k} ({m}): {w}" for k, m, w in findings] or ["- none with enough data (each needs 50+ settled)"])
    L += ["", "## Probation"] + ([f"- {m}: {r}" for m, r in demote] or ["- none"])
    os.makedirs("reports", exist_ok=True)
    open("reports/diagnostics.md", "w").write("\n".join(L) + "\n")
    return dict(markets=out, findings=len(findings), queued=len(queue), probation=demote)
