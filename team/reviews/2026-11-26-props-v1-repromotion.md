# Independent review, 2026-11-26: re-promote props-v1 as the prop estimator

Reviewer: a Claude session with no authorship of props-v1. Holdout (2026-02-01..2026-06-30) was not touched and nothing was tuned.

## Verdict: PASS as a probability estimator (market status stays research)

| check | result |
|---|---|
| Validate gain vs props-v0 reproduced (`propbacktest --start 2025-10-01 --end 2026-01-31`, no cache) | pts +0.0260 (t 5.5), reb +0.0271 (t 5.8), ast +0.0202 (t 4.2), fg3m +0.0223 (t 5.2). Matches the Nov 22 weekly report. Gate needs t >= 2. |
| Live calibration of props-v1, all 31,699 settled live predictions (2026-10-22..11-02) | error 0.0126 (gate 0.06); top decile predicted 0.928, observed 0.921. props-v0 live over 84,013 settled: error 0.0488, top decile predicted 0.949, observed 0.908. |
| Live head-to-head on the same props (748 matched) | v1 better by 0.012 log loss, naive t 1.3: not significant. reb +0.046, ast +0.021, pts +0.001, fg3m -0.011. Live evidence is weak, not negative. |
| Why it was demoted on Nov 2 | The 0.122 came from the last 150 settled rows, all created on one day (Nov 2, 137 rejects). A perfectly calibrated model scores a median 0.076 on 150 rows (5-95%: 0.044-0.105) with this 10-bin statistic, so the 0.06 gate trips on noise most of the time. It is not evidence the model is miscalibrated. |

## What this does NOT show
- Beating props-v0 is not beating the book. The Oct 22 skeptic review still stands: on real main lines props-v1 does not beat a coin flip for pts/reb/ast, and no prop stat has positive ROI at real prices. Market status stays research; no gate for paper/live is met.
- Model edge vs price has not predicted winners recently (-9.9% ROI at raw edge >= 4%, Nov 13-24, per the analysis thread). Promotion does not change that.

## Changes made
- champion.json props -> props-v1 via `python -m nbapicks.weekly --promote props-v1`.
- `forward_prop_check` now counts only predictions created on or after the model's `since` date, so a reinstated model is not demoted immediately on its old rows. Threshold (0.06) and window (150) are unchanged.

## Recommendation for Uday (gate change, not made here)
The demotion statistic is too noisy at n=150: v1 will probably be demoted again within a day or two of settled props even if well calibrated. Suggest a window of ~1,000 settled props across at least 5 days. That loosens a gate, so it needs a decision record and Uday's OK.
