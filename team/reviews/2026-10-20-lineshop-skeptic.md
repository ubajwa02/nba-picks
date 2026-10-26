# Independent review: line-shop moneyline "edge" (exp-20261020-lineshop)

Reviewer: independent skeptic (did not write the code). Data used: explore (2015-2020) and validate (2021-2023) only, from a scratch copy containing only `games_/odds_2014..2023` (the loader was asserted to see no season >= 2024). For the holdout I looked only at metadata (book names, `kind`, `flags` columns of `odds_2024..2026`): no prices, no games files, no results.

Reproduction: the scratch run gives the report's numbers exactly: explore 348 bets, ROI +21.7%, t 2.36; validate 417 bets, ROI +12.4%, t 2.30.

## Verdict: REJECT

Do not spend the holdout on this specification, for four reasons.

1. The money comes from quotes that show signs of data errors or non-simultaneous capture. Examples: zero-vig MGM pairs; a "Caesars Sportsbook" price that disagrees with the same operator's other feeds; MLs that disagree with the same book's own spread.
2. The validate p-value does not survive correction for the roughly 26 validate tests in the registry.
3. The strategy cannot be run by this user. FanDuel is the only account, and a FanDuel-like book is almost never the outlier.
4. The holdout as specified is effectively 2024 alone. 2025 has one book and 2026 has two, so MIN_FAMILIES = 3 yields zero bets in those seasons. 2024 gives only about 100 bets, too few to confirm or refute a realistic edge.

A narrower re-spec could still be worth testing, but only as a new experiment run on explore and validate first (see "Path forward").

## Findings

### 1. The result is real relative to the recorded quotes, so the question is whether those quotes were bettable
- On the 5% bets the consensus fair probability is calibrated. Explore: 179 wins vs 176.1 expected from consensus fair (156.5 implied by the bet prices). Validate: 244 wins vs 246.3 (222.3). Over all games, consensus fair is calibrated too: validate 2131 home wins vs 2144 expected.
- So realised ROI is close to the "EV vs consensus" (validate: 12.4% realised vs 11.1% mean EV). This is not luck on outcomes. It is the gap between one recorded price and the median of the others.
- A 11-14% EV gap at the close between regulated books is not plausible as a real, executable price. It is the signature of quotes captured at different times, or of feed errors. The findings below test this directly.

### 2. Stale or untimed-quote artifacts: direct evidence
**(a) Same operator, different price.** Half of all bets (382 of 765) are at Caesars-named feeds: 126 explore, 256 validate. "Caesars Sportsbook" alone has 119 explore and 207 validate bets, against about 1 of 6-13 books per game.
- On those bets the same operator's sibling feeds (Caesars NJ/CO/PA, "Caesars", "Caesar's") had the same price only 0-1.4% of the time.
- At the siblings' best price, median EV vs consensus was -2.3% to -2.7%, which is just ordinary vig. Only 2.4% (explore) and 6.6% (validate) of these bets would still be at least 5% EV at the sibling price.
- Re-pricing these bets at the sibling price turns ROI from +11.7% to -4.3% (explore) and from +8.0% to -5.2% (validate).
- One operator does not post two prices at once. The bet price is a capture of Caesars at a different time.

**(b) The ML disagrees with the same book's own spread.** I split bets by whether the bet book's own spread matched the leave-one-out consensus spread (within 1 point) while its ML was off.
- The "spread matches consensus, ML off" bucket holds explore 200 bets, +33.7%, +67.4u of 75.5u; validate 154 bets, +17.1%, +26.3u of 51.7u.
- Where the whole line moved by 3 or more points (a genuinely stale book), ROI is about 0: explore -0.2% on 23 bets, validate +4.2% on 68.
- A live book moves its ML and spread together. An ML that is 5%+ off while that book's own spread sits on consensus means the ML field was recorded at a different moment from the spread, or is wrong.
- `clean_quotes` lets this through because its ML-vs-spread check allows a 10-point gap (`MAX_ML_SPREAD_GAP = 10.0`, backtest.py). That is far too loose to catch a 5% price discrepancy.

**(c) Prices that cannot be real.**
- MGM ML pairs with less than 1% overround: 60% of games in 2021 and 52% in 2022 (5% in 2023). Typical books run about 3.7-4.5%.
- BetStars 2020: 81% of pairs under 1%, median overround -0.6%.
- Betradar 2019-20: 40-43% under 1%.
- 55 of the 765 bets have a bet-book pair with overround at most 0.5% (13 are negative, i.e. an arb inside one book). They contribute +7.7u. MGM accounts for 74 validate bets and +15.0u, the largest single validate contributor.

**(d) Non-books.**
- betegy is a prediction/tipster service, not a sportsbook.
- Betradar is a Sportradar odds-feed product.
- Fantasy911.com is a picks site.
- All three vote in the consensus and can be bet "at". Fantasy911 alone has 27 explore bets.

**(e) Leave-one-book-out (book removed from the data entirely, consensus recomputed).**

| Book removed | Explore n | Explore ROI | Explore t | Validate n | Validate ROI | Validate t |
|---|---|---|---|---|---|---|
| Caesars Sportsbook | 233 | +24.2% | 1.92 | 218 | +17.1% | 2.02 |
| SportsInteraction | 305 | +18.3% | 1.84 | (unchanged) | | |
| MGM | (unchanged) | | | 354 | +10.5% | 1.83 |
| All Caesars-named feeds | 239 | +27.6% | 2.19 | 189 | +10.5% | 1.18 |
| Caesars + non-books, families merged | 205 | +16.6% | 1.69 | 190 | +12.5% | 1.35 |
| Caesars Sportsbook, 5Dimes, SportsInteraction | 190 | +20.0% | 1.40 | 218 | +17.1% | 2.02 |

ROI stays positive in every variant but significance mostly goes. Positive ROI is expected whichever book is removed: any remaining book with mis-timed quotes produces the same artifact.

### 3. Book-family grouping (`line_shop.family` = first word of the name)
Measured identical-ML-quote rates show these duplicates are counted as independent families:
- BETONLINE.ag = SportsBetting.ag: 100% identical, 2015-17.
- 5Dimes.eu = BETNOW.eu: 100% identical, 2017.
- Holland Casino and Titanbets: 78% identical (2022), 94% (2023).
- DraftKings and Unibet: 75% identical (2020, shared Kambi era).

Caesars state variants are grouped correctly. No book votes on its own family's price; the leave-one-out logic in `bets_for_game` is right. But a duplicate twin can vote for the bet book, and twins double-weight one feed in the median.

Merging the duplicates moves explore from +21.7% (t 2.37) to +16.3% (t 2.23); validate is unchanged (+12.4%, t 2.32). The grouping is a minor issue and not the driver.

Separately, "first word" grouping lumps "Caesars Sportsbook" (2018-20) with "Caesar's"/"Caesars", which match it only about 26% of the time. That is a conservative error.

### 4. Selection and multiple testing
- The threshold was chosen on explore from 5 values, and the commits show no visible iteration before the result: the strategy commit is 02:33:09, the results commit 02:34:20.
- The registry nonetheless holds at least 26 distinct validate-stage tests today: 5 ratings variants x 3 markets (re-run 3 times as the code changed), 3 line-shop markets and 8 situational rules. Only this one passed.
- Validate t 2.30 gives a one-sided p of 0.0107. Bonferroni or Holm over 26 tests gives p of about 0.28. Restricted to just the line-shop and situational batch (11 tests), p is about 0.12. It does not survive.
- The result is not monotone in the threshold, and it depends on the threshold. On a cleaned universe A (non-books removed, duplicate families merged, ML pairs with overround under 1% dropped), the 5% threshold gives explore +14.0% (t 1.90, n 306) and validate +12.7% (t 2.20, n 362). Other thresholds on validate: 3% gives +5.9% (t 1.38), 7% gives +9.5% (t 1.44), 10% gives +13.5% (t 1.62). Adding the removal of the 'Caesars Sportsbook' feed to A gives validate +18.8% (t 1.78, n 160).
- The cleaning thresholds in `clean_quotes` were derived partly from validate seasons 2021-22 (see the backtest.py comment "clean seasons (2014-17, 2021-22)"). That is not outcome leakage, but validate is not fully untouched.

### 5. Long shots and outliers

| Subset | Explore ROI | Explore t | Validate ROI | Validate t |
|---|---|---|---|---|
| Price <= 4.0 | +13.9% | 2.17 | +9.6% | 1.96 |
| Price <= 2.5 | +9.2% | 1.51 | +7.7% | 1.66 |
| Drop top 3 winners | +11.9% | 1.70 | +9.0% | 1.79 |
| Drop top 10 winners | +2.4% | 0.40 | +3.7% | 0.78 |

- In explore, two 5Dimes long-shot wins at 12.5 and 17.75 make up 28.3u of the 75.5u total.
- Validate by season: 2021 +16.0% (t 1.5), 2022 +13.1% (t 1.65), 2023 +6.9% (t 0.69). The season most like the holdout, 2023, is the weakest and not significant.

### 6. Bugs and leakage
- **No outcome leakage in `clean_quotes`.** It uses only quotes: the ML-vs-own-spread gap, deviation from the cross-book median, and impossible lines. None of those rules reads results.
- **Settlement and de-vig.** Settlement (`settle_leg` for ml) and the de-vig (power method per book, median across families, EV = fair x price - 1) are correct.
- **No duplicates.** No duplicate game_ids, no duplicate (date, home, away) rows, and no duplicate (game, side) bets.
- **Minor: both sides of one game can be bet.** `best_per_side` keys on (game, market, selection), so 21 games have both sides bet at different books. That is effectively an arb created by mis-timed quotes, worth +5.9u in total.
- **Missing vig check.** The ML pair of the bet book is not checked for overround. Zero-vig and negative-vig pairs (finding 2c) should be rejected as not being real prices.

### 7. Practical executability for this user (FanDuel Ontario only; live feed DK + bet365 + perhaps others)
- **The edge is not at FanDuel-like books.** The result relies on taking the best of about 6-13 books per game. Bets restricted to a single mainstream book (5% threshold, validate):

| Book (bet there only) | Bets | ROI |
|---|---|---|
| DraftKings | 3 | +11.7% |
| BetfairSportsbook (Flutter; closest available FanDuel proxy, unverified as identical) | 2 | +55% |
| Unibet | 7 | +40.1% |
| PointsBet | 41 | -0.9% |

  Almost all volume is at Caesars Sportsbook, MGM and Holland, the feeds with the artifacts above.
- **A live-like consensus produces almost no bets.** Simulating the live setup on validate (bet only at BetfairSportsbook, consensus from 2-5 other mainstream books) gives 2-6 bets over three seasons. A FanDuel version would bet roughly once or twice a season.
- **The live data differs from the historical data.** Live, the timestamps are real and the consensus has only 2-3 books. The historical result depends on ESPN's untimed per-book final quotes, which cannot be reproduced.
- **Holdout composition (metadata only).** 2024 has about 12 books, with `open`/`close` quotes and no `final_quote_untimed` flag. 2025 has only ESPN BET. 2026 has DraftKings and ESPN BET (12 untimed rows). With MIN_FAMILIES = 3, 2025 and 2026 produce zero bets by construction, so the "2024-2026 holdout" is really 2024.
- **2024 is too small to decide.** At the 2023 rate, 2024 gives about 100 bets. Per-bet SD is about 1.1, so the ROI standard error is about 11%. Passing a t >= 2 gate would need about 22% ROI. A real edge of 2-5% could not be detected, and a pass would most likely be noise or the same artifact.

## Path forward (only if the team wants to keep this idea)
This would be a new experiment, decided now without looking at the holdout, and run on explore and validate first:
1. Drop non-books: betegy, Betradar, Fantasy911.com.
2. Merge measured duplicates into one family: BetOnline/SportsBetting; 5Dimes/BETNOW; Holland/Titanbets; DK/Unibet for 2020. Better still, merge any two books whose ML pairs are identical in at least 70% of games that season.
3. Reject any book's ML pair with overround below 1.5%.
4. Require the bet book's ML-implied spread to be within 1.5 points of its own quoted spread, and its own spread to be within 1 point of the consensus spread. This removes ML-stale artifacts.
5. Reject a bet when a sibling feed of the same operator in the same game prices that side at least 2% worse.
6. Allow at most one side per game.
7. Report results for "bet only at a FanDuel-like book" (BetfairSportsbook as proxy) separately from "best of all books".
8. Apply a registry-wide multiple-testing correction.

Then accept that the only meaningful test of the timed-quote hypothesis is forward paper-trading of FanDuel vs DK/bet365 snapshots with real timestamps, or 2024 alone, which is underpowered. A one-shot holdout read is not justified for the current spec.

Scratch scripts: /tmp/claude-0/-home-user/268fbe1e-a6ff-5f43-b494-89d2b20536b6/scratchpad/ls_review/ (repro.py, an1.py, an2.py, an3.py, variants.py, clean_var.py, live.py).
