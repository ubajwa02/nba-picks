# Live diagnostics (2026-11-25T08:05:31Z)

- **ml**: 736 settled, calibration error 0.075, log loss 0.6044 (market 0.5840), Brier drift -0.0157
- **spread**: 814 settled, calibration error 0.065, log loss 0.6996 (market 0.6930), Brier drift -0.0046
- **total**: 810 settled, calibration error 0.067, log loss 0.7031 (market 0.6921), Brier drift +0.0103
- **prop**: 87987 settled, calibration error 0.025, log loss 0.4709 (market 0.6750), Brier drift +0.0248

## Findings
- overconfident (ml): live log loss is worse than the de-vigged market
- overconfident (spread): live log loss is worse than the de-vigged market
- overconfident (total): 86% of populated bins are more extreme than outcomes
- overconfident (total): live log loss is worse than the de-vigged market
- slow_adapt (total): Brier worsened by 0.010 between halves
- overconfident (prop): 100% of populated bins are more extreme than outcomes
- slow_adapt (prop): Brier worsened by 0.025 between halves

## Probation
- ml: calibration error 0.075
- spread: calibration error 0.065
- total: calibration error 0.067
