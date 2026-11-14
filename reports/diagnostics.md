# Live diagnostics (2026-11-14T04:54:19Z)

- **ml**: 475 settled, calibration error 0.078, log loss 0.5909 (market 0.5509), Brier drift -0.0631
- **spread**: 529 settled, calibration error 0.079, log loss 0.7053 (market 0.6932), Brier drift -0.0187
- **total**: 508 settled, calibration error 0.049, log loss 0.6957 (market 0.6915), Brier drift +0.0145
- **prop**: 63614 settled, calibration error 0.014, log loss 0.4447 (market 0.6729), Brier drift +0.0071

## Findings
- overconfident (ml): live log loss is worse than the de-vigged market
- overconfident (spread): live log loss is worse than the de-vigged market
- overconfident (total): 67% of populated bins are more extreme than outcomes
- overconfident (total): live log loss is worse than the de-vigged market
- slow_adapt (total): Brier worsened by 0.014 between halves
- overconfident (prop): 100% of populated bins are more extreme than outcomes

## Probation
- ml: calibration error 0.078
- spread: calibration error 0.079
