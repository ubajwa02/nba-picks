# DraftKings prop sides: is the first price listed the Over?

Written by `nbapicks/sideorder.py` after every settle. How the rule works and what it replaced: `docs/SIDE_ORDER.md`.

**Status: confirmed** through 2026-11-16 (slope +1.05 (se 0.10) on 8,152 graded pairs over 24 slates).

The slope is how fast "went over" rises with the first-listed side's fair chance on graded closing pairs. 1 means the first price is the Over, 0 means the order says nothing, -1 means it is the Under.

| last slates | from | to | pairs | slope | se | verdict |
|---|---|---|---|---|---|---|
| 1 | 2026-11-16 | 2026-11-16 | 392 | +1.72 | 0.57 | ok |
| 3 | 2026-11-14 | 2026-11-16 | 1,016 | +1.34 | 0.31 | ok |
| 10 | 2026-11-07 | 2026-11-16 | 3,292 | +1.13 | 0.16 | ok |
| 24 | 2026-10-20 | 2026-11-16 | 8,152 | +1.05 | 0.10 | ok |

Fail: slope + 3 se < 0.75 on >= 100 pairs. Confirm: slope - 3 se > 0 on >= 300 pairs. Only the last 60 days of results count.

## By week

| week | slates | pairs | slope | se |
|---|---|---|---|---|
| 2026-W43 | 3 | 805 | +1.10 | 0.31 |
| 2026-W44 | 7 | 2,184 | +1.10 | 0.19 |
| 2026-W45 | 6 | 2,503 | +0.93 | 0.18 |
| 2026-W46 | 7 | 2,268 | +0.97 | 0.19 |
| 2026-W47 | 1 | 392 | +1.72 | 0.57 |
