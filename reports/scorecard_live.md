# Live scorecard

Settled predictions since 2026-10-20: **876** (deduplicated). Descriptive only: tiny sample, no inference. Market prob = 1/price (includes vig).

Brier: model 0.1528 vs market-implied 0.1503 (n=876; lower is better).

## Calibration

| prob bucket | n | predicted | market | actual |
|---|---|---|---|---|
| <40% | 458 | 0.146 | 0.179 | 0.114 |
| 40-50% | 113 | 0.458 | 0.514 | 0.504 |
| 50-60% | 100 | 0.543 | 0.565 | 0.400 |
| 60-70% | 84 | 0.650 | 0.627 | 0.619 |
| >=70% | 121 | 0.817 | 0.817 | 0.802 |

## By EV bucket

| group | n | wins | win rate | units |
|---|---|---|---|---|
| EV 0-5% | 17 | 6 | 0.353 | -6.02 |
| EV 5-15% | 26 | 15 | 0.577 | +0.58 |
| EV<0 | 126 | 65 | 0.516 | -8.54 |
| EV>=15% | 42 | 21 | 0.500 | -1.71 |

## By market

| group | n | wins | win rate | units |
|---|---|---|---|---|
| ml | 32 | 16 | 0.500 | -4.41 |
| prop | 769 | 245 | 0.319 | -269.98 |
| spread | 36 | 18 | 0.500 | -1.75 |
| total | 39 | 19 | 0.487 | -2.74 |

## By decision

| group | n | wins | win rate | units |
|---|---|---|---|---|
| hold | 60 | 28 | 0.467 | -7.58 |
| reject | 803 | 262 | 0.326 | -272.75 |
| watch | 13 | 8 | 0.615 | +1.45 |

## Posted leans (1u flat)

Record 16-9-0, +4.62u, pending 0.

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
| 2026-10-22 | Jaylen Brown o19.5 pts | -135 | 21 | win | +0.74 |
| 2026-10-22 | Anfernee Simons o1.5 fg3m | -150 | 0 | loss | -1.00 |
| 2026-10-22 | Tyrese Maxey o24.5 pts | +125 | 32 | win | +1.25 |
| 2026-10-22 | Joel Embiid o19.5 pts | -210 | 24 | win | +0.48 |
| 2026-10-22 | VJ Edgecombe o9.5 pts | -150 | 11 | win | +0.67 |
| 2026-10-23 | Jrue Holiday o3.5 ast | -119 | 8 | win | +0.84 |
| 2026-10-23 | Marcus Smart o7.5 pts | -114 | 5 | loss | -1.00 |
| 2026-10-23 | Rui Hachimura u5.5 reb | -119 | 6 | loss | -1.00 |
| 2026-10-23 | Saddiq Bey o3.5 reb | -135 | 3 | loss | -1.00 |
| 2026-10-23 | Sion James u7.5 pts | -116 | 3 | win | +0.86 |
| 2026-10-23 | Tre Jones o9.5 pts | +120 | 11 | win | +1.20 |

## Rows

| market | pick | decision | model p | book p | EV | result |
|---|---|---|---|---|---|---|
| prop | Jaylon Tyson pts under 9.5 (401909093) | hold | 0.902 | 0.556 | +0.624 | win |
| prop | Jerami Grant fg3m over 1.5 (401909838) | hold | 0.669 | 0.435 | +0.540 | win |
| total | under 234.5 (401909092) | hold | 0.771 | 0.512 | +0.505 | win |
| total | under 231.5 (401909841) | hold | 0.776 | 0.526 | +0.475 | win |
| total | under 237.5 (401909837) | hold | 0.747 | 0.512 | +0.459 | win |
| total | under 233.5 (401909092) | hold | 0.754 | 0.519 | +0.452 | win |
| total | under 234.5 (401909834) | hold | 0.749 | 0.519 | +0.443 | loss |
| prop | Kentavious Caldwell-Pope pts over 5.5 (401909093) | hold | 0.763 | 0.535 | +0.426 | loss |
| total | under 238.5 (401909835) | hold | 0.746 | 0.524 | +0.424 | loss |
| total | under 237.5 (401909093) | hold | 0.744 | 0.524 | +0.420 | win |
| total | under 232.5 (401909089) | hold | 0.757 | 0.535 | +0.415 | win |
| ml | home (401909839) | hold | 0.615 | 0.435 | +0.414 | loss |
| total | under 236.5 (401909093) | hold | 0.726 | 0.522 | +0.392 | win |
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
| prop | James Harden ast under 6.5 (401909093) | hold | 0.621 | 0.490 | +0.266 | win |
| spread | away 4.5 (401909835) | hold | 0.646 | 0.512 | +0.261 | loss |
| ml | away (401909840) | hold | 0.286 | 0.227 | +0.260 | loss |
| prop | Alex Caruso pts over 6.5 (401909094) | hold | 0.697 | 0.556 | +0.255 | win |
| total | under 221.5 (401909088) | hold | 0.638 | 0.512 | +0.245 | loss |
| total | under 236.5 (401909094) | hold | 0.648 | 0.522 | +0.243 | win |
| prop | Cedric Coward fg3m under 1.5 (401909838) | hold | 0.573 | 0.461 | +0.243 | win |
| prop | Anfernee Simons pts over 9.5 (401909093) | hold | 0.680 | 0.552 | +0.230 | loss |
| ml | home (401909089) | hold | 0.788 | 0.643 | +0.225 | loss |
| prop | Kentavious Caldwell-Pope pts over 6.5 (401909093) | hold | 0.690 | 0.575 | +0.201 | loss |
| prop | Alex Caruso reb over 2.5 (401909094) | hold | 0.679 | 0.568 | +0.195 | win |
| prop | VJ Edgecombe pts over 10.5 (401909093) | hold | 0.675 | 0.568 | +0.188 | win |
| total | under 220.5 (401909088) | hold | 0.617 | 0.524 | +0.178 | loss |
| spread | away 10.5 (401909837) | hold | 0.611 | 0.524 | +0.166 | loss |
| spread | home 1.5 (401909090) | hold | 0.615 | 0.528 | +0.164 | loss |
| ml | home (401909090) | hold | 0.584 | 0.505 | +0.156 | loss |
| prop | Anfernee Simons pts over 10.5 (401909093) | hold | 0.625 | 0.546 | +0.143 | loss |
| total | under 227.5 (401909842) | watch | 0.598 | 0.526 | +0.136 | win |
| ml | home (401909088) | watch | 0.562 | 0.495 | +0.135 | win |
| spread | home 1.5 (401909088) | watch | 0.594 | 0.524 | +0.133 | win |
| prop | VJ Edgecombe pts over 11.5 (401909093) | hold | 0.624 | 0.556 | +0.124 | loss |
| prop | Cason Wallace reb under 3.5 (401909094) | hold | 0.710 | 0.633 | +0.121 | win |
| spread | home -4.5 (401909842) | watch | 0.603 | 0.539 | +0.119 | win |
| ml | home (401909842) | watch | 0.724 | 0.649 | +0.115 | win |
| spread | away 9.5 (401909840) | hold | 0.570 | 0.512 | +0.113 | loss |
| prop | Ajay Mitchell fg3m under 1.5 (401909094) | hold | 0.771 | 0.699 | +0.103 | win |
| spread | away 6.5 (401909092) | hold | 0.569 | 0.517 | +0.102 | loss |
| total | under 219.5 (401909836) | watch | 0.577 | 0.524 | +0.101 | win |
| prop | Jaylen Brown pts over 20.5 (401909093) | hold | 0.607 | 0.552 | +0.098 | win |
| prop | Keyonte George pts over 19.5 (401909838) | watch | 0.609 | 0.556 | +0.097 | win |
| prop | Jamal Murray reb over 4.5 (401909094) | hold | 0.492 | 0.448 | +0.096 | win |
| spread | home -1.5 (401909090) | watch | 0.551 | 0.505 | +0.092 | loss |
| ml | away (401909092) | hold | 0.375 | 0.345 | +0.089 | loss |
| prop | Immanuel Quickley ast under 6.5 (401909837) | hold | 0.658 | 0.606 | +0.086 | loss |
| prop | LeBron James reb under 6.5 (401909093) | hold | 0.518 | 0.478 | +0.083 | loss |
| prop | Christian Braun ast over 1.5 (401909094) | hold | 0.654 | 0.610 | +0.072 | loss |
| prop | LeBron James pts over 16.5 (401909093) | hold | 0.595 | 0.559 | +0.065 | win |
| prop | Joel Embiid ast over 4.5 (401909093) | hold | 0.484 | 0.455 | +0.064 | loss |
| prop | Jamal Murray pts over 21.5 (401909094) | hold | 0.570 | 0.538 | +0.060 | loss |
| prop | VJ Edgecombe reb over 4.5 (401909093) | hold | 0.633 | 0.599 | +0.058 | win |
| prop | Jaren Jackson Jr. ast under 2.5 (401909838) | watch | 0.694 | 0.658 | +0.055 | win |
| prop | Alex Caruso ast over 1.5 (401909094) | hold | 0.651 | 0.617 | +0.054 | win |
| prop | Sam Merrill fg3m under 1.5 (401909093) | reject | 0.432 | 0.412 | +0.050 | win |
| prop | Ajay Mitchell ast over 2.5 (401909094) | hold | 0.660 | 0.629 | +0.050 | loss |
| prop | Jaylen Wells fg3m over 1.5 (401909838) | watch | 0.622 | 0.595 | +0.045 | loss |
| prop | Donovan Mitchell pts under 26.5 (401909093) | reject | 0.562 | 0.541 | +0.040 | loss |
| prop | Sam Merrill fg3m under 2.5 (401909093) | reject | 0.675 | 0.649 | +0.039 | win |
| prop | Joel Embiid reb under 8.5 (401909093) | reject | 0.581 | 0.562 | +0.034 | win |
| spread | home -2.5 (401909090) | watch | 0.519 | 0.507 | +0.022 | loss |
| ml | home (401909091) | watch | 0.562 | 0.550 | +0.022 | loss |
| prop | Jamal Murray ast over 6.5 (401909094) | reject | 0.485 | 0.476 | +0.019 | loss |
| spread | home -1.5 (401909091) | watch | 0.529 | 0.519 | +0.019 | loss |
| prop | Evan Mobley fg3m over 0.5 (401909093) | reject | 0.660 | 0.649 | +0.017 | win |
| prop | Ajay Mitchell pts under 11.5 (401909094) | reject | 0.565 | 0.556 | +0.016 | loss |
| spread | away 2.5 (401909841) | reject | 0.516 | 0.512 | +0.008 | loss |
| ml | away (401909094) | reject | 0.276 | 0.274 | +0.008 | loss |
| prop | Cameron Johnson pts under 12.5 (401909094) | reject | 0.542 | 0.541 | +0.003 | win |
| prop | Nikola Jokic pts under 25.5 (401909094) | reject | 0.545 | 0.543 | +0.002 | win |
| ml | away (401909841) | reject | 0.451 | 0.450 | +0.001 | loss |
| prop | Anfernee Simons ast over 2.5 (401909093) | reject | 0.374 | 0.312 | - | loss |
| prop | Anfernee Simons ast over 4.5 (401909093) | reject | 0.089 | 0.077 | - | loss |
| prop | Anfernee Simons ast over 6.5 (401909093) | reject | 0.014 | 0.028 | - | loss |
| prop | Anfernee Simons fg3m over 0.5 (401909093) | reject | 0.897 | 0.857 | - | loss |
| prop | Anfernee Simons fg3m over 1.5 (401909093) | reject | 0.693 | 0.637 | - | loss |
| prop | Anfernee Simons fg3m over 3.5 (401909093) | reject | 0.277 | 0.174 | - | loss |
| prop | Anfernee Simons fg3m over 4.5 (401909093) | reject | 0.149 | 0.095 | - | loss |
| prop | Anfernee Simons fg3m over 5.5 (401909093) | reject | 0.074 | 0.056 | - | loss |
| prop | Anfernee Simons fg3m over 6.5 (401909093) | reject | 0.035 | 0.034 | - | loss |
| prop | Anfernee Simons fg3m over 7.5 (401909093) | reject | 0.015 | 0.028 | - | loss |
| prop | Anfernee Simons pts over 14.5 (401909093) | reject | 0.419 | 0.211 | - | loss |
| prop | Anfernee Simons pts over 19.5 (401909093) | reject | 0.227 | 0.087 | - | loss |
| prop | Anfernee Simons pts over 24.5 (401909093) | reject | 0.112 | 0.048 | - | loss |
| prop | Anfernee Simons pts over 29.5 (401909093) | reject | 0.052 | 0.028 | - | loss |
| prop | Anfernee Simons pts over 4.5 (401909093) | reject | 0.919 | 0.846 | - | loss |
| prop | Anfernee Simons reb over 2.5 (401909093) | reject | 0.424 | 0.435 | - | win |
| prop | Anfernee Simons reb over 4.5 (401909093) | reject | 0.118 | 0.129 | - | loss |
| prop | Anfernee Simons reb over 6.5 (401909093) | reject | 0.023 | 0.053 | - | loss |
| prop | Donovan Mitchell ast over 12.5 (401909093) | reject | 0.002 | 0.028 | - | loss |
| prop | Donovan Mitchell ast over 2.5 (401909093) | reject | 0.710 | 0.895 | - | win |
| prop | Donovan Mitchell ast over 4.5 (401909093) | reject | 0.357 | 0.541 | - | loss |
| prop | Donovan Mitchell ast over 6.5 (401909093) | reject | 0.131 | 0.274 | - | loss |
| prop | Donovan Mitchell ast over 9.5 (401909093) | reject | 0.018 | 0.077 | - | loss |
| prop | Donovan Mitchell fg3m over 0.5 (401909093) | reject | 0.924 | 0.962 | - | win |
| prop | Donovan Mitchell fg3m over 1.5 (401909093) | reject | 0.755 | 0.818 | - | win |
| prop | Donovan Mitchell fg3m over 2.5 (401909093) | reject | 0.546 | 0.575 | - | loss |
| prop | Donovan Mitchell fg3m over 3.5 (401909093) | reject | 0.354 | 0.370 | - | loss |
| prop | Donovan Mitchell fg3m over 4.5 (401909093) | reject | 0.209 | 0.211 | - | loss |
| prop | Donovan Mitchell fg3m over 5.5 (401909093) | reject | 0.115 | 0.118 | - | loss |
| prop | Donovan Mitchell fg3m over 6.5 (401909093) | reject | 0.059 | 0.071 | - | loss |
| prop | Donovan Mitchell fg3m over 7.5 (401909093) | reject | 0.029 | 0.050 | - | loss |
| prop | Donovan Mitchell fg3m over 8.5 (401909093) | reject | 0.013 | 0.028 | - | loss |
| prop | Donovan Mitchell pts over 14.5 (401909093) | reject | 0.793 | 0.941 | - | win |
| prop | Donovan Mitchell pts over 19.5 (401909093) | reject | 0.643 | 0.810 | - | win |
| prop | Donovan Mitchell pts over 24.5 (401909093) | reject | 0.493 | 0.583 | - | win |
| prop | Donovan Mitchell pts over 29.5 (401909093) | reject | 0.362 | 0.364 | - | win |
| prop | Donovan Mitchell pts over 34.5 (401909093) | reject | 0.256 | 0.190 | - | loss |
| prop | Donovan Mitchell pts over 39.5 (401909093) | reject | 0.175 | 0.100 | - | loss |
| prop | Donovan Mitchell pts over 44.5 (401909093) | reject | 0.117 | 0.053 | - | loss |
| prop | Donovan Mitchell pts over 49.5 (401909093) | reject | 0.077 | 0.028 | - | loss |
| prop | Donovan Mitchell reb over 12.5 (401909093) | reject | 0.011 | 0.028 | - | loss |
| prop | Donovan Mitchell reb over 2.5 (401909093) | reject | 0.819 | 0.846 | - | win |
| prop | Donovan Mitchell reb over 4.5 (401909093) | reject | 0.522 | 0.552 | - | win |
| prop | Donovan Mitchell reb over 6.5 (401909093) | reject | 0.259 | 0.211 | - | win |
| prop | Donovan Mitchell reb over 9.5 (401909093) | reject | 0.062 | 0.056 | - | win |
| prop | Evan Mobley ast over 2.5 (401909093) | reject | 0.690 | 0.677 | - | loss |
| prop | Evan Mobley ast over 4.5 (401909093) | reject | 0.334 | 0.312 | - | loss |
| prop | Evan Mobley ast over 6.5 (401909093) | reject | 0.117 | 0.118 | - | loss |
| prop | Evan Mobley ast over 9.5 (401909093) | reject | 0.015 | 0.043 | - | loss |
| prop | Evan Mobley fg3m over 1.5 (401909093) | reject | 0.316 | 0.377 | - | loss |
| prop | Evan Mobley fg3m over 2.5 (401909093) | reject | 0.121 | 0.154 | - | loss |
| prop | Evan Mobley fg3m over 3.5 (401909093) | reject | 0.039 | 0.083 | - | loss |
| prop | Evan Mobley fg3m over 4.5 (401909093) | reject | 0.011 | 0.050 | - | loss |
| prop | Evan Mobley fg3m over 5.5 (401909093) | reject | 0.003 | 0.028 | - | loss |
| prop | Evan Mobley pts over 14.5 (401909093) | reject | 0.613 | 0.733 | - | win |
| prop | Evan Mobley pts over 19.5 (401909093) | reject | 0.417 | 0.426 | - | loss |
| prop | Evan Mobley pts over 24.5 (401909093) | reject | 0.263 | 0.190 | - | loss |
| prop | Evan Mobley pts over 29.5 (401909093) | reject | 0.156 | 0.083 | - | loss |
| prop | Evan Mobley pts over 34.5 (401909093) | reject | 0.089 | 0.043 | - | loss |
| prop | Evan Mobley pts over 39.5 (401909093) | reject | 0.049 | 0.028 | - | loss |
| prop | Evan Mobley pts over 9.5 (401909093) | reject | 0.817 | 0.941 | - | win |
| prop | Evan Mobley reb over 12.5 (401909093) | reject | 0.259 | 0.190 | - | loss |
| prop | Evan Mobley reb over 14.5 (401909093) | reject | 0.151 | 0.100 | - | loss |
| prop | Evan Mobley reb over 16.5 (401909093) | reject | 0.082 | 0.056 | - | loss |
| prop | Evan Mobley reb over 19.5 (401909093) | reject | 0.029 | 0.028 | - | loss |
| prop | Evan Mobley reb over 4.5 (401909093) | reject | 0.912 | 0.957 | - | win |
| prop | Evan Mobley reb over 6.5 (401909093) | reject | 0.775 | 0.818 | - | win |
| prop | Evan Mobley reb over 9.5 (401909093) | reject | 0.500 | 0.476 | - | loss |
| prop | James Harden ast over 12.5 (401909093) | reject | 0.026 | 0.077 | - | loss |
| prop | James Harden ast over 14.5 (401909093) | reject | 0.008 | 0.048 | - | loss |
| prop | James Harden ast over 2.5 (401909093) | reject | 0.891 | 0.980 | - | win |
| prop | James Harden ast over 4.5 (401909093) | reject | 0.651 | 0.857 | - | win |
| prop | James Harden ast over 9.5 (401909093) | reject | 0.117 | 0.238 | - | loss |
| prop | James Harden fg3m over 0.5 (401909093) | reject | 0.909 | 0.947 | - | win |
| prop | James Harden fg3m over 1.5 (401909093) | reject | 0.720 | 0.767 | - | win |
| prop | James Harden fg3m over 2.5 (401909093) | reject | 0.499 | 0.610 | - | win |
| prop | James Harden fg3m over 3.5 (401909093) | reject | 0.308 | 0.294 | - | loss |
| prop | James Harden fg3m over 4.5 (401909093) | reject | 0.173 | 0.148 | - | loss |
| prop | James Harden fg3m over 5.5 (401909093) | reject | 0.090 | 0.087 | - | loss |
| prop | James Harden fg3m over 6.5 (401909093) | reject | 0.044 | 0.056 | - | loss |
| prop | James Harden fg3m over 7.5 (401909093) | reject | 0.020 | 0.034 | - | loss |
| prop | James Harden fg3m over 8.5 (401909093) | reject | 0.009 | 0.028 | - | loss |
| prop | James Harden pts over 14.5 (401909093) | reject | 0.658 | 0.783 | - | win |
| prop | James Harden pts over 19.5 (401909093) | reject | 0.468 | 0.512 | - | loss |
| prop | James Harden pts over 24.5 (401909093) | reject | 0.310 | 0.256 | - | loss |
| prop | James Harden pts over 29.5 (401909093) | reject | 0.194 | 0.111 | - | loss |
| prop | James Harden pts over 34.5 (401909093) | reject | 0.117 | 0.059 | - | loss |
| prop | James Harden pts over 39.5 (401909093) | reject | 0.068 | 0.034 | - | loss |
| prop | James Harden pts over 9.5 (401909093) | reject | 0.844 | 0.957 | - | win |
| prop | James Harden reb over 12.5 (401909093) | reject | 0.011 | 0.028 | - | loss |
| prop | James Harden reb over 2.5 (401909093) | reject | 0.823 | 0.867 | - | win |
| prop | James Harden reb over 4.5 (401909093) | reject | 0.528 | 0.559 | - | loss |
| prop | James Harden reb over 6.5 (401909093) | reject | 0.264 | 0.211 | - | loss |
| prop | James Harden reb over 9.5 (401909093) | reject | 0.065 | 0.056 | - | loss |
| prop | Jarrett Allen ast over 2.5 (401909093) | reject | 0.163 | 0.200 | - | loss |
| prop | Jarrett Allen ast over 4.5 (401909093) | reject | 0.018 | 0.053 | - | loss |
| prop | Jarrett Allen ast over 6.5 (401909093) | reject | 0.001 | 0.028 | - | loss |
| prop | Jarrett Allen pts over 14.5 (401909093) | reject | 0.431 | 0.444 | - | loss |
| prop | Jarrett Allen pts over 19.5 (401909093) | reject | 0.237 | 0.174 | - | loss |
| prop | Jarrett Allen pts over 24.5 (401909093) | reject | 0.119 | 0.071 | - | loss |
| prop | Jarrett Allen pts over 29.5 (401909093) | reject | 0.056 | 0.028 | - | loss |
| prop | Jarrett Allen pts over 4.5 (401909093) | reject | 0.923 | 0.976 | - | win |
| prop | Jarrett Allen pts over 9.5 (401909093) | reject | 0.690 | 0.787 | - | win |
| prop | Jarrett Allen reb over 12.5 (401909093) | reject | 0.153 | 0.133 | - | loss |
| prop | Jarrett Allen reb over 14.5 (401909093) | reject | 0.077 | 0.071 | - | loss |
| prop | Jarrett Allen reb over 16.5 (401909093) | reject | 0.036 | 0.048 | - | loss |
| prop | Jarrett Allen reb over 19.5 (401909093) | reject | 0.010 | 0.028 | - | loss |
| prop | Jarrett Allen reb over 2.5 (401909093) | reject | 0.965 | 0.988 | - | win |
| prop | Jarrett Allen reb over 4.5 (401909093) | reject | 0.854 | 0.905 | - | win |
| prop | Jarrett Allen reb over 6.5 (401909093) | reject | 0.667 | 0.714 | - | win |
| prop | Jarrett Allen reb over 9.5 (401909093) | reject | 0.362 | 0.355 | - | loss |
| prop | Jaylen Brown ast over 2.5 (401909093) | reject | 0.791 | 0.792 | - | win |
| prop | Jaylen Brown ast over 4.5 (401909093) | reject | 0.469 | 0.417 | - | loss |
| prop | Jaylen Brown ast over 6.5 (401909093) | reject | 0.209 | 0.160 | - | loss |
| prop | Jaylen Brown ast over 9.5 (401909093) | reject | 0.041 | 0.053 | - | loss |
| prop | Jaylen Brown fg3m over 0.5 (401909093) | reject | 0.835 | 0.833 | - | win |
| prop | Jaylen Brown fg3m over 1.5 (401909093) | reject | 0.568 | 0.575 | - | loss |
| prop | Jaylen Brown fg3m over 2.5 (401909093) | reject | 0.325 | 0.270 | - | loss |
| prop | Jaylen Brown fg3m over 3.5 (401909093) | reject | 0.162 | 0.129 | - | loss |
| prop | Jaylen Brown fg3m over 4.5 (401909093) | reject | 0.073 | 0.062 | - | loss |
| prop | Jaylen Brown fg3m over 5.5 (401909093) | reject | 0.030 | 0.048 | - | loss |
| prop | Jaylen Brown fg3m over 6.5 (401909093) | reject | 0.012 | 0.028 | - | loss |
| prop | Jaylen Brown pts over 14.5 (401909093) | reject | 0.789 | 0.833 | - | win |
| prop | Jaylen Brown pts over 19.5 (401909093) | reject | 0.637 | 0.600 | - | win |
| prop | Jaylen Brown pts over 24.5 (401909093) | reject | 0.487 | 0.351 | - | loss |
| prop | Jaylen Brown pts over 29.5 (401909093) | reject | 0.356 | 0.160 | - | loss |
| prop | Jaylen Brown pts over 34.5 (401909093) | reject | 0.250 | 0.083 | - | loss |
| prop | Jaylen Brown pts over 39.5 (401909093) | reject | 0.171 | 0.048 | - | loss |
| prop | Jaylen Brown pts over 44.5 (401909093) | reject | 0.114 | 0.028 | - | loss |
| prop | Jaylen Brown pts over 9.5 (401909093) | reject | 0.914 | 0.966 | - | win |
| prop | Jaylen Brown reb over 12.5 (401909093) | reject | 0.061 | 0.053 | - | loss |
| prop | Jaylen Brown reb over 14.5 (401909093) | reject | 0.024 | 0.028 | - | loss |
| prop | Jaylen Brown reb over 2.5 (401909093) | reject | 0.925 | 0.941 | - | win |
| prop | Jaylen Brown reb over 4.5 (401909093) | reject | 0.740 | 0.744 | - | win |
| prop | Jaylen Brown reb over 9.5 (401909093) | reject | 0.201 | 0.138 | - | loss |
| prop | Jaylon Tyson ast over 2.5 (401909093) | reject | 0.115 | 0.299 | - | loss |
| prop | Jaylon Tyson ast over 4.5 (401909093) | reject | 0.009 | 0.087 | - | loss |
| prop | Jaylon Tyson ast over 6.5 (401909093) | reject | 0.000 | 0.034 | - | loss |
| prop | Jaylon Tyson fg3m over 0.5 (401909093) | reject | 0.537 | 0.796 | - | loss |
| prop | Jaylon Tyson fg3m over 1.5 (401909093) | reject | 0.196 | 0.452 | - | loss |
| prop | Jaylon Tyson fg3m over 2.5 (401909093) | reject | 0.056 | 0.200 | - | loss |
| prop | Jaylon Tyson fg3m over 3.5 (401909093) | reject | 0.013 | 0.095 | - | loss |
| prop | Jaylon Tyson fg3m over 4.5 (401909093) | reject | 0.003 | 0.053 | - | loss |
| prop | Jaylon Tyson fg3m over 5.5 (401909093) | reject | 0.001 | 0.028 | - | loss |
| prop | Jaylon Tyson pts over 14.5 (401909093) | reject | 0.014 | 0.182 | - | loss |
| prop | Jaylon Tyson pts over 19.5 (401909093) | reject | 0.002 | 0.071 | - | loss |
| prop | Jaylon Tyson pts over 24.5 (401909093) | reject | 0.000 | 0.034 | - | loss |
| prop | Jaylon Tyson pts over 29.5 (401909093) | reject | 0.000 | 0.028 | - | loss |
| prop | Jaylon Tyson pts over 4.5 (401909093) | reject | 0.479 | 0.857 | - | loss |
| prop | Jaylon Tyson reb over 12.5 (401909093) | reject | 0.000 | 0.028 | - | loss |
| prop | Jaylon Tyson reb over 2.5 (401909093) | reject | 0.387 | 0.800 | - | win |
| prop | Jaylon Tyson reb over 4.5 (401909093) | reject | 0.098 | 0.543 | - | win |
| prop | Jaylon Tyson reb over 6.5 (401909093) | reject | 0.017 | 0.200 | - | loss |
| prop | Jaylon Tyson reb over 9.5 (401909093) | reject | 0.001 | 0.059 | - | loss |
| prop | Joel Embiid ast over 2.5 (401909093) | reject | 0.801 | 0.818 | - | loss |
| prop | Joel Embiid ast over 6.5 (401909093) | reject | 0.220 | 0.182 | - | loss |
| prop | Joel Embiid ast over 9.5 (401909093) | reject | 0.045 | 0.056 | - | loss |
| prop | Joel Embiid fg3m over 0.5 (401909093) | reject | 0.726 | 0.800 | - | win |
| prop | Joel Embiid fg3m over 1.5 (401909093) | reject | 0.398 | 0.452 | - | loss |
| prop | Joel Embiid fg3m over 2.5 (401909093) | reject | 0.177 | 0.238 | - | loss |
| prop | Joel Embiid fg3m over 3.5 (401909093) | reject | 0.068 | 0.105 | - | loss |
| prop | Joel Embiid fg3m over 4.5 (401909093) | reject | 0.023 | 0.059 | - | loss |
| prop | Joel Embiid fg3m over 5.5 (401909093) | reject | 0.007 | 0.034 | - | loss |
| prop | Joel Embiid fg3m over 6.5 (401909093) | reject | 0.002 | 0.028 | - | loss |
| prop | Joel Embiid pts over 14.5 (401909093) | reject | 0.764 | 0.882 | - | win |
| prop | Joel Embiid pts over 19.5 (401909093) | reject | 0.603 | 0.667 | - | win |
| prop | Joel Embiid pts over 24.5 (401909093) | reject | 0.448 | 0.408 | - | loss |
| prop | Joel Embiid pts over 29.5 (401909093) | reject | 0.318 | 0.200 | - | loss |
| prop | Joel Embiid pts over 34.5 (401909093) | reject | 0.217 | 0.100 | - | loss |
| prop | Joel Embiid pts over 39.5 (401909093) | reject | 0.143 | 0.053 | - | loss |
| prop | Joel Embiid pts over 44.5 (401909093) | reject | 0.092 | 0.028 | - | loss |
| prop | Joel Embiid pts over 9.5 (401909093) | reject | 0.902 | 0.980 | - | win |
| prop | Joel Embiid reb over 12.5 (401909093) | reject | 0.129 | 0.121 | - | loss |
| prop | Joel Embiid reb over 14.5 (401909093) | reject | 0.062 | 0.062 | - | loss |
| prop | Joel Embiid reb over 16.5 (401909093) | reject | 0.027 | 0.038 | - | loss |
| prop | Joel Embiid reb over 19.5 (401909093) | reject | 0.007 | 0.028 | - | loss |
| prop | Joel Embiid reb over 2.5 (401909093) | reject | 0.959 | 0.985 | - | win |
| prop | Joel Embiid reb over 4.5 (401909093) | reject | 0.834 | 0.905 | - | win |
| prop | Joel Embiid reb over 6.5 (401909093) | reject | 0.633 | 0.714 | - | win |
| prop | Joel Embiid reb over 9.5 (401909093) | reject | 0.325 | 0.355 | - | loss |
| prop | Kentavious Caldwell-Pope ast over 2.5 (401909093) | reject | 0.429 | 0.174 | - | loss |
| prop | Kentavious Caldwell-Pope ast over 4.5 (401909093) | reject | 0.118 | 0.053 | - | loss |
| prop | Kentavious Caldwell-Pope fg3m over 0.5 (401909093) | reject | 0.696 | 0.744 | - | win |
| prop | Kentavious Caldwell-Pope fg3m over 1.5 (401909093) | reject | 0.359 | 0.437 | - | loss |
| prop | Kentavious Caldwell-Pope fg3m over 2.5 (401909093) | reject | 0.149 | 0.167 | - | loss |
| prop | Kentavious Caldwell-Pope fg3m over 3.5 (401909093) | reject | 0.053 | 0.083 | - | loss |
| prop | Kentavious Caldwell-Pope fg3m over 4.5 (401909093) | reject | 0.017 | 0.050 | - | loss |
| prop | Kentavious Caldwell-Pope fg3m over 5.5 (401909093) | reject | 0.005 | 0.028 | - | loss |
| prop | Kentavious Caldwell-Pope pts over 14.5 (401909093) | reject | 0.210 | 0.083 | - | loss |
| prop | Kentavious Caldwell-Pope pts over 19.5 (401909093) | reject | 0.080 | 0.034 | - | loss |
| prop | Kentavious Caldwell-Pope pts over 24.5 (401909093) | reject | 0.027 | 0.028 | - | loss |
| prop | Kentavious Caldwell-Pope pts over 4.5 (401909093) | reject | 0.831 | 0.667 | - | loss |
| prop | Kentavious Caldwell-Pope pts over 9.5 (401909093) | reject | 0.475 | 0.250 | - | loss |
| prop | Kentavious Caldwell-Pope reb over 2.5 (401909093) | reject | 0.503 | 0.476 | - | win |
| prop | Kentavious Caldwell-Pope reb over 4.5 (401909093) | reject | 0.169 | 0.143 | - | loss |
| prop | Kentavious Caldwell-Pope reb over 6.5 (401909093) | reject | 0.040 | 0.056 | - | loss |
| prop | Kentavious Caldwell-Pope reb over 9.5 (401909093) | reject | 0.003 | 0.028 | - | loss |
| prop | LeBron James ast over 12.5 (401909093) | reject | 0.069 | 0.083 | - | loss |
| prop | LeBron James ast over 14.5 (401909093) | reject | 0.027 | 0.050 | - | loss |
| prop | LeBron James ast over 2.5 (401909093) | reject | 0.941 | 0.980 | - | win |
| prop | LeBron James ast over 4.5 (401909093) | reject | 0.775 | 0.846 | - | win |
| prop | LeBron James ast over 6.5 (401909093) | reject | 0.535 | 0.615 | - | loss |
| prop | LeBron James ast over 9.5 (401909093) | reject | 0.224 | 0.244 | - | loss |
| prop | LeBron James fg3m over 0.5 (401909093) | reject | 0.720 | 0.750 | - | win |
| prop | LeBron James fg3m over 1.5 (401909093) | reject | 0.389 | 0.403 | - | loss |
| prop | LeBron James fg3m over 2.5 (401909093) | reject | 0.170 | 0.182 | - | loss |
| prop | LeBron James fg3m over 3.5 (401909093) | reject | 0.064 | 0.087 | - | loss |
| prop | LeBron James fg3m over 4.5 (401909093) | reject | 0.021 | 0.050 | - | loss |
| prop | LeBron James fg3m over 5.5 (401909093) | reject | 0.006 | 0.028 | - | loss |
| prop | LeBron James pts over 14.5 (401909093) | reject | 0.672 | 0.600 | - | win |
| prop | LeBron James pts over 19.5 (401909093) | reject | 0.484 | 0.308 | - | loss |
| prop | LeBron James pts over 24.5 (401909093) | reject | 0.326 | 0.121 | - | loss |
| prop | LeBron James pts over 29.5 (401909093) | reject | 0.208 | 0.059 | - | loss |
| prop | LeBron James pts over 34.5 (401909093) | reject | 0.127 | 0.028 | - | loss |
| prop | LeBron James pts over 4.5 (401909093) | reject | 0.970 | 0.990 | - | win |
| prop | LeBron James pts over 9.5 (401909093) | reject | 0.852 | 0.889 | - | win |
| prop | LeBron James reb over 12.5 (401909093) | reject | 0.056 | 0.062 | - | loss |
| prop | LeBron James reb over 14.5 (401909093) | reject | 0.022 | 0.034 | - | loss |
| prop | LeBron James reb over 16.5 (401909093) | reject | 0.008 | 0.028 | - | loss |
| prop | LeBron James reb over 2.5 (401909093) | reject | 0.921 | 0.976 | - | win |
| prop | LeBron James reb over 4.5 (401909093) | reject | 0.730 | 0.833 | - | win |
| prop | LeBron James reb over 9.5 (401909093) | reject | 0.191 | 0.190 | - | win |
| prop | Sam Merrill ast over 2.5 (401909093) | reject | 0.224 | 0.294 | - | loss |
| prop | Sam Merrill ast over 4.5 (401909093) | reject | 0.033 | 0.077 | - | loss |
| prop | Sam Merrill ast over 6.5 (401909093) | reject | 0.003 | 0.028 | - | loss |
| prop | Sam Merrill fg3m over 0.5 (401909093) | reject | 0.835 | 0.905 | - | win |
| prop | Sam Merrill fg3m over 3.5 (401909093) | reject | 0.163 | 0.190 | - | loss |
| prop | Sam Merrill fg3m over 4.5 (401909093) | reject | 0.073 | 0.100 | - | loss |
| prop | Sam Merrill fg3m over 5.5 (401909093) | reject | 0.030 | 0.059 | - | loss |
| prop | Sam Merrill fg3m over 6.5 (401909093) | reject | 0.012 | 0.034 | - | loss |
| prop | Sam Merrill fg3m over 7.5 (401909093) | reject | 0.004 | 0.028 | - | loss |
| prop | Sam Merrill pts over 14.5 (401909093) | reject | 0.138 | 0.160 | - | loss |
| prop | Sam Merrill pts over 19.5 (401909093) | reject | 0.043 | 0.062 | - | loss |
| prop | Sam Merrill pts over 24.5 (401909093) | reject | 0.012 | 0.028 | - | loss |
| prop | Sam Merrill pts over 29.5 (401909093) | reject | 0.003 | 0.028 | - | loss |
| prop | Sam Merrill pts over 4.5 (401909093) | reject | 0.773 | 0.818 | - | win |
| prop | Sam Merrill pts over 9.5 (401909093) | reject | 0.377 | 0.417 | - | loss |
| prop | Sam Merrill reb over 2.5 (401909093) | reject | 0.320 | 0.400 | - | win |
| prop | Sam Merrill reb over 4.5 (401909093) | reject | 0.067 | 0.111 | - | win |
| prop | Sam Merrill reb over 6.5 (401909093) | reject | 0.010 | 0.043 | - | loss |
| prop | Sam Merrill reb over 9.5 (401909093) | reject | 0.000 | 0.028 | - | loss |
| prop | Tyrese Maxey ast over 12.5 (401909093) | reject | 0.026 | 0.034 | - | loss |
| prop | Tyrese Maxey ast over 14.5 (401909093) | reject | 0.008 | 0.028 | - | loss |
| prop | Tyrese Maxey ast over 2.5 (401909093) | reject | 0.891 | 0.938 | - | win |
| prop | Tyrese Maxey ast over 4.5 (401909093) | reject | 0.651 | 0.677 | - | win |
| prop | Tyrese Maxey ast over 6.5 (401909093) | reject | 0.379 | 0.357 | - | loss |
| prop | Tyrese Maxey ast over 9.5 (401909093) | reject | 0.117 | 0.100 | - | loss |
| prop | Tyrese Maxey fg3m over 0.5 (401909093) | reject | 0.912 | 0.917 | - | win |
| prop | Tyrese Maxey fg3m over 1.5 (401909093) | reject | 0.725 | 0.714 | - | win |
| prop | Tyrese Maxey fg3m over 2.5 (401909093) | reject | 0.506 | 0.568 | - | loss |
| prop | Tyrese Maxey fg3m over 3.5 (401909093) | reject | 0.315 | 0.274 | - | loss |
| prop | Tyrese Maxey fg3m over 4.5 (401909093) | reject | 0.178 | 0.143 | - | loss |
| prop | Tyrese Maxey fg3m over 5.5 (401909093) | reject | 0.093 | 0.087 | - | loss |
| prop | Tyrese Maxey fg3m over 6.5 (401909093) | reject | 0.046 | 0.056 | - | loss |
| prop | Tyrese Maxey fg3m over 7.5 (401909093) | reject | 0.021 | 0.034 | - | loss |
| prop | Tyrese Maxey fg3m over 8.5 (401909093) | reject | 0.009 | 0.028 | - | loss |
| prop | Tyrese Maxey pts over 14.5 (401909093) | reject | 0.790 | 0.917 | - | win |
| prop | Tyrese Maxey pts over 19.5 (401909093) | reject | 0.639 | 0.714 | - | win |
| prop | Tyrese Maxey pts over 24.5 (401909093) | reject | 0.489 | 0.455 | - | win |
| prop | Tyrese Maxey pts over 29.5 (401909093) | reject | 0.358 | 0.238 | - | win |
| prop | Tyrese Maxey pts over 34.5 (401909093) | reject | 0.252 | 0.111 | - | loss |
| prop | Tyrese Maxey pts over 39.5 (401909093) | reject | 0.172 | 0.059 | - | loss |
| prop | Tyrese Maxey pts over 44.5 (401909093) | reject | 0.115 | 0.034 | - | loss |
| prop | Tyrese Maxey pts over 9.5 (401909093) | reject | 0.915 | 0.988 | - | win |
| prop | Tyrese Maxey reb over 2.5 (401909093) | reject | 0.731 | 0.655 | - | win |
| prop | Tyrese Maxey reb over 4.5 (401909093) | reject | 0.392 | 0.286 | - | loss |
| prop | Tyrese Maxey reb over 6.5 (401909093) | reject | 0.157 | 0.103 | - | loss |
| prop | Tyrese Maxey reb over 9.5 (401909093) | reject | 0.027 | 0.028 | - | loss |
| prop | VJ Edgecombe ast over 2.5 (401909093) | reject | 0.682 | 0.617 | - | win |
| prop | VJ Edgecombe ast over 4.5 (401909093) | reject | 0.325 | 0.154 | - | win |
| prop | VJ Edgecombe ast over 6.5 (401909093) | reject | 0.112 | 0.056 | - | loss |
| prop | VJ Edgecombe fg3m over 0.5 (401909093) | reject | 0.805 | 0.810 | - | win |
| prop | VJ Edgecombe fg3m over 1.5 (401909093) | reject | 0.516 | 0.448 | - | loss |
| prop | VJ Edgecombe fg3m over 2.5 (401909093) | reject | 0.275 | 0.222 | - | loss |
| prop | VJ Edgecombe fg3m over 3.5 (401909093) | reject | 0.127 | 0.105 | - | loss |
| prop | VJ Edgecombe fg3m over 4.5 (401909093) | reject | 0.053 | 0.056 | - | loss |
| prop | VJ Edgecombe fg3m over 5.5 (401909093) | reject | 0.020 | 0.034 | - | loss |
| prop | VJ Edgecombe fg3m over 6.5 (401909093) | reject | 0.007 | 0.028 | - | loss |
| prop | VJ Edgecombe pts over 14.5 (401909093) | reject | 0.478 | 0.303 | - | loss |
| prop | VJ Edgecombe pts over 19.5 (401909093) | reject | 0.279 | 0.111 | - | loss |
| prop | VJ Edgecombe pts over 24.5 (401909093) | reject | 0.149 | 0.053 | - | loss |
| prop | VJ Edgecombe pts over 29.5 (401909093) | reject | 0.075 | 0.028 | - | loss |
| prop | VJ Edgecombe pts over 4.5 (401909093) | reject | 0.934 | 0.933 | - | win |
| prop | VJ Edgecombe pts over 9.5 (401909093) | reject | 0.725 | 0.643 | - | win |
| prop | VJ Edgecombe reb over 12.5 (401909093) | reject | 0.027 | 0.028 | - | loss |
| prop | VJ Edgecombe reb over 14.5 (401909093) | reject | 0.009 | 0.028 | - | loss |
| prop | VJ Edgecombe reb over 2.5 (401909093) | reject | 0.879 | 0.867 | - | win |
| prop | VJ Edgecombe reb over 6.5 (401909093) | reject | 0.367 | 0.256 | - | win |
| prop | VJ Edgecombe reb over 9.5 (401909093) | reject | 0.116 | 0.071 | - | loss |
| prop | LeBron James ast over 7.5 (401909093) | reject | 0.416 | 0.538 | - | loss |
| prop | LeBron James ast under 7.5 (401909093) | reject | 0.584 | 0.538 | - | win |
| prop | LeBron James fg3m under 1.5 (401909093) | reject | 0.611 | 0.667 | - | win |
| prop | LeBron James pts over 15.5 (401909093) | reject | 0.633 | 0.532 | - | win |
| prop | LeBron James pts under 15.5 (401909093) | reject | 0.367 | 0.532 | - | loss |
| prop | Kentavious Caldwell-Pope fg3m under 1.5 (401909093) | reject | 0.641 | 0.633 | - | win |
| prop | Joel Embiid ast over 3.5 (401909093) | reject | 0.646 | 0.621 | - | loss |
| prop | Joel Embiid ast under 3.5 (401909093) | reject | 0.354 | 0.621 | - | win |
| prop | Joel Embiid fg3m under 1.5 (401909093) | reject | 0.602 | 0.617 | - | win |
| prop | Joel Embiid pts over 22.5 (401909093) | reject | 0.508 | 0.543 | - | win |
| prop | Joel Embiid pts under 22.5 (401909093) | reject | 0.492 | 0.543 | - | loss |
| prop | Donovan Mitchell ast under 4.5 (401909093) | reject | 0.643 | 0.541 | - | win |
| prop | Donovan Mitchell fg3m under 2.5 (401909093) | reject | 0.454 | 0.493 | - | win |
| prop | Donovan Mitchell reb under 4.5 (401909093) | reject | 0.478 | 0.552 | - | loss |
| prop | Jaylen Brown ast over 3.5 (401909093) | reject | 0.633 | 0.595 | - | win |
| prop | Jaylen Brown ast under 3.5 (401909093) | reject | 0.367 | 0.595 | - | loss |
| prop | Jaylen Brown fg3m under 1.5 (401909093) | reject | 0.432 | 0.575 | - | win |
| prop | Jaylen Brown reb over 5.5 (401909093) | reject | 0.619 | 0.602 | - | win |
| prop | Jaylen Brown reb under 5.5 (401909093) | reject | 0.381 | 0.602 | - | loss |
| prop | James Harden fg3m under 2.5 (401909093) | reject | 0.501 | 0.610 | - | loss |
| prop | James Harden pts over 18.5 (401909093) | reject | 0.504 | 0.546 | - | loss |
| prop | James Harden pts under 18.5 (401909093) | reject | 0.496 | 0.546 | - | win |
| prop | James Harden reb under 4.5 (401909093) | reject | 0.472 | 0.559 | - | win |
| prop | Jarrett Allen ast over 1.5 (401909093) | reject | 0.386 | 0.588 | - | loss |
| prop | Jarrett Allen ast under 1.5 (401909093) | reject | 0.614 | 0.588 | - | win |
| prop | Sam Merrill pts over 8.5 (401909093) | reject | 0.448 | 0.538 | - | loss |
| prop | Sam Merrill pts under 8.5 (401909093) | reject | 0.552 | 0.538 | - | win |
| prop | Anfernee Simons fg3m under 1.5 (401909093) | reject | 0.307 | 0.431 | - | win |
| prop | Tyrese Maxey ast over 5.5 (401909093) | reject | 0.510 | 0.565 | - | win |
| prop | Tyrese Maxey ast under 5.5 (401909093) | reject | 0.490 | 0.565 | - | loss |
| prop | Tyrese Maxey fg3m under 2.5 (401909093) | reject | 0.494 | 0.568 | - | win |
| prop | Tyrese Maxey reb over 3.5 (401909093) | reject | 0.557 | 0.592 | - | loss |
| prop | Tyrese Maxey reb under 3.5 (401909093) | reject | 0.443 | 0.592 | - | win |
| prop | Evan Mobley ast over 3.5 (401909093) | reject | 0.503 | 0.578 | - | loss |
| prop | Evan Mobley ast under 3.5 (401909093) | reject | 0.497 | 0.578 | - | win |
| prop | Evan Mobley fg3m under 1.5 (401909093) | reject | 0.684 | 0.690 | - | win |
| prop | Evan Mobley reb over 8.5 (401909093) | reject | 0.594 | 0.575 | - | loss |
| prop | Evan Mobley reb under 8.5 (401909093) | reject | 0.406 | 0.575 | - | win |
| prop | Jaylon Tyson ast over 1.5 (401909093) | reject | 0.312 | 0.549 | - | win |
| prop | Jaylon Tyson ast under 1.5 (401909093) | reject | 0.688 | 0.549 | - | loss |
| prop | Jaylon Tyson fg3m under 1.5 (401909093) | reject | 0.804 | 0.617 | - | win |
| prop | Jaylon Tyson reb under 4.5 (401909093) | reject | 0.902 | 0.543 | - | loss |
| prop | VJ Edgecombe ast under 2.5 (401909093) | reject | 0.318 | 0.617 | - | loss |
| prop | VJ Edgecombe fg3m under 1.5 (401909093) | reject | 0.484 | 0.621 | - | win |
| prop | Joel Embiid ast over 12.5 (401909093) | reject | 0.006 | 0.028 | - | loss |
| prop | Jaylen Brown ast over 12.5 (401909093) | reject | 0.005 | 0.028 | - | loss |
| prop | Aaron Gordon ast over 2.5 (401909094) | reject | 0.543 | 0.521 | - | loss |
| prop | Aaron Gordon ast over 4.5 (401909094) | reject | 0.194 | 0.143 | - | loss |
| prop | Aaron Gordon ast over 6.5 (401909094) | reject | 0.048 | 0.056 | - | loss |
| prop | Aaron Gordon ast over 9.5 (401909094) | reject | 0.004 | 0.028 | - | loss |
| prop | Aaron Gordon fg3m over 0.5 (401909094) | reject | 0.758 | 0.857 | - | win |
| prop | Aaron Gordon fg3m over 1.5 (401909094) | reject | 0.442 | 0.549 | - | win |
| prop | Aaron Gordon fg3m over 2.5 (401909094) | reject | 0.211 | 0.282 | - | win |
| prop | Aaron Gordon fg3m over 3.5 (401909094) | reject | 0.087 | 0.129 | - | loss |
| prop | Aaron Gordon fg3m over 4.5 (401909094) | reject | 0.032 | 0.071 | - | loss |
| prop | Aaron Gordon fg3m over 5.5 (401909094) | reject | 0.011 | 0.043 | - | loss |
| prop | Aaron Gordon fg3m over 6.5 (401909094) | reject | 0.003 | 0.028 | - | loss |
| prop | Aaron Gordon pts over 14.5 (401909094) | reject | 0.438 | 0.549 | - | win |
| prop | Aaron Gordon pts over 19.5 (401909094) | reject | 0.243 | 0.238 | - | win |
| prop | Aaron Gordon pts over 24.5 (401909094) | reject | 0.124 | 0.100 | - | loss |
| prop | Aaron Gordon pts over 29.5 (401909094) | reject | 0.059 | 0.053 | - | loss |
| prop | Aaron Gordon pts over 34.5 (401909094) | reject | 0.027 | 0.028 | - | loss |
| prop | Aaron Gordon pts over 4.5 (401909094) | reject | 0.924 | 0.980 | - | win |
| prop | Aaron Gordon pts over 9.5 (401909094) | reject | 0.695 | 0.818 | - | win |
| prop | Aaron Gordon reb over 12.5 (401909094) | reject | 0.024 | 0.050 | - | loss |
| prop | Aaron Gordon reb over 14.5 (401909094) | reject | 0.008 | 0.028 | - | loss |
| prop | Aaron Gordon reb over 2.5 (401909094) | reject | 0.871 | 0.947 | - | win |
| prop | Aaron Gordon reb over 4.5 (401909094) | reject | 0.619 | 0.737 | - | win |
| prop | Aaron Gordon reb over 6.5 (401909094) | reject | 0.352 | 0.435 | - | loss |
| prop | Aaron Gordon reb over 9.5 (401909094) | reject | 0.107 | 0.133 | - | loss |
| prop | Ajay Mitchell ast over 4.5 (401909094) | reject | 0.301 | 0.267 | - | loss |
| prop | Ajay Mitchell ast over 6.5 (401909094) | reject | 0.098 | 0.100 | - | loss |
| prop | Ajay Mitchell ast over 9.5 (401909094) | reject | 0.011 | 0.028 | - | loss |
| prop | Ajay Mitchell fg3m over 0.5 (401909094) | reject | 0.574 | 0.744 | - | loss |
| prop | Ajay Mitchell fg3m over 2.5 (401909094) | reject | 0.072 | 0.154 | - | loss |
| prop | Ajay Mitchell fg3m over 3.5 (401909094) | reject | 0.019 | 0.071 | - | loss |
| prop | Ajay Mitchell fg3m over 4.5 (401909094) | reject | 0.004 | 0.038 | - | loss |
| prop | Ajay Mitchell fg3m over 5.5 (401909094) | reject | 0.001 | 0.028 | - | loss |
| prop | Ajay Mitchell pts over 14.5 (401909094) | reject | 0.285 | 0.312 | - | loss |
| prop | Ajay Mitchell pts over 19.5 (401909094) | reject | 0.125 | 0.121 | - | loss |
| prop | Ajay Mitchell pts over 24.5 (401909094) | reject | 0.050 | 0.056 | - | loss |
| prop | Ajay Mitchell pts over 29.5 (401909094) | reject | 0.018 | 0.028 | - | loss |
| prop | Ajay Mitchell pts over 4.5 (401909094) | reject | 0.871 | 0.933 | - | win |
| prop | Ajay Mitchell pts over 9.5 (401909094) | reject | 0.557 | 0.655 | - | win |
| prop | Ajay Mitchell reb over 2.5 (401909094) | reject | 0.579 | 0.613 | - | loss |
| prop | Ajay Mitchell reb over 4.5 (401909094) | reject | 0.229 | 0.250 | - | loss |
| prop | Ajay Mitchell reb over 6.5 (401909094) | reject | 0.065 | 0.091 | - | loss |
| prop | Ajay Mitchell reb over 9.5 (401909094) | reject | 0.006 | 0.028 | - | loss |
| prop | Alex Caruso ast over 2.5 (401909094) | reject | 0.405 | 0.392 | - | win |
| prop | Alex Caruso ast over 4.5 (401909094) | reject | 0.105 | 0.111 | - | win |
| prop | Alex Caruso ast over 6.5 (401909094) | reject | 0.018 | 0.050 | - | loss |
| prop | Alex Caruso fg3m over 0.5 (401909094) | reject | 0.781 | 0.762 | - | win |
| prop | Alex Caruso fg3m over 1.5 (401909094) | reject | 0.476 | 0.417 | - | loss |
| prop | Alex Caruso fg3m over 2.5 (401909094) | reject | 0.240 | 0.190 | - | loss |
| prop | Alex Caruso fg3m over 3.5 (401909094) | reject | 0.104 | 0.095 | - | loss |
| prop | Alex Caruso fg3m over 4.5 (401909094) | reject | 0.041 | 0.053 | - | loss |
| prop | Alex Caruso fg3m over 5.5 (401909094) | reject | 0.014 | 0.028 | - | loss |
| prop | Alex Caruso pts over 14.5 (401909094) | reject | 0.218 | 0.118 | - | loss |
| prop | Alex Caruso pts over 19.5 (401909094) | reject | 0.084 | 0.053 | - | loss |
| prop | Alex Caruso pts over 24.5 (401909094) | reject | 0.029 | 0.028 | - | loss |
| prop | Alex Caruso pts over 4.5 (401909094) | reject | 0.835 | 0.756 | - | win |
| prop | Alex Caruso pts over 9.5 (401909094) | reject | 0.484 | 0.339 | - | loss |
| prop | Alex Caruso reb over 4.5 (401909094) | reject | 0.329 | 0.222 | - | loss |
| prop | Alex Caruso reb over 6.5 (401909094) | reject | 0.117 | 0.083 | - | loss |
| prop | Alex Caruso reb over 9.5 (401909094) | reject | 0.016 | 0.028 | - | loss |
| prop | Cameron Johnson ast over 2.5 (401909094) | reject | 0.475 | 0.437 | - | loss |
| prop | Cameron Johnson ast over 4.5 (401909094) | reject | 0.146 | 0.100 | - | loss |
| prop | Cameron Johnson ast over 6.5 (401909094) | reject | 0.030 | 0.034 | - | loss |
| prop | Cameron Johnson fg3m over 0.5 (401909094) | reject | 0.841 | 0.909 | - | win |
| prop | Cameron Johnson fg3m over 1.5 (401909094) | reject | 0.578 | 0.655 | - | loss |
| prop | Cameron Johnson fg3m over 2.5 (401909094) | reject | 0.335 | 0.418 | - | loss |
| prop | Cameron Johnson fg3m over 3.5 (401909094) | reject | 0.170 | 0.200 | - | loss |
| prop | Cameron Johnson fg3m over 4.5 (401909094) | reject | 0.077 | 0.103 | - | loss |
| prop | Cameron Johnson fg3m over 5.5 (401909094) | reject | 0.032 | 0.059 | - | loss |
| prop | Cameron Johnson fg3m over 6.5 (401909094) | reject | 0.013 | 0.028 | - | loss |
| prop | Cameron Johnson fg3m over 7.5 (401909094) | reject | 0.005 | 0.028 | - | loss |
| prop | Cameron Johnson pts over 14.5 (401909094) | reject | 0.359 | 0.408 | - | loss |
| prop | Cameron Johnson pts over 19.5 (401909094) | reject | 0.179 | 0.167 | - | loss |
| prop | Cameron Johnson pts over 24.5 (401909094) | reject | 0.081 | 0.071 | - | loss |
| prop | Cameron Johnson pts over 29.5 (401909094) | reject | 0.034 | 0.034 | - | loss |
| prop | Cameron Johnson pts over 34.5 (401909094) | reject | 0.014 | 0.028 | - | loss |
| prop | Cameron Johnson pts over 4.5 (401909094) | reject | 0.900 | 0.957 | - | win |
| prop | Cameron Johnson pts over 9.5 (401909094) | reject | 0.629 | 0.730 | - | loss |
| prop | Cameron Johnson reb over 2.5 (401909094) | reject | 0.686 | 0.762 | - | loss |
| prop | Cameron Johnson reb over 4.5 (401909094) | reject | 0.337 | 0.368 | - | loss |
| prop | Cameron Johnson reb over 6.5 (401909094) | reject | 0.122 | 0.133 | - | loss |
| prop | Cameron Johnson reb over 9.5 (401909094) | reject | 0.017 | 0.038 | - | loss |
| prop | Cason Wallace ast over 2.5 (401909094) | reject | 0.339 | 0.420 | - | loss |
| prop | Cason Wallace ast over 4.5 (401909094) | reject | 0.073 | 0.111 | - | loss |
| prop | Cason Wallace ast over 6.5 (401909094) | reject | 0.010 | 0.043 | - | loss |
| prop | Cason Wallace fg3m over 0.5 (401909094) | reject | 0.668 | 0.773 | - | win |
| prop | Cason Wallace fg3m over 1.5 (401909094) | reject | 0.324 | 0.474 | - | win |
| prop | Cason Wallace fg3m over 2.5 (401909094) | reject | 0.126 | 0.190 | - | win |
| prop | Cason Wallace fg3m over 3.5 (401909094) | reject | 0.042 | 0.091 | - | loss |
| prop | Cason Wallace fg3m over 4.5 (401909094) | reject | 0.012 | 0.050 | - | loss |
| prop | Cason Wallace fg3m over 5.5 (401909094) | reject | 0.003 | 0.028 | - | loss |
| prop | Cason Wallace pts over 14.5 (401909094) | reject | 0.079 | 0.143 | - | loss |
| prop | Cason Wallace pts over 19.5 (401909094) | reject | 0.019 | 0.059 | - | loss |
| prop | Cason Wallace pts over 24.5 (401909094) | reject | 0.004 | 0.028 | - | loss |
| prop | Cason Wallace pts over 4.5 (401909094) | reject | 0.697 | 0.818 | - | win |
| prop | Cason Wallace pts over 9.5 (401909094) | reject | 0.275 | 0.408 | - | loss |
| prop | Cason Wallace reb over 2.5 (401909094) | reject | 0.485 | 0.600 | - | loss |
| prop | Cason Wallace reb over 4.5 (401909094) | reject | 0.156 | 0.238 | - | loss |
| prop | Cason Wallace reb over 6.5 (401909094) | reject | 0.035 | 0.083 | - | loss |
| prop | Cason Wallace reb over 9.5 (401909094) | reject | 0.002 | 0.028 | - | loss |
| prop | Chet Holmgren ast over 2.5 (401909094) | reject | 0.196 | 0.200 | - | loss |
| prop | Chet Holmgren ast over 4.5 (401909094) | reject | 0.025 | 0.053 | - | loss |
| prop | Chet Holmgren ast over 6.5 (401909094) | reject | 0.002 | 0.028 | - | loss |
| prop | Chet Holmgren fg3m over 0.5 (401909094) | reject | 0.660 | 0.733 | - | loss |
| prop | Chet Holmgren fg3m over 2.5 (401909094) | reject | 0.121 | 0.148 | - | loss |
| prop | Chet Holmgren fg3m over 3.5 (401909094) | reject | 0.039 | 0.071 | - | loss |
| prop | Chet Holmgren fg3m over 4.5 (401909094) | reject | 0.011 | 0.043 | - | loss |
| prop | Chet Holmgren fg3m over 5.5 (401909094) | reject | 0.003 | 0.028 | - | loss |
| prop | Chet Holmgren pts over 14.5 (401909094) | reject | 0.492 | 0.535 | - | loss |
| prop | Chet Holmgren pts over 19.5 (401909094) | reject | 0.292 | 0.250 | - | loss |
| prop | Chet Holmgren pts over 24.5 (401909094) | reject | 0.160 | 0.100 | - | loss |
| prop | Chet Holmgren pts over 29.5 (401909094) | reject | 0.082 | 0.050 | - | loss |
| prop | Chet Holmgren pts over 34.5 (401909094) | reject | 0.040 | 0.028 | - | loss |
| prop | Chet Holmgren pts over 4.5 (401909094) | reject | 0.938 | 0.988 | - | win |
| prop | Chet Holmgren pts over 9.5 (401909094) | reject | 0.736 | 0.857 | - | win |
| prop | Chet Holmgren reb over 12.5 (401909094) | reject | 0.185 | 0.133 | - | win |
| prop | Chet Holmgren reb over 14.5 (401909094) | reject | 0.098 | 0.077 | - | win |
| prop | Chet Holmgren reb over 16.5 (401909094) | reject | 0.048 | 0.048 | - | win |
| prop | Chet Holmgren reb over 19.5 (401909094) | reject | 0.015 | 0.028 | - | loss |
| prop | Chet Holmgren reb over 2.5 (401909094) | reject | 0.972 | 0.990 | - | win |
| prop | Chet Holmgren reb over 4.5 (401909094) | reject | 0.876 | 0.923 | - | win |
| prop | Chet Holmgren reb over 6.5 (401909094) | reject | 0.706 | 0.744 | - | win |
| prop | Chet Holmgren reb over 9.5 (401909094) | reject | 0.408 | 0.385 | - | win |
| prop | Christian Braun ast over 2.5 (401909094) | reject | 0.408 | 0.407 | - | loss |
| prop | Christian Braun ast over 4.5 (401909094) | reject | 0.106 | 0.087 | - | loss |
| prop | Christian Braun ast over 6.5 (401909094) | reject | 0.019 | 0.028 | - | loss |
| prop | Christian Braun fg3m over 0.5 (401909094) | reject | 0.641 | 0.750 | - | win |
| prop | Christian Braun fg3m over 1.5 (401909094) | reject | 0.295 | 0.426 | - | loss |
| prop | Christian Braun fg3m over 2.5 (401909094) | reject | 0.108 | 0.182 | - | loss |
| prop | Christian Braun fg3m over 3.5 (401909094) | reject | 0.034 | 0.083 | - | loss |
| prop | Christian Braun fg3m over 4.5 (401909094) | reject | 0.009 | 0.048 | - | loss |
| prop | Christian Braun fg3m over 5.5 (401909094) | reject | 0.002 | 0.028 | - | loss |
| prop | Christian Braun pts over 14.5 (401909094) | reject | 0.313 | 0.282 | - | loss |
| prop | Christian Braun pts over 19.5 (401909094) | reject | 0.145 | 0.105 | - | loss |
| prop | Christian Braun pts over 24.5 (401909094) | reject | 0.061 | 0.053 | - | loss |
| prop | Christian Braun pts over 29.5 (401909094) | reject | 0.024 | 0.028 | - | loss |
| prop | Christian Braun pts over 4.5 (401909094) | reject | 0.883 | 0.929 | - | win |
| prop | Christian Braun pts over 9.5 (401909094) | reject | 0.586 | 0.623 | - | loss |
| prop | Christian Braun reb over 12.5 (401909094) | reject | 0.008 | 0.028 | - | loss |
| prop | Christian Braun reb over 2.5 (401909094) | reject | 0.802 | 0.833 | - | win |
| prop | Christian Braun reb over 4.5 (401909094) | reject | 0.494 | 0.455 | - | win |
| prop | Christian Braun reb over 6.5 (401909094) | reject | 0.235 | 0.190 | - | loss |
| prop | Christian Braun reb over 9.5 (401909094) | reject | 0.052 | 0.056 | - | loss |
| prop | Isaiah Hartenstein ast over 2.5 (401909094) | reject | 0.417 | 0.581 | - | loss |
| prop | Isaiah Hartenstein ast over 4.5 (401909094) | reject | 0.111 | 0.200 | - | loss |
| prop | Isaiah Hartenstein ast over 6.5 (401909094) | reject | 0.020 | 0.071 | - | loss |
| prop | Isaiah Hartenstein pts over 14.5 (401909094) | reject | 0.054 | 0.138 | - | loss |
| prop | Isaiah Hartenstein pts over 19.5 (401909094) | reject | 0.011 | 0.053 | - | loss |
| prop | Isaiah Hartenstein pts over 24.5 (401909094) | reject | 0.002 | 0.028 | - | loss |
| prop | Isaiah Hartenstein pts over 4.5 (401909094) | reject | 0.646 | 0.818 | - | win |
| prop | Isaiah Hartenstein pts over 9.5 (401909094) | reject | 0.221 | 0.435 | - | loss |
| prop | Isaiah Hartenstein reb over 12.5 (401909094) | reject | 0.057 | 0.160 | - | loss |
| prop | Isaiah Hartenstein reb over 14.5 (401909094) | reject | 0.023 | 0.095 | - | loss |
| prop | Isaiah Hartenstein reb over 16.5 (401909094) | reject | 0.008 | 0.056 | - | loss |
| prop | Isaiah Hartenstein reb over 19.5 (401909094) | reject | 0.002 | 0.028 | - | loss |
| prop | Isaiah Hartenstein reb over 2.5 (401909094) | reject | 0.922 | 0.985 | - | win |
| prop | Isaiah Hartenstein reb over 4.5 (401909094) | reject | 0.732 | 0.900 | - | win |
| prop | Isaiah Hartenstein reb over 6.5 (401909094) | reject | 0.485 | 0.714 | - | loss |
| prop | Isaiah Hartenstein reb over 9.5 (401909094) | reject | 0.193 | 0.385 | - | loss |
| prop | Jalen Williams ast over 12.5 (401909094) | reject | 0.005 | 0.028 | - | loss |
| prop | Jalen Williams ast over 2.5 (401909094) | reject | 0.778 | 0.846 | - | win |
| prop | Jalen Williams ast over 4.5 (401909094) | reject | 0.449 | 0.568 | - | loss |
| prop | Jalen Williams ast over 6.5 (401909094) | reject | 0.193 | 0.222 | - | loss |
| prop | Jalen Williams ast over 9.5 (401909094) | reject | 0.036 | 0.059 | - | loss |
| prop | Jalen Williams fg3m over 0.5 (401909094) | reject | 0.594 | 0.714 | - | win |
| prop | Jalen Williams fg3m over 1.5 (401909094) | reject | 0.247 | 0.373 | - | win |
| prop | Jalen Williams fg3m over 2.5 (401909094) | reject | 0.081 | 0.138 | - | loss |
| prop | Jalen Williams fg3m over 3.5 (401909094) | reject | 0.023 | 0.062 | - | loss |
| prop | Jalen Williams fg3m over 4.5 (401909094) | reject | 0.006 | 0.034 | - | loss |
| prop | Jalen Williams fg3m over 5.5 (401909094) | reject | 0.001 | 0.028 | - | loss |
| prop | Jalen Williams pts over 14.5 (401909094) | reject | 0.509 | 0.750 | - | win |
| prop | Jalen Williams pts over 19.5 (401909094) | reject | 0.308 | 0.455 | - | win |
| prop | Jalen Williams pts over 24.5 (401909094) | reject | 0.172 | 0.211 | - | loss |
| prop | Jalen Williams pts over 29.5 (401909094) | reject | 0.090 | 0.095 | - | loss |
| prop | Jalen Williams pts over 34.5 (401909094) | reject | 0.045 | 0.053 | - | loss |
| prop | Jalen Williams pts over 39.5 (401909094) | reject | 0.021 | 0.028 | - | loss |
| prop | Jalen Williams pts over 9.5 (401909094) | reject | 0.748 | 0.947 | - | win |
| prop | Jalen Williams reb over 12.5 (401909094) | reject | 0.006 | 0.028 | - | loss |
| prop | Jalen Williams reb over 2.5 (401909094) | reject | 0.775 | 0.867 | - | win |
| prop | Jalen Williams reb over 4.5 (401909094) | reject | 0.453 | 0.535 | - | win |
| prop | Jalen Williams reb over 6.5 (401909094) | reject | 0.202 | 0.244 | - | loss |
| prop | Jalen Williams reb over 9.5 (401909094) | reject | 0.041 | 0.062 | - | loss |
| prop | Jamal Murray ast over 12.5 (401909094) | reject | 0.051 | 0.056 | - | loss |
| prop | Jamal Murray ast over 14.5 (401909094) | reject | 0.019 | 0.028 | - | loss |
| prop | Jamal Murray ast over 2.5 (401909094) | reject | 0.927 | 0.952 | - | win |
| prop | Jamal Murray ast over 4.5 (401909094) | reject | 0.738 | 0.750 | - | loss |
| prop | Jamal Murray ast over 9.5 (401909094) | reject | 0.186 | 0.154 | - | loss |
| prop | Jamal Murray fg3m over 0.5 (401909094) | reject | 0.939 | 0.980 | - | loss |
| prop | Jamal Murray fg3m over 1.5 (401909094) | reject | 0.794 | 0.867 | - | loss |
| prop | Jamal Murray fg3m over 2.5 (401909094) | reject | 0.602 | 0.655 | - | loss |
| prop | Jamal Murray fg3m over 3.5 (401909094) | reject | 0.412 | 0.426 | - | loss |
| prop | Jamal Murray fg3m over 4.5 (401909094) | reject | 0.259 | 0.244 | - | loss |
| prop | Jamal Murray fg3m over 5.5 (401909094) | reject | 0.151 | 0.133 | - | loss |
| prop | Jamal Murray fg3m over 6.5 (401909094) | reject | 0.083 | 0.083 | - | loss |
| prop | Jamal Murray fg3m over 7.5 (401909094) | reject | 0.043 | 0.053 | - | loss |
| prop | Jamal Murray fg3m over 8.5 (401909094) | reject | 0.022 | 0.034 | - | loss |
| prop | Jamal Murray fg3m over 9.5 (401909094) | reject | 0.010 | 0.028 | - | loss |
| prop | Jamal Murray pts over 14.5 (401909094) | reject | 0.785 | 0.867 | - | loss |
| prop | Jamal Murray pts over 19.5 (401909094) | reject | 0.632 | 0.655 | - | loss |
| prop | Jamal Murray pts over 24.5 (401909094) | reject | 0.481 | 0.400 | - | loss |
| prop | Jamal Murray pts over 29.5 (401909094) | reject | 0.349 | 0.211 | - | loss |
| prop | Jamal Murray pts over 34.5 (401909094) | reject | 0.245 | 0.105 | - | loss |
| prop | Jamal Murray pts over 39.5 (401909094) | reject | 0.166 | 0.059 | - | loss |
| prop | Jamal Murray pts over 44.5 (401909094) | reject | 0.110 | 0.028 | - | loss |
| prop | Jamal Murray pts over 49.5 (401909094) | reject | 0.071 | 0.028 | - | loss |
| prop | Jamal Murray pts over 9.5 (401909094) | reject | 0.912 | 0.980 | - | loss |
| prop | Jamal Murray reb over 2.5 (401909094) | reject | 0.800 | 0.833 | - | win |
| prop | Jamal Murray reb over 6.5 (401909094) | reject | 0.232 | 0.167 | - | win |
| prop | Jamal Murray reb over 9.5 (401909094) | reject | 0.052 | 0.050 | - | win |
| prop | Jared McCain ast over 2.5 (401909094) | reject | 0.198 | 0.167 | - | loss |
| prop | Jared McCain ast over 4.5 (401909094) | reject | 0.026 | 0.050 | - | loss |
| prop | Jared McCain ast over 6.5 (401909094) | reject | 0.002 | 0.028 | - | loss |
| prop | Jared McCain fg3m over 0.5 (401909094) | reject | 0.863 | 0.900 | - | loss |
| prop | Jared McCain fg3m over 1.5 (401909094) | reject | 0.621 | 0.667 | - | loss |
| prop | Jared McCain fg3m over 3.5 (401909094) | reject | 0.205 | 0.222 | - | loss |
| prop | Jared McCain fg3m over 4.5 (401909094) | reject | 0.100 | 0.118 | - | loss |
| prop | Jared McCain fg3m over 5.5 (401909094) | reject | 0.044 | 0.071 | - | loss |
| prop | Jared McCain fg3m over 6.5 (401909094) | reject | 0.019 | 0.050 | - | loss |
| prop | Jared McCain fg3m over 7.5 (401909094) | reject | 0.007 | 0.028 | - | loss |
| prop | Jared McCain pts over 14.5 (401909094) | reject | 0.323 | 0.263 | - | loss |
| prop | Jared McCain pts over 19.5 (401909094) | reject | 0.152 | 0.105 | - | loss |
| prop | Jared McCain pts over 24.5 (401909094) | reject | 0.065 | 0.056 | - | loss |
| prop | Jared McCain pts over 29.5 (401909094) | reject | 0.026 | 0.028 | - | loss |
| prop | Jared McCain pts over 4.5 (401909094) | reject | 0.887 | 0.875 | - | loss |
| prop | Jared McCain pts over 9.5 (401909094) | reject | 0.595 | 0.556 | - | loss |
| prop | Jared McCain reb over 2.5 (401909094) | reject | 0.453 | 0.333 | - | loss |
| prop | Jared McCain reb over 4.5 (401909094) | reject | 0.135 | 0.095 | - | loss |
| prop | Jared McCain reb over 6.5 (401909094) | reject | 0.028 | 0.034 | - | loss |
| prop | Nikola Jokic ast over 12.5 (401909094) | reject | 0.271 | 0.200 | - | loss |
| prop | Nikola Jokic ast over 14.5 (401909094) | reject | 0.156 | 0.103 | - | loss |
| prop | Nikola Jokic ast over 4.5 (401909094) | reject | 0.927 | 0.952 | - | win |
| prop | Nikola Jokic ast over 6.5 (401909094) | reject | 0.798 | 0.815 | - | loss |
| prop | Nikola Jokic ast over 9.5 (401909094) | reject | 0.523 | 0.508 | - | loss |
| prop | Nikola Jokic fg3m over 0.5 (401909094) | reject | 0.773 | 0.818 | - | win |
| prop | Nikola Jokic fg3m over 1.5 (401909094) | reject | 0.465 | 0.528 | - | loss |
| prop | Nikola Jokic fg3m over 2.5 (401909094) | reject | 0.230 | 0.278 | - | loss |
| prop | Nikola Jokic fg3m over 3.5 (401909094) | reject | 0.098 | 0.138 | - | loss |
| prop | Nikola Jokic fg3m over 4.5 (401909094) | reject | 0.038 | 0.077 | - | loss |
| prop | Nikola Jokic fg3m over 5.5 (401909094) | reject | 0.013 | 0.053 | - | loss |
| prop | Nikola Jokic fg3m over 6.5 (401909094) | reject | 0.004 | 0.028 | - | loss |
| prop | Nikola Jokic pts over 14.5 (401909094) | reject | 0.787 | 0.929 | - | loss |
| prop | Nikola Jokic pts over 19.5 (401909094) | reject | 0.634 | 0.767 | - | loss |
| prop | Nikola Jokic pts over 24.5 (401909094) | reject | 0.483 | 0.528 | - | loss |
| prop | Nikola Jokic pts over 29.5 (401909094) | reject | 0.352 | 0.312 | - | loss |
| prop | Nikola Jokic pts over 34.5 (401909094) | reject | 0.247 | 0.167 | - | loss |
| prop | Nikola Jokic pts over 39.5 (401909094) | reject | 0.168 | 0.087 | - | loss |
| prop | Nikola Jokic pts over 44.5 (401909094) | reject | 0.112 | 0.050 | - | loss |
| prop | Nikola Jokic pts over 49.5 (401909094) | reject | 0.072 | 0.028 | - | loss |
| prop | Nikola Jokic pts over 9.5 (401909094) | reject | 0.913 | 0.988 | - | win |
| prop | Nikola Jokic reb over 12.5 (401909094) | reject | 0.529 | 0.556 | - | loss |
| prop | Nikola Jokic reb over 14.5 (401909094) | reject | 0.387 | 0.368 | - | loss |
| prop | Nikola Jokic reb over 16.5 (401909094) | reject | 0.268 | 0.211 | - | loss |
| prop | Nikola Jokic reb over 19.5 (401909094) | reject | 0.140 | 0.095 | - | loss |
| prop | Nikola Jokic reb over 6.5 (401909094) | reject | 0.915 | 0.968 | - | win |
| prop | Nikola Jokic reb over 9.5 (401909094) | reject | 0.749 | 0.833 | - | loss |
| prop | Shai Gilgeous-Alexander ast over 12.5 (401909094) | reject | 0.077 | 0.062 | - | loss |
| prop | Shai Gilgeous-Alexander ast over 14.5 (401909094) | reject | 0.032 | 0.034 | - | loss |
| prop | Shai Gilgeous-Alexander ast over 2.5 (401909094) | reject | 0.946 | 0.968 | - | win |
| prop | Shai Gilgeous-Alexander ast over 4.5 (401909094) | reject | 0.789 | 0.810 | - | loss |
| prop | Shai Gilgeous-Alexander ast over 6.5 (401909094) | reject | 0.556 | 0.556 | - | loss |
| prop | Shai Gilgeous-Alexander ast over 9.5 (401909094) | reject | 0.242 | 0.182 | - | loss |
| prop | Shai Gilgeous-Alexander fg3m over 0.5 (401909094) | reject | 0.776 | 0.867 | - | win |
| prop | Shai Gilgeous-Alexander fg3m over 1.5 (401909094) | reject | 0.469 | 0.565 | - | win |
| prop | Shai Gilgeous-Alexander fg3m over 2.5 (401909094) | reject | 0.233 | 0.303 | - | win |
| prop | Shai Gilgeous-Alexander fg3m over 3.5 (401909094) | reject | 0.100 | 0.138 | - | loss |
| prop | Shai Gilgeous-Alexander fg3m over 4.5 (401909094) | reject | 0.038 | 0.077 | - | loss |
| prop | Shai Gilgeous-Alexander fg3m over 5.5 (401909094) | reject | 0.014 | 0.048 | - | loss |
| prop | Shai Gilgeous-Alexander fg3m over 6.5 (401909094) | reject | 0.004 | 0.028 | - | loss |
| prop | Shai Gilgeous-Alexander pts over 14.5 (401909094) | reject | 0.835 | 0.990 | - | win |
| prop | Shai Gilgeous-Alexander pts over 19.5 (401909094) | reject | 0.704 | 0.941 | - | loss |
| prop | Shai Gilgeous-Alexander pts over 24.5 (401909094) | reject | 0.565 | 0.810 | - | loss |
| prop | Shai Gilgeous-Alexander pts over 29.5 (401909094) | reject | 0.436 | 0.592 | - | loss |
| prop | Shai Gilgeous-Alexander pts over 34.5 (401909094) | reject | 0.325 | 0.368 | - | loss |
| prop | Shai Gilgeous-Alexander pts over 39.5 (401909094) | reject | 0.235 | 0.190 | - | loss |
| prop | Shai Gilgeous-Alexander pts over 44.5 (401909094) | reject | 0.167 | 0.100 | - | loss |
| prop | Shai Gilgeous-Alexander pts over 49.5 (401909094) | reject | 0.115 | 0.056 | - | loss |
| prop | Shai Gilgeous-Alexander reb over 2.5 (401909094) | reject | 0.743 | 0.796 | - | loss |
| prop | Shai Gilgeous-Alexander reb over 4.5 (401909094) | reject | 0.408 | 0.385 | - | loss |
| prop | Shai Gilgeous-Alexander reb over 6.5 (401909094) | reject | 0.168 | 0.148 | - | loss |
| prop | Shai Gilgeous-Alexander reb over 9.5 (401909094) | reject | 0.030 | 0.048 | - | loss |
| prop | Aaron Gordon ast under 2.5 (401909094) | reject | 0.457 | 0.552 | - | win |
| prop | Aaron Gordon fg3m under 1.5 (401909094) | reject | 0.558 | 0.524 | - | loss |
| prop | Aaron Gordon pts under 14.5 (401909094) | reject | 0.562 | 0.549 | - | loss |
| prop | Aaron Gordon reb over 5.5 (401909094) | reject | 0.479 | 0.565 | - | win |
| prop | Aaron Gordon reb under 5.5 (401909094) | reject | 0.521 | 0.565 | - | loss |
| prop | Nikola Jokic ast under 9.5 (401909094) | reject | 0.477 | 0.562 | - | win |
| prop | Nikola Jokic fg3m under 1.5 (401909094) | reject | 0.535 | 0.526 | - | win |
| prop | Nikola Jokic reb under 12.5 (401909094) | reject | 0.471 | 0.513 | - | win |
| prop | Cameron Johnson ast under 2.5 (401909094) | reject | 0.525 | 0.633 | - | win |
| prop | Cameron Johnson fg3m under 2.5 (401909094) | reject | 0.665 | 0.649 | - | win |
| prop | Cameron Johnson reb over 3.5 (401909094) | reject | 0.502 | 0.565 | - | loss |
| prop | Cameron Johnson reb under 3.5 (401909094) | reject | 0.498 | 0.565 | - | win |
| prop | Jamal Murray ast over 5.5 (401909094) | reject | 0.613 | 0.581 | - | loss |
| prop | Jamal Murray fg3m under 2.5 (401909094) | reject | 0.398 | 0.461 | - | win |
| prop | Jamal Murray pts over 22.5 (401909094) | reject | 0.539 | 0.546 | - | loss |
| prop | Jamal Murray pts under 22.5 (401909094) | reject | 0.461 | 0.546 | - | win |
| prop | Jamal Murray reb over 3.5 (401909094) | reject | 0.650 | 0.606 | - | win |
| prop | Jamal Murray reb under 3.5 (401909094) | reject | 0.350 | 0.606 | - | loss |
| prop | Isaiah Hartenstein ast under 2.5 (401909094) | reject | 0.583 | 0.490 | - | win |
| prop | Isaiah Hartenstein pts over 8.5 (401909094) | reject | 0.283 | 0.556 | - | loss |
| prop | Isaiah Hartenstein pts under 8.5 (401909094) | reject | 0.717 | 0.556 | - | win |
| prop | Isaiah Hartenstein reb over 7.5 (401909094) | reject | 0.370 | 0.585 | - | loss |
| prop | Isaiah Hartenstein reb under 7.5 (401909094) | reject | 0.630 | 0.585 | - | win |
| prop | Shai Gilgeous-Alexander ast under 6.5 (401909094) | reject | 0.444 | 0.556 | - | win |
| prop | Shai Gilgeous-Alexander fg3m under 1.5 (401909094) | reject | 0.531 | 0.478 | - | loss |
| prop | Shai Gilgeous-Alexander pts over 30.5 (401909094) | reject | 0.412 | 0.556 | - | loss |
| prop | Shai Gilgeous-Alexander pts under 30.5 (401909094) | reject | 0.588 | 0.556 | - | win |
| prop | Christian Braun fg3m under 1.5 (401909094) | reject | 0.705 | 0.641 | - | win |
| prop | Christian Braun pts over 10.5 (401909094) | reject | 0.525 | 0.541 | - | loss |
| prop | Christian Braun pts under 10.5 (401909094) | reject | 0.475 | 0.541 | - | win |
| prop | Christian Braun reb under 4.5 (401909094) | reject | 0.506 | 0.617 | - | loss |
| prop | Chet Holmgren ast over 1.5 (401909094) | reject | 0.430 | 0.606 | - | win |
| prop | Chet Holmgren ast under 1.5 (401909094) | reject | 0.570 | 0.606 | - | loss |
| prop | Chet Holmgren pts under 14.5 (401909094) | reject | 0.508 | 0.513 | - | win |
| prop | Chet Holmgren reb over 8.5 (401909094) | reject | 0.504 | 0.568 | - | win |
| prop | Chet Holmgren reb under 8.5 (401909094) | reject | 0.496 | 0.568 | - | loss |
| prop | Jalen Williams ast under 4.5 (401909094) | reject | 0.551 | 0.568 | - | win |
| prop | Jalen Williams fg3m under 1.5 (401909094) | reject | 0.753 | 0.694 | - | loss |
| prop | Jalen Williams pts over 18.5 (401909094) | reject | 0.343 | 0.532 | - | win |
| prop | Jalen Williams pts under 18.5 (401909094) | reject | 0.657 | 0.532 | - | loss |
| prop | Jalen Williams reb under 4.5 (401909094) | reject | 0.547 | 0.505 | - | loss |
| prop | Cason Wallace ast under 2.5 (401909094) | reject | 0.661 | 0.649 | - | win |
| prop | Cason Wallace fg3m under 1.5 (401909094) | reject | 0.676 | 0.595 | - | loss |
| prop | Cason Wallace pts over 8.5 (401909094) | reject | 0.342 | 0.538 | - | win |
| prop | Cason Wallace pts under 8.5 (401909094) | reject | 0.658 | 0.538 | - | loss |
| prop | Jared McCain fg3m under 1.5 (401909094) | reject | 0.379 | 0.412 | - | win |
| prop | Ajay Mitchell ast over 3.5 (401909094) | reject | 0.468 | 0.641 | - | loss |
| prop | Ajay Mitchell ast under 3.5 (401909094) | reject | 0.532 | 0.641 | - | win |
| prop | Ajay Mitchell reb under 2.5 (401909094) | reject | 0.421 | 0.455 | - | win |
| prop | Nikola Jokic reb over 4.5 (401909094) | reject | 0.973 | 0.990 | - | win |
| prop | Alex Caruso fg3m under 1.5 (401909094) | reject | 0.524 | 0.654 | - | win |
| spread | away 2.5 (401909834) | reject | 0.528 | 0.528 | -0.000 | win |
| prop | Nikola Jokic pts under 24.5 (401909094) | reject | 0.517 | 0.518 | -0.003 | win |
| ml | away (401909834) | reject | 0.463 | 0.469 | -0.014 | win |
| ml | home (401909838) | reject | 0.543 | 0.552 | -0.016 | win |
| prop | Jared McCain pts over 10.5 (401909094) | reject | 0.534 | 0.543 | -0.017 | loss |
| prop | Jarrett Allen pts over 12.5 (401909093) | reject | 0.530 | 0.541 | -0.020 | win |
| ml | away (401909093) | reject | 0.451 | 0.461 | -0.021 | loss |
| spread | away 2.5 (401909093) | reject | 0.516 | 0.528 | -0.022 | loss |
| spread | away 8.5 (401909094) | reject | 0.526 | 0.539 | -0.024 | loss |
| prop | James Harden pts over 17.5 (401909093) | reject | 0.541 | 0.556 | -0.026 | loss |
| prop | Chet Holmgren fg3m under 1.5 (401909094) | reject | 0.684 | 0.704 | -0.029 | win |
| spread | home -1.5 (401909838) | reject | 0.510 | 0.526 | -0.030 | win |
| prop | Jared McCain fg3m under 2.5 (401909094) | reject | 0.620 | 0.645 | -0.040 | win |
| prop | Jarrett Allen reb under 8.5 (401909093) | reject | 0.542 | 0.568 | -0.046 | win |
| prop | Chet Holmgren fg3m under 0.5 (401909094) | reject | 0.340 | 0.357 | -0.049 | win |
| ml | home (401909834) | reject | 0.537 | 0.565 | -0.050 | loss |
| ml | home (401909093) | reject | 0.549 | 0.578 | -0.050 | win |
| prop | Evan Mobley pts under 17.5 (401909093) | reject | 0.509 | 0.538 | -0.054 | loss |
| spread | away 1.5 (401909838) | reject | 0.490 | 0.519 | -0.056 | loss |
| ml | home (401909094) | reject | 0.724 | 0.767 | -0.057 | win |
| prop | Jarrett Allen reb over 7.5 (401909093) | reject | 0.561 | 0.595 | -0.057 | loss |
| prop | Tyrese Maxey pts over 23.5 (401909093) | reject | 0.518 | 0.552 | -0.062 | win |
| ml | away (401909838) | reject | 0.457 | 0.488 | -0.063 | loss |
| ml | home (401909841) | reject | 0.549 | 0.587 | -0.065 | win |
| spread | home -8.5 (401909094) | reject | 0.474 | 0.507 | -0.066 | win |
| spread | home -2.5 (401909093) | reject | 0.484 | 0.519 | -0.069 | win |
| prop | Shai Gilgeous-Alexander reb over 3.5 (401909094) | reject | 0.573 | 0.617 | -0.072 | loss |
| prop | Jarrett Allen pts under 13.5 (401909093) | reject | 0.521 | 0.562 | -0.073 | loss |
| spread | home -2.5 (401909841) | reject | 0.484 | 0.528 | -0.085 | win |
| prop | Evan Mobley pts over 17.5 (401909093) | reject | 0.491 | 0.538 | -0.086 | win |
| spread | home -2.5 (401909834) | reject | 0.472 | 0.517 | -0.087 | loss |
| spread | away 2.5 (401909090) | reject | 0.481 | 0.535 | -0.100 | win |
| ml | home (401909092) | reject | 0.625 | 0.697 | -0.104 | win |
| prop | Jared McCain fg3m over 2.5 (401909094) | reject | 0.380 | 0.426 | -0.106 | loss |
| prop | Christian Braun ast under 2.5 (401909094) | reject | 0.592 | 0.662 | -0.107 | win |
| prop | Jaylen Brown reb under 6.5 (401909093) | reject | 0.504 | 0.565 | -0.108 | loss |
| spread | away 1.5 (401909091) | reject | 0.471 | 0.528 | -0.108 | win |
| prop | Ajay Mitchell pts under 10.5 (401909094) | reject | 0.505 | 0.568 | -0.111 | loss |
| ml | away (401909091) | reject | 0.438 | 0.495 | -0.114 | win |
| prop | Joel Embiid reb over 7.5 (401909093) | reject | 0.524 | 0.592 | -0.115 | loss |
| ml | home (401909840) | reject | 0.714 | 0.811 | -0.120 | win |
| prop | Jaylen Brown reb over 6.5 (401909093) | reject | 0.496 | 0.565 | -0.122 | win |
| prop | Chet Holmgren fg3m over 1.5 (401909094) | reject | 0.316 | 0.361 | -0.124 | loss |
| prop | Tyrese Maxey pts under 23.5 (401909093) | reject | 0.482 | 0.552 | -0.128 | loss |
| prop | Ajay Mitchell pts over 10.5 (401909094) | reject | 0.495 | 0.568 | -0.129 | win |
| prop | Jarrett Allen pts under 12.5 (401909093) | reject | 0.470 | 0.541 | -0.130 | loss |
| ml | home (401909837) | reject | 0.705 | 0.815 | -0.134 | win |
| prop | Jamal Murray ast under 6.5 (401909094) | reject | 0.515 | 0.595 | -0.135 | win |
| prop | Sam Merrill fg3m over 1.5 (401909093) | reject | 0.568 | 0.658 | -0.137 | loss |
| prop | Jared McCain pts under 10.5 (401909094) | reject | 0.466 | 0.543 | -0.143 | win |
| prop | Jarrett Allen pts over 13.5 (401909093) | reject | 0.479 | 0.562 | -0.147 | win |
| prop | Cameron Johnson pts over 12.5 (401909094) | reject | 0.458 | 0.541 | -0.153 | loss |
| spread | away 1.5 (401909090) | reject | 0.449 | 0.535 | -0.161 | win |
| prop | Nikola Jokic pts over 25.5 (401909094) | reject | 0.455 | 0.543 | -0.162 | loss |
| prop | Joel Embiid ast under 4.5 (401909093) | reject | 0.516 | 0.617 | -0.164 | win |
| prop | James Harden pts under 17.5 (401909093) | reject | 0.459 | 0.556 | -0.174 | win |
| prop | Anfernee Simons fg3m under 2.5 (401909093) | reject | 0.535 | 0.649 | -0.175 | win |
| prop | Jamal Murray reb under 4.5 (401909094) | reject | 0.508 | 0.621 | -0.181 | loss |
| spread | home -6.5 (401909092) | reject | 0.431 | 0.528 | -0.185 | win |
| prop | LeBron James reb over 6.5 (401909093) | reject | 0.482 | 0.592 | -0.186 | win |
| prop | Evan Mobley fg3m under 0.5 (401909093) | reject | 0.340 | 0.418 | -0.189 | loss |
| spread | home -9.5 (401909840) | reject | 0.430 | 0.531 | -0.190 | win |
| prop | Donovan Mitchell pts over 26.5 (401909093) | reject | 0.438 | 0.541 | -0.190 | win |
| total | over 219.5 (401909836) | reject | 0.423 | 0.524 | -0.192 | loss |
| prop | Jarrett Allen reb over 8.5 (401909093) | reject | 0.458 | 0.568 | -0.194 | loss |
| prop | Joel Embiid reb under 7.5 (401909093) | reject | 0.476 | 0.592 | -0.195 | win |
| prop | Jamal Murray pts under 21.5 (401909094) | reject | 0.430 | 0.538 | -0.200 | win |
| ml | away (401909088) | reject | 0.438 | 0.550 | -0.203 | loss |
| spread | away 4.5 (401909842) | reject | 0.397 | 0.505 | -0.214 | loss |
| prop | Ajay Mitchell pts over 11.5 (401909094) | reject | 0.435 | 0.556 | -0.216 | win |
| prop | VJ Edgecombe reb under 4.5 (401909093) | reject | 0.367 | 0.469 | -0.219 | loss |
| spread | away -1.5 (401909088) | reject | 0.406 | 0.524 | -0.224 | loss |
| total | over 227.5 (401909842) | reject | 0.402 | 0.519 | -0.225 | loss |
| prop | Ajay Mitchell ast under 2.5 (401909094) | reject | 0.340 | 0.439 | -0.225 | win |
| prop | Sam Merrill fg3m over 2.5 (401909093) | reject | 0.325 | 0.422 | -0.229 | loss |
| ml | away (401909090) | reject | 0.416 | 0.541 | -0.231 | win |
| ml | home (401909835) | reject | 0.480 | 0.636 | -0.245 | win |
| spread | home -10.5 (401909837) | reject | 0.389 | 0.519 | -0.250 | win |
| prop | Joel Embiid reb over 8.5 (401909093) | reject | 0.419 | 0.562 | -0.254 | loss |
| spread | away -1.5 (401909090) | reject | 0.385 | 0.519 | -0.259 | win |
| prop | Jarrett Allen reb under 7.5 (401909093) | reject | 0.439 | 0.595 | -0.263 | win |
| total | over 220.5 (401909088) | reject | 0.383 | 0.524 | -0.269 | win |
| prop | LeBron James pts under 16.5 (401909093) | reject | 0.405 | 0.559 | -0.275 | loss |
| ml | away (401909842) | reject | 0.276 | 0.383 | -0.279 | loss |
| prop | Anfernee Simons fg3m over 2.5 (401909093) | reject | 0.465 | 0.649 | -0.285 | loss |
| prop | Jaylen Brown pts under 20.5 (401909093) | reject | 0.393 | 0.552 | -0.288 | loss |
| total | over 235.5 (401909094) | reject | 0.372 | 0.528 | -0.296 | loss |
| prop | Shai Gilgeous-Alexander reb under 3.5 (401909094) | reject | 0.427 | 0.617 | -0.308 | win |
| prop | Anfernee Simons pts under 10.5 (401909093) | reject | 0.375 | 0.546 | -0.313 | win |
| total | over 221.5 (401909088) | reject | 0.362 | 0.535 | -0.322 | win |
| prop | VJ Edgecombe pts under 11.5 (401909093) | reject | 0.376 | 0.556 | -0.324 | win |
| total | over 236.5 (401909094) | reject | 0.352 | 0.526 | -0.332 | loss |
| spread | home -4.5 (401909835) | reject | 0.354 | 0.531 | -0.333 | win |
| prop | Jamal Murray ast under 5.5 (401909094) | reject | 0.387 | 0.581 | -0.335 | win |
| prop | James Harden ast over 6.5 (401909093) | reject | 0.379 | 0.581 | -0.348 | loss |
| total | over 229.5 (401909090) | reject | 0.346 | 0.535 | -0.353 | loss |
| prop | Alex Caruso reb under 2.5 (401909094) | reject | 0.321 | 0.503 | -0.361 | loss |
| total | over 230.5 (401909090) | reject | 0.326 | 0.512 | -0.363 | loss |
| ml | away (401909839) | reject | 0.385 | 0.606 | -0.365 | win |
| prop | Ajay Mitchell fg3m over 1.5 (401909094) | reject | 0.229 | 0.366 | -0.376 | loss |
| spread | away 4.5 (401909089) | reject | 0.322 | 0.519 | -0.381 | win |
| total | over 230.5 (401909840) | reject | 0.314 | 0.512 | -0.387 | win |
| total | over 242.5 (401909838) | reject | 0.313 | 0.512 | -0.390 | loss |
| total | over 231.5 (401909090) | reject | 0.307 | 0.522 | -0.411 | loss |
| prop | Anfernee Simons pts under 9.5 (401909093) | reject | 0.320 | 0.552 | -0.420 | win |
| prop | VJ Edgecombe pts under 10.5 (401909093) | reject | 0.325 | 0.568 | -0.428 | loss |
| spread | away -3.5 (401909839) | reject | 0.296 | 0.519 | -0.429 | loss |
| prop | Christian Braun ast under 1.5 (401909094) | reject | 0.346 | 0.610 | -0.432 | win |
| prop | Alex Caruso ast under 1.5 (401909094) | reject | 0.349 | 0.617 | -0.434 | loss |
| spread | home 1.5 (401909836) | reject | 0.296 | 0.528 | -0.439 | loss |
| total | over 239.5 (401909839) | reject | 0.280 | 0.512 | -0.454 | win |
| prop | Alex Caruso pts under 6.5 (401909094) | reject | 0.303 | 0.556 | -0.455 | loss |
| prop | Kentavious Caldwell-Pope pts under 6.5 (401909093) | reject | 0.310 | 0.575 | -0.461 | win |
| total | over 239.5 (401909091) | reject | 0.280 | 0.524 | -0.465 | loss |
| ml | away (401909089) | reject | 0.212 | 0.397 | -0.465 | win |
| ml | home (401909836) | reject | 0.268 | 0.505 | -0.469 | loss |
| total | over 236.5 (401909093) | reject | 0.274 | 0.526 | -0.479 | loss |
| total | over 233.5 (401909834) | reject | 0.268 | 0.535 | -0.499 | win |
| total | over 238.5 (401909835) | reject | 0.254 | 0.524 | -0.515 | win |
| total | over 237.5 (401909837) | reject | 0.253 | 0.528 | -0.521 | loss |
| total | over 232.5 (401909089) | reject | 0.243 | 0.512 | -0.525 | loss |
| total | over 233.5 (401909092) | reject | 0.246 | 0.524 | -0.530 | loss |
| prop | Cason Wallace reb over 3.5 (401909094) | reject | 0.290 | 0.633 | -0.541 | loss |
| prop | Kentavious Caldwell-Pope pts under 5.5 (401909093) | reject | 0.237 | 0.535 | -0.556 | win |
| total | over 231.5 (401909841) | reject | 0.224 | 0.519 | -0.568 | loss |
| prop | Jaylon Tyson pts over 9.5 (401909093) | reject | 0.098 | 0.556 | -0.824 | loss |
