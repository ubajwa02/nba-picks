# Live diagnostics (2026-11-24T04:54:54Z)

- **ml**: 720 settled, calibration error 0.083, log loss 0.6085 (market 0.5856), Brier drift -0.0162
- **spread**: 792 settled, calibration error 0.065, log loss 0.7016 (market 0.6930), Brier drift -0.0058
- **total**: 791 settled, calibration error 0.057, log loss 0.6998 (market 0.6921), Brier drift +0.0069
- **prop**: 86894 settled, calibration error 0.024, log loss 0.4677 (market 0.6750), Brier drift +0.0222

## Findings
- overconfident (ml): live log loss is worse than the de-vigged market
- overconfident (spread): 62% of populated bins are more extreme than outcomes
- overconfident (spread): live log loss is worse than the de-vigged market
- overconfident (total): 86% of populated bins are more extreme than outcomes
- overconfident (total): live log loss is worse than the de-vigged market
- overconfident (prop): 100% of populated bins are more extreme than outcomes
- slow_adapt (prop): Brier worsened by 0.022 between halves

## Probation
- ml: calibration error 0.083
- spread: calibration error 0.065
