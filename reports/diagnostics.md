# Live diagnostics (2026-10-27T18:29:09Z)

- **ml**: 70 settled, calibration error 0.119, log loss 0.6539 (market 0.6023), Brier drift -0.0236
- **spread**: 72 settled, calibration error 0.199, log loss 0.6714 (market 0.6899), Brier drift -0.0607
- **total**: 72 settled, calibration error 0.045, log loss 0.6518 (market 0.6905), Brier drift +0.0276
- **prop**: 5869 settled, calibration error 0.030, log loss 0.4155 (market 0.6641), Brier drift +0.0044

## Findings
- overconfident (ml): live log loss is worse than the de-vigged market
- overconfident (spread): 67% of populated bins are more extreme than outcomes
- slow_adapt (total): Brier worsened by 0.028 between halves
- totals_bias (total): overs hit +4.0% vs predicted

## Probation
- none
