# Skeptic review, 2026-10-22: props-v1 (branch claude/project-thread-8rc2tc @ 2283bf5)

Independent reviewer: a Claude agent with a fresh context and no authorship of the code, asked to break two claims. No code or data was changed. Every number below was recomputed from `data/history/*` with the repo's own functions (`propbacktest.build_events`, `score`, `_bets`, `paired`, `make_runs`); the scratch scripts were not committed. `pytest`: 214 passed.

## Verdicts

| claim | verdict |
|---|---|
| **A**: props-v1 is a better probability estimator than props-v0 (validate, synthetic lines) | **PASS**, with the caveats below. It may replace props-v0 as the estimator in the daily pipeline while every prop market stays in research. |
| **B**: props-v1 has positive ROI on reb (+7.9%), ast (+5.0%) and fg3m (+23.6%) at real 2025-26 prices | **REJECT**. All of the profit, and more, comes from ESPN BET quotes whose two prices cannot be an over/under pair for the chosen line. If those quotes are dropped, ROI is reb -1.0%, ast -7.4%, pts -3.9% and fg3m +1.0%, and none of the four is distinguishable from losing. |

## Findings

| # | severity | finding |
|---|---|---|
| 1 | critical (B) | The "conservative pair" is not a lower bound on ESPN BET data. Many quotes are alt-line ladder rungs or unrelated price pairs (overround < 1), and they produce the whole ROI. |
| 2 | major (B) | The "closest to even" rule ranks quotes by \|1/p0 - 1/p1\|, so a pair of long shots counts as "even". |
| 3 | major (B) | On real main lines, props-v1 does worse than a constant 0.5 for pts, reb and ast, and it leans to the under. |
| 4 | minor (B) | `teammates_out` comes from the game's own box, but most of the chosen lines are opening lines. |
| 5 | info (B) | Of the real-price window's 12 model × stat ROIs, 3 positive ones were reported. Same-night bets are correlated. |
| 6 | info (A) | Checks that came back clean for A: point-in-time, fit and validate splits, ablations, cache, pipeline history depth. |
| 7 | info | The only clean two-way prices in validate are DraftKings, 2026-01-14..31: 11 games, too few to say anything. |

### 1. Critical (B): the "conservative pair" is not conservative on ESPN BET data

`propbacktest.prices` (nbapicks/propbacktest.py:172-180) prices both sides at `min(p0, p1)`. It calls this a lower bound. That holds only if (p0, p1) is a real two-way market on the chosen line, which needs 1/p0 + 1/p1 >= 1. Nothing checks this. `real_lines` (propbacktest.py:149-153) only requires both prices to be above 1.

What is in the data: every quote in the window is ESPN BET. DraftKings starts on 2026-01-14 (`props_2026.csv.gz`: ESPN BET covers 2025-10-21..2025-12-01, DraftKings 2026-01-14..2026-06-13). ESPN BET rows are often ladders of alt lines. The two prices on many of them cannot be an over/under pair:

- Overround 1/p0 + 1/p1 across all ESPN BET rows: 5th percentile 0.88, minimum 0.077. For DraftKings it is 1.061 to 1.073, as a real market should be.
- Examples of chosen lines that were bet:
  - Kevin Durant fg3m 6.5, 15.0 / 26.0. He made 0. The model bet under at 15.0 and won +14u.
  - Alperen Sengun reb 15.5, 21.0 / 15.0. Under at 15.0, +14u.
  - SGA ast 7.5, 15.0 / 17.0, +14u.
  - Game 401809243 (2025-10-21) alone supplies a dozen of these.
- Eligible rows (v1 and v0 both scored) with overround < 1.0: 244 of 2,480 for ast, 452 of 2,990 for fg3m, 265 of 3,487 for reb and 17 of 3,962 for pts.

Recomputed props-v1 bets (they reproduce the report exactly: reb 1,063 bets at +7.9%, ast 824 at +5.0%, fg3m 907 at +23.6%, pts 1,838 at -2.3%), split by quote overround:

| stat | overround < 0.95: bets, ROI, units | 0.95–1.0 | **1.03–1.10 (normal market)** | all with overround >= 1.0 |
|---|---|---|---|---|
| ast | 133, +67.1%, +89.2u | 65, 0.0% | **529, -9.6%, -50.8u** | 634, -7.1% |
| fg3m | 313, +62.8%, +196.6u | 110, +14.8% | **351, +4.3%, +15.2u** | 495, +0.5% |
| pts | 5, +628%, +31.4u | 11, -45.9% | **1,794, -4.3%** | 1,825, -3.7% |
| reb | 107, +72.3%, +77.4u | 98, +10.8% | **769, -0.8%** | 867, -0.8% |

Quotes with overround below 1 contribute about +390u. The three "positive" stats make +338.6u in total, so without those quotes the result is a loss.

The fg3m signature fits this. Unders at lines of 3.5 and above are 100% of bets there, at average prices of 2.46 to 15.0, with ROI from +59% to +1,400%. The average fg3m bet price is 2.05, which is impossible as the worse side of a vigged pair. Of the 24 fg3m bets on ESPN BET "current" quotes, the average price is 4.23, the hit rate 79% and the ROI +289%.

Clean re-run. I kept only plausible pairs (1.0 <= overround <= 1.15 and both prices in [1.3, 3.5]), with the same timing rule, and chose the main line by de-vigged probability closest to 0.5. The chosen line is unchanged for 19,893 of 19,961 keys. Results from `make_runs`, with a day-clustered bootstrap 95% CI over 2,000 resamples:

| stat | bets | ROI | day-bootstrap 95% | props-v0 ROI |
|---|---|---|---|---|
| pts | 1,836 | -3.9% | [-7.6%, -0.2%] | -3.9% |
| reb | 876 | -1.0% | [-6.2%, +4.0%] | -8.3% |
| ast | 644 | -7.4% | [-13.3%, -1.0%] | -8.1% |
| fg3m | 502 | +1.0% | [-5.7%, +7.7%] | -8.4% |

### 2. Major (B): the "closest to even" rule favours pairs of long shots

`real_lines` (propbacktest.py:159-161) breaks ties with `abs(1/p0 - 1/p1)`. That measures how different the two implied probabilities are, not how close either is to 0.5. A 15.0 / 26.0 pair (balance 0.028) beats a real 2.05 / 1.71 main line (balance 0.097).

Every "open" row gets the same rank, `when = "0000-open"` (propbacktest.py:142-143). So among the opening alt ladder, this rule decides which rung is used. It is how Durant's 6.5 rung was chosen over his real 1.5/3.5 lines.

Most chosen lines are "open" rows: 15,068 of 22,164 overall (12,498 ESPN BET and 2,570 DraftKings). Bets in this window: 3,656 of 4,632.

The "open" rows carry the same `source_updated_at` as the current rows. For ESPN BET the median is 333 minutes after tip, so the timing of the open quote itself cannot be checked. Accepting "open" as pregame by definition is reasonable for a genuine opening price. It is not reasonable when the row is a ladder rung with a mismatched pair.

### 3. Major (B): on real main lines props-v1 is worse than a coin flip for pts, reb and ast

On the clean lines, props-v1 log loss is:

| stat | log loss | ln 2 |
|---|---|---|
| pts | 0.7127 | 0.6931 |
| reb | 0.6969 | 0.6931 |
| ast | 0.7062 | 0.6931 |
| fg3m | 0.6824 | 0.6931 |

The report's own figures on the uncleaned lines are 0.708, 0.690, 0.696 and 0.681.

The model leans to the under against the book line. For pts its mean P(over) is 0.436 against 0.494 observed, and for ast 0.450 against 0.480. That is why 1,614 of 1,836 pts bets are unders. On synthetic lines the same model is calibrated in the large (pts Oct–Nov: predicted 0.453, observed 0.477), so the shortfall comes from the market's line carrying information the model lacks.

An estimator that loses to 0.5 at the book's line cannot have an edge at that line. A positive ROI should have been read as a red flag here, not as evidence.

### 4. Minor (B): box-derived `teammates_out` against opening lines

`build_events` (propbacktest.py:222-226) sets `mates_out` to key teammates absent from this game's box. That includes late scratches, which an opening line could not know about.

On clean lines, bets with a teammate out do better than bets without:

| stat | with a teammate out | without |
|---|---|---|
| pts | -0.9% (721 bets) | -5.8% (1,115 bets) |
| ast | -0.8% (261 bets) | -11.9% (383 bets) |

That fits a small information advantage that would not exist live. It does not change the verdict, because the clean ROI is not positive anyway.

### 5. Info (B): multiple comparisons and clustering

The real-price window shows 12 model × stat ROIs (3 models × 4 stats), and the 3 positive props-v1 ones were reported.

The reported `roi_ci` treats bets as independent. Several players and stats on one night share game script. For B I used a day-clustered bootstrap, shown in finding 1.

Pushes: there are no integer lines in the window, so pushes play no part.

### 6. Info (A): what I tried against claim A, and what held

- **Point-in-time.** I built `PropModelV1` only from rows before D, for 4 random validate days and 60 events each. The predicted means are identical to the full-history model: max |diff| = 0. The `searchsorted(..., side="left")` cuts in props_v1.py:223, 242, 249 and 228 behave as documented.
- **Fit/validate separation.** `reports/props_v1_fit.json` has `explore_end` 2025-06-30. `fit()` truncates rows before building the model (propbacktest.py:485). There is no overlap with validate (2025-10-01..).
- **Cache.** Inputs under 1 MB, which is all box, games and props files plus the code, are content-hashed (cache.py:31-34). Parameters and dispersion are part of the key (propbacktest.py:451-452). I found no way for a stale entry to be reused after a change.
- **Ablations.** On validate with synthetic lines, I compared variants to props-v0 using the log-loss gain and the day-clustered t:

| stat | props-v1 as run | without `teammates_out` | without `teammates_out` and opponent |
|---|---|---|---|
| pts | +0.0217 (t 7.8) | +0.0196 (t 7.3) | +0.0189 (t 7.2) |
| reb | +0.0246 | +0.0242 | +0.0232 |
| ast | +0.0243 | +0.0232 | +0.0224 |
| fg3m | +0.0542 | +0.0543 | +0.0534 |

  The gain comes from the minutes and rate model, not from box-derived absences. On events with no teammate out, it is +0.022 to +0.044 with t >= 3.8.
- **Pipeline history depth.** The pipeline loads only the last two box seasons (pipeline.py:276); the backtest used four. Rebuilt on 2025–2026 only, the model is 0.0001 to 0.0005 worse in log loss (t up to -2.2, a trivial size) and still beats props-v0 by +0.021 to +0.054 (t 6 to 11).
- **On real lines** (finding 3) the gain over props-v0 holds too: +0.021 to +0.030, t 4.1 to 5.9.

Caveats on A:

- props-v0 is a weak baseline. For fg3m it loses to the naive hit rate by 0.041.
- Synthetic median lines are easier than book lines.
- The pts upper tail is overconfident: p > 0.8 is predicted at 0.84–0.93 against 0.73–0.79 observed, as the authors already noted.
- In the pipeline, Doubtful players are treated as out (pipeline.py:448), which the backtest proxy did not test.

None of these makes props-v1 a worse estimator than props-v0. They do mean A says nothing about beating a book.

### 7. Info: the DraftKings window

The only clean two-way prices in validate are DraftKings, 2026-01-14..31: 11 games, 11 to 61 props-v1 bets per stat. Log-loss gains over props-v0 have t from -0.5 to 1.8. This says nothing either way.

## What would change the verdicts

**A.** Evidence that features use same-game or later data in a way the tests above missed. A pipeline configuration that differs materially from the validated one, for example different parameters in `champion.json` from `PARAMS`/`DISPERSION`. Or a holdout run (when the team chooses to spend it) where props-v1 does not beat props-v0.

**B.** A re-run that:

1. rejects any quote that is not a plausible two-way pair for its line (overround within about [1.0, 1.15]);
2. chooses the main line by de-vigged probability nearest 0.5, or uses the book's main-line flag if the backfill can store it;
3. shows props-v1 ROI > 0 with >= 150 bets per stat and a day-clustered interval excluding 0;
4. ideally uses DraftKings or other labelled-side prices, timestamped pregame and not "open" alt ladders;
5. ideally uses a pregame injury snapshot instead of box absence.

On this window, the clean-pair version already answers it: no stat clears 0 by a margin, and pts and ast lose significantly. `propbacktest.real_lines` and `prices` should get the pair-plausibility check before any further real-price report is written.

## Follow-up applied (2026-10-22, same day)

- `propsides.plausible_pair` (implied probabilities of the two prices must add to 0.99..1.20) now gates `propbacktest.real_lines` and the live DraftKings pairs in `pipeline.predict` (implausible pairs are counted in `side_check.pairs_implausible` and not priced).
- Main-line choice now picks the pair whose de-vigged price is nearest 50/50.
- Real-price rerun, 2025-10-21..2025-11-30, props-v1 at EV >= 5%, conservative pricing: pts -4.0% (1837 bets), reb -0.7% (896), ast -8.4% (661), fg3m -0.1% (522). Claim B stays rejected: no prop shows a profit at real prices.
- Claim A: props-v1 promoted as the prop probability estimator through `weekly --promote` (exp-20261022-prop-props-v1: paired log-loss gain over props-v0 on validate, conservative t 3.7-5.8 per stat). Prop market status stays research.
