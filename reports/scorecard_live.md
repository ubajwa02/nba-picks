# Live scorecard

Settled predictions since 2026-10-20: **1777** (deduplicated). Descriptive only: tiny sample, no inference. Market prob = 1/price (includes vig).

Brier: model 0.1483 vs market-implied 0.1498 (n=1777; lower is better).

## Calibration

| prob bucket | n | predicted | market | actual |
|---|---|---|---|---|
| <40% | 927 | 0.138 | 0.175 | 0.111 |
| 40-50% | 243 | 0.455 | 0.533 | 0.465 |
| 50-60% | 227 | 0.548 | 0.574 | 0.489 |
| 60-70% | 165 | 0.646 | 0.638 | 0.630 |
| >=70% | 215 | 0.821 | 0.841 | 0.842 |

## By EV bucket

| group | n | wins | win rate | units |
|---|---|---|---|---|
| EV 0-5% | 35 | 15 | 0.429 | -6.32 |
| EV 5-15% | 41 | 21 | 0.512 | -4.03 |
| EV<0 | 256 | 130 | 0.508 | -24.37 |
| EV>=15% | 55 | 28 | 0.509 | -1.83 |

## By market

| group | n | wins | win rate | units |
|---|---|---|---|---|
| ml | 38 | 19 | 0.500 | -6.00 |
| prop | 1642 | 545 | 0.332 | -554.64 |
| spread | 46 | 23 | 0.500 | -2.26 |
| total | 51 | 25 | 0.490 | -3.38 |

## By decision

| group | n | wins | win rate | units |
|---|---|---|---|---|
| hold | 88 | 41 | 0.466 | -12.31 |
| reject | 1674 | 562 | 0.336 | -555.30 |
| watch | 15 | 9 | 0.600 | +1.32 |

## Posted leans (1u flat)

Record 16-9-0, +4.62u, pending 6.

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
| 2026-10-26 | Christian Braun u1.5 fg3m | -196 | None | pending | +0.00 |
| 2026-10-26 | CJ McCollum u3.5 ast | -175 | None | pending | +0.00 |
| 2026-10-26 | Jalen Green u2.5 fg3m | -196 | None | pending | +0.00 |
| 2026-10-26 | Collin Gillespie u2.5 fg3m | -185 | None | pending | +0.00 |
| 2026-10-26 | Tim Hardaway Jr. u2.5 reb | -182 | None | pending | +0.00 |
| 2026-10-26 | Jaren Jackson Jr. u2.5 ast | -192 | None | pending | +0.00 |

## Rows

| market | pick | decision | model p | book p | EV | result |
|---|---|---|---|---|---|---|
| prop | Jaylon Tyson pts under 9.5 (401909093) | hold | 0.902 | 0.556 | +0.624 | win |
| ml | away (401909869) | hold | 0.647 | 0.405 | +0.599 | loss |
| prop | Jerami Grant fg3m over 1.5 (401909838) | hold | 0.669 | 0.435 | +0.540 | win |
| total | under 234.5 (401909092) | hold | 0.771 | 0.512 | +0.505 | win |
| total | under 231.5 (401909841) | hold | 0.776 | 0.526 | +0.475 | win |
| total | under 237.5 (401909837) | hold | 0.747 | 0.512 | +0.459 | win |
| spread | away 5.5 (401909869) | hold | 0.783 | 0.537 | +0.457 | win |
| total | under 233.5 (401909092) | hold | 0.754 | 0.519 | +0.452 | win |
| total | under 234.5 (401909834) | hold | 0.749 | 0.519 | +0.443 | loss |
| spread | away 4.5 (401909869) | hold | 0.758 | 0.526 | +0.441 | win |
| prop | Kentavious Caldwell-Pope pts over 5.5 (401909093) | hold | 0.763 | 0.535 | +0.426 | loss |
| total | under 238.5 (401909835) | hold | 0.746 | 0.524 | +0.424 | loss |
| total | under 237.5 (401909093) | hold | 0.744 | 0.524 | +0.420 | win |
| total | under 232.5 (401909089) | hold | 0.757 | 0.535 | +0.415 | win |
| ml | home (401909839) | hold | 0.615 | 0.435 | +0.414 | loss |
| total | under 236.5 (401909093) | hold | 0.726 | 0.522 | +0.392 | win |
| prop | LaMelo Ball ast under 7.5 (401909869) | hold | 0.807 | 0.585 | +0.381 | win |
| total | under 240.5 (401909091) | hold | 0.738 | 0.535 | +0.379 | win |
| total | under 239.5 (401909839) | hold | 0.720 | 0.524 | +0.375 | loss |
| ml | away (401909837) | hold | 0.295 | 0.217 | +0.355 | loss |
| spread | away -1.5 (401909836) | hold | 0.704 | 0.519 | +0.355 | win |
| ml | away (401909836) | hold | 0.732 | 0.541 | +0.352 | win |
| spread | home 3.5 (401909839) | hold | 0.704 | 0.526 | +0.338 | win |
| prop | Brandon Miller pts under 24.5 (401909868) | hold | 0.713 | 0.538 | +0.326 | loss |
| prop | Josh Giddey ast over 9.5 (401909837) | hold | 0.637 | 0.481 | +0.324 | loss |
| total | under 242.5 (401909838) | hold | 0.687 | 0.526 | +0.307 | win |
| prop | LaMelo Ball pts under 19.5 (401909869) | hold | 0.702 | 0.538 | +0.305 | win |
| ml | away (401909835) | hold | 0.520 | 0.398 | +0.304 | loss |
| prop | Cam Spencer fg3m over 1.5 (401909838) | hold | 0.531 | 0.408 | +0.302 | loss |
| total | under 231.5 (401909090) | hold | 0.693 | 0.535 | +0.295 | win |
| spread | home -4.5 (401909089) | hold | 0.678 | 0.524 | +0.295 | loss |
| total | under 230.5 (401909840) | hold | 0.686 | 0.535 | +0.282 | loss |
| prop | James Harden ast under 6.5 (401909093) | hold | 0.621 | 0.490 | +0.266 | win |
| spread | away 4.5 (401909835) | hold | 0.646 | 0.512 | +0.261 | loss |
| ml | away (401909840) | hold | 0.286 | 0.227 | +0.260 | loss |
| prop | Alex Caruso pts over 6.5 (401909094) | hold | 0.697 | 0.556 | +0.255 | win |
| prop | Anthony Edwards pts under 27.5 (401909869) | hold | 0.670 | 0.535 | +0.253 | loss |
| prop | LaMelo Ball reb under 4.5 (401909869) | hold | 0.692 | 0.556 | +0.246 | win |
| total | under 221.5 (401909088) | hold | 0.638 | 0.512 | +0.245 | loss |
| total | under 236.5 (401909094) | hold | 0.648 | 0.522 | +0.243 | win |
| prop | Cedric Coward fg3m under 1.5 (401909838) | hold | 0.573 | 0.461 | +0.243 | win |
| prop | Anfernee Simons pts over 9.5 (401909093) | hold | 0.680 | 0.552 | +0.230 | loss |
| prop | Naz Reid pts under 18.5 (401909868) | hold | 0.654 | 0.532 | +0.229 | win |
| ml | home (401909089) | hold | 0.788 | 0.643 | +0.225 | loss |
| prop | James Harden ast under 6.5 (401909869) | hold | 0.671 | 0.556 | +0.207 | loss |
| prop | Kentavious Caldwell-Pope pts over 6.5 (401909093) | hold | 0.690 | 0.575 | +0.201 | loss |
| total | under 233.5 (401909869) | hold | 0.630 | 0.526 | +0.197 | loss |
| prop | Alex Caruso reb over 2.5 (401909094) | hold | 0.679 | 0.568 | +0.195 | win |
| prop | VJ Edgecombe pts over 10.5 (401909093) | hold | 0.675 | 0.568 | +0.188 | win |
| total | under 220.5 (401909088) | hold | 0.617 | 0.524 | +0.178 | loss |
| spread | away 10.5 (401909837) | hold | 0.611 | 0.524 | +0.166 | loss |
| spread | home 1.5 (401909090) | hold | 0.615 | 0.528 | +0.164 | loss |
| prop | Jaden McDaniels pts under 15.5 (401909869) | hold | 0.622 | 0.535 | +0.164 | win |
| prop | Donovan Mitchell ast under 4.5 (401909869) | hold | 0.669 | 0.575 | +0.164 | loss |
| ml | home (401909090) | hold | 0.584 | 0.505 | +0.156 | loss |
| total | under 231.5 (401909869) | hold | 0.588 | 0.512 | +0.149 | loss |
| prop | Dennis Schroder pts under 14.5 (401909868) | hold | 0.636 | 0.556 | +0.145 | win |
| prop | Anfernee Simons pts over 10.5 (401909093) | hold | 0.625 | 0.546 | +0.143 | loss |
| total | under 232.5 (401909869) | hold | 0.609 | 0.535 | +0.139 | loss |
| total | under 227.5 (401909842) | watch | 0.598 | 0.526 | +0.136 | win |
| ml | home (401909088) | watch | 0.562 | 0.495 | +0.135 | win |
| spread | home 1.5 (401909088) | watch | 0.594 | 0.524 | +0.133 | win |
| prop | VJ Edgecombe pts over 11.5 (401909093) | hold | 0.624 | 0.556 | +0.124 | loss |
| spread | home -2.5 (401909868) | hold | 0.589 | 0.524 | +0.124 | win |
| prop | Cason Wallace reb under 3.5 (401909094) | hold | 0.710 | 0.633 | +0.121 | win |
| spread | home -4.5 (401909842) | watch | 0.603 | 0.539 | +0.119 | win |
| ml | home (401909842) | watch | 0.724 | 0.649 | +0.115 | win |
| spread | away 9.5 (401909840) | hold | 0.570 | 0.512 | +0.113 | loss |
| ml | home (401909868) | hold | 0.652 | 0.587 | +0.110 | win |
| prop | Ajay Mitchell fg3m under 1.5 (401909094) | hold | 0.771 | 0.699 | +0.103 | win |
| prop | Anthony Edwards fg3m under 3.5 (401909869) | hold | 0.664 | 0.602 | +0.102 | loss |
| spread | away 6.5 (401909092) | hold | 0.569 | 0.517 | +0.102 | loss |
| total | under 219.5 (401909836) | watch | 0.577 | 0.524 | +0.101 | win |
| prop | Jaylen Brown pts over 20.5 (401909093) | hold | 0.607 | 0.552 | +0.098 | win |
| prop | Keyonte George pts over 19.5 (401909838) | watch | 0.609 | 0.556 | +0.097 | win |
| prop | Jamal Murray reb over 4.5 (401909094) | hold | 0.492 | 0.448 | +0.096 | win |
| spread | home -1.5 (401909090) | watch | 0.551 | 0.505 | +0.092 | loss |
| prop | Jaden McDaniels ast under 2.5 (401909869) | hold | 0.593 | 0.543 | +0.092 | loss |
| ml | away (401909092) | hold | 0.375 | 0.345 | +0.089 | loss |
| spread | away 13.5 (401909870) | hold | 0.557 | 0.512 | +0.087 | loss |
| prop | Immanuel Quickley ast under 6.5 (401909837) | hold | 0.658 | 0.606 | +0.086 | loss |
| prop | LeBron James reb under 6.5 (401909093) | hold | 0.518 | 0.478 | +0.083 | loss |
| prop | LaMelo Ball fg3m under 3.5 (401909869) | hold | 0.627 | 0.581 | +0.079 | win |
| prop | Jaylon Tyson reb under 4.5 (401909869) | hold | 0.656 | 0.610 | +0.076 | win |
| prop | Christian Braun ast over 1.5 (401909094) | hold | 0.654 | 0.610 | +0.072 | loss |
| prop | Jaden McDaniels fg3m under 1.5 (401909869) | hold | 0.674 | 0.629 | +0.072 | loss |
| prop | LeBron James pts over 16.5 (401909093) | hold | 0.595 | 0.559 | +0.065 | win |
| prop | Rudy Gobert reb under 11.5 (401909869) | hold | 0.572 | 0.538 | +0.064 | loss |
| prop | Joel Embiid ast over 4.5 (401909093) | hold | 0.484 | 0.455 | +0.064 | loss |
| prop | Jamal Murray pts over 21.5 (401909094) | hold | 0.570 | 0.538 | +0.060 | loss |
| prop | Grayson Allen fg3m under 3.5 (401909868) | hold | 0.658 | 0.621 | +0.059 | win |
| prop | Terrence Shannon Jr. reb under 2.5 (401909869) | hold | 0.595 | 0.562 | +0.059 | loss |
| prop | Bilal Coulibaly pts over 9.5 (401909868) | hold | 0.588 | 0.556 | +0.058 | loss |
| prop | VJ Edgecombe reb over 4.5 (401909093) | hold | 0.633 | 0.599 | +0.058 | win |
| prop | Jaren Jackson Jr. ast under 2.5 (401909838) | watch | 0.694 | 0.658 | +0.055 | win |
| prop | Alex Caruso ast over 1.5 (401909094) | hold | 0.651 | 0.617 | +0.054 | win |
| prop | Sam Merrill fg3m under 1.5 (401909093) | reject | 0.432 | 0.412 | +0.050 | win |
| prop | Ajay Mitchell ast over 2.5 (401909094) | hold | 0.660 | 0.629 | +0.050 | loss |
| prop | James Harden fg3m over 2.5 (401909869) | reject | 0.426 | 0.407 | +0.048 | win |
| prop | Donovan Mitchell pts under 25.5 (401909869) | reject | 0.574 | 0.549 | +0.045 | loss |
| prop | Jaylen Wells fg3m over 1.5 (401909838) | watch | 0.622 | 0.595 | +0.045 | loss |
| prop | Donovan Mitchell pts under 26.5 (401909093) | reject | 0.562 | 0.541 | +0.040 | loss |
| prop | Sam Merrill fg3m under 2.5 (401909093) | reject | 0.675 | 0.649 | +0.039 | win |
| prop | Brandon Miller reb under 5.5 (401909868) | reject | 0.618 | 0.595 | +0.038 | loss |
| total | under 233.5 (401909870) | watch | 0.555 | 0.535 | +0.038 | win |
| prop | Jaylon Tyson pts under 8.5 (401909869) | reject | 0.564 | 0.543 | +0.038 | loss |
| prop | James Harden pts under 17.5 (401909869) | reject | 0.554 | 0.535 | +0.035 | loss |
| prop | Joel Embiid reb under 8.5 (401909093) | reject | 0.581 | 0.562 | +0.034 | win |
| total | under 232.5 (401909870) | watch | 0.534 | 0.517 | +0.032 | loss |
| prop | Sam Merrill fg3m under 1.5 (401909869) | reject | 0.448 | 0.435 | +0.031 | win |
| prop | Evan Mobley pts under 17.5 (401909869) | reject | 0.550 | 0.535 | +0.029 | win |
| spread | home -2.5 (401909090) | watch | 0.519 | 0.507 | +0.022 | loss |
| ml | home (401909091) | watch | 0.562 | 0.550 | +0.022 | loss |
| prop | Jarrett Allen pts under 13.5 (401909869) | reject | 0.552 | 0.541 | +0.022 | win |
| prop | Ayo Dosunmu pts under 13.5 (401909869) | reject | 0.557 | 0.546 | +0.020 | win |
| prop | Jamal Murray ast over 6.5 (401909094) | reject | 0.485 | 0.476 | +0.019 | loss |
| prop | Grayson Allen pts under 15.5 (401909868) | reject | 0.563 | 0.552 | +0.019 | win |
| spread | home -1.5 (401909091) | watch | 0.529 | 0.519 | +0.019 | loss |
| prop | Evan Mobley fg3m over 0.5 (401909093) | reject | 0.660 | 0.649 | +0.017 | win |
| prop | Jonathan Kuminga pts over 11.5 (401909869) | reject | 0.568 | 0.559 | +0.016 | loss |
| prop | Ajay Mitchell pts under 11.5 (401909094) | reject | 0.565 | 0.556 | +0.016 | loss |
| prop | Anthony Davis fg3m under 0.5 (401909868) | reject | 0.549 | 0.541 | +0.016 | loss |
| spread | away 2.5 (401909841) | reject | 0.516 | 0.512 | +0.008 | loss |
| ml | away (401909094) | reject | 0.276 | 0.274 | +0.008 | loss |
| prop | Rudy Gobert pts under 9.5 (401909869) | reject | 0.541 | 0.538 | +0.007 | win |
| prop | Tre Johnson pts over 9.5 (401909868) | reject | 0.559 | 0.556 | +0.007 | loss |
| prop | Anthony Edwards ast under 2.5 (401909869) | reject | 0.461 | 0.459 | +0.005 | loss |
| prop | Cameron Johnson pts under 12.5 (401909094) | reject | 0.542 | 0.541 | +0.003 | win |
| prop | Nikola Jokic pts under 25.5 (401909094) | reject | 0.545 | 0.543 | +0.002 | win |
| prop | Matas Buzelis pts under 14.5 (401909870) | reject | 0.542 | 0.541 | +0.002 | win |
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
| prop | Dennis Schroder ast under 6.5 (401909868) | reject | 0.775 | 0.602 | - | win |
| prop | Dennis Schroder fg3m over 1.5 (401909868) | reject | 0.339 | 0.562 | - | loss |
| prop | Dennis Schroder fg3m under 1.5 (401909868) | reject | 0.661 | 0.562 | - | win |
| prop | Dennis Schroder pts over 15.5 (401909868) | reject | 0.320 | 0.543 | - | loss |
| prop | Dennis Schroder pts under 15.5 (401909868) | reject | 0.680 | 0.543 | - | win |
| prop | Dennis Schroder reb over 3.5 (401909868) | reject | 0.423 | 0.549 | - | loss |
| prop | Dennis Schroder reb under 3.5 (401909868) | reject | 0.577 | 0.549 | - | win |
| prop | Grayson Allen ast over 3.5 (401909868) | reject | 0.457 | 0.562 | - | loss |
| prop | Grayson Allen ast under 3.5 (401909868) | reject | 0.543 | 0.562 | - | win |
| prop | Grayson Allen fg3m over 2.5 (401909868) | reject | 0.534 | 0.637 | - | loss |
| prop | Grayson Allen fg3m under 2.5 (401909868) | reject | 0.466 | 0.637 | - | win |
| prop | Grayson Allen pts under 16.5 (401909868) | reject | 0.606 | 0.559 | - | win |
| prop | Grayson Allen reb over 2.5 (401909868) | reject | 0.551 | 0.592 | - | loss |
| prop | Grayson Allen reb under 2.5 (401909868) | reject | 0.449 | 0.592 | - | win |
| prop | Trae Young fg3m over 2.5 (401909868) | reject | 0.476 | 0.559 | - | loss |
| prop | Trae Young fg3m under 2.5 (401909868) | reject | 0.524 | 0.559 | - | win |
| prop | Trae Young pts over 20.5 (401909868) | reject | 0.515 | 0.538 | - | win |
| prop | Trae Young pts under 20.5 (401909868) | reject | 0.485 | 0.538 | - | loss |
| prop | Trae Young reb over 2.5 (401909868) | reject | 0.470 | 0.559 | - | win |
| prop | Trae Young reb under 2.5 (401909868) | reject | 0.530 | 0.559 | - | loss |
| prop | Naz Reid ast over 2.5 (401909868) | reject | 0.400 | 0.633 | - | loss |
| prop | Naz Reid ast under 2.5 (401909868) | reject | 0.600 | 0.633 | - | win |
| prop | Naz Reid fg3m over 2.5 (401909868) | reject | 0.435 | 0.565 | - | loss |
| prop | Naz Reid fg3m under 2.5 (401909868) | reject | 0.565 | 0.565 | - | win |
| prop | Naz Reid pts under 17.5 (401909868) | reject | 0.616 | 0.549 | - | loss |
| prop | Naz Reid reb over 7.5 (401909868) | reject | 0.485 | 0.562 | - | win |
| prop | Naz Reid reb under 7.5 (401909868) | reject | 0.515 | 0.562 | - | loss |
| prop | Justin Champagnie pts over 7.5 (401909868) | reject | 0.632 | 0.549 | - | loss |
| prop | Justin Champagnie pts under 7.5 (401909868) | reject | 0.368 | 0.549 | - | win |
| prop | Justin Champagnie reb over 5.5 (401909868) | reject | 0.603 | 0.541 | - | loss |
| prop | Moussa Diabate ast over 1.5 (401909868) | reject | 0.609 | 0.595 | - | win |
| prop | Moussa Diabate ast under 1.5 (401909868) | reject | 0.391 | 0.595 | - | loss |
| prop | Moussa Diabate pts over 8.5 (401909868) | reject | 0.355 | 0.538 | - | win |
| prop | Moussa Diabate pts under 8.5 (401909868) | reject | 0.645 | 0.538 | - | loss |
| prop | Moussa Diabate reb over 8.5 (401909868) | reject | 0.422 | 0.543 | - | win |
| prop | Moussa Diabate reb under 8.5 (401909868) | reject | 0.578 | 0.543 | - | loss |
| prop | Brandon Miller ast over 3.5 (401909868) | reject | 0.319 | 0.637 | - | loss |
| prop | Brandon Miller ast under 3.5 (401909868) | reject | 0.681 | 0.637 | - | win |
| prop | Brandon Miller fg3m over 3.5 (401909868) | reject | 0.380 | 0.562 | - | win |
| prop | Brandon Miller fg3m under 3.5 (401909868) | reject | 0.620 | 0.562 | - | loss |
| prop | Ryan Kalkbrenner pts over 5.5 (401909868) | reject | 0.530 | 0.549 | - | win |
| prop | Ryan Kalkbrenner pts under 5.5 (401909868) | reject | 0.470 | 0.549 | - | loss |
| prop | Ryan Kalkbrenner reb over 4.5 (401909868) | reject | 0.521 | 0.565 | - | loss |
| prop | Ryan Kalkbrenner reb under 4.5 (401909868) | reject | 0.479 | 0.565 | - | win |
| prop | Sion James ast over 2.5 (401909868) | reject | 0.538 | 0.543 | - | win |
| prop | Sion James ast under 2.5 (401909868) | reject | 0.462 | 0.543 | - | loss |
| prop | Sion James fg3m over 1.5 (401909868) | reject | 0.302 | 0.602 | - | loss |
| prop | Sion James fg3m under 1.5 (401909868) | reject | 0.698 | 0.602 | - | win |
| prop | Sion James pts over 6.5 (401909868) | reject | 0.383 | 0.543 | - | loss |
| prop | Sion James pts under 6.5 (401909868) | reject | 0.617 | 0.543 | - | win |
| prop | Sion James reb over 3.5 (401909868) | reject | 0.544 | 0.568 | - | loss |
| prop | Sion James reb under 3.5 (401909868) | reject | 0.456 | 0.568 | - | win |
| prop | Alex Sarr ast over 2.5 (401909868) | reject | 0.470 | 0.654 | - | loss |
| prop | Alex Sarr ast under 2.5 (401909868) | reject | 0.530 | 0.654 | - | win |
| prop | Kyshawn George ast over 3.5 (401909868) | reject | 0.548 | 0.556 | - | loss |
| prop | Kyshawn George ast under 3.5 (401909868) | reject | 0.452 | 0.556 | - | win |
| prop | Kyshawn George fg3m over 1.5 (401909868) | reject | 0.538 | 0.633 | - | win |
| prop | Kyshawn George fg3m under 1.5 (401909868) | reject | 0.462 | 0.633 | - | loss |
| prop | Kyshawn George reb over 4.5 (401909868) | reject | 0.543 | 0.549 | - | loss |
| prop | Kyshawn George reb under 4.5 (401909868) | reject | 0.457 | 0.549 | - | win |
| prop | Tre Johnson fg3m over 1.5 (401909868) | reject | 0.519 | 0.541 | - | loss |
| prop | Tre Johnson fg3m under 1.5 (401909868) | reject | 0.481 | 0.541 | - | win |
| prop | Tre Johnson pts over 10.5 (401909868) | reject | 0.497 | 0.543 | - | loss |
| prop | Tre Johnson pts under 10.5 (401909868) | reject | 0.503 | 0.543 | - | win |
| prop | Anthony Davis ast over 2.5 (401909868) | reject | 0.547 | 0.568 | - | loss |
| prop | Anthony Davis ast under 2.5 (401909868) | reject | 0.453 | 0.568 | - | win |
| prop | Anthony Davis pts over 21.5 (401909868) | reject | 0.413 | 0.546 | - | win |
| prop | Anthony Davis pts under 21.5 (401909868) | reject | 0.587 | 0.546 | - | loss |
| prop | Anthony Davis reb over 10.5 (401909868) | reject | 0.472 | 0.552 | - | loss |
| prop | Anthony Davis reb under 10.5 (401909868) | reject | 0.528 | 0.552 | - | win |
| prop | Anthony Edwards ast over 2.5 (401909869) | reject | 0.539 | 0.608 | - | win |
| prop | Anthony Edwards ast over 4.5 (401909869) | reject | 0.191 | 0.238 | - | loss |
| prop | Anthony Edwards ast over 6.5 (401909869) | reject | 0.047 | 0.083 | - | loss |
| prop | Anthony Edwards ast over 9.5 (401909869) | reject | 0.003 | 0.028 | - | loss |
| prop | Anthony Edwards fg3m over 0.5 (401909869) | reject | 0.919 | 0.968 | - | win |
| prop | Anthony Edwards fg3m over 1.5 (401909869) | reject | 0.742 | 0.833 | - | win |
| prop | Anthony Edwards fg3m over 2.5 (401909869) | reject | 0.528 | 0.615 | - | win |
| prop | Anthony Edwards fg3m over 4.5 (401909869) | reject | 0.195 | 0.222 | - | win |
| prop | Anthony Edwards fg3m over 5.5 (401909869) | reject | 0.105 | 0.129 | - | loss |
| prop | Anthony Edwards fg3m over 6.5 (401909869) | reject | 0.053 | 0.077 | - | loss |
| prop | Anthony Edwards fg3m over 7.5 (401909869) | reject | 0.025 | 0.053 | - | loss |
| prop | Anthony Edwards fg3m over 8.5 (401909869) | reject | 0.011 | 0.043 | - | loss |
| prop | Anthony Edwards fg3m over 9.5 (401909869) | reject | 0.005 | 0.028 | - | loss |
| prop | Anthony Edwards pts over 14.5 (401909869) | reject | 0.738 | 0.957 | - | win |
| prop | Anthony Edwards pts over 19.5 (401909869) | reject | 0.568 | 0.833 | - | win |
| prop | Anthony Edwards pts over 24.5 (401909869) | reject | 0.411 | 0.630 | - | win |
| prop | Anthony Edwards pts over 29.5 (401909869) | reject | 0.283 | 0.400 | - | win |
| prop | Anthony Edwards pts over 34.5 (401909869) | reject | 0.187 | 0.222 | - | win |
| prop | Anthony Edwards pts over 39.5 (401909869) | reject | 0.120 | 0.118 | - | win |
| prop | Anthony Edwards pts over 44.5 (401909869) | reject | 0.075 | 0.071 | - | win |
| prop | Anthony Edwards pts over 49.5 (401909869) | reject | 0.046 | 0.038 | - | loss |
| prop | Anthony Edwards reb over 12.5 (401909869) | reject | 0.006 | 0.028 | - | loss |
| prop | Anthony Edwards reb over 2.5 (401909869) | reject | 0.781 | 0.857 | - | win |
| prop | Anthony Edwards reb over 6.5 (401909869) | reject | 0.209 | 0.222 | - | loss |
| prop | Anthony Edwards reb over 9.5 (401909869) | reject | 0.043 | 0.059 | - | loss |
| prop | Donovan Mitchell ast over 12.5 (401909869) | reject | 0.001 | 0.028 | - | loss |
| prop | Donovan Mitchell ast over 2.5 (401909869) | reject | 0.687 | 0.857 | - | win |
| prop | Donovan Mitchell ast over 6.5 (401909869) | reject | 0.115 | 0.244 | - | win |
| prop | Donovan Mitchell ast over 9.5 (401909869) | reject | 0.015 | 0.071 | - | loss |
| prop | Donovan Mitchell fg3m over 0.5 (401909869) | reject | 0.908 | 0.923 | - | win |
| prop | Donovan Mitchell fg3m over 1.5 (401909869) | reject | 0.717 | 0.714 | - | win |
| prop | Donovan Mitchell fg3m over 3.5 (401909869) | reject | 0.304 | 0.250 | - | win |
| prop | Donovan Mitchell fg3m over 4.5 (401909869) | reject | 0.170 | 0.129 | - | win |
| prop | Donovan Mitchell fg3m over 5.5 (401909869) | reject | 0.088 | 0.077 | - | loss |
| prop | Donovan Mitchell fg3m over 6.5 (401909869) | reject | 0.043 | 0.050 | - | loss |
| prop | Donovan Mitchell fg3m over 7.5 (401909869) | reject | 0.020 | 0.028 | - | loss |
| prop | Donovan Mitchell pts over 14.5 (401909869) | reject | 0.768 | 0.941 | - | win |
| prop | Donovan Mitchell pts over 19.5 (401909869) | reject | 0.608 | 0.800 | - | win |
| prop | Donovan Mitchell pts over 24.5 (401909869) | reject | 0.454 | 0.556 | - | win |
| prop | Donovan Mitchell pts over 29.5 (401909869) | reject | 0.323 | 0.323 | - | loss |
| prop | Donovan Mitchell pts over 34.5 (401909869) | reject | 0.222 | 0.154 | - | loss |
| prop | Donovan Mitchell pts over 39.5 (401909869) | reject | 0.147 | 0.077 | - | loss |
| prop | Donovan Mitchell pts over 44.5 (401909869) | reject | 0.095 | 0.050 | - | loss |
| prop | Donovan Mitchell pts over 49.5 (401909869) | reject | 0.060 | 0.028 | - | loss |
| prop | Donovan Mitchell reb over 12.5 (401909869) | reject | 0.010 | 0.028 | - | loss |
| prop | Donovan Mitchell reb over 2.5 (401909869) | reject | 0.815 | 0.882 | - | win |
| prop | Donovan Mitchell reb over 6.5 (401909869) | reject | 0.253 | 0.244 | - | loss |
| prop | Donovan Mitchell reb over 9.5 (401909869) | reject | 0.060 | 0.062 | - | loss |
| prop | Evan Mobley ast over 2.5 (401909869) | reject | 0.656 | 0.733 | - | win |
| prop | Evan Mobley ast over 4.5 (401909869) | reject | 0.296 | 0.364 | - | loss |
| prop | Evan Mobley ast over 6.5 (401909869) | reject | 0.096 | 0.133 | - | loss |
| prop | Evan Mobley ast over 9.5 (401909869) | reject | 0.011 | 0.043 | - | loss |
| prop | Evan Mobley fg3m over 0.5 (401909869) | reject | 0.650 | 0.714 | - | win |
| prop | Evan Mobley fg3m over 1.5 (401909869) | reject | 0.305 | 0.370 | - | win |
| prop | Evan Mobley fg3m over 2.5 (401909869) | reject | 0.114 | 0.160 | - | win |
| prop | Evan Mobley fg3m over 3.5 (401909869) | reject | 0.036 | 0.083 | - | loss |
| prop | Evan Mobley fg3m over 4.5 (401909869) | reject | 0.010 | 0.048 | - | loss |
| prop | Evan Mobley fg3m over 5.5 (401909869) | reject | 0.003 | 0.028 | - | loss |
| prop | Evan Mobley pts over 14.5 (401909869) | reject | 0.575 | 0.730 | - | win |
| prop | Evan Mobley pts over 19.5 (401909869) | reject | 0.375 | 0.426 | - | loss |
| prop | Evan Mobley pts over 24.5 (401909869) | reject | 0.226 | 0.200 | - | loss |
| prop | Evan Mobley pts over 29.5 (401909869) | reject | 0.129 | 0.091 | - | loss |
| prop | Evan Mobley pts over 34.5 (401909869) | reject | 0.070 | 0.050 | - | loss |
| prop | Evan Mobley pts over 39.5 (401909869) | reject | 0.036 | 0.028 | - | loss |
| prop | Evan Mobley pts over 9.5 (401909869) | reject | 0.793 | 0.938 | - | win |
| prop | Evan Mobley reb over 12.5 (401909869) | reject | 0.214 | 0.160 | - | loss |
| prop | Evan Mobley reb over 14.5 (401909869) | reject | 0.118 | 0.087 | - | loss |
| prop | Evan Mobley reb over 16.5 (401909869) | reject | 0.060 | 0.050 | - | loss |
| prop | Evan Mobley reb over 19.5 (401909869) | reject | 0.020 | 0.028 | - | loss |
| prop | Evan Mobley reb over 4.5 (401909869) | reject | 0.892 | 0.941 | - | win |
| prop | Evan Mobley reb over 6.5 (401909869) | reject | 0.735 | 0.783 | - | win |
| prop | Evan Mobley reb over 9.5 (401909869) | reject | 0.445 | 0.426 | - | loss |
| prop | Jaden McDaniels ast over 4.5 (401909869) | reject | 0.105 | 0.148 | - | loss |
| prop | Jaden McDaniels ast over 6.5 (401909869) | reject | 0.018 | 0.056 | - | loss |
| prop | Jaden McDaniels fg3m over 0.5 (401909869) | reject | 0.669 | 0.787 | - | win |
| prop | Jaden McDaniels fg3m over 2.5 (401909869) | reject | 0.127 | 0.222 | - | loss |
| prop | Jaden McDaniels fg3m over 3.5 (401909869) | reject | 0.042 | 0.103 | - | loss |
| prop | Jaden McDaniels fg3m over 4.5 (401909869) | reject | 0.012 | 0.059 | - | loss |
| prop | Jaden McDaniels fg3m over 5.5 (401909869) | reject | 0.003 | 0.034 | - | loss |
| prop | Jaden McDaniels pts over 14.5 (401909869) | reject | 0.423 | 0.524 | - | loss |
| prop | Jaden McDaniels pts over 19.5 (401909869) | reject | 0.230 | 0.299 | - | loss |
| prop | Jaden McDaniels pts over 24.5 (401909869) | reject | 0.114 | 0.129 | - | loss |
| prop | Jaden McDaniels pts over 29.5 (401909869) | reject | 0.053 | 0.062 | - | loss |
| prop | Jaden McDaniels pts over 34.5 (401909869) | reject | 0.024 | 0.028 | - | loss |
| prop | Jaden McDaniels pts over 4.5 (401909869) | reject | 0.920 | 0.985 | - | win |
| prop | Jaden McDaniels pts over 9.5 (401909869) | reject | 0.683 | 0.846 | - | win |
| prop | Jaden McDaniels reb over 12.5 (401909869) | reject | 0.006 | 0.028 | - | loss |
| prop | Jaden McDaniels reb over 2.5 (401909869) | reject | 0.777 | 0.846 | - | win |
| prop | Jaden McDaniels reb over 6.5 (401909869) | reject | 0.204 | 0.250 | - | loss |
| prop | Jaden McDaniels reb over 9.5 (401909869) | reject | 0.041 | 0.071 | - | loss |
| prop | James Harden ast over 12.5 (401909869) | reject | 0.018 | 0.059 | - | loss |
| prop | James Harden ast over 14.5 (401909869) | reject | 0.005 | 0.034 | - | loss |
| prop | James Harden ast over 2.5 (401909869) | reject | 0.868 | 0.966 | - | win |
| prop | James Harden ast over 4.5 (401909869) | reject | 0.604 | 0.792 | - | win |
| prop | James Harden ast over 9.5 (401909869) | reject | 0.090 | 0.182 | - | loss |
| prop | James Harden fg3m over 0.5 (401909869) | reject | 0.883 | 0.905 | - | win |
| prop | James Harden fg3m over 1.5 (401909869) | reject | 0.661 | 0.677 | - | win |
| prop | James Harden fg3m over 3.5 (401909869) | reject | 0.243 | 0.211 | - | win |
| prop | James Harden fg3m over 4.5 (401909869) | reject | 0.125 | 0.111 | - | loss |
| prop | James Harden fg3m over 5.5 (401909869) | reject | 0.059 | 0.062 | - | loss |
| prop | James Harden fg3m over 6.5 (401909869) | reject | 0.026 | 0.043 | - | loss |
| prop | James Harden fg3m over 7.5 (401909869) | reject | 0.011 | 0.028 | - | loss |
| prop | James Harden pts over 14.5 (401909869) | reject | 0.572 | 0.667 | - | win |
| prop | James Harden pts over 19.5 (401909869) | reject | 0.372 | 0.370 | - | win |
| prop | James Harden pts over 24.5 (401909869) | reject | 0.223 | 0.167 | - | loss |
| prop | James Harden pts over 29.5 (401909869) | reject | 0.126 | 0.077 | - | loss |
| prop | James Harden pts over 34.5 (401909869) | reject | 0.068 | 0.038 | - | loss |
| prop | James Harden pts over 39.5 (401909869) | reject | 0.036 | 0.028 | - | loss |
| prop | James Harden pts over 9.5 (401909869) | reject | 0.791 | 0.909 | - | win |
| prop | James Harden reb over 2.5 (401909869) | reject | 0.783 | 0.833 | - | win |
| prop | James Harden reb over 6.5 (401909869) | reject | 0.211 | 0.182 | - | loss |
| prop | James Harden reb over 9.5 (401909869) | reject | 0.044 | 0.053 | - | loss |
| prop | Jarrett Allen ast over 2.5 (401909869) | reject | 0.110 | 0.211 | - | loss |
| prop | Jarrett Allen ast over 4.5 (401909869) | reject | 0.009 | 0.056 | - | loss |
| prop | Jarrett Allen ast over 6.5 (401909869) | reject | 0.000 | 0.028 | - | loss |
| prop | Jarrett Allen pts over 14.5 (401909869) | reject | 0.400 | 0.435 | - | loss |
| prop | Jarrett Allen pts over 19.5 (401909869) | reject | 0.211 | 0.174 | - | loss |
| prop | Jarrett Allen pts over 24.5 (401909869) | reject | 0.102 | 0.071 | - | loss |
| prop | Jarrett Allen pts over 29.5 (401909869) | reject | 0.046 | 0.034 | - | loss |
| prop | Jarrett Allen pts over 4.5 (401909869) | reject | 0.913 | 0.980 | - | win |
| prop | Jarrett Allen pts over 9.5 (401909869) | reject | 0.664 | 0.796 | - | win |
| prop | Jarrett Allen reb over 12.5 (401909869) | reject | 0.115 | 0.133 | - | loss |
| prop | Jarrett Allen reb over 14.5 (401909869) | reject | 0.053 | 0.077 | - | loss |
| prop | Jarrett Allen reb over 16.5 (401909869) | reject | 0.023 | 0.050 | - | loss |
| prop | Jarrett Allen reb over 19.5 (401909869) | reject | 0.006 | 0.028 | - | loss |
| prop | Jarrett Allen reb over 2.5 (401909869) | reject | 0.954 | 0.990 | - | win |
| prop | Jarrett Allen reb over 4.5 (401909869) | reject | 0.820 | 0.909 | - | win |
| prop | Jarrett Allen reb over 6.5 (401909869) | reject | 0.611 | 0.714 | - | win |
| prop | Jarrett Allen reb over 9.5 (401909869) | reject | 0.302 | 0.364 | - | loss |
| prop | Jaylon Tyson ast over 2.5 (401909869) | reject | 0.365 | 0.435 | - | win |
| prop | Jaylon Tyson ast over 4.5 (401909869) | reject | 0.085 | 0.133 | - | win |
| prop | Jaylon Tyson ast over 6.5 (401909869) | reject | 0.013 | 0.053 | - | loss |
| prop | Jaylon Tyson fg3m over 0.5 (401909869) | reject | 0.723 | 0.744 | - | loss |
| prop | Jaylon Tyson fg3m over 2.5 (401909869) | reject | 0.174 | 0.190 | - | loss |
| prop | Jaylon Tyson fg3m over 3.5 (401909869) | reject | 0.066 | 0.095 | - | loss |
| prop | Jaylon Tyson fg3m over 4.5 (401909869) | reject | 0.022 | 0.056 | - | loss |
| prop | Jaylon Tyson fg3m over 5.5 (401909869) | reject | 0.007 | 0.028 | - | loss |
| prop | Jaylon Tyson pts over 14.5 (401909869) | reject | 0.131 | 0.200 | - | loss |
| prop | Jaylon Tyson pts over 19.5 (401909869) | reject | 0.039 | 0.077 | - | loss |
| prop | Jaylon Tyson pts over 24.5 (401909869) | reject | 0.011 | 0.034 | - | loss |
| prop | Jaylon Tyson pts over 4.5 (401909869) | reject | 0.766 | 0.867 | - | win |
| prop | Jaylon Tyson pts over 9.5 (401909869) | reject | 0.366 | 0.500 | - | win |
| prop | Jaylon Tyson reb over 12.5 (401909869) | reject | 0.002 | 0.028 | - | loss |
| prop | Jaylon Tyson reb over 2.5 (401909869) | reject | 0.692 | 0.796 | - | win |
| prop | Jaylon Tyson reb over 6.5 (401909869) | reject | 0.126 | 0.174 | - | loss |
| prop | Jaylon Tyson reb over 9.5 (401909869) | reject | 0.019 | 0.056 | - | loss |
| prop | Jonathan Kuminga ast over 4.5 (401909869) | reject | 0.104 | 0.105 | - | loss |
| prop | Jonathan Kuminga ast over 6.5 (401909869) | reject | 0.018 | 0.043 | - | loss |
| prop | Jonathan Kuminga fg3m over 0.5 (401909869) | reject | 0.721 | 0.773 | - | loss |
| prop | Jonathan Kuminga fg3m over 1.5 (401909869) | reject | 0.391 | 0.426 | - | loss |
| prop | Jonathan Kuminga fg3m over 2.5 (401909869) | reject | 0.172 | 0.190 | - | loss |
| prop | Jonathan Kuminga fg3m over 3.5 (401909869) | reject | 0.065 | 0.091 | - | loss |
| prop | Jonathan Kuminga fg3m over 4.5 (401909869) | reject | 0.022 | 0.053 | - | loss |
| prop | Jonathan Kuminga fg3m over 5.5 (401909869) | reject | 0.007 | 0.028 | - | loss |
| prop | Jonathan Kuminga pts over 14.5 (401909869) | reject | 0.416 | 0.408 | - | loss |
| prop | Jonathan Kuminga pts over 19.5 (401909869) | reject | 0.224 | 0.174 | - | loss |
| prop | Jonathan Kuminga pts over 24.5 (401909869) | reject | 0.111 | 0.077 | - | loss |
| prop | Jonathan Kuminga pts over 29.5 (401909869) | reject | 0.051 | 0.043 | - | loss |
| prop | Jonathan Kuminga pts over 34.5 (401909869) | reject | 0.022 | 0.028 | - | loss |
| prop | Jonathan Kuminga pts over 4.5 (401909869) | reject | 0.918 | 0.962 | - | win |
| prop | Jonathan Kuminga pts over 9.5 (401909869) | reject | 0.677 | 0.737 | - | win |
| prop | Jonathan Kuminga reb over 12.5 (401909869) | reject | 0.020 | 0.028 | - | loss |
| prop | Jonathan Kuminga reb over 2.5 (401909869) | reject | 0.860 | 0.875 | - | win |
| prop | Jonathan Kuminga reb over 6.5 (401909869) | reject | 0.330 | 0.282 | - | win |
| prop | Jonathan Kuminga reb over 9.5 (401909869) | reject | 0.095 | 0.077 | - | loss |
| prop | LaMelo Ball ast over 12.5 (401909869) | reject | 0.013 | 0.091 | - | loss |
| prop | LaMelo Ball ast over 14.5 (401909869) | reject | 0.003 | 0.050 | - | loss |
| prop | LaMelo Ball ast over 2.5 (401909869) | reject | 0.848 | 0.972 | - | win |
| prop | LaMelo Ball ast over 4.5 (401909869) | reject | 0.565 | 0.833 | - | win |
| prop | LaMelo Ball ast over 6.5 (401909869) | reject | 0.292 | 0.592 | - | loss |
| prop | LaMelo Ball ast over 9.5 (401909869) | reject | 0.073 | 0.250 | - | loss |
| prop | LaMelo Ball fg3m over 0.5 (401909869) | reject | 0.929 | 0.980 | - | win |
| prop | LaMelo Ball fg3m over 1.5 (401909869) | reject | 0.768 | 0.875 | - | loss |
| prop | LaMelo Ball fg3m over 2.5 (401909869) | reject | 0.564 | 0.697 | - | loss |
| prop | LaMelo Ball fg3m over 4.5 (401909869) | reject | 0.225 | 0.323 | - | loss |
| prop | LaMelo Ball fg3m over 5.5 (401909869) | reject | 0.126 | 0.190 | - | loss |
| prop | LaMelo Ball fg3m over 6.5 (401909869) | reject | 0.066 | 0.111 | - | loss |
| prop | LaMelo Ball fg3m over 7.5 (401909869) | reject | 0.033 | 0.077 | - | loss |
| prop | LaMelo Ball fg3m over 8.5 (401909869) | reject | 0.016 | 0.053 | - | loss |
| prop | LaMelo Ball fg3m over 9.5 (401909869) | reject | 0.007 | 0.034 | - | loss |
| prop | LaMelo Ball pts over 14.5 (401909869) | reject | 0.498 | 0.733 | - | loss |
| prop | LaMelo Ball pts over 24.5 (401909869) | reject | 0.164 | 0.282 | - | loss |
| prop | LaMelo Ball pts over 29.5 (401909869) | reject | 0.085 | 0.138 | - | loss |
| prop | LaMelo Ball pts over 34.5 (401909869) | reject | 0.042 | 0.077 | - | loss |
| prop | LaMelo Ball pts over 39.5 (401909869) | reject | 0.020 | 0.050 | - | loss |
| prop | LaMelo Ball pts over 44.5 (401909869) | reject | 0.009 | 0.028 | - | loss |
| prop | LaMelo Ball pts over 9.5 (401909869) | reject | 0.741 | 0.917 | - | win |
| prop | LaMelo Ball reb over 12.5 (401909869) | reject | 0.001 | 0.028 | - | loss |
| prop | LaMelo Ball reb over 2.5 (401909869) | reject | 0.660 | 0.787 | - | loss |
| prop | LaMelo Ball reb over 6.5 (401909869) | reject | 0.105 | 0.182 | - | loss |
| prop | LaMelo Ball reb over 9.5 (401909869) | reject | 0.014 | 0.056 | - | loss |
| prop | Peyton Watson ast over 2.5 (401909869) | reject | 0.461 | 0.370 | - | loss |
| prop | Peyton Watson ast over 4.5 (401909869) | reject | 0.137 | 0.105 | - | loss |
| prop | Peyton Watson ast over 6.5 (401909869) | reject | 0.028 | 0.038 | - | loss |
| prop | Peyton Watson fg3m over 0.5 (401909869) | reject | 0.730 | 0.796 | - | loss |
| prop | Peyton Watson fg3m over 2.5 (401909869) | reject | 0.180 | 0.222 | - | loss |
| prop | Peyton Watson fg3m over 3.5 (401909869) | reject | 0.069 | 0.105 | - | loss |
| prop | Peyton Watson fg3m over 4.5 (401909869) | reject | 0.024 | 0.056 | - | loss |
| prop | Peyton Watson fg3m over 5.5 (401909869) | reject | 0.007 | 0.028 | - | loss |
| prop | Peyton Watson pts over 14.5 (401909869) | reject | 0.390 | 0.450 | - | win |
| prop | Peyton Watson pts over 19.5 (401909869) | reject | 0.203 | 0.190 | - | loss |
| prop | Peyton Watson pts over 24.5 (401909869) | reject | 0.096 | 0.083 | - | loss |
| prop | Peyton Watson pts over 29.5 (401909869) | reject | 0.043 | 0.038 | - | loss |
| prop | Peyton Watson pts over 34.5 (401909869) | reject | 0.018 | 0.028 | - | loss |
| prop | Peyton Watson pts over 4.5 (401909869) | reject | 0.910 | 0.968 | - | win |
| prop | Peyton Watson pts over 9.5 (401909869) | reject | 0.656 | 0.773 | - | win |
| prop | Peyton Watson reb over 2.5 (401909869) | reject | 0.767 | 0.787 | - | win |
| prop | Peyton Watson reb over 4.5 (401909869) | reject | 0.441 | 0.426 | - | win |
| prop | Peyton Watson reb over 6.5 (401909869) | reject | 0.193 | 0.167 | - | win |
| prop | Peyton Watson reb over 9.5 (401909869) | reject | 0.038 | 0.050 | - | loss |
| prop | Rudy Gobert ast over 2.5 (401909869) | reject | 0.205 | 0.222 | - | loss |
| prop | Rudy Gobert ast over 4.5 (401909869) | reject | 0.027 | 0.056 | - | loss |
| prop | Rudy Gobert ast over 6.5 (401909869) | reject | 0.002 | 0.028 | - | loss |
| prop | Rudy Gobert pts over 14.5 (401909869) | reject | 0.197 | 0.174 | - | loss |
| prop | Rudy Gobert pts over 19.5 (401909869) | reject | 0.072 | 0.062 | - | loss |
| prop | Rudy Gobert pts over 24.5 (401909869) | reject | 0.024 | 0.028 | - | loss |
| prop | Rudy Gobert pts over 4.5 (401909869) | reject | 0.822 | 0.895 | - | win |
| prop | Rudy Gobert reb over 12.5 (401909869) | reject | 0.351 | 0.392 | - | win |
| prop | Rudy Gobert reb over 14.5 (401909869) | reject | 0.224 | 0.222 | - | win |
| prop | Rudy Gobert reb over 16.5 (401909869) | reject | 0.134 | 0.129 | - | win |
| prop | Rudy Gobert reb over 19.5 (401909869) | reject | 0.055 | 0.059 | - | loss |
| prop | Rudy Gobert reb over 4.5 (401909869) | reject | 0.941 | 0.980 | - | win |
| prop | Rudy Gobert reb over 6.5 (401909869) | reject | 0.837 | 0.917 | - | win |
| prop | Rudy Gobert reb over 9.5 (401909869) | reject | 0.597 | 0.692 | - | win |
| prop | Sam Merrill ast over 2.5 (401909869) | reject | 0.273 | 0.339 | - | loss |
| prop | Sam Merrill ast over 4.5 (401909869) | reject | 0.048 | 0.100 | - | loss |
| prop | Sam Merrill ast over 6.5 (401909869) | reject | 0.005 | 0.038 | - | loss |
| prop | Sam Merrill fg3m over 0.5 (401909869) | reject | 0.826 | 0.900 | - | win |
| prop | Sam Merrill fg3m over 2.5 (401909869) | reject | 0.309 | 0.345 | - | loss |
| prop | Sam Merrill fg3m over 3.5 (401909869) | reject | 0.151 | 0.160 | - | loss |
| prop | Sam Merrill fg3m over 4.5 (401909869) | reject | 0.066 | 0.087 | - | loss |
| prop | Sam Merrill fg3m over 5.5 (401909869) | reject | 0.027 | 0.053 | - | loss |
| prop | Sam Merrill fg3m over 6.5 (401909869) | reject | 0.010 | 0.028 | - | loss |
| prop | Sam Merrill pts over 14.5 (401909869) | reject | 0.129 | 0.138 | - | loss |
| prop | Sam Merrill pts over 19.5 (401909869) | reject | 0.038 | 0.056 | - | loss |
| prop | Sam Merrill pts over 24.5 (401909869) | reject | 0.010 | 0.028 | - | loss |
| prop | Sam Merrill pts over 4.5 (401909869) | reject | 0.764 | 0.810 | - | win |
| prop | Sam Merrill pts over 9.5 (401909869) | reject | 0.363 | 0.385 | - | loss |
| prop | Sam Merrill reb over 2.5 (401909869) | reject | 0.356 | 0.385 | - | win |
| prop | Sam Merrill reb over 4.5 (401909869) | reject | 0.083 | 0.105 | - | loss |
| prop | Sam Merrill reb over 6.5 (401909869) | reject | 0.013 | 0.034 | - | loss |
| prop | Ayo Dosunmu fg3m over 1.5 (401909869) | reject | 0.422 | 0.400 | - | loss |
| prop | Terrence Shannon Jr. pts over 8.5 (401909869) | reject | 0.603 | 0.565 | - | win |
| ml | home (401909870) | reject | 0.824 | 0.889 | - | win |
| ml | away (401909870) | reject | 0.176 | 0.154 | - | loss |
| prop | Baylor Scheierman ast over 2.5 (401909870) | reject | 0.104 | 0.211 | - | loss |
| prop | Baylor Scheierman ast over 4.5 (401909870) | reject | 0.008 | 0.062 | - | loss |
| prop | Baylor Scheierman ast over 6.5 (401909870) | reject | 0.000 | 0.028 | - | loss |
| prop | Baylor Scheierman fg3m over 0.5 (401909870) | reject | 0.624 | 0.722 | - | loss |
| prop | Baylor Scheierman fg3m over 1.5 (401909870) | reject | 0.277 | 0.385 | - | loss |
| prop | Baylor Scheierman fg3m over 2.5 (401909870) | reject | 0.097 | 0.167 | - | loss |
| prop | Baylor Scheierman fg3m over 3.5 (401909870) | reject | 0.029 | 0.087 | - | loss |
| prop | Baylor Scheierman fg3m over 4.5 (401909870) | reject | 0.008 | 0.050 | - | loss |
| prop | Baylor Scheierman fg3m over 5.5 (401909870) | reject | 0.002 | 0.028 | - | loss |
| prop | Baylor Scheierman pts over 14.5 (401909870) | reject | 0.014 | 0.087 | - | loss |
| prop | Baylor Scheierman pts over 19.5 (401909870) | reject | 0.002 | 0.038 | - | loss |
| prop | Baylor Scheierman pts over 24.5 (401909870) | reject | 0.000 | 0.028 | - | loss |
| prop | Baylor Scheierman pts over 4.5 (401909870) | reject | 0.483 | 0.630 | - | loss |
| prop | Baylor Scheierman pts over 9.5 (401909870) | reject | 0.100 | 0.222 | - | loss |
| prop | Baylor Scheierman reb over 2.5 (401909870) | reject | 0.488 | 0.630 | - | win |
| prop | Baylor Scheierman reb over 4.5 (401909870) | reject | 0.158 | 0.294 | - | win |
| prop | Baylor Scheierman reb over 6.5 (401909870) | reject | 0.036 | 0.111 | - | loss |
| prop | Baylor Scheierman reb over 9.5 (401909870) | reject | 0.002 | 0.034 | - | loss |
| prop | Derrick White ast over 12.5 (401909870) | reject | 0.006 | 0.034 | - | loss |
| prop | Derrick White ast over 2.5 (401909870) | reject | 0.802 | 0.917 | - | win |
| prop | Derrick White ast over 4.5 (401909870) | reject | 0.486 | 0.630 | - | loss |
| prop | Derrick White ast over 6.5 (401909870) | reject | 0.222 | 0.323 | - | loss |
| prop | Derrick White ast over 9.5 (401909870) | reject | 0.045 | 0.091 | - | loss |
| prop | Derrick White fg3m over 0.5 (401909870) | reject | 0.893 | 0.968 | - | win |
| prop | Derrick White fg3m over 1.5 (401909870) | reject | 0.682 | 0.818 | - | loss |
| prop | Derrick White fg3m over 2.5 (401909870) | reject | 0.452 | 0.565 | - | loss |
| prop | Derrick White fg3m over 3.5 (401909870) | reject | 0.265 | 0.355 | - | loss |
| prop | Derrick White fg3m over 4.5 (401909870) | reject | 0.141 | 0.190 | - | loss |
| prop | Derrick White fg3m over 5.5 (401909870) | reject | 0.069 | 0.103 | - | loss |
| prop | Derrick White fg3m over 6.5 (401909870) | reject | 0.032 | 0.059 | - | loss |
| prop | Derrick White fg3m over 7.5 (401909870) | reject | 0.014 | 0.043 | - | loss |
| prop | Derrick White pts over 14.5 (401909870) | reject | 0.476 | 0.643 | - | loss |
| prop | Derrick White pts over 19.5 (401909870) | reject | 0.277 | 0.345 | - | loss |
| prop | Derrick White pts over 24.5 (401909870) | reject | 0.148 | 0.148 | - | loss |
| prop | Derrick White pts over 29.5 (401909870) | reject | 0.074 | 0.071 | - | loss |
| prop | Derrick White pts over 34.5 (401909870) | reject | 0.035 | 0.034 | - | loss |
| prop | Derrick White pts over 4.5 (401909870) | reject | 0.934 | 0.990 | - | win |
| prop | Derrick White pts over 9.5 (401909870) | reject | 0.724 | 0.900 | - | loss |
| prop | Derrick White reb over 2.5 (401909870) | reject | 0.739 | 0.701 | - | win |
| prop | Derrick White reb over 4.5 (401909870) | reject | 0.403 | 0.308 | - | win |
| prop | Derrick White reb over 6.5 (401909870) | reject | 0.165 | 0.103 | - | loss |
| prop | Derrick White reb over 9.5 (401909870) | reject | 0.029 | 0.028 | - | loss |
| prop | Isaac Okoro ast over 2.5 (401909870) | reject | 0.134 | 0.133 | - | win |
| prop | Isaac Okoro ast over 4.5 (401909870) | reject | 0.012 | 0.034 | - | loss |
| prop | Isaac Okoro fg3m over 0.5 (401909870) | reject | 0.556 | 0.528 | - | loss |
| prop | Isaac Okoro fg3m over 1.5 (401909870) | reject | 0.212 | 0.190 | - | loss |
| prop | Isaac Okoro fg3m over 2.5 (401909870) | reject | 0.063 | 0.077 | - | loss |
| prop | Isaac Okoro fg3m over 3.5 (401909870) | reject | 0.016 | 0.034 | - | loss |
| prop | Isaac Okoro fg3m over 4.5 (401909870) | reject | 0.004 | 0.028 | - | loss |
| prop | Isaac Okoro pts over 14.5 (401909870) | reject | 0.061 | 0.053 | - | loss |
| prop | Isaac Okoro pts over 19.5 (401909870) | reject | 0.013 | 0.028 | - | loss |
| prop | Isaac Okoro pts over 4.5 (401909870) | reject | 0.664 | 0.528 | - | loss |
| prop | Isaac Okoro pts over 9.5 (401909870) | reject | 0.238 | 0.148 | - | loss |
| prop | Isaac Okoro reb over 2.5 (401909870) | reject | 0.330 | 0.328 | - | loss |
| prop | Isaac Okoro reb over 4.5 (401909870) | reject | 0.071 | 0.095 | - | loss |
| prop | Isaac Okoro reb over 6.5 (401909870) | reject | 0.010 | 0.034 | - | loss |
| prop | Jalen Smith ast over 2.5 (401909870) | reject | 0.126 | 0.222 | - | loss |
| prop | Jalen Smith ast over 4.5 (401909870) | reject | 0.011 | 0.062 | - | loss |
| prop | Jalen Smith ast over 6.5 (401909870) | reject | 0.001 | 0.028 | - | loss |
| prop | Jalen Smith fg3m over 0.5 (401909870) | reject | 0.770 | 0.810 | - | win |
| prop | Jalen Smith fg3m over 1.5 (401909870) | reject | 0.460 | 0.495 | - | win |
| prop | Jalen Smith fg3m over 2.5 (401909870) | reject | 0.226 | 0.238 | - | loss |
| prop | Jalen Smith fg3m over 3.5 (401909870) | reject | 0.096 | 0.111 | - | loss |
| prop | Jalen Smith fg3m over 4.5 (401909870) | reject | 0.036 | 0.059 | - | loss |
| prop | Jalen Smith fg3m over 5.5 (401909870) | reject | 0.013 | 0.034 | - | loss |
| prop | Jalen Smith pts over 14.5 (401909870) | reject | 0.264 | 0.299 | - | loss |
| prop | Jalen Smith pts over 19.5 (401909870) | reject | 0.112 | 0.121 | - | loss |
| prop | Jalen Smith pts over 24.5 (401909870) | reject | 0.043 | 0.059 | - | loss |
| prop | Jalen Smith pts over 29.5 (401909870) | reject | 0.015 | 0.028 | - | loss |
| prop | Jalen Smith pts over 4.5 (401909870) | reject | 0.861 | 0.923 | - | win |
| prop | Jalen Smith pts over 9.5 (401909870) | reject | 0.536 | 0.615 | - | loss |
| prop | Jalen Smith reb over 12.5 (401909870) | reject | 0.085 | 0.095 | - | loss |
| prop | Jalen Smith reb over 14.5 (401909870) | reject | 0.037 | 0.056 | - | loss |
| prop | Jalen Smith reb over 16.5 (401909870) | reject | 0.015 | 0.028 | - | loss |
| prop | Jalen Smith reb over 2.5 (401909870) | reject | 0.941 | 0.968 | - | win |
| prop | Jalen Smith reb over 4.5 (401909870) | reject | 0.783 | 0.818 | - | win |
| prop | Jalen Smith reb over 6.5 (401909870) | reject | 0.555 | 0.574 | - | loss |
| prop | Jalen Smith reb over 9.5 (401909870) | reject | 0.250 | 0.250 | - | loss |
| prop | Jayson Tatum ast over 12.5 (401909870) | reject | 0.062 | 0.071 | - | loss |
| prop | Jayson Tatum ast over 14.5 (401909870) | reject | 0.024 | 0.043 | - | loss |
| prop | Jayson Tatum ast over 2.5 (401909870) | reject | 0.936 | 0.980 | - | win |
| prop | Jayson Tatum ast over 4.5 (401909870) | reject | 0.762 | 0.846 | - | win |
| prop | Jayson Tatum ast over 6.5 (401909870) | reject | 0.517 | 0.568 | - | loss |
| prop | Jayson Tatum ast over 9.5 (401909870) | reject | 0.210 | 0.222 | - | loss |
| prop | Jayson Tatum fg3m over 0.5 (401909870) | reject | 0.927 | 0.972 | - | win |
| prop | Jayson Tatum fg3m over 1.5 (401909870) | reject | 0.762 | 0.833 | - | win |
| prop | Jayson Tatum fg3m over 2.5 (401909870) | reject | 0.555 | 0.623 | - | loss |
| prop | Jayson Tatum fg3m over 3.5 (401909870) | reject | 0.364 | 0.490 | - | loss |
| prop | Jayson Tatum fg3m over 4.5 (401909870) | reject | 0.218 | 0.222 | - | loss |
| prop | Jayson Tatum fg3m over 5.5 (401909870) | reject | 0.121 | 0.121 | - | loss |
| prop | Jayson Tatum fg3m over 6.5 (401909870) | reject | 0.063 | 0.077 | - | loss |
| prop | Jayson Tatum fg3m over 7.5 (401909870) | reject | 0.031 | 0.053 | - | loss |
| prop | Jayson Tatum fg3m over 8.5 (401909870) | reject | 0.015 | 0.028 | - | loss |
| prop | Jayson Tatum pts over 14.5 (401909870) | reject | 0.774 | 0.972 | - | win |
| prop | Jayson Tatum pts over 19.5 (401909870) | reject | 0.616 | 0.882 | - | win |
| prop | Jayson Tatum pts over 24.5 (401909870) | reject | 0.463 | 0.692 | - | loss |
| prop | Jayson Tatum pts over 29.5 (401909870) | reject | 0.332 | 0.455 | - | loss |
| prop | Jayson Tatum pts over 34.5 (401909870) | reject | 0.230 | 0.250 | - | loss |
| prop | Jayson Tatum pts over 39.5 (401909870) | reject | 0.154 | 0.129 | - | loss |
| prop | Jayson Tatum pts over 44.5 (401909870) | reject | 0.100 | 0.062 | - | loss |
| prop | Jayson Tatum pts over 49.5 (401909870) | reject | 0.064 | 0.034 | - | loss |
| prop | Jayson Tatum reb over 12.5 (401909870) | reject | 0.249 | 0.121 | - | loss |
| prop | Jayson Tatum reb over 14.5 (401909870) | reject | 0.143 | 0.062 | - | loss |
| prop | Jayson Tatum reb over 16.5 (401909870) | reject | 0.077 | 0.034 | - | loss |
| prop | Jayson Tatum reb over 4.5 (401909870) | reject | 0.908 | 0.933 | - | win |
| prop | Jayson Tatum reb over 6.5 (401909870) | reject | 0.767 | 0.744 | - | win |
| prop | Jayson Tatum reb over 9.5 (401909870) | reject | 0.488 | 0.417 | - | loss |
| prop | Jordan Walsh ast over 2.5 (401909870) | reject | 0.084 | 0.129 | - | loss |
| prop | Jordan Walsh ast over 4.5 (401909870) | reject | 0.005 | 0.028 | - | loss |
| prop | Jordan Walsh fg3m over 0.5 (401909870) | reject | 0.453 | 0.574 | - | loss |
| prop | Jordan Walsh fg3m over 1.5 (401909870) | reject | 0.135 | 0.222 | - | loss |
| prop | Jordan Walsh fg3m over 2.5 (401909870) | reject | 0.031 | 0.087 | - | loss |
| prop | Jordan Walsh fg3m over 3.5 (401909870) | reject | 0.006 | 0.048 | - | loss |
| prop | Jordan Walsh fg3m over 4.5 (401909870) | reject | 0.001 | 0.028 | - | loss |
| prop | Jordan Walsh pts over 14.5 (401909870) | reject | 0.010 | 0.059 | - | loss |
| prop | Jordan Walsh pts over 19.5 (401909870) | reject | 0.001 | 0.028 | - | loss |
| prop | Jordan Walsh pts over 4.5 (401909870) | reject | 0.448 | 0.535 | - | loss |
| prop | Jordan Walsh pts over 9.5 (401909870) | reject | 0.082 | 0.167 | - | loss |
| prop | Jordan Walsh reb over 2.5 (401909870) | reject | 0.660 | 0.733 | - | win |
| prop | Jordan Walsh reb over 4.5 (401909870) | reject | 0.308 | 0.368 | - | loss |
| prop | Jordan Walsh reb over 6.5 (401909870) | reject | 0.105 | 0.143 | - | loss |
| prop | Jordan Walsh reb over 9.5 (401909870) | reject | 0.014 | 0.050 | - | loss |
| prop | Josh Giddey ast over 12.5 (401909870) | reject | 0.116 | 0.133 | - | loss |
| prop | Josh Giddey ast over 14.5 (401909870) | reject | 0.053 | 0.071 | - | loss |
| prop | Josh Giddey ast over 4.5 (401909870) | reject | 0.838 | 0.923 | - | loss |
| prop | Josh Giddey ast over 6.5 (401909870) | reject | 0.632 | 0.737 | - | loss |
| prop | Josh Giddey ast over 9.5 (401909870) | reject | 0.313 | 0.370 | - | loss |
| prop | Josh Giddey fg3m over 0.5 (401909870) | reject | 0.747 | 0.722 | - | win |
| prop | Josh Giddey fg3m over 1.5 (401909870) | reject | 0.426 | 0.649 | - | loss |
| prop | Josh Giddey fg3m over 2.5 (401909870) | reject | 0.199 | 0.154 | - | loss |
| prop | Josh Giddey fg3m over 3.5 (401909870) | reject | 0.080 | 0.077 | - | loss |
| prop | Josh Giddey fg3m over 4.5 (401909870) | reject | 0.028 | 0.043 | - | loss |
| prop | Josh Giddey fg3m over 5.5 (401909870) | reject | 0.009 | 0.028 | - | loss |
| prop | Josh Giddey pts over 14.5 (401909870) | reject | 0.315 | 0.263 | - | loss |
| prop | Josh Giddey pts over 19.5 (401909870) | reject | 0.146 | 0.100 | - | loss |
| prop | Josh Giddey pts over 24.5 (401909870) | reject | 0.062 | 0.050 | - | loss |
| prop | Josh Giddey pts over 29.5 (401909870) | reject | 0.024 | 0.028 | - | loss |
| prop | Josh Giddey pts over 4.5 (401909870) | reject | 0.884 | 0.917 | - | win |
| prop | Josh Giddey pts over 9.5 (401909870) | reject | 0.588 | 0.592 | - | win |
| prop | Josh Giddey reb over 12.5 (401909870) | reject | 0.068 | 0.083 | - | loss |
| prop | Josh Giddey reb over 14.5 (401909870) | reject | 0.028 | 0.050 | - | loss |
| prop | Josh Giddey reb over 16.5 (401909870) | reject | 0.010 | 0.028 | - | loss |
| prop | Josh Giddey reb over 2.5 (401909870) | reject | 0.930 | 0.976 | - | loss |
| prop | Josh Giddey reb over 4.5 (401909870) | reject | 0.753 | 0.833 | - | loss |
| prop | Josh Giddey reb over 6.5 (401909870) | reject | 0.513 | 0.571 | - | loss |
| prop | Josh Giddey reb over 9.5 (401909870) | reject | 0.215 | 0.222 | - | loss |
| prop | Leonard Miller ast over 2.5 (401909870) | reject | 0.177 | 0.148 | - | loss |
| prop | Leonard Miller ast over 4.5 (401909870) | reject | 0.021 | 0.050 | - | loss |
| prop | Leonard Miller ast over 6.5 (401909870) | reject | 0.002 | 0.028 | - | loss |
| prop | Leonard Miller fg3m over 0.5 (401909870) | reject | 0.658 | 0.667 | - | win |
| prop | Leonard Miller fg3m over 1.5 (401909870) | reject | 0.313 | 0.312 | - | loss |
| prop | Leonard Miller fg3m over 2.5 (401909870) | reject | 0.119 | 0.121 | - | loss |
| prop | Leonard Miller fg3m over 3.5 (401909870) | reject | 0.039 | 0.059 | - | loss |
| prop | Leonard Miller fg3m over 4.5 (401909870) | reject | 0.011 | 0.034 | - | loss |
| prop | Leonard Miller pts over 14.5 (401909870) | reject | 0.288 | 0.200 | - | loss |
| prop | Leonard Miller pts over 19.5 (401909870) | reject | 0.128 | 0.077 | - | loss |
| prop | Leonard Miller pts over 24.5 (401909870) | reject | 0.051 | 0.034 | - | loss |
| prop | Leonard Miller pts over 29.5 (401909870) | reject | 0.019 | 0.028 | - | loss |
| prop | Leonard Miller pts over 4.5 (401909870) | reject | 0.872 | 0.875 | - | win |
| prop | Leonard Miller pts over 9.5 (401909870) | reject | 0.561 | 0.562 | - | loss |
| prop | Leonard Miller reb over 12.5 (401909870) | reject | 0.025 | 0.028 | - | loss |
| prop | Leonard Miller reb over 2.5 (401909870) | reject | 0.874 | 0.905 | - | win |
| prop | Leonard Miller reb over 4.5 (401909870) | reject | 0.623 | 0.595 | - | win |
| prop | Leonard Miller reb over 6.5 (401909870) | reject | 0.357 | 0.323 | - | win |
| prop | Leonard Miller reb over 9.5 (401909870) | reject | 0.110 | 0.091 | - | loss |
| prop | Matas Buzelis ast over 2.5 (401909870) | reject | 0.306 | 0.355 | - | loss |
| prop | Matas Buzelis ast over 4.5 (401909870) | reject | 0.060 | 0.100 | - | loss |
| prop | Matas Buzelis ast over 6.5 (401909870) | reject | 0.008 | 0.034 | - | loss |
| prop | Matas Buzelis fg3m over 0.5 (401909870) | reject | 0.835 | 0.889 | - | win |
| prop | Matas Buzelis fg3m over 1.5 (401909870) | reject | 0.567 | 0.649 | - | win |
| prop | Matas Buzelis fg3m over 2.5 (401909870) | reject | 0.324 | 0.357 | - | loss |
| prop | Matas Buzelis fg3m over 3.5 (401909870) | reject | 0.162 | 0.182 | - | loss |
| prop | Matas Buzelis fg3m over 4.5 (401909870) | reject | 0.073 | 0.091 | - | loss |
| prop | Matas Buzelis fg3m over 5.5 (401909870) | reject | 0.030 | 0.053 | - | loss |
| prop | Matas Buzelis fg3m over 6.5 (401909870) | reject | 0.011 | 0.028 | - | loss |
| prop | Matas Buzelis pts over 19.5 (401909870) | reject | 0.261 | 0.244 | - | loss |
| prop | Matas Buzelis pts over 24.5 (401909870) | reject | 0.136 | 0.103 | - | loss |
| prop | Matas Buzelis pts over 29.5 (401909870) | reject | 0.067 | 0.053 | - | loss |
| prop | Matas Buzelis pts over 34.5 (401909870) | reject | 0.031 | 0.028 | - | loss |
| prop | Matas Buzelis pts over 4.5 (401909870) | reject | 0.930 | 0.972 | - | win |
| prop | Matas Buzelis pts over 9.5 (401909870) | reject | 0.711 | 0.810 | - | win |
| prop | Matas Buzelis reb over 12.5 (401909870) | reject | 0.019 | 0.038 | - | loss |
| prop | Matas Buzelis reb over 14.5 (401909870) | reject | 0.006 | 0.028 | - | loss |
| prop | Matas Buzelis reb over 2.5 (401909870) | reject | 0.856 | 0.917 | - | loss |
| prop | Matas Buzelis reb over 4.5 (401909870) | reject | 0.589 | 0.649 | - | loss |
| prop | Matas Buzelis reb over 6.5 (401909870) | reject | 0.321 | 0.355 | - | loss |
| prop | Matas Buzelis reb over 9.5 (401909870) | reject | 0.091 | 0.103 | - | loss |
| prop | Mitchell Robinson ast over 2.5 (401909870) | reject | 0.074 | 0.105 | - | loss |
| prop | Mitchell Robinson ast over 4.5 (401909870) | reject | 0.004 | 0.028 | - | loss |
| prop | Mitchell Robinson pts over 14.5 (401909870) | reject | 0.048 | 0.077 | - | loss |
| prop | Mitchell Robinson pts over 19.5 (401909870) | reject | 0.009 | 0.028 | - | loss |
| prop | Mitchell Robinson pts over 4.5 (401909870) | reject | 0.632 | 0.697 | - | win |
| prop | Mitchell Robinson pts over 9.5 (401909870) | reject | 0.207 | 0.270 | - | loss |
| prop | Mitchell Robinson reb over 12.5 (401909870) | reject | 0.109 | 0.118 | - | loss |
| prop | Mitchell Robinson reb over 14.5 (401909870) | reject | 0.050 | 0.071 | - | loss |
| prop | Mitchell Robinson reb over 16.5 (401909870) | reject | 0.021 | 0.050 | - | loss |
| prop | Mitchell Robinson reb over 19.5 (401909870) | reject | 0.005 | 0.028 | - | loss |
| prop | Mitchell Robinson reb over 2.5 (401909870) | reject | 0.952 | 0.976 | - | win |
| prop | Mitchell Robinson reb over 4.5 (401909870) | reject | 0.814 | 0.857 | - | win |
| prop | Mitchell Robinson reb over 6.5 (401909870) | reject | 0.602 | 0.630 | - | win |
| prop | Mitchell Robinson reb over 9.5 (401909870) | reject | 0.293 | 0.299 | - | loss |
| prop | Neemias Queta ast over 2.5 (401909870) | reject | 0.199 | 0.250 | - | loss |
| prop | Neemias Queta ast over 4.5 (401909870) | reject | 0.026 | 0.062 | - | loss |
| prop | Neemias Queta ast over 6.5 (401909870) | reject | 0.002 | 0.028 | - | loss |
| prop | Neemias Queta pts over 14.5 (401909870) | reject | 0.179 | 0.238 | - | loss |
| prop | Neemias Queta pts over 19.5 (401909870) | reject | 0.062 | 0.091 | - | loss |
| prop | Neemias Queta pts over 24.5 (401909870) | reject | 0.020 | 0.038 | - | loss |
| prop | Neemias Queta pts over 4.5 (401909870) | reject | 0.808 | 0.917 | - | win |
| prop | Neemias Queta pts over 9.5 (401909870) | reject | 0.434 | 0.556 | - | loss |
| prop | Neemias Queta reb over 12.5 (401909870) | reject | 0.083 | 0.103 | - | loss |
| prop | Neemias Queta reb over 14.5 (401909870) | reject | 0.036 | 0.059 | - | loss |
| prop | Neemias Queta reb over 16.5 (401909870) | reject | 0.014 | 0.034 | - | loss |
| prop | Neemias Queta reb over 2.5 (401909870) | reject | 0.940 | 0.972 | - | win |
| prop | Neemias Queta reb over 4.5 (401909870) | reject | 0.780 | 0.857 | - | win |
| prop | Neemias Queta reb over 6.5 (401909870) | reject | 0.550 | 0.623 | - | loss |
| prop | Neemias Queta reb over 9.5 (401909870) | reject | 0.246 | 0.278 | - | loss |
| prop | Norman Powell ast over 2.5 (401909870) | reject | 0.370 | 0.339 | - | loss |
| prop | Norman Powell ast over 4.5 (401909870) | reject | 0.087 | 0.091 | - | loss |
| prop | Norman Powell ast over 6.5 (401909870) | reject | 0.014 | 0.028 | - | loss |
| prop | Norman Powell fg3m over 0.5 (401909870) | reject | 0.891 | 0.947 | - | win |
| prop | Norman Powell fg3m over 1.5 (401909870) | reject | 0.678 | 0.773 | - | win |
| prop | Norman Powell fg3m over 2.5 (401909870) | reject | 0.447 | 0.545 | - | win |
| prop | Norman Powell fg3m over 3.5 (401909870) | reject | 0.261 | 0.339 | - | win |
| prop | Norman Powell fg3m over 4.5 (401909870) | reject | 0.138 | 0.182 | - | loss |
| prop | Norman Powell fg3m over 5.5 (401909870) | reject | 0.067 | 0.103 | - | loss |
| prop | Norman Powell fg3m over 6.5 (401909870) | reject | 0.031 | 0.062 | - | loss |
| prop | Norman Powell fg3m over 7.5 (401909870) | reject | 0.013 | 0.048 | - | loss |
| prop | Norman Powell fg3m over 8.5 (401909870) | reject | 0.005 | 0.028 | - | loss |
| prop | Norman Powell pts over 14.5 (401909870) | reject | 0.627 | 0.744 | - | win |
| prop | Norman Powell pts over 19.5 (401909870) | reject | 0.433 | 0.488 | - | win |
| prop | Norman Powell pts over 24.5 (401909870) | reject | 0.277 | 0.256 | - | loss |
| prop | Norman Powell pts over 29.5 (401909870) | reject | 0.168 | 0.121 | - | loss |
| prop | Norman Powell pts over 34.5 (401909870) | reject | 0.097 | 0.071 | - | loss |
| prop | Norman Powell pts over 39.5 (401909870) | reject | 0.054 | 0.043 | - | loss |
| prop | Norman Powell pts over 9.5 (401909870) | reject | 0.826 | 0.933 | - | win |
| prop | Norman Powell reb over 2.5 (401909870) | reject | 0.614 | 0.706 | - | loss |
| prop | Norman Powell reb over 4.5 (401909870) | reject | 0.261 | 0.238 | - | loss |
| prop | Norman Powell reb over 6.5 (401909870) | reject | 0.080 | 0.100 | - | loss |
| prop | Norman Powell reb over 9.5 (401909870) | reject | 0.009 | 0.028 | - | loss |
| prop | Paul George ast over 2.5 (401909870) | reject | 0.603 | 0.677 | - | loss |
| prop | Paul George ast over 4.5 (401909870) | reject | 0.245 | 0.294 | - | loss |
| prop | Paul George ast over 6.5 (401909870) | reject | 0.070 | 0.105 | - | loss |
| prop | Paul George ast over 9.5 (401909870) | reject | 0.007 | 0.034 | - | loss |
| prop | Paul George fg3m over 0.5 (401909870) | reject | 0.925 | 0.972 | - | win |
| prop | Paul George fg3m over 1.5 (401909870) | reject | 0.757 | 0.857 | - | win |
| prop | Paul George fg3m over 2.5 (401909870) | reject | 0.549 | 0.649 | - | win |
| prop | Paul George fg3m over 3.5 (401909870) | reject | 0.357 | 0.426 | - | loss |
| prop | Paul George fg3m over 4.5 (401909870) | reject | 0.212 | 0.250 | - | loss |
| prop | Paul George fg3m over 5.5 (401909870) | reject | 0.117 | 0.138 | - | loss |
| prop | Paul George fg3m over 6.5 (401909870) | reject | 0.060 | 0.083 | - | loss |
| prop | Paul George fg3m over 7.5 (401909870) | reject | 0.030 | 0.053 | - | loss |
| prop | Paul George fg3m over 8.5 (401909870) | reject | 0.014 | 0.028 | - | loss |
| prop | Paul George pts over 14.5 (401909870) | reject | 0.615 | 0.778 | - | win |
| prop | Paul George pts over 19.5 (401909870) | reject | 0.419 | 0.543 | - | loss |
| prop | Paul George pts over 24.5 (401909870) | reject | 0.265 | 0.270 | - | loss |
| prop | Paul George pts over 29.5 (401909870) | reject | 0.158 | 0.121 | - | loss |
| prop | Paul George pts over 34.5 (401909870) | reject | 0.090 | 0.062 | - | loss |
| prop | Paul George pts over 39.5 (401909870) | reject | 0.050 | 0.034 | - | loss |
| prop | Paul George pts over 44.5 (401909870) | reject | 0.026 | 0.028 | - | loss |
| prop | Paul George pts over 9.5 (401909870) | reject | 0.819 | 0.947 | - | win |
| prop | Paul George reb over 12.5 (401909870) | reject | 0.013 | 0.028 | - | loss |
| prop | Paul George reb over 2.5 (401909870) | reject | 0.834 | 0.882 | - | win |
| prop | Paul George reb over 4.5 (401909870) | reject | 0.548 | 0.541 | - | win |
| prop | Paul George reb over 6.5 (401909870) | reject | 0.282 | 0.263 | - | loss |
| prop | Paul George reb over 9.5 (401909870) | reject | 0.072 | 0.071 | - | loss |
| prop | Payton Pritchard ast over 12.5 (401909870) | reject | 0.004 | 0.028 | - | loss |
| prop | Payton Pritchard ast over 2.5 (401909870) | reject | 0.767 | 0.857 | - | win |
| prop | Payton Pritchard ast over 4.5 (401909870) | reject | 0.433 | 0.556 | - | loss |
| prop | Payton Pritchard ast over 6.5 (401909870) | reject | 0.182 | 0.250 | - | loss |
| prop | Payton Pritchard ast over 9.5 (401909870) | reject | 0.032 | 0.077 | - | loss |
| prop | Payton Pritchard fg3m over 0.5 (401909870) | reject | 0.882 | 0.941 | - | win |
| prop | Payton Pritchard fg3m over 1.5 (401909870) | reject | 0.659 | 0.750 | - | win |
| prop | Payton Pritchard fg3m over 2.5 (401909870) | reject | 0.424 | 0.481 | - | win |
| prop | Payton Pritchard fg3m over 3.5 (401909870) | reject | 0.241 | 0.286 | - | win |
| prop | Payton Pritchard fg3m over 4.5 (401909870) | reject | 0.124 | 0.148 | - | win |
| prop | Payton Pritchard fg3m over 5.5 (401909870) | reject | 0.059 | 0.091 | - | win |
| prop | Payton Pritchard fg3m over 6.5 (401909870) | reject | 0.026 | 0.056 | - | win |
| prop | Payton Pritchard fg3m over 7.5 (401909870) | reject | 0.011 | 0.038 | - | loss |
| prop | Payton Pritchard fg3m over 8.5 (401909870) | reject | 0.004 | 0.028 | - | loss |
| prop | Payton Pritchard pts over 14.5 (401909870) | reject | 0.470 | 0.592 | - | win |
| prop | Payton Pritchard pts over 19.5 (401909870) | reject | 0.272 | 0.303 | - | win |
| prop | Payton Pritchard pts over 24.5 (401909870) | reject | 0.144 | 0.133 | - | win |
| prop | Payton Pritchard pts over 29.5 (401909870) | reject | 0.071 | 0.062 | - | loss |
| prop | Payton Pritchard pts over 34.5 (401909870) | reject | 0.034 | 0.034 | - | loss |
| prop | Payton Pritchard pts over 4.5 (401909870) | reject | 0.933 | 0.988 | - | win |
| prop | Payton Pritchard pts over 9.5 (401909870) | reject | 0.719 | 0.867 | - | win |
| prop | Payton Pritchard reb over 2.5 (401909870) | reject | 0.634 | 0.667 | - | loss |
| prop | Payton Pritchard reb over 4.5 (401909870) | reject | 0.280 | 0.267 | - | loss |
| prop | Payton Pritchard reb over 6.5 (401909870) | reject | 0.090 | 0.095 | - | loss |
| prop | Payton Pritchard reb over 9.5 (401909870) | reject | 0.011 | 0.028 | - | loss |
| prop | Sam Hauser ast over 2.5 (401909870) | reject | 0.144 | 0.190 | - | loss |
| prop | Sam Hauser ast over 4.5 (401909870) | reject | 0.014 | 0.053 | - | loss |
| prop | Sam Hauser ast over 6.5 (401909870) | reject | 0.001 | 0.028 | - | loss |
| prop | Sam Hauser fg3m over 0.5 (401909870) | reject | 0.850 | 0.917 | - | win |
| prop | Sam Hauser fg3m over 1.5 (401909870) | reject | 0.595 | 0.688 | - | win |
| prop | Sam Hauser fg3m over 2.5 (401909870) | reject | 0.353 | 0.435 | - | win |
| prop | Sam Hauser fg3m over 3.5 (401909870) | reject | 0.184 | 0.238 | - | loss |
| prop | Sam Hauser fg3m over 4.5 (401909870) | reject | 0.086 | 0.129 | - | loss |
| prop | Sam Hauser fg3m over 5.5 (401909870) | reject | 0.037 | 0.071 | - | loss |
| prop | Sam Hauser fg3m over 6.5 (401909870) | reject | 0.015 | 0.050 | - | loss |
| prop | Sam Hauser fg3m over 7.5 (401909870) | reject | 0.006 | 0.028 | - | loss |
| prop | Sam Hauser pts over 14.5 (401909870) | reject | 0.119 | 0.174 | - | loss |
| prop | Sam Hauser pts over 19.5 (401909870) | reject | 0.034 | 0.071 | - | loss |
| prop | Sam Hauser pts over 24.5 (401909870) | reject | 0.009 | 0.034 | - | loss |
| prop | Sam Hauser pts over 4.5 (401909870) | reject | 0.753 | 0.833 | - | win |
| prop | Sam Hauser pts over 9.5 (401909870) | reject | 0.347 | 0.426 | - | win |
| prop | Sam Hauser reb over 2.5 (401909870) | reject | 0.613 | 0.630 | - | win |
| prop | Sam Hauser reb over 4.5 (401909870) | reject | 0.260 | 0.267 | - | loss |
| prop | Sam Hauser reb over 6.5 (401909870) | reject | 0.080 | 0.095 | - | loss |
| prop | Sam Hauser reb over 9.5 (401909870) | reject | 0.009 | 0.028 | - | loss |
| prop | Tre Jones ast over 12.5 (401909870) | reject | 0.001 | 0.028 | - | loss |
| prop | Tre Jones ast over 2.5 (401909870) | reject | 0.656 | 0.818 | - | loss |
| prop | Tre Jones ast over 4.5 (401909870) | reject | 0.296 | 0.565 | - | loss |
| prop | Tre Jones ast over 6.5 (401909870) | reject | 0.096 | 0.222 | - | loss |
| prop | Tre Jones ast over 9.5 (401909870) | reject | 0.011 | 0.071 | - | loss |
| prop | Tre Jones fg3m over 0.5 (401909870) | reject | 0.389 | 0.444 | - | loss |
| prop | Tre Jones fg3m over 1.5 (401909870) | reject | 0.097 | 0.138 | - | loss |
| prop | Tre Jones fg3m over 2.5 (401909870) | reject | 0.018 | 0.056 | - | loss |
| prop | Tre Jones fg3m over 3.5 (401909870) | reject | 0.003 | 0.028 | - | loss |
| prop | Tre Jones pts over 14.5 (401909870) | reject | 0.240 | 0.182 | - | loss |
| prop | Tre Jones pts over 19.5 (401909870) | reject | 0.097 | 0.071 | - | loss |
| prop | Tre Jones pts over 24.5 (401909870) | reject | 0.035 | 0.028 | - | loss |
| prop | Tre Jones pts over 4.5 (401909870) | reject | 0.848 | 0.857 | - | win |
| prop | Tre Jones pts over 9.5 (401909870) | reject | 0.509 | 0.541 | - | loss |
| prop | Tre Jones reb over 2.5 (401909870) | reject | 0.417 | 0.481 | - | loss |
| prop | Tre Jones reb over 4.5 (401909870) | reject | 0.115 | 0.129 | - | loss |
| prop | Tre Jones reb over 6.5 (401909870) | reject | 0.022 | 0.050 | - | loss |
| prop | Norman Powell ast over 1.5 (401909870) | reject | 0.619 | 0.610 | - | win |
| prop | Norman Powell ast under 1.5 (401909870) | reject | 0.381 | 0.610 | - | loss |
| prop | Norman Powell fg3m under 2.5 (401909870) | reject | 0.553 | 0.565 | - | loss |
| prop | Norman Powell reb over 3.5 (401909870) | reject | 0.420 | 0.595 | - | loss |
| prop | Norman Powell reb under 3.5 (401909870) | reject | 0.580 | 0.595 | - | win |
| prop | Derrick White ast over 5.5 (401909870) | reject | 0.339 | 0.562 | - | loss |
| prop | Derrick White ast under 5.5 (401909870) | reject | 0.661 | 0.562 | - | win |
| prop | Derrick White fg3m under 2.5 (401909870) | reject | 0.548 | 0.565 | - | win |
| prop | Derrick White pts over 16.5 (401909870) | reject | 0.388 | 0.532 | - | loss |
| prop | Derrick White pts under 16.5 (401909870) | reject | 0.612 | 0.532 | - | win |
| prop | Derrick White reb over 3.5 (401909870) | reject | 0.568 | 0.543 | - | win |
| prop | Derrick White reb under 3.5 (401909870) | reject | 0.432 | 0.543 | - | loss |
| prop | Jayson Tatum ast under 6.5 (401909870) | reject | 0.483 | 0.503 | - | win |
| prop | Jayson Tatum fg3m under 3.5 (401909870) | reject | 0.636 | 0.581 | - | win |
| prop | Jayson Tatum pts over 27.5 (401909870) | reject | 0.382 | 0.538 | - | loss |
| prop | Jayson Tatum pts under 27.5 (401909870) | reject | 0.618 | 0.538 | - | win |
| prop | Jayson Tatum reb over 8.5 (401909870) | reject | 0.583 | 0.571 | - | loss |
| prop | Jayson Tatum reb under 8.5 (401909870) | reject | 0.417 | 0.571 | - | win |
| prop | Payton Pritchard ast under 4.5 (401909870) | reject | 0.567 | 0.556 | - | win |
| prop | Payton Pritchard fg3m under 2.5 (401909870) | reject | 0.576 | 0.588 | - | loss |
| prop | Payton Pritchard pts over 16.5 (401909870) | reject | 0.382 | 0.532 | - | win |
| prop | Payton Pritchard pts under 16.5 (401909870) | reject | 0.618 | 0.532 | - | loss |
| prop | Payton Pritchard reb over 3.5 (401909870) | reject | 0.441 | 0.581 | - | loss |
| prop | Payton Pritchard reb under 3.5 (401909870) | reject | 0.559 | 0.581 | - | win |
| prop | Paul George ast over 3.5 (401909870) | reject | 0.404 | 0.613 | - | loss |
| prop | Paul George ast under 3.5 (401909870) | reject | 0.596 | 0.613 | - | win |
| prop | Paul George fg3m under 3.5 (401909870) | reject | 0.643 | 0.617 | - | win |
| prop | Paul George pts under 19.5 (401909870) | reject | 0.581 | 0.543 | - | win |
| prop | Paul George reb under 4.5 (401909870) | reject | 0.452 | 0.541 | - | loss |
| prop | Mitchell Robinson pts over 6.5 (401909870) | reject | 0.428 | 0.581 | - | win |
| prop | Mitchell Robinson pts under 6.5 (401909870) | reject | 0.572 | 0.581 | - | loss |
| prop | Mitchell Robinson reb over 7.5 (401909870) | reject | 0.490 | 0.571 | - | loss |
| prop | Mitchell Robinson reb under 7.5 (401909870) | reject | 0.510 | 0.571 | - | win |
| prop | Tre Jones ast under 4.5 (401909870) | reject | 0.704 | 0.565 | - | win |
| prop | Tre Jones pts under 9.5 (401909870) | reject | 0.491 | 0.541 | - | win |
| prop | Tre Jones reb under 2.5 (401909870) | reject | 0.583 | 0.588 | - | win |
| prop | Jalen Smith ast over 1.5 (401909870) | reject | 0.330 | 0.610 | - | loss |
| prop | Jalen Smith ast under 1.5 (401909870) | reject | 0.670 | 0.610 | - | win |
| prop | Jalen Smith fg3m under 1.5 (401909870) | reject | 0.540 | 0.575 | - | loss |
| prop | Jalen Smith pts over 10.5 (401909870) | reject | 0.472 | 0.562 | - | loss |
| prop | Jalen Smith pts under 10.5 (401909870) | reject | 0.528 | 0.562 | - | win |
| prop | Jalen Smith reb over 7.5 (401909870) | reject | 0.441 | 0.565 | - | loss |
| prop | Jalen Smith reb under 7.5 (401909870) | reject | 0.559 | 0.565 | - | win |
| prop | Neemias Queta pts under 9.5 (401909870) | reject | 0.566 | 0.556 | - | win |
| prop | Neemias Queta reb over 7.5 (401909870) | reject | 0.436 | 0.562 | - | loss |
| prop | Neemias Queta reb under 7.5 (401909870) | reject | 0.564 | 0.562 | - | win |
| prop | Matas Buzelis ast over 1.5 (401909870) | reject | 0.557 | 0.585 | - | win |
| prop | Matas Buzelis ast under 1.5 (401909870) | reject | 0.443 | 0.585 | - | loss |
| prop | Matas Buzelis fg3m under 1.5 (401909870) | reject | 0.433 | 0.418 | - | loss |
| prop | Matas Buzelis pts under 15.5 (401909870) | reject | 0.587 | 0.556 | - | win |
| prop | Matas Buzelis reb over 5.5 (401909870) | reject | 0.446 | 0.592 | - | loss |
| prop | Matas Buzelis reb under 5.5 (401909870) | reject | 0.554 | 0.592 | - | win |
| prop | Josh Giddey fg3m under 1.5 (401909870) | reject | 0.574 | 0.649 | - | win |
| prop | Josh Giddey pts over 11.5 (401909870) | reject | 0.468 | 0.556 | - | loss |
| prop | Josh Giddey pts under 11.5 (401909870) | reject | 0.532 | 0.556 | - | win |
| prop | Josh Giddey reb under 6.5 (401909870) | reject | 0.487 | 0.498 | - | win |
| prop | Leonard Miller pts under 9.5 (401909870) | reject | 0.439 | 0.562 | - | win |
| spread | away 14.5 (401909870) | reject | 0.589 | 0.535 | - | loss |
| prop | LaMelo Ball pts over 4.5 (401909869) | reject | 0.939 | 0.990 | - | win |
| prop | Ayo Dosunmu pts over 4.5 (401909869) | reject | 0.912 | 0.947 | - | win |
| prop | Ayo Dosunmu pts over 9.5 (401909869) | reject | 0.660 | 0.722 | - | loss |
| prop | Ayo Dosunmu pts over 14.5 (401909869) | reject | 0.395 | 0.426 | - | loss |
| prop | Ayo Dosunmu pts over 19.5 (401909869) | reject | 0.207 | 0.200 | - | loss |
| prop | Ayo Dosunmu pts over 24.5 (401909869) | reject | 0.099 | 0.091 | - | loss |
| prop | Ayo Dosunmu pts over 29.5 (401909869) | reject | 0.044 | 0.050 | - | loss |
| prop | Ayo Dosunmu pts over 34.5 (401909869) | reject | 0.019 | 0.028 | - | loss |
| prop | Ayo Dosunmu ast over 2.5 (401909869) | reject | 0.696 | 0.692 | - | loss |
| prop | Ayo Dosunmu ast over 4.5 (401909869) | reject | 0.341 | 0.333 | - | loss |
| prop | Ayo Dosunmu ast over 6.5 (401909869) | reject | 0.121 | 0.133 | - | loss |
| prop | Ayo Dosunmu ast over 9.5 (401909869) | reject | 0.016 | 0.050 | - | loss |
| prop | James Harden reb over 12.5 (401909869) | reject | 0.006 | 0.028 | - | loss |
| prop | Ayo Dosunmu reb over 2.5 (401909869) | reject | 0.649 | 0.667 | - | loss |
| prop | Ayo Dosunmu reb over 4.5 (401909869) | reject | 0.296 | 0.299 | - | loss |
| prop | Ayo Dosunmu reb over 6.5 (401909869) | reject | 0.098 | 0.103 | - | loss |
| prop | Ayo Dosunmu reb over 9.5 (401909869) | reject | 0.012 | 0.034 | - | loss |
| prop | Ayo Dosunmu fg3m over 0.5 (401909869) | reject | 0.744 | 0.737 | - | win |
| prop | Ayo Dosunmu fg3m over 2.5 (401909869) | reject | 0.195 | 0.190 | - | loss |
| prop | Ayo Dosunmu fg3m over 3.5 (401909869) | reject | 0.078 | 0.095 | - | loss |
| prop | Ayo Dosunmu fg3m over 4.5 (401909869) | reject | 0.028 | 0.053 | - | loss |
| prop | Ayo Dosunmu fg3m over 5.5 (401909869) | reject | 0.009 | 0.028 | - | loss |
| prop | Norman Powell pts over 44.5 (401909870) | reject | 0.029 | 0.028 | - | loss |
| prop | Josh Giddey ast over 2.5 (401909870) | reject | 0.962 | 0.990 | - | win |
| prop | Derrick White fg3m over 8.5 (401909870) | reject | 0.006 | 0.028 | - | loss |
| spread | away 2.5 (401909834) | reject | 0.528 | 0.528 | -0.000 | win |
| prop | Ryan Kalkbrenner pts under 6.5 (401909868) | reject | 0.568 | 0.568 | -0.001 | win |
| prop | Jonathan Kuminga reb over 4.5 (401909869) | reject | 0.597 | 0.599 | -0.003 | win |
| prop | Nikola Jokic pts under 24.5 (401909094) | reject | 0.517 | 0.518 | -0.003 | win |
| prop | Evan Mobley fg3m under 1.5 (401909869) | reject | 0.695 | 0.699 | -0.006 | loss |
| prop | Bilal Coulibaly fg3m under 1.5 (401909868) | reject | 0.684 | 0.690 | -0.009 | win |
| prop | Josh Giddey ast under 8.5 (401909870) | reject | 0.590 | 0.595 | -0.009 | win |
| prop | Norman Powell pts under 18.5 (401909870) | reject | 0.531 | 0.538 | -0.013 | loss |
| ml | away (401909834) | reject | 0.463 | 0.469 | -0.014 | win |
| prop | Peyton Watson reb over 3.5 (401909869) | reject | 0.604 | 0.613 | -0.015 | win |
| ml | home (401909838) | reject | 0.543 | 0.552 | -0.016 | win |
| prop | Kyshawn George pts under 14.5 (401909868) | reject | 0.526 | 0.535 | -0.016 | loss |
| prop | Jared McCain pts over 10.5 (401909094) | reject | 0.534 | 0.543 | -0.017 | loss |
| prop | James Harden reb over 4.5 (401909869) | reject | 0.465 | 0.474 | -0.019 | loss |
| prop | Jarrett Allen pts over 12.5 (401909093) | reject | 0.530 | 0.541 | -0.020 | win |
| prop | Josh Giddey pts over 10.5 (401909870) | reject | 0.527 | 0.538 | -0.021 | win |
| ml | away (401909093) | reject | 0.451 | 0.461 | -0.021 | loss |
| spread | away 2.5 (401909093) | reject | 0.516 | 0.528 | -0.022 | loss |
| spread | away 8.5 (401909094) | reject | 0.526 | 0.539 | -0.024 | loss |
| prop | Terrence Shannon Jr. pts over 9.5 (401909869) | reject | 0.536 | 0.549 | -0.024 | win |
| prop | Anthony Edwards reb over 4.5 (401909869) | reject | 0.462 | 0.474 | -0.025 | loss |
| prop | James Harden pts over 17.5 (401909093) | reject | 0.541 | 0.556 | -0.026 | loss |
| prop | Chet Holmgren fg3m under 1.5 (401909094) | reject | 0.684 | 0.704 | -0.029 | win |
| spread | home -1.5 (401909838) | reject | 0.510 | 0.526 | -0.030 | win |
| prop | Ayo Dosunmu reb under 3.5 (401909869) | reject | 0.541 | 0.559 | -0.031 | win |
| total | under 227.5 (401909868) | reject | 0.516 | 0.535 | -0.036 | win |
| prop | Donovan Mitchell reb under 4.5 (401909869) | reject | 0.484 | 0.503 | -0.037 | loss |
| prop | Jared McCain fg3m under 2.5 (401909094) | reject | 0.620 | 0.645 | -0.040 | win |
| prop | Jonathan Kuminga ast under 2.5 (401909869) | reject | 0.595 | 0.621 | -0.042 | win |
| prop | Alex Sarr pts over 10.5 (401909868) | reject | 0.528 | 0.552 | -0.044 | win |
| prop | Jarrett Allen reb under 8.5 (401909093) | reject | 0.542 | 0.568 | -0.046 | win |
| prop | Trae Young ast over 9.5 (401909868) | reject | 0.556 | 0.585 | -0.049 | win |
| prop | Chet Holmgren fg3m under 0.5 (401909094) | reject | 0.340 | 0.357 | -0.049 | win |
| ml | home (401909834) | reject | 0.537 | 0.565 | -0.050 | loss |
| ml | home (401909093) | reject | 0.549 | 0.578 | -0.050 | win |
| prop | Jaylon Tyson fg3m over 1.5 (401909869) | reject | 0.394 | 0.415 | -0.051 | loss |
| prop | Evan Mobley pts under 17.5 (401909093) | reject | 0.509 | 0.538 | -0.054 | loss |
| total | over 227.5 (401909868) | reject | 0.484 | 0.512 | -0.055 | loss |
| spread | away 1.5 (401909838) | reject | 0.490 | 0.519 | -0.056 | loss |
| ml | home (401909094) | reject | 0.724 | 0.767 | -0.057 | win |
| prop | Jarrett Allen reb over 7.5 (401909093) | reject | 0.561 | 0.595 | -0.057 | loss |
| prop | Tyrese Maxey pts over 23.5 (401909093) | reject | 0.518 | 0.552 | -0.062 | win |
| ml | away (401909838) | reject | 0.457 | 0.488 | -0.063 | loss |
| ml | home (401909841) | reject | 0.549 | 0.587 | -0.065 | win |
| prop | James Harden pts under 16.5 (401909869) | reject | 0.514 | 0.549 | -0.065 | loss |
| spread | home -8.5 (401909094) | reject | 0.474 | 0.507 | -0.066 | win |
| prop | Jonathan Kuminga fg3m under 1.5 (401909869) | reject | 0.609 | 0.654 | -0.069 | win |
| spread | home -2.5 (401909093) | reject | 0.484 | 0.519 | -0.069 | win |
| prop | Jaylon Tyson fg3m under 1.5 (401909869) | reject | 0.606 | 0.654 | -0.072 | win |
| prop | Shai Gilgeous-Alexander reb over 3.5 (401909094) | reject | 0.573 | 0.617 | -0.072 | loss |
| prop | Ayo Dosunmu ast over 3.5 (401909869) | reject | 0.510 | 0.549 | -0.072 | loss |
| prop | Jarrett Allen pts under 13.5 (401909093) | reject | 0.521 | 0.562 | -0.073 | loss |
| prop | Ayo Dosunmu pts under 12.5 (401909869) | reject | 0.506 | 0.546 | -0.074 | win |
| prop | Evan Mobley reb over 8.5 (401909869) | reject | 0.541 | 0.585 | -0.075 | loss |
| prop | Jarrett Allen pts under 12.5 (401909869) | reject | 0.501 | 0.543 | -0.078 | win |
| prop | Peyton Watson fg3m under 1.5 (401909869) | reject | 0.598 | 0.649 | -0.079 | win |
| prop | Peyton Watson pts under 12.5 (401909869) | reject | 0.511 | 0.556 | -0.081 | loss |
| prop | Jarrett Allen pts over 12.5 (401909869) | reject | 0.499 | 0.543 | -0.082 | loss |
| spread | home -2.5 (401909841) | reject | 0.484 | 0.528 | -0.085 | win |
| prop | Evan Mobley pts over 17.5 (401909093) | reject | 0.491 | 0.538 | -0.086 | win |
| spread | home -2.5 (401909834) | reject | 0.472 | 0.517 | -0.087 | loss |
| prop | Donovan Mitchell fg3m under 2.5 (401909869) | reject | 0.505 | 0.556 | -0.090 | loss |
| prop | Donovan Mitchell reb over 4.5 (401909869) | reject | 0.516 | 0.568 | -0.092 | win |
| prop | Josh Giddey ast over 7.5 (401909870) | reject | 0.518 | 0.571 | -0.093 | loss |
| prop | Terrence Shannon Jr. fg3m under 1.5 (401909869) | reject | 0.603 | 0.667 | -0.095 | loss |
| prop | Trae Young ast under 10.5 (401909868) | reject | 0.535 | 0.592 | -0.095 | win |
| prop | Ayo Dosunmu pts over 12.5 (401909869) | reject | 0.494 | 0.546 | -0.096 | loss |
| prop | Anthony Edwards reb under 4.5 (401909869) | reject | 0.538 | 0.595 | -0.097 | win |
| prop | Jaden McDaniels reb under 4.5 (401909869) | reject | 0.544 | 0.602 | -0.097 | loss |
| prop | Alex Sarr reb over 5.5 (401909868) | reject | 0.523 | 0.581 | -0.100 | win |
| spread | away 2.5 (401909090) | reject | 0.481 | 0.535 | -0.100 | win |
| prop | Bilal Coulibaly reb over 3.5 (401909868) | reject | 0.559 | 0.621 | -0.100 | win |
| prop | James Harden reb under 4.5 (401909869) | reject | 0.535 | 0.595 | -0.101 | win |
| prop | Sam Merrill pts over 7.5 (401909869) | reject | 0.511 | 0.568 | -0.101 | win |
| prop | Alex Sarr fg3m over 0.5 (401909868) | reject | 0.594 | 0.662 | -0.104 | loss |
| ml | home (401909092) | reject | 0.625 | 0.697 | -0.104 | win |
| prop | Jared McCain fg3m over 2.5 (401909094) | reject | 0.380 | 0.426 | -0.106 | loss |
| prop | Christian Braun ast under 2.5 (401909094) | reject | 0.592 | 0.662 | -0.107 | win |
| prop | Ayo Dosunmu ast under 3.5 (401909869) | reject | 0.490 | 0.549 | -0.108 | win |
| prop | Jaylen Brown reb under 6.5 (401909093) | reject | 0.504 | 0.565 | -0.108 | loss |
| spread | away 1.5 (401909091) | reject | 0.471 | 0.528 | -0.108 | win |
| prop | Donovan Mitchell fg3m over 2.5 (401909869) | reject | 0.495 | 0.556 | -0.110 | win |
| prop | Ajay Mitchell pts under 10.5 (401909094) | reject | 0.505 | 0.568 | -0.111 | loss |
| prop | Jonathan Kuminga reb under 5.5 (401909869) | reject | 0.544 | 0.613 | -0.113 | loss |
| prop | Kyshawn George pts over 14.5 (401909868) | reject | 0.474 | 0.535 | -0.114 | win |
| ml | away (401909091) | reject | 0.438 | 0.495 | -0.114 | win |
| prop | James Harden pts over 16.5 (401909869) | reject | 0.486 | 0.549 | -0.115 | win |
| prop | Joel Embiid reb over 7.5 (401909093) | reject | 0.524 | 0.592 | -0.115 | loss |
| prop | Peyton Watson pts over 12.5 (401909869) | reject | 0.489 | 0.556 | -0.119 | win |
| prop | Josh Giddey pts under 10.5 (401909870) | reject | 0.473 | 0.538 | -0.119 | loss |
| ml | home (401909840) | reject | 0.714 | 0.811 | -0.120 | win |
| total | over 232.5 (401909870) | reject | 0.466 | 0.531 | -0.121 | win |
| prop | Jaylen Brown reb over 6.5 (401909093) | reject | 0.496 | 0.565 | -0.122 | win |
| prop | Chet Holmgren fg3m over 1.5 (401909094) | reject | 0.316 | 0.361 | -0.124 | loss |
| prop | Norman Powell pts over 18.5 (401909870) | reject | 0.469 | 0.538 | -0.127 | win |
| prop | Tyrese Maxey pts under 23.5 (401909093) | reject | 0.482 | 0.552 | -0.128 | loss |
| prop | Sam Merrill fg3m over 1.5 (401909869) | reject | 0.552 | 0.633 | -0.128 | loss |
| prop | Evan Mobley ast under 3.5 (401909869) | reject | 0.537 | 0.617 | -0.129 | win |
| prop | Ajay Mitchell pts over 10.5 (401909094) | reject | 0.495 | 0.568 | -0.129 | win |
| prop | Jarrett Allen pts under 12.5 (401909093) | reject | 0.470 | 0.541 | -0.130 | loss |
| total | over 233.5 (401909870) | reject | 0.445 | 0.512 | -0.131 | loss |
| prop | James Harden fg3m under 2.5 (401909869) | reject | 0.574 | 0.662 | -0.133 | loss |
| ml | home (401909837) | reject | 0.705 | 0.815 | -0.134 | win |
| prop | Jamal Murray ast under 6.5 (401909094) | reject | 0.515 | 0.595 | -0.135 | win |
| prop | Sam Merrill fg3m over 1.5 (401909093) | reject | 0.568 | 0.658 | -0.137 | loss |
| prop | Sam Merrill pts under 7.5 (401909869) | reject | 0.489 | 0.568 | -0.139 | loss |
| prop | Jonathan Kuminga reb under 4.5 (401909869) | reject | 0.403 | 0.469 | -0.142 | loss |
| prop | Jared McCain pts under 10.5 (401909094) | reject | 0.466 | 0.543 | -0.143 | win |
| prop | Ayo Dosunmu fg3m under 1.5 (401909869) | reject | 0.578 | 0.676 | -0.144 | win |
| prop | Alex Sarr pts under 10.5 (401909868) | reject | 0.472 | 0.552 | -0.146 | loss |
| prop | Rudy Gobert pts over 9.5 (401909869) | reject | 0.459 | 0.538 | -0.147 | loss |
| prop | Jarrett Allen pts over 13.5 (401909093) | reject | 0.479 | 0.562 | -0.147 | win |
| prop | Matas Buzelis pts over 14.5 (401909870) | reject | 0.458 | 0.541 | -0.152 | loss |
| prop | Cameron Johnson pts over 12.5 (401909094) | reject | 0.458 | 0.541 | -0.153 | loss |
| prop | Terrence Shannon Jr. pts under 9.5 (401909869) | reject | 0.464 | 0.549 | -0.156 | loss |
| prop | Josh Giddey ast under 7.5 (401909870) | reject | 0.482 | 0.571 | -0.157 | win |
| prop | Jarrett Allen reb under 7.5 (401909869) | reject | 0.501 | 0.595 | -0.159 | loss |
| prop | Evan Mobley pts over 17.5 (401909869) | reject | 0.450 | 0.535 | -0.159 | loss |
| spread | away 1.5 (401909090) | reject | 0.449 | 0.535 | -0.161 | win |
| prop | Jarrett Allen reb over 7.5 (401909869) | reject | 0.499 | 0.595 | -0.161 | win |
| prop | Nikola Jokic pts over 25.5 (401909094) | reject | 0.455 | 0.543 | -0.162 | loss |
| prop | Joel Embiid ast under 4.5 (401909093) | reject | 0.516 | 0.617 | -0.164 | win |
| prop | James Harden pts over 17.5 (401909869) | reject | 0.446 | 0.535 | -0.165 | win |
| prop | Anthony Davis fg3m over 0.5 (401909868) | reject | 0.451 | 0.541 | -0.166 | win |
| prop | Jarrett Allen pts over 13.5 (401909869) | reject | 0.448 | 0.541 | -0.172 | loss |
| spread | home -13.5 (401909870) | reject | 0.443 | 0.535 | -0.172 | win |
| prop | James Harden pts under 17.5 (401909093) | reject | 0.459 | 0.556 | -0.174 | win |
| prop | Anfernee Simons fg3m under 2.5 (401909093) | reject | 0.535 | 0.649 | -0.175 | win |
| prop | Ayo Dosunmu reb over 3.5 (401909869) | reject | 0.459 | 0.559 | -0.179 | loss |
| prop | Alex Sarr reb under 5.5 (401909868) | reject | 0.477 | 0.581 | -0.180 | loss |
| prop | Jamal Murray reb under 4.5 (401909094) | reject | 0.508 | 0.621 | -0.181 | loss |
| spread | home -6.5 (401909092) | reject | 0.431 | 0.528 | -0.185 | win |
| prop | LeBron James reb over 6.5 (401909093) | reject | 0.482 | 0.592 | -0.186 | win |
| prop | Evan Mobley fg3m under 0.5 (401909093) | reject | 0.340 | 0.418 | -0.189 | loss |
| spread | home -9.5 (401909840) | reject | 0.430 | 0.531 | -0.190 | win |
| prop | Ayo Dosunmu pts over 13.5 (401909869) | reject | 0.443 | 0.546 | -0.190 | loss |
| prop | Donovan Mitchell pts over 26.5 (401909093) | reject | 0.438 | 0.541 | -0.190 | win |
| total | over 219.5 (401909836) | reject | 0.423 | 0.524 | -0.192 | loss |
| prop | Jarrett Allen reb over 8.5 (401909093) | reject | 0.458 | 0.568 | -0.194 | loss |
| prop | Joel Embiid reb under 7.5 (401909093) | reject | 0.476 | 0.592 | -0.195 | win |
| spread | home -14.5 (401909870) | reject | 0.411 | 0.512 | -0.197 | win |
| prop | Jaylon Tyson pts over 8.5 (401909869) | reject | 0.436 | 0.543 | -0.198 | win |
| prop | Jamal Murray pts under 21.5 (401909094) | reject | 0.430 | 0.538 | -0.200 | win |
| ml | away (401909088) | reject | 0.438 | 0.550 | -0.203 | loss |
| prop | Rudy Gobert reb over 11.5 (401909869) | reject | 0.428 | 0.538 | -0.204 | win |
| prop | Leonard Miller reb under 4.5 (401909870) | reject | 0.377 | 0.474 | -0.205 | loss |
| prop | Tre Johnson pts under 9.5 (401909868) | reject | 0.441 | 0.556 | -0.207 | win |
| prop | Grayson Allen pts over 15.5 (401909868) | reject | 0.437 | 0.552 | -0.209 | loss |
| spread | away 4.5 (401909842) | reject | 0.397 | 0.505 | -0.214 | loss |
| spread | away 2.5 (401909868) | reject | 0.411 | 0.524 | -0.214 | loss |
| prop | Trae Young ast over 10.5 (401909868) | reject | 0.465 | 0.592 | -0.215 | loss |
| prop | Evan Mobley reb under 8.5 (401909869) | reject | 0.459 | 0.585 | -0.215 | win |
| prop | Ajay Mitchell pts over 11.5 (401909094) | reject | 0.435 | 0.556 | -0.216 | win |
| prop | VJ Edgecombe reb under 4.5 (401909093) | reject | 0.367 | 0.469 | -0.219 | loss |
| spread | away -1.5 (401909088) | reject | 0.406 | 0.524 | -0.224 | loss |
| total | over 227.5 (401909842) | reject | 0.402 | 0.519 | -0.225 | loss |
| prop | Ajay Mitchell ast under 2.5 (401909094) | reject | 0.340 | 0.439 | -0.225 | win |
| prop | Donovan Mitchell pts over 25.5 (401909869) | reject | 0.426 | 0.549 | -0.225 | win |
| prop | Jonathan Kuminga pts under 11.5 (401909869) | reject | 0.432 | 0.559 | -0.226 | win |
| prop | Sam Merrill fg3m over 2.5 (401909093) | reject | 0.325 | 0.422 | -0.229 | loss |
| total | over 231.5 (401909869) | reject | 0.412 | 0.535 | -0.230 | win |
| ml | away (401909090) | reject | 0.416 | 0.541 | -0.231 | win |
| ml | away (401909868) | reject | 0.348 | 0.455 | -0.234 | loss |
| total | over 232.5 (401909869) | reject | 0.391 | 0.512 | -0.237 | win |
| prop | Ryan Kalkbrenner pts over 6.5 (401909868) | reject | 0.432 | 0.568 | -0.239 | loss |
| prop | LaMelo Ball fg3m over 3.5 (401909869) | reject | 0.373 | 0.490 | -0.240 | loss |
| prop | Trae Young ast under 9.5 (401909868) | reject | 0.444 | 0.585 | -0.241 | loss |
| prop | Jaden McDaniels reb over 4.5 (401909869) | reject | 0.456 | 0.602 | -0.243 | win |
| ml | home (401909835) | reject | 0.480 | 0.636 | -0.245 | win |
| spread | home -10.5 (401909837) | reject | 0.389 | 0.519 | -0.250 | win |
| prop | Evan Mobley ast over 3.5 (401909869) | reject | 0.463 | 0.617 | -0.251 | loss |
| prop | Jaden McDaniels ast over 2.5 (401909869) | reject | 0.407 | 0.543 | -0.252 | win |
| prop | Jaylon Tyson reb over 4.5 (401909869) | reject | 0.344 | 0.461 | -0.253 | loss |
| prop | Joel Embiid reb over 8.5 (401909093) | reject | 0.419 | 0.562 | -0.254 | loss |
| prop | Matas Buzelis pts over 15.5 (401909870) | reject | 0.413 | 0.556 | -0.257 | loss |
| prop | Jaden McDaniels fg3m over 1.5 (401909869) | reject | 0.326 | 0.439 | -0.257 | win |
| prop | Jonathan Kuminga reb over 5.5 (401909869) | reject | 0.456 | 0.613 | -0.257 | win |
| prop | Bilal Coulibaly pts under 9.5 (401909868) | reject | 0.412 | 0.556 | -0.258 | win |
| spread | away -1.5 (401909090) | reject | 0.385 | 0.519 | -0.259 | win |
| prop | Jarrett Allen reb under 7.5 (401909093) | reject | 0.439 | 0.595 | -0.263 | win |
| prop | Justin Champagnie reb under 5.5 (401909868) | reject | 0.397 | 0.541 | -0.265 | win |
| total | over 220.5 (401909088) | reject | 0.383 | 0.524 | -0.269 | win |
| prop | LeBron James pts under 16.5 (401909093) | reject | 0.405 | 0.559 | -0.275 | loss |
| prop | Terrence Shannon Jr. reb over 2.5 (401909869) | reject | 0.405 | 0.562 | -0.279 | win |
| ml | away (401909842) | reject | 0.276 | 0.383 | -0.279 | loss |
| prop | Anfernee Simons fg3m over 2.5 (401909093) | reject | 0.465 | 0.649 | -0.285 | loss |
| prop | Jaylen Brown pts under 20.5 (401909093) | reject | 0.393 | 0.552 | -0.288 | loss |
| prop | Bilal Coulibaly reb under 3.5 (401909868) | reject | 0.441 | 0.621 | -0.290 | loss |
| total | over 233.5 (401909869) | reject | 0.370 | 0.522 | -0.290 | win |
| prop | Jaden McDaniels pts over 15.5 (401909869) | reject | 0.378 | 0.535 | -0.294 | loss |
| prop | Grayson Allen pts over 16.5 (401909868) | reject | 0.394 | 0.559 | -0.294 | loss |
| total | over 235.5 (401909094) | reject | 0.372 | 0.528 | -0.296 | loss |
| prop | Terrence Shannon Jr. pts under 8.5 (401909869) | reject | 0.397 | 0.565 | -0.296 | loss |
| prop | Naz Reid pts over 17.5 (401909868) | reject | 0.384 | 0.549 | -0.302 | win |
| prop | Shai Gilgeous-Alexander reb under 3.5 (401909094) | reject | 0.427 | 0.617 | -0.308 | win |
| prop | Josh Giddey ast over 8.5 (401909870) | reject | 0.410 | 0.595 | -0.311 | loss |
| prop | Anfernee Simons pts under 10.5 (401909093) | reject | 0.375 | 0.546 | -0.313 | win |
| total | over 221.5 (401909088) | reject | 0.362 | 0.535 | -0.322 | win |
| prop | VJ Edgecombe pts under 11.5 (401909093) | reject | 0.376 | 0.556 | -0.324 | win |
| total | over 236.5 (401909094) | reject | 0.352 | 0.526 | -0.332 | loss |
| spread | home -4.5 (401909835) | reject | 0.354 | 0.531 | -0.333 | win |
| prop | Jamal Murray ast under 5.5 (401909094) | reject | 0.387 | 0.581 | -0.335 | win |
| prop | Dennis Schroder pts over 14.5 (401909868) | reject | 0.364 | 0.556 | -0.345 | loss |
| prop | James Harden ast over 6.5 (401909093) | reject | 0.379 | 0.581 | -0.348 | loss |
| prop | Jonathan Kuminga ast over 2.5 (401909869) | reject | 0.405 | 0.621 | -0.348 | loss |
| prop | Naz Reid pts over 18.5 (401909868) | reject | 0.346 | 0.532 | -0.349 | loss |
| total | over 229.5 (401909090) | reject | 0.346 | 0.535 | -0.353 | loss |
| prop | Peyton Watson reb under 3.5 (401909869) | reject | 0.396 | 0.613 | -0.355 | loss |
| prop | Brandon Miller reb over 5.5 (401909868) | reject | 0.382 | 0.595 | -0.358 | win |
| prop | Alex Caruso reb under 2.5 (401909094) | reject | 0.321 | 0.503 | -0.361 | loss |
| total | over 230.5 (401909090) | reject | 0.326 | 0.512 | -0.363 | loss |
| ml | away (401909839) | reject | 0.385 | 0.606 | -0.365 | win |
| prop | Ajay Mitchell fg3m over 1.5 (401909094) | reject | 0.229 | 0.366 | -0.376 | loss |
| spread | away 4.5 (401909089) | reject | 0.322 | 0.519 | -0.381 | win |
| prop | Peyton Watson fg3m over 1.5 (401909869) | reject | 0.402 | 0.649 | -0.381 | loss |
| prop | Anthony Edwards pts over 27.5 (401909869) | reject | 0.330 | 0.535 | -0.383 | win |
| prop | Alex Sarr fg3m under 0.5 (401909868) | reject | 0.406 | 0.662 | -0.386 | win |
| total | over 230.5 (401909840) | reject | 0.314 | 0.512 | -0.387 | win |
| total | over 242.5 (401909838) | reject | 0.313 | 0.512 | -0.390 | loss |
| prop | Terrence Shannon Jr. fg3m over 1.5 (401909869) | reject | 0.397 | 0.667 | -0.405 | win |
| prop | James Harden ast over 6.5 (401909869) | reject | 0.329 | 0.556 | -0.407 | win |
| total | over 231.5 (401909090) | reject | 0.307 | 0.522 | -0.411 | loss |
| prop | Anfernee Simons pts under 9.5 (401909093) | reject | 0.320 | 0.552 | -0.420 | win |
| prop | Donovan Mitchell ast over 4.5 (401909869) | reject | 0.331 | 0.575 | -0.424 | win |
| prop | VJ Edgecombe pts under 10.5 (401909093) | reject | 0.325 | 0.568 | -0.428 | loss |
| spread | away -3.5 (401909839) | reject | 0.296 | 0.519 | -0.429 | loss |
| prop | Christian Braun ast under 1.5 (401909094) | reject | 0.346 | 0.610 | -0.432 | win |
| prop | Alex Caruso ast under 1.5 (401909094) | reject | 0.349 | 0.617 | -0.434 | loss |
| spread | home 1.5 (401909836) | reject | 0.296 | 0.528 | -0.439 | loss |
| prop | Anthony Edwards fg3m over 3.5 (401909869) | reject | 0.336 | 0.602 | -0.442 | win |
| ml | home (401909869) | reject | 0.353 | 0.635 | -0.445 | win |
| prop | LaMelo Ball pts over 19.5 (401909869) | reject | 0.298 | 0.538 | -0.445 | loss |
| prop | LaMelo Ball reb over 4.5 (401909869) | reject | 0.308 | 0.556 | -0.446 | loss |
| prop | Grayson Allen fg3m over 3.5 (401909868) | reject | 0.342 | 0.621 | -0.449 | loss |
| total | over 239.5 (401909839) | reject | 0.280 | 0.512 | -0.454 | win |
| prop | Alex Caruso pts under 6.5 (401909094) | reject | 0.303 | 0.556 | -0.455 | loss |
| prop | Kentavious Caldwell-Pope pts under 6.5 (401909093) | reject | 0.310 | 0.575 | -0.461 | win |
| total | over 239.5 (401909091) | reject | 0.280 | 0.524 | -0.465 | loss |
| ml | away (401909089) | reject | 0.212 | 0.397 | -0.465 | win |
| prop | Brandon Miller pts over 24.5 (401909868) | reject | 0.287 | 0.538 | -0.466 | win |
| ml | home (401909836) | reject | 0.268 | 0.505 | -0.469 | loss |
| total | over 236.5 (401909093) | reject | 0.274 | 0.526 | -0.479 | loss |
| total | over 233.5 (401909834) | reject | 0.268 | 0.535 | -0.499 | win |
| total | over 238.5 (401909835) | reject | 0.254 | 0.524 | -0.515 | win |
| total | over 237.5 (401909837) | reject | 0.253 | 0.528 | -0.521 | loss |
| total | over 232.5 (401909089) | reject | 0.243 | 0.512 | -0.525 | loss |
| total | over 233.5 (401909092) | reject | 0.246 | 0.524 | -0.530 | loss |
| spread | home -4.5 (401909869) | reject | 0.242 | 0.522 | -0.537 | loss |
| prop | Cason Wallace reb over 3.5 (401909094) | reject | 0.290 | 0.633 | -0.541 | loss |
| prop | Bilal Coulibaly fg3m over 1.5 (401909868) | reject | 0.316 | 0.690 | -0.541 | loss |
| prop | Kentavious Caldwell-Pope pts under 5.5 (401909093) | reject | 0.237 | 0.535 | -0.556 | win |
| total | over 231.5 (401909841) | reject | 0.224 | 0.519 | -0.568 | loss |
| spread | home -5.5 (401909869) | reject | 0.217 | 0.510 | -0.574 | loss |
| prop | Dennis Schroder ast over 6.5 (401909868) | reject | 0.225 | 0.602 | -0.626 | loss |
| prop | LaMelo Ball ast over 7.5 (401909869) | reject | 0.193 | 0.585 | -0.671 | loss |
| prop | Jaylon Tyson pts over 9.5 (401909093) | reject | 0.098 | 0.556 | -0.824 | loss |
