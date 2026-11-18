# Live diagnostics (2026-11-18T14:29:55Z)

- **ml**: 617 settled, calibration error 0.092, log loss 0.5986 (market 0.5689), Brier drift -0.0414
- **spread**: 675 settled, calibration error 0.068, log loss 0.7039 (market 0.6931), Brier drift -0.0108
- **total**: 659 settled, calibration error 0.031, log loss 0.6923 (market 0.6919), Brier drift +0.0145
- **prop**: 80900 settled, calibration error 0.020, log loss 0.4492 (market 0.6750), Brier drift +0.0101

## Findings
- overconfident (ml): live log loss is worse than the de-vigged market
- overconfident (spread): live log loss is worse than the de-vigged market
- overconfident (total): 86% of populated bins are more extreme than outcomes
- overconfident (total): live log loss is worse than the de-vigged market
- slow_adapt (total): Brier worsened by 0.015 between halves
- overconfident (prop): 100% of populated bins are more extreme than outcomes
- slow_adapt (prop): Brier worsened by 0.010 between halves

## Probation
- ml: calibration error 0.092
- spread: calibration error 0.068
