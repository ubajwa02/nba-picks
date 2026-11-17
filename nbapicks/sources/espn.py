"""ESPN public JSON (site.api / sports.core.api). Undocumented but public; no key.

Verified from a GitHub runner on 2026-10-20 (reports/source_probe*.md):
schedule/scores back to at least 2008, multi-book closing lines from 2013-14,
open+close from 2023-24, DraftKings (provider 100) for 2026-27 with player props
(points/assists/rebounds/threes), injuries (current only, no history).
Every parse function is pure and tested against captured real responses.
"""
from __future__ import annotations

import datetime as dt
import re
from urllib.parse import parse_qs, urlparse
from typing import Any

from .. import odds as O
from ..teams import canon
from ..http import get_json

SITE = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"
CORE = "https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba"
STATUS = {"STATUS_SCHEDULED": "scheduled", "STATUS_IN_PROGRESS": "in_progress", "STATUS_HALFTIME": "in_progress",
          "STATUS_END_PERIOD": "in_progress", "STATUS_FINAL": "final", "STATUS_POSTPONED": "postponed",
          "STATUS_CANCELED": "cancelled", "STATUS_SUSPENDED": "suspended", "STATUS_DELAYED": "scheduled"}
PROP_STATS = {"Total Points": "pts", "Total Assists": "ast", "Total Rebounds": "reb",
              "Total 3-Point Field Goals": "fg3m", "Total Steals": "stl", "Total Blocks": "blk"}
# ESPN provider ids worth keeping as real sportsbooks (others are tipsters/aggregates or live odds)
NON_BOOKS = {"consensus", "numberfire", "teamrankings", "accuscore", "Opening"}
# ESPN spells some providers differently between endpoints and seasons; store one name each
BOOK_ALIASES = {"Draft Kings": "DraftKings"}
# a quoted line outside these bounds is a parsing artefact (e.g. a price in the line field), not a market
MAX_ABS_SPREAD, TOTAL_RANGE = 40.0, (150.0, 300.0)


def canon_book(name: str) -> str:
    return BOOK_ALIASES.get(name, name)


def _status(t: dict) -> str:
    if t.get("name") in STATUS:
        return STATUS[t["name"]]
    if t.get("completed"):
        return "final"
    return {"pre": "scheduled", "in": "in_progress"}.get(t.get("state"), "unknown")


def scoreboard_url(day: dt.date) -> str:
    return f"{SITE}/scoreboard?dates={day:%Y%m%d}&limit=100"


def parse_scoreboard(d: dict, observed_at: str) -> tuple[list[dict], list[dict]]:
    """Returns (games, odds_rows) from a scoreboard response."""
    games, rows = [], []
    for ev in d.get("events", []):
        comp = ev["competitions"][0]
        teams = {c["homeAway"]: c for c in comp["competitors"]}
        st = _status(ev["status"]["type"])
        final = st == "final"
        season = ev.get("season", {})
        g = dict(game_id=str(ev["id"]), season=season.get("year"),
                 season_type={1: "pre", 2: "regular", 3: "post", 5: "playin"}.get(season.get("type"), str(season.get("type"))),
                 start_utc=ev["date"], home=canon(teams["home"]["team"]["abbreviation"]),
                 away=canon(teams["away"]["team"]["abbreviation"]),
                 home_id=teams["home"]["team"]["id"], away_id=teams["away"]["team"]["id"], status=st,
                 home_score=int(teams["home"]["score"]) if final else None,
                 away_score=int(teams["away"]["score"]) if final else None,
                 observed_at=observed_at, source="espn")
        games.append(g)
    return games, rows


def parse_core_odds(d: dict, game_id: str, observed_at: str, game_final: bool = False) -> list[dict]:
    """Rows for ml/spread/total from the core odds list (all providers).

    kind='current' for the live quote, plus 'open'/'close' where ESPN provides them.
    Seasons before 2023-24 carry only a 'current' quote. For a finished game that quote
    is the book's last posted line, so it is stored as kind='close' with flag
    'final_quote_untimed' (the time it was taken is unknown).
    """
    out = []
    for it in d.get("items", []):
        prov = it.get("provider", {})
        book = canon_book(prov.get("name", "?"))
        if book in NON_BOOKS or "Live" in book:
            continue
        h, a = it.get("homeTeamOdds") or {}, it.get("awayTeamOdds") or {}
        has_oc = bool(h.get("open") or h.get("close") or h.get("current"))
        def add(kind, market, sel, line, american, flags=None):
            dec = _dec(american)
            if dec is None and line is None:
                return
            out.append(dict(game_id=game_id, market=market, selection=sel, line=line, price_dec=dec, book=book,
                            source="espn", kind=kind, observed_at=observed_at, flags=flags))
        legacy = game_final and not (h.get("close") or a.get("close"))
        if has_oc:
            for src_kind in ("open", "current", "close"):
                hk, ak = h.get(src_kind) or {}, a.get(src_kind) or {}
                if not hk and not ak:
                    continue
                if legacy and src_kind == "current":
                    kind, flags = "close", "final_quote_untimed"
                elif game_final and src_kind == "current":
                    continue  # duplicate of close for a finished game
                else:
                    kind, flags = src_kind, None
                add(kind, "ml", "home", None, _am(hk.get("moneyLine")), flags)
                add(kind, "ml", "away", None, _am(ak.get("moneyLine")), flags)
                hl, al = _num((hk.get("pointSpread") or {}).get("american")), _num((ak.get("pointSpread") or {}).get("american"))
                if hl is not None:
                    add(kind, "spread", "home", hl, _am(hk.get("spread")), flags)
                if al is not None:
                    add(kind, "spread", "away", al, _am(ak.get("spread")), flags)
                tot = it.get(src_kind) or {}
                tl = _num((tot.get("total") or {}).get("american"))
                if tl is not None:
                    add(kind, "total", "over", tl, _am(tot.get("over")), flags)
                    add(kind, "total", "under", tl, _am(tot.get("under")), flags)
        else:
            fl = "final_quote_untimed"
            sp = it.get("spread")
            add("close", "ml", "home", None, h.get("moneyLine"), fl)
            add("close", "ml", "away", None, a.get("moneyLine"), fl)
            if sp is not None:
                add("close", "spread", "home", float(sp), h.get("spreadOdds") or -110, fl if h.get("spreadOdds") else fl + ",price_assumed_-110")
                add("close", "spread", "away", -float(sp), a.get("spreadOdds") or -110, fl if a.get("spreadOdds") else fl + ",price_assumed_-110")
            if it.get("overUnder") is not None:
                add("close", "total", "over", float(it["overUnder"]), it.get("overOdds") or -110, fl if it.get("overOdds") else fl + ",price_assumed_-110")
                add("close", "total", "under", float(it["overUnder"]), it.get("underOdds") or -110, fl if it.get("underOdds") else fl + ",price_assumed_-110")
    # drop rows whose price is missing or nonsensical (ESPN uses 0 for "no line"), and lines
    # that cannot be real (ESPN BET 2022-23 carries the American price in the spread field)
    return [r for r in out if r["price_dec"] is not None and _line_ok(r)]


# ---- DraftKings bet-slip links (convenience only; never used for pricing) ----------
# ESPN's core odds item for DraftKings carries one link per side, e.g.
#   gateway?...&preurl=https://sportsbook.draftkings.com/event/34937000?outcomes=0HC87027713P550_1
# The outcome id encodes the line (P/N = +/- spread, O/U = over/under total, hundredths).
DK_REL = {"home": ("ml", "home"), "away": ("ml", "away"), "homeSpread": ("spread", "home"),
          "awaySpread": ("spread", "away"), "over": ("total", "over"), "under": ("total", "under")}
_DK_EVENT = re.compile(r"^https://sportsbook\.draftkings\.com/event/(\d+)$")
_DK_OUTCOME = re.compile(r"^0(ML|HC|OU)\d+(?:([PNOU])(\d+))?_\d+$")


def _dk_direct(href: str) -> tuple[str, str | None] | None:
    """(event url, outcome id) from an ESPN DraftKings link, dropping ESPN's affiliate gateway."""
    u = urlparse(href or "")
    if u.netloc != "sportsbook.draftkings.com":
        return None
    if u.path.startswith("/gateway"):
        pre = (parse_qs(u.query).get("preurl") or [None])[0]
        if not pre:
            return None
        u = urlparse(pre)
    base = f"{u.scheme}://{u.netloc}{u.path}"
    if not _DK_EVENT.match(base):
        return None
    oc = (parse_qs(u.query).get("outcomes") or [None])[0]
    return base, oc


def _dk_line(market: str, outcome_id: str) -> float | None | bool:
    """Signed line encoded in the outcome id; None for moneyline; False if it does not parse."""
    m = _DK_OUTCOME.match(outcome_id or "")
    if not m or {"ml": "ML", "spread": "HC", "total": "OU"}[market] != m.group(1):
        return False
    if market == "ml":
        return None if m.group(2) is None else False
    if m.group(2) is None:
        return False
    v = int(m.group(3)) / 100
    return -v if m.group(2) == "N" else v


def parse_dk_links(d: dict) -> dict | None:
    """DraftKings event page + bet-slip outcome per (market, side) from a core odds response.

    Returns {"event_url", "outcomes": [{market, selection, line, outcome_id}]} or None when ESPN
    carries no DraftKings links. Outcomes whose id does not encode the expected market are dropped.
    """
    for it in d.get("items", []):
        if canon_book((it.get("provider") or {}).get("name", "")) != "DraftKings":
            continue
        event_url, outcomes = None, []
        for link in it.get("links") or []:
            got = _dk_direct(link.get("href"))
            if not got:
                continue
            base, oc = got
            event_url = event_url or base
            rel = next((r for r in link.get("rel") or [] if r in DK_REL), None)
            if rel and oc:
                market, sel = DK_REL[rel]
                line = _dk_line(market, oc)
                if line is not False:
                    outcomes.append(dict(market=market, selection=sel, line=line, outcome_id=oc))
        if event_url:
            return dict(event_url=event_url, outcomes=outcomes)
    return None


def _line_ok(r: dict) -> bool:
    if r["line"] is None:
        return True
    if r["market"] == "spread":
        return abs(r["line"]) <= MAX_ABS_SPREAD
    if r["market"] == "total":
        return TOTAL_RANGE[0] <= r["line"] <= TOTAL_RANGE[1]
    return True


def parse_propbets(d: dict, game_id: str, book: str, observed_at: str, athletes: dict[str, str]) -> list[dict]:
    """Player O/U props. ESPN lists each line twice (over and under) without labelling
    which is which, so rows carry selection 'side0'/'side1' in listing order and flag
    'side_unverified'. Qualification refuses them until the order is verified.
    For DraftKings the first one listed is the Over; nbapicks/sideorder.py measures that on
    results after every settle and predict labels the pair only while it holds."""
    out, seen = [], {}
    for it in d.get("items", []):
        stat = PROP_STATS.get(it.get("type", {}).get("name"))
        if not stat or "athlete" not in it:
            continue
        aid = it["athlete"]["$ref"].split("/athletes/")[1].split("?")[0]
        line = _num(it["odds"]["total"]["value"])
        key = (aid, stat, line)
        idx = seen.get(key, 0); seen[key] = idx + 1
        if idx > 1:
            continue
        for kind, field in (("current", "value"), ("open", "open")):
            dec = _num(it["odds"]["decimal"].get(field))
            ln = _num(it["odds"]["total"].get(field))
            if dec is None or dec <= 1 or ln is None:
                continue
            out.append(dict(game_id=game_id, market="prop", selection=f"side{idx}", line=ln, player_id=aid,
                            player_name=athletes.get(aid), stat=stat, price_dec=dec, book=book, source="espn",
                            kind=kind, observed_at=observed_at, source_updated_at=it.get("lastUpdated"),
                            flags="side_unverified"))
    return out


def parse_injuries(d: dict, observed_at: str) -> list[dict]:
    out = []
    for team in d.get("injuries", []):
        for inj in team.get("injuries", []):
            ath = inj.get("athlete", {})
            t = (ath.get("team") or {}).get("abbreviation") or team.get("abbreviation")
            out.append(dict(player_id=str(ath.get("id") or _athlete_id(ath)), player_name=ath.get("displayName", "?"),
                            team=canon(t) if t else _team_from_name(team.get("displayName")),
                            status=inj.get("status", "?"), detail=inj.get("shortComment"),
                            source_date=inj.get("date"), observed_at=observed_at, source="espn"))
    return out


def parse_boxscore(summary: dict, game_id: str, observed_at: str) -> list[dict]:
    rows = []
    for team in (summary.get("boxscore") or {}).get("players", []):
        abbr = canon(team["team"]["abbreviation"])
        for blk in team.get("statistics", []):
            labels = blk.get("labels") or blk.get("names") or []
            for a in blk.get("athletes", []):
                ath = a.get("athlete", {})
                st = dict(zip(labels, a.get("stats", [])))
                played = bool(st) and not a.get("didNotPlay", False)
                def num(k):
                    v = st.get(k)
                    try:
                        return int(str(v).split("-")[0])
                    except Exception:
                        return None
                def att(k):
                    # "made-attempted" -> attempted
                    v = str(st.get(k, ""))
                    if not played or "-" not in v:
                        return None
                    try:
                        return int(v.split("-")[1])
                    except ValueError:
                        return None
                three = st.get("3PT", "")
                rows.append(dict(game_id=game_id, player_id=str(ath.get("id")), player_name=ath.get("displayName"),
                                 team=abbr, starter=int(bool(a.get("starter"))),
                                 minutes=_num(st.get("MIN")) if played else 0.0,
                                 pts=num("PTS"), reb=num("REB"), ast=num("AST"),
                                 fg3m=int(three.split("-")[0]) if played and "-" in str(three) else None,
                                 stl=num("STL"), blk=num("BLK"), tov=num("TO"), played=int(played),
                                 fga=att("FG"), fg3a=att("3PT"), fta=att("FT"),
                                 oreb=num("OREB") if played else None, dreb=num("DREB") if played else None,
                                 plus_minus=_int_signed(st.get("+/-")) if played else None,
                                 observed_at=observed_at))
    return rows


# ---- fetchers (network; exercised on the runner, not in unit tests) ----------
def fetch_scoreboard(day: dt.date) -> dict:
    return get_json(scoreboard_url(day))


def fetch_core_odds(game_id: str) -> dict:
    return get_json(f"{CORE}/events/{game_id}/competitions/{game_id}/odds")


def fetch_propbets(game_id: str, provider: str = "100", page: int = 1) -> dict:
    url = f"{CORE}/events/{game_id}/competitions/{game_id}/odds/{provider}/propBets?limit=1000"
    return get_json(url + (f"&page={page}" if page > 1 else ""))


def fetch_athlete_name(ref: str) -> str | None:
    try:
        return get_json(ref.replace("http://", "https://")).get("displayName")
    except Exception:
        return None


def fetch_injuries() -> dict:
    return get_json(f"{SITE}/injuries")


def fetch_summary(game_id: str) -> dict:
    return get_json(f"{SITE}/summary?event={game_id}")


# ---- helpers ------------------------------------------------------------------
def _num(v: Any) -> float | None:
    if v is None:
        return None
    try:
        s = str(v).strip().replace("+", "")
        if s.upper() in ("EVEN", "PK"):
            return 0.0
        return float(s)
    except ValueError:
        return None


def _int_signed(v: Any) -> int | None:
    """'+12' / '-3' / '0' -> int; anything else (None, '--') -> None."""
    try:
        return int(str(v).strip().replace("+", ""))
    except (TypeError, ValueError):
        return None


def _am(obj: Any) -> float | None:
    """American odds from ESPN's {'american': '-110', 'decimal': 1.9} objects."""
    if not obj:
        return None
    a = obj.get("american") if isinstance(obj, dict) else obj
    if isinstance(a, str) and a.upper() == "EVEN":
        return 100.0
    return _num(a)


def _dec(american: Any) -> float | None:
    a = _num(american)
    if a is None or a == 0 or -100 < a < 100:
        return None
    return O.american_to_decimal(a)


def _athlete_id(ath: dict) -> str:
    for l in ath.get("links", []):
        if "/id/" in l.get("href", ""):
            return l["href"].split("/id/")[1].split("/")[0]
    return ath.get("displayName", "?")


def _team_from_name(name: str | None) -> str | None:
    from ..teams import from_name
    return from_name(name or "")
