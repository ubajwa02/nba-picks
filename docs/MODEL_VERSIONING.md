# Model versions, research ledger and rollback

- **Version stamp.** Every prediction stores its `model_version` (for example `ratings-v1-trend+props-v1`) and a content-based version id, so a rerun with the same inputs adds nothing and a changed estimate adds a new version. Old predictions are never edited; corrections are events in `pred_events`.
- **Champion.** `data/research/champion.json` names the live game model and the live prop model. Challengers run in `nba-research` (weekly) on the pre-registered validate window; the holdout is scored once per frozen candidate (`--holdout`).
- **Ledger.** `data/research/experiments.jsonl` holds every evaluation with its commit and gates result; `data/research/decisions.jsonl` holds every promotion, rejection and rollback with evidence and review. Recent example: the pace term was tried on validate and not adopted (2026-10-26).
- **Promotion.** Needs the gates in `config/gates.yaml` plus an independent review file under `team/reviews/`. Nothing promotes on its own.
- **Demotion.** The weekly job falls back from `props-v1` to `props-v0` automatically when live calibration error passes the gate.
- **Rollback by hand.** `python -m nbapicks.rollback props props-v0 --reason "why"` (or run the `nba-rollback` workflow from the Actions tab with the model and reason). It edits only `champion.json` and appends a decision; past predictions keep their original version.
- **Reproducing a prediction.** Check out the commit recorded on the experiment or the run, replay `data/ledger`, and run `python -m nbapicks.pipeline predict --now <run time>`.
