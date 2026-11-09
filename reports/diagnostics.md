# Live diagnostics (2026-11-09T22:48:39Z)

- **ml**: 449 settled, calibration error 0.080, log loss 0.5947 (market 0.5480), Brier drift -0.0631
- **spread**: 503 settled, calibration error 0.078, log loss 0.7043 (market 0.6932), Brier drift -0.0232
- **total**: 484 settled, calibration error 0.055, log loss 0.6929 (market 0.6920), Brier drift +0.0110
- **prop**: 60264 settled, calibration error 0.014, log loss 0.4444 (market 0.6729), Brier drift +0.0051

## Findings
- overconfident (ml): live log loss is worse than the de-vigged market
- overconfident (spread): 67% of populated bins are more extreme than outcomes
- overconfident (spread): live log loss is worse than the de-vigged market
- overconfident (total): 67% of populated bins are more extreme than outcomes
- overconfident (total): live log loss is worse than the de-vigged market
- slow_adapt (total): Brier worsened by 0.011 between halves
- overconfident (prop): 100% of populated bins are more extreme than outcomes

## Probation
- ml: calibration error 0.080
- spread: calibration error 0.078
