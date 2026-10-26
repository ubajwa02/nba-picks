# Architecture

## Flow

```
ESPN scoreboard/injuries/odds/box ─┐
MovioOdds (bet365, optional) ──────┼─> ingest ─> ledger (JSONL) ─> predict ─> qualify ─> publish (Discord, dashboard)
data/manual/signals.csv ───────────┘                 │                                      │
data/manual/wagers.csv ─────────────────────────────>│<─────────── settle <─ final box scores ┘
                                                      └─> recap, diagnose ─> research queue ─> weekly research
```

The daily workflow runs `nbapicks.pipeline` steps in order: ingest, predict, publish, settle, recap, diagnose, export. Each step is idempotent: rerunning a step on the same inputs writes nothing new.

## Ledger

`nbapicks/store.py` keeps every record as a line of JSON in `data/ledger/<table>/…jsonl` (odds and injuries partitioned by month) and replays it into in-memory SQLite with primary keys, foreign keys and CHECK constraints on load. Immutable tables (predictions, publications, wagers) reject a second record with the same key and different content; an identical record is a no-op. Changes are expressed as events (`pred_events`, `wager_events`), never edits, so the history of every pick (created, published, settled, corrected) is reconstructable.

Three records are kept strictly apart:
- **Predictions** (`origin` model, signal or backtest; `decision` eligible, watch, hold, reject or info) with the exact price, book, observation time and inputs used.
- **Publications**: what was sent where, keyed `kind:slate:mode` so a slate is never posted twice.
- **Wagers**: only what you entered as actually placed, with your FanDuel odds and stake.

## Pricing

- `models/ratings.py`: exponentially weighted ridge regression of margin and team points on team offence/defence and home court, refit each game day on prior games only (no leakage). Options: totals trend, rest/back-to-back.
- `models/availability.py`: value of missing regulars (recency-weighted box game score), an optional second-stage adjustment to margin and total in `RatingsModel` (`availability=True`). Backtests read absences from the game's box score (an upper bound: includes late scratches); live use reads the injury report.
- `monthtest.py`: walk-forward game-market report over a date range (`reports/backtest_games.{json,md}`, contract §2); refuses holdout dates without `--holdout`.
- `models/dist.py`: integer-normal distributions turn expected margin/total into win, cover and push probabilities. `props.py` uses a negative binomial for counting stats.
- `odds.py`: conversions, multiplicative and power de-vig, EV with push, `min_decimal_for_edge` (the FanDuel price at which a pick still clears its threshold).
- Model and de-vigged market can be blended in logit space; the weight is fit on explore seasons only.

## Qualification (`qualify.py`)

Checks, in order: data (fresh odds, game not imminent, no missing inputs) → price (positive EV, plausibility caps) → injuries (unresolved key-player status holds) → threshold (per-market min EV; at least half the threshold is a watch) → skeptic (book disagreement, model-market gap, EV too good to be true) → market status (a research market can never be eligible). `portfolio()` then applies daily, per-game, parlay and same-side caps. Targets of 6 straights, 2 parlays and 1 lotto are ceilings, never quotas.

Parlays (`parlay.py`) only combine legs from different games unless a same-game joint probability is simulated.

## Execution book

FanDuel Ontario has no permitted data feed. Picks show the reference book and price that produced them (DraftKings via ESPN, or bet365 via MovioOdds) and the line "FanDuel: bet only at X or better". A bet365 price is never labelled FanDuel.

## Self-improvement loop

`diagnose.py` measures calibration, drift and segment performance on settled predictions and queues at most three hypotheses in `data/research/queue.yaml`. The weekly research workflow evaluates queued challengers walk-forward, appends every run to `data/research/experiments.jsonl` (registered before evaluation), and applies `config/gates.yaml`. Promotions need the gates plus an independent review; demotions are automatic.
