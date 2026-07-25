"""Persistence: JSON snapshots for diffing + SQLite for history and dedupe."""
from __future__ import annotations

import json
import sqlite3
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from monitor.config import DB_PATH, SNAPSHOT_DIR


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def slug(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]


# ------------- SQLite init -------------
_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT,
    finished_at TEXT,
    total INTEGER,
    ok INTEGER,
    failed INTEGER,
    changed INTEGER
);
CREATE TABLE IF NOT EXISTS site_status (
    url TEXT PRIMARY KEY,
    name TEXT,
    last_ok_at TEXT,
    last_fail_at TEXT,
    last_error TEXT,
    consecutive_failures INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    detected_at TEXT,
    url TEXT,
    name TEXT,
    priority TEXT,
    change_type TEXT,
    summary TEXT,
    payload TEXT
);
CREATE TABLE IF NOT EXISTS alerts_sent (
    dedupe_key TEXT PRIMARY KEY,
    sent_at TEXT
);
CREATE TABLE IF NOT EXISTS digest_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    queued_at TEXT,
    url TEXT,
    name TEXT,
    priority TEXT,
    change_type TEXT,
    summary TEXT
);
"""


def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(_SCHEMA)
    conn.row_factory = sqlite3.Row
    return conn


# ------------- Snapshot IO -------------
def snapshot_path(url: str) -> Path:
    return SNAPSHOT_DIR / f"{slug(url)}.json"


def load_snapshot(url: str) -> Optional[dict]:
    p = snapshot_path(url)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def save_snapshot(url: str, data: dict) -> None:
    data = dict(data)
    data["_saved_at"] = _now_iso()
    snapshot_path(url).write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ------------- Site status -------------
def record_ok(url: str, name: str) -> None:
    with db() as conn:
        conn.execute(
            """INSERT INTO site_status(url, name, last_ok_at, consecutive_failures)
               VALUES(?, ?, ?, 0)
               ON CONFLICT(url) DO UPDATE SET
                 last_ok_at = excluded.last_ok_at,
                 name = excluded.name,
                 consecutive_failures = 0""",
            (url, name, _now_iso()),
        )


def record_fail(url: str, name: str, error: str) -> int:
    with db() as conn:
        cur = conn.execute(
            "SELECT consecutive_failures FROM site_status WHERE url=?", (url,)
        )
        row = cur.fetchone()
        streak = (row["consecutive_failures"] if row else 0) + 1
        conn.execute(
            """INSERT INTO site_status(url, name, last_fail_at, last_error, consecutive_failures)
               VALUES(?, ?, ?, ?, ?)
               ON CONFLICT(url) DO UPDATE SET
                 last_fail_at = excluded.last_fail_at,
                 last_error = excluded.last_error,
                 name = excluded.name,
                 consecutive_failures = excluded.consecutive_failures""",
            (url, name, _now_iso(), error[:500], streak),
        )
        return streak


# ------------- Changes + dedupe -------------
def record_change(
    url: str, name: str, priority: str, change_type: str, summary: str, payload: dict
) -> None:
    with db() as conn:
        conn.execute(
            """INSERT INTO changes(detected_at, url, name, priority, change_type, summary, payload)
               VALUES(?, ?, ?, ?, ?, ?, ?)""",
            (_now_iso(), url, name, priority, change_type, summary,
             json.dumps(payload, ensure_ascii=False)),
        )


def already_alerted(key: str) -> bool:
    with db() as conn:
        cur = conn.execute("SELECT 1 FROM alerts_sent WHERE dedupe_key=?", (key,))
        return cur.fetchone() is not None


def mark_alerted(key: str) -> None:
    with db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO alerts_sent(dedupe_key, sent_at) VALUES(?, ?)",
            (key, _now_iso()),
        )


# ------------- Digest queue -------------
def queue_for_digest(
    url: str, name: str, priority: str, change_type: str, summary: str
) -> None:
    with db() as conn:
        conn.execute(
            """INSERT INTO digest_queue(queued_at, url, name, priority, change_type, summary)
               VALUES(?, ?, ?, ?, ?, ?)""",
            (_now_iso(), url, name, priority, change_type, summary),
        )


def drain_digest() -> list[dict]:
    with db() as conn:
        rows = conn.execute(
            "SELECT * FROM digest_queue ORDER BY id"
        ).fetchall()
        items = [dict(r) for r in rows]
        conn.execute("DELETE FROM digest_queue")
        return items


# ------------- Runs -------------
def start_run() -> int:
    with db() as conn:
        cur = conn.execute(
            "INSERT INTO runs(started_at) VALUES(?)", (_now_iso(),)
        )
        return cur.lastrowid


def finish_run(run_id: int, total: int, ok: int, failed: int, changed: int) -> None:
    with db() as conn:
        conn.execute(
            """UPDATE runs SET finished_at=?, total=?, ok=?, failed=?, changed=?
               WHERE id=?""",
            (_now_iso(), total, ok, failed, changed, run_id),
        )


def health_report() -> dict:
    with db() as conn:
        last_run = conn.execute(
            "SELECT * FROM runs ORDER BY id DESC LIMIT 1"
        ).fetchone()
        statuses = conn.execute("SELECT * FROM site_status").fetchall()
        failing = [dict(r) for r in statuses if (r["consecutive_failures"] or 0) >= 3]
        recent_changes = conn.execute(
            "SELECT * FROM changes ORDER BY id DESC LIMIT 30"
        ).fetchall()
    return {
        "last_run": dict(last_run) if last_run else None,
        "failing_sites": failing,
        "recent_changes": [dict(r) for r in recent_changes],
        "all_statuses": [dict(r) for r in statuses],
    }
