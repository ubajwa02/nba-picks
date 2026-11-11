# Live diagnostics (2026-11-11T04:41:29Z)

- **ml**: 481 settled, calibration error 0.081, log loss 0.5889 (market 0.5491), Brier drift -0.0593
- **spread**: 535 settled, calibration error 0.080, log loss 0.7053 (market 0.6932), Brier drift -0.0196
- **total**: 514 settled, calibration error 0.047, log loss 0.6950 (market 0.6917), Brier drift +0.0125
- **prop**: 64624 settled, calibration error 0.014, log loss 0.4438 (market 0.6730), Brier drift +0.0063

## Findings
- overconfident (ml): live log loss is worse than the de-vigged market
- overconfident (spread): live log loss is worse than the de-vigged market
- overconfident (total): 67% of populated bins are more extreme than outcomes
- overconfident (total): live log loss is worse than the de-vigged market
- slow_adapt (total): Brier worsened by 0.012 between halves
- overconfident (prop): 100% of populated bins are more extreme than outcomes

## Probation
- ml: calibration error 0.081
- spread: calibration error 0.080
