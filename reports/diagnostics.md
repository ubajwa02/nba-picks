# Live diagnostics (2026-11-25T04:32:12Z)

- **ml**: 733 settled, calibration error 0.078, log loss 0.6025 (market 0.5811), Brier drift -0.0180
- **spread**: 812 settled, calibration error 0.066, log loss 0.7000 (market 0.6930), Brier drift -0.0049
- **total**: 808 settled, calibration error 0.068, log loss 0.7034 (market 0.6921), Brier drift +0.0105
- **prop**: 87736 settled, calibration error 0.025, log loss 0.4704 (market 0.6750), Brier drift +0.0248

## Findings
- overconfident (ml): live log loss is worse than the de-vigged market
- overconfident (spread): live log loss is worse than the de-vigged market
- overconfident (total): 86% of populated bins are more extreme than outcomes
- overconfident (total): live log loss is worse than the de-vigged market
- slow_adapt (total): Brier worsened by 0.010 between halves
- overconfident (prop): 100% of populated bins are more extreme than outcomes
- slow_adapt (prop): Brier worsened by 0.025 between halves

## Probation
- ml: calibration error 0.078
- spread: calibration error 0.066
- total: calibration error 0.068
