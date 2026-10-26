# Line shopping vs leave-one-out consensus

Generated 2026-10-20T02:33:39Z. One bet per game side at the book with the highest EV against the median de-vigged price of the other book families; flat 1 unit at that book's closing price. Legacy closing quotes are untimed, so a 'beatable' price may be a stale one.

| market | split | EV threshold | bets | ROI | 95% CI | t | mean EV |
|---|---|---|---|---|---|---|---|
| ml | explore | 0% | 3672 | +1.9% | -1.1% to +5.0% | +1.1 | +2.3% |
| ml | explore | 1% | 1682 | +5.6% | +0.3% to +11.2% | +1.9 | +4.5% |
| ml | explore | 2% | 923 | +7.8% | -1.5% to +17.5% | +1.7 | +7.1% |
| ml | explore | 3% | 571 | +14.8% | +3.5% to +27.3% | +2.3 | +9.9% |
| ml | explore | 5% **chosen** | 348 | +21.7% | +4.4% to +41.5% | +2.4 | +13.8% |
| ml | validate | 0% | 3350 | +0.9% | -2.2% to +3.7% | +0.6 | +2.8% |
| ml | validate | 1% | 2208 | +1.4% | -2.3% to +5.3% | +0.7 | +4.0% |
| ml | validate | 2% | 1422 | +1.8% | -3.5% to +6.5% | +0.7 | +5.4% |
| ml | validate | 3% | 867 | +4.7% | -2.3% to +11.2% | +1.4 | +7.3% |
| ml | validate | 5% **chosen** | 417 | +12.4% | +2.8% to +21.9% | +2.3 | +11.1% |
| ml | gate | | | | | | PASS {'threshold_chosen': True, 'validate_roi': True, 'validate_min_bets': True, 'validate_t': True} |
| spread | explore | 0% **chosen** | 275 | -1.2% | -12.7% to +10.8% | -0.2 | +1.1% |
| spread | explore | 1% | 119 | -5.2% | -23.8% to +12.4% | -0.6 | +2.4% |
| spread | explore | 2% | 57 | -10.6% | -36.7% to +16.7% | -0.8 | +3.7% |
| spread | explore | 3% | 31 | -0.4% | -40.0% to +37.7% | -0.0 | +4.9% |
| spread | explore | 5% | 10 | -40.8% | -100.0% to +20.3% | -1.4 | +7.8% |
| spread | validate | 0% **chosen** | 78 | -9.9% | -32.7% to +14.7% | -0.9 | +1.4% |
| spread | validate | 1% | 45 | +2.9% | -25.0% to +32.6% | +0.2 | +2.4% |
| spread | validate | 2% | 25 | +3.1% | -37.1% to +42.2% | +0.2 | +3.4% |
| spread | validate | 3% | 12 | +0.6% | -65.7% to +53.3% | +0.0 | +4.7% |
| spread | validate | 5% | 5 | -61.8% | -100.0% to +14.5% | -1.6 | +6.6% |
| spread | gate | | | | | | fail {'threshold_chosen': True, 'validate_roi': False, 'validate_min_bets': False, 'validate_t': False} |
| total | explore | 0% **chosen** | 190 | +1.5% | -13.2% to +16.5% | +0.2 | +1.4% |
| total | explore | 1% | 92 | -5.8% | -29.2% to +14.2% | -0.5 | +2.8% |
| total | explore | 2% | 40 | -2.3% | -32.4% to +31.5% | -0.1 | +5.0% |
| total | explore | 3% | 21 | -0.7% | -40.8% to +47.7% | -0.0 | +7.3% |
| total | explore | 5% | 12 | +25.9% | -44.1% to +95.6% | +0.8 | +10.0% |
| total | validate | 0% **chosen** | 74 | -15.1% | -37.0% to +8.7% | -1.3 | +1.3% |
| total | validate | 1% | 27 | -8.0% | -46.9% to +30.5% | -0.4 | +3.5% |
| total | validate | 2% | 13 | +28.8% | -35.2% to +78.2% | +1.0 | +6.1% |
| total | validate | 3% | 7 | +24.3% | -65.0% to +96.7% | +0.5 | +9.3% |
| total | validate | 5% | 5 | +32.8% | -61.8% to +124.0% | +0.6 | +11.8% |
| total | gate | | | | | | fail {'threshold_chosen': True, 'validate_roi': False, 'validate_min_bets': False, 'validate_t': False} |
