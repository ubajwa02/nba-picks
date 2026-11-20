# Live diagnostics (2026-11-20T14:42:03Z)

- **ml**: 653 settled, calibration error 0.086, log loss 0.6076 (market 0.5779), Brier drift -0.0322
- **spread**: 713 settled, calibration error 0.073, log loss 0.7069 (market 0.6931), Brier drift -0.0092
- **total**: 703 settled, calibration error 0.037, log loss 0.6938 (market 0.6919), Brier drift +0.0092
- **prop**: 82792 settled, calibration error 0.022, log loss 0.4555 (market 0.6750), Brier drift +0.0147

## Findings
- overconfident (ml): live log loss is worse than the de-vigged market
- overconfident (spread): live log loss is worse than the de-vigged market
- overconfident (total): 86% of populated bins are more extreme than outcomes
- overconfident (total): live log loss is worse than the de-vigged market
- overconfident (prop): 100% of populated bins are more extreme than outcomes
- slow_adapt (prop): Brier worsened by 0.015 between halves

## Probation
- ml: calibration error 0.086
- spread: calibration error 0.073
