"""Temporary: confirm ODDS_API_KEY works and show sample link formats (never prints the key)."""
import json, urllib.parse, urllib.request
from collections import Counter
from nbapicks.sources import oddsapi
from nbapicks.teams import from_name

key = oddsapi.api_key()
print("key present:", bool(key))
if not key:
    raise SystemExit(1)
evs = oddsapi.fetch_events(key)
print("events:", len(evs))
ev = sorted(evs, key=lambda e: e["commence_time"])[0]
print("event:", ev["away_team"], "@", ev["home_team"], ev["commence_time"])
url = f"{oddsapi.BASE}/events/{ev['id']}/odds?" + urllib.parse.urlencode(dict(
    apiKey=key, bookmakers="draftkings,fanduel", markets=",".join(oddsapi.MARKETS), oddsFormat="american",
    includeLinks="true", includeSids="true"))
with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "nba-picks"}), timeout=30) as r:
    print("credits last/used/remaining:", r.headers.get("x-requests-last"), r.headers.get("x-requests-used"), r.headers.get("x-requests-remaining"))
    d = json.loads(r.read())
for bm in d.get("bookmakers", []):
    print("\n==", bm["key"], "event link:", bm.get("link"), "sid:", bm.get("sid"))
    for m in bm.get("markets", []):
        oc = m.get("outcomes", [])
        print(" market", m["key"], "n", len(oc), "link:", m.get("link"), "sid:", m.get("sid"),
              "with link:", sum(1 for o in oc if o.get("link")))
        for o in oc[:2]:
            print("   ", json.dumps({k: o.get(k) for k in ("name", "description", "point", "price", "link", "sid")}))
p = oddsapi.parse_event_links(d, from_name(ev["home_team"]), from_name(ev["away_team"]))
print("\nparsed:", {b: dict(Counter(o["market"] for o in rows)) for b, rows in p.items()})
