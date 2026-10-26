# History line quality

Quotes dropped before any model is scored (rules in `nbapicks/backtest.py`, `clean_quotes`). Counts are book-level quotes, per season (ESPN year) and quote kind.

| season | kind | impossible_line | ml_off_consensus | ml_spread_mismatch | spread_off_consensus | total_off_consensus |
|---|---|---|---|---|---|---|
| 2015 | close | 0 | 1 | 0 | 9 | 3 |
| 2016 | close | 1 | 2 | 6 | 2 | 2 |
| 2017 | close | 0 | 10 | 9 | 12 | 2 |
| 2018 | close | 0 | 21 | 36 | 28 | 44 |
| 2019 | close | 0 | 24 | 34 | 25 | 131 |
| 2020 | close | 44 | 54 | 19 | 31 | 79 |
| 2021 | close | 29 | 5 | 4 | 43 | 14 |
| 2022 | close | 26 | 32 | 5 | 138 | 148 |
| 2023 | close | 2676 | 13 | 8 | 165 | 134 |
