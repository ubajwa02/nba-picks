"""The Odds API (the-odds-api.com): bet-slip links for DraftKings and FanDuel, props included.

Used only for the site's "open on the slip" links. Prices from this feed are NOT stored,
modelled or graded; pricing stays on ESPN/DraftKings as before.

Off unless the ODDS_API_KEY environment variable is set (GitHub secret of the same name).
Cost: /events is free; /events/{id}/odds costs (markets returned) x (regions), where two
bookmakers count as one region. pipeline.book_links asks only for the markets today's picks
use, once per game per day (~10 credits a slate), so the free 500/month tier is enough.
The key is never logged: errors are re-raised with it redacted.
"""
from __future__ import annotations

import os
import re
import unicodedata
import urllib.parse

from ..http import FetchError, get_json
from ..teams import from_name

BASE = "https://api.the-odds-api.com/v4/sports/basketball_nba"
BOOKS = ("draftkings", "fanduel")
PROP_MARKETS = {"player_points": "pts", "player_rebounds": "reb", "player_assists": "ast", "player_threes": "fg3m"}
GAME_MARKETS = {"h2h": "ml", "spreads": "spread", "totals": "total"}
MARKETS = tuple(GAME_MARKETS) + tuple(PROP_MARKETS)
LINK_HOSTS = {"draftkings": "sportsbook.draftkings.com", "fanduel": "sportsbook.fanduel.com"}


def api_key() -> str | None:
    return (os.environ.get("ODDS_API_KEY") or "").strip() or None


def _get(path: str, key: str, **params) -> dict | list:
    url = f"{BASE}{path}?" + urllib.parse.urlencode(dict(params, apiKey=key))
    try:
        return get_json(url, retries=1)
    except FetchError as e:
        raise FetchError(url.replace(key, "***"), e.status, e.detail) from None


def fetch_events(key: str) -> list[dict]:
    return _get("/events", key)


def fetch_event_links(key: str, event_id: str, markets=MARKETS) -> dict:
    return _get(f"/events/{event_id}/odds", key, bookmakers=",".join(BOOKS), markets=",".join(markets),
                oddsFormat="american", includeLinks="true", includeSids="true")


_STAT_MARKET = {v: k for k, v in PROP_MARKETS.items()}
_GAME_MARKET = {v: k for k, v in GAME_MARKETS.items()}


def market_key(r: dict) -> str | None:
    """Odds API market key for a pick/leg/outcome row (prop stat -> player_*, ml -> h2h ...)."""
    if r.get("market") == "prop":
        return _STAT_MARKET.get(r.get("stat"))
    return _GAME_MARKET.get(r.get("market"))


def match_events(events: list[dict], games: list[dict]) -> dict[str, str]:
    """ESPN game_id -> Odds API event id, by home/away team and a start within 3 hours."""
    import datetime as dt
    def t(s):
        return dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    out = {}
    for g in games:
        for e in events:
            if (from_name(e.get("home_team")) == g["home"] and from_name(e.get("away_team")) == g["away"]
                    and abs((t(e["commence_time"]) - t(g["start_utc"])).total_seconds()) <= 3 * 3600):
                out[g["game_id"]] = e["id"]
                break
    return out


def norm_name(s: str) -> str:
    """'P.J. Washington Jr.' -> 'pj washington' (the same rule is used in site/index.html)."""
    s = "".join(c for c in unicodedata.normalize("NFKD", s or "") if not unicodedata.combining(c))
    s = re.sub(r"[^a-z ]", "", s.lower().replace("-", " "))
    return " ".join(w for w in s.split() if w not in ("jr", "sr", "ii", "iii", "iv"))


def _safe_link(book: str, link: str | None) -> str | None:
    u = urllib.parse.urlparse(link or "")
    return link if u.scheme == "https" and u.netloc == LINK_HOSTS[book] else None


def parse_event_links(d: dict, home: str, away: str) -> dict:
    """{book: [outcome]} where outcome = {market, selection, line, stat?, player?, link, sid}.

    Game lines use the repo's conventions (selection home/away/over/under, spread line signed
    for that side); props carry the player's normalised name and stat code. Outcomes without
    a bet-slip link on the bookmaker's own host are dropped.
    """
    out: dict[str, list] = {}
    for bm in d.get("bookmakers") or []:
        book = bm.get("key")
        if book not in BOOKS:
            continue
        rows = []
        for m in bm.get("markets") or []:
            mk = m.get("key")
            for o in m.get("outcomes") or []:
                link = _safe_link(book, o.get("link"))
                if not link:
                    continue
                name, point = o.get("name") or "", o.get("point")
                r = dict(link=link, sid=o.get("sid"), price=o.get("price"))
                if mk in PROP_MARKETS:
                    if name not in ("Over", "Under") or point is None:
                        continue
                    r.update(market="prop", stat=PROP_MARKETS[mk], player=norm_name(o.get("description")),
                             selection=name.lower(), line=float(point))
                elif mk in GAME_MARKETS:
                    if mk == "totals":
                        if name not in ("Over", "Under"):
                            continue
                        sel = name.lower()
                    else:
                        team = from_name(name)
                        sel = "home" if team == home else "away" if team == away else None
                        if sel is None:
                            continue
                    r.update(market=GAME_MARKETS[mk], selection=sel,
                             line=None if mk == "h2h" else (float(point) if point is not None else None))
                else:
                    continue
                rows.append(r)
        if rows:
            out[book] = rows
    return out


def fd_prop_prices(books: dict) -> dict:
    """{player|stat|side|line: American price} for FanDuel prop outcomes that carry a price."""
    return {f'{o["player"]}|{o["stat"]}|{o["selection"]}|{float(o["line"])}': o["price"]
            for o in books.get("fanduel", []) if o.get("market") == "prop" and o.get("line") is not None
            and o.get("player") and o.get("stat") and o.get("price")}


def fd_prop_set(books: dict) -> set:
    """{(normalised player, stat, side, line)} for FanDuel prop outcomes from parse_event_links output."""
    return {(o["player"], o["stat"], o["selection"], float(o["line"]))
            for o in books.get("fanduel", []) if o.get("market") == "prop" and o.get("line") is not None
            and o.get("player") and o.get("stat")}
