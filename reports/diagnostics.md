# Live diagnostics (2026-11-24T15:32:34Z)

- **ml**: 727 settled, calibration error 0.081, log loss 0.6044 (market 0.5816), Brier drift -0.0180
- **spread**: 800 settled, calibration error 0.064, log loss 0.7009 (market 0.6930), Brier drift -0.0053
- **total**: 802 settled, calibration error 0.064, log loss 0.7017 (market 0.6921), Brier drift +0.0089
- **prop**: 87301 settled, calibration error 0.025, log loss 0.4690 (market 0.6750), Brier drift +0.0231

## Findings
- overconfident (ml): live log loss is worse than the de-vigged market
- overconfident (spread): 62% of populated bins are more extreme than outcomes
- overconfident (spread): live log loss is worse than the de-vigged market
- overconfident (total): 86% of populated bins are more extreme than outcomes
- overconfident (total): live log loss is worse than the de-vigged market
- overconfident (prop): 100% of populated bins are more extreme than outcomes
- slow_adapt (prop): Brier worsened by 0.023 between halves

## Probation
- ml: calibration error 0.081
- spread: calibration error 0.064
- total: calibration error 0.064
