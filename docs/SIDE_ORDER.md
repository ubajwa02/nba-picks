# DraftKings prop sides: the first price listed is the Over (2026-11-17)

## What was wrong

ESPN's feed gives every DraftKings player prop as two prices at one line and does not say which price is the Over. The system refused to guess. A pair was labelled only when bet365 milestone prices could bracket it, which was about one pair in four. Every other pair was recorded at the worse of its two prices, with no fair value, so:

- the price on the record was wrong for one side of almost every pair (an underdog at +124 was recorded at -164),
- the check that holds a pick when the model is far from the market could not run, because there was no market chance to compare with,
- only a quarter of the props could be used to measure the model against the market.

On 2026-11-16 the bet365 feed started answering 401 and no pair has been labelled since.

## What was measured

The first price ESPN lists for a DraftKings prop is the Over, the second is the Under. Three independent ways of looking say so:

| evidence | result |
|---|---|
| Exact prices. One game (NYK at TOR, 2026-11-17) fetched from a second feed that labels the sides, compared with ESPN's pairs for the same game. The fixture is `tests/fixtures/oddsapi_event_props_20261117.json` in the FanDuel price PR. | 24 of 24 pairs with unequal prices match to the cent with the first price as the Over. 2 pairs had equal prices and say nothing. |
| bet365 ladder. Every pair the old ladder rule could label while that feed worked. | 2,297 of 2,374 (96.8%) say the first price is the Over. The 77 others are near-even pairs, which the ladder cannot tell apart. |
| Results. For every graded closing pair, did the stat go over, against the fair chance of the first-listed price. | Slope 1.05 (se 0.10) on 8,152 pairs over 24 slates, and between 0.93 and 1.72 in each of the five weeks (`reports/side_order.md`). A random order would give 0, a reversed order -1. |

It is not a property of ESPN's feed in general. Last season's ESPN BET props were listed in no fixed order (slope about 0), so the rule is used for DraftKings only and is checked all the time.

## How it is used

`nbapicks/sideorder.py`. While the checks below hold, `predict` labels every DraftKings pair by its listing order: each side gets its own price and a fair chance (the pair with the margin removed). The record says `price_basis: "labelled"` and `side_basis: "listing_order"`.

A pair is labelled by order only with evidence for the order and none against it:

1. **Results** (`refresh`, run by `settle`). The slope above is measured again on the trailing 1, 3, 10 and 30 slates. A window whose slope plus three standard errors is under 0.75 marks the order `failed`. A slope three standard errors above zero on 300 or more pairs marks it `confirmed`. Results older than 60 days do not count, so a new season starts `unconfirmed`, and a `confirmed` that has not seen a graded slate for 14 days is not relied on. The state is `data/state/side_order.json` and the readable version is `reports/side_order.md`.
2. **Same run** (`run_check`, in `predict`, before anything is priced). The model's P(over) is ranked against the first-listed fair chance across the slate's pairs. That rank correlation was between 0.32 and 0.66 on every slate so far and above zero in all 164 games. Under 0.15 on a slate of 40 or more pairs, or zero or less in a game of 12 or more pairs, counts as evidence against.
3. **A labelled feed**, when one answers. If bet365 votes the other way for a game (90% of at least 8 pairs), nothing in that game is labelled.

The rule on each run:

| results status | this run's agreement | pairs are labelled by order |
|---|---|---|
| failed | anything | no |
| anything | against (slate) | no |
| confirmed | not against | yes, except a game that is itself against or contradicted by a labelled feed |
| unconfirmed | strong (0.25 or more on 100 or more pairs) | yes, same exceptions |
| unconfirmed | anything else | no |

"No" means exactly the old behaviour: the bet365 pair or ladder label where there is one, otherwise the worse price of the pair and no fair value.

How the checks behave when the feed is wrong, replayed on the real slates:

- True order: `confirmed` after the second slate of the season and never `failed` since. Started from any later slate, it is confirmed within one to four slates.
- Sides reversed: the same-run check refuses on the first run (rank correlation -0.42 on 280 pairs on 2026-11-17), and the results check reads `failed` after two slates. A reversal in mid-season reads `failed` after the first reversed slate.
- Sides in random order: the same-run check refused in 3 of 3 shuffles of the 2026-11-17 slate. Over 200 shuffles of the season the results check read `failed` after 4 slates at the median and 13 at worst, and read `confirmed` at any point in 1 of the 200.
- One game reversed: that game goes back to the conservative price, the others are unaffected.

## What changes downstream

- Prices and EV on DraftKings prop records are the real ones, not lower bounds.
- The existing check `quality.max_model_market_gap` now applies to DraftKings props, because they now have a market chance. A prop where the model is more than 10 points from DraftKings' fair chance is held ("likely missing information"). On 3,192 past props the old lean rule would take (model at 60% or more, price -200 or longer), 2,298 fail this check or the 15% edge ceiling; they won 52.4% against 59.7% for the rest. Neither group beat the price (-4.0% and -1.8% per unit).
- The dashboard's model-against-market comparison covers every DraftKings prop with a model estimate, not a quarter of them.
- A candidate whose price, probability and decision did not change keeps its existing record (`pipeline.version_id`), so on the day this is deployed some records of the slate in progress still say `conservative`.

## Limits

- The closing pair is the last quote change before tip. A quote is stored only when it changes, so a line that moved away and came back at identical prices is missed and the line in between is used.
- The same-run check leans on the prop model being roughly aligned with the market. If a model were ever uncorrelated with the market, pairs would fall back to the conservative price, which is safe but loses the benefit.
- Turning it off: `prop_sides.listing_order: off` in `config/nbapicks.yaml`.
