# Why Nov 11 to 16 lost, and what changed (2026-11-17)

Reproduce every number with `python -m tools.red_week_analysis`. Forward ledger data only; the props holdout (2026-02-01 to 2026-06-30) was not touched.

## What happened

| period | straight picks | units | parlays and lottos | units |
|---|---|---|---|---|
| Oct 20 to Nov 1 (props-v1) | 39-18 | +7.28 | 9-10 | +3.12 |
| Nov 2 to Nov 10 (props-v0) | 30-11 | +7.25 | 11-12 | +8.55 |
| Nov 11 to Nov 16 (props-v0) | 10-21 | -14.52 | 0-16 | -16.00 |

## Root cause

The picks never had an edge. The first three weeks were good luck and the red week was the bill.

1. **The live prop model adds nothing over the book's price.** On all 10,174 graded DraftKings props since Nov 2, props-v0 has a log loss of 0.7318. A coin flip scores 0.6931. Where it said 60 to 65% the props hit 54.1%; where it said 80 to 85% they hit 56.7%. With the market's fair price in the same regression, the model's coefficient is 0.21 (z 1.9) for props-v0 and 0.01 for props-v1. Neither clears the project's t >= 2 bar, so the model's weight should be zero.
2. **The pick rule bought the model's favourites anyway.** It ranked by model win chance (>= 60%) and ignored edge. Every prop that rule could have chosen under props-v0 (n = 2,477) hit 53.7% against a 57.3% break-even: ROI -6.3%, t -2.3 clustered by day. The posted picks are a sample of that pool. At 53.7%, going 30-11 has a probability of about 0.8% and going 10-21 about 1.3%. Both are tails of the same losing rule.
3. **For three props in four, the system did not know which price was the Over.** ESPN lists DraftKings props as two unlabelled prices. Sides were labelled only where a bet365 ladder confirmed them; the rest were recorded at the worse price of the pair. On those 1,914 unlabelled props the old rule hit 51.4%. 12 of the 14 picks on Nov 14 to 16 with a stored prediction were of this kind. The bet365 feed has returned 401 since Nov 16, so now no side is labelled at all.
4. **A worse model was live because of a bug.** props-v1 was demoted to props-v0 on Nov 2 by a calibration check that took 150 unordered props in 10 bins, where a perfectly calibrated model scores about 0.065 against a 0.06 limit. props-v1's pool hit 58.9% (ROI +1.0%), props-v0's 53.7%.
5. **Rejected props were posted.** The rule treated "EV below threshold" as a soft reason. 8 of the 14 picks on Nov 14 to 16 were rejects at the run that posted them.
6. **Parlays and the lotto were always posted, at any edge.** 16 of 58 had a negative edge by the model's own numbers, and the model's numbers were too high to begin with.
7. **Prices were DraftKings', not FanDuel's**, and 22 of the 31 red-week picks were -150 or shorter, so a win paid 0.64u on average against 1u lost.

Not the cause: stale box scores or injuries (sources were healthy on Nov 14 to 16), or a bias to one side (overs and unders both lost).

## What changed

- A pick is now a FanDuel prop whose price beats the fair price by 5% (the pre-registered prop threshold). The fair chance is DraftKings' two-way price for the same line from the same odds response, margin removed. Sides are labelled by the feed. The prop model has weight 0.
- Picks are ranked by that edge, one per player and one per game, and recorded and graded at the FanDuel price.
- Parlays and the lotto are posted only when their combined edge clears their thresholds.
- Posted picks are re-checked on every run before tip (price and injuries). The result is shown as advice; a pick is never removed or regraded.
- Every FanDuel and DraftKings quote fetched is stored in `data/ledger/fd_quotes/`, so this rule can be scored later.
- The demotion check uses the newest 500 settled props in time order. Past picks tagged `props_v1` from Nov 2 on are shown as props-v0.

## What this does not prove

The new rule stops the known leak. It is not shown to win: there is no historical FanDuel prop price to test it on, and a two-book comparison is a thin fair price. Expect few picks. On Nov 17 the best of 126 comparable FanDuel prices was +4.7%, so no straight pick qualified. The market stays in research until the forward gates in `config/gates.yaml` pass.
