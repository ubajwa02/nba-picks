# Live diagnostics (2026-10-29T15:31:58Z)

- **ml**: 134 settled, calibration error 0.170, log loss 0.6635 (market 0.5652), Brier drift +0.0052
- **spread**: 137 settled, calibration error 0.188, log loss 0.7468 (market 0.6917), Brier drift +0.0718
- **total**: 138 settled, calibration error 0.061, log loss 0.6779 (market 0.6902), Brier drift +0.0321
- **prop**: 14221 settled, calibration error 0.016, log loss 0.4246 (market 0.6652), Brier drift +0.0078

## Findings
- overconfident (ml): live log loss is worse than the de-vigged market
- overconfident (spread): 67% of populated bins are more extreme than outcomes
- overconfident (spread): live log loss is worse than the de-vigged market
- slow_adapt (spread): Brier worsened by 0.072 between halves
- slow_adapt (total): Brier worsened by 0.032 between halves

## Probation
- ml: calibration error 0.170
- spread: calibration error 0.188
- total: calibration error 0.061
