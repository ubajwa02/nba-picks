# Live scorecard

Settled predictions since 2026-10-20: **101** (deduplicated). Descriptive only: tiny sample, no inference. Market prob = 1/price (includes vig).

Brier: model 0.2479 vs market-implied 0.2343 (n=101; lower is better).

## Calibration

| prob bucket | n | predicted | market | actual |
|---|---|---|---|---|
| <40% | 29 | 0.308 | 0.488 | 0.414 |
| 40-50% | 18 | 0.449 | 0.523 | 0.556 |
| 50-60% | 20 | 0.551 | 0.511 | 0.450 |
| 60-70% | 18 | 0.645 | 0.540 | 0.389 |
| >=70% | 16 | 0.739 | 0.576 | 0.750 |

## By EV bucket

| group | n | wins | win rate | units |
|---|---|---|---|---|
| EV 0-5% | 6 | 0 | 0.000 | -6.00 |
| EV 5-15% | 13 | 8 | 0.615 | +1.45 |
| EV<0 | 51 | 29 | 0.569 | +2.37 |
| EV>=15% | 31 | 13 | 0.419 | -5.62 |

## By market

| group | n | wins | win rate | units |
|---|---|---|---|---|
| ml | 28 | 14 | 0.500 | -3.44 |
| prop | 8 | 4 | 0.500 | -0.21 |
| spread | 32 | 16 | 0.500 | -1.65 |
| total | 33 | 16 | 0.485 | -2.49 |

## By decision

| group | n | wins | win rate | units |
|---|---|---|---|---|
| hold | 35 | 13 | 0.371 | -9.62 |
| reject | 53 | 29 | 0.547 | +0.37 |
| watch | 13 | 8 | 0.615 | +1.45 |

## Posted leans (1u flat)

Record 9-5-0, +2.58u, pending 5.

| slate | lean | price | stat/score | result | units |
|---|---|---|---|---|---|
| 2026-10-20 | Pistons ML | +102 | BOS 113 @ DET 121 | win | +1.02 |
| 2026-10-20 | Pistons +1.5 | -110 | BOS 113 @ DET 121 | win | +0.91 |
| 2026-10-20 | Spurs ML | -112 | OKC 116 @ SA 104 | loss | -1.00 |
| 2026-10-20 | Spurs -1.5 | -102 | OKC 116 @ SA 104 | loss | -1.00 |
| 2026-10-21 | CHA-BKN u219.5 | -110 | CHA 110 @ BKN 103 | win | +0.91 |
| 2026-10-21 | MIA ML | -119 | MIN 131 @ MIA 106 | loss | -1.00 |
| 2026-10-21 | LAC ML | -185 | SAC 96 @ LAC 121 | win | +0.54 |
| 2026-10-21 | LAC -4.5 | -117 | SAC 96 @ LAC 121 | win | +0.85 |
| 2026-10-21 | SAC-LAC u227.5 | -111 | SAC 96 @ LAC 121 | win | +0.90 |
| 2026-10-21 | Trae Young o19.5 pts | +105 | 20 | win | +1.05 |
| 2026-10-21 | Myles Turner o9.5 pts | -130 | 11 | win | +0.77 |
| 2026-10-21 | Jrue Holiday o2.5 reb | -160 | 4 | win | +0.62 |
| 2026-10-21 | Scoot Henderson o2.5 ast | -130 | 1 | loss | -1.00 |
| 2026-10-21 | Jabari Smith Jr. o6.5 reb | +140 | 5 | loss | -1.00 |
| 2026-10-22 | Jaylen Brown o19.5 pts | -135 | None | pending | +0.00 |
| 2026-10-22 | Anfernee Simons o1.5 fg3m | -150 | None | pending | +0.00 |
| 2026-10-22 | Tyrese Maxey o24.5 pts | +125 | None | pending | +0.00 |
| 2026-10-22 | Joel Embiid o19.5 pts | -210 | None | pending | +0.00 |
| 2026-10-22 | VJ Edgecombe o9.5 pts | -150 | None | pending | +0.00 |

## Rows

| market | pick | decision | model p | book p | EV | result |
|---|---|---|---|---|---|---|
| prop | Jerami Grant fg3m over 1.5 (401909838) | hold | 0.669 | 0.435 | +0.540 | win |
| total | under 234.5 (401909092) | hold | 0.771 | 0.512 | +0.505 | win |
| total | under 231.5 (401909841) | hold | 0.776 | 0.526 | +0.475 | win |
| total | under 237.5 (401909837) | hold | 0.747 | 0.512 | +0.459 | win |
| total | under 233.5 (401909092) | hold | 0.754 | 0.519 | +0.452 | win |
| total | under 234.5 (401909834) | hold | 0.749 | 0.519 | +0.443 | loss |
| total | under 238.5 (401909835) | hold | 0.746 | 0.524 | +0.424 | loss |
| total | under 232.5 (401909089) | hold | 0.757 | 0.535 | +0.415 | win |
| ml | home (401909839) | hold | 0.615 | 0.435 | +0.414 | loss |
| total | under 240.5 (401909091) | hold | 0.738 | 0.535 | +0.379 | win |
| total | under 239.5 (401909839) | hold | 0.720 | 0.524 | +0.375 | loss |
| ml | away (401909837) | hold | 0.295 | 0.217 | +0.355 | loss |
| spread | away -1.5 (401909836) | hold | 0.704 | 0.519 | +0.355 | win |
| ml | away (401909836) | hold | 0.732 | 0.541 | +0.352 | win |
| spread | home 3.5 (401909839) | hold | 0.704 | 0.526 | +0.338 | win |
| prop | Josh Giddey ast over 9.5 (401909837) | hold | 0.637 | 0.481 | +0.324 | loss |
| total | under 242.5 (401909838) | hold | 0.687 | 0.526 | +0.307 | win |
| ml | away (401909835) | hold | 0.520 | 0.398 | +0.304 | loss |
| prop | Cam Spencer fg3m over 1.5 (401909838) | hold | 0.531 | 0.408 | +0.302 | loss |
| total | under 231.5 (401909090) | hold | 0.693 | 0.535 | +0.295 | win |
| spread | home -4.5 (401909089) | hold | 0.678 | 0.524 | +0.295 | loss |
| total | under 230.5 (401909840) | hold | 0.686 | 0.535 | +0.282 | loss |
| spread | away 4.5 (401909835) | hold | 0.646 | 0.512 | +0.261 | loss |
| ml | away (401909840) | hold | 0.286 | 0.227 | +0.260 | loss |
| total | under 221.5 (401909088) | hold | 0.638 | 0.512 | +0.245 | loss |
| prop | Cedric Coward fg3m under 1.5 (401909838) | hold | 0.573 | 0.461 | +0.243 | win |
| ml | home (401909089) | hold | 0.788 | 0.643 | +0.225 | loss |
| total | under 220.5 (401909088) | hold | 0.617 | 0.524 | +0.178 | loss |
| spread | away 10.5 (401909837) | hold | 0.611 | 0.524 | +0.166 | loss |
| spread | home 1.5 (401909090) | hold | 0.615 | 0.528 | +0.164 | loss |
| ml | home (401909090) | hold | 0.584 | 0.505 | +0.156 | loss |
| total | under 227.5 (401909842) | watch | 0.598 | 0.526 | +0.136 | win |
| ml | home (401909088) | watch | 0.562 | 0.495 | +0.135 | win |
| spread | home 1.5 (401909088) | watch | 0.594 | 0.524 | +0.133 | win |
| spread | home -4.5 (401909842) | watch | 0.603 | 0.539 | +0.119 | win |
| ml | home (401909842) | watch | 0.724 | 0.649 | +0.115 | win |
| spread | away 9.5 (401909840) | hold | 0.570 | 0.512 | +0.113 | loss |
| spread | away 6.5 (401909092) | hold | 0.569 | 0.517 | +0.102 | loss |
| total | under 219.5 (401909836) | watch | 0.577 | 0.524 | +0.101 | win |
| prop | Keyonte George pts over 19.5 (401909838) | watch | 0.609 | 0.556 | +0.097 | win |
| spread | home -1.5 (401909090) | watch | 0.551 | 0.505 | +0.092 | loss |
| ml | away (401909092) | hold | 0.375 | 0.345 | +0.089 | loss |
| prop | Immanuel Quickley ast under 6.5 (401909837) | hold | 0.658 | 0.606 | +0.086 | loss |
| prop | Jaren Jackson Jr. ast under 2.5 (401909838) | watch | 0.694 | 0.658 | +0.055 | win |
| prop | Jaylen Wells fg3m over 1.5 (401909838) | watch | 0.622 | 0.595 | +0.045 | loss |
| spread | home -2.5 (401909090) | watch | 0.519 | 0.507 | +0.022 | loss |
| ml | home (401909091) | watch | 0.562 | 0.550 | +0.022 | loss |
| spread | home -1.5 (401909091) | watch | 0.529 | 0.519 | +0.019 | loss |
| spread | away 2.5 (401909841) | reject | 0.516 | 0.512 | +0.008 | loss |
| ml | away (401909841) | reject | 0.451 | 0.450 | +0.001 | loss |
| spread | away 2.5 (401909834) | reject | 0.528 | 0.528 | -0.000 | win |
| ml | away (401909834) | reject | 0.463 | 0.469 | -0.014 | win |
| ml | home (401909838) | reject | 0.543 | 0.552 | -0.016 | win |
| spread | home -1.5 (401909838) | reject | 0.510 | 0.526 | -0.030 | win |
| ml | home (401909834) | reject | 0.537 | 0.565 | -0.050 | loss |
| spread | away 1.5 (401909838) | reject | 0.490 | 0.519 | -0.056 | loss |
| ml | away (401909838) | reject | 0.457 | 0.488 | -0.063 | loss |
| ml | home (401909841) | reject | 0.549 | 0.587 | -0.065 | win |
| spread | home -2.5 (401909841) | reject | 0.484 | 0.528 | -0.085 | win |
| spread | home -2.5 (401909834) | reject | 0.472 | 0.517 | -0.087 | loss |
| spread | away 2.5 (401909090) | reject | 0.481 | 0.535 | -0.100 | win |
| ml | home (401909092) | reject | 0.625 | 0.697 | -0.104 | win |
| spread | away 1.5 (401909091) | reject | 0.471 | 0.528 | -0.108 | win |
| ml | away (401909091) | reject | 0.438 | 0.495 | -0.114 | win |
| ml | home (401909840) | reject | 0.714 | 0.811 | -0.120 | win |
| ml | home (401909837) | reject | 0.705 | 0.815 | -0.134 | win |
| spread | away 1.5 (401909090) | reject | 0.449 | 0.535 | -0.161 | win |
| spread | home -6.5 (401909092) | reject | 0.431 | 0.528 | -0.185 | win |
| spread | home -9.5 (401909840) | reject | 0.430 | 0.531 | -0.190 | win |
| total | over 219.5 (401909836) | reject | 0.423 | 0.524 | -0.192 | loss |
| ml | away (401909088) | reject | 0.438 | 0.550 | -0.203 | loss |
| spread | away 4.5 (401909842) | reject | 0.397 | 0.505 | -0.214 | loss |
| spread | away -1.5 (401909088) | reject | 0.406 | 0.524 | -0.224 | loss |
| total | over 227.5 (401909842) | reject | 0.402 | 0.519 | -0.225 | loss |
| ml | away (401909090) | reject | 0.416 | 0.541 | -0.231 | win |
| ml | home (401909835) | reject | 0.480 | 0.636 | -0.245 | win |
| spread | home -10.5 (401909837) | reject | 0.389 | 0.519 | -0.250 | win |
| spread | away -1.5 (401909090) | reject | 0.385 | 0.519 | -0.259 | win |
| total | over 220.5 (401909088) | reject | 0.383 | 0.524 | -0.269 | win |
| ml | away (401909842) | reject | 0.276 | 0.383 | -0.279 | loss |
| total | over 221.5 (401909088) | reject | 0.362 | 0.535 | -0.322 | win |
| spread | home -4.5 (401909835) | reject | 0.354 | 0.531 | -0.333 | win |
| total | over 229.5 (401909090) | reject | 0.346 | 0.535 | -0.353 | loss |
| total | over 230.5 (401909090) | reject | 0.326 | 0.512 | -0.363 | loss |
| ml | away (401909839) | reject | 0.385 | 0.606 | -0.365 | win |
| spread | away 4.5 (401909089) | reject | 0.322 | 0.519 | -0.381 | win |
| total | over 230.5 (401909840) | reject | 0.314 | 0.512 | -0.387 | win |
| total | over 242.5 (401909838) | reject | 0.313 | 0.512 | -0.390 | loss |
| total | over 231.5 (401909090) | reject | 0.307 | 0.522 | -0.411 | loss |
| spread | away -3.5 (401909839) | reject | 0.296 | 0.519 | -0.429 | loss |
| spread | home 1.5 (401909836) | reject | 0.296 | 0.528 | -0.439 | loss |
| total | over 239.5 (401909839) | reject | 0.280 | 0.512 | -0.454 | win |
| total | over 239.5 (401909091) | reject | 0.280 | 0.524 | -0.465 | loss |
| ml | away (401909089) | reject | 0.212 | 0.397 | -0.465 | win |
| ml | home (401909836) | reject | 0.268 | 0.505 | -0.469 | loss |
| total | over 233.5 (401909834) | reject | 0.268 | 0.535 | -0.499 | win |
| total | over 238.5 (401909835) | reject | 0.254 | 0.524 | -0.515 | win |
| total | over 237.5 (401909837) | reject | 0.253 | 0.528 | -0.521 | loss |
| total | over 232.5 (401909089) | reject | 0.243 | 0.512 | -0.525 | loss |
| total | over 233.5 (401909092) | reject | 0.246 | 0.524 | -0.530 | loss |
| total | over 231.5 (401909841) | reject | 0.224 | 0.519 | -0.568 | loss |
