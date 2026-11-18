# Live diagnostics (2026-11-18T04:57:26Z)

- **ml**: 612 settled, calibration error 0.090, log loss 0.5986 (market 0.5683), Brier drift -0.0423
- **spread**: 670 settled, calibration error 0.066, log loss 0.7016 (market 0.6931), Brier drift -0.0135
- **total**: 653 settled, calibration error 0.031, log loss 0.6921 (market 0.6918), Brier drift +0.0132
- **prop**: 80643 settled, calibration error 0.020, log loss 0.4481 (market 0.6750), Brier drift +0.0092

## Findings
- overconfident (ml): live log loss is worse than the de-vigged market
- overconfident (spread): live log loss is worse than the de-vigged market
- overconfident (total): 86% of populated bins are more extreme than outcomes
- overconfident (total): live log loss is worse than the de-vigged market
- slow_adapt (total): Brier worsened by 0.013 between halves
- overconfident (prop): 100% of populated bins are more extreme than outcomes

## Probation
- ml: calibration error 0.090
- spread: calibration error 0.066
