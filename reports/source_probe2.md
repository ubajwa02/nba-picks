# Source probe 2

### page https://moviodds.com/doc
status=200

 bet365 Odds API Docs: REST + WebSocket, 24 Sports | MoviOdds Odds API bet365 odds feed Start with GET /odds to get the matches and current prices. Then connect to /ws to keep receiving odds updates. More docs: Sports &middot; Markets &middot; WebSocket &middot; Bet Builder &middot; Python client &middot; History &middot; moviodds.com 1. Load matches 2. Subscribe 3. Apply updates 4. Reconnect 5. Bet builder 6. Results 7. History 8. Futures 9. API keys 10. Match stats 1. Load all matches and their odds curl https://moviodds.com/odds Example response: { "matches": [{ "id": "123456", "home": "Team A", "away": "Team B", "league": "Example League", "kickoff_utc": "2026-09-11T18:00:00Z", "in_play": false, "quotes": [{ "fixture_id": "123456", "group_id": "981", "market_id": "100", "sel_id": "9001", "label": "Team A", "odds_dec": 2.5, "ts": "2026-09-11T12:00:00Z" }] }] } Save each match under its id , along with its names and odds If quotes is empty, there are no cached odds for that match yet Only need part of the board? /odds?in_play=1 returns just the matches in play, and /odds?groups=40 returns just the markets you list (comma-separated group ids; Full Time Result is 40 before kickoff and 1777 in play). Each match always carries market_count , the number of markets priced for it. Soccer is the default. Add sport for any of the other 23 sports, for example /odds?sport=tennis , or sport=all for every sport at once; every match carries its own sport field. The keys and each sport's main markets are on the sports page . A match in play carries a score field. It is always written home-away, the home side first, for every sport (for example "2-1" ). Cricket is the one that does not use a plain number-to-number score: it uses bet365's own wickets/runs form, for example "7/199" (7 wickets, 199 runs), with each innings separated by a comma. Want a link straight to the match on bet365? Add /odds?links=1 and every match gains a links object: match (open this: the live page while the match is in play, otherwise the pre-match page), prematch and live . They are bet365's own in-browser routes, so the same link works on any regional bet365 domain. It's opt-in so the default board stays small. To find a specific selection on that page, use the quote's sel_id . If the response has "warming": true (and few or no matches), the service has just restarted and is still loading the board. Wait ~30 seconds and fetch again. Matches and odds arrive within a couple of minutes. 2. Subscribe to all matches on one WebSocket wss://moviodds.com/ws Once the connection opens, send: {"op":"subscribe"} Leave out fixtures and groups to get updates for all matches and markets. New matches are included as their odds come in. You'll first get a snapshot for each match with cached odds. After that, delta messages arrive whenever quotes change. Matches without cached odds won't have a snapshot yet. 3. Apply each message to your match list The fixture value tells you which match to update. It matches the id from the first request. { "type": "delta", "fixture": "123456", "quotes": [{ "fixture_id": "123456", "group_id": "981", "market_id": "100", "sel_id": "9001", "label": "Team A", "odds_dec": 2.6, "ts": "2026-09-11T12:00:05Z" }] } When a snapshot comes in, use it as the match's new odds list. A delta only contains changes, so update or add those quotes without clearing the rest Within each match, use [group_id, market_id, sel_id] to identify a quote. If market_id is missing, use "" . Replace the whole quote when an update arrives. If suspended is missing, treat it as false. A remove message tells you a market has closed or the match has left the board, so those selections are no longer bettable. {"type":"remove","fixture":"123456","quotes":[{"group_id":"981","market_id":"100","sel_id":"9001"}]} means drop those selections; {"type":"remove","fixture":"123456"} with no quotes means the whole match is gone, so drop it. This is the signal that a WebSocket-only client used to miss: without it the server simply stops sending and a stale last price looks bettable. If your client does not handle the remove type, you still stop betting those selections anyway: just before each remove we send the same selections in a delta marked suspended , which an older client applies as a normal update. 4. Handle new matches and reconnects Check /catalog about once a minute for updated names, kickoff times and the current match list. Keep the odds you already have, and remove matches that have left the catalog. The socket also pushes a remove (see section 3) the moment a market closes or a match leaves the board, so you do not have to wait for the next catalog refresh to drop a stale price. If odds arrive for a match you haven't seen yet, save them under its ID. The next catalog refresh will give you its details. If a sport looks empty, check last_fixture_seen_by_sport on /health before assuming it is broken. It maps each sport to the most recent time we saw one of its fixtures, so a recent timestamp means we are still reading that sport and it is just a quiet off-week, while a stale or missing one points to a real problem worth reporting. If the socket disconnects, reconnect and subscribe again. If you get a lagged message, fresh snapshots of the matches affected follow on their own; don't subscribe again. A connection's first 3 subscribe/unsubscribe messages apply at once, then one every 2 seconds; extra ones are merged and the latest wins. Each subscribe sends a full snapshot of every match you subscribe to, suspended selections included, so replace your copy of each match with it. Missed updates can't be replayed. Close code 1001 means we restarted. Wait about 3 seconds, then retry at 3, 6, 12 and 24 seconds, then every 30. Code 1008 means our ping, sent every 30 seconds, went unanswered for 10 seconds, or your socket wasn't being read. In Node.js and browsers, keep long synchronous work off the event loop. More on the WebSocket page . Two timestamps tell you different things. ts is when a price last changed . polled_at (per fixture, on /odds and /snapshot ) is when we last successfully read fresh prices for that fixture, whether or not any price moved. To judge whether a match is still being priced, compare polled_at to server_time , not ts : a stable price (normal for pre-match and far-off matches) keeps an old ts while it is still being checked, so a large server_time − ts by itself does not mean stale. polled_at advances whenever we read a fixture's current prices, including when every price is suspended (a suspended market is still a successful read). Live matches are re-confirmed on a short cadence even when nothing is moving, so a suspended or quiet match keeps a recent polled_at . Only an empty or failed read leaves it where it was. On /ws , every snapshot carries the fixture's polled_at , and after each read a polled message confirms it: {"type":"polled","fixtures":{"202138001":"2026-10-14T21:40:05Z"},"groups":{"202138001":

### page https://moviodds.com/bet365-nba-odds-api/
status=200

 Free bet365 NBA &amp; Basketball Odds API: Live &amp; Pre-match, REST + WebSocket | MoviOdds MoviOdds Docs API docs Sports Bet Builder Python moviodds.com Basketball (NBA) Overview Leagues Markets Quickstart Sample response Live prices FAQ Free bet365 NBA &amp; Basketball odds API Every bet365 basketball market, pre-match and in-play, as JSON over REST and WebSocket. No key, no sign-up. Overview MoviOdds serves only bet365's basketball prices. You get every market bet365 lists for a match, from the same GET /odds endpoint and WebSocket used for every sport. NBA, WNBA, EuroLeague and domestic leagues worldwide. Leagues Every league bet365 lists, including: NBA Japan B League Premier Japan B League One Germany Pro A Uruguay Tercera de Ascenso Spain Liga ACB Italy Lega 1 Greece A1 Women Markets Game: point spread, total points, money line Halves and quarters Team totals Player props where bet365 offers them The Game grid (Line, Total, To Win) is group 1453 before tip-off and 112 in play. Every price carries its group_id and group_name ; grid markets also carry the team in side and the market in line . Quickstart curl "https://moviodds.com/odds?sport=basketball" curl "https://moviodds.com/odds?sport=basketball&amp;in_play=1" import requests data = requests.get("https://moviodds.com/odds", params={"sport": "basketball"}, timeout=30).json() for match in data["matches"]: print(match["league"], "|", match["home"], "v", match["away"], "|", len(match["quotes"]), "prices") Sample response A real /odds?sport=basketball match, trimmed to a few prices: { "matches": [ { "id": "199419304", "sport": "basketball", "home": "DET Pistons", "away": "BOS Celtics", "league": "NBA", "kickoff_utc": "2026-10-20T19:00:00Z", "in_play": false, "market_count": 1, "quotes": [ { "fixture_id": "199419304", "group_id": "1453", "group_name": "Game", "side": "BOS Celtics", "line": "Line", "label": "+1.5", "odds_dec": 1.90909, "odds_frac": "10/11", "sel_id": "1888364452" }, { "fixture_id": "199419304", "group_id": "1453", "group_name": "Game", "side": "DET Pistons", "line": "Line", "label": "-1.5", "odds_dec": 1.90909, "odds_frac": "10/11", "sel_id": "1888364453" }, { "fixture_id": "199419304", "group_id": "1453", "group_name": "Game", "side": "BOS Celtics", "line": "To Win", "odds_dec": 2.1, "odds_frac": "11/10", "sel_id": "1888364459" }, … ] } ] } Live prices In-play basketball prices are pushed over the WebSocket within about a second of bet365 changing them. Connect to wss://moviodds.com/ws and send {"op":"subscribe"} to receive every price change ( WebSocket guide ). See the API docs for loading the board and applying updates, and every sport for the other 23. FAQ Is the bet365 Basketball (NBA) odds API free? Yes. GET /odds needs no sign-up and no key. Limits are 300 requests per minute and 25 WebSocket connections per IP. Are these really bet365 odds? Yes, exclusively bet365&#x27;s own prices, pre-match and in-play. MoviOdds is an independent project and is not affiliated with bet365. Do you have live basketball odds? Yes. Live matches carry in_play: true. In-play basketball prices are pushed over the WebSocket within about a second of bet365 changing them. Which markets are included? Every market bet365 prices for a match. Each price carries its group_id and group_name so you can filter. Do you have historical odds, closing lines and results? Yes. /history?fi=&lt;match&gt; returns every recorded price move, /closing?fi=&lt;match&gt; each selection's closing line (its last price before kickoff), and /results finished matches with their final score. See historical odds , closing lines and the API docs . MoviOdds is an independent project. The odds served here are exclusively bet365 odds. Not affiliated with or endorsed by bet365. Odds data is for informational use only. Questions or custom work: Discord . 

### page https://moviodds.com/bet365-historical-odds-api/
status=200

 bet365 Historical Odds API: Every Recorded Price Move as JSON | MoviOdds MoviOdds Docs API docs Sports Bet Builder Python moviodds.com Historical odds What you get Request Sample response Export to CSV FAQ bet365 historical odds API Every bet365 price change we have recorded, pre-match and in-play, as a timeline per selection. Free, no key. What you get GET /history?fi=&lt;match&gt; returns the recorded price points for a match, oldest first. Each point has the time, the selection and its price, and whether it was suspended. All 24 sports, every market bet365 prices; pre-match and in-play in one timeline; recorded since September 2026: hundreds of millions of price points. Pair it with closing lines for the last price before kickoff and /results for the final score. Request curl "https://moviodds.com/history?fi=201714836&amp;sel=59223458" Parameter Use fi Match id (required). Pre-match and live ids both work and are merged. group Only one market group, e.g. 40 for soccer Full Time Result. sel Only one selection. from , to Time window, RFC 3339 ( 2026-10-04T12:00:00Z ) or Unix seconds. limit Max rows, default 5000, up to 50000. truncated is true when you hit it. Sample response A real timeline: the underdog's money line in LV Raiders v KC Chiefs (NFL, 4 October 2026), trimmed to its first and last points. It drifted from 2.80 to 2.90 before kickoff. { "fixture_id": "201714836", "fixture_ids": ["201714836", "202267109"], "count": 25, "truncated": false, "limit": 5000, "points": [ {"ts": "2026-10-02T17:56:23Z", "fixture_id": "201714836", "group_id": "1441", "group_name": "Money Line", "sel_id": "59223458", "label": "KC Chiefs", "odds_dec": 2.8, "odds_frac": "9/5", "suspended": false}, &hellip; {"ts": "2026-10-04T20:01:03Z", "fixture_id": "201714836", "group_id": "1441", "group_name": "Money Line", "sel_id": "59223458", "label": "KC Chiefs", "odds_dec": 2.9, "odds_frac": "19/10", "suspended": false}, {"ts": "2026-10-04T20:21:01Z", "fixture_id": "201714836", "group_id": "1441", "group_name": "Money Line", "sel_id": "59223458", "label": "KC Chiefs", "odds_dec": 2.9, "odds_frac": "19/10", "suspended": false} ] } Each point carries the same identity fields as /odds : group_name and label , plus side , line , handicap and n2 on the markets that use them (a totals leg, for example, carries "side": "O", "line": "2.5" ). Fields are present only when they have a value. Export to CSV import csv, requests h = requests.get("https://moviodds.com/history", params={"fi": "201714836", "group": "1441"}, timeout=60).json() with open("history.csv", "w", newline="") as f: w = csv.writer(f) w.writerow(["ts", "sel_id", "label", "odds_dec", "suspended"]) for p in h["points"]: w.writerow([p["ts"], p["sel_id"], p.get("label", ""), p["odds_dec"], p["suspended"]]) print(h["count"], "rows") Each point already names its market and selection ( group_name , label , side , line ), so you usually do not need a second call. If you want the full market list for a match, read its quotes from /odds : each quote has the same sel_id . FAQ Is the bet365 historical odds API free? Yes. No sign-up and no key. /history allows 120 requests per minute per IP. How far back does the history go? To September 2026, when we started recording. Every price change since then is kept. Does it include in-play odds? Yes. Pre-match and in-play prices are in the same timeline, and points carry suspended when the market was closed. Which sports and markets? All 24 sports we cover and every market bet365 prices, from match winners to player props. Are these really bet365 odds? Yes, only bet365's own prices. MoviOdds is an independent project and is not affiliated with bet365. More: closing lines &middot; live WebSocket &middot; all 24 sports &middot; Python client &middot; API docs MoviOdds is an independent project. The odds served here are exclusively bet365 odds. Not affiliated with or endorsed by bet365. Odds data is for informational use only. Questions or custom work: Discord . 

### page https://moviodds.com/bet365-closing-line-odds/
status=200

 bet365 Closing Line Odds API: Closing Prices for Every Market | MoviOdds MoviOdds Docs API docs Sports Bet Builder Python moviodds.com Closing lines What you get Request Sample response Measure your CLV FAQ bet365 closing line odds API The last bet365 price before kickoff for every selection in a match, as JSON. Use it to measure closing line value (CLV). Free, no key. What you get GET /closing?fi=&lt;match&gt; returns every selection bet365 priced for a match, each with: pre_close : its last price before kickoff (the closing line); last : its last recorded price, which for a finished match is the final in-play price. It covers every market, from the match winner to spreads, totals, player props, corners and alternative lines. A single NFL game has over 4,000 selections with a close. It works for all 24 sports we cover, for matches recorded since September 2026. Request curl "https://moviodds.com/closing?fi=201714836" Get the match id from /odds before the game, or from /results after it. bet365 sometimes gives a match a new id when it goes live. Both ids work, and the response merges them: fixture_ids lists both and prematch_id names the one the close was taken from. Sample response A real response for LV Raiders v KC Chiefs (NFL, 4 October 2026, kickoff 20:25 UTC), trimmed to the money line: { "fixture_id": "201714836", "fixture_ids": ["201714836", "202267109"], "prematch_id": "201714836", "kickoff_utc": "2026-10-04T20:25:00Z", "kickoff_known": true, "kickoff_estimated": false, "pre_close_basis": "kickoff", "closed": true, "selection_count": 4347, "selections": [ { "group_id": "1441", "group_name": "Money Line", "sel_id": "59223451", "label": "LV Raiders", "pre_close": {"ts": "2026-10-04T20:21:01Z", "group_name": "Money Line", "label": "LV Raiders", "odds_dec": 1.434782608695652, "odds_frac": "7/16", "suspended": false} }, { "group_id": "1441", "group_name": "Money Line", "sel_id": "59223458", "label": "KC Chiefs", "pre_close": {"ts": "2026-10-04T20:21:01Z", "group_name": "Money Line", "label": "KC Chiefs", "odds_dec": 2.9, "odds_frac": "19/10", "suspended": false} }, &hellip; ] } Each selection row, and the pre_close and last inside it, carry the same identity fields as /odds : group_name , label , and side , line , handicap and n2 on the markets that use them (for example a totals leg carries "side": "O", "line": "2.5" ). So a row maps to a team, side and line on its own, with no second call to /odds . Fields are present only when they have a value. pre_close_basis tells you how the close was picked: kickoff (last price at or before the scheduled start), prematch-records (last price under the pre-match id, when the start time isn't known) or omitted (no pre-match close is reported, because we only saw the match in play or recorded no price before the scheduled start). When the basis is omitted the selections have no pre_close . closed is false for a match that has not started yet. Its pre_close is then just the current pre-match price and will keep moving until kickoff, so wait for closed to turn true (the match has kicked off, gone in play, or finished) before you treat a pre_close as the settled close. Measure your CLV Closing line value is how the price you took compares with the close. Beating the close consistently is the standard sign of a winning bettor. Save the sel_id and price when you bet, then after kickoff: import requests closing = requests.get("https://moviodds.com/closing", params={"fi": "201714836"}, timeout=30).json() close = {s["sel_id"]: s["pre_close"]["odds_dec"] for s in closing["selections"] if "pre_close" in s} my_bets = [("59223458", 2.80)] # (sel_id, decimal price you took) for sel, taken in my_bets: print(sel, "took", taken, "closed", close[sel], "CLV %+.1f%%" % ((taken / close[sel] - 1) * 100)) 59223458 took 2.8 closed 2.9 CLV -3.4% To see how a price got to its close, pull its full timeline from historical odds . FAQ Is the bet365 closing line API free? Yes. No sign-up and no key. /closing allows 120 requests per minute per IP. What counts as the closing line? The last price we recorded for a selection before the scheduled kickoff, taken from the pre-match market. Which sports have closing lines? All 24 we cover, including soccer, NFL, NBA, NHL, MLB, tennis, cricket and esports. Every market, including spreads, totals and player props. How far back does it go? Matches recorded since September 2026. Are these really bet365 odds? Yes, only bet365's own prices. MoviOdds is an independent project and is not affiliated with bet365. More: historical odds &middot; live WebSocket &middot; all 24 sports &middot; Python client &middot; API docs MoviOdds is an independent project. The odds served here are exclusively bet365 odds. Not affiliated with or endorsed by bet365. Odds data is for informational use only. Questions or custom work: Discord . 

### page https://moviodds.com/docs/markets/
status=200

 bet365 Soccer Markets in the API: Every Market Covered | MoviOdds MoviOdds Docs API docs Sports WebSocket Bet Builder Python moviodds.com Markets Overview Match result Goals and goal lines Handicaps Correct score and combos Corners Cards Shots, offsides, tackles Penalties and more Player markets In-play only Using them in the API bet365 soccer markets in the API If bet365 prices a soccer market, the API returns it. Overview The API returns every market bet365 lists for a match, including the ones behind collapsed headers on bet365's own page, all from the same endpoints. The odds are exclusively bet365 odds. What you get depends on the match. A lower-league game might have 15 to 20 markets; a big league match often has 40 or more. Every market below has appeared in the feed. Names are exactly as bet365 shows them. This page lists soccer. Tennis, basketball, the NFL, NHL and 20 more sports are covered too: see every sport . Need a market that isn't here? Message @Movisu on Discord. Match result Full Time Result (1X2) Double Chance Draw No Bet Half Time Result Half Time Double Chance Half Time/Full Time To Win 2nd Half 10 Minute Result Method of Victory, To Qualify, Game Won In Extra Time, Game Won After Penalties (cup matches) Goals and goal lines Goal Line and Alternative Total Goals (every over/under line bet365 offers) Match Goals Range Goals Odd/Even Both Teams to Score, in the 1st Half and in the 2nd Half Team Total Goals (over/under for each team) Team Goals Range and each team's Exact Goals Team Clean Sheet Team to Score in Both Halves, Team to Score in 2nd Half, To Score In Half 1st Half Goals, 1st Half Goal Line, 1st Half Goals Range, 2nd Half Goals Range Last Team to Score Handicaps Asian Handicap, with alternative lines Handicap Result (3-way) and Alternative Handicap Result Handicap 2-Way 1st Half Asian Handicap and 1st Half Handicap Correct score and combos Correct Score and Half Time Correct Score Match Result / Both Teams To Score Match Result / Total Goals Total Goals / Both Teams To Score Double Chance / Goals Range and Result / Goals Range Corners Match Corners, Total Corners and Alternative Corners Asian Corners and 1st Half Asian Corners Corners 2-Way 1st Half Corners and 2nd Half Corners Team Corners Corners Race Cards Number of Cards in Match and Cards (over/under) Both Teams to Receive Cards Card Handicap, Asian Handicap Cards and Asian Total Cards Team Cards First Card Received and Time of First Card Red Card in Match/Half Shots, fouls, offsides and tackles Match Shots and Match Shots on Target (over/under) Team Shots and Team Shots on Target Team to Get Most (shots, shots on target, corners, cards and more) Fouls Committed and To Be Fouled Match Offsides and Team Offsides Match Tackles, Team Tackles and Tackles bet365 lists these on its Other, Shots, Cards/Fouls and Player Stats tabs and usually prices them in the last hours before kickoff, mostly on bigger matches. A match far from kickoff may list none of them yet. Their group ids: Market group_id Match Shots 50528 Match Shots on Target 50527 Team Shots 50532 Team Shots on Target 50530 Team to Get Most 177790 Match Offsides 50559 Team Offsides 50536 Match Tackles 50529 Team Tackles 50534 Fouls Committed 177759 To Be Fouled 177868 Penalties and other markets To Score a Penalty, To Miss a Penalty and A Penalty in the Match Own Goal First Team to Score Goals Odd/Even, plus each half's and each team's Odd/Even 10 Minute Result and First 10 Minutes Team Performances Player markets Goalscorers (first, last and anytime) Multi Scorers (2 or more, 3 or more) Score, Assist, Score or Assist Player Shots and Shots on Target (1+ up to 6+) Goalkeeper Saves bet365 prices the goalscorer and multi scorer markets on matches it covers in depth, such as major leagues and internationals, and fills them in as kickoff gets closer. Smaller competitions may list only Score or Assist, or no player markets at all. Each goalscorer quote carries the player in the line field, the bet type (Anytime, First or Last) in side, and the player's team in n2. bet365 also lists one-off Specials on some matches; those come through too. In-play only Once a match kicks off, bet365 opens markets that only make sense live. The API streams these over the WebSocket as they change: Next goal (1st Goal, 2nd Goal, 3rd Goal and so on) Asian Handicap and Goal Line from the current score, e.g. Asian Handicap (1-0) 1st Half Asian Handicap and 1st Half Goal Line from the current score First 10 Minutes Using them in the API Every price carries a group_name (the market name above) and a group_id . The id stays the same across matches and languages, so filter on that. For example, Full Time Result is 40 before kickoff and 1777 once the match is in play. curl "https://moviodds.com/odds?groups=40,1777" Each match also has a market_count , the number of markets priced for it right now. See the API docs for loading the board and streaming changes, and the Bet Builder docs for pricing several legs together. MoviOdds is an independent project. The odds served here are exclusively bet365 odds. Not affiliated with or endorsed by bet365. Odds data is for informational use only. 

### MovioOdds health
`https://moviodds.com/health`

status=200 bytes=1329 secs=0.1 ratelimit={}
```
{
 "cache_fixtures": 3002,
 "cache_quotes": 503532,
 "cached_fixtures": 47,
 "catalog_fixtures": 3107,
 "catalog_sweeps": 1825,
 "changes_published": 2699335,
 "last_change_unix": 1792454566,
 "last_fixture_seen_by_sport": {
  "american_football": "2026-10-20T00:00:16.874817306Z",
  "australian_rules": "2026-10-20T00:01:01.714344793Z",
  "badminton": "2026-10-20T00:02:03.036290946Z",
  "bandy": "2026-10-19T12:08:52.612171632Z",
  "baseball": "2026-10-20T00:00:40.85156379Z",
  "basketball": "2026-10-19T23:59:49.063863812Z",
  "boxing": "2026-10-20T00:00:16.760253174Z",
  "cricket": "2026-10-20T00:02:07.968309116Z",
  "darts": "2026-10-20T00:00:46.796725631Z",
  "esports": "2026-10-20T00:01:01.303912609Z",
  "floorball": "2026-10-19T20:50:55.588340471Z",
  "gaelic_sports": "2026-10-20T00:00:07.373318417Z",
  "handball": "2026-10-20T00:01:35.927454758Z",
  "ice_hockey": "2026-10-20T00:00:15.915537565Z",
  "mma": "2026-10-20T00:00:35.140987882Z",
  "rugby_league": "2026-10-20T00:02:46.832728213Z",
  "rugby_union": "2026-10-20T00:02:36.926547137Z",
  "snooker": "2026-10-20T00:00:59.787534809Z",
  "soccer": "2026-10-20T00:02:26.836721686Z",
  "table_tennis": "2026-10-20T00:00:58.657007761Z",
  "tennis": "2026-10-20T00:01:54.163897694Z",
  "volleyball": "2026-10-20T00:01:30.386616582Z"
 },
 "odds_raw": {
  "served": 87,
  "rate_limited": 4,
  "busy": 0,
  "in_flight": 0,
  "max_in_flight": 4,
  "gzip_required_mode": false
 },
 "status": "ok",
 "warming": false
}
```

### MovioOdds NBA odds
`https://moviodds.com/odds?sport=basketball`

status=200 bytes=8115727 secs=0.8 ratelimit={}
```
{
 "keys": [
  "cached_matches",
  "catalog_matches",
  "generated_at",
  "match_count",
  "matches",
  "quote_count",
  "server_time"
 ],
 "n": 182,
 "leagues": [
  "Adriatic League Div 2",
  "Argentina LLF Women",
  "Argentina La Liga",
  "Argentina La Liga Proximo",
  "Argentina Liga Nacional",
  "Australia NBL",
  "Australia WNBL",
  "Bahrain Premier League",
  "Basketball Champions League",
  "Brazil Camp.Carioca U22",
  "Brazil NBB",
  "China CBA",
  "Club Friendlies",
  "Colombia Liga",
  "Ebasketball H2H GG League - 4x5mins",
  "Ecuador LBP",
  "Euro Cup",
  "Euroleague",
  "France Ligue B",
  "France Nationale 1",
  "Georgia League U22",
  "Greece Basket League",
  "Greece Elite League",
  "Hong Kong BL",
  "Hong Kong Silver Shield Cup Women",
  "Hungary NB 1.A",
  "Israel National League",
  "Italy Lega 1",
  "Korea KBL",
  "Latvia-Estonia BL"
 ],
 "m0": {
  "id": "202925902",
  "home": "Bigua",
  "away": "Hebraica Macabi",
  "league": "Uruguay Liga",
  "region": "Uruguay Liga",
  "in_play": true,
  "inplay_nav_id": "152031300915C18",
  "entry_tab": "0",
  "score": "86-84",
  "clock": {
   "min": 0,
   "sec": 50,
   "ticking": false,
   "ref": "2026-10-20T00:02:25Z"
  },
  "last_live_seen": "2026-10-20T00:02:26.884708796Z",
  "sport": "basketball",
  "competition_id": "21173438",
  "coupon_event_id": "26990665",
  "last_seen": "2026-10-19T23:59:49.063863812Z",
  "discovery_source": "prematch-list",
  "kickoff_utc": "2026-10-19T22:15:00Z",
  "quotes": [
   {
    "fixture_id": "202925902",
    "group_id": "112",
    "group_name": "Game",
    "market_id": "1446",
    "sel_id": "249999854",
    "label": " -2.5",
    "handicap": "-2.5",
    "side": "Bigua",
    "line": "Line",
    "odds_dec": 1.7407407407407407,
    "odds_frac": "20/27",
    "suspended": true,
    "ts": "2026-10-19T23:59:52.654923978Z",
    "phase": "inplay"
   },
   {
    "fixture_id": "202925902",
    "group_id": "112",
    "group_name": "Game",
    "market_id": "1446",
    "sel_id": "249999856",
    "label": " +2.5",
    "handicap": "+2.5",
    "side": "Hebraica Macabi",
    "line": "Line",
    "odds_dec": 1.9523809523809523,
    "odds_frac": "20/21",
    "suspended": true,
    "ts": "2026-10-19T23:59:52.654923978Z",
    "phase": "inplay"
   },
   {
    "fixture_id": "202925902",
    "group_id": "112",
    "group_name": "Game",
    "market_id": "180032",
    "sel_id": "249999882",
    "side": "Bigua",
    "line": "To Win",
    "odds_dec": 1.2777777777777777,
    "odds_frac": "5/18",
    "suspended": true,
    "ts": "2026-10-20T00:01:18.536858071Z",
    "phase": "inplay"
   },
   {
    "fixture_id": "202925902",
    "group_id": "112",
    "group_name": "Game",
    "market_id": "180032",
    "sel_id": "249999887",
    "side": "Hebraica Macabi",
    "line": "To Win",
    "odds_dec": 3.4,
    "odds_frac": "12/5",
    "suspended": true,
    "ts": "2026-10-20T00:01:18.536858071Z",
    "phase": "inplay"
   }
  ],
  "market_count": 1,
  "polled_at": "2026-10-20T00:02:45.427960207Z"
 }
}
```
NBA matches: 42

### MovioOdds match all markets
`https://moviodds.com/odds?sport=basketball&match=202991767`

status=429 bytes=220 secs=0.1 ratelimit={}
body head: {"error":"raw_rate_limited","message":"Uncompressed responses this big are limited to one per minute per IP. Send Accept-Encoding: gzip to skip this limit (about 13x smaller and faster). Docs: https://moviodds.com/doc"} 

### MovioOdds match markets (id param)
`https://moviodds.com/odds/202991767`

status=404 bytes=548 secs=0.3 ratelimit={}
body head: <html> <head><title>404 Not Found</title></head> <body> <center><h1>404 Not Found</h1></center> <hr><center>nginx</center> </body> </html> <!-- a padding to disable MSIE and Chrome friendly error page --> <!-- a padding to disable MSIE and Chrome friendly error page --> <!-- a padding to di

### MovioOdds history
`https://moviodds.com/history?match=202991767`

status=400 bytes=73 secs=0.1 ratelimit={}
body head: {"error":"query param 'fi' is required and must be a numeric fixture id"}

### MovioOdds closing
`https://moviodds.com/closing?sport=basketball`

status=400 bytes=73 secs=0.1 ratelimit={}
body head: {"error":"query param 'fi' is required and must be a numeric fixture id"}

### MovioOdds results
`https://moviodds.com/results?sport=basketball`

status=200 bytes=2515580 secs=0.7 ratelimit={}
```
{
 "sport": "basketball",
 "count": 5918,
 "results": [
  {
   "fixture_id": "203182883",
   "sport": "basketball",
   "home": "NY Knicks (RADIANT)",
   "away": "OKC Thunder (SIGNAL)",
   "league": "Ebasketball H2H GG League - 4x5mins",
   "final_score": "49-53",
   "periods": [
    {
     "name": "Quarter 1",
     "score": "11-11"
    },
    {
     "name": "Quarter 2",
     "score": "10-19"
    },
    {
     "name": "Quarter 3",
     "score": "12-9"
    },
    {
     "name": "Quarter 4",
     "score": "16-14"
    }
   ],
   "status": "finished",
   "finished_at": "2026-10-19T23:56:29.506591Z",
   "updated_at": "2026-10-19T23:58:30.160769Z"
  },
  {
   "fixture_id": "203201113",
   "sport": "basketball",
   "home": "MEM Grizzlies (ADMIRAL)",
   "away": "PHX Suns (BLADE)",
   "league": "Ebasketball H2H GG League - 4x5mins",
   "final_score": "54-44",
   "periods": [
    {
     "name": "Quarter 1",
     "score": "13-7"
    },
    {
     "name": "Quarter 2",
     "score": "16-10"
    },
    {
     "name": "Quarter 3",
     "score": "10-8"
    },
    {
     "name": "Quarter 4",
     "score": "15-19"
    }
   ],
   "status": "finished",
   "finished_at": "2026-10-19T23:53:29.497891Z",
   "updated_at": "2026-10-19T23:55:29.530631Z"
  },
  {
   "fixture_id": "203182880",
   "sport": "basketball",
   "home": "MIA Heat (DOMAIN)",
   "away": "TOR Raptors (INVINCIBLE)",
   "league": "Ebasketball H2H GG League - 4x5mins",
   "final_score": "52-53",
   "periods": [
    {
     "name": "Quarter 1",
     "score": "16-11"
    },
    {
     "name": "Quarter 2",
     "score": "6-12"
    },
    {
     "name": "Quarter 3",
     "score": "20-17"
    },
    {
     "name": "Quarter 4",
     "score": "10-13"
    }
   ],
   "status": "finished",
   "finished_at": "2026-10-19T23:49:29.496714Z",
   "updated_at": "2026-10-19T23:51:29.531842Z"
  },
  {
   "fixture_id": "203196488",
   "sport": "basketball",
   "home": "TOR Raptors (DAGGER)",
   "away": "CHI Bulls (RAPTOR)",
   "league": "Ebasket
```

2008-03-01 event 280301019: odds providers (name, details, total, homeML, has_open, has_close) = []; ESPN BET propBets count=None

2009-03-01 event 290301002: odds providers (name, details, total, homeML, has_open, has_close) = []; ESPN BET propBets count=None

2010-03-01 event 300301005: odds providers (name, details, total, homeML, has_open, has_close) = []; ESPN BET propBets count=None

2011-03-01 event 310301011: odds providers (name, details, total, homeML, has_open, has_close) = []; ESPN BET propBets count=None

2012-03-01 event 320301019: odds providers (name, details, total, homeML, has_open, has_close) = []; ESPN BET propBets count=None

2013-03-01 event 400278584: odds providers (name, details, total, homeML, has_open, has_close) = [('consensus', 'IND -2.5', None, None, False, False), ('numberfire', 'IND -1.5', 185.0, 105, False, False), ('teamrankings', 'IND -2', 185.5, 116, False, False)]; ESPN BET propBets count=None

2014-03-01 event 400489747: odds providers (name, details, total, homeML, has_open, has_close) = [('5Dimes.eu', 'MIA -14', 199.0, -1600, False, False), ('BETONLINE.ag', 'MIA -14.5', 199.0, -2200, False, False), ('BOVADA.lv', 'MIA -14.5', 199.0, 0, False, False), ('Fantasy911.com', 'MIA -14.5', 199.5, -2500, False, False), ('Opening', 'MIA -13.5', 201.0, -2000, False, False), ('SportsBetting.ag', 'MIA -14.5', 199.0, -2200, False, False), ('consensus', 'MIA -13.5', None, None, False, False), ('numberfire', 'MIA -14', 199.0, -2500, False, False), ('teamrankings', 'MIA -14', 199.5, -2300, False, False)]; ESPN BET propBets count=None

2015-03-01 event 400579169: odds providers (name, details, total, homeML, has_open, has_close) = [('5Dimes.eu', 'LAC -2', 197.5, 120, False, False), ('BETONLINE.ag', 'LAC -2', 197.5, 115, False, False), ('BOVADA.lv', 'LAC -2.5', 198.0, 0, False, False), ('Fantasy911.com', 'LAC -2.5', 197.0, 115, False, False), ('Opening', 'CHI -1', 201.0, 100, False, False), ('SportsBetting.ag', 'LAC -2', 197.5, 115, False, False), ('consensus', 'CHI -2.5', None, None, False, False), ('numberfire', 'LAC -1.5', 197.0, 111, False, False), ('teamrankings', 'LAC -2', 197.5, 113, False, False)]; ESPN BET propBets count=None

2016-03-01 event 400828778: odds providers (name, details, total, homeML, has_open, has_close) = [('5Dimes.eu', 'CHA -12.5', 210.0, -1100, False, False), ('BETONLINE.ag', 'CHA -12.5', 209.5, -1050, False, False), ('BOVADA.lv', 'CHA -12.5', 210.0, 0, False, False), ('Opening', 'CHA -12.5', 206.5, -1450, False, False), ('PinnacleSports.com', 'CHA -13', 209.5, -1300, False, False), ('SportsBetting.ag', 'CHA -12.5', 209.5, -1050, False, False), ('Westgate', 'CHA -12.5', 210.0, -1300, False, False), ('consensus', 'CHA -12.5', None, None, False, False), ('teamrankings', 'CHA -12.5', 209.5, -1200, False, False)]; ESPN BET propBets count=None

2017-03-01 event 400899364: odds providers (name, details, total, homeML, has_open, has_close) = [('5Dimes.eu', 'ORL -2', 216.0, -125, False, False), ('BETNOW.eu', 'ORL -2', 216.0, -125, False, False), ('BETONLINE.ag', 'ORL -2.5', 215.0, -135, False, False), ('BOVADA.lv', 'ORL -2', 216.0, -130, False, False), ('BetUS.COM', 'ORL -2', 216.0, -130, False, False), ('Opening', 'ORL -2.5', 215.0, -120, False, False), ('SportsBetting.ag', 'ORL -2.5', 215.0, -135, False, False), ('SportsInteraction.com', 'ORL -2', 214.5, -130, False, False), ('Sportsbook.com', 'ORL -2', 215.5, -130, False, False), ('Westgate', 'ORL -2.5', 216.0, -135, False, False), ('consensus', 'ORL -2.5', None, None, False, False), ('numberfire', 'ORL -2.5', 215.0, -135, False, False), ('teamrankings', 'ORL -2', 216.0, -131, False, False)]; ESPN BET propBets count=None

2018-03-01 event 400975668: odds providers (name, details, total, homeML, has_open, has_close) = [('Bet 365', None, None, None, False, False), ('CG Technology', 'MIA -5.5', 218.0, -225, False, False), ("Caesar's", 'MIA -5.5', 218.0, -220, False, False), ('Caesars Sportsbook', 'MIA -5', 217.5, -200, False, False), ('Unibet', 'MIA -4.5', 215.5, -222, False, False), ('Westgate', 'MIA -5.5', 218.5, -220, False, False), ('Wynn', 'MIA -5.5', 217.5, -210, False, False), ('accuscore', 'MIA -5.5', 218.5, -227, False, False), ('consensus', 'MIA -5.5', 217.5, -217, False, False), ('numberfire', 'MIA -5.5', 218.5, -221, False, False), ('teamrankings', 'MIA -5.5', 218.5, -213, False, False)]; ESPN BET propBets count=None

2019-03-01 event 401071601: odds providers (name, details, total, homeML, has_open, has_close) = [("Caesar's", 'EVEN', 230.0, -105, False, False), ('Caesars', 'EVEN', 230.0, -105, False, False), ('Caesars Sportsbook', 'EVEN', 230.0, -110, False, False), ('Unibet', 'ATL -2.5', 230.5, -122, False, False), ('Westgate', 'EVEN', 230.0, -105, False, False), ('Wynn', 'EVEN', 230.0, 0, False, False), ('accuscore', 'ATL -1', 230.5, -111, False, False), ('consensus', 'EVEN', 230.0, -110, False, False), ('numberfire', 'ATL -1', 229.5, -114, False, False), ('teamrankings', 'ATL -1', 230.0, -110, False, False)]; ESPN BET propBets count=None

2020-03-01 event 401161530: odds providers (name, details, total, homeML, has_open, has_close) = [('Caesars', 'ATL -2.5', 239.5, -140, False, False), ('Caesars Sportsbook', 'ATL -0.5', 61.5, -120, False, False), ('DraftKings', 'ATL -2.5', 237.5, -133, False, False), ('SugarHouse', 'ATL -2', 237.5, -133, False, False), ('Unibet', 'ATL -2.5', 237.5, -133, False, False), ('Westgate', 'ATL -2.5', 240.0, -135, False, False), ('accuscore', 'ATL -2.5', 240.0, -141, False, False), ('consensus', 'ATL -2.5', 240.0, -137, False, False), ('numberfire', 'ATL -2', 239.5, -124, False, False), ('teamrankings', 'ATL -2', 238.5, -126, False, False)]; ESPN BET propBets count=None

2021-03-01 event 401267689: odds providers (name, details, total, homeML, has_open, has_close) = [('BetfairSportsbook', 'DAL -6.5', 220.0, 210, False, False), ('Caesars', 'DAL -7', 220.0, 230, False, False), ('Caesars (New Jersey) - Live Odds', 'DAL -11.5', None, 750, False, False), ('Caesars Sportsbook', 'DAL -6.5', 220.0, 230, False, False), ('Caesars Sportsbook (New Jersey)', 'DAL -7', 220.0, 235, False, False), ('Caesars Sportsbook (New Jersey) - Live Odds', 'DAL -9.5', 247.5, 2500, False, False), ('Caesars Sportsbook (Pennsylvania)', 'DAL -7', 220.0, 230, False, False), ('DraftKings', 'DAL -7', 220.0, 250, False, False), ('MGM', 'DAL -7', 219.5, 240, False, False), ('Unibet', 'DAL -6.5', 225.5, 250, False, False), ('Westgate', 'DAL -7', 220.0, 235, False, False), ('accuscore', 'DAL -7', 220.0, 230, False, False), ('consensus', 'DAL -7', 220.0, 236, False, False), ('numberfire', 'DAL -6.5', 220.0, 225, False, False), ('teamrankings', 'DAL -6.5', 220.0, 225, False, False)]; ESPN BET propBets count=None

2022-03-01 event 401360745: odds providers (name, details, total, homeML, has_open, has_close) = [('Caesars Sportsbook', 'WSH -3', 217.5, -155, False, False), ('Caesars Sportsbook (Colorado)', 'WSH -3', 217.5, -150, False, False), ('Caesars Sportsbook (New Jersey)', 'WSH -3', 217.5, -150, False, False), ('Caesars Sportsbook (New Jersey) - Live Odds', 'WSH -3.5', 232.5, -1600, False, False), ('Caesars Sportsbook (Pennsylvania)', 'WSH -3', 217.5, -155, False, False), ('DraftKings', 'WSH -3', 217.5, -155, False, False), ('Holland Casino', 'WSH -3', 217.5, -154, False, False), ('MGM', 'WSH -3.5', 217.5, -145, False, False), ('PointsBet', 'WSH -3', 217.5, -150, False, False), ('SugarHouse', 'WSH -4.5', 218.5, -167, False, False), ('Titanbets', 'WSH -3', 217.5, -154, False, False), ('Unibet', 'WSH -4.5', 218.5, -167, False, False), ('Westgate', 'WSH -3', 217.5, -150, False, False), ('accuscore', 'WSH -3', 217.5, -150, False, False), ('consensus', 'WSH -3', 217.5, -157, False, False), ('teamrankings', 'WSH -3', 217.5, -150, False, False)]; ESPN BET propBets count=None

2023-03-01 event 401469088: odds providers (name, details, total, homeML, has_open, has_close) = [('BetfairSportsbook', 'PHX -10.5', 228.5, 400, False, False), ('Caesars Sportsbook', 'PHX -10.5', 228.0, 400, False, False), ('Caesars Sportsbook (Colorado)', 'PHX -10.5', 228.0, 400, False, False), ('Caesars Sportsbook (New Jersey)', 'PHX -10.5', 228.0, 400, False, False), ('Caesars Sportsbook (New Jersey) - Live Odds', 'PHX -13.5', 195.5, 2500, False, False), ('Caesars Sportsbook (Tennessee)', 'PHX -10.5', 228.0, 366, False, False), ('DraftKings', 'PHX -10.5', 229.0, 410, False, False), ('ESPN BET', 'PHX -10.5', 229.5, 400, False, True), ('Holland Casino', 'PHX -10.5', 228.5, 400, False, False), ('MGM', 'PHX -10.5', 228.5, 400, False, False), ('PointsBet', 'PHX -10.5', 229.0, 375, False, False), ('SugarHouse', 'PHX -10.5', 228.0, 410, False, False), ('Titanbets', 'PHX -10.5', 229.0, 400, False, False), ('Unibet', 'PHX -9.5', 225.5, 410, False, False), ('accuscore', 'PHX -10.5', 228.5, 400, False, False), ('consensus', 'PHX -10.5', 228.5, 395, False, False), ('teamrankings', 'PHX -10.5', 229.0, 383, False, False)]; ESPN BET propBets count=None

2024-03-01 event 401585485: odds providers (name, details, total, homeML, has_open, has_close) = [('BetfairSportsbook', 'CLE -7', 219.0, 210, True, True), ('Caesars Sportsbook (Colorado)', 'CLE -7', 219.0, 222, True, True), ('Caesars Sportsbook (New Jersey)', 'CLE -7', 219.0, 222, True, True), ('Caesars Sportsbook (New Jersey) - Live Odds', 'CLE -22.5', 226.5, 2200, True, False), ('Caesars Sportsbook (Tennessee)', 'CLE -7', 219.0, 222, True, True), ('DraftKings', 'CLE -7', 219.0, 220, True, True), ('ESPN BET', 'CLE -6.5', 219.5, 220, True, True), ('MGM', 'CLE -6.5', 219.5, 240, True, True), ('SugarHouse', 'CLE -7', 218.5, 245, True, True), ('Titanbets', 'CLE -7', 219.0, 220, True, True), ('Unibet', 'CLE -9.5', 222.5, 235, True, True), ('accuscore', 'CLE -7', 219.0, 225, True, True)]; ESPN BET propBets count=228

2025-03-01 event 401705426: odds providers (name, details, total, homeML, has_open, has_close) = [('ESPN BET', 'CHA -3.5', 226.5, -175, True, True), ('ESPN Bet - Live Odds', 'WSH -13.5', 211.5, None, True, False)]; ESPN BET propBets count=1613

2026-03-01 event 401810723: odds providers (name, details, total, homeML, has_open, has_close) = [('Draft Kings', 'SA -1.5', 227.5, -102, True, True)]; ESPN BET propBets count=None

### ESPN core odds upcoming
`https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba/events/401909834/competitions/401909834/odds`

status=200 bytes=5859 secs=0.2 ratelimit={}
```
[
 [
  "100",
  "Draft Kings",
  "ORL -2.5",
  235.5,
  -105.0,
  -142,
  120
 ]
]
```

### ESPN propBets upcoming provider 100
`https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba/events/401909834/competitions/401909834/odds/100/propBets?limit=3`

status=200 bytes=2359 secs=0.2 ratelimit={}
```
{
 "count": 825,
 "types": [
  {
   "id": "1",
   "name": "Total Points"
  },
  {
   "id": "1",
   "name": "Total Points"
  },
  {
   "id": "1",
   "name": "Total Points"
  }
 ]
}
```

### ESPN propBets upcoming provider 58
`https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba/events/401909834/competitions/401909834/odds/58/propBets?limit=3`

status=404 bytes=90 secs=0.2 ratelimit={}
body head: {"error":{"message":"No propBets found for eventId 401909834 and provider 58","code":404}}

### ESPN propBets upcoming provider 2000
`https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba/events/401909834/competitions/401909834/odds/2000/propBets?limit=3`

status=404 bytes=92 secs=0.2 ratelimit={}
body head: {"error":{"message":"No propBets found for eventId 401909834 and provider 2000","code":404}}

### ESPN propBets upcoming provider 40
`https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba/events/401909834/competitions/401909834/odds/40/propBets?limit=3`

status=404 bytes=90 secs=0.2 ratelimit={}
body head: {"error":{"message":"No propBets found for eventId 401909834 and provider 40","code":404}}

### ESPN core movement upcoming
`https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba/events/401909834/competitions/401909834/odds/100/history/0/movement?limit=20`

status=200 bytes=64 secs=0.2 ratelimit={}
```
{
 "count": 0,
 "pageIndex": 0,
 "pageSize": 25,
 "pageCount": 0,
 "items": []
}
```

### ESPN athlete gamelog
`https://site.web.api.espn.com/apis/common/v3/sports/basketball/nba/athletes/3112335/gamelog?season=2025`

status=200 bytes=855290 secs=0.5 ratelimit={}
```
{
 "keys": [
  "filters",
  "labels",
  "names",
  "displayNames",
  "events",
  "seasonTypes",
  "glossary"
 ],
 "labels": [
  "MIN",
  "FG",
  "FG%",
  "3PT",
  "3P%",
  "FT",
  "FT%",
  "REB",
  "AST",
  "BLK",
  "STL",
  "PF",
  "TO",
  "PTS"
 ],
 "n_events": 90
}
```

### ESPN season-wide scoreboard via calendar
`https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates=20250301&limit=100&groups=`

status=200 bytes=86661 secs=0.3 ratelimit={}
```
[
 "2024-10-04T07:00Z",
 "2024-10-05T07:00Z",
 "2024-10-06T07:00Z",
 "2024-10-07T07:00Z",
 "2024-10-08T07:00Z"
]
```
