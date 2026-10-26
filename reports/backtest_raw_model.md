# Raw model against closing lines (explore seasons 2014-15 to 2019-20)

The base ratings model on its own (no market blend), flat 1 unit at the closing price, on every side whose model EV cleared the threshold. Lines were cleaned first (`reports/line_quality.md`); an earlier version of this table used uncleaned lines and is in git history.

| market | games | model log loss | market log loss | EV threshold | bets | win % | ROI | 95% CI |
|---|---|---|---|---|---|---|---|---|
| ml | 7414 | 0.6115 | 0.5898 | 0% | 6340 | 34.4% | -4.0% | -8.0% to +0.0% |
| ml | 7414 | 0.6115 | 0.5898 | 2% | 5798 | 33.1% | -3.5% | -7.9% to +0.7% |
| ml | 7414 | 0.6115 | 0.5898 | 3% | 5533 | 32.5% | -2.9% | -7.3% to +1.8% |
| ml | 7414 | 0.6115 | 0.5898 | 5% | 5096 | 31.3% | -2.8% | -7.5% to +2.3% |
| spread | 7337 | 0.7119 | 0.6928 | 0% | 5844 | 49.3% | -4.2% | -6.6% to -1.8% |
| spread | 7337 | 0.7119 | 0.6928 | 2% | 5147 | 49.6% | -3.7% | -6.3% to -1.1% |
| spread | 7337 | 0.7119 | 0.6928 | 3% | 4821 | 49.8% | -3.3% | -6.0% to -0.5% |
| spread | 7337 | 0.7119 | 0.6928 | 5% | 4213 | 49.5% | -3.7% | -6.4% to -0.8% |
| total | 7355 | 0.7104 | 0.6925 | 0% | 5628 | 48.2% | -6.1% | -8.4% to -3.6% |
| total | 7355 | 0.7104 | 0.6925 | 2% | 4936 | 48.2% | -5.9% | -8.7% to -3.4% |
| total | 7355 | 0.7104 | 0.6925 | 3% | 4601 | 48.1% | -6.2% | -9.0% to -3.5% |
| total | 7355 | 0.7104 | 0.6925 | 5% | 3991 | 47.9% | -6.6% | -9.6% to -3.6% |

Reading: on its own the model's probabilities are worse than the de-vigged close in every market, and betting its 'edges' at the close loses about the bookmaker's margin or more. The totals loss is partly a 2.6-point low bias in the base model, which the 'trend' variant removes.
