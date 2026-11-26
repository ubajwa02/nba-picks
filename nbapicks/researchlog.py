"""Research-only feature log (added 2026-11-26).

Writes extra context for each pick candidate to ledger/research_features.jsonl so factors that are not
stored anywhere else (line and price movement, rest and back-to-backs, home/away, pace proxy, defence
against the stat) can be tested later against settled results. READ-ONLY with respect to picks: nothing
here is read by leans.py, qualify.py or any model, and every failure is swallowed.
"""
from __future__ import annotations

import datetime as dt
import json
import os


def _date(s: str) -> dt.datetime:
    return dt.datetime.fromisoformat(str(s).replace("Z", "+00:00").replace("z", "+00:00")) if "T" in str(s) else dt.datetime.fromisoformat(str(s) + "T00:00:00+00:00")


def _team_games(store, team: str, before_utc: str, n: int):
    return store.q("SELECT game_id, start_utc, home, away, home_score, away_score FROM games WHERE (home = ? OR away = ?) "
                   "AND start_utc < ? AND status = 'final' ORDER BY start_utc DESC LIMIT ?", (team, team, before_utc, n))


def candidate_features(store, p: dict, game: dict) -> dict:
    """Features for one candidate prediction row p (needs player_id, stat, line, selection, game_id)."""
    sgn = 1 if p.get("selection") == "over" else -1
    f: dict = {}
    row = store.one("SELECT team FROM player_games WHERE player_id = ? AND team IS NOT NULL ORDER BY observed_at DESC LIMIT 1", (str(p["player_id"]),))
    team = (row or {}).get("team")
    if team and game:
        opp = game["away"] if team == game["home"] else game["home"] if team == game["away"] else None
        f.update(team=team, opp=opp, home=1 if team == game["home"] else 0 if team == game["away"] else None)
        start = game["start_utc"]
        for tag, tm in (("team", team), ("opp", opp)):
            if not tm:
                continue
            prev = _team_games(store, tm, start, 10)
            if prev:
                gap = (_date(start) - _date(prev[0]["start_utc"])).total_seconds() / 86400
                f[f"{tag}_rest_days"] = round(gap, 2)
                f[f"{tag}_b2b"] = int(gap < 1.5)
                tots = [(g["home_score"] or 0) + (g["away_score"] or 0) for g in prev if g["home_score"] is not None]
                if tots:
                    f[f"{tag}_pace_pts10"] = round(sum(tots) / len(tots), 1)      # combined points of its last 10: pace/scoring proxy
        if opp:
            prev = _team_games(store, opp, start, 15)
            ids = [g["game_id"] for g in prev]
            if ids:
                q = ",".join("?" * len(ids))
                stat = p["stat"] if p["stat"] in ("pts", "reb", "ast", "fg3m") else None
                if stat:
                    tot = store.one(f"SELECT SUM({stat}) s FROM player_games WHERE game_id IN ({q}) AND team != ? AND played = 1", ids + [opp])
                    lg = store.one(f"SELECT SUM({stat}) s, COUNT(DISTINCT game_id || team) c FROM player_games WHERE played = 1 AND game_id IN "
                                   f"(SELECT game_id FROM games WHERE status = 'final' AND start_utc < ? ORDER BY start_utc DESC LIMIT 150)", (start,))
                    if tot and tot["s"] is not None and lg and lg["c"]:
                        f["opp_allowed_stat_per_game"] = round(tot["s"] / len(ids), 2)
                        f["league_stat_per_team_game"] = round(lg["s"] / lg["c"], 2)
    mv = store.q("SELECT line, price_dec, observed_at FROM odds WHERE market = 'prop' AND game_id = ? AND player_id = ? AND stat = ? "
                 "AND book = 'DraftKings' AND line IS NOT NULL ORDER BY observed_at", (p["game_id"], str(p["player_id"]), p["stat"]))
    if mv:
        f.update(line_first=mv[0]["line"], line_now=mv[-1]["line"], line_snaps=len(mv), line_first_at=mv[0]["observed_at"],
                 line_move_toward_pick=round(sgn * (mv[0]["line"] - mv[-1]["line"]), 2))   # + = line moved in our favour since first seen
    return f


def log_features(ctx, rows: list[dict], preds: list[dict], slate: str, posted_ids: set, stage: str = "posted") -> int:
    """Append one row per candidate lean. Never raises."""
    try:
        by_key = {(str(p["game_id"]), str(p["player_id"]), p["stat"], p["line"], p["selection"]): p for p in preds if p.get("player_id")}
        games = {g["game_id"]: g for g in ctx.store.q("SELECT game_id, home, away, start_utc FROM games")}
        out = []
        for r in rows:
            p = by_key.get((str(r["game_id"]), str(r["player_id"]), r["stat"], r["line"], r["selection"]))
            if not p:
                continue
            feats = candidate_features(ctx.store, p, games.get(r["game_id"]) or games.get(str(r["game_id"])))
            out.append(dict(slate=slate, at=ctx.now.strftime("%Y-%m-%dT%H:%M:%SZ"), stage=stage, label=r["label"], game_id=r["game_id"],
                            player_id=r["player_id"], stat=r["stat"], side=r["selection"], line=r["line"], prob=r["prob"],
                            price_american=r["price_american"], posted=int(str(r["player_id"]) in posted_ids), **feats))
        if out:
            os.makedirs(f"{ctx.root}/ledger", exist_ok=True)
            with open(f"{ctx.root}/ledger/research_features.jsonl", "a") as fh:
                for o in out:
                    fh.write(json.dumps(o, sort_keys=True) + "\n")
        return len(out)
    except Exception as e:
        try:
            ctx.fail("research_log", e)
        except Exception:
            pass
        return 0
