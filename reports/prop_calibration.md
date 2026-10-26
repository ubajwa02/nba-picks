# exp-20261022-propcalib (NBA-034): prop calibrators, 2023 synthetic lines

Pre-registered c0ab114; run from clean commit e58e202. Explore (before 2023-01-15, n=36,336) fits; validate (n=46,792) scores. Holdout untouched.

| calibrator | validate log-loss | gain vs Platt | paired t | tail (raw<0.2/>0.8, n=5,392) mean abs err |
|---|---|---|---|---|
| identity (raw) | 0.65365 | -0.00629 | -15.5 | 0.084 |
| **Platt (production)** | **0.64736** | 0 | - | **0.038** |
| Platt tail-capped | 0.64736 | 0 | - | 0.038 |
| isotonic (PAV, 20 bins) | 0.64952 | -0.00216 | -8.0 | 0.045 |

**Decision: no candidate passes; keep Platt.** The "inflation" in NBA-034 is Platt (b=0.785) lifting small raw p toward 0.5, and on validate that lift is *correct*: raw p underpredicts the low tail (error 0.084 vs 0.038). The tail cap never fires, because Platt never moves p away from 0.5. Isotonic is significantly worse.

Caveats: synthetic lines yield few raw p < 0.06 (true +1600 longshots), so extreme-longshot behaviour is not tested. A market-blended (de-vigged implied) variant could not be tested because there are no historical prop prices. Configs counted: 4 (8 cumulative across prop calibration).
