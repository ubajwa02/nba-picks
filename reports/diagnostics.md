# Live diagnostics (2026-11-15T04:49:03Z)

- **ml**: 505 settled, calibration error 0.082, log loss 0.5991 (market 0.5735), Brier drift -0.0579
- **spread**: 562 settled, calibration error 0.079, log loss 0.6946 (market 0.6934), Brier drift -0.0219
- **total**: 546 settled, calibration error 0.042, log loss 0.6914 (market 0.6916), Brier drift +0.0124
- **prop**: 66796 settled, calibration error 0.016, log loss 0.4461 (market 0.6735), Brier drift +0.0066

## Findings
- overconfident (ml): live log loss is worse than the de-vigged market
- overconfident (spread): live log loss is worse than the de-vigged market
- overconfident (total): 67% of populated bins are more extreme than outcomes
- slow_adapt (total): Brier worsened by 0.012 between halves
- overconfident (prop): 100% of populated bins are more extreme than outcomes

## Probation
- ml: calibration error 0.082
- spread: calibration error 0.079
