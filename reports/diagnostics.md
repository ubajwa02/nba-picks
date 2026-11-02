# Live diagnostics (2026-11-02T16:38:04Z)

- **ml**: 227 settled, calibration error 0.177, log loss 0.6643 (market 0.5852), Brier drift +0.0248
- **spread**: 240 settled, calibration error 0.191, log loss 0.7339 (market 0.6934), Brier drift -0.0046
- **total**: 239 settled, calibration error 0.064, log loss 0.6829 (market 0.6918), Brier drift +0.0089
- **prop**: 27369 settled, calibration error 0.010, log loss 0.4386 (market 0.6741), Brier drift +0.0129

## Findings
- overconfident (ml): live log loss is worse than the de-vigged market
- slow_adapt (ml): Brier worsened by 0.025 between halves
- overconfident (spread): 83% of populated bins are more extreme than outcomes
- overconfident (spread): live log loss is worse than the de-vigged market
- overconfident (total): 67% of populated bins are more extreme than outcomes
- totals_bias (total): overs hit +4.2% vs predicted
- overconfident (prop): 70% of populated bins are more extreme than outcomes
- slow_adapt (prop): Brier worsened by 0.013 between halves

## Probation
- ml: calibration error 0.177
- spread: calibration error 0.191
- total: calibration error 0.064
