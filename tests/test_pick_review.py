from nbapicks import review as RV


def test_enrich_build_and_archive(tmp_path):
    lean = dict(slate="2026-10-21", label="A o9.5 pts", market="prop", stat="pts", source="split_card", result="win",
                net_units=0.9, prob=0.7, price_american=-110, game_id="g1", selection="over", line=9.5, player_id="p1")
    ml = dict(slate="2026-10-21", label="X ML", market="ml", stat=None, result="loss", net_units=-1.0, prob=0.6,
              price_american=100, game_id="g1", selection="home", line=None, player_id=None)
    pend = dict(ml, result="pending")
    games = {"g1": dict(start_utc="2026-10-21T23:00Z")}
    odds = [dict(game_id="g1", market="ml", selection="home", line=None, book="b", price_dec=1.8, observed_at="2026-10-21T22:00:00Z"),
            dict(game_id="g1", market="ml", selection="home", line=None, book="b", price_dec=1.5, observed_at="2026-10-22T01:00:00Z")]
    preds = [dict(game_id="g1", market="ml", selection="home", line=None, player_id=None, stat=None, created_at="t",
                  inputs='{"home_rest": 2, "away_rest": 1}', reason="unresolved injury: Y")]
    card = dict(game_id="g1", player_id="p1", player="A", stat="pts", side="over", line=9.5,
                splits=[dict(split="season", hits=1, n=2, rate=0.5), dict(split="career", hits=80, n=100, rate=0.8)])
    assert RV.archive_cards(str(tmp_path), [card, card]) == 1
    assert RV.archive_cards(str(tmp_path), [card]) == 0
    rows = RV.enrich([lean, ml, pend], preds, games, odds, RV.load_cards(str(tmp_path)))
    assert len(rows) == 2  # pending skipped
    m = next(r for r in rows if r["market"] == "ml")
    assert abs(m["clv"] - (1 / 1.8 - 0.5)) < 1e-3  # post-start quote ignored
    assert m["injury_flag"] and m["rest"] == [1, 2]
    p = next(r for r in rows if r["market"] == "prop")
    assert p["splits"]["season"] == "1/2" and p["small_sample"] and p["clv"] is None
    rev = RV.build(rows, dict(n=3, brier=dict(model=0.25, market=0.24, n=3)))
    assert rev["n"] == 2 and rev["groups"]["by_market"]["ml"]["losses"] == 1
    assert "tiny" in rev["note"] and any("Brier" in f for f in rev["findings"])
    assert "## 2026-10-21" in RV.markdown(rev, "2026-10-22")
