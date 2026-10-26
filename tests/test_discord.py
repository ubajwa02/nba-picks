import copy
import pytest
from nbapicks import config, discord
from nbapicks.store import Store

CFG = config.load()
PICK = dict(label="ORL ML", away="ATL", home="ORL", start_utc="2026-10-21T23:00:00Z", book="DraftKings",
            price_dec=1.704, price_time="13:30 ET", prob=0.62, ev=0.057, stake=1.0, min_price_dec=1.66,
            pred_id="abc123", model_version="ratings-v1", status="paper")


def test_picks_message_contents():
    m = discord.picks_message("2026-10-21", [PICK], [], CFG, 40)
    assert "PAPER" in m and "ORL ML" in m and "-142" in m and "FanDuel: bet only at" in m
    assert "$" not in m and "7:00 PM" in m


def test_no_picks_message_explains():
    m = discord.picks_message("2026-10-21", [], [], CFG, 37, "Two games held for injuries.")
    assert "No picks today" in m and "37" in m and "held for injuries" in m


def test_recap_separates_theoretical_and_actual():
    rows = [dict(label="ORL ML", price_dec=1.7, result="win", net=0.7, stake=1.0),
            dict(label="BOS -3.5", price_dec=1.91, result="loss", net=-1.0, stake=1.0),
            dict(label="Over 230.5", price_dec=1.91, result="pending", net=None, stake=1.0)]
    m = discord.recap_message("2026-10-21", rows, [], ["DK price feed was stale for one game"])
    assert "1-1" in m and "-0.30u" in m and "theoretical" in m and "none logged" in m and "1 still pending" in m


def test_publish_is_idempotent_and_dry_by_default(tmp_path):
    s = Store(str(tmp_path))
    assert discord.publish(s, "picks", "2026-10-21", "hello", CFG, "t") == "dry_run"
    assert discord.publish(s, "picks", "2026-10-21", "hello", CFG, "t") == "already_dry_run"


def test_live_send_once_and_failure_recorded(tmp_path, monkeypatch):
    c = copy.deepcopy(CFG); c["publishing"]["dry_run"] = False
    s = Store(str(tmp_path)); sent = []
    monkeypatch.delenv("NBA_DISCORD_WEBHOOK_URL", raising=False)
    assert discord.publish(s, "picks", "d1", "x", c, "t", sender=lambda u, m: sent.append(m)) == "failed"
    monkeypatch.setenv("NBA_DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/1/abc")
    assert discord.publish(s, "picks", "d1", "x", c, "t", sender=lambda u, m: sent.append(m) or "id1") == "sent"
    assert discord.publish(s, "picks", "d1", "x", c, "t", sender=lambda u, m: sent.append(m)) == "already_sent"
    assert len(sent) == 1
    def boom(u, m):
        raise RuntimeError("discord down")
    assert discord.publish(s, "recap", "d1", "y", c, "t", sender=boom) == "failed"
    assert discord.publish(s, "recap", "d1", "y", c, "t", sender=lambda u, m: "id2") == "sent"   # retried next run


def test_split_long_messages():
    parts = discord.split("\n".join(["x" * 100] * 50))
    assert len(parts) >= 3 and all(len(p) <= discord.LIMIT + 101 for p in parts)
