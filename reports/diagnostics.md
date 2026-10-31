# Live diagnostics (2026-10-31T14:43:39Z)

- **ml**: 182 settled, calibration error 0.232, log loss 0.6929 (market 0.6081), Brier drift +0.0612
- **spread**: 192 settled, calibration error 0.181, log loss 0.7439 (market 0.6926), Brier drift +0.0336
- **total**: 192 settled, calibration error 0.049, log loss 0.6756 (market 0.6912), Brier drift +0.0046
- **prop**: 21539 settled, calibration error 0.012, log loss 0.4355 (market 0.6701), Brier drift +0.0149

## Findings
- overconfident (ml): live log loss is worse than the de-vigged market
- slow_adapt (ml): Brier worsened by 0.061 between halves
- overconfident (spread): 83% of populated bins are more extreme than outcomes
- overconfident (spread): live log loss is worse than the de-vigged market
- slow_adapt (spread): Brier worsened by 0.034 between halves
- overconfident (total): 67% of populated bins are more extreme than outcomes
- overconfident (prop): 70% of populated bins are more extreme than outcomes
- slow_adapt (prop): Brier worsened by 0.015 between halves

## Probation
- ml: calibration error 0.232
- spread: calibration error 0.181
