"""Historical backfill for research (not the live audit ledger).

Pulls every game of a season from ESPN's scoreboard, then each finished game's
odds from the core API, and optionally box scores. Writes gzip CSVs under
data/history/. Re-runnable: a season file is rewritten whole, deterministically
sorted, so re-running only produces a diff when ESPN's data changed.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import io
import logging
import os
from concurrent.futures import ThreadPoolExecutor

from .sources import espn
from .teams import TEAMS

log = logging.getLogger("nbapicks.history")
GAME_COLS = ["game_id", "season", "season_type", "start_utc", "home", "away", "status", "home_score", "away_score"]
ODDS_COLS = ["game_id", "book", "kind", "market", "selection", "line", "price_dec", "flags"]
BOX_COLS = ["game_id", "player_id", "player_name", "team", "starter", "minutes", "pts", "reb", "ast", "fg3m",
            "stl", "blk", "tov", "played",
            # added 2026-10-22 (shot volume, rebounds split, plus-minus); files written before lack them
            "fga", "fg3a", "fta", "oreb", "dreb", "plus_minus"]


def season_dates(season: int) -> list[dt.date]:
    d, end = dt.date(season - 1, 9, 25), min(dt.date(season, 7, 1), dt.date.today() + dt.timedelta(days=10))
    out = []
    while d <= end:
        out.append(d); d += dt.timedelta(days=1)
    return out


def write_csv(path: str, cols: list[str], rows: list[dict]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore", lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow(r)
    # mtime=0 keeps the gzip bytes identical across runs with identical content
    with open(path, "wb") as fh, gzip.GzipFile(fileobj=fh, mode="wb", mtime=0) as gz:
        gz.write(buf.getvalue().encode())


def read_csv(path: str) -> list[dict]:
    with gzip.open(path, "rt") as fh:
        return list(csv.DictReader(fh))


def backfill(season: int, out_dir: str, box: bool = False, workers: int = 6) -> dict:
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    games: dict[str, dict] = {}
    errors = []

    def day(d):
        try:
            return espn.parse_scoreboard(espn.fetch_scoreboard(d), now)[0]
        except Exception as e:
            errors.append(f"scoreboard {d}: {e}")
            return []
    with ThreadPoolExecutor(workers) as ex:
        for gs in ex.map(day, season_dates(season)):
            for g in gs:
                if g["home"] in TEAMS and g["away"] in TEAMS and g["season_type"] in ("regular", "post", "playin"):
                    games[g["game_id"]] = g
    finals = [g for g in games.values() if g["status"] == "final"]

    def odds(g):
        try:
            return espn.parse_core_odds(espn.fetch_core_odds(g["game_id"]), g["game_id"], now, game_final=True)
        except Exception as e:
            errors.append(f"odds {g['game_id']}: {e}")
            return []
    rows = []
    with ThreadPoolExecutor(workers) as ex:
        for r in ex.map(odds, finals):
            rows.extend(r)
    gl = sorted(games.values(), key=lambda g: (g["start_utc"], g["game_id"]))
    rows.sort(key=lambda r: (r["game_id"], r["book"], r["kind"], r["market"], r["selection"]))
    write_csv(f"{out_dir}/games_{season}.csv.gz", GAME_COLS, gl)
    write_csv(f"{out_dir}/odds_{season}.csv.gz", ODDS_COLS, rows)
    nbox = 0
    if box:
        def bx(g):
            try:
                return espn.parse_boxscore(espn.fetch_summary(g["game_id"]), g["game_id"], now)
            except Exception as e:
                errors.append(f"box {g['game_id']}: {e}")
                return []
        brows = []
        with ThreadPoolExecutor(workers) as ex:
            for r in ex.map(bx, finals):
                brows.extend(r)
        brows.sort(key=lambda r: (r["game_id"], r["team"], r["player_id"]))
        write_csv(f"{out_dir}/box_{season}.csv.gz", BOX_COLS, brows)
        nbox = len(brows)
    with_odds = len({r["game_id"] for r in rows})
    summary = dict(season=season, games=len(gl), finals=len(finals), finals_with_odds=with_odds,
                   odds_rows=len(rows), box_rows=nbox, errors=len(errors), first_errors=errors[:10])
    log.info("%s", summary)
    return summary


# ---------------- historical player-prop prices -------------------------------------------
PROP_COLS = ["game_id", "player_id", "player_name", "stat", "line", "price0_dec", "price1_dec", "side_label",
             "kind", "observed_at", "source_updated_at", "flags", "book"]
PROP_PROVIDERS = (("100", "DraftKings"), ("58", "ESPN BET"))   # 58 only when 100 has nothing


def _utc(s: str | None) -> dt.datetime | None:
    if not s:
        return None
    try:
        d = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None
    return d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)


def prop_rows(d: dict, game_id: str, observed_at: str, names: dict[str, str], tip_utc: str | None,
              book: str = "DraftKings") -> list[dict]:
    """Paired prop prices from one propBets response.

    ESPN lists every (player, stat, line) twice, once per side, without saying which side is
    over and which is under. The two listings are paired in order: price0 is the first one
    listed, price1 the second, and side_label stays 'unknown'. One row per pair and kind
    ('current' = ESPN's last value, 'open' = its opening value). A row is flagged
    'untimed_final' when an item of the pair has no lastUpdated or was updated after tip,
    so its price may not be a pre-game price.
    """
    tip = _utc(tip_utc)
    groups: dict[tuple, list[dict]] = {}
    for it in d.get("items", []):
        stat = espn.PROP_STATS.get((it.get("type") or {}).get("name"))
        if not stat or "athlete" not in it or "odds" not in it:
            continue
        aid = it["athlete"]["$ref"].split("/athletes/")[1].split("?")[0]
        line = espn._num((it["odds"].get("total") or {}).get("value"))
        if line is None:
            continue
        groups.setdefault((aid, stat, line), []).append(it)
    out = []
    for (aid, stat, line), items in groups.items():
        if len(items) < 2:
            continue          # one side only: no pair to price
        a, b = items[0], items[1]
        upd = [_utc(x.get("lastUpdated")) for x in (a, b)]
        known = [u for u in upd if u is not None]
        last = max(known) if known else None
        untimed = len(known) < 2 or (tip is not None and last > tip)
        last_s = last.strftime("%Y-%m-%dT%H:%M:%SZ") if last else None
        for kind, field in (("current", "value"), ("open", "open")):
            la, lb = (espn._num((x["odds"].get("total") or {}).get(field)) for x in (a, b))
            pa, pb = (espn._num((x["odds"].get("decimal") or {}).get(field)) for x in (a, b))
            if la is None or la != lb or pa is None or pb is None or pa <= 1 or pb <= 1:
                continue
            out.append(dict(game_id=game_id, player_id=aid, player_name=names.get(aid), stat=stat, line=la,
                            price0_dec=pa, price1_dec=pb, side_label="unknown", kind=kind, observed_at=observed_at,
                            source_updated_at=last_s, flags="untimed_final" if untimed else "", book=book))
    return out


def fetch_all_propbets(game_id: str, provider: str) -> dict:
    """Every page of a game's propBets (ESPN pages at 1000 items)."""
    d = espn.fetch_propbets(game_id, provider)
    items = list(d.get("items", []))
    for page in range(2, int(d.get("pageCount") or 1) + 1):
        items += espn.fetch_propbets(game_id, provider, page=page).get("items", [])
    return {**d, "items": items}


def season_finals(season: int, out_dir: str, workers: int = 6, errors: list | None = None) -> list[dict]:
    """Final games of a season: from games_<season>.csv.gz when present, else the scoreboard."""
    errors = [] if errors is None else errors
    path = f"{out_dir}/games_{season}.csv.gz"
    if os.path.exists(path):
        return [g for g in read_csv(path) if g["status"] == "final"]
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    games = {}

    def day(d):
        try:
            return espn.parse_scoreboard(espn.fetch_scoreboard(d), now)[0]
        except Exception as e:
            errors.append(f"scoreboard {d}: {e}")
            return []
    with ThreadPoolExecutor(workers) as ex:
        for gs in ex.map(day, season_dates(season)):
            for g in gs:
                if g["home"] in TEAMS and g["away"] in TEAMS and g["season_type"] in ("regular", "post", "playin"):
                    games[g["game_id"]] = g
    return [g for g in games.values() if g["status"] == "final"]


def backfill_props(season: int, out_dir: str, workers: int = 6, fetch=None, summary_fetch=None,
                   finals: list[dict] | None = None) -> dict:
    """data/history/props_<season>.csv.gz from ESPN's propBets for every final game of a season.
    DraftKings (provider 100) first; ESPN BET (58) only for a game where 100 returns nothing.
    Player names come from that game's box score (the season box file when it has the game,
    otherwise one summary call per game), never from one call per athlete."""
    fetch = fetch or fetch_all_propbets
    summary_fetch = summary_fetch or espn.fetch_summary
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    errors: list[str] = []
    finals = season_finals(season, out_dir, workers, errors) if finals is None else finals
    names_by_game: dict[str, dict[str, str]] = {}
    bp = f"{out_dir}/box_{season}.csv.gz"
    if os.path.exists(bp):
        for r in read_csv(bp):
            names_by_game.setdefault(r["game_id"], {})[r["player_id"]] = r["player_name"]
    books: dict[str, int] = {}
    empty: list[str] = []

    def one(g):
        gid = g["game_id"]
        rows, book = [], None
        for prov, bname in PROP_PROVIDERS:
            try:
                d = fetch(gid, prov)
            except Exception as e:
                errors.append(f"props {gid} provider {prov}: {e}")
                continue
            obs = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            rows = prop_rows(d, gid, obs, {}, g.get("start_utc"), bname)
            if rows:
                book = bname
                break
        if not rows:
            empty.append(gid)
            return []
        names = names_by_game.get(gid)
        if not names:
            try:
                names = {r["player_id"]: r["player_name"] for r in espn.parse_boxscore(summary_fetch(gid), gid, now)}
            except Exception as e:
                errors.append(f"box names {gid}: {e}")
                names = {}
        for r in rows:
            r["player_name"] = names.get(r["player_id"])
        books[book] = books.get(book, 0) + 1
        return rows
    rows = []
    with ThreadPoolExecutor(workers) as ex:
        for r in ex.map(one, finals):
            rows.extend(r)
    rows.sort(key=lambda r: (r["game_id"], r["player_id"], r["stat"], r["kind"], r["line"]))
    write_csv(f"{out_dir}/props_{season}.csv.gz", PROP_COLS, rows)
    gw = len({r["game_id"] for r in rows})
    summary = dict(season=season, games=len(finals), games_with_props=gw, rows=len(rows),
                   rows_current=sum(r["kind"] == "current" for r in rows),
                   rows_open=sum(r["kind"] == "open" for r in rows),
                   rows_untimed_final=sum("untimed_final" in r["flags"] for r in rows),
                   rows_without_name=sum(not r["player_name"] for r in rows),
                   games_by_book=books, games_with_empty_propbets=len(empty),
                   errors=len(errors), first_errors=errors[:10])
    if finals and not gw and len(empty) == len(finals) and not errors:
        summary["finding"] = ("ESPN returned no propBets (DraftKings provider 100, ESPN BET provider 58) for any "
                              "finished game of this season: historical prop prices are not available from this "
                              "endpoint. This is a property of the source, not a fetch failure.")
    elif empty:
        summary["finding"] = (f"{len(empty)} of {len(finals)} finished games had no propBets from either provider"
                              + (f" ({len(errors)} fetch errors; see first_errors)." if errors else "."))
    log.info("%s", summary)
    return summary


def backfill_box(season: int, out_dir: str, workers: int = 6) -> dict:
    """Re-fetch only the box scores of a season's final games (refreshes the box columns)."""
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    errors: list[str] = []
    finals = season_finals(season, out_dir, workers, errors)

    def bx(g):
        try:
            return espn.parse_boxscore(espn.fetch_summary(g["game_id"]), g["game_id"], now)
        except Exception as e:
            errors.append(f"box {g['game_id']}: {e}")
            return []
    brows = []
    with ThreadPoolExecutor(workers) as ex:
        for r in ex.map(bx, finals):
            brows.extend(r)
    brows.sort(key=lambda r: (r["game_id"], r["team"], r["player_id"]))
    write_csv(f"{out_dir}/box_{season}.csv.gz", BOX_COLS, brows)
    return dict(season=season, finals=len(finals), box_games=len({r["game_id"] for r in brows}),
                box_rows=len(brows), errors=len(errors), first_errors=errors[:10])


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("seasons", nargs="+", type=int)
    ap.add_argument("--out", default="data/history")
    ap.add_argument("--box", action="store_true", help="also fetch box scores")
    ap.add_argument("--box-only", action="store_true", help="re-fetch only the box scores")
    ap.add_argument("--props", action="store_true", help="historical player-prop prices only")
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    import json
    os.makedirs("reports", exist_ok=True)
    if a.props or a.box_only:
        res = []
        for s in a.seasons:
            for flag, fn, name in ((a.box_only, backfill_box, "box"), (a.props, backfill_props, "props")):
                if flag:
                    r = fn(s, a.out)
                    with open(f"reports/backfill_{name}_{s}.json", "w") as fh:
                        json.dump(r, fh, indent=1)
                    res.append(r)
        print(json.dumps(res, indent=1))
        return
    res = [backfill(s, a.out, box=a.box) for s in a.seasons]
    for r in res:
        with open(f"reports/backfill_{r['season']}.json", "w") as fh:
            json.dump(r, fh, indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
