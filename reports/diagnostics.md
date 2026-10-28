# Live diagnostics (2026-10-28T10:44:03Z)

- **ml**: 80 settled, calibration error 0.123, log loss 0.6340 (market 0.5837), Brier drift -0.0099
- **spread**: 84 settled, calibration error 0.206, log loss 0.6983 (market 0.6914), Brier drift -0.0354
- **total**: 84 settled, calibration error 0.097, log loss 0.6739 (market 0.6916), Brier drift +0.0803
- **prop**: 8137 settled, calibration error 0.017, log loss 0.4221 (market 0.6635), Brier drift +0.0119

## Findings
- overconfident (ml): 71% of populated bins are more extreme than outcomes
- overconfident (ml): live log loss is worse than the de-vigged market
- overconfident (spread): 67% of populated bins are more extreme than outcomes
- overconfident (spread): live log loss is worse than the de-vigged market
- slow_adapt (total): Brier worsened by 0.080 between halves
- totals_bias (total): overs hit +9.3% vs predicted
- slow_adapt (prop): Brier worsened by 0.012 between halves

## Probation
- none
