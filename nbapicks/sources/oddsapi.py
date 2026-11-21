"""The Odds API (the-odds-api.com): DraftKings and FanDuel prop prices and bet-slip links.

Two uses. (1) The site's "open on the slip" links. (2) Since 2026-11-17 the posted picks: the
FanDuel price is the price a pick is posted and graded at, and the DraftKings two-way price from
the same response is the reference its edge is measured against (nbapicks/leans.py). Every
two-way quote fetched is appended to data/ledger/fd_quotes/ so the rule can be tested later.

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
                r = dict(link=link, sid=o.get("sid"))
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


def parse_event_prices(d: dict) -> list[dict]:
    """Two-way prop quotes of one event: [{book, player, stat, line, over, under, updated}] with
    decimal prices. A player/stat/line with only one side priced is dropped (no fair price, no bet)."""
    out = []
    for bm in d.get("bookmakers") or []:
        book = bm.get("key")
        if book not in BOOKS:
            continue
        for m in bm.get("markets") or []:
            stat = PROP_MARKETS.get(m.get("key"))
            if not stat:
                continue
            sides: dict[tuple, dict] = {}
            for o in m.get("outcomes") or []:
                name, point, price = o.get("name"), o.get("point"), o.get("price")
                if name not in ("Over", "Under") or point is None or price in (None, 0) or not o.get("description"):
                    continue
                dec = 1 + price / 100 if price > 0 else 1 + 100 / -price
                sides.setdefault((norm_name(o["description"]), float(point)), {})[name.lower()] = round(dec, 4)
            for (player, line), s in sorted(sides.items()):
                if len(s) == 2:
                    out.append(dict(book=book, player=player, stat=stat, line=line, over=s["over"], under=s["under"],
                                    updated=m.get("last_update") or bm.get("last_update")))
    return out


def fd_prop_set(books: dict) -> set:
    """{(normalised player, stat, side, line)} for FanDuel prop outcomes from parse_event_links output."""
    return {(o["player"], o["stat"], o["selection"], float(o["line"]))
            for o in books.get("fanduel", []) if o.get("market") == "prop" and o.get("line") is not None
            and o.get("player") and o.get("stat")}
