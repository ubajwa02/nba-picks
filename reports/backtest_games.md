# Game-market backtest: 2023-02-01 to 2023-02-28 (validate)

Generated 2026-10-22T19:59:24Z at commit `e0bf9b9` by `python -m nbapicks.monthtest`.

Walk-forward: every game day each variant is refit on games strictly before that day and priced against the cleaned line of one book (DraftKings first, fixed priority list). A side is bet when EV >= the market's min_ev (config/nbapicks.yaml), flat 1u = $100. Log loss and Brier are one side per game (home/over) against the de-vigged price of the same book; 'gain vs mkt' = market minus model (positive = model better). 'raw' = model probability; 'blend' = logit blend with the market using the weight frozen in the research registry (not refit).

| variant | market | kind | pricing | games | bets | W-L-P | hit % | ROI | 95% CI | net $ | logloss model | logloss mkt | gain vs mkt | baseline | logloss baseline |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| trend | ml | close | raw | 163 | 115 | 45-70-0 | 39.1% | -6.8% | -30.1% to +17.4% | -781 | 0.6115 | 0.5861 | -0.0253 | de-vigged market (same book, same price kind) | 0.5861 |
| trend | ml | close | blend w=0.10 | 163 | 1 | 0-1-0 | 0.0% | -100.0% |  | -100 | 0.5864 | 0.5861 | -0.0003 | de-vigged market (same book, same price kind) | 0.5861 |
| trend | spread | close | raw | 161 | 109 | 58-49-2 | 54.2% | +3.6% | -14.2% to +20.9% | +388 | 0.7007 | 0.6927 | -0.0080 | de-vigged market (same book, same price kind) | 0.6927 |
| trend | spread | close | blend w=0.00 | 161 | 0 | 0-0-0 |  |  |  | +0 | 0.6927 | 0.6927 | +0.0000 | de-vigged market (same book, same price kind) | 0.6927 |
| trend | total | close | raw | 161 | 112 | 60-51-1 | 54.1% | +3.3% | -14.5% to +21.3% | +372 | 0.6894 | 0.6937 | +0.0043 | de-vigged market (same book, same price kind) | 0.6937 |
| trend | total | close | blend w=0.00 | 161 | 0 | 0-0-0 |  |  |  | +0 | 0.6937 | 0.6937 | +0.0000 | de-vigged market (same book, same price kind) | 0.6937 |
| avail | ml | close | raw | 163 | 110 | 45-65-0 | 40.9% | -4.8% | -27.8% to +19.9% | -530 | 0.6057 | 0.5861 | -0.0196 | trend (raw) | 0.6115 |
| avail | spread | close | raw | 161 | 107 | 58-47-2 | 55.2% | +5.4% | -11.6% to +23.9% | +576 | 0.6922 | 0.6927 | +0.0004 | trend (raw) | 0.7007 |
| avail | total | close | raw | 161 | 110 | 58-51-1 | 53.2% | +1.7% | -15.6% to +20.0% | +190 | 0.6913 | 0.6937 | +0.0024 | trend (raw) | 0.6894 |

## Coverage

- close: 163 games in the period, 163 with any close quote. Games with a clean quote: ml 163 (books {'DraftKings': 163}, model not ready 0); spread 163 (books {'DraftKings': 163}, model not ready 0); total 163 (books {'DraftKings': 163}, model not ready 0). Book-level quotes dropped by clean_quotes (all markets): {'impossible_line': 331, 'total_off_consensus': 14, 'spread_off_consensus': 13, 'ml_spread_mismatch': 2}.
- open: 163 games in the period, 0 with any open quote. Games with a clean quote: ml 0 (books none, model not ready 0); spread 0 (books none, model not ready 0); total 0 (books none, model not ready 0). Book-level quotes dropped by clean_quotes (all markets): none.
- availability feature ('avail'): known for 163 games, 0 for 0 (no box score or fewer than 5 earlier team games this season).
- nothing to score (no quotes of that kind): avail ml open, avail spread open, avail total open, trend ml open, trend spread open, trend total open.

## Notes

- Raw model probabilities (no blending with the market).
- Seasons up to 2022-23 carry one untimed final quote per book (flag final_quote_untimed), used as the closing line.
- ESPN BET 2022-23 puts the American price in the spread/total line field (e.g. spread -115.0); clean_quotes drops those as impossible lines (323 ESPN BET book-quotes in this period), and DraftKings is priced first in any case.
- Blend weight w=0.10 frozen from exp-20261020-trend (fit on explore seasons; not refit here).
- No opening lines in ESPN's history for this period (open + close exist from 2023-24); nothing to score.
- Blend weight w=0.00 frozen from exp-20261020-trend (fit on explore seasons; not refit here). w=0 makes the blend the de-vigged market, so no side can clear a positive EV threshold and bets are 0 by construction.
- Availability caveat: in backtests a regular counts as missing when he does not appear in that game's box score (known only after the game, includes late scratches), so backtest gains are an upper bound; live use relies on the pregame injury report (Out/Doubtful). A regular traded away also counts as missing for his old team in backtests.
- One month is a small sample: a few hundred sides per market. ROI intervals are wide and the log-loss differences are not tested for significance here; use the research runner for decisions.
