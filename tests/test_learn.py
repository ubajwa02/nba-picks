"""The learning loop (nbapicks/learn.py): the graded table, the corrections and their walk-forward
scores, the gate, what is applied, the rule scoreboard, posted picks against later prices, and the
wiring into settle."""
import datetime as dt, json, os, types
import numpy as np
import pytest
from nbapicks import learn as L, pipeline
from nbapicks.store import Store
from tests.test_e2e import env, NOW  # noqa: F401  (fixture)
from tests.test_sideorder import put_state, _odds


# ---- helpers ------------------------------------------------------------------------------
def table(slates=30, per=300, shift=0.0, model_weight=0.0, seed=1):
    """Synthetic graded props: market chances around 50%, a prop model that disagrees a little, and
    results drawn from the market's log-odds + shift + model_weight x (model - market)."""
    rng = np.random.default_rng(seed)
    rows = []
    for s in range(slates):
        day = (dt.date(2026, 11, 1) + dt.timedelta(days=s)).isoformat()
        for i in range(per):
            p = float(np.clip(rng.normal(0.5, 0.08), 0.2, 0.8))
            z = np.log(p / (1 - p))
            zm = z + rng.normal(0, 0.4)
            truth = 1 / (1 + np.exp(-(z + shift + model_weight * (zm - z))))
            rows.append(dict(slate=day, game_id=f"g{s}", player_id=str(i), stat=L.STATS[i % 4], line=9.5, p_mkt=p,
                             price_over=0.95 / p, price_under=0.95 / (1 - p), over=int(rng.random() < truth),
                             p_model=float(1 / (1 + np.exp(-zm))), model_version="sim", lead_h=2.0))
    return rows


def loop(rows, gate=L.GATE, incumbent=None):
    wf = L.walk_forward(L.Table(rows))
    stats = {n: L.summarise(d["per"]) for n, d in wf.items()}
    return wf, stats, L.judge(stats, gate, incumbent)


def game(gid, start, status="final"):
    return dict(game_id=gid, season=2027, season_type="regular", start_utc=start, home="A", away="B", status=status,
                home_score=100 if status == "final" else None, away_score=90 if status == "final" else None,
                observed_at="2026-11-01T00:00:00Z", source="espn")


def box(s, gid, pid, **stats):
    s.put("player_games", dict(dict(game_id=gid, player_id=pid, player_name=f"P{pid}", team="A", starter=1, minutes=30.0,
                                    pts=0, reb=0, ast=0, fg3m=0, played=1, observed_at="2026-11-06T04:00:00Z"), **stats))


def model_pred(s, pid, gid, player, stat, line, prob, created, selection="over", book="DraftKings", prob_push=0.0, version="props-v0"):
    s.put("predictions", dict(pred_id=pid, created_at=created, origin="model", provider="nbapicks", model_version=version,
                              category="straight", game_id=gid, market="prop", selection=selection, line=line, player_id=player,
                              player_name=f"P{player}", stat=stat, price_dec=1.9, book=book, price_observed_at=created,
                              price_source="espn", prob=prob, prob_push=prob_push, ev=0.0, edge_threshold=0.05,
                              decision="watch", reason="test", inputs=dict(status="research"), run_id="run-t"))


def pair(s, gid, pid, stat, line, over, under, at):
    _odds(s, gid, pid, stat, line, "side0", over, at)
    _odds(s, gid, pid, stat, line, "side1", under, at)


def season(root, slates=30, per=130, shift=0.0, seed=4, first=dt.date(2026, 10, 20)):
    """A ledger on disk: one final game a slate, `per` players with a DraftKings points pair before
    tip, a box score drawn from the fair chance (+ shift on the log-odds) and a model estimate."""
    s, rng = Store(root), np.random.default_rng(seed)
    for d in range(slates):
        add_slate(s, rng, first + dt.timedelta(days=d), per, shift)
    return s, rng


def add_slate(s, rng, day, per, shift=0.0, tag=""):
    gid, tip = f"g{day}{tag}", f"{day + dt.timedelta(days=1)}T00:00Z"      # 7 PM Toronto on `day`
    s.put("games", game(gid, tip))
    for i in range(per):
        p = float(np.clip(rng.normal(0.5, 0.08), 0.2, 0.8))
        pair(s, gid, f"p{i}", "pts", 19.5, round(0.95 / p, 3), round(0.95 / (1 - p), 3), f"{day}T20:00:00Z")
        over = rng.random() < 1 / (1 + np.exp(-(np.log(p / (1 - p)) + shift)))
        box(s, gid, f"p{i}", pts=25 if over else 15)
        model_pred(s, f"m{day}{tag}{i}", gid, f"p{i}", "pts", 19.5, float(np.clip(p + rng.normal(0, 0.08), 0.05, 0.95)), f"{day}T20:30:00Z")


def ctx_for(root, s, today, at=None):
    return types.SimpleNamespace(root=root, store=s, tz="America/Toronto", today=today, notes=[],
                                 now=at or dt.datetime(today.year, today.month, today.day, 12, tzinfo=dt.timezone.utc))


# ---- fitting and scoring -------------------------------------------------------------------
def test_fit_recovers_a_shift_and_barely_moves_on_little_data():
    rng = np.random.default_rng(0)
    n = 40000
    z = rng.normal(0, 0.3, n)
    y = (rng.random(n) < L._sig(z - 0.3)).astype(float)
    assert L._fit(np.ones((n, 1)), y, z, [L.L_SHIFT], [0.0])[0] == pytest.approx(-0.3, abs=0.03)
    assert abs(L._fit(np.ones((40, 1)), y[:40], z[:40], [L.L_SHIFT], [0.0])[0]) < 0.05     # 40 results against a prior worth 500
    assert L._fit(np.zeros((0, 2)), np.zeros(0), np.zeros(0), [1.0, 1.0], [0.0, 1.0]).tolist() == [0.0, 1.0]   # no data: the prior


def test_recent_shift_weights_recent_slates_more_so_a_bias_that_ended_fades():
    rows = table(slates=20, per=200, shift=-0.5, seed=2) + [
        dict(r, slate=(dt.date(2026, 11, 21) + dt.timedelta(days=int(r["game_id"][1:]))).isoformat()) for r in table(slates=40, per=200, seed=3)]
    t = L.Table(rows)                                                    # 20 slates with Overs far too high, then 40 where the price is right
    every = np.arange(len(t.y))
    flat = L.fit("shift", t, every)[0]
    assert flat == pytest.approx(-0.5 / 3, abs=0.04)                     # all slates equal: the old bias is still a third of its size
    assert abs(L.fit("recent_shift", t, every)[0]) < abs(flat) / 3       # recent slates first (10 slates to half): it has gone
    during = every[t.s < 20]
    assert -0.5 < L.fit("recent_shift", t, during, now=20)[0] < -0.33    # while it lasted it was seen, less the pull toward the market
    # the weights by hand: a slate counts half as much once RECENT_HALF_LIFE newer slates have been played
    two = L.Table([dict(rows[0], slate="2026-10-01", over=1)] * 50 + [dict(rows[0], slate="2026-10-02", over=0)] * 50 + [dict(rows[0], slate="2026-10-03")])
    b = L.fit("recent_shift", two, np.arange(100), now=2)[0]
    p, w = L._sig(two.z[0] + b), lambda age: 0.5 ** (age / L.RECENT_HALF_LIFE)          # noqa: E731
    assert w(2) * 50 * (1 - p) - w(1) * 50 * p - L.L_SHIFT * b == pytest.approx(0, abs=1e-6)        # the fit's first-order condition


def test_summarise_by_hand():
    s = L.summarise([(0, 2, 0.2, 1.0), (1, 2, -0.1, 1.0)])
    assert (s["slates"], s["n"], s["slates_better"]) == (2, 4, 1)
    assert s["gain"] == pytest.approx(0.025) and s["gain_se"] == pytest.approx(0.075) and s["gain_t"] == pytest.approx(1 / 3)
    assert s["z"] == pytest.approx(2 / 2 ** 0.5) and s["older"] == pytest.approx(0.1) and s["newer"] == pytest.approx(-0.05)
    assert L.summarise([]) == dict(slates=0, n=0, gain=None, gain_se=None, gain_t=None, z=None, older=None, newer=None, slates_better=0)
    one = L.summarise([(3, 10, 0.5, -2.0)])
    assert one["gain_se"] is None and one["z"] == pytest.approx(-1.0) and one["older"] is None and one["newer"] == pytest.approx(0.05)


def test_nothing_is_put_in_force_when_the_market_is_right():
    for seed in (1, 2, 3):
        wf, stats, (active, verdicts) = loop(table(seed=seed))
        assert active is None and all(v.startswith("not in force: ") for v in verdicts.values())
        assert all(abs(s["z"]) < 3 for s in stats.values())
        assert abs(wf["shift"]["params"][0]) < 0.05 and wf["shift_slope"]["params"][1] == pytest.approx(1.0, abs=0.25)


def test_a_real_bias_is_found_scored_out_of_sample_and_put_in_force():
    wf, stats, (active, verdicts) = loop(table(slates=40, shift=-0.25))
    assert active == "recent_shift" and verdicts[active] == "in force" and verdicts["shift"] == "passes, but recent_shift is in force"
    assert stats[active]["z"] > 3 and stats[active]["gain"] > 0 and stats[active]["newer"] > 0
    assert wf["shift"]["params"][0] == pytest.approx(-0.25, abs=0.06)
    assert [p[0] for p in wf["shift"]["per"]] == list(range(L.MIN_TRAIN_SLATES, 40))     # every later slate scored once
    assert all(p[1] == 300 for p in wf["shift"]["per"])
    fixed = L.adjust(dict(learner="shift", params=wf["shift"]["params"]), 0.5)
    assert fixed == pytest.approx(L._sig(-0.25), abs=0.02)                               # 50% becomes about 44%


def test_a_model_that_knows_something_is_weighed_in():
    wf, stats, (active, verdicts) = loop(table(slates=40, model_weight=0.5))
    assert active == "model:sim" and wf["model:sim"]["params"][1] == pytest.approx(0.5, abs=0.12)
    assert verdicts["shift"].startswith("not in force: ")
    nothing = loop(table(slates=40, model_weight=0.0, seed=9))
    assert nothing[2][0] is None and abs(nothing[0]["model:sim"]["params"][1]) < 0.1    # a model that adds nothing gets no weight


def test_walk_forward_never_uses_the_slate_it_scores():
    rows = table(slates=12, per=150, shift=-0.2, seed=5)
    last = max(r["slate"] for r in rows)
    wf = L.walk_forward(L.Table(rows))
    flipped = L.walk_forward(L.Table([dict(r, over=1 - r["over"]) if r["slate"] == last else r for r in rows]))
    for name in wf:
        assert wf[name]["per"][:-1] == flipped[name]["per"][:-1]          # earlier slates: untouched
        a, b = wf[name]["per"][-1], flipped[name]["per"][-1]
        assert a[:2] == b[:2] and a[2:] != b[2:]                         # the last slate: scored on its own results only
    few = L.walk_forward(L.Table(table(slates=L.MIN_TRAIN_SLATES, per=50)))
    assert all(d["per"] == [] for d in few.values())                     # nothing to score yet


def test_model_corrections_keep_to_their_own_model_version():
    rows = table(slates=14, per=100)
    for r in rows:
        r["model_version"] = "props-v1" if r["slate"] < "2026-11-08" else "props-v0"
        if r["player_id"] == "0":
            r["p_model"] = r["model_version"] = None                     # a prop the model did not price
    t = L.Table(rows)
    assert L.names(t) == ["shift", "shift_slope", "stat_shift", "recent_shift", "model:props-v0", "model:props-v1"]
    wf = L.walk_forward(t)
    assert wf["model:props-v1"]["trained_on"] == 7 * 99 and wf["model:props-v0"]["trained_on"] == 7 * 99
    assert [p[0] for p in wf["model:props-v0"]["per"]] == [12, 13] and [p[0] for p in wf["model:props-v1"]["per"]] == [5, 6]
    assert wf["shift"]["trained_on"] == 1400


# ---- the gate ------------------------------------------------------------------------------
def test_gate_conditions_and_incumbency():
    good = dict(slates=20, n=6000, gain=0.001, gain_se=0.0003, gain_t=3.3, z=3.4, older=0.001, newer=0.001, slates_better=14)
    s = lambda **kw: dict(good, **kw)                                    # noqa: E731
    g = L.GATE
    assert L.judge(dict(a=good), g, None) == ("a", {"a": "in force"})
    for bad, word in ((s(z=2.9), "evidence +2.90 is under 3.00"), (s(z=None), "evidence"), (s(slates=14), "needs 15 unseen slates"),
                      (s(n=2999), "3,000 props"), (s(gain=-0.0001), "did not lower log loss"), (s(newer=-0.0001), "newer half")):
        active, v = L.judge(dict(a=bad), g, None)
        assert active is None and v["a"].startswith("not in force: ") and word in v["a"]
    assert L.judge(dict(a=s(z=2.1)), g, "a")[0] == "a"                   # in force: kept down to keep_z
    assert L.judge(dict(a=s(z=1.9)), g, "a")[0] is None                  # ... and dropped under it
    assert L.judge(dict(a=s(z=2.5, newer=-0.001)), g, "a")[0] is None    # or when it stops helping
    assert L.judge(dict(a=s(z=2.5)), g, None)[0] is None                 # 2.5 is not enough to start
    active, v = L.judge(dict(a=s(z=2.5), b=s(z=5.0)), g, "a")
    assert active == "a" and v == {"a": "in force", "b": "passes, but a is in force"}     # no flapping between two that pass
    assert L.judge(dict(a=s(z=3.5), b=s(z=5.0)), g, None)[0] == "b"      # no incumbent: the most evidence
    assert L.judge(dict(a=s(z=1.0), b=s(z=5.0)), g, "a")[0] == "b"       # a failing incumbent hands over
    assert L.judge(dict(b=s(z=5.0)), g, "gone")[0] == "b"                # an incumbent that is no longer fitted
    # of those that pass, recent_shift is used (it lets go soonest when a bias ends) unless another explains clearly more
    two = lambda other, recent: dict(shift=s(**other), recent_shift=s(**recent))        # noqa: E731
    active, v = L.judge(two(dict(z=5.0), dict(z=3.2)), g, "shift")
    assert active == "recent_shift" and v == {"shift": "passes, but recent_shift is in force", "recent_shift": "in force"}
    assert L.judge(two(dict(z=5.0), dict(z=2.5)), g, "shift")[0] == "shift"              # it has to pass the bar to start first
    assert L.judge(two(dict(z=5.0), dict(z=2.5)), g, "recent_shift")[0] == "recent_shift"            # and is then kept like any other
    assert L.judge(two(dict(z=5.0), dict(z=1.9)), g, "recent_shift")[0] == "shift"
    assert L.judge(two(dict(z=5.0, gain=0.00149), dict(z=3.2)), g, "shift")[0] == "recent_shift"     # 1.49 times the saving: not clearly more
    rich = {"recent_shift": s(z=3.2), "model:v": s(z=4.0, gain=0.0015), "stat_shift": s(z=4.0, gain=0.002), "shift": s(z=9.0, gain=0.0014)}
    active, v = L.judge(rich, g, None)
    assert active == "stat_shift" and v["recent_shift"] == "passes, but stat_shift is in force"      # the one that explains most
    assert L.judge(dict(rich, stat_shift=s(z=2.5, gain=0.002)), g, None)[0] == "model:v"             # a richer one must pass the gate too
    many = {f"c{i}": s(z=-1.0) for i in range(120)}
    many["a"] = s(z=3.05)
    assert L.judge(many, g, None)[0] is None                             # 121 candidates raise the bar to sqrt(2 ln 121) = 3.10
    assert L.judge({}, g, "a") == (None, {})


def test_adjust_applies_exactly_the_correction_in_force():
    sh = dict(learner="shift", params=[-0.1])
    assert L.adjust(None, 0.55) == 0.55 and L.adjust({}, 0.55) == 0.55
    assert L.adjust(sh, 0.5) == pytest.approx(1 / (1 + np.exp(0.1)))
    assert L.adjust(dict(learner="recent_shift", params=[0.2]), 0.5) == pytest.approx(L._sig(0.2))
    assert L.adjust(dict(learner="shift_slope", params=[0.0, 1.2]), 0.6) == pytest.approx(L._sig(1.2 * np.log(1.5)))
    st = dict(learner="stat_shift", params=[-0.1, 0.05, 0.0, 0.0, -0.05])
    assert L.adjust(st, 0.5, stat="pts") == pytest.approx(L._sig(-0.05)) and L.adjust(st, 0.5, stat="fg3m") == pytest.approx(L._sig(-0.15))
    assert L.adjust(st, 0.5, stat="stl") == pytest.approx(L._sig(-0.1))                 # an unknown stat gets the common part
    mo = dict(learner="model:props-v1", params=[0.0, 0.5])
    assert L.adjust(mo, 0.5, model_prob=0.6, model_version="props-v1") == pytest.approx(L._sig(0.5 * np.log(1.5)))
    assert L.adjust(mo, 0.5, model_prob=0.6, model_version="props-v0") == 0.5           # another model's estimate: not applied
    assert L.adjust(mo, 0.5) == 0.5 and L.adjust(sh, None) is None and L.adjust(sh, 1.0) == 1.0
    assert L.adjust(dict(learner="something_new", params=[1.0]), 0.5) == 0.5


def test_a_stale_correction_is_not_applied():
    st = dict(through="2026-11-16", active=dict(learner="shift", params=[-0.1], since="2026-11-10"))
    assert L.active(st, dt.date(2026, 11, 17)) == st["active"] and L.active(st) == st["active"]
    assert L.active(st, dt.date(2026, 12, 16)) == st["active"] and L.active(st, dt.date(2026, 12, 17)) is None
    assert L.active(st, dt.date(2027, 10, 20)) is None                                   # a summer later
    assert L.active(dict(active=st["active"]), dt.date(2026, 11, 17)) is None            # no date: cannot be shown to be fresh
    assert L.active({}, dt.date(2026, 11, 17)) is None and L.active(None) is None
    assert L.active(dict(through="2026-11-16", active=None), dt.date(2026, 11, 17)) is None


def test_the_loop_never_reads_the_holdout_window(tmp_path):
    assert L.first_slate(dt.date(2026, 11, 17)) == "2026-07-01"          # 240 days back is 2026-03-22, inside the holdout
    assert L.first_slate(dt.date(2027, 4, 1)) == "2026-08-04"            # later on, plain 240 days
    assert L.first_slate(dt.date(2026, 11, 17), str(tmp_path / "missing.yaml")) == "2026-07-01"     # built in when the file is gone
    p = tmp_path / "gates.yaml"
    p.write_text("props:\n  splits:\n    holdout: {start: 2027-02-01, end: 2027-06-30}\nlearning:\n  activate_z: 4.0\n")
    assert L.first_slate(dt.date(2027, 11, 1), str(p)) == "2027-07-01"
    assert L.gates(str(p))["activate_z"] == 4.0 and L.gates(str(p))["keep_z"] == 2.0
    assert L.gates() == L.GATE and L.gates(str(tmp_path / "missing.yaml")) == L.GATE     # config/gates.yaml carries the same numbers


# ---- the graded table ----------------------------------------------------------------------
def test_graded_joins_the_last_model_estimate_made_before_tip_at_that_line():
    s = Store(None)
    s.put("games", game("g1", "2026-11-05T00:00Z"))
    pair(s, "g1", "p1", "pts", 20.5, 1.80, 2.05, "2026-11-04T20:00:00Z")
    pair(s, "g1", "p2", "reb", 7.5, 1.80, 2.05, "2026-11-04T20:00:00Z")
    pair(s, "g1", "p3", "ast", 6.0, 1.95, 1.87, "2026-11-04T21:00:00Z")
    pair(s, "g1", "p4", "ast", 6.0, 1.95, 1.87, "2026-11-04T21:00:00Z")          # lands on the line: no result
    box(s, "g1", "p1", pts=24); box(s, "g1", "p2", reb=5); box(s, "g1", "p3", ast=8); box(s, "g1", "p4", ast=6)
    model_pred(s, "a", "g1", "p1", "pts", 20.5, 0.50, "2026-11-04T15:00:00Z", version="props-v0")
    model_pred(s, "b", "g1", "p1", "pts", 20.5, 0.60, "2026-11-04T21:00:00Z", version="props-v1")   # the last one before tip
    model_pred(s, "c", "g1", "p1", "pts", 20.5, 0.90, "2026-11-05T00:30:00Z")                       # after tip
    model_pred(s, "d", "g1", "p1", "pts", 19.5, 0.70, "2026-11-04T22:00:00Z")                       # another line
    model_pred(s, "e", "g1", "p1", "pts", 20.5, 0.20, "2026-11-04T22:00:00Z", selection="under")    # the other side
    model_pred(s, "f", "g1", "p1", "pts", 20.5, 0.80, "2026-11-04T22:00:00Z", book="bet365")        # another book
    model_pred(s, "g", "g1", "p3", "ast", 6.0, 0.45, "2026-11-04T22:00:00Z", prob_push=0.10)        # a whole-number line
    rows = {r["player_id"]: r for r in L.graded(s, "America/Toronto", "2026-11-01")}
    assert set(rows) == {"p1", "p2", "p3"}
    p1 = rows["p1"]
    assert (p1["over"], p1["p_model"], p1["model_version"], p1["line"]) == (1, 0.60, "props-v1", 20.5)
    assert p1["p_mkt"] == pytest.approx((1 / 1.80) / (1 / 1.80 + 1 / 2.05)) and (p1["price_over"], p1["price_under"]) == (1.80, 2.05)
    assert p1["slate"] == "2026-11-04" and p1["lead_h"] == pytest.approx(4.0)
    assert rows["p2"]["over"] == 0 and rows["p2"]["p_model"] is None and rows["p2"]["model_version"] is None
    assert rows["p3"]["p_model"] == pytest.approx(0.5) and rows["p3"]["lead_h"] == pytest.approx(3.0)   # P(over) given no push
    assert L.graded(s, "America/Toronto", "2026-11-05") == []
    t = L.Table(list(rows.values()))
    assert t.has_model.tolist() == [True, False, True] and t.slates == ["2026-11-04"]


# ---- the market and the rules --------------------------------------------------------------
def by_hand():
    row = lambda slate, stat, p, o, u, over, pm: dict(slate=slate, stat=stat, p_mkt=p, price_over=o, price_under=u,     # noqa: E731
                                                      over=over, p_model=pm, model_version=pm and "v", lead_h=1.0)
    return L.Table([row("d1", "pts", 0.60, 1.60, 2.40, 1, 0.68), row("d1", "reb", 0.40, 2.40, 1.60, 1, 0.32),
                    row("d2", "ast", 0.50, 1.90, 1.90, 0, None), row("d2", "fg3m", 0.50, 1.90, 1.90, 0, 0.80)])


def test_rules_are_graded_at_the_price_by_hand():
    r = L.rules(by_hand(), L.GATE)
    assert (r["every Over"]["bets"], r["every Over"]["hit"], r["every Over"]["roi"]) == (4, 0.5, 0.0)
    under = r["every Under"]
    assert (under["roi"], under["se"], under["t"], under["avg_price"]) == (-0.05, 0.95, -0.05, 1.95)
    assert r["every pts Under"]["roi"] == -1.0 and r["every pts Under"]["bets"] == 1 and r["every pts Under"]["se"] is None
    assert r["the favourite (fair chance 55% or more)"]["roi"] == -0.2 and r["the underdog (fair chance 45% or less)"]["roi"] == 0.2
    assert r["model edge of 5% or more at the price"]["bets"] == 3 and r["model edge of 5% or more at the price"]["roi"] == pytest.approx(-0.4667)
    main = r["model 60% or more at -200 or longer (the pick rule on main)"]
    assert (main["bets"], main["roi"]) == (3, pytest.approx(-0.4667))    # the prop with no model estimate is never taken
    assert r["the same, within 10 points of the market"]["bets"] == 2 and r["the same, within 10 points of the market"]["roi"] == -0.2
    assert not any(x["flag"] for x in r.values()) and under["bets_last10"] == 4
    assert len(r) == 11


def test_a_rule_is_flagged_only_with_enough_bets_and_a_clear_result():
    rows = table(slates=30, per=200, shift=-0.6)                          # Unders win far more often than their price says
    r = L.rules(L.Table(rows), L.GATE)
    assert r["every Under"]["flag"] and r["every Under"]["roi"] > 0.1 and r["every Under"]["t"] > 3
    assert not r["every Over"]["flag"] and r["every Over"]["roi"] < -0.1
    assert not L.rules(L.Table(table(slates=30, per=200)), L.GATE)["every Under"]["flag"]
    few = L.rules(L.Table(rows[:260]), L.GATE)                            # under 300 bets: never flagged
    assert few["every Under"]["bets"] == 260 and not few["every Under"]["flag"]


def test_market_fit_reads_the_market_and_survives_flat_prices():
    m = L.market_fit(L.Table(table(slates=30, shift=-0.2)))
    assert m["pairs"] == 9000 and m["slates"] == 30 and m["median_hours_before_tip"] == 2.0
    assert m["shift"] == pytest.approx(-0.2, abs=0.07) and m["slope"] == pytest.approx(1.0, abs=0.3)
    assert m["over_minus_fair"] == pytest.approx(-0.05, abs=0.015) and 0 < m["over_minus_fair_se"] < 0.01
    flat = [dict(r, p_mkt=0.5) for r in table(slates=6, per=40)]
    f = L.market_fit(L.Table(flat))
    assert np.isfinite([f["shift"], f["slope"], f["shift_se"], f["slope_se"], f["logloss"]]).all()


# ---- posted picks against later prices -----------------------------------------------------
def test_posted_picks_are_compared_with_later_prices_of_the_same_bet():
    s = Store(None)
    s.put("games", game("g1", "2026-11-05T00:00Z", status="scheduled"))
    s.put("publications", dict(pub_id="picks:2026-11-04:dry", kind="picks", slate_date="2026-11-04", at="2026-11-04T16:00:00Z",
                               status="dry_run", message_sha="x", detail="picks"))
    early, late = "2026-11-04T15:00:00Z", "2026-11-04T20:00:00Z"
    pair(s, "g1", "p1", "reb", 2.5, 1.60, 2.40, early); pair(s, "g1", "p1", "reb", 2.5, 1.50, 2.60, late)     # shortened: toward the pick
    pair(s, "g1", "p2", "ast", 4.5, 1.667, 2.20, early); pair(s, "g1", "p2", "ast", 4.5, 1.60, 2.30, late)    # drifted: away from it
    pair(s, "g1", "p3", "pts", 9.5, 1.80, 2.00, early); pair(s, "g1", "p3", "pts", 9.5, 1.40, 3.00, "2026-11-05T00:30:00Z")   # after tip
    pair(s, "g1", "p4", "reb", 2.5, 1.58, 2.42, early); pair(s, "g1", "p4", "reb", 3.5, 2.42, 1.58, late)     # the main line moved
    pair(s, "g1", "p5", "pts", 9.5, 1.90, 1.90, early)
    pair(s, "g1", "p6", "fg3m", 1.5, 1.60, 2.40, early); _odds(s, "g1", "p6", "fg3m", 1.5, "side1", 2.45, late)   # only the other side moved
    pair(s, "g1", "p7", "pts", 19.5, 1.80, 2.00, early); pair(s, "g1", "p7", "pts", 19.5, 1.70, 2.15, late)
    lean = lambda pid, stat, line, sel, price, src="props_v1", **kw: dict(slate="2026-11-04", game_id="g1", market="prop",   # noqa: E731
                                                                         selection=sel, line=line, player_id=pid, stat=stat,
                                                                         price_american=price, source=src, **kw)
    leans = [lean("p1", "reb", 2.5, "over", -167),
             lean("p2", "ast", 4.5, "under", -150),          # recorded at the worse price of the pair; its own side was +120
             lean("p3", "pts", 9.5, "over", -125), lean("p4", "reb", 2.5, "over", -172),
             lean("p5", "pts", 9.5, "over", -200),           # no stored quote shows this price
             lean("p6", "fg3m", 1.5, "over", -167),
             lean("p9", "pts", 20.0, "over", 150, src="split_card"),
             dict(slate="2026-11-04", game_id="g1", market="ml", selection="home", line=None, price_american=-120, source="model"),
             dict(lean("p1", "reb", 2.5, "over", -167), slate="2026-06-01")]      # before the first slate the loop may read
    out = L.picks_clv(s, leans, "2026-07-01")
    a = out["all"]
    assert (a["picks"], a["priced"], a["repriced"], a["later"], a["line_changed"]) == (7, 5, 1, 3, 1)
    assert (a["toward"], a["same"], a["away"]) == (1, 1, 1)
    p1, p2 = (1 + 100 / 167) / 1.5 - 1, 2.20 / 2.30 - 1
    assert a["move"] == pytest.approx((p1 + p2 + 0) / 3, abs=1e-4) and a["move_se"] is None       # one slate: no error bar
    assert out["props_v1"]["picks"] == 6 and out["split_card"] == dict(out["split_card"], picks=1, priced=0, later=0, move=None)
    fair = (1 / 1.5) / (1 / 1.5 + 1 / 2.6)
    only = L.picks_clv(s, leans[:1], "2026-07-01")["all"]
    assert only["value"] == pytest.approx((1 + 100 / 167) * fair - 1, abs=1e-4)                    # worth more than the margin
    assert only["margin"] == pytest.approx(1 / (1 / 1.5 + 1 / 2.6) - 1, abs=1e-4) and only["value"] > only["margin"]
    # a pick taken at another book carries DraftKings' price for its side: the move is DraftKings', the value is at the price taken
    fd = L.picks_clv(s, [lean("p7", "pts", 19.5, "over", 100, src="fanduel_edge", ref_price_american=-125, book="FanDuel")], "2026-07-01")
    assert (fd["fanduel_edge"]["priced"], fd["fanduel_edge"]["toward"], fd["fanduel_edge"]["repriced"]) == (1, 1, 0)
    assert fd["all"]["move"] == pytest.approx(1.80 / (1 + 100 / 143) - 1, abs=1e-4)
    assert fd["all"]["value"] == pytest.approx(2.0 * (1 / 1.7) / (1 / 1.7 + 1 / 2.15) - 1, abs=1e-4)
    wrong = L.picks_clv(s, [lean("p7", "pts", 19.5, "over", 100, ref_price_american=100)], "2026-07-01")["all"]
    assert wrong["priced"] == 0                              # DraftKings never showed +100 on that side
    none = L.picks_clv(s, [], "2026-07-01")
    assert list(none) == ["all"] and none["all"]["picks"] == 0 and none["all"]["move"] is None and none["all"]["margin"] is None
    assert [h[1:] for h in L.pair_history(s, "g1", "p4", "reb")] == [(2.5, 1.58, 2.42), (3.5, 2.42, 1.58)]
    assert len(L.pair_history(s, "g1", "p3", "pts")) == 1 and L.pair_history(s, "nope", "p1", "reb") == []


def test_a_pick_is_matched_to_the_quote_in_force_when_the_slate_went_out():
    s = Store(None)
    s.put("games", game("g1", "2026-11-05T00:00Z", status="scheduled"))
    for at, over, under in (("2026-11-04T10:00:00Z", 1.60, 2.40), ("2026-11-04T14:00:00Z", 1.70, 2.20),
                            ("2026-11-04T18:00:00Z", 1.60, 2.40), ("2026-11-04T22:00:00Z", 1.55, 2.50)):
        pair(s, "g1", "p1", "reb", 2.5, over, under, at)
    lean = dict(slate="2026-11-04", game_id="g1", market="prop", selection="over", line=2.5, player_id="p1", stat="reb",
                price_american=-167, source="props_v1")
    first = L.picks_clv(s, [lean], "2026-07-01")["all"]      # no posting time known: the first quote showing the price
    assert first["later"] == 1 and first["toward"] == 1
    pub = lambda at: s.put("publications", dict(pub_id=f"picks:{at}", kind="picks", slate_date="2026-11-04", at=at,   # noqa: E731
                                                status="dry_run", message_sha=at, detail="picks"))
    pub("2026-11-04T19:00:00Z")                              # posted at 19:00: priced on the 18:00 quote
    assert L.picks_clv(s, [lean], "2026-07-01")["all"]["move"] == pytest.approx((1 + 100 / 167) / (1 + 100 / 182) - 1, abs=1e-4)
    assert L.picks_clv(s, [dict(lean, posted_at="2026-11-04T23:00:00Z")], "2026-07-01")["all"]["move"] is not None    # the pick's own time wins
    late = L.picks_clv(s, [dict(lean, posted_at="2026-11-04T09:00:00Z")], "2026-07-01")["all"]
    assert late["priced"] == 1 and late["later"] == 1       # nothing stored by then: the first quote showing the price


# ---- the loop end to end -------------------------------------------------------------------
def test_run_scores_stores_and_reports_then_waits_for_something_new(tmp_path):
    root = str(tmp_path / "data")
    s, rng = season(root, slates=12, per=40)
    last = dt.date(2026, 10, 31)
    put_state(root, "confirmed", through=last.isoformat())
    ctx = ctx_for(root, s, last + dt.timedelta(days=1))
    r = L.run(ctx)
    assert r == dict(status="updated", through="2026-10-31", pairs=480, active=None)
    st = L.load(root)
    assert st["through"] == "2026-10-31" and st["active"] is None and st["changes"] == [] and st["version"] == L.VERSION
    assert set(st["learners"]) == {"shift", "shift_slope", "stat_shift", "recent_shift", "model:props-v0"}
    assert all(d["slates"] == 7 and d["n"] == 280 and d["verdict"].startswith("not in force: needs 15 unseen slates") for d in st["learners"].values())
    assert st["market"]["pairs"] == 480 and st["market"]["median_hours_before_tip"] == 4.0 and st["picks"]["all"]["picks"] == 0
    rep = (tmp_path / "reports" / L.REPORT).read_text()
    assert "No correction is in force" in rep and "480 graded DraftKings props on 12 slates" in rep and "nan" not in rep
    assert rep == L.report_md(st)
    log = tmp_path / "data" / "research" / L.LOG
    assert [json.loads(x)["through"] for x in log.read_text().splitlines()] == ["2026-10-31"]
    files = [tmp_path / "data" / "research" / L.STATE, tmp_path / "reports" / L.REPORT, log]
    before = [f.stat().st_mtime_ns for f in files]
    assert L.run(ctx) == dict(status="unchanged", through="2026-10-31", active=None)      # nothing new: nothing rewritten
    assert before == [f.stat().st_mtime_ns for f in files]
    add_slate(s, rng, dt.date(2026, 11, 1), 40)                                           # a new slate is graded
    put_state(root, "confirmed", through="2026-11-01")
    assert L.run(ctx_for(root, s, dt.date(2026, 11, 2)))["through"] == "2026-11-01"
    assert [json.loads(x)["through"] for x in log.read_text().splitlines()] == ["2026-10-31", "2026-11-01"]
    assert L.run(ctx_for(root, s, dt.date(2026, 11, 2)), force=True)["status"] == "updated"
    assert len(log.read_text().splitlines()) == 2                                         # a forced refit of the same slate adds no line
    add_slate(s, rng, dt.date(2026, 11, 1), 25, tag="late")                              # a late game of that slate goes final
    assert L.run(ctx_for(root, s, dt.date(2026, 11, 2)))["pairs"] == 545
    assert [(json.loads(x)["through"], json.loads(x)["pairs"]) for x in log.read_text().splitlines()] == [("2026-10-31", 480), ("2026-11-01", 545)]


def test_run_puts_a_correction_in_force_and_drops_it_when_it_stops_passing(tmp_path, monkeypatch):
    root = str(tmp_path / "data")
    s, rng = season(root, slates=30, per=130, shift=-0.6)                # Overs priced far too high all season
    put_state(root, "confirmed", through="2026-11-18")
    ctx = ctx_for(root, s, dt.date(2026, 11, 19))
    r = L.run(ctx)
    assert r["status"] == "updated" and r["active"] == "recent_shift"
    st = L.load(root)
    a = L.active(st, ctx.today)
    assert a["learner"] == r["active"] and a["since"] == "2026-11-18" and a["params"][0] < -0.3
    assert L.adjust(a, 0.5, stat="pts") < 0.45                           # an even-money Over is now priced under 45%
    assert len(st["changes"]) == 1 and "put in force" in st["changes"][0]["what"] and any("put in force" in n for n in ctx.notes)
    rep = (tmp_path / "reports" / L.REPORT).read_text()
    assert f"A correction is in force: `{r['active']}`, since 2026-11-18" in rep and "## Changes" in rep
    assert "every Under **(clears the bar)**" in rep
    add_slate(s, rng, dt.date(2026, 11, 19), 130, shift=-0.6)            # the next slate: still in force, same start date
    put_state(root, "confirmed", through="2026-11-19")
    assert L.run(ctx_for(root, s, dt.date(2026, 11, 20)))["active"] == r["active"]
    assert L.load(root)["active"]["since"] == "2026-11-18" and len(L.load(root)["changes"]) == 1
    monkeypatch.setattr(L, "gates", lambda path="config/gates.yaml": dict(L.GATE, keep_z=99.0, activate_z=99.0))
    later = ctx_for(root, s, dt.date(2026, 11, 20))
    assert L.run(later)["active"] is None                                # the gate changed, so the state is refreshed
    st = L.load(root)
    assert st["active"] is None and len(st["changes"]) == 2 and "dropped" in st["changes"][1]["what"]
    assert any("dropped" in n for n in later.notes) and L.adjust(L.active(st, later.today), 0.5) == 0.5


def test_run_waits_for_confirmed_sides_and_enough_slates(tmp_path):
    root = str(tmp_path / "data")
    s, rng = season(root, slates=L.MIN_TRAIN_SLATES, per=20)
    ctx = ctx_for(root, s, dt.date(2026, 10, 25))
    assert L.run(ctx)["status"] == "skipped: prop sides are not measured yet, so results cannot be matched to a side"
    put_state(root, "failed", through="2026-10-24")
    assert "prop sides are failed" in L.run(ctx)["status"]
    put_state(root, "confirmed", through="2026-09-01")                   # confirmed long ago: not relied on
    assert "prop sides are unconfirmed" in L.run(ctx)["status"]
    put_state(root, "confirmed", through="2026-10-24")
    assert L.run(ctx)["status"] == "skipped: 5 graded slates, the loop starts after 5"
    assert L.load(root) == {} and not (tmp_path / "reports").exists()


def test_settle_runs_the_loop_and_a_broken_loop_never_blocks_it(env, monkeypatch):
    root, cfg, state = env
    ctx = pipeline.Ctx(NOW, cfg, root)
    pipeline.ingest(ctx)
    out = pipeline.settle(ctx)
    assert out["learning"].startswith("skipped: prop sides are ")         # nothing graded in this fixture yet
    monkeypatch.setattr(L, "run", lambda c: (_ for _ in ()).throw(RuntimeError("boom")))
    out = pipeline.settle(ctx)
    assert "learning" not in out and any("learning loop failed: boom" in n for n in ctx.notes)


def test_gate_simulation_tool_replays_the_loop_slate_by_slate(tmp_path):
    from tools import learn_gate_sim as sim
    rows = table(slates=6, per=60)
    real = [[r for r in rows if r["slate"] == d] for d in sorted({r["slate"] for r in rows})]
    gate = dict(L.GATE, min_slates=5, min_pairs=300)
    play = lambda n, until=None, **truth: sim.replay(sim.scored(sim.season(real, n, np.random.default_rng(3), until=until, **truth)), gate, until)  # noqa: E731
    quiet = play(26)
    assert quiet == dict(quiet, first=None, drops=0, slates_on=0, props=0, end=None) and quiet["all_props"] == 21 * 60
    loud = play(26, a=-0.8)
    assert loud["first"] is not None and loud["first"] >= L.MIN_TRAIN_SLATES + 5 and loud["end"] and loud["gain"] > 0
    ends = play(60, until=20, a=-0.8)
    assert ends["first"] is not None and ends["drops"] >= 1 and ends["end"] is None    # the bias ended: the correction goes
    assert 0 < ends["slates_on_after"] < 40 and ends["gain_after"] < 0 < ends["gain"]  # it cost something before it went, less than it had saved
    # the refits are cached per scenario and replayed from the cache
    cache = str(tmp_path / "walks")
    first = sim.seasons("under by 3 points", real, 2, 12, 5, cache)
    assert len(first) == 2 and set(first[0]) == set(L.CORRECTIONS) | {"model:sim"} and len(os.listdir(cache)) == 1
    assert sim.seasons("under by 3 points", real, 2, 12, 5, cache) == first and sim.seasons("under by 3 points", [], 2, 12, 5, cache) == first
    out = sim.summary("bias that ends", [ends, quiet], 60)
    assert out["seasons"] == 2 and out["seasons_with_a_correction"] == 1 and out["seasons_with_a_drop"] == 1 and out["in_force_at_season_end"] == 0
    assert out["slates_in_force_after_the_change_mean"] == ends["slates_on_after"] / 2 and out["log_loss_saved_per_prop_in_force_after_the_change"] < 0
    assert "slates_in_force_after_the_change_mean" not in sim.summary("market is right", [quiet], 26)
