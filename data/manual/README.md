# Your manual inputs

Two files here are yours to edit. The daily job reads them; nothing else writes to them.

## wagers.csv: bets you actually placed

Only rows in this file count as actual wagers. A published pick is never assumed to have been bet.

| column | example | notes |
|---|---|---|
| wager_id | fd-0001 | optional but recommended: your own id for the bet. Needed to log two identical bets, or to correct one |
| corrects | fd-0001 | optional: the wager_id this row replaces (the old row stops counting) |
| placed_at | 2026-10-21T22:41:00Z | when you placed it; end with Z (UTC) or an offset like -04:00 |
| book | FanDuel | |
| game_id | 401909834 | ESPN game id, shown on every pick and on the dashboard |
| market | ml / spread / total / prop / parlay | |
| selection | home / away / over / under | parlays: anything (e.g. `parlay`) |
| line | -3.5 | blank for moneyline; required for spread, total, prop |
| price_american | -110 | or fill price_dec instead |
| price_dec | 1.91 | |
| stake | 1 | **this repository is public: log stakes in units, not money** |
| units | 1 | optional |
| player_id, stat | 3934672, pts | props only (ESPN athlete id; pts, reb, ast, fg3m, stl, blk) |
| legs | 401909834 ml home; 401909835 total over 221.5 | parlays only, for your own reference |
| result | win / loss / push / void / cashout | optional manual settlement. Parlays and cash-outs always need it |
| net | 0.4 | profit or loss in stake units; required for cashout, otherwise computed |
| notes | | free text |

Straight ml, spread, total and prop bets settle automatically from ESPN results and box scores. A row that cannot be read is skipped and named in the run notes; the others still import.

## signals.csv: picks posted by other Discord channels

Paste each message with its original timestamp. One pick per line inside `text`; keep the odds the poster stated.
Picks without stated odds are kept as text and not scored, because odds are never invented.

```
provider,posted_at,text,channel,book
SharpGuy,2026-10-21T15:00:00Z,"Magic ML -140 1u
Hawks/Magic o235.5 -110",nba-picks,FanDuel
```
