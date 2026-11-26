# Live diagnostics (2026-11-26T04:54:04Z)

- **ml**: 755 settled, calibration error 0.080, log loss 0.6021 (market 0.5850), Brier drift -0.0145
- **spread**: 836 settled, calibration error 0.058, log loss 0.6968 (market 0.6932), Brier drift -0.0081
- **total**: 837 settled, calibration error 0.068, log loss 0.7053 (market 0.6921), Brier drift +0.0119
- **prop**: 89300 settled, calibration error 0.026, log loss 0.4745 (market 0.6750), Brier drift +0.0269

## Findings
- overconfident (ml): live log loss is worse than the de-vigged market
- overconfident (spread): live log loss is worse than the de-vigged market
- overconfident (total): 86% of populated bins are more extreme than outcomes
- overconfident (total): live log loss is worse than the de-vigged market
- slow_adapt (total): Brier worsened by 0.012 between halves
- overconfident (prop): 100% of populated bins are more extreme than outcomes
- slow_adapt (prop): Brier worsened by 0.027 between halves

## Probation
- ml: calibration error 0.080
- total: calibration error 0.068
