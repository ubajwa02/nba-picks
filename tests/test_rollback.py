import datetime as dt
import json

import pytest

from nbapicks.rollback import rollback

NOW = dt.datetime(2026, 10, 26, 20, 0, tzinfo=dt.timezone.utc)


def files(tmp_path):
    ch = tmp_path / "champion.json"
    ch.write_text(json.dumps({"model_id": "ratings-v1-trend", "since": "2026-10-20", "props": {"model_id": "props-v1", "since": "2026-10-22"}}))
    return str(ch), str(tmp_path / "decisions.jsonl")


def test_props_rollback_updates_champion_and_records_the_decision(tmp_path):
    ch, dec = files(tmp_path)
    r = rollback("props", "props-v0", "calibration drifted", ch, dec, NOW)
    assert r == dict(changed=True, model_id="props-v0", previous="props-v1")
    doc = json.load(open(ch))
    assert doc["props"]["model_id"] == "props-v0" and doc["props"]["since"] == "2026-10-26" and doc["model_id"] == "ratings-v1-trend"
    rec = json.loads(open(dec).read())
    assert rec["decision"] == "props model props-v1 -> props-v0" and rec["evidence"] == "calibration drifted"


def test_rollback_to_the_current_model_changes_nothing(tmp_path):
    ch, dec = files(tmp_path)
    assert rollback("props", "props-v1", "x", ch, dec, NOW)["changed"] is False
    assert not (tmp_path / "decisions.jsonl").exists()


def test_unknown_model_and_missing_reason_are_refused(tmp_path):
    ch, dec = files(tmp_path)
    with pytest.raises(ValueError):
        rollback("props", "props-v9", "x", ch, dec, NOW)
    with pytest.raises(ValueError):
        rollback("games", "ratings-v1", " ", ch, dec, NOW)
