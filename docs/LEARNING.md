# The learning loop (2026-11-17)

## What it is for

Since the DraftKings prop sides are labelled (`docs/SIDE_ORDER.md`), every finished slate gives about 340 props that each carry a market chance and a result. `nbapicks/learn.py` turns that into three standing answers, refreshed after every slate that is graded:

1. **Is the DraftKings price itself off in a way we could correct?** It tests a fixed list of corrections on slates they have not seen, and puts one in force by itself when the evidence clears a gate. It takes it out again when it stops working.
2. **Would any simple rule have paid?** A fixed scoreboard of rules graded at the last price before tip.
3. **Do the posted picks beat later prices?** The earliest sign of a real edge, long before the win-loss record can say anything.

It runs at the end of `settle`, so on every runner slot, and costs two counts when nothing new was graded. The results are in `reports/learning_latest.md`.

## What happens after each slate

1. **The graded table.** For every finished game, the last DraftKings pair stored before tip for each player and stat (`sideorder.closing_pairs`), its fair chance (the pair with the margin removed), the result, and the prop model's last estimate made before tip at that line. Pushes and players who did not play are left out.
2. **Walk-forward scoring.** Each correction is refitted on the slates before a slate and scored on that slate. It never sees the results it is scored on. The first five slates are for learning only.
3. **The gate** decides which correction, if any, is in force for the next slate.
4. **State, report, log.** `data/research/learned.json` (everything, including the parameters in force), `reports/learning_latest.md` (the readable version) and one line per graded slate in `data/research/learning_log.jsonl` (what the loop believed that day, so its decisions can be checked later against what it knew).

## The corrections

All work on the log-odds of the fair chance and are pulled toward "the market is right", so with little data they do nothing.

| name | what it can learn | pull toward the market |
|---|---|---|
| `shift` | Overs (or Unders) win more often than their price says | as if 500 results had already shown no bias |
| `shift_slope` | the same, plus favourites being over- or under-priced | 500 results on the bias, about 1,600 on the slope |
| `stat_shift` | a bias per stat (points, rebounds, assists, threes) around a common one | 1,500 results per stat |
| `recent_shift` | a bias that drifts: recent slates count more (half weight after 10 slates) | 500 results |
| `model:<version>` | how far to move from the market toward prop model `<version>` when they disagree | about 1,150 results |

A `model:` correction is fitted and scored only on the props that model version priced. The list is fixed in code (`learn.CORRECTIONS`); changing it means bumping `learn.VERSION`.

## The gate

In `config/gates.yaml` under `learning`, written before the loop had put anything in force.

A correction is put in force when, on slates it had not seen:

- **Evidence of 3 or more.** For every unseen prop, the adjustment the correction proposed is multiplied by how the result differed from the market chance. Summed by slate, the total over the root of the summed squares is about a standard normal number when the correction knows nothing. It answers "did the adjustments lean the way the results went".
- **It helped.** Applying it lowered log loss over all unseen slates, and over the newer half of them.
- **Enough of them.** At least 15 unseen slates and 3,000 props.

It is dropped when the evidence falls under 2 or it stops helping. An active correction is not applied when no slate has been graded for 30 days (`learn.active`), as after a summer.

**At most one is in force, and which one is a rule too.** When several pass, `recent_shift` is used. A bias that is real can still end: books correct their prices, and the one bias seen so far (Overs priced too high in the opening weeks) faded within a month. `recent_shift` is the correction that follows a bias down when it fades; the others average over the whole season and would keep correcting for it. The exception is another passing correction that has saved at least 1.5 times as much log loss per prop (`richer`): it explains more than a plain bias does, for example a model that knows something or a bias in one stat only, and it is used instead. When `recent_shift` does not pass, the correction in force stays while it clears the lower bar, so two that both pass do not take turns.

Why this test. The obvious test, a t-test on the log loss saved, has half the power: a correction of size `a` saves about `a²/8` per prop with a spread of `|a|/2`, which gives `t = |a|·√n / 4`, while the evidence number is `|a|·√n / 2`. Half the power means four times the slates before a real bias is acted on. The evidence number alone would not be enough either, because it does not care whether the size of the adjustment was right, so the gate also asks for an actual saving. The bar is 3 and not 2 because the gate is looked at after every slate; with more than about 90 corrections the bar would rise further (`metrics.noise_floor`).

### How the gate behaves when the truth is known

`python -m tools.learn_gate_sim` builds full seasons of 160 slates from the real slates (their sizes, prices and model estimates), draws the results from a known truth, and replays the loop slate by slate. 800 seasons on the 24 real slates through 2026-11-16 (`--seasons 300 --only "market is right"` for the first row, `--seasons 100` for the others, seed 1):

| the truth in the simulated seasons | seasons | a correction was put in force in | first time (median) | share of the season in force | dropped at least once in | in force at the end in | log loss saved per prop while in force | the same over the whole season |
|---|---|---|---|---|---|---|---|---|
| the market is right | 300 | 3 | slate 62 | 0.1% | 3 | 0 | -0.00025 | 0.00000 |
| Overs 1 point too high | 100 | 93 | slate 75 | 41% | 29 | 88 | +0.00013 | +0.00005 |
| Overs 2 points too high | 100 | 100 | slate 32 | 78% | 12 | 100 | +0.00073 | +0.00059 |
| Overs 3 points too high | 100 | 100 | slate 23 | 85% | 2 | 100 | +0.00171 | +0.00150 |
| the prop model knows 15% of what it disagrees with the market about | 100 | 100 | slate 40 | 71% | 9 | 100 | +0.00084 | +0.00058 |
| Overs 3 points too high for 60 slates, then the market is right | 100 | 100 | slate 23 | 48% | 100 | 9 | +0.00061 | +0.00031 |

Reading it:

- **It does not act on noise.** With the market exactly right, a correction was put in force in 3 of 300 seasons, for 0.1% of all slates, and it was dropped again every time. While in force it cost 0.0002 per prop, which is a fair chance moved by about one point.
- **It finds a real bias, and how fast depends on its size.** 3 points: as soon as the gate allows (20 slates are the minimum: 5 to learn from, 15 unseen). 2 points: about five weeks. 1 point: about half a season, and in 7 seasons of 100 never. A 2-point bias known exactly from the first day would be worth about 0.0008 of log loss per prop; over a whole season the loop collects 0.0006 of it. The rest is the time it takes to be sure.
- **A model that knows something is weighed in.** With the truth 15% of the way from the market to the model, `model:` took over from the plain bias corrections in every season.
- **When a bias ends, the correction fades and is then dropped.** It stayed in force for 41 slates after the change on average, at a cost of 0.0003 per prop over those slates, and the season still ended ahead. This is the case the choice of `recent_shift` is for: when the correction with the most evidence was used instead (the first version of the rule), the same seasons cost 0.0007 per prop after the change and the season's saving was a third lower (0.00021 against 0.00031). Dropping a correction on its last 10, 15 or 20 slates alone was tried on the same seasons as well: it let go sooner after the change, but it also let go of corrections that were still right, and it saved less over the season than the rule above.

The refits of each scenario can be kept (`--cache DIR`), so a change to the gate is replayed on the same seasons in seconds.

## What it found on the first 24 slates (through 2026-11-16)

- **The market.** Overs won 47.4%; the fair chance said 49.3%. Fitted on all 24 slates that is a bias of -0.077 on the log-odds (se 0.026), which looks significant. Out of sample it is not: the four bias corrections have evidence between +2.1 and +2.4, saved log loss on the older half of the unseen slates and lost it on the newer half. The Under bias of the opening weeks has faded (Overs won 53.5%, 52.0% and 51.0% on the last three slates). Nothing is in force.
- **The prop model.** `model:props-v0`, the model in use, has evidence +0.30 on 3,282 unseen props: when it disagrees with DraftKings it is not right more often than chance. This is the same conclusion as the red-week analysis, now measured every day.
- **Rules.** Nothing pays at the last price before tip. Every Over lost 10.1% per unit, every Under 2.8%, the pick rule on main 3.4%. No rule is near the bar.
- **Posted picks.** 114 of the 123 posted model picks could be matched to the quote they were posted on, and 54 of those had a later quote at the same line. The market moved toward the pick in 21, not at all in 10 and away in 23, on average by -0.1% (se 0.5). By the later fair chance they were worth -6.5% per unit, exactly the book margin on those pairs. So far the picks carry no edge that the market recognises.

## How a correction is used

```python
from nbapicks import learn
a = learn.active(learn.load(ctx.root), ctx.today)          # None unless a correction is in force and fresh
fair_over = learn.adjust(a, fair_over, stat=stat, model_prob=p_model_over, model_version=version)
```

`adjust` returns its input when nothing is in force. Nothing on `main` calls it yet: the pick rule there ranks by the model's own probability. The price-edge rule of the FanDuel pull request measures edge against the DraftKings fair chance, and that fair chance is what a correction in force would refine; wiring it in is the follow-up to this change.

## Limits

- **"Last price before tip" is not the closing line.** Half of the pairs were stored 2.4 hours or more before tip, because the runner's last pre-tip pass is in the early evening. A pass shortly before each tip would make the benchmark sharper and the comparison with later prices cover more picks (54 of 123 today).
- **A quote is stored only when it changes.** A line that moved away and came back at the same prices is not seen, and the main line switching between neighbours (Over 2.5 at -170, then Under 3.5 at -170) is not a move, so it is counted and not compared.
- **Picks posted before the sides were labelled** were recorded at the worse price of the pair. They are matched to their quote through that price and compared at the price of their own side (7 of the 123 were really on the better-priced side).
- **One book.** Everything is measured against DraftKings as ESPN reports it.
- **The corrections are simple on purpose.** They can learn a bias by side, by stat, by price level and by model disagreement. They cannot learn anything about a single player or matchup.
- **Held-back data.** The loop never reads the props holdout window of `config/gates.yaml` or anything before it (`learn.first_slate`), and otherwise looks back 240 days.
- **A cold start.** The first 20 slates of the first season cannot change anything: 5 to learn from and 15 unseen ones to be sure. The opening-weeks bias of this season was over before the loop could have acted on it. Later seasons start warm, because the last 240 days carry over.
- **A new season.** The side order has to be confirmed again by results before the loop runs (two slates), and a correction from the season before is not applied until then.
