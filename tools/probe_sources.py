"""Probe candidate free data sources from a GitHub Actions runner.

Prints a short, structured summary per endpoint: HTTP status, size, top-level
keys and a few sample values. Never prints secrets; uses no keys. Output is
written to reports/source_probe.md so the evidence is kept in git.
"""
import json, sys, time, urllib.request, urllib.error, re, datetime as dt

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
OUT = []


def get(url, headers=None, timeout=25):
    h = {"User-Agent": UA, "Accept": "application/json,text/html,*/*"}
    h.update(headers or {})
    req = urllib.request.Request(url, headers=h)
    t = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read()
            return r.status, body, time.time() - t, dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:2000], time.time() - t, dict(e.headers or {})
    except Exception as e:  # network / DNS / timeout
        return None, repr(e).encode(), time.time() - t, {}


def log(s=""):
    print(s)
    OUT.append(s)


def probe(name, url, headers=None, show=None):
    code, body, secs, hdr = get(url, headers)
    log(f"\n### {name}\n`{url}`\n\nstatus={code} bytes={len(body)} secs={secs:.1f} "
        f"ratelimit={ {k: v for k, v in hdr.items() if 'limit' in k.lower() or 'remaining' in k.lower()} }")
    data = None
    if code == 200:
        try:
            data = json.loads(body)
        except Exception:
            log("not json; head: " + body[:300].decode("utf8", "replace").replace("\n", " "))
            return code, body
        if show:
            try:
                log("```\n" + show(data)[:3500] + "\n```")
            except Exception as e:
                log(f"show() failed: {e!r}; keys={list(data)[:20] if isinstance(data, dict) else type(data)}")
        else:
            log(f"keys={list(data)[:25] if isinstance(data, dict) else type(data).__name__}")
    else:
        log("body head: " + body[:300].decode("utf8", "replace").replace("\n", " "))
    return code, data


def j(x, n=1500):
    return json.dumps(x, indent=1, default=str)[:n]


def main():
    log(f"# Source probe {dt.datetime.utcnow():%Y-%m-%d %H:%M} UTC (GitHub Actions runner)")
    # --- NBA CDN
    code, sched = probe("NBA CDN schedule", "https://cdn.nba.com/static/json/staticData/scheduleLeagueV2.json",
        show=lambda d: j({"season": d["leagueSchedule"]["seasonYear"],
                          "dates": len(d["leagueSchedule"]["gameDates"]),
                          "first_game": d["leagueSchedule"]["gameDates"][0]["games"][0]}, 2500))
    probe("NBA CDN today scoreboard", "https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json",
        show=lambda d: j({"date": d["scoreboard"]["gameDate"], "n": len(d["scoreboard"]["games"]),
                          "g0": d["scoreboard"]["games"][:1]}, 2000))
    probe("NBA CDN odds (todaysOddsData)", "https://cdn.nba.com/static/json/liveData/odds/odds_todaysGames.json",
        show=lambda d: j(d, 2500))
    probe("stats.nba.com leaguegamelog", "https://stats.nba.com/stats/leaguegamelog?Counter=10&DateFrom=&DateTo=&Direction=ASC&LeagueID=00&PlayerOrTeam=T&Season=2024-25&SeasonType=Regular%20Season&Sorter=DATE",
        headers={"Referer": "https://www.nba.com/", "Origin": "https://www.nba.com", "x-nba-stats-origin": "stats", "x-nba-stats-token": "true"},
        show=lambda d: j({"headers": d["resultSets"][0]["headers"], "rows": len(d["resultSets"][0]["rowSet"]), "r0": d["resultSets"][0]["rowSet"][0]}))
    # --- ESPN
    base = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"
    def sb_show(d):
        evs = d.get("events", [])
        res = {"n": len(evs)}
        if evs:
            c = evs[0]["competitions"][0]
            res["event0"] = {"id": evs[0]["id"], "date": evs[0]["date"], "name": evs[0]["name"],
                              "status": evs[0]["status"]["type"], "odds": c.get("odds"),
                              "competitors": [(x["team"]["abbreviation"], x.get("homeAway"), x.get("score")) for x in c["competitors"]]}
        return j(res, 3500)
    code, past = probe("ESPN scoreboard past (2025-03-01)", base + "/scoreboard?dates=20250301", show=sb_show)
    probe("ESPN scoreboard old (2019-01-15)", base + "/scoreboard?dates=20190115", show=sb_show)
    probe("ESPN scoreboard opening week (2026-10-21)", base + "/scoreboard?dates=20261021", show=sb_show)
    probe("ESPN scoreboard season range", base + "/scoreboard?dates=20241022-20241030&limit=300",
          show=lambda d: j({"n": len(d.get("events", []))}))
    if isinstance(past, dict) and past.get("events"):
        eid = past["events"][0]["id"]
        probe("ESPN summary (pickcenter, boxscore, injuries)", base + f"/summary?event={eid}",
              show=lambda d: j({"keys": list(d), "pickcenter": d.get("pickcenter"), "againstTheSpread": d.get("againstTheSpread"),
                                "box_players_team0": [s.get("labels") for s in d.get("boxscore", {}).get("players", [{}])[0].get("statistics", [])],
                                "injuries": (d.get("injuries") or [])[:1]}, 3500))
        core = f"https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba/events/{eid}/competitions/{eid}/odds"
        code, od = probe("ESPN core odds list", core, show=lambda d: j(d, 2500))
        if isinstance(od, dict) and od.get("items"):
            ref = od["items"][0].get("$ref", "")
            m = re.search(r"/odds/(\d+)", ref)
            if m:
                probe("ESPN core odds movement history", core + f"/{m.group(1)}/history/0/movement?limit=100", show=lambda d: j(d, 2500))
        probe("ESPN core player props (propBets)", f"https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba/events/{eid}/competitions/{eid}/odds/58/propBets?limit=50",
              show=lambda d: j(d, 1500))
    probe("ESPN injuries", base + "/injuries", show=lambda d: j({"n_teams": len(d.get("injuries", [])), "t0": (d.get("injuries") or [{}])[0]}, 2500))
    probe("ESPN teams", base + "/teams", show=lambda d: j(len(d["sports"][0]["leagues"][0]["teams"])))
    # --- odds providers
    for name, url in [
        ("MovioOdds home", "https://moviodds.com/"),
        ("MovioOdds docs", "https://moviodds.com/docs"),
        ("MovioOdds api", "https://moviodds.com/api"),
        ("MovioOdds terms", "https://moviodds.com/terms"),
        ("The Odds API (no key)", "https://api.the-odds-api.com/v4/sports"),
        ("balldontlie (no key)", "https://api.balldontlie.io/v1/teams"),
        ("basketball-reference robots", "https://www.basketball-reference.com/robots.txt"),
        ("NBA official injury report index", "https://official.nba.com/nba-injury-report-2025-26-season/"),
        ("FanDuel sportsbook (ON) public page", "https://on.sportsbook.fanduel.ca/navigation/nba"),
    ]:
        code, body = probe(name, url)
        if code == 200 and isinstance(body, (bytes, bytearray)):
            text = body.decode("utf8", "replace")
            links = sorted(set(re.findall(r'href="([^"]+)"', text)))[:60]
            log("links: " + ", ".join(links))
            if "movi" in url:
                log("text: " + re.sub(r"<[^>]+>", " ", re.sub(r"(?s)<script.*?</script>|<style.*?</style>", " ", text))[:3000].replace("\n", " "))
    open("reports/source_probe.md", "w").write("\n".join(OUT) + "\n")


if __name__ == "__main__":
    import os; os.makedirs("reports", exist_ok=True)
    main()
