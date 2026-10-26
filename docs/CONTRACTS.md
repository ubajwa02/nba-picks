# Data contracts between pipeline, research and dashboard

All files are produced by Python in this repo. The dashboard (site/index.html) only reads
site/data.json, which nbapicks/dashboard.py builds from these sources. Nothing is typed by hand.

## 1. Prediction rows (data/ledger/predictions*.jsonl, table `predictions`)

Unchanged columns plus these conventions:
- `prob` may be NULL when the model has no estimate (e.g. no player history). Never 0.5 as a placeholder.
- `decision` in eligible | watch | hold | reject | info. `origin` in model | signal | backtest.
- `category` in straight | parlay | lotto.
- A prediction is **versioned by content**: `pred_id = stable_id(candidate_key, line, price_dec, round(prob,3), decision, model_version)`.
  A rerun with identical inputs writes nothing; a changed price/line/probability/decision writes a new row.
  `data/state/last_predict.json["pred_ids"]` lists the rows that make up the current slate view.
- `inputs` (JSON) keys used by the dashboard:
  - `status`: market status at prediction time (research | paper | live)
  - `fair`: de-vigged market probability for this side when both sides are known, else null
  - `implied`: 1 / price_dec
  - `price_basis`: "labelled" (book states the side) | "conservative" (DraftKings pair with unlabelled sides; price is the worse of the two, so EV/ROI are lower bounds)
  - `explain` (props): `{season: {avg, n}, last5: [values newest first], last10_avg, line_hits: {h, n}, line_hits_last10: {h, n},
     vs_opp: {h, n, avg}, exp_minutes, minutes_basis, role: "starter"|"bench"|null, opp_def: {rank, teams, allowed_pg},
     teammates_out: [names], injury_status: str|null, mean, sd, flags: [str]}`
  - `explain` (game markets): `{mu_margin, mu_total, home_rest, away_rest, home_missing: [names], away_missing: [names], availability_adj}`
  - `quality_flags`: list of strings (stale_price, injury_unresolved, conservative_price, low_sample, ...)

## 2. Backtest reports (reports/backtest_*.json)

Each file: `{"generated_at": iso, "commit": str, "runs": [Run, ...]}` where Run is:

```
{ "name": str,                 # e.g. "props-v1 pts over/under, Jan 2026 (validate)"
  "kind": "props" | "games" | "parlay",
  "market": "prop:pts" | "prop:fg3m" | "ml" | "spread" | "total" | ...,
  "model_version": str, "baseline": str,          # what it is compared to
  "split": "explore" | "validate" | "holdout" | "forward",
  "period": {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"},
  "staking": "flat 1u per bet (1u = $100)",
  "selection_rule": str,                           # e.g. "EV >= 5% at the recorded price"
  "price_basis": "closing (untimed)" | "conservative pair" | "timestamped pregame" | "none",
  "eligible": int,                                 # predictions that could be scored
  "bets": int, "wins": int, "losses": int, "pushes": int, "voids": int,
  "hit_rate": float|null, "avg_prob": float|null, "avg_price_dec": float|null, "avg_implied": float|null,
  "units_staked": float, "net_units": float, "net_dollars": float, "roi": float|null, "roi_ci": [lo, hi]|null,
  "logloss_model": float|null, "logloss_baseline": float|null, "logloss_market": float|null,
  "brier_model": float|null, "brier_market": float|null,
  "calibration": [{"lo": float, "hi": float, "n": int, "predicted": float, "observed": float}],
  "coverage": {...},                               # free-form counts: games, players, rows dropped and why
  "notes": [str] }
```

ROI fields are null when no valid historical price exists. Never fill them from assumed odds.

## 3. Research registry

`data/research/experiments.jsonl` (append-only; `registered` row before `evaluated` row),
`data/research/decisions.jsonl` (gate changes, promotions, demotions), `data/research/champion.json`
(`model_id`, `params`, and `props: {model_id, params, since, reason}` for the prop model in use).
