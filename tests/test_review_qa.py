"""Independent QA repros. Each test asserts the CORRECT behaviour; a failure = bug confirmed."""
import datetime as dt, json, os, shutil
import pytest
from nbapicks import pipeline, discord
from nbapicks.store import Store, LedgerError
from tests.test_e2e import env, NOW, load  # noqa: F401  (fixture)


def test_publish_rerun_later_does_not_crash(env):
    root, cfg, state = env
    ctx = pipeline.Ctx(NOW, cfg, root)
    pipeline.ingest(ctx); pipeline.predict(ctx)
    assert pipeline.publish_picks(ctx) == "dry_run"
    ctx.save_state()
    later = pipeline.Ctx(NOW + dt.timedelta(minutes=30), cfg, root)   # e.g. manual "publish" re-run
    assert pipeline.publish_picks(later) == "already_dry_run"


def test_publish_refuses_stale_prediction_run(env):
    """20:30 run: predict step fails, publish still posts the 15:00 run's picks."""
    root, cfg, state = env
    ctx = pipeline.Ctx(NOW, cfg, root)
    pipeline.ingest(ctx); pipeline.predict(ctx); ctx.save_state()
    later = pipeline.Ctx(NOW + dt.timedelta(hours=5, minutes=30), cfg, root)
    st = pipeline.publish_picks(later)
    assert st.startswith("skipped"), st


WHDR = "placed_at,book,game_id,market,selection,line,price_american,price_dec,stake,units,pred_id,player_id,stat,notes\n"

def _wagers(root, text):
    os.makedirs(f"{root}/manual", exist_ok=True)
    open(f"{root}/manual/wagers.csv", "w").write(text)


def test_adding_csv_column_does_not_duplicate_wagers(env):
    root, cfg, state = env
    ctx = pipeline.Ctx(NOW, cfg, root); pipeline.ingest(ctx)
    gid = ctx.store.q("SELECT game_id FROM games")[0]["game_id"]
    row = f"2026-10-21T17:00:00Z,FanDuel,{gid},ml,home,,-140,,10,1,,,,x"
    _wagers(root, WHDR + row + "\n"); pipeline.import_wagers(ctx)
    _wagers(root, WHDR.strip() + ",tag\n" + row + ",\n"); pipeline.import_wagers(ctx)  # user adds a column
    assert ctx.store.one("SELECT count(*) n FROM wagers")["n"] == 1


def test_bad_wager_row_does_not_break_settle(env):
    root, cfg, state = env
    ctx = pipeline.Ctx(NOW, cfg, root); pipeline.ingest(ctx); ctx.save_state()
    gids = [g["game_id"] for g in ctx.store.q("SELECT game_id FROM games")]
    _wagers(root, WHDR + f"2026-10-21T17:00:00Z,FanDuel,{gids[0]},spread,home,,-110,,10,1,,,,missing line\n"
                         f"2026-10-21T17:00:00Z,FanDuel,{gids[1]},ml,home,,-140,,10,1,,,,good\n")
    state["final"] = True
    later = pipeline.Ctx(NOW + dt.timedelta(hours=14), cfg, root); pipeline.ingest(later)
    out = pipeline.settle(later)        # raises ValueError('spread needs a line') today
    assert out.get("wagers_settled") == 1


def test_one_bad_signal_row_does_not_block_others(env):
    root, cfg, state = env
    ctx = pipeline.Ctx(NOW, cfg, root)
    os.makedirs(f"{root}/manual", exist_ok=True)
    open(f"{root}/manual/signals.csv", "w").write(
        'provider,posted_at,text,channel\n'
        'A,2026-10-21 15:00,"Magic ML -140",x\n'          # naive timestamp (no Z)
        'B,2026-10-21T15:00:00Z,"Magic ML -150",x\n')
    out = pipeline.ingest(ctx)
    assert out.get("signals_raw_new", 0) >= 1, (out, ctx.notes)


def test_truncated_last_ledger_line_is_survivable(tmp_path):
    root = str(tmp_path)
    s = Store(root)
    s.put("audit", dict(audit_id="a1", at="t", actor="x", action="y"))
    with open(f"{root}/ledger/audit.jsonl", "a") as fh:
        fh.write('{"audit_id": "a2", "at": "t", "act')        # killed mid-write
    Store(root)   # LedgerError today: every later run (incl. export) dies at Ctx()


def test_partial_discord_send_not_repeated(tmp_path):
    s = Store(str(tmp_path)); cfg = dict(publishing=dict(dry_run=False, webhook_secret="W"))
    os.environ["W"] = "https://discord.com/api/webhooks/1/x"
    sent = []
    def flaky(url, part):
        if len(sent) == 1: raise RuntimeError("500")
        sent.append(part); return "id"
    msg = "\n".join("line %d %s" % (i, "x" * 80) for i in range(60))
    assert discord.publish(s, "picks", "2026-10-21", msg, cfg, "t", sender=flaky) == "failed"
    discord.publish(s, "picks", "2026-10-21", msg, cfg, "t2", sender=lambda u, p: sent.append(p) or "id")
    assert sent.count(sent[0]) == 1, "part 1 posted twice"


def test_recap_not_sent_for_empty_slate(tmp_path):
    from nbapicks import config
    cfg = config.load(); cfg["publishing"]["dry_run"] = True
    ctx = pipeline.Ctx(dt.datetime(2026, 7, 15, 7, tzinfo=dt.timezone.utc), cfg, str(tmp_path))
    assert pipeline.recap(ctx).startswith("skipped")     # offseason: daily empty recap today


def test_split_never_emits_empty_or_oversized_part():
    parts = discord.split("x" * 2500 + "\nshort")
    assert all(0 < len(p) <= 2000 for p in parts), [len(p) for p in parts]


def test_live_espn_book_name_draft_kings_is_used(env, monkeypatch):
    """Live ledger (data/ledger/odds/2026-10.jsonl) shows ESPN provider name 'Draft Kings'."""
    from nbapicks.sources import espn
    root, cfg, state = env
    d = load("espn_core_odds_pre.json")
    s = json.dumps(d).replace('"DraftKings"', '"Draft Kings"')
    monkeypatch.setattr(espn, "fetch_core_odds", lambda gid: json.loads(s))
    ctx = pipeline.Ctx(NOW, cfg, root); pipeline.ingest(ctx); pipeline.predict(ctx)
    books = {p["book"] for p in ctx.store.q("SELECT book FROM predictions WHERE market IN ('ml','spread','total')")}
    assert any("Draft" in b for b in books), books


def test_second_predict_publish_does_not_double_paper_record(env):
    root, cfg, state = env
    ctx = pipeline.Ctx(NOW, cfg, root); pipeline.ingest(ctx); pipeline.predict(ctx); pipeline.publish_picks(ctx); ctx.save_state()
    n1 = ctx.store.one("SELECT count(*) n FROM pred_events WHERE type='note'")["n"]
    c2 = pipeline.Ctx(NOW + dt.timedelta(minutes=20), cfg, root); pipeline.predict(c2)
    assert pipeline.publish_picks(c2) == "already_dry_run"
    n2 = c2.store.one("SELECT count(*) n FROM pred_events WHERE type='note'")["n"]
    assert n1 > 0 and n2 == n1, (n1, n2)


def test_injury_reobservation_is_idempotent(env):
    root, cfg, state = env
    ctx = pipeline.Ctx(NOW, cfg, root); pipeline.ingest(ctx); ctx.save_state()
    c2 = pipeline.Ctx(NOW + dt.timedelta(hours=1), cfg, root); pipeline.ingest(c2)
    assert c2.health["espn_injuries"]["consecutive_failures"] == 0, c2.notes


def test_failed_put_does_not_wipe_replayed_ledger_and_resend_recap(env):
    """07:00 run sends the recap; 13:00 catch-up run (nothing changed) must not send it again."""
    root, cfg, state = env
    ctx = pipeline.Ctx(NOW, cfg, root); pipeline.ingest(ctx); pipeline.predict(ctx); pipeline.publish_picks(ctx); ctx.save_state()
    state["final"] = True
    r1 = pipeline.Ctx(dt.datetime(2026, 10, 22, 7, tzinfo=dt.timezone.utc), cfg, root)
    pipeline.ingest(r1); pipeline.settle(r1)
    assert pipeline.recap(r1) == "dry_run"; r1.save_state()
    r2 = pipeline.Ctx(dt.datetime(2026, 10, 22, 13, tzinfo=dt.timezone.utc), cfg, root)
    n_before = r2.store.one("SELECT count(*) n FROM predictions")["n"]
    pipeline.ingest(r2); pipeline.settle(r2)
    n_after = r2.store.one("SELECT count(*) n FROM predictions")["n"]
    st = pipeline.recap(r2)
    assert n_after == n_before and st == "already_dry_run", (n_before, n_after, st, r2.notes)
