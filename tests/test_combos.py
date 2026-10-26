from nbapicks import combos as C


def g(pts, reb, ast, minutes=30.0, played=1):
    return dict(pts=pts, reb=reb, ast=ast, minutes=minutes, played=played)


def test_pra_uses_the_players_own_joint_games():
    games = [g(20, 5, 5)] * 6 + [g(10, 2, 2)] * 6          # totals 30 and 14
    r = C.combo_probability(games, "pra", 20.5, "over")
    assert r["ok"] and r["n"] == 12 and r["prob"] == 0.5 and r["research_only"] and not r["priced"]


def test_push_is_split_out_and_sides_sum_to_one():
    games = [g(10, 5, 5)] * 5 + [g(8, 5, 5)] * 5          # totals 20 and 18
    over = C.combo_probability(games, "pra", 20, "over")
    under = C.combo_probability(games, "pra", 20, "under")
    assert over["prob_push"] == 0.5 and over["prob"] + under["prob"] + over["prob_push"] == 1


def test_thin_history_is_refused():
    r = C.combo_probability([g(20, 5, 5)] * 4, "pra", 20.5, "over")
    assert not r["ok"] and "need 10" in r["reason"]


def test_dnp_games_and_missing_stats_are_ignored():
    games = [g(20, 5, 5)] * 10 + [g(0, 0, 0, minutes=0, played=0), dict(pts=3, reb=None, ast=1, minutes=10, played=1)]
    assert C.combo_probability(games, "pra", 20.5, "over")["n"] == 10


def test_minutes_scaling_is_capped():
    games = [g(10, 5, 5, minutes=10)] * 10                  # 20 in 10 minutes
    assert C.combo_probability(games, "pra", 25, "over", expected_minutes=30)["mean"] == 30.0
