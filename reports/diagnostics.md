# Live diagnostics (2026-11-06T14:40:57Z)

- **ml**: 341 settled, calibration error 0.097, log loss 0.6339 (market 0.5751), Brier drift -0.0472
- **spread**: 370 settled, calibration error 0.107, log loss 0.7125 (market 0.6935), Brier drift -0.0296
- **total**: 358 settled, calibration error 0.035, log loss 0.6875 (market 0.6925), Brier drift +0.0119
- **prop**: 45101 settled, calibration error 0.012, log loss 0.4422 (market 0.6755), Brier drift +0.0066

## Findings
- overconfident (ml): live log loss is worse than the de-vigged market
- overconfident (spread): 67% of populated bins are more extreme than outcomes
- overconfident (spread): live log loss is worse than the de-vigged market
- overconfident (total): 83% of populated bins are more extreme than outcomes
- slow_adapt (total): Brier worsened by 0.012 between halves
- overconfident (prop): 90% of populated bins are more extreme than outcomes

## Probation
- ml: calibration error 0.097
- spread: calibration error 0.107
