# What the system has learned from its own results

Written by `nbapicks/learn.py` after every settle that grades something new. How it works: `docs/LEARNING.md`.

**Through 2026-11-16: 8,152 graded DraftKings props on 24 slates.**

**No correction is in force.** The DraftKings price with the margin removed is still the best estimate here: nothing tested below beat it reliably on slates it had not seen.

## How good the market price was

The fair chance is the last pair of prices stored before tip with the book's margin removed (half of them within 2.4 hours of tip).

- Overs won 47.4%. The fair chance said 49.3%: a difference of -1.9 points (standard error 0.6).
- Best-fitting constant -0.077 (se 0.026) and slope 1.05 (se 0.12) on the log-odds. 0 and 1 would mean the price was right on average. This is measured on the same slates it is fitted on, so it flatters any pattern; the table below is the honest test.
- Log loss of the fair chance: 0.6856 (a coin flip scores 0.6931).

## Corrections, scored on slates they had not seen

Each correction is refitted before every slate on the earlier slates only, then scored on that slate. Evidence is how many standard errors its adjustments leaned the way the results went (about 0 when it knows nothing). Gain is the log loss it saved per prop against the plain fair chance (above 0 is better).

| correction | unseen slates | props | evidence | gain | gain, older half | gain, newer half | slates it helped | status |
|---|---|---|---|---|---|---|---|---|
| shift | 19 | 6,761 | +2.25 | +0.00034 | +0.00149 | -0.00086 | 11 of 19 | not in force: evidence +2.25 is under 3.00; no gain on the newer half of the unseen slates |
| shift_slope | 19 | 6,761 | +2.10 | +0.00012 | +0.00113 | -0.00095 | 11 of 19 | not in force: evidence +2.10 is under 3.00; no gain on the newer half of the unseen slates |
| stat_shift | 19 | 6,761 | +2.19 | +0.00032 | +0.00168 | -0.00111 | 10 of 19 | not in force: evidence +2.19 is under 3.00; no gain on the newer half of the unseen slates |
| recent_shift | 19 | 6,761 | +2.35 | +0.00051 | +0.00143 | -0.00046 | 11 of 19 | not in force: evidence +2.35 is under 3.00; no gain on the newer half of the unseen slates |
| model:props-v0 | 10 | 3,282 | +0.30 | -0.00065 | +0.00090 | -0.00225 | 4 of 10 | not in force: needs 15 unseen slates and 3,000 props (has 10 and 3,282); evidence +0.30 is under 3.00; it did not lower log loss on unseen slates |
| model:props-v1 | 3 | 917 | +1.18 | +0.00188 | +0.00085 | +0.00290 | 2 of 3 | not in force: needs 15 unseen slates and 3,000 props (has 3 and 917); evidence +1.18 is under 3.00 |

The gate: evidence of 3.00 or more on at least 15 unseen slates and 3,000 props, with a gain overall and on the newer half. A correction in force is dropped when its evidence falls under 2.00 or the gain goes. The bar is 3 and not 2 because it is checked after every slate. When several pass, `recent_shift` is used, because it lets go soonest when a bias ends, unless another saved 1.5 times as much per prop.

## Simple rules at the last price before tip

Flat 1 unit on every prop a rule would take. Nothing is fitted, so every slate counts. ROI is profit per unit staked; t is ROI over its day-clustered standard error.

| rule | bets | won | average price | ROI | se | t | ROI, last 10 slates |
|---|---|---|---|---|---|---|---|
| every Over | 8,152 | 47.4% | 1.93 | -10.1% | 1.2 | -8.41 | -6.9% on 3,292 |
| every Under | 8,152 | 52.6% | 1.87 | -2.8% | 1.2 | -2.41 | -6.1% on 3,292 |
| every pts Under | 2,360 | 53.1% | 1.89 | -0.1% | 1.5 | -0.08 | -3.7% on 949 |
| every reb Under | 2,208 | 52.0% | 1.86 | -4.4% | 1.8 | -2.43 | -2.3% on 893 |
| every ast Under | 1,684 | 52.5% | 1.88 | -2.6% | 1.9 | -1.39 | -6.0% on 688 |
| every fg3m Under | 1,900 | 52.6% | 1.86 | -4.6% | 2.2 | -2.03 | -13.5% on 762 |
| the favourite (fair chance 55% or more) | 2,994 | 59.2% | 1.61 | -5.0% | 1.8 | -2.85 | -4.5% on 1,204 |
| the underdog (fair chance 45% or less) | 2,994 | 40.8% | 2.25 | -8.3% | 2.4 | -3.44 | -8.9% on 1,204 |
| model edge of 5% or more at the price | 4,246 | 50.0% | 1.91 | -5.9% | 2.1 | -2.78 | -9.0% on 2,015 |
| model 60% or more at -200 or longer (the pick rule on main) | 3,191 | 54.4% | 1.79 | -3.4% | 2.2 | -1.52 | -6.7% on 1,535 |
| the same, within 10 points of the market | 894 | 59.7% | 1.65 | -1.8% | 3.2 | -0.57 | -4.1% on 393 |

No rule clears the bar (t of 3 or more on 300 or more bets).

## Posted picks against later prices

Each posted prop pick is matched to the DraftKings quote it was posted on and compared with the last quote stored at the same line before tip, when there is a later one. The market coming toward a pick after it is posted is the earliest sign of a real edge. Move is DraftKings' price for the pick's side when posted against its later price (above 0: that side got shorter). Value is what the pick was worth per unit if the later price was right; a pick with no edge is worth the book margin.

| source | picks | matched to a quote | with a later price | market moved toward / not / away | average move | value at the later fair chance | book margin there | main line changed |
|---|---|---|---|---|---|---|---|---|
| all | 139 | 114 | 54 | 21 / 10 / 23 | -0.1% (se 0.5) | -6.5% (se 0.5) | -6.5% | 28 |
| props_v1 | 123 | 114 | 54 | 21 / 10 / 23 | -0.1% (se 0.5) | -6.5% (se 0.5) | -6.5% | 28 |
| split_card | 16 | 0 | 0 | 0 / 0 / 0 | n/a | n/a | n/a | 0 |

A change of the main line is counted but not compared: DraftKings moves between neighbouring lines (Over 2.5 at -170, then Under 3.5 at -170) without changing its view.
7 picks were recorded at the price of the other side (before the sides were labelled); their own side's price is used here.
