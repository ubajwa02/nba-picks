# Live diagnostics (2026-11-08T13:56:11Z)

- **ml**: 418 settled, calibration error 0.093, log loss 0.6055 (market 0.5549), Brier drift -0.0568
- **spread**: 460 settled, calibration error 0.111, log loss 0.7143 (market 0.6933), Brier drift -0.0187
- **total**: 439 settled, calibration error 0.051, log loss 0.6907 (market 0.6919), Brier drift +0.0108
- **prop**: 55622 settled, calibration error 0.014, log loss 0.4449 (market 0.6726), Brier drift +0.0049

## Findings
- overconfident (ml): live log loss is worse than the de-vigged market
- overconfident (spread): 67% of populated bins are more extreme than outcomes
- overconfident (spread): live log loss is worse than the de-vigged market
- overconfident (total): 67% of populated bins are more extreme than outcomes
- slow_adapt (total): Brier worsened by 0.011 between halves
- overconfident (prop): 100% of populated bins are more extreme than outcomes

## Probation
- ml: calibration error 0.093
- spread: calibration error 0.111
