"""Discord signal ingestion (manual-import fallback) and provider tracking.

No Discord bot token or channel access was granted, so automated reading is not
built against a live server. Signals are imported from data/manual/signals.csv
(provider, posted_at, text[, channel]): paste a message, keep its timestamp.
Each message is parsed conservatively. Anything ambiguous is stored as raw text
with parse_status 'ambiguous' or 'unparsed' and never guessed into a pick.
Parsed picks become predictions with origin='signal' and decision='info', so they
settle like everything else but are tracked separately from the model.
"""
from __future__ import annotations

import csv
import datetime as dt
import os
import re
from zoneinfo import ZoneInfo

from . import odds as O
from .store import stable_id
from .teams import TEAMS, canon, from_name

ODDS = r"(?P<odds>[+-]\d{3,4}|even|ev)"
UNITS = re.compile(r"(?P<u>\d+(?:\.\d+)?)\s*u(?:nits?)?\b", re.I)
STAT = {"pts": "pts", "points": "pts", "reb": "reb", "rebs": "reb", "rebounds": "reb", "ast": "ast", "asts": "ast",
        "assists": "ast", "3pm": "fg3m", "threes": "fg3m", "3s": "fg3m"}
TEAM_WORDS = {**{a.lower(): a for a in TEAMS}, **{n.lower(): a for a, n in TEAMS.items()},
              "nyk": "NY", "gsw": "GS", "sas": "SA", "nop": "NO", "uta": "UTAH", "was": "WSH", "bkn": "BKN", "brk": "BKN",
              "sixers": "PHI", "blazers": "POR", "cavs": "CLE", "mavs": "DAL", "wolves": "MIN", "knicks": "NY"}


def find_team(text: str) -> list[str]:
    toks = re.findall(r"[a-z0-9]+", text.lower())
    found = []
    for i, t in enumerate(toks):
        two = " ".join(toks[i:i + 2])
        a = TEAM_WORDS.get(two) or TEAM_WORDS.get(t)
        if a and a not in found:
            found.append(a)
    return found


def parse_line(line: str) -> dict | None:
    """One pick per line. Returns a dict or None if the line is not a pick."""
    s = line.strip()
    if not s:
        return None
    um = UNITS.search(s)
    units = float(um.group("u")) if um else None
    om = re.search(ODDS + r"\)?\s*(?:\d+(?:\.\d+)?\s*u)?\s*$", s, re.I) or re.search(r"\(" + ODDS + r"\)", s, re.I)
    american = None
    if om:
        o = om.group("odds").lower()
        american = 100.0 if o in ("even", "ev") else float(o)
    body = s[:om.start()] if om else s
    teams = find_team(body)
    # player prop: "<name> o/over 27.5 pts"
    pm = re.search(r"^(?P<name>[A-Za-z.'\- ]+?)\s+(?P<side>o|u|over|under)\s*(?P<line>\d+(?:\.\d+)?)\s*(?P<stat>pts|points|reb|rebs|rebounds|ast|asts|assists|3pm|threes|3s)\b", body, re.I)
    if pm and not find_team(pm.group("name")):
        return dict(market="prop", selection="over" if pm.group("side").lower().startswith("o") else "under",
                    line=float(pm.group("line")), player_name=pm.group("name").strip(), stat=STAT[pm.group("stat").lower()],
                    american=american, units=units, teams=[])
    tm = re.search(r"\b(?P<side>o|u|over|under)\s*(?P<line>\d{3}(?:\.\d)?)\b", body, re.I)
    if tm:
        return dict(market="total", selection="over" if tm.group("side").lower().startswith("o") else "under",
                    line=float(tm.group("line")), american=american, units=units, teams=teams)
    if len(teams) == 1:
        if re.search(r"\b(ml|moneyline|to win)\b", body, re.I):
            return dict(market="ml", team=teams[0], line=None, american=american, units=units, teams=teams)
        sm = re.search(r"(?<![\d.])(?P<line>[+-]\d{1,2}(?:\.5)?|pk|pick'?em)\b", body, re.I)
        if sm:
            v = sm.group("line").lower()
            return dict(market="spread", team=teams[0], line=0.0 if v.startswith("pick") or v == "pk" else float(v),
                        american=american, units=units, teams=teams)
    return None


def import_csv(ctx, path: str | None = None) -> dict:
    path = path or f"{ctx.root}/manual/signals.csv"
    out = dict(raw_new=0, picks=0, ambiguous=0, unparsed=0)
    if not os.path.exists(path):
        return out
    games = ctx.store.q("SELECT * FROM games")
    players = player_teams(ctx)
    with open(path) as fh:
        for row in csv.DictReader(fh):
            if not row.get("text") or not row.get("posted_at"):
                continue
            raw_id = stable_id(row["provider"], row["posted_at"], row["text"])
            if ctx.store.one("SELECT 1 FROM signals_raw WHERE raw_id = ?", [raw_id]):
                continue
            try:
                posted = dt.datetime.fromisoformat(row["posted_at"].replace("Z", "+00:00"))
                if posted.tzinfo is None:
                    raise ValueError("posted_at needs a time zone (end it with Z for UTC)")
            except ValueError as e:
                ctx.store.put("signals_raw", dict(raw_id=raw_id, provider=row.get("provider") or "?", posted_at=row["posted_at"],
                                                  text=row["text"], channel=row.get("channel"), parse_status="unparsed",
                                                  parse_error=f"bad posted_at: {e}"[:500], pred_ids=[],
                                                  imported_at=ctx.now.strftime("%Y-%m-%dT%H:%M:%SZ")))
                out["raw_new"] += 1; out["unparsed"] += 1
                continue
            slate = posted.astimezone(ZoneInfo(ctx.tz)).date().isoformat()
            day_games = [g for g in games if _slate(g["start_utc"], ctx.tz) == slate
                         and dt.datetime.fromisoformat(g["start_utc"].replace("Z", "+00:00")) > posted]
            pred_ids, problems = [], []
            for line in row["text"].splitlines():
                p = parse_line(line)
                if not p:
                    continue
                g, sel, err = _resolve(p, day_games, players)
                if err:
                    problems.append(f"{line.strip()}: {err}"); continue
                if p.get("american") is None:
                    problems.append(f"{line.strip()}: no odds stated (not invented)"); continue
                pid = stable_id("signal", raw_id, line)
                ctx.store.put("predictions", dict(
                    pred_id=pid, created_at=row["posted_at"], origin="signal", provider=row["provider"], category="straight",
                    game_id=g["game_id"], market=p["market"], selection=sel, line=p.get("line"),
                    player_id=players.get(_norm(p.get("player_name") or ""), (None, None))[0] if p["market"] == "prop" else None,
                    player_name=p.get("player_name"), stat=p.get("stat"), price_dec=O.american_to_decimal(p["american"]),
                    book=row.get("book") or "as stated", price_observed_at=row["posted_at"], price_source="discord",
                    decision="info", reason=f"imported signal: {line.strip()[:120]}", stake_units=p.get("units") or 1.0,
                    inputs=dict(raw_id=raw_id)))
                pred_ids.append(pid)
            status = "parsed" if pred_ids and not problems else "ambiguous" if problems else "unparsed"
            ctx.store.put("signals_raw", dict(raw_id=raw_id, provider=row["provider"], posted_at=row["posted_at"], text=row["text"],
                                              channel=row.get("channel"), parse_status=status,
                                              parse_error="; ".join(problems)[:500] or None, pred_ids=pred_ids,
                                              imported_at=ctx.now.strftime("%Y-%m-%dT%H:%M:%SZ")))
            out["raw_new"] += 1; out["picks"] += len(pred_ids); out["ambiguous"] += bool(problems)
            out["unparsed"] += status == "unparsed"
    return out


def _slate(start_utc, tz):
    return dt.datetime.fromisoformat(start_utc.replace("Z", "+00:00")).astimezone(ZoneInfo(tz)).date().isoformat()


def _resolve(p, games, players=None):
    if p["market"] == "prop":
        # player -> team from the latest box score row before the game; the game is that team's game
        team = (players or {}).get(_norm(p.get("player_name") or ""), (None, None))[1]
        if not team:
            return None, None, "player not found in box scores (needs a player-to-team mapping)"
        cand = [g for g in games if team in (g["home"], g["away"])]
        if len(cand) != 1:
            return None, None, f"{len(cand)} games for {team} before tip"
        return cand[0], p["selection"], None
    teams = p["teams"]
    cand = [g for g in games if any(t in (g["home"], g["away"]) for t in teams)]
    if p["market"] == "total" and len(teams) == 0:
        return None, None, "total without a team"
    if len(cand) != 1:
        return None, None, f"{len(cand)} matching games before tip"
    g = cand[0]
    if p["market"] == "total":
        return g, p["selection"], None
    return g, "home" if p["team"] == g["home"] else "away", None


def _norm(name: str) -> str:
    return "".join(ch for ch in name.lower() if ch.isalpha())


def player_teams(ctx) -> dict:
    """normalised player name -> (player_id, team) from the most recent box score row in the ledger."""
    out = {}
    rows = ctx.store.q("""SELECT b.player_id, b.player_name, b.team, g.start_utc FROM player_games b
                          JOIN games g ON g.game_id = b.game_id ORDER BY g.start_utc""")
    for r in rows:
        if r["player_name"]:
            out[_norm(r["player_name"])] = (str(r["player_id"]), r["team"])
    return out


def compare_with_model(ctx) -> dict:
    """For each external signal, the model's own view of the same bet: the latest model prediction for
    the same game, market, side, line (and player/stat) made before tip. Recorded once per (signal,
    model version) as a 'note' event; the signal itself is never changed and never becomes model truth."""
    from .store import stable_id as sid
    out = dict(compared=0, no_model_view=0)
    sigs = ctx.store.q("SELECT * FROM predictions WHERE origin = 'signal' AND category = 'straight'")
    if not sigs:
        return out
    model = ctx.store.q("SELECT * FROM predictions WHERE origin = 'model' AND category = 'straight' AND prob IS NOT NULL")
    by = {}
    for m in model:
        by.setdefault((m["game_id"], m["market"], m["selection"], m["line"], m["player_id"], m["stat"]), []).append(m)
    starts = {g["game_id"]: g["start_utc"] for g in ctx.store.q("SELECT game_id, start_utc FROM games")}
    for s in sigs:
        k = (s["game_id"], s["market"], s["selection"], s["line"], s["player_id"], s["stat"])
        ms = sorted((m for m in by.get(k, []) if m["created_at"] < (starts.get(s["game_id"]) or "9")), key=lambda m: m["created_at"])
        if not ms:
            out["no_model_view"] += 1
            continue
        before = [m for m in ms if m["created_at"] <= s["created_at"]]
        m = (before or ms)[-1]
        ev = O.ev_with_push(m["prob"], m["prob_push"] or 0.0, s["price_dec"]) if s["price_dec"] else None
        eid = sid(s["pred_id"], "model_compare", m["pred_id"])
        if ctx.store.one("SELECT 1 FROM pred_events WHERE event_id = ?", [eid]):
            continue
        ctx.store.put("pred_events", dict(event_id=eid, pred_id=s["pred_id"], at=ctx.now.strftime("%Y-%m-%dT%H:%M:%SZ"), type="note",
                                          data=dict(model_compare=dict(model_pred_id=m["pred_id"], model_version=m["model_version"],
                                                                       model_prob=m["prob"], model_ev_at_signal_price=ev,
                                                                       model_decision=m["decision"],
                                                                       independently_qualifies=m["decision"] == "eligible",
                                                                       model_view_after_signal=not before))))
        out["compared"] += 1
    return out
