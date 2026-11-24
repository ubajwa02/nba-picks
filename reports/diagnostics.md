# Live diagnostics (2026-11-24T05:25:29Z)

- **ml**: 724 settled, calibration error 0.083, log loss 0.6058 (market 0.5835), Brier drift -0.0168
- **spread**: 797 settled, calibration error 0.062, log loss 0.6999 (market 0.6930), Brier drift -0.0071
- **total**: 797 settled, calibration error 0.061, log loss 0.7005 (market 0.6922), Brier drift +0.0074
- **prop**: 87107 settled, calibration error 0.025, log loss 0.4686 (market 0.6750), Brier drift +0.0226

## Findings
- overconfident (ml): live log loss is worse than the de-vigged market
- overconfident (spread): 62% of populated bins are more extreme than outcomes
- overconfident (spread): live log loss is worse than the de-vigged market
- overconfident (total): 86% of populated bins are more extreme than outcomes
- overconfident (total): live log loss is worse than the de-vigged market
- overconfident (prop): 100% of populated bins are more extreme than outcomes
- slow_adapt (prop): Brier worsened by 0.023 between halves

## Probation
- ml: calibration error 0.083
- spread: calibration error 0.062
- total: calibration error 0.061
