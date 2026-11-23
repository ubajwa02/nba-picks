# Live diagnostics (2026-11-23T15:35:36Z)

- **ml**: 697 settled, calibration error 0.080, log loss 0.6083 (market 0.5795), Brier drift -0.0218
- **spread**: 762 settled, calibration error 0.076, log loss 0.7083 (market 0.6930), Brier drift -0.0026
- **total**: 754 settled, calibration error 0.050, log loss 0.6987 (market 0.6920), Brier drift +0.0080
- **prop**: 85121 settled, calibration error 0.023, log loss 0.4626 (market 0.6750), Brier drift +0.0188

## Findings
- overconfident (ml): live log loss is worse than the de-vigged market
- overconfident (spread): 62% of populated bins are more extreme than outcomes
- overconfident (spread): live log loss is worse than the de-vigged market
- overconfident (total): 86% of populated bins are more extreme than outcomes
- overconfident (total): live log loss is worse than the de-vigged market
- overconfident (prop): 100% of populated bins are more extreme than outcomes
- slow_adapt (prop): Brier worsened by 0.019 between halves

## Probation
- ml: calibration error 0.080
- spread: calibration error 0.076
