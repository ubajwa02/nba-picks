# Line shopping, cleaned re-spec (moneylines)

`python -m tools.lineshop_respec`. Explore 2015-2020 and validate 2021-2023 only; holdout not loaded. Threshold chosen on explore: 3%. Validate t must reach 2.38 (noise floor over 17 registry experiments).

| scope | split | EV threshold | bets | ROI | 95% CI | t | mean EV |
|---|---|---|---|---|---|---|---|
| all | explore | 0% | 1855 | +0.7% | -3.3% to +4.8% | +0.4 | +1.1% |
| all | explore | 1% | 737 | +5.5% | -1.5% to +11.7% | +1.6 | +2.3% |
| all | explore | 2% | 340 | +8.6% | -2.9% to +19.3% | +1.5 | +3.3% |
| all | explore | 3% **chosen** | 144 | +18.4% | +0.7% to +36.0% | +2.0 | +4.4% |
| all | explore | 5% | 33 | +43.5% | -0.3% to +82.3% | +2.0 | +6.6% |
| all | validate | 0% | 1246 | +1.4% | -2.9% to +6.1% | +0.6 | +1.3% |
| all | validate | 1% | 611 | +4.5% | -1.8% to +10.6% | +1.3 | +2.3% |
| all | validate | 2% | 282 | +5.8% | -4.2% to +15.4% | +1.1 | +3.2% |
| all | validate | 3% **chosen** | 106 | +1.1% | -14.9% to +16.1% | +0.1 | +4.4% |
| all | validate | 5% | 23 | +4.2% | -38.2% to +47.3% | +0.2 | +7.0% |
| all | gate | | | | | | fail {'threshold_chosen': True, 'validate_roi': True, 'validate_min_bets': False, 'validate_t': False} |
| fd_like | explore | 0% | 0 |  |  |  |  |
| fd_like | explore | 1% | 0 |  |  |  |  |
| fd_like | explore | 2% | 0 |  |  |  |  |
| fd_like | explore | 3% **chosen** | 0 |  |  |  |  |
| fd_like | explore | 5% | 0 |  |  |  |  |
| fd_like | validate | 0% | 57 | +2.8% | -23.5% to +26.7% | +0.2 | +1.0% |
| fd_like | validate | 1% | 21 | -5.5% | -40.2% to +31.5% | -0.3 | +2.2% |
| fd_like | validate | 2% | 8 | -42.7% | -83.9% to +13.2% | -1.5 | +3.3% |
| fd_like | validate | 3% **chosen** | 5 | -62.0% | -100.0% to +14.1% | -1.6 | +3.9% |
| fd_like | validate | 5% | 1 | -100.0% |  |  | +6.0% |
| fd_like | gate | | | | | | fail {'threshold_chosen': True, 'validate_roi': False, 'validate_min_bets': False, 'validate_t': False} |
