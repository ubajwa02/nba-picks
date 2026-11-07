# Live diagnostics (2026-11-07T17:54:36Z)

- **ml**: 379 settled, calibration error 0.089, log loss 0.6146 (market 0.5641), Brier drift -0.0687
- **spread**: 409 settled, calibration error 0.084, log loss 0.7035 (market 0.6936), Brier drift -0.0333
- **total**: 396 settled, calibration error 0.054, log loss 0.6928 (market 0.6921), Brier drift +0.0169
- **prop**: 50513 settled, calibration error 0.016, log loss 0.4462 (market 0.6761), Brier drift +0.0073

## Findings
- overconfident (ml): live log loss is worse than the de-vigged market
- overconfident (spread): 67% of populated bins are more extreme than outcomes
- overconfident (spread): live log loss is worse than the de-vigged market
- overconfident (total): 83% of populated bins are more extreme than outcomes
- overconfident (total): live log loss is worse than the de-vigged market
- slow_adapt (total): Brier worsened by 0.017 between halves
- overconfident (prop): 100% of populated bins are more extreme than outcomes

## Probation
- ml: calibration error 0.089
- spread: calibration error 0.084
