"""Discord publishing: daily picks and the end-of-day recap. Nothing else posts.

Idempotent: every message has a publication id (kind + slate date + mode). A
'sent' record in the ledger means it is never sent again; a failed send is
recorded and retried on the next run. Dry-run builds and records the message
without sending. The webhook URL comes from an environment secret only.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import time
import urllib.request

from . import odds as O
from .store import Store

LIMIT = 1900


def fmt_american(dec: float | None) -> str:
    if dec is None or dec <= 1:
        return "n/a"
    a = O.decimal_to_american(dec)
    return f"{a:+d}"


def local_time(start_utc: str, tz: str) -> str:
    from zoneinfo import ZoneInfo
    t = dt.datetime.fromisoformat(start_utc.replace("Z", "+00:00")).astimezone(ZoneInfo(tz))
    return t.strftime("%-I:%M %p")


def picks_message(slate: str, picks: list[dict], parlays: list[dict], cfg: dict, n_considered: int, why_none: str = "") -> str:
    tz = cfg["timezone"]
    paper = any(p.get("status") == "paper" for p in picks + parlays)
    head = f"**NBA Picks — {slate}**"
    if paper:
        head += "\nPAPER: these come from models still being validated. They are tracked, not proven."
    if not picks and not parlays:
        return (f"{head}\nNo picks today. {n_considered} prices checked; none cleared every check."
                + (f"\n{why_none}" if why_none else "") + "\nNo pick is better than a forced one.")
    lines = [head, ""]
    for p in picks:
        lines.append(f"**{p['label']}** ({p['away']} @ {p['home']}, {local_time(p['start_utc'], tz)})")
        lines.append(f"  {p['book']} {fmt_american(p['price_dec'])} at {p['price_time']} · model {p['prob']:.1%} vs "
                     f"break-even {1 / p['price_dec']:.1%} · EV {p['ev']:+.1%} · {p['stake']:g}u")
        lines.append(f"  FanDuel: bet only at {fmt_american(p['min_price_dec'])} or better")
        if p.get("caveat"):
            lines.append(f"  Note: {p['caveat']}")
        lines.append(f"  `{p['pred_id']}` {p['model_version']}")
    for z in parlays:
        tag = "Lotto parlay" if z["kind"] == "lotto" else "Parlay"
        lines.append("")
        lines.append(f"**{tag}** ({len(z['legs'])} legs, {z['stake']:g}u): " + " + ".join(z["leg_labels"]))
        lines.append(f"  combined {fmt_american(z['price_dec'])} · joint {z['prob']:.1%} · EV {z['ev']:+.1%}"
                     + (" · long shot: expect to lose most of these" if z["kind"] == "lotto" else ""))
        lines.append(f"  `{z['pred_id']}`")
    lines += ["", "Research tool, not advice. Prices move; check FanDuel before betting. Bets are placed by you, manually."]
    return "\n".join(lines)


def recap_message(slate: str, rows: list[dict], wagers: list[dict], notes: list[str]) -> str:
    settled = [r for r in rows if r["result"] in ("win", "loss", "push", "void")]
    pending = [r for r in rows if r["result"] == "pending"]
    w = sum(r["result"] == "win" for r in settled); l = sum(r["result"] == "loss" for r in settled)
    pu = sum(r["result"] in ("push", "void") for r in settled)
    units = sum(r["net"] or 0 for r in settled)
    staked = sum(r["stake"] for r in settled if r["result"] in ("win", "loss"))
    lines = [f"**NBA Picks recap — {slate}**"]
    if not rows:
        lines.append("No picks were published for this slate.")
    else:
        lines.append(f"Published picks: {w}-{l}" + (f"-{pu} push/void" if pu else "") +
                     f" · {units:+.2f}u on {staked:g}u staked (at the recorded prices; theoretical)")
        for r in rows:
            mark = {"win": "W", "loss": "L", "push": "P", "void": "V", "pending": "…"}[r["result"]]
            lines.append(f"  {mark} {r['label']} {fmt_american(r['price_dec'])} → "
                         + ("pending" if r["net"] is None else format(r["net"], "+.2f") + "u"))
        if pending:
            lines.append(f"{len(pending)} still pending.")
    if wagers:
        wn = sum(x["net"] or 0 for x in wagers if x["net"] is not None)
        lines.append(f"Your confirmed bets: {len(wagers)} · {wn:+.2f} (actual, from your wager log)")
    else:
        lines.append("Your confirmed bets: none logged for this slate.")
    for n in notes:
        lines.append(f"Note: {n}")
    return "\n".join(lines)


def split(msg: str) -> list[str]:
    """Parts of at most LIMIT characters, broken at line ends; a single over-long line is cut."""
    parts, cur = [], ""
    for line in msg.split("\n"):
        while len(line) > LIMIT - 1:
            if cur.strip():
                parts.append(cur); cur = ""
            parts.append(line[:LIMIT - 1] + "\n"); line = line[LIMIT - 1:]
        if cur and len(cur) + len(line) + 1 > LIMIT:
            parts.append(cur); cur = ""
        cur += line + "\n"
    if cur.strip():
        parts.append(cur)
    return parts


def publish(store: Store, kind: str, slate: str, msg: str, cfg: dict, now: str, sender=None) -> str:
    """Returns the publication status. Never sends twice."""
    dry = cfg["publishing"]["dry_run"]
    mode = "dry" if dry else "live"
    pub_id = f"{kind}:{slate}:{mode}"
    sha = hashlib.sha256(msg.encode()).hexdigest()[:16]
    prev = store.one("SELECT * FROM publications WHERE pub_id = ?", [pub_id])
    if prev and prev["status"] in ("sent", "dry_run"):
        return "already_" + prev["status"]
    if dry:
        store.put("publications", dict(pub_id=pub_id, kind=kind, slate_date=slate, at=now, status="dry_run",
                                       message_sha=sha, detail=msg))
        return "dry_run"
    url = os.environ.get(cfg["publishing"]["webhook_secret"], "")
    if not url.startswith("https://discord.com/api/webhooks/") and not url.startswith("https://discordapp.com/api/webhooks/"):
        store.put("publications", dict(pub_id=pub_id, kind=kind, slate_date=slate, at=now, status="failed",
                                       message_sha=sha, detail="webhook secret missing or not a Discord webhook URL"))
        return "failed"
    sender = sender or _send
    # resume a partly sent message: re-send neither the parts already posted nor a different text
    done, ids = 0, []
    if prev and prev["status"] == "failed" and prev["detail"] and prev["detail"].startswith("{"):
        d = json.loads(prev["detail"])
        if d.get("sent_parts"):
            done, ids, msg, sha = d["sent_parts"], d.get("message_ids", []), d["message"], prev["message_sha"]
    parts = split(msg)
    try:
        for part in parts[done:]:
            ids.append(sender(url, part)); done += 1
        store.put("publications", dict(pub_id=pub_id, kind=kind, slate_date=slate, at=now, status="sent",
                                       message_sha=sha, detail=json.dumps({"message_ids": ids})))
        return "sent"
    except Exception as e:
        detail = json.dumps(dict(error=f"{type(e).__name__}: {str(e)[:200]}", sent_parts=done, message_ids=ids, message=msg)) \
            if done else f"{type(e).__name__}: {str(e)[:200]}"
        store.put("publications", dict(pub_id=pub_id, kind=kind, slate_date=slate, at=now, status="failed",
                                       message_sha=sha, detail=detail))
        return "failed"


def _send(url: str, content: str, retries: int = 3) -> str | None:
    body = json.dumps({"content": content, "allowed_mentions": {"parse": []}}).encode()
    for i in range(retries + 1):
        req = urllib.request.Request(url + "?wait=true", data=body, method="POST",
                                     headers={"Content-Type": "application/json", "User-Agent": "nbapicks"})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.loads(r.read() or b"{}").get("id")
        except urllib.error.HTTPError as e:
            if e.code == 429 and i < retries:
                time.sleep(min(30, float(json.loads(e.read() or b"{}").get("retry_after", 2))))
                continue
            if e.code >= 500 and i < retries:
                time.sleep(2 ** (i + 1)); continue
            raise
    return None
