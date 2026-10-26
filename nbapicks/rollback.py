"""One-command model rollback.

    python -m nbapicks.rollback props props-v0 --reason "why"
    python -m nbapicks.rollback games ratings-v1 --reason "why"

Points the champion at an earlier model, records the decision, and changes nothing else.
Predictions already in the ledger keep the model version they were made with."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os

CHAMPION = "data/research/champion.json"
DECISIONS = "data/research/decisions.jsonl"
PROP_MODELS = ("props-v0", "props-v1")
GAME_MODELS = ("ratings-v1", "ratings-v1-trend")


def rollback(kind: str, model_id: str, reason: str, champion: str = CHAMPION, decisions: str = DECISIONS,
             now: dt.datetime | None = None) -> dict:
    known = PROP_MODELS if kind == "props" else GAME_MODELS if kind == "games" else None
    if known is None:
        raise ValueError("kind must be 'props' or 'games'")
    if model_id not in known:
        raise ValueError(f"unknown {kind} model {model_id!r}; choose from {', '.join(known)}")
    if not reason.strip():
        raise ValueError("a rollback needs a reason")
    now = now or dt.datetime.now(dt.timezone.utc)
    day = now.date().isoformat()
    doc = json.load(open(champion))
    old = (doc.get("props") or {}).get("model_id") if kind == "props" else doc.get("model_id")
    if old == model_id:
        return dict(changed=False, model_id=model_id)
    if kind == "props":
        doc["props"] = dict(model_id=model_id, since=day, experiment=None, reason=f"manual rollback from {old}: {reason}")
    else:
        doc.update(model_id=model_id, since=day, reason=f"manual rollback from {old}: {reason}")
    with open(champion, "w") as fh:
        json.dump(doc, fh, indent=1)
    os.makedirs(os.path.dirname(decisions), exist_ok=True)
    with open(decisions, "a") as fh:
        fh.write(json.dumps(dict(at=now.strftime("%Y-%m-%dT%H:%M:%SZ"), by="manual rollback", decision=f"{kind} model {old} -> {model_id}",
                                 evidence=reason, review="rollback needs no vote"), sort_keys=True) + "\n")
    return dict(changed=True, model_id=model_id, previous=old)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("kind", choices=("props", "games"))
    ap.add_argument("model_id")
    ap.add_argument("--reason", required=True)
    a = ap.parse_args(argv)
    print(rollback(a.kind, a.model_id, a.reason))


if __name__ == "__main__":
    main()
