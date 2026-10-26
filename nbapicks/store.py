"""The audit ledger.

Source of truth: append-only JSON Lines files under data/ledger/, committed to
git by every scheduled run. git history is the backup and the tamper record.
At start-up the files are replayed into an in-memory SQLite database whose
schema (below, versioned by MIGRATIONS) enforces primary keys, uniqueness and
foreign keys. Every write is checked against SQLite first and only then
appended to its file, so a record that breaks a constraint never reaches disk.

Immutable tables (predictions, wagers, signals_raw, odds, injuries,
publications' first attempt) refuse a second, different record with the same
id; re-sending an identical record is a no-op (idempotent ingestion).
Changes to a prediction are new rows in pred_events, never edits.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from typing import Any, Iterable

MIGRATIONS: list[str] = [
    # v1
    """
    CREATE TABLE games (
        game_id TEXT PRIMARY KEY, season INTEGER, season_type TEXT, start_utc TEXT NOT NULL,
        home TEXT NOT NULL, away TEXT NOT NULL, home_id TEXT, away_id TEXT,
        status TEXT NOT NULL, home_score INTEGER, away_score INTEGER,
        observed_at TEXT NOT NULL, source TEXT NOT NULL
    );
    CREATE TABLE odds (
        snap_id TEXT PRIMARY KEY, game_id TEXT NOT NULL REFERENCES games(game_id),
        market TEXT NOT NULL CHECK (market IN ('ml','spread','total','prop')),
        selection TEXT NOT NULL, line REAL, player_id TEXT, player_name TEXT, stat TEXT,
        price_dec REAL CHECK (price_dec IS NULL OR price_dec > 1), book TEXT NOT NULL, source TEXT NOT NULL,
        kind TEXT NOT NULL CHECK (kind IN ('current','open','close')),
        observed_at TEXT NOT NULL, source_updated_at TEXT, suspended INTEGER,
        flags TEXT
    );
    CREATE INDEX odds_game ON odds(game_id, market, book);
    CREATE TABLE injuries (
        obs_id TEXT PRIMARY KEY, player_id TEXT, player_name TEXT NOT NULL, team TEXT,
        status TEXT NOT NULL, detail TEXT, source_date TEXT, observed_at TEXT NOT NULL, source TEXT NOT NULL
    );
    CREATE TABLE player_games (
        game_id TEXT NOT NULL REFERENCES games(game_id), player_id TEXT NOT NULL, player_name TEXT,
        team TEXT, starter INTEGER, minutes REAL, pts INTEGER, reb INTEGER, ast INTEGER,
        fg3m INTEGER, stl INTEGER, blk INTEGER, tov INTEGER, played INTEGER NOT NULL,
        observed_at TEXT NOT NULL, PRIMARY KEY (game_id, player_id)
    );
    CREATE TABLE predictions (
        pred_id TEXT PRIMARY KEY, created_at TEXT NOT NULL,
        origin TEXT NOT NULL CHECK (origin IN ('model','signal','backtest')),
        provider TEXT NOT NULL, model_version TEXT,
        category TEXT NOT NULL CHECK (category IN ('straight','parlay','lotto')),
        game_id TEXT REFERENCES games(game_id), market TEXT, selection TEXT, line REAL,
        player_id TEXT, player_name TEXT, stat TEXT,
        price_dec REAL, book TEXT, price_observed_at TEXT, price_source TEXT,
        prob REAL CHECK (prob IS NULL OR (prob >= 0 AND prob <= 1)), prob_push REAL, ev REAL, edge_threshold REAL,
        min_price_dec REAL, decision TEXT NOT NULL CHECK (decision IN ('eligible','watch','hold','reject','info')),
        reason TEXT NOT NULL, stake_units REAL, legs TEXT, inputs TEXT, run_id TEXT
    );
    CREATE INDEX pred_game ON predictions(game_id);
    CREATE TABLE pred_events (
        event_id TEXT PRIMARY KEY, pred_id TEXT NOT NULL REFERENCES predictions(pred_id),
        at TEXT NOT NULL, type TEXT NOT NULL CHECK (type IN ('published','settled','corrected','note')),
        result TEXT, net_units REAL, data TEXT
    );
    CREATE TABLE publications (
        pub_id TEXT PRIMARY KEY, kind TEXT NOT NULL, slate_date TEXT NOT NULL, at TEXT NOT NULL,
        status TEXT NOT NULL CHECK (status IN ('dry_run','sent','failed')),
        message_sha TEXT NOT NULL, detail TEXT
    );
    CREATE TABLE wagers (
        wager_id TEXT PRIMARY KEY, pred_id TEXT REFERENCES predictions(pred_id), placed_at TEXT NOT NULL,
        book TEXT NOT NULL, game_id TEXT REFERENCES games(game_id), market TEXT NOT NULL, selection TEXT NOT NULL,
        line REAL, player_id TEXT, stat TEXT, price_dec REAL NOT NULL CHECK (price_dec > 1),
        stake REAL NOT NULL CHECK (stake > 0), units REAL, legs TEXT, notes TEXT, confirmed_by TEXT NOT NULL
    );
    CREATE TABLE wager_events (
        event_id TEXT PRIMARY KEY, wager_id TEXT NOT NULL REFERENCES wagers(wager_id), at TEXT NOT NULL,
        type TEXT NOT NULL CHECK (type IN ('settled','corrected','void','cashout')), result TEXT, net REAL, data TEXT
    );
    CREATE TABLE signals_raw (
        raw_id TEXT PRIMARY KEY, provider TEXT NOT NULL, posted_at TEXT NOT NULL, text TEXT NOT NULL,
        channel TEXT, parse_status TEXT NOT NULL, parse_error TEXT, pred_ids TEXT, imported_at TEXT NOT NULL
    );
    CREATE TABLE audit (
        audit_id TEXT PRIMARY KEY, at TEXT NOT NULL, actor TEXT NOT NULL, action TEXT NOT NULL, data TEXT
    );
    """,
    # v2 (2026-10-22): box-score shot volume and plus-minus. Nullable, so ledger rows written
    # before v2 replay unchanged.
    """
    ALTER TABLE player_games ADD COLUMN fga INTEGER;
    ALTER TABLE player_games ADD COLUMN fg3a INTEGER;
    ALTER TABLE player_games ADD COLUMN fta INTEGER;
    ALTER TABLE player_games ADD COLUMN oreb INTEGER;
    ALTER TABLE player_games ADD COLUMN dreb INTEGER;
    ALTER TABLE player_games ADD COLUMN plus_minus INTEGER;
    """,
]

# table -> (primary key columns, immutable?)
TABLES: dict[str, tuple[tuple[str, ...], bool]] = {
    "games": (("game_id",), False),
    "odds": (("snap_id",), True),
    "injuries": (("obs_id",), True),
    "player_games": (("game_id", "player_id"), False),
    "predictions": (("pred_id",), True),
    "pred_events": (("event_id",), True),
    "publications": (("pub_id",), False),
    "wagers": (("wager_id",), True),
    "wager_events": (("event_id",), True),
    "signals_raw": (("raw_id",), True),
    "audit": (("audit_id",), True),
}
# ledger files that are partitioned by month of a timestamp column
# (predictions since 2026-10-22: every candidate is recorded and versioned, so the file grows daily;
# rows written before then stay in the legacy flat file predictions.jsonl, which is still replayed)
PARTITIONED = {"odds": "observed_at", "injuries": "observed_at", "predictions": "created_at"}
# replay order respects foreign keys
ORDER = ["games", "player_games", "odds", "injuries", "predictions", "pred_events",
         "publications", "wagers", "wager_events", "signals_raw", "audit"]


class LedgerError(Exception):
    pass


def stable_id(*parts: Any, n: int = 16) -> str:
    raw = json.dumps(parts, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()[:n]


class Store:
    def __init__(self, root: str | None):
        """root=None gives a purely in-memory store (tests, backtests)."""
        self.root = root
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys = ON")
        for m in MIGRATIONS:
            self.db.executescript(m)
        self.db.execute(f"PRAGMA user_version = {len(MIGRATIONS)}")
        self._cols = {t: [r[1] for r in self.db.execute(f"PRAGMA table_info({t})")] for t in TABLES}
        self.appended = 0
        self.repairs: list[str] = []
        if root:
            self._replay()

    # ---- persistence -------------------------------------------------
    def _path(self, table: str, rec: dict) -> str:
        d = os.path.join(self.root, "ledger")
        if table in PARTITIONED:
            month = str(rec.get(PARTITIONED[table]) or "unknown")[:7]
            return os.path.join(d, table, f"{month}.jsonl")
        return os.path.join(d, f"{table}.jsonl")

    def _files(self, table: str) -> list[str]:
        d = os.path.join(self.root, "ledger")
        if table in PARTITIONED:
            sub = os.path.join(d, table)
            legacy = os.path.join(d, f"{table}.jsonl")
            return ([legacy] if os.path.exists(legacy) else []) + \
                (sorted(os.path.join(sub, f) for f in os.listdir(sub) if f.endswith(".jsonl")) if os.path.isdir(sub) else [])
        p = os.path.join(d, f"{table}.jsonl")
        return [p] if os.path.exists(p) else []

    def _replay(self) -> None:
        for t in ORDER:
            for path in self._files(t):
                self._repair_tail(path)
                with open(path) as fh:
                    for i, line in enumerate(fh, 1):
                        if not line.strip():
                            continue
                        try:
                            self._apply(t, json.loads(line))
                        except Exception as e:
                            raise LedgerError(f"{path}:{i}: {e}") from e
        # commit, so a later failed put() rolls back only its own row, never the replayed ledger
        self.db.commit()

    def _repair_tail(self, path: str) -> None:
        """A run killed mid-append can leave a last line without its newline. If that line
        is valid JSON, finish it; if not, drop it (it was never committed) and say so."""
        with open(path, "rb") as fh:
            data = fh.read()
        if not data or data.endswith(b"\n"):
            return
        cut = data.rfind(b"\n") + 1
        try:
            json.loads(data[cut:])
            fixed = data + b"\n"
        except ValueError:
            fixed = data[:cut]
            self.repairs.append(f"{path}: dropped truncated last line")
        with open(path, "wb") as fh:
            fh.write(fixed)

    # ---- writes ------------------------------------------------------
    def _apply(self, table: str, rec: dict) -> str:
        """Apply to SQLite. Returns 'new', 'same' or 'updated'."""
        pk, immutable = TABLES[table]
        cols = self._cols[table]
        unknown = set(rec) - set(cols)
        if unknown:
            raise LedgerError(f"{table}: unknown columns {sorted(unknown)}")
        row = {c: _enc(rec.get(c)) for c in cols}
        where = " AND ".join(f"{k} = ?" for k in pk)
        old = self.db.execute(f"SELECT * FROM {table} WHERE {where}", [row[k] for k in pk]).fetchone()
        if old is not None:
            if all(old[c] == row[c] for c in cols):
                return "same"
            if immutable:
                raise LedgerError(f"{table} {[row[k] for k in pk]} is immutable; write an event instead")
            sets = ", ".join(f"{c} = ?" for c in cols)
            self.db.execute(f"UPDATE {table} SET {sets} WHERE {where}", [row[c] for c in cols] + [row[k] for k in pk])
            return "updated"
        q = ", ".join("?" for _ in cols)
        self.db.execute(f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({q})", [row[c] for c in cols])
        return "new"

    def put(self, table: str, rec: dict) -> str:
        """Validate, apply and (if it changed anything) append to the ledger file."""
        with self.db:  # transaction: roll back SQLite if the append fails
            outcome = self._apply(table, rec)
            if outcome != "same" and self.root:
                path = self._path(table, rec)
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "a") as fh:
                    fh.write(json.dumps({k: rec.get(k) for k in self._cols[table] if rec.get(k) is not None},
                                        sort_keys=True, default=str) + "\n")
                self.appended += 1
        return outcome

    def put_many(self, table: str, recs: Iterable[dict]) -> dict[str, int]:
        out = {"new": 0, "same": 0, "updated": 0}
        for r in recs:
            out[self.put(table, r)] += 1
        return out

    # ---- reads -------------------------------------------------------
    def q(self, sql: str, params: Iterable = ()) -> list[dict]:
        return [dict(r) for r in self.db.execute(sql, list(params))]

    def one(self, sql: str, params: Iterable = ()) -> dict | None:
        r = self.db.execute(sql, list(params)).fetchone()
        return dict(r) if r else None


def _enc(v: Any) -> Any:
    if isinstance(v, (dict, list)):
        return json.dumps(v, sort_keys=True, default=str)
    if isinstance(v, bool):
        return int(v)
    return v
