# Live diagnostics (2026-11-03T19:54:04Z)

- **ml**: 282 settled, calibration error 0.123, log loss 0.6449 (market 0.5826), Brier drift -0.0174
- **spread**: 297 settled, calibration error 0.152, log loss 0.7175 (market 0.6932), Brier drift -0.0214
- **total**: 294 settled, calibration error 0.047, log loss 0.6754 (market 0.6922), Brier drift -0.0006
- **prop**: 34924 settled, calibration error 0.008, log loss 0.4390 (market 0.6754), Brier drift +0.0103

## Findings
- overconfident (ml): live log loss is worse than the de-vigged market
- overconfident (spread): 83% of populated bins are more extreme than outcomes
- overconfident (spread): live log loss is worse than the de-vigged market
- overconfident (total): 67% of populated bins are more extreme than outcomes
- overconfident (prop): 70% of populated bins are more extreme than outcomes
- slow_adapt (prop): Brier worsened by 0.010 between halves

## Probation
- ml: calibration error 0.123
- spread: calibration error 0.152
