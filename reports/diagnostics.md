# Live diagnostics (2026-11-01T13:52:32Z)

- **ml**: 210 settled, calibration error 0.202, log loss 0.6638 (market 0.5843), Brier drift +0.0068
- **spread**: 220 settled, calibration error 0.178, log loss 0.7295 (market 0.6927), Brier drift -0.0140
- **total**: 219 settled, calibration error 0.054, log loss 0.6794 (market 0.6918), Brier drift +0.0011
- **prop**: 24778 settled, calibration error 0.010, log loss 0.4363 (market 0.6726), Brier drift +0.0113

## Findings
- overconfident (ml): live log loss is worse than the de-vigged market
- overconfident (spread): 83% of populated bins are more extreme than outcomes
- overconfident (spread): live log loss is worse than the de-vigged market
- overconfident (total): 67% of populated bins are more extreme than outcomes
- overconfident (prop): 70% of populated bins are more extreme than outcomes
- slow_adapt (prop): Brier worsened by 0.011 between halves

## Probation
- ml: calibration error 0.202
- spread: calibration error 0.178
