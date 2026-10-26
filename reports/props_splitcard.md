# Prop split cards: calibration on synthetic lines (exp-20261021-splitcard)

Pre-registered in `data/research/experiments.jsonl` (commit cbb8041) before any result was computed.
Script: `tools/splitcard_experiment.py`; raw output: `reports/props_splitcard.json`.

## Setup and the big limitation
- **No free historical prop lines exist.** Each event uses a *synthetic* line: the player's prior-10-game median of the stat, rounded to x.5 (floor(median)+0.5). Synthetic lines are not prices. This measures forecasting skill only and **cannot show betting edge**.
- Data: `box_2023` regular season only. Seasons 2024-2026 are the holdout in `config/gates.yaml`, and 2023 is the only box season outside it. So explore/validate are chronological **within 2023**: explore = before 2023-01-15 (36,336 events), validate = on or after that date (46,792 events). Thin: one season.
- Events: player-games with minutes > 0 and at least 10 prior games, for pts/reb/ast/fg3m, target P(over). Strictly point-in-time. Teammate status is "played the team's previous game". Defence rank is the opponent's allowed-per-game for the stat this season, with no positions in the data. Same-month-past-seasons is empty because only one season is used.
- Configurations tried: 3 (shrinkage k in {10, 20, 40}, chosen on explore Brier, so k = 40). Flag threshold fixed at 0.58. A by-side breakdown was added after the results as a diagnostic, not as a config.

## Results (validate, k = 40)
| forecast | Brier | log-loss |
|---|---|---|
| split card (combined) | **0.23135** | **0.65365** |
| season rate (Laplace) | 0.23170 | 0.65430 |
| last-10 rate (Laplace) | 0.23691 | 0.66466 |

- The paired per-event Brier difference against last-10 is t = -9.1; against season it is t = -7.3. These are naive t values, because events within a player-day are correlated.
- **On explore the card did NOT beat the season rate** (Brier 0.22986 vs 0.22965, t = +4.5 in the season rate's favour). So the improvement over the season rate is small and not consistent. The improvement over last-10 is consistent: last-10 hit rates are noisy and the card is better calibrated.
- Calibration (validate): the card is **overconfident at the extremes**. Predicted 0.74 hit 0.67, predicted 0.82 hit 0.70, and predicted 0.16 had an observed rate of 0.25.
- Flagged sides (P >= 0.58 or P <= 0.42): 0.651 hit rate, n = 32,162, 11,520 player-day clusters, cluster t = 42.6 vs 0.524. **This is mostly a construction artifact.** The x.5-above-median line makes "over" the minority outcome (base rate 0.42), so unders win by design: unders hit 0.664 (n = 25,370) and overs 0.604 (n = 6,792). A real book prices its line near 50/50 with vig, so this hit rate does not transfer to real prices. The naive last-10 flags also "beat" breakeven (0.625).

## Verdict
The pre-registered criteria are met on validate for Brier/log-loss and the flagged hit rate. That is not evidence of edge:
explore disagrees on the season-rate comparison, the flagged result is a synthetic-line artifact, and the card is overconfident in the tails.
Split cards ship as **watchlist information only**. Props stay `research`. The forward prop-line archive (NBA-031) is what can test them against real prices.
Holdout not touched. Pending independent review.

## Post-review calibration (2026-10-21, Skeptic review)
The calibration was fitted on explore only and evaluated once on validate. This is a 4th configuration and was not pre-registered. Cards now show `prob` (calibrated) and `prob_raw`. EV uses `prob` and names the book. Every card carries `status: research`.
- Platt fit on explore (k=40): a = 0.0235, b = 0.7852. Because b < 1, it pulls the tails toward the middle.
- Validate, calibrated: Brier 0.22908, log-loss 0.64736 (raw 0.23135 / 0.65365; season-rate baseline 0.23170 / 0.65430). Tails are closer: predictions of 0.73 hit 0.68, and predictions of 0.16 hit 0.20.
- This is still fitted to synthetic lines, so refit it on real archived lines (NBA-031) before trusting EV.
