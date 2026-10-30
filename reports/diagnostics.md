# Live diagnostics (2026-10-30T15:19:23Z)

- **ml**: 146 settled, calibration error 0.202, log loss 0.6838 (market 0.5987), Brier drift +0.0396
- **spread**: 150 settled, calibration error 0.168, log loss 0.7392 (market 0.6927), Brier drift +0.0541
- **total**: 152 settled, calibration error 0.084, log loss 0.6723 (market 0.6904), Brier drift +0.0211
- **prop**: 15896 settled, calibration error 0.015, log loss 0.4262 (market 0.6612), Brier drift +0.0045

## Findings
- overconfident (ml): live log loss is worse than the de-vigged market
- slow_adapt (ml): Brier worsened by 0.040 between halves
- overconfident (spread): 67% of populated bins are more extreme than outcomes
- overconfident (spread): live log loss is worse than the de-vigged market
- slow_adapt (spread): Brier worsened by 0.054 between halves
- slow_adapt (total): Brier worsened by 0.021 between halves

## Probation
- ml: calibration error 0.202
- spread: calibration error 0.168
- total: calibration error 0.084
