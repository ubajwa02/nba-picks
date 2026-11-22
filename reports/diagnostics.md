# Live diagnostics (2026-11-22T06:02:35Z)

- **ml**: 682 settled, calibration error 0.077, log loss 0.6063 (market 0.5759), Brier drift -0.0283
- **spread**: 745 settled, calibration error 0.077, log loss 0.7083 (market 0.6930), Brier drift -0.0039
- **total**: 736 settled, calibration error 0.049, log loss 0.6973 (market 0.6919), Brier drift +0.0082
- **prop**: 84301 settled, calibration error 0.023, log loss 0.4601 (market 0.6750), Brier drift +0.0170

## Findings
- overconfident (ml): live log loss is worse than the de-vigged market
- overconfident (spread): live log loss is worse than the de-vigged market
- overconfident (total): 86% of populated bins are more extreme than outcomes
- overconfident (total): live log loss is worse than the de-vigged market
- overconfident (prop): 100% of populated bins are more extreme than outcomes
- slow_adapt (prop): Brier worsened by 0.017 between halves

## Probation
- ml: calibration error 0.077
- spread: calibration error 0.077
