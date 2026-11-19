# Live diagnostics (2026-11-19T14:10:08Z)

- **ml**: 647 settled, calibration error 0.086, log loss 0.6096 (market 0.5802), Brier drift -0.0315
- **spread**: 707 settled, calibration error 0.071, log loss 0.7060 (market 0.6930), Brier drift -0.0125
- **total**: 695 settled, calibration error 0.037, log loss 0.6932 (market 0.6919), Brier drift +0.0107
- **prop**: 82462 settled, calibration error 0.022, log loss 0.4543 (market 0.6750), Brier drift +0.0139

## Findings
- overconfident (ml): live log loss is worse than the de-vigged market
- overconfident (spread): live log loss is worse than the de-vigged market
- overconfident (total): 86% of populated bins are more extreme than outcomes
- overconfident (total): live log loss is worse than the de-vigged market
- slow_adapt (total): Brier worsened by 0.011 between halves
- overconfident (prop): 100% of populated bins are more extreme than outcomes
- slow_adapt (prop): Brier worsened by 0.014 between halves

## Probation
- ml: calibration error 0.086
- spread: calibration error 0.071
