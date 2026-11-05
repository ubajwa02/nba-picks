# Live diagnostics (2026-11-05T15:00:04Z)

- **ml**: 328 settled, calibration error 0.099, log loss 0.6391 (market 0.5758), Brier drift -0.0444
- **spread**: 357 settled, calibration error 0.128, log loss 0.7153 (market 0.6932), Brier drift -0.0241
- **total**: 341 settled, calibration error 0.038, log loss 0.6786 (market 0.6924), Brier drift +0.0040
- **prop**: 43189 settled, calibration error 0.010, log loss 0.4409 (market 0.6760), Brier drift +0.0034

## Findings
- overconfident (ml): live log loss is worse than the de-vigged market
- overconfident (spread): 67% of populated bins are more extreme than outcomes
- overconfident (spread): live log loss is worse than the de-vigged market
- overconfident (total): 67% of populated bins are more extreme than outcomes
- overconfident (prop): 90% of populated bins are more extreme than outcomes

## Probation
- ml: calibration error 0.099
- spread: calibration error 0.128
