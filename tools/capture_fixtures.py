"""Capture small real API responses as test fixtures (run on a GitHub runner).

Fixtures are trimmed copies of real responses so parsers are tested against the
true shape. Saved under reports/probe_fixtures/ (never over the pinned test fixtures in tests/fixtures/,
which tests assert exact values on). Copy a capture into tests/fixtures/ by hand when a parser changes.
No secrets involved.
"""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(__file__))
from probe_sources import get

D = os.environ.get("FIXTURE_DIR", "reports/probe_fixtures")
CORE = "https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba"
SITE = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"


def fetch(url):
    code, body, _, _ = get(url)
    print(code, url, len(body))
    if code != 200:
        return None
    return json.loads(body)


def save(name, obj):
    with open(f"{D}/{name}", "w") as f:
        json.dump(obj, f, indent=1)


def main():
    os.makedirs(D, exist_ok=True)
    save("espn_scoreboard_final_20250301.json", fetch(f"{SITE}/scoreboard?dates=20250301"))
    up = fetch(f"{SITE}/scoreboard?dates=20261021")
    save("espn_scoreboard_pre_20261021.json", up)
    ev_up = up["events"][0]["id"]
    save("espn_core_odds_pre.json", fetch(f"{CORE}/events/{ev_up}/competitions/{ev_up}/odds"))
    save("espn_core_odds_final_401705426.json", fetch(f"{CORE}/events/401705426/competitions/401705426/odds"))
    save("espn_core_odds_2019.json", fetch(f"{CORE}/events/401071601/competitions/401071601/odds"))
    props = fetch(f"{CORE}/events/{ev_up}/competitions/{ev_up}/odds/100/propBets?limit=1000")
    if props:
        types = {}
        for it in props["items"]:
            types.setdefault(it["type"]["name"], 0)
            types[it["type"]["name"]] += 1
        print("prop types", types)
        props["items"] = props["items"][:60]
        save("espn_propbets_pre.json", props)
        # one athlete ref to learn athlete shape
        ref = props["items"][0]["athlete"]["$ref"].replace("http://", "https://")
        save("espn_core_athlete.json", fetch(ref))
    inj = fetch(f"{SITE}/injuries")
    inj["injuries"] = inj["injuries"][:3]
    for t in inj["injuries"]:
        t["injuries"] = t["injuries"][:4]
    save("espn_injuries.json", inj)
    s = fetch(f"{SITE}/summary?event=401705426")
    save("espn_summary_final.json", {k: s.get(k) for k in ("boxscore", "header", "pickcenter", "injuries", "gameInfo")})
    time.sleep(3)
    mo = fetch("https://moviodds.com/odds?sport=basketball")
    if mo:
        nba = [m for m in mo["matches"] if m.get("league") == "NBA"]
        print("movi NBA", len(nba), [ (m["home"], m["away"], m["kickoff_utc"], m.get("market_count"), len(m.get("quotes", []))) for m in nba[:15]])
        groups = {}
        for m in nba:
            for q in m.get("quotes", []):
                groups.setdefault((q.get("group_id"), q.get("group_name")), 0)
                groups[(q.get("group_id"), q.get("group_name"))] += 1
        print("movi NBA groups", groups)
        save("moviodds_nba.json", {"generated_at": mo.get("generated_at"), "server_time": mo.get("server_time"), "matches": nba[:4]})
    time.sleep(5)
    res = fetch("https://moviodds.com/results?sport=basketball")
    if res:
        keys = list(res)
        items = res.get("results") or res.get("matches") or []
        nba = [r for r in items if "NBA" in json.dumps(r)][:5]
        save("moviodds_results_nba.json", {"keys": keys, "sample": nba or items[:3]})


if __name__ == "__main__":
    main()
