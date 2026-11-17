# Live diagnostics (2026-11-17T14:28:13Z)

- **ml**: 548 settled, calibration error 0.075, log loss 0.5976 (market 0.5713), Brier drift -0.0531
- **spread**: 606 settled, calibration error 0.071, log loss 0.6952 (market 0.6931), Brier drift -0.0244
- **total**: 588 settled, calibration error 0.029, log loss 0.6911 (market 0.6916), Brier drift +0.0152
- **prop**: 70894 settled, calibration error 0.018, log loss 0.4505 (market 0.6739), Brier drift +0.0089

## Findings
- overconfident (ml): live log loss is worse than the de-vigged market
- overconfident (spread): live log loss is worse than the de-vigged market
- overconfident (total): 86% of populated bins are more extreme than outcomes
- slow_adapt (total): Brier worsened by 0.015 between halves
- overconfident (prop): 100% of populated bins are more extreme than outcomes

## Probation
- ml: calibration error 0.075
- spread: calibration error 0.071
