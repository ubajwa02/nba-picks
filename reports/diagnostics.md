# Live diagnostics (2026-11-26T15:04:34Z)

- **ml**: 761 settled, calibration error 0.076, log loss 0.6017 (market 0.5851), Brier drift -0.0133
- **spread**: 842 settled, calibration error 0.054, log loss 0.6960 (market 0.6932), Brier drift -0.0088
- **total**: 844 settled, calibration error 0.066, log loss 0.7043 (market 0.6921), Brier drift +0.0112
- **prop**: 89562 settled, calibration error 0.026, log loss 0.4752 (market 0.6750), Brier drift +0.0273

## Findings
- overconfident (ml): live log loss is worse than the de-vigged market
- overconfident (spread): live log loss is worse than the de-vigged market
- overconfident (total): 86% of populated bins are more extreme than outcomes
- overconfident (total): live log loss is worse than the de-vigged market
- slow_adapt (total): Brier worsened by 0.011 between halves
- overconfident (prop): 100% of populated bins are more extreme than outcomes
- slow_adapt (prop): Brier worsened by 0.027 between halves

## Probation
- ml: calibration error 0.076
- total: calibration error 0.066
