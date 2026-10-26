import math, pytest
from nbapicks import metrics as M


def test_scores():
    assert M.brier([1, 0], [1, 0]) == 0
    assert M.brier([0.5, 0.5], [1, 0]) == 0.25
    assert M.log_loss([0.5], [1]) == pytest.approx(math.log(2))
    with pytest.raises(ValueError):
        M.brier([], [])


def test_calibration_bins():
    rows = M.calibration([0.15, 0.15, 0.85, 0.85], [0, 1, 1, 1], bins=10)
    assert [r["n"] for r in rows] == [2, 2]
    assert rows[1]["observed"] == 1.0 and rows[0]["predicted"] == pytest.approx(0.15)
    lo, hi = M.wilson(5, 10)
    assert lo < 0.5 < hi


def test_roi_and_drawdown():
    nets = [0.91, -1, 0.91, -1, -1, 0.91]
    s = M.roi_summary(nets)
    assert s["n"] == 6 and s["roi"] == pytest.approx(sum(nets) / 6)
    assert s["roi_ci"][0] < s["roi"] < s["roi_ci"][1]
    d = M.drawdown(nets)
    assert d["longest_losing_streak"] == 2 and d["max_drawdown"] == pytest.approx(-2.09)
    assert M.roi_summary([])["roi"] is None


def test_noise_floor():
    assert M.noise_floor(40) == pytest.approx(2.716, abs=1e-3)
