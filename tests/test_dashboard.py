"""Dashboard export (nbapicks/dashboard.py) and page (site/index.html) on temp ledgers:
populated, empty, and a slate with zero games. Every number checked here is derived from
rows written through nbapicks.store.Store in the test itself."""
import datetime as dt
import json
import os
import re
import shutil
import subprocess

import pytest

from nbapicks import config, pipeline
from nbapicks import dashboard
from nbapicks.dashboard import MAX_BYTES, export, pick_label
from nbapicks.store import Store

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOW = dt.datetime(2026, 10, 21, 16, 0, tzinfo=dt.timezone.utc)        # 12:00 in Toronto: slate 2026-10-21
SECTIONS = ("meta", "tickets", "today", "picks_by_day", "performance", "players", "valuation", "backtests", "research", "settings")
POPS = ("qualified", "all_model", "posted_leans", "signals", "wagers")

EXPLAIN = dict(season=dict(avg=21.3, n=12), last5=[24, 18, 22, 25, 19], last10_avg=21.0, line_hits=dict(h=4, n=5),
               line_hits_last10=dict(h=7, n=10), vs_opp=dict(h=2, n=3, avg=20.5), exp_minutes=33.5, minutes_basis="last 10",
               role="starter", teammates_out=["A. Player"], injury_status=None, opp_def=dict(rank=7, teams=30, allowed_pg=22.1),
               mean=21.2, sd=5.1, flags=["low_sample"])


@pytest.fixture
def cfg():
    c = config.load(os.path.join(REPO, "config", "nbapicks.yaml"))
    c["quality"]["max_odds_age_minutes"] = 120
    return c


@pytest.fixture
def cwd(tmp_path, monkeypatch):
    """Run in an empty working directory: reports/, data/research, team/ and config/gates.yaml are all missing."""
    d = tmp_path / "cwd"
    d.mkdir()
    monkeypatch.chdir(d)
    return d


def game(gid, start, home, away, status="scheduled", hs=None, as_=None):
    return dict(game_id=gid, season=2027, season_type="regular", start_utc=start, home=home, away=away, status=status,
                home_score=hs, away_score=as_, observed_at="2026-10-21T15:00:00Z", source="test")


def pred(pid, gid, market, selection, line, price, prob, decision, created="2026-10-20T20:00:00Z", run="run-y", **kw):
    inputs = kw.pop("inputs", {})
    rec = dict(pred_id=pid, created_at=created, origin="model", provider="nbapicks", model_version="test-v1", category="straight",
               game_id=gid, market=market, selection=selection, line=line, price_dec=price, book="DraftKings",
               price_observed_at=created, price_source="espn", prob=prob, prob_push=0.0,
               ev=(prob * (price - 1) - (1 - prob)) if (price and prob is not None) else None, edge_threshold=0.03,
               min_price_dec=None, decision=decision, reason=f"test {decision}", stake_units=1.0 if decision == "eligible" else None,
               inputs=dict(dict(status="research", fair=None), **inputs), run_id=run)
    rec.update(kw)
    return rec


def settle_ev(pid, result, net):
    return dict(event_id=f"s-{pid}", pred_id=pid, at="2026-10-21T05:00:00Z", type="settled", result=result, net_units=net,
                data=dict(stake=1.0))


def populated(root):
    ctx_store = Store(root)
    s = ctx_store
    s.put("games", game("g1", "2026-10-20T23:00Z", "DET", "BOS", "final", 110, 104))          # yesterday, final
    s.put("games", game("g2", "2026-10-21T23:30Z", "NYK", "MIA"))                               # today, scheduled
    s.put("games", game("g3", "2026-10-21T17:00Z", "LAL", "GSW", "in_progress", 50, 48))        # today, live
    s.put("player_games", dict(game_id="g1", player_id="p9", player_name="Jay Test", team="DET", starter=1, minutes=34,
                               pts=24, reb=5, ast=4, fg3m=2, stl=1, blk=0, tov=2, played=1, observed_at="2026-10-21T05:00:00Z"))
    rows = [
        # an earlier version of the same prop candidate (different price): counted once, versions=2
        pred("old", "g1", "prop", "over", 19.5, 1.80, 0.58, "eligible", created="2026-10-20T15:00:00Z", player_id="p9",
             player_name="Jay Test", stat="pts", inputs=dict(explain=EXPLAIN, price_basis="conservative")),
        pred("win", "g1", "prop", "over", 19.5, 1.91, 0.60, "eligible", player_id="p9", player_name="Jay Test", stat="pts",
             inputs=dict(explain=EXPLAIN, price_basis="conservative", quality_flags=["conservative_price"])),
        pred("loss", "g1", "ml", "home", None, 2.00, 0.55, "eligible", inputs=dict(fair=0.48)),
        pred("push", "g1", "spread", "home", -3.0, 1.90, 0.52, "hold", inputs=dict(fair=0.50)),
        pred("void", "g1", "prop", "under", 2.5, 1.80, 0.57, "reject", player_id="p9", player_name="Jay Test", stat="fg3m",
             inputs=dict(explain=dict(season=dict(avg=2.1, n=12)))),
        pred("pend", "g2", "total", "over", 224.5, 1.95, 0.56, "eligible", created="2026-10-21T15:30:00Z", run="run-t"),
        pred("noprice", "g2", "prop", "over", 5.5, None, 0.50, "reject", created="2026-10-21T15:30:00Z", run="run-t",
             player_id="p9", player_name="Jay Test", stat="ast", price_observed_at=None),
        pred("live", "g3", "spread", "away", 2.5, 1.91, 0.49, "watch", created="2026-10-21T15:30:00Z", run="run-t"),
    ]
    for r in rows:
        s.put("predictions", r)
    s.put("predictions", dict(pred("sig", "g1", "ml", "away", None, 2.10, None, "info"), origin="signal", provider="SharpGuy",
                              model_version=None))
    for pid, res, net in (("win", "win", 0.91), ("loss", "loss", -1.0), ("push", "push", 0.0), ("void", "void", 0.0),
                          ("sig", "win", 1.10), ("old", "win", 0.80)):
        s.put("pred_events", settle_ev(pid, res, net))
    s.put("wagers", dict(wager_id="w1", placed_at="2026-10-20T20:00:00Z", book="FanDuel", game_id="g1", market="ml",
                         selection="home", price_dec=2.0, stake=50.0, units=0.5, confirmed_by="test"))
    s.put("wager_events", dict(event_id="we1", wager_id="w1", at="2026-10-21T05:00:00Z", type="settled", result="loss", net=-50.0))
    os.makedirs(f"{root}/state", exist_ok=True)
    json.dump(dict(run_id="run-t", slate="2026-10-21", pred_ids=["pend", "noprice", "live"], candidates=40,
                   decisions={"total:eligible": 1}), open(f"{root}/state/last_predict.json", "w"))
    json.dump({"espn_odds": dict(consecutive_failures=2, last_error="2026-10-21T15:00:00Z", last_error_detail="HTTP 503")},
              open(f"{root}/state/source_health.json", "w"))
    with open(f"{root}/state/runs.jsonl", "w") as fh:
        fh.write(json.dumps(dict(at="2026-10-21T15:30:00Z", ok=False, steps=dict(
            ingest=dict(status="completed"), predict=dict(status="completed"),
            publish=dict(status="failed", error="RuntimeError: boom")))) + "\n")
    with open(f"{root}/ledger/posted_leans.jsonl", "w") as fh:
        fh.write(json.dumps(dict(slate="2026-10-20", game_id="g1", market="ml", selection="home", line=None, player_id=None,
                                 stat=None, price_american=100, label="DET ML", source="model_lean", stake=1.0, prob=0.55)) + "\n")


def run_export(cfg, root, out, **kw):
    ctx = pipeline.Ctx(NOW, cfg, str(root))
    e = export(ctx, str(out), **kw)
    return e, json.load(open(e["path"]))


def all_rows(d):
    for day in d["picks_by_day"]:
        yield from day["qualified"] + day["research"] + day["candidates"]


# ------------------------------------------------------------------ populated ledger
def test_populated_sections_and_populations(cfg, cwd, tmp_path):
    root = tmp_path / "data"
    populated(str(root))
    e, d = run_export(cfg, root, tmp_path / "site")
    for k in SECTIONS:
        assert k in d
    for k in POPS:
        assert k in d["performance"]
    assert d["meta"]["today"] == "2026-10-21" and d["meta"]["generated_at"] == "2026-10-21T16:00:00Z"

    q = d["performance"]["qualified"]
    # yesterday: win + loss settled; today's eligible total is pending and is NOT a loss
    assert (q["wins"], q["losses"], q["pending"]) == (1, 1, 1)
    assert q["units_staked"] == pytest.approx(2.0)
    assert q["net_units"] == pytest.approx(0.91 - 1.0, abs=1e-3)
    assert q["roi"] == pytest.approx(q["net_units"] / q["units_staked"], abs=1e-3)
    assert q["hit_rate"] == pytest.approx(0.5)

    a = d["performance"]["all_model"]
    assert a["title"] == "All model predictions (hypothetical, 1u each)"
    # each candidate once (the older 'old' version is dropped); no-price row excluded; signal row excluded
    assert (a["wins"], a["losses"], a["pushes"], a["voids"]) == (1, 1, 1, 1)
    assert a["pending"] == 2       # today's total and the live spread
    assert a["roi"] == pytest.approx(a["net_units"] / a["units_staked"], abs=1e-3)
    for k in POPS:
        b = d["performance"][k]
        assert b["net_dollars"] == pytest.approx(b["net_units"] * 100, abs=0.05) or k == "wagers"
        for sub in b["by_market"].values():
            assert sub["net_dollars"] == pytest.approx(sub["net_units"] * 100, abs=0.05) or k == "wagers"

    # actual wagers are their own population and never reach theoretical totals
    w = d["performance"]["wagers"]
    assert (w["n"], w["losses"]) == (1, 1) and w["net_dollars"] == pytest.approx(-50.0) and w["net_units"] == pytest.approx(-0.5)
    assert q["n"] == 3 and a["n"] == 6
    assert d["actual"]["summary"]["n"] == 1 and d["theoretical"]["summary"]["n"] == 0
    sg = d["performance"]["signals"]
    assert sg["wins"] == 1 and "SharpGuy" in sg["by_provider"]
    assert d["performance"]["posted_leans"]["n"] == 1
    assert [b["n"] for b in q["by_bucket"]] and sum(b["n"] for b in a["by_bucket"]) == 2   # win/loss rows with a prob

    # readable labels, conservative price flag, explain-only 'why'
    rows = {r["pred_id"]: r for r in all_rows(d)}
    assert rows["win"]["label"] == "Over 19.5 Points" and rows["win"]["player"] == "Jay Test"
    assert rows["void"]["label"] == "Under 2.5 Made Three-Pointers"
    assert rows["loss"]["label"] == "DET Moneyline"
    assert rows["push"]["label"] == "DET -3 Spread"
    assert rows["pend"]["label"] == "Over 224.5 Total Points"
    assert "old" not in rows and rows["win"]["versions"] == 2
    assert rows["win"]["conservative"] is True and rows["win"]["price_basis"] == "conservative"
    assert rows["win"]["status"] == "win" and rows["pend"]["status"] == "pending" and rows["void"]["status"] == "void"
    assert rows["win"]["price_american"] == -110 and rows["loss"]["price_american"] == 100
    assert rows["loss"]["implied"] == pytest.approx(0.5) and rows["loss"]["fair"] == pytest.approx(0.48)
    assert rows["win"]["return_dollars"] == pytest.approx(rows["win"]["return_units"] * 100)
    assert rows["win"]["team"] == "DET" and rows["win"]["opponent"] == "BOS"
    why = dict(rows["win"]["why"])
    assert why["Cleared this exact line"] == "4/5 games (80%)"
    assert why["Season average"] == "21.3 (n=12 games)"
    assert why["Injury status"] == "none reported"
    vwhy = dict(rows["void"]["why"])
    assert vwhy["Last 5 games (newest first)"] == "not available" and vwhy["Role"] == "not available"
    assert rows["loss"]["why"] is None            # no explain recorded: nothing invented
    assert rows["noprice"]["price_dec"] is None and rows["noprice"]["price_american"] is None

    # picks by day: today first, then yesterday; parlays separate
    assert [x["date"] for x in d["picks_by_day"]] == ["2026-10-21", "2026-10-20"]
    t = d["picks_by_day"][0]
    assert [r["pred_id"] for r in t["qualified"]] == ["pend"]

    # today: games, candidate set from last_predict.pred_ids, decision counts, yesterday's record
    T = d["today"]
    assert T["game_count"] == 2 and {g["status"] for g in T["games"]} == {"scheduled", "in_progress"}
    live = [g for g in T["games"] if g["status"] == "in_progress"][0]
    assert (live["home_score"], live["away_score"]) == (50, 48)
    assert set(T["candidate_ids"]) == {"pend", "noprice", "live"} and T["candidate_source"] == "last_predict.pred_ids"
    assert T["decision_counts"] == {"eligible": 1, "reject": 1, "watch": 1}
    assert T["leans"] == []            # the only posted lean is for the 2026-10-20 slate, not today
    assert T["overview"]["date"] == "2026-10-20" and T["overview"]["qualified"]["wins"] == 1

    # players: grouped, stale flag uses the configured threshold
    pl = {p["player"]: p for p in d["players"]["players"]}
    assert d["players"]["max_odds_age_minutes"] == 120
    assert "Jay Test" not in pl             # too little last-10 history to rank as a top player

    # meta: failures and stale flags
    m = d["meta"]
    assert m["stale"]["failed_sources"] and any("espn_odds" in w for w in m["warnings"])
    assert m["last_failed"][0]["step"] == "publish" and "boom" in m["last_failed"][0]["error"]
    assert m["last_success"]["predict"] == "2026-10-21T15:30:00Z"

    # valuation help and settings carry no secrets
    assert any("EV = p" in h[1] or "p × (d − 1)" in h[1] for h in d["valuation"]["help"])
    blob = open(e["path"]).read()
    assert "webhook_secret" not in blob and "NBA_DISCORD_WEBHOOK_URL" not in blob
    assert d["backtests"] == []                    # no reports/backtest_*.json in this cwd
    assert e["bytes"] < MAX_BYTES


def test_backtest_files_are_passed_through(cfg, cwd, tmp_path):
    os.makedirs("reports")
    run = dict(name="props-v1 pts (validate)", kind="props", market="prop:pts", split="validate", bets=10, wins=6, losses=4,
               pushes=0, voids=0, roi=None, roi_ci=None, price_basis="none", calibration=[])
    json.dump(dict(generated_at="2026-10-21T00:00:00Z", commit="abc", runs=[run]), open("reports/backtest_props.json", "w"))
    open("reports/backtest_broken.json", "w").write("not json")
    root = tmp_path / "data"
    populated(str(root))
    _, d = run_export(cfg, root, tmp_path / "site")
    good = [b for b in d["backtests"] if b["file"].endswith("backtest_props.json")][0]
    assert good["runs"][0]["roi"] is None and good["runs"][0]["name"] == run["name"]
    assert any(b["file"].endswith("backtest_broken.json") and b["runs"] == [] for b in d["backtests"])


def test_size_cap_trims_and_says_so(cfg, cwd, tmp_path):
    root = tmp_path / "data"
    populated(str(root))
    s = Store(str(root))
    for i in range(400):
        s.put("predictions", pred(f"bulk{i}", "g2", "prop", "over", 0.5 + i, 1.9, 0.4, "reject", created="2026-10-21T15:30:00Z",
                                  run="run-t", player_id=f"x{i % 40}", player_name=f"Bulk Player {i % 40}", stat="pts",
                                  reason="x" * 200))
    full, _ = run_export(cfg, root, tmp_path / "full")
    cap = full["bytes"] // 3
    e, d = run_export(cfg, root, tmp_path / "site", max_bytes=cap)
    assert e["bytes"] <= cap < full["bytes"]
    assert d["meta"]["capped"] and d["meta"]["caps"]["max_bytes"] == cap
    assert MAX_BYTES == 2_000_000


# ------------------------------------------------------------------ empty ledger, zero-game slate
def test_empty_ledger(cfg, cwd, tmp_path):
    e, d = run_export(cfg, tmp_path / "empty", tmp_path / "site")
    for k in SECTIONS:
        assert k in d
    for k in POPS:
        b = d["performance"][k]
        assert b["n"] == 0 and b["roi"] is None and b["hit_rate"] is None and b["net_dollars"] == 0
    assert d["today"]["games"] == [] and d["today"]["qualified"] == [] and d["today"]["overview"]["date"] is None
    assert [x["date"] for x in d["picks_by_day"]] == ["2026-10-21"]
    assert d["players"]["players"] == [] and d["valuation"]["rows"] == [] and d["backtests"] == []
    assert any("ingest" in w for w in d["meta"]["warnings"])           # nothing has ever run


def test_zero_game_slate(cfg, cwd, tmp_path):
    root = tmp_path / "data"
    s = Store(str(root))
    s.put("games", game("g1", "2026-10-20T23:00Z", "DET", "BOS", "final", 110, 104))
    s.put("predictions", pred("loss", "g1", "ml", "home", None, 2.0, 0.55, "eligible"))
    s.put("pred_events", settle_ev("loss", "loss", -1.0))
    _, d = run_export(cfg, root, tmp_path / "site")
    assert d["today"]["game_count"] == 0 and d["today"]["games"] == []
    assert d["picks_by_day"][0]["date"] == "2026-10-21" and d["picks_by_day"][0]["qualified"] == []
    assert d["picks_by_day"][1]["qualified"][0]["status"] == "loss"
    assert d["performance"]["qualified"]["losses"] == 1 and d["performance"]["qualified"]["net_dollars"] == -100
    assert not d["meta"]["stale"]["odds"]        # no games today: odds cannot be stale


def test_pick_label_forms():
    assert pick_label("prop", "over", 19.5, "pts") == "Over 19.5 Points"
    assert pick_label("prop", "under", 2.5, "fg3m") == "Under 2.5 Made Three-Pointers"
    assert pick_label("ml", "away", None, home="DET", away="BOS") == "BOS Moneyline"
    assert pick_label("spread", "away", -3.5, home="DET", away="BOS") == "BOS -3.5 Spread"
    assert pick_label("total", "over", 224.5) == "Over 224.5 Total Points"
    assert "Unverified" in pick_label("prop", "side0", 5.5, "ast")


# ------------------------------------------------------------------ page: JS smoke test (skipped without node)
HARNESS = r"""
const fs = require("fs"), vm = require("vm");
const html = fs.readFileSync(process.argv[2], "utf8");
const src = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]).join("\n").replace(/\bboot\(\);\s*$/, "");
const el = () => ({textContent: "", innerHTML: "", value: "", dataset: {}, classList: {add() {}}, addEventListener() {}, setAttribute() {}});
const sandbox = {document: {querySelector: el, querySelectorAll: () => []}, window: {addEventListener() {}, scrollTo() {}},
  location: {hash: ""}, localStorage: {getItem: () => null, setItem() {}}, console, Date, Math, JSON, Object, Number, String, Set, isNaN};
const out = {};
sandbox.__DATA__ = JSON.parse(fs.readFileSync(process.argv[3], "utf8"));
sandbox.__OUT__ = out;
vm.runInNewContext(src + "\nD = __DATA__; for (const [k] of VIEWS) __OUT__[k] = R[k]();", sandbox);
for (const [k, v] of Object.entries(out)) { if (typeof v !== "string" || !v.length) throw new Error("empty view " + k); }
process.stdout.write(JSON.stringify(Object.fromEntries(Object.entries(out).map(([k, v]) => [k, v.length]))));
"""


def _node():
    return shutil.which("node")


@pytest.mark.skipif(not _node(), reason="node is not installed")
def test_page_script_parses_and_renders(cfg, cwd, tmp_path):
    page = os.path.join(REPO, "site", "index.html")
    html = open(page).read()
    assert '<script id="embedded" type="application/json"></script>' in html and 'fetch("data.json"' in html
    script = "\n".join(re.findall(r"<script>([\s\S]*?)</script>", html))
    (tmp_path / "page.js").write_text(script)
    subprocess.run([_node(), "--check", str(tmp_path / "page.js")], check=True, capture_output=True)
    (tmp_path / "harness.js").write_text(HARNESS)
    root = tmp_path / "data"
    populated(str(root))
    views = {}
    for name, r in (("populated", root), ("empty", tmp_path / "empty")):
        e, _ = run_export(cfg, r, tmp_path / f"site-{name}")
        p = subprocess.run([_node(), str(tmp_path / "harness.js"), page, e["path"]], capture_output=True, text=True)
        assert p.returncode == 0, p.stderr
        views[name] = json.loads(p.stdout)
    assert set(views["populated"]) == {"today", "picks", "performance", "parlays", "lottos", "players", "settings"}


def test_top_players_keeps_ten_players_three_props_and_drops_junk_prices():
    def prop(prob, dec=1.9, flags=(), n=10):
        return dict(prob=prob, price_dec=dec, flags=list(flags), line_hits_last10=dict(h=5, n=n))
    plist = [dict(player=f"P{i}", props=[prop(0.5 + i / 100), prop(0.45), prop(0.44), prop(0.43)]) for i in range(12)]
    plist.append(dict(player="Junk", props=[prop(0.99, dec=1.02), prop(0.98, flags=["milestone_one_sided"]),
                                            prop(0.97, flags=["side_unverified"]), prop(0.96, n=2)]))
    top = dashboard.top_players(plist)
    assert len(top) == 10 and top[0]["player"] == "P11" and "Junk" not in [p["player"] for p in top]
    assert [x["prob"] for x in top[0]["props"]] == [0.61, 0.45, 0.44]
