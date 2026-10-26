# Model research: walk-forward results

Generated 2026-10-20T02:25:34Z at commit `a3db0ce`. Splits (ESPN season years): explore [2015, 2020], validate [2021, 2023]; holdout [2024, 2026] untouched.

Each variant is refit every game day on games before that day and priced against one sportsbook's closing line (DraftKings where ESPN has it, else the next book in a fixed priority list). 'Blend' mixes model and de-vigged market in logit space with a weight chosen on explore only. Log-loss gain is market minus blend (positive = blend better). ROI is flat 1 unit at the closing price.

Explore gain is scored leave-one-season-out (w fit on the other explore seasons); validate gain uses the explore w. Each gain is the mean per-game log-loss improvement over the de-vigged close with its paired t statistic; the gate needs t >= 2.0. The EV threshold is the best explore ROI among thresholds with at least 100 explore bets.

| variant | market | w | thr | explore gain (t) | validate gain (t) | validate bets | validate win % | validate ROI | 95% CI | paper gate |
|---|---|---|---|---|---|---|---|---|---|---|
| base | ml | 0.10 | 0.0 | +0.0002 (+0.7) | +0.0002 (+0.5) | 137 | 40.9% (56-81) | -3.2% | -22.4% to +20.5% | fail |
| base | spread | 0.00 | none | -0.0000 (-0.9) | 0 (w = 0) | 0 |  |  |  | fail |
| base | total | 0.00 | none | +0.0000 (+1.2) | 0 (w = 0) | 0 |  |  |  | fail |
| trend | ml | 0.10 | 0.0 | +0.0002 (+0.7) | +0.0002 (+0.5) | 137 | 40.9% (56-81) | -3.2% | -22.4% to +20.5% | fail |
| trend | spread | 0.00 | none | -0.0000 (-0.9) | 0 (w = 0) | 0 |  |  |  | fail |
| trend | total | 0.00 | none | +0.0000 (+1.2) | 0 (w = 0) | 0 |  |  |  | fail |
| rest | ml | 0.10 | 0.0 | +0.0000 (+0.0) | +0.0003 (+0.9) | 142 | 40.1% (57-85) | -6.4% | -28.2% to +13.8% | fail |
| rest | spread | 0.00 | none | -0.0000 (-0.9) | 0 (w = 0) | 0 |  |  |  | fail |
| rest | total | 0.00 | none | +0.0000 (+1.2) | 0 (w = 0) | 0 |  |  |  | fail |
| hl30 | ml | 0.10 | 0.0 | +0.0001 (+0.3) | +0.0002 (+0.5) | 190 | 39.5% (75-115) | -5.7% | -24.2% to +13.6% | fail |
| hl30 | spread | 0.00 | none | -0.0000 (-0.9) | 0 (w = 0) | 0 |  |  |  | fail |
| hl30 | total | 0.00 | none | +0.0000 (+1.2) | 0 (w = 0) | 0 |  |  |  | fail |
| hl120 | ml | 0.15 | 0.0 | +0.0005 (+1.1) | +0.0000 (+0.1) | 482 | 38.8% (187-295) | -4.8% | -18.0% to +7.6% | fail |
| hl120 | spread | 0.05 | none | -0.0000 (-0.4) | -0.0001 (-0.8) | 0 |  |  |  | fail |
| hl120 | total | 0.00 | none | +0.0000 (+1.2) | 0 (w = 0) | 0 |  |  |  | fail |

A weight of 0.00 means the model added nothing over the closing price on explore: the blend is the market itself, and any ROI is the bookmaker margin.

