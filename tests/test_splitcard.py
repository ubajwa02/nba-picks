"""Split-card tests on synthetic box scores only."""
import datetime as dt

from nbapicks import splitcard as SC


def _data(n=30, late_pts=None):
    """Player P1 (team AAA) scores 20 on even days, 30 on odd days; mate M1 sits on day%5==0.
    Opponents alternate BBB/CCC; AAA home on even days."""
    games, rows = {}, []
    start = dt.date(2022, 11, 1)
    for i in range(n):
        d = start + dt.timedelta(days=2 * i)
        gid = f"g{i}"
        opp = "BBB" if i % 2 else "CCC"
        home, away = ("AAA", opp) if i % 2 == 0 else (opp, "AAA")
        games[gid] = dict(start_utc=f"{d.isoformat()}T23:30Z", home=home, away=away)
        pts = 30 if i % 2 else 20
        if late_pts is not None and i == n - 1:
            pts = late_pts
        rows.append(dict(game_id=gid, player_id="P1", player_name="Pat", team="AAA", minutes=34, played=1,
                         pts=pts, reb=5, ast=5, fg3m=2))
        rows.append(dict(game_id=gid, player_id="M1", player_name="Mate", team="AAA",
                         minutes=0 if i % 5 == 0 else 30, played=0 if i % 5 == 0 else 1, pts=10, reb=3, ast=3, fg3m=1))
        rows.append(dict(game_id=gid, player_id="O1", player_name="Opp", team=opp, minutes=30, played=1,
                         pts=12 if opp == "BBB" else 25, reb=4, ast=2, fg3m=1))
    return SC.build_index(rows, games), games


def test_counts_exact_line_and_n():
    idx, _ = _data()
    date = dt.date(2023, 2, 1)
    c = SC.split_counts(idx, "P1", "pts", 25.5, "over", date, "BBB", False)
    assert c["career"] == (15, 30) and c["last10"] == (5, 10) and c["last5"][1] == 5
    assert c["vs BBB"] == (15, 15)        # every BBB game was a 30-point game
    assert c["away"] == (15, 15)
    assert "with Mate" in c or "without Mate" in c


def test_no_lookahead():
    """A game on or after the prop date must not change the card."""
    idx_a, _ = _data(n=30)
    idx_b, _ = _data(n=31, late_pts=99)   # extra game on the prop date itself
    date = dt.date(2022, 11, 1) + dt.timedelta(days=60)   # = day of game 30
    a = SC.card(idx_a, "P1", "pts", 25.5, "over", date, "CCC", True)
    b = SC.card(idx_b, "P1", "pts", 25.5, "over", date, "CCC", True)
    assert a == b


def test_small_n_shrinks_toward_baseline():
    counts = {"career": (50, 100), "season": (50, 100), "vs XXX": (3, 3)}
    p = SC.combine(counts, k=20)
    assert 0.5 < p < 0.6                  # 3/3 moves it, but nowhere near 1.0
    big = SC.combine({"career": (50, 100), "season": (50, 100), "vs XXX": (300, 300)}, k=20)
    assert big > p


def test_outcome_push_and_under():
    assert SC.outcome(20, 20, "over") is None
    assert SC.outcome(19, 19.5, "under") == 1 and SC.outcome(20, 19.5, "under") == 0


def test_defense_rank_point_in_time():
    idx, _ = _data()
    r = SC.defense_ranks(idx, dt.date(2023, 2, 1), "pts")
    assert [t for t in sorted(r, key=lambda t: r[t][1])] == ["AAA", "CCC", "BBB"]
    late = SC.defense_ranks(idx, dt.date(2022, 11, 5), "pts")
    assert late == {}                      # fewer than MIN_DEF_GAMES games: no rank yet


def test_card_ev_and_text():
    idx, _ = _data()
    c = SC.card(idx, "P1", "pts", 25.5, "over", dt.date(2023, 2, 1), "BBB", False, price_dec=1.91)
    assert abs(c["ev"] - (c["prob"] * 1.91 - 1)) < 1e-3
    assert "/" in SC.card_text(c) and c["implied"] == round(1 / 1.91, 4)


def test_pipeline_cards_watchlist_only(tmp_path):
    """prop_split_cards builds a card from history files; unverified sides get no price."""
    import csv, gzip
    from types import SimpleNamespace
    from nbapicks import pipeline
    idx, games = _data()
    h = tmp_path / "history"; h.mkdir()
    with gzip.open(h / "games_2023.csv.gz", "wt", newline="") as f:
        w = csv.DictWriter(f, ["game_id", "start_utc", "home", "away"]); w.writeheader()
        for gid, g in games.items():
            w.writerow(dict(game_id=gid, **g))
    rows = []
    for pid, gs in idx.logs.items():
        for g in gs:
            rows.append(dict(game_id=g.game_id, player_id=pid, player_name=idx.names[pid], team=g.team, minutes=g.minutes,
                             played=1, **{k: int(v) for k, v in g.stats.items()}))
    with gzip.open(h / "box_2023.csv.gz", "wt", newline="") as f:
        w = csv.DictWriter(f, list(rows[0])); w.writeheader(); w.writerows(rows)
    ctx = SimpleNamespace(root=str(tmp_path), today=dt.date(2023, 2, 1), store=SimpleNamespace(q=lambda *a, **k: []))
    mk = lambda sel: SimpleNamespace(market="prop", player_id="P1", stat="pts", line=25.5, selection=sel, price_dec=1.9,
                                     fair=0.5, home="BBB", away="AAA", game_id="gx", book="DraftKings", price_observed_at="t")
    cards = pipeline.prop_split_cards(ctx, [mk("over"), mk("side0")])
    assert len(cards) == 1 and cards[0]["ev"] is not None and cards[0]["opp"] == "BBB" and not cards[0]["home"]
    only_unverified = pipeline.prop_split_cards(ctx, [mk("side0")])
    assert only_unverified[0]["ev"] is None and only_unverified[0]["side"] == "over"


def test_card_book_status_and_calibrated_ev():
    idx, _ = _data()
    c = SC.card(idx, "P1", "pts", 25.5, "over", dt.date(2023, 2, 1), "BBB", False, price_dec=1.91, book="DraftKings")
    assert c["status"] == "research" and c["book"] == "DraftKings"
    assert c["prob"] == round(SC.calibrate(c["prob_raw"]), 4) and abs(c["prob"] - 0.5) < abs(c["prob_raw"] - 0.5)
    assert abs(c["ev"] - (c["prob"] * 1.91 - 1)) < 1e-3
    assert "@ DraftKings" in SC.card_text(c) and "[research]" in SC.card_text(c)


def test_teammate_with_without_split():
    idx, _ = _data()
    d = dt.date(2023, 2, 1)
    w = SC.split_counts(idx, "P1", "pts", 25.5, "over", d, "BBB", False, mates_status={"M1": True}, team="AAA")
    wo = SC.split_counts(idx, "P1", "pts", 25.5, "over", d, "BBB", False, mates_status={"M1": False}, team="AAA")
    assert w["with Mate"][1] == 24 and wo["without Mate"][1] == 6   # M1 sat games 0,5,...,25


def test_rest_split():
    idx, _ = _data()   # every game two days apart -> rest 1
    c = SC.split_counts(idx, "P1", "pts", 25.5, "over", dt.date(2022, 11, 1) + dt.timedelta(days=60), "CCC", True)
    assert c["rest 1 day"] == (15, 29)                 # first game has no previous game
    b2b = SC.split_counts(idx, "P1", "pts", 25.5, "over", dt.date(2022, 11, 1) + dt.timedelta(days=59), "CCC", True)
    assert "rest b2b" not in b2b                       # no b2b games in history -> split omitted


def test_swallowed_exception_and_traded_skip(monkeypatch, tmp_path):
    from types import SimpleNamespace
    from nbapicks import pipeline
    def boom(*a): raise RuntimeError("x")
    monkeypatch.setattr(pipeline, "prop_split_cards", boom)
    assert pipeline.safe_split_cards(SimpleNamespace(), []) == []
    monkeypatch.undo()
    idx, games = _data()
    monkeypatch.setattr(pipeline.SC, "build_index", lambda rows, g: idx)
    monkeypatch.setattr(pipeline.glob, "glob", lambda p: [])
    ctx = SimpleNamespace(root=str(tmp_path), today=dt.date(2023, 2, 1), store=SimpleNamespace(q=lambda *a, **k: []))
    c = SimpleNamespace(market="prop", player_id="P1", stat="pts", line=25.5, selection="over", price_dec=1.9, fair=0.5,
                        home="XXX", away="YYY", game_id="gx", book="DraftKings", price_observed_at="t")
    assert pipeline.prop_split_cards(ctx, [c]) == []   # P1's last team AAA plays in neither side: skipped


def test_tailcap_never_inflates_longshot():
    from nbapicks import splitcard as SC
    for p in (0.03, 0.1, 0.9, 0.97):
        c = SC.calibrate_tailcap(p, a=0.5, b=0.5)
        assert abs(c - 0.5) <= abs(p - 0.5) + 1e-12
    assert SC.calibrate_tailcap(0.5, a=0.0, b=0.8) == SC.calibrate(0.5, a=0.0, b=0.8)


def test_isotonic_monotone_and_pools():
    from nbapicks import splitcard as SC
    ps = [i / 100 for i in range(100)]
    ys = [1 if (i % 10 == 0) else 0 for i in range(50)] + [1 if i % 3 else 0 for i in range(50)]
    steps = SC.fit_isotonic(ps, ys, bins=10)
    rates = [r for _, r in steps]
    assert rates == sorted(rates)
    assert SC.apply_isotonic(0.0, steps) <= SC.apply_isotonic(0.99, steps)
    assert SC.apply_isotonic(5.0, steps) == min(rates[-1], 1 - 1e-4)
