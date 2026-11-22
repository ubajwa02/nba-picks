# Live diagnostics (2026-11-22T04:46:18Z)

- **ml**: 680 settled, calibration error 0.080, log loss 0.6020 (market 0.5718), Brier drift -0.0322
- **spread**: 743 settled, calibration error 0.075, log loss 0.7081 (market 0.6930), Brier drift -0.0041
- **total**: 734 settled, calibration error 0.048, log loss 0.6971 (market 0.6919), Brier drift +0.0080
- **prop**: 84247 settled, calibration error 0.023, log loss 0.4600 (market 0.6750), Brier drift +0.0168

## Findings
- overconfident (ml): live log loss is worse than the de-vigged market
- overconfident (spread): live log loss is worse than the de-vigged market
- overconfident (total): 86% of populated bins are more extreme than outcomes
- overconfident (total): live log loss is worse than the de-vigged market
- overconfident (prop): 100% of populated bins are more extreme than outcomes
- slow_adapt (prop): Brier worsened by 0.017 between halves

## Probation
- ml: calibration error 0.080
- spread: calibration error 0.075
