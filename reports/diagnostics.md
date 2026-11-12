# Live diagnostics (2026-11-12T04:41:39Z)

- **ml**: 503 settled, calibration error 0.086, log loss 0.5899 (market 0.5467), Brier drift -0.0633
- **spread**: 557 settled, calibration error 0.079, log loss 0.7067 (market 0.6930), Brier drift -0.0125
- **total**: 536 settled, calibration error 0.047, log loss 0.6950 (market 0.6915), Brier drift +0.0143
- **prop**: 68144 settled, calibration error 0.014, log loss 0.4417 (market 0.6728), Brier drift +0.0032

## Findings
- overconfident (ml): live log loss is worse than the de-vigged market
- overconfident (spread): live log loss is worse than the de-vigged market
- overconfident (total): 83% of populated bins are more extreme than outcomes
- overconfident (total): live log loss is worse than the de-vigged market
- slow_adapt (total): Brier worsened by 0.014 between halves
- overconfident (prop): 100% of populated bins are more extreme than outcomes

## Probation
- ml: calibration error 0.086
- spread: calibration error 0.079
