# Model research: walk-forward results

Generated 2026-11-22T12:09:11Z at commit `f2b15cd`. Splits (ESPN season years): explore [2015, 2020], validate [2021, 2023]; holdout [2024, 2026] untouched.

Each variant is refit every game day on games before that day and priced against one sportsbook's closing line (DraftKings where ESPN has it, else the next book in a fixed priority list). 'Blend' mixes model and de-vigged market in logit space with a weight chosen on explore only. Log-loss gain is market minus blend (positive = blend better). ROI is flat 1 unit at the closing price.

Explore gain is scored leave-one-season-out (w fit on the other explore seasons); validate gain uses the explore w. Each gain is the mean per-game log-loss improvement over the de-vigged close with its paired t statistic; the gate needs t >= 2.0. The EV threshold is the best explore ROI among thresholds with at least 100 explore bets.

| variant | market | w | thr | explore gain (t) | validate gain (t) | validate bets | validate win % | validate ROI | 95% CI | paper gate |
|---|---|---|---|---|---|---|---|---|---|---|
| hl30 | ml | 0.10 | 0.0 | +0.0001 (+0.3) | +0.0002 (+0.5) | 190 | 39.5% (75-115) | -5.7% | -24.2% to +13.6% | fail |
| hl30 | spread | 0.00 | none | -0.0000 (-1.5) | 0 (w = 0) | 0 |  |  |  | fail |
| hl30 | total | 0.00 | none | +0.0000 (+1.3) | 0 (w = 0) | 0 |  |  |  | fail |

A weight of 0.00 means the model added nothing over the closing price on explore: the blend is the market itself, and any ROI is the bookmaker margin.

