# Prop backtest (walk-forward)

Generated 2026-10-22T22:36:28Z at commit cadd253-dirty by `python -m nbapicks.propbacktest`. Machine-readable: reports/backtest_props.json (docs/CONTRACTS.md §2).

## 2025-10-01 .. 2026-01-31 (validate); price basis: none

| stat | model | n | log loss | Brier | baseline | gain vs baseline | paired t (day-clustered) | bets | ROI |
|---|---|---|---|---|---|---|---|---|---|
| ast | props-v0 | 13755 | 0.66381 | 0.23463 | naive | +0.00693 | 2.24 (2.03) | 0 | null |
| ast | splitcard | 13755 | 0.66638 | 0.23647 | props-v0 | -0.00257 | -0.86 (-0.81) | 0 | null |
| ast | props-v1 | 13755 | 0.63952 | 0.22444 | props-v0 | +0.02428 | 8.91 (7.71) | 0 | null |
| ast | naive | 13755 | 0.67073 | 0.23772 | props-v0 | -0.00693 | -2.24 (-2.03) | 0 | null |
| fg3m | props-v0 | 13755 | 0.63303 | 0.20692 | naive | -0.04134 | -4.72 (-4.78) | 0 | null |
| fg3m | splitcard | 13755 | 0.5901 | 0.20524 | props-v0 | +0.04292 | 4.82 (4.9) | 0 | null |
| fg3m | props-v1 | 13755 | 0.57886 | 0.19991 | props-v0 | +0.05417 | 6.09 (6.13) | 0 | null |
| fg3m | naive | 13755 | 0.59169 | 0.20544 | props-v0 | +0.04134 | 4.72 (4.78) | 0 | null |
| pts | props-v0 | 13755 | 0.68236 | 0.24452 | naive | +0.00848 | 3.43 (2.9) | 0 | null |
| pts | splitcard | 13755 | 0.68669 | 0.24622 | props-v0 | -0.00432 | -1.87 (-1.62) | 0 | null |
| pts | props-v1 | 13755 | 0.66069 | 0.23403 | props-v0 | +0.02167 | 9.41 (7.78) | 0 | null |
| pts | naive | 13755 | 0.69084 | 0.24779 | props-v0 | -0.00848 | -3.43 (-2.9) | 0 | null |
| reb | props-v0 | 13755 | 0.67306 | 0.24011 | naive | +0.00197 | 0.9 (0.92) | 0 | null |
| reb | splitcard | 13755 | 0.67188 | 0.23936 | props-v0 | +0.00118 | 0.57 (0.58) | 0 | null |
| reb | props-v1 | 13755 | 0.64849 | 0.22874 | props-v0 | +0.02457 | 11.62 (9.73) | 0 | null |
| reb | naive | 13755 | 0.67503 | 0.24046 | props-v0 | -0.00197 | -0.9 (-0.92) | 0 | null |

Coverage: 730 games, 15780 player-games played, 13757 scored per stat after the subsample (players with >= 10 prior games and >= 10 mpg over their last 10 (point in time); every such player-game, DNPs excluded); dropped 709 with < 10 prior games and 1314 under 10 mpg. Lines: synthetic floor(median of previous 10 games)+0.5; P(over) scored.

## 2025-10-21 .. 2025-11-30 (validate); price basis: conservative pair

| stat | model | n | log loss | Brier | baseline | gain vs baseline | paired t (day-clustered) | bets | ROI |
|---|---|---|---|---|---|---|---|---|---|
| ast | props-v0 | 2225 | 0.72255 | 0.26172 | naive | +0.01416 | 2.0 (1.77) | 920 | -8.8% |
| ast | splitcard | 2225 | 0.71977 | 0.26128 | props-v0 | +0.00277 | 0.41 (0.36) | 970 | -9.9% |
| ast | props-v1 | 2225 | 0.70023 | 0.25297 | props-v0 | +0.02232 | 4.44 (3.94) | 661 | -8.4% |
| ast | naive | 2225 | 0.73671 | 0.26756 | props-v0 | -0.01416 | -2.0 (-1.77) | 1128 | -10.3% |
| fg3m | props-v0 | 2436 | 0.69976 | 0.25192 | naive | +0.00175 | 0.31 (0.27) | 844 | -8.7% |
| fg3m | splitcard | 2436 | 0.69244 | 0.24956 | props-v0 | +0.00732 | 1.32 (1.1) | 645 | -6.7% |
| fg3m | props-v1 | 2436 | 0.67677 | 0.2421 | props-v0 | +0.02299 | 5.14 (5.04) | 522 | -0.1% |
| fg3m | naive | 2436 | 0.7015 | 0.25312 | props-v0 | -0.00175 | -0.31 (-0.27) | 885 | -7.6% |
| pts | props-v0 | 3960 | 0.73645 | 0.26698 | naive | +0.00464 | 0.81 (0.77) | 2415 | -4.0% |
| pts | splitcard | 3960 | 0.72462 | 0.26399 | props-v0 | +0.01184 | 2.15 (1.88) | 2314 | -6.6% |
| pts | props-v1 | 3960 | 0.70973 | 0.25659 | props-v0 | +0.02672 | 5.5 (5.16) | 1837 | -4.0% |
| pts | naive | 3960 | 0.74109 | 0.27024 | props-v0 | -0.00464 | -0.81 (-0.77) | 2579 | -6.3% |
| reb | props-v0 | 3269 | 0.72183 | 0.26175 | naive | -0.00558 | -1.07 (-0.99) | 1474 | -8.0% |
| reb | splitcard | 3269 | 0.70426 | 0.25477 | props-v0 | +0.01757 | 3.47 (3.23) | 1164 | -4.8% |
| reb | props-v1 | 3269 | 0.69355 | 0.24911 | props-v0 | +0.02828 | 5.77 (6.1) | 896 | -0.7% |
| reb | naive | 3269 | 0.71625 | 0.25956 | props-v0 | +0.00558 | 1.07 (0.99) | 1468 | -7.7% |

Coverage: 299 games, 6542 player-games played, 5486 scored per stat after the subsample (players with >= 10 prior games and >= 10 mpg over their last 10 (point in time); every such player-game, DNPs excluded); dropped 542 with < 10 prior games and 514 under 10 mpg. Lines: real pregame lines.

## 2026-01-01 .. 2026-01-31 (validate); price basis: none

| stat | model | n | log loss | Brier | baseline | gain vs baseline | paired t (day-clustered) | bets | ROI |
|---|---|---|---|---|---|---|---|---|---|
| ast | props-v0 | 4471 | 0.65713 | 0.23257 | naive | +0.00880 | 2.22 (2.17) | 0 | null |
| ast | splitcard | 4471 | 0.66359 | 0.23495 | props-v0 | -0.00646 | -1.72 (-1.92) | 0 | null |
| ast | props-v1 | 4471 | 0.6367 | 0.22325 | props-v0 | +0.02043 | 6.93 (9.92) | 0 | null |
| ast | naive | 4471 | 0.66593 | 0.23517 | props-v0 | -0.00880 | -2.22 (-2.17) | 0 | null |
| fg3m | props-v0 | 4471 | 0.62867 | 0.20606 | naive | -0.04085 | -2.78 (-3.17) | 0 | null |
| fg3m | splitcard | 4471 | 0.5894 | 0.20466 | props-v0 | +0.03927 | 2.62 (3.09) | 0 | null |
| fg3m | props-v1 | 4471 | 0.57598 | 0.19843 | props-v0 | +0.05268 | 3.5 (4.45) | 0 | null |
| fg3m | naive | 4471 | 0.58782 | 0.20372 | props-v0 | +0.04085 | 2.78 (3.17) | 0 | null |
| pts | props-v0 | 4471 | 0.68086 | 0.24389 | naive | +0.00751 | 1.86 (2.2) | 0 | null |
| pts | splitcard | 4471 | 0.68757 | 0.24665 | props-v0 | -0.00671 | -1.71 (-2.1) | 0 | null |
| pts | props-v1 | 4471 | 0.66365 | 0.23569 | props-v0 | +0.01721 | 4.93 (5.41) | 0 | null |
| pts | naive | 4471 | 0.68837 | 0.24678 | props-v0 | -0.00751 | -1.86 (-2.2) | 0 | null |
| reb | props-v0 | 4471 | 0.67143 | 0.23929 | naive | +0.00338 | 0.95 (0.8) | 0 | null |
| reb | splitcard | 4471 | 0.67273 | 0.23956 | props-v0 | -0.00129 | -0.38 (-0.33) | 0 | null |
| reb | props-v1 | 4471 | 0.65199 | 0.23026 | props-v0 | +0.01945 | 6.08 (5.02) | 0 | null |
| reb | naive | 4471 | 0.67482 | 0.23999 | props-v0 | -0.00338 | -0.95 (-0.8) | 0 | null |

Coverage: 233 games, 4973 player-games played, 4471 scored per stat after the subsample (players with >= 10 prior games and >= 10 mpg over their last 10 (point in time); every such player-game, DNPs excluded); dropped 63 with < 10 prior games and 439 under 10 mpg. Lines: synthetic floor(median of previous 10 games)+0.5; P(over) scored.

Positive gain = lower log loss than the baseline on the same events. ROI is null where no historical price exists; it is never filled from assumed odds.
