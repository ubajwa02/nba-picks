# Live diagnostics (2026-11-10T04:40:55Z)

- **ml**: 473 settled, calibration error 0.077, log loss 0.5918 (market 0.5524), Brier drift -0.0640
- **spread**: 527 settled, calibration error 0.076, log loss 0.7039 (market 0.6933), Brier drift -0.0211
- **total**: 506 settled, calibration error 0.047, log loss 0.6941 (market 0.6916), Brier drift +0.0132
- **prop**: 63098 settled, calibration error 0.014, log loss 0.4449 (market 0.6726), Brier drift +0.0070

## Findings
- overconfident (ml): live log loss is worse than the de-vigged market
- overconfident (spread): live log loss is worse than the de-vigged market
- overconfident (total): 67% of populated bins are more extreme than outcomes
- overconfident (total): live log loss is worse than the de-vigged market
- slow_adapt (total): Brier worsened by 0.013 between halves
- overconfident (prop): 100% of populated bins are more extreme than outcomes

## Probation
- ml: calibration error 0.077
- spread: calibration error 0.076
