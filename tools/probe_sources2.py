"""Second probe: MovioOdds NBA endpoints and docs, ESPN historical odds depth,
current-season providers and props. Writes reports/source_probe2.md."""
import json, re, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from probe_sources import get, OUT, log, probe, j

CORE = "https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba"
SITE = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"


def text(url, n=6000):
    code, body, secs, _ = get(url)
    t = body.decode("utf8", "replace")
    t = re.sub(r"(?s)<script.*?</script>|<style.*?</style>", " ", t)
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"\s+", " ", t)
    log(f"\n### page {url}\nstatus={code}\n\n{t[:n]}")


def main():
    log("# Source probe 2")
    for p in ["/doc", "/bet365-nba-odds-api/", "/bet365-historical-odds-api/", "/bet365-closing-line-odds/", "/docs/markets/"]:
        text("https://moviodds.com" + p, 7000)
    probe("MovioOdds health", "https://moviodds.com/health", show=lambda d: j(d))
    code, d = probe("MovioOdds NBA odds", "https://moviodds.com/odds?sport=basketball",
                    show=lambda d: j({"keys": list(d), "n": len(d.get("matches", [])),
                                      "leagues": sorted({m.get("league") for m in d.get("matches", [])})[:30],
                                      "m0": d.get("matches", [None])[0]}, 3500))
    nba = [m for m in (d or {}).get("matches", []) if "NBA" in str(m.get("league", ""))]
    log(f"NBA matches: {len(nba)}")
    if nba:
        mid = nba[0]["id"]
        probe("MovioOdds match all markets", f"https://moviodds.com/odds?sport=basketball&match={mid}",
              show=lambda d: j(d, 3500))
        probe("MovioOdds match markets (id param)", f"https://moviodds.com/odds/{mid}", show=lambda d: j(d, 3500))
        probe("MovioOdds history", f"https://moviodds.com/history?match={mid}", show=lambda d: j(d, 2000))
    probe("MovioOdds closing", "https://moviodds.com/closing?sport=basketball", show=lambda d: j(d, 2000))
    probe("MovioOdds results", "https://moviodds.com/results?sport=basketball", show=lambda d: j(d, 2000))

    # ESPN: historical odds depth, one game near 1 March of each season
    for season_end in range(2008, 2027):
        code, body, _, _ = get(f"{SITE}/scoreboard?dates={season_end}0301")
        try:
            ev = json.loads(body)["events"][0]["id"]
        except Exception:
            log(f"\n{season_end}: no scoreboard ({code})"); continue
        code, body, _, _ = get(f"{CORE}/events/{ev}/competitions/{ev}/odds")
        try:
            items = json.loads(body).get("items", [])
            provs = [(i["provider"]["name"], i.get("details"), i.get("overUnder"),
                      (i.get("homeTeamOdds") or {}).get("moneyLine"),
                      bool((i.get("homeTeamOdds") or {}).get("open")), bool((i.get("homeTeamOdds") or {}).get("close"))) for i in items]
        except Exception as e:
            provs = f"err {code} {e!r}"
        code, body, _, _ = get(f"{CORE}/events/{ev}/competitions/{ev}/odds/58/propBets?limit=1")
        try:
            props = json.loads(body).get("count")
        except Exception:
            props = code
        log(f"\n{season_end}-03-01 event {ev}: odds providers (name, details, total, homeML, has_open, has_close) = {provs}; ESPN BET propBets count={props}")

    # Current season: upcoming game providers + props
    code, body, _, _ = get(f"{SITE}/scoreboard?dates=20261021")
    evs = json.loads(body)["events"]
    ev = evs[0]["id"]
    probe("ESPN core odds upcoming", f"{CORE}/events/{ev}/competitions/{ev}/odds",
          show=lambda d: j([(i["provider"]["id"], i["provider"]["name"], i.get("details"), i.get("overUnder"), i.get("overOdds"),
                             (i.get("homeTeamOdds") or {}).get("moneyLine"), (i.get("awayTeamOdds") or {}).get("moneyLine")) for i in d.get("items", [])]))
    for pid in (100, 58, 2000, 40):
        probe(f"ESPN propBets upcoming provider {pid}", f"{CORE}/events/{ev}/competitions/{ev}/odds/{pid}/propBets?limit=3",
              show=lambda d: j({"count": d.get("count"), "types": [i.get("type") for i in d.get("items", [])]}, 800))
    probe("ESPN core movement upcoming", f"{CORE}/events/{ev}/competitions/{ev}/odds/100/history/0/movement?limit=20", show=lambda d: j(d, 1500))
    # ESPN player gamelog
    probe("ESPN athlete gamelog", "https://site.web.api.espn.com/apis/common/v3/sports/basketball/nba/athletes/3112335/gamelog?season=2025",
          show=lambda d: j({"keys": list(d), "labels": d.get("labels"), "n_events": len(d.get("events", {}))}, 1500))
    probe("ESPN season-wide scoreboard via calendar", f"{SITE}/scoreboard?dates=20250301&limit=100&groups=", show=lambda d: j(d.get("leagues", [{}])[0].get("calendar", [])[:5]))
    open("reports/source_probe2.md", "w").write("\n".join(OUT) + "\n")


if __name__ == "__main__":
    os.makedirs("reports", exist_ok=True)
    main()
