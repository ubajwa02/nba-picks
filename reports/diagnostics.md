# Live diagnostics (2026-11-28T15:51:53Z)

- **ml**: 786 settled, calibration error 0.070, log loss 0.6047 (market 0.5866), Brier drift -0.0083
- **spread**: 869 settled, calibration error 0.061, log loss 0.6984 (market 0.6931), Brier drift -0.0101
- **total**: 871 settled, calibration error 0.071, log loss 0.7044 (market 0.6921), Brier drift +0.0134
- **prop**: 90907 settled, calibration error 0.026, log loss 0.4783 (market 0.6750), Brier drift +0.0289

## Findings
- overconfident (ml): live log loss is worse than the de-vigged market
- overconfident (spread): live log loss is worse than the de-vigged market
- overconfident (total): 86% of populated bins are more extreme than outcomes
- overconfident (total): live log loss is worse than the de-vigged market
- slow_adapt (total): Brier worsened by 0.013 between halves
- overconfident (prop): 100% of populated bins are more extreme than outcomes
- slow_adapt (prop): Brier worsened by 0.029 between halves

## Probation
- ml: calibration error 0.070
- spread: calibration error 0.061
- total: calibration error 0.071
