# Live diagnostics (2026-11-16T04:33:10Z)

- **ml**: 527 settled, calibration error 0.080, log loss 0.5867 (market 0.5617), Brier drift -0.0626
- **spread**: 585 settled, calibration error 0.067, log loss 0.6922 (market 0.6931), Brier drift -0.0244
- **total**: 569 settled, calibration error 0.035, log loss 0.6912 (market 0.6916), Brier drift +0.0120
- **prop**: 69789 settled, calibration error 0.017, log loss 0.4462 (market 0.6739), Brier drift +0.0054

## Findings
- overconfident (ml): live log loss is worse than the de-vigged market
- overconfident (total): 83% of populated bins are more extreme than outcomes
- slow_adapt (total): Brier worsened by 0.012 between halves
- overconfident (prop): 100% of populated bins are more extreme than outcomes

## Probation
- ml: calibration error 0.080
- spread: calibration error 0.067
