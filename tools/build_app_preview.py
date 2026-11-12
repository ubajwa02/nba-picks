"""Build one self-contained HTML file of the NBA Picks app (site/app) with a snapshot of site/data.json inside.

Use it to share or preview the app where there is no web server for site/ (for example a claude.ai artifact):
    python tools/build_app_preview.py [--data site/data.json] [--out build/nba-picks-app.html]
The data is trimmed to what the app reads (about 1/10 of data.json). Fonts are inlined, so the file works offline.
The page is marked as a snapshot: it does not warn that an older slate is "not updated today".
"""
import argparse
import base64
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "site", "app")


def _key(r):
    return "|".join(str(x if x is not None else "") for x in
                    (r.get("game_id"), r.get("market"), r.get("player_id") or "", r.get("stat") or "", r.get("line"), r.get("selection") or ""))


def trim(d):
    """Keep only what site/app/app.js reads."""
    perf = d.get("performance") or {}
    rows = (perf.get("posted_leans") or {}).get("rows") or []
    today = d.get("today") or {}
    legs = [l for t in (d.get("tickets") or {}).get("rows") or [] for l in t.get("legs") or []]
    wanted = {_key(r) for r in rows + (today.get("leans") or []) + legs}
    days = []
    for day in d.get("picks_by_day") or []:
        cands = [c for c in (day.get("candidates") or []) + (day.get("qualified") or []) if _key(c) in wanted]
        days.append({"date": day.get("date"), "candidates": cands})
    keep_today = {k: today.get(k) for k in ("date", "games", "game_count", "leans", "dk_links", "book_links")}
    val = [r for r in (d.get("valuation") or {}).get("rows") or [] if r.get("market") == "ml"]
    return {
        "meta": d.get("meta"), "today": keep_today, "picks_by_day": days, "tickets": d.get("tickets"),
        "performance": {"posted_leans": perf.get("posted_leans"), "scorecard": perf.get("scorecard")},
        "players": {"players": (d.get("players") or {}).get("players") or []}, "valuation": {"rows": val},
    }


def build(data_path, out_path):
    with open(data_path) as f:
        data = trim(json.load(f))
    html = open(os.path.join(APP, "index.html")).read()
    css = open(os.path.join(APP, "app.css")).read()
    js = open(os.path.join(APP, "app.js")).read()

    def font(m):
        p = os.path.join(APP, m.group(1))
        return 'url("data:font/woff2;base64,%s")' % base64.b64encode(open(p, "rb").read()).decode()
    css = re.sub(r'url\("(fonts/[^"]+)"\)', font, css)
    icon = "data:image/svg+xml;base64," + base64.b64encode(open(os.path.join(APP, "icons", "mark.svg"), "rb").read()).decode()
    payload = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")

    html = html.replace("<title>NBA Picks</title>", '<title>NBA Picks</title>\n<meta name="nba-snapshot" content="1">')
    html = re.sub(r'<link rel="manifest"[^>]*>\n', "", html)
    html = re.sub(r'<link rel="apple-touch-icon"[^>]*>\n', "", html)
    html = html.replace('href="icons/mark.svg"', 'href="%s"' % icon)
    html = html.replace('<link rel="stylesheet" href="app.css">', "<style>\n%s\n</style>" % css)
    html = html.replace('<script id="embedded" type="application/json"></script>', '<script id="embedded" type="application/json">%s</script>' % payload)
    html = html.replace('<script src="app.js"></script>', "<script>\n%s\n</script>" % js.replace("</script", "<\\/script"))
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w") as f:
        f.write(html)
    return os.path.getsize(out_path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=os.path.join(ROOT, "site", "data.json"))
    ap.add_argument("--out", default=os.path.join(ROOT, "build", "nba-picks-app.html"))
    a = ap.parse_args()
    print(a.out, build(a.data, a.out), "bytes")
