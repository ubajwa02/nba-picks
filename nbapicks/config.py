"""Load and validate config/nbapicks.yaml. Invalid settings stop the run."""
from __future__ import annotations

import yaml

STATUSES = ("research", "paper", "live")


class ConfigError(Exception):
    pass


def load(path: str = "config/nbapicks.yaml") -> dict:
    with open(path) as fh:
        c = yaml.safe_load(fh)
    validate(c)
    return c


def validate(c: dict) -> None:
    errs = []
    for k in ("straight", "parlay", "lotto"):
        v = c.get("stakes", {}).get(k)
        if not isinstance(v, (int, float)) or v <= 0 or v > 5:
            errs.append(f"stakes.{k} must be in (0, 5], got {v!r}")
        t = c.get("targets", {}).get(k)
        if not isinstance(t, int) or t < 0 or t > 10:
            errs.append(f"targets.{k} must be an integer 0-10, got {t!r}")
    if c.get("stakes", {}).get("parlay", 0) > c.get("stakes", {}).get("straight", 0):
        errs.append("stakes.parlay must not exceed stakes.straight")
    if c.get("stakes", {}).get("lotto", 0) > c.get("stakes", {}).get("parlay", 0):
        errs.append("stakes.lotto must not exceed stakes.parlay")
    for m, s in (c.get("markets") or {}).items():
        if s.get("status") not in STATUSES:
            errs.append(f"markets.{m}.status must be one of {STATUSES}")
        if not (0 <= float(s.get("min_ev", -1)) <= 0.5):
            errs.append(f"markets.{m}.min_ev must be in [0, 0.5]")
    r = c.get("risk", {})
    for k in ("max_units_per_game", "max_units_per_day", "max_parlay_units_per_day", "max_lotto_units_per_day"):
        if not isinstance(r.get(k), (int, float)) or r[k] <= 0:
            errs.append(f"risk.{k} must be > 0")
    q = c.get("quality", {})
    for k in ("max_odds_age_minutes", "max_model_market_gap", "max_ev"):
        if not isinstance(q.get(k), (int, float)) or q[k] <= 0:
            errs.append(f"quality.{k} must be > 0")
    missing = {"ml", "spread", "total", "prop", "parlay", "lotto"} - set(c.get("markets") or {})
    if missing:
        errs.append(f"markets is missing {sorted(missing)}")
    for k in ("min_minutes_before_tip", "key_player_min_minutes"):
        if not isinstance(q.get(k), (int, float)) or q[k] < 0:
            errs.append(f"quality.{k} must be a number >= 0")
    if not isinstance(q.get("unresolved_statuses"), list):
        errs.append("quality.unresolved_statuses must be a list")
    try:
        from zoneinfo import ZoneInfo
        ZoneInfo(str(c.get("timezone")))
    except Exception:
        errs.append(f"timezone {c.get('timezone')!r} is not a known time zone")
    rb = (c.get("execution") or {}).get("reference_books")
    if not isinstance(rb, list) or not rb:
        errs.append("execution.reference_books must be a non-empty list")
    pub = c.get("publishing", {})
    if not isinstance(pub.get("publish_paper"), bool):
        errs.append("publishing.publish_paper must be true or false")
    if not isinstance(pub.get("max_prediction_age_minutes"), (int, float)) or pub["max_prediction_age_minutes"] <= 0:
        errs.append("publishing.max_prediction_age_minutes must be > 0")
    if not isinstance(c.get("publishing", {}).get("dry_run"), bool):
        errs.append("publishing.dry_run must be true or false")
    if "http" in str(c.get("publishing", {}).get("webhook_secret", "")):
        errs.append("publishing.webhook_secret is the NAME of a secret, never the URL")
    if errs:
        raise ConfigError("; ".join(errs))
