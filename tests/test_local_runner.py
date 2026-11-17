"""ops/local/nba_local.py: picks the right nba-daily slot in US Eastern time, once per slot."""
import importlib.util
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
spec = importlib.util.spec_from_file_location("nba_local", Path(__file__).parents[1] / "ops" / "local" / "nba_local.py")
nl = importlib.util.module_from_spec(spec); spec.loader.exec_module(nl)


def at(*a):
    return datetime(*a, tzinfo=ET)


def test_weekday_picks_slot_and_once_only():
    now = at(2026, 11, 10, 16, 45)                       # Tuesday
    _, key, steps = nl.due(now, set())
    assert key == "2026-11-10:picks-1630" and "publish" in steps and "leans" in steps
    assert nl.due(now, {key}) is None or nl.due(now, {key})[1] != key


def test_weekend_picks_at_11():
    _, key, steps = nl.due(at(2026, 11, 14, 11, 10), set())   # Saturday
    assert key == "2026-11-14:picks-1100" and "publish" in steps


def test_late_night_grading_and_results():
    assert nl.due(at(2026, 11, 10, 23, 40), set())[1] == "2026-11-10:grade-2330"
    _, key, steps = nl.due(at(2026, 11, 11, 3, 5), set())
    assert key == "2026-11-11:results-0300" and "recap" in steps and "publish" not in steps


def test_nothing_due_between_slots_or_too_late():
    assert nl.due(at(2026, 11, 10, 14, 30), set()) is None   # 11:00 slot is 3.5 h old: out of window
    assert nl.due(at(2026, 11, 10, 13, 0), {"2026-11-10:morning-1100"}) is None
