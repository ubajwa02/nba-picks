# Live diagnostics (2026-11-13T16:27:01Z)

- **ml**: 514 settled, calibration error 0.087, log loss 0.5877 (market 0.5429), Brier drift -0.0613
- **spread**: 568 settled, calibration error 0.080, log loss 0.7096 (market 0.6930), Brier drift -0.0085
- **total**: 547 settled, calibration error 0.052, log loss 0.6959 (market 0.6916), Brier drift +0.0168
- **prop**: 69875 settled, calibration error 0.015, log loss 0.4419 (market 0.6734), Brier drift +0.0018

## Findings
- overconfident (ml): live log loss is worse than the de-vigged market
- overconfident (spread): live log loss is worse than the de-vigged market
- overconfident (total): 83% of populated bins are more extreme than outcomes
- overconfident (total): live log loss is worse than the de-vigged market
- slow_adapt (total): Brier worsened by 0.017 between halves
- overconfident (prop): 100% of populated bins are more extreme than outcomes

## Probation
- ml: calibration error 0.087
- spread: calibration error 0.080
