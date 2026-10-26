"""Small local SQLite store for SkinWise journal and routine adherence.

Only structured journal entries and completion events are stored. Photos and API keys are never stored here.
"""
import json
import os
import sqlite3
from pathlib import Path
from typing import Any

DEFAULT_DB = Path(os.getenv("SKINWISE_DB_PATH", "skinwise.db"))


def connect(db_path: str | Path | None = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else DEFAULT_DB
    if str(path) != ":memory:":
        path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("""CREATE TABLE IF NOT EXISTS journal (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entry_date TEXT NOT NULL,
        source TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS routine_checkins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        checkin_date TEXT NOT NULL,
        step_name TEXT NOT NULL,
        completed INTEGER NOT NULL CHECK (completed IN (0,1)),
        UNIQUE(checkin_date, step_name)
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS scans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scan_date TEXT NOT NULL,
        source TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS routines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        saved_date TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS user_profile (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        payload_json TEXT NOT NULL,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.commit()
    return conn


def add_journal_entry(entry: dict[str, Any], db_path: str | Path | None = None) -> None:
    with connect(db_path) as conn:
        conn.execute(
            "INSERT INTO journal(entry_date, source, payload_json) VALUES (?, ?, ?)",
            (str(entry.get("date", "")), str(entry.get("source", "Journal entry")), json.dumps(entry, ensure_ascii=False)),
        )


def get_journal_entries(db_path: str | Path | None = None, limit: int = 200) -> list[dict[str, Any]]:
    with connect(db_path) as conn:
        rows = conn.execute("SELECT payload_json FROM journal ORDER BY entry_date DESC, id DESC LIMIT ?", (limit,)).fetchall()
    return [json.loads(row["payload_json"]) for row in rows]


def clear_journal(db_path: str | Path | None = None) -> None:
    with connect(db_path) as conn:
        conn.execute("DELETE FROM journal")


def save_checkins(checkin_date: str, completed_steps: list[str], all_steps: list[str], db_path: str | Path | None = None) -> None:
    with connect(db_path) as conn:
        for step in all_steps:
            conn.execute(
                "INSERT INTO routine_checkins(checkin_date, step_name, completed) VALUES (?, ?, ?) "
                "ON CONFLICT(checkin_date, step_name) DO UPDATE SET completed=excluded.completed",
                (checkin_date, step, int(step in completed_steps)),
            )


def get_checkins(db_path: str | Path | None = None, limit: int = 90) -> list[dict[str, Any]]:
    with connect(db_path) as conn:
        rows = conn.execute(
            "SELECT checkin_date, step_name, completed FROM routine_checkins ORDER BY checkin_date DESC LIMIT ?", (limit * 10,)
        ).fetchall()
    return [dict(row) for row in rows]


def save_profile(profile: dict[str, Any], db_path: str | Path | None = None) -> None:
    """Save the single local onboarding profile for this app instance."""
    with connect(db_path) as conn:
        conn.execute(
            "INSERT INTO user_profile(id, payload_json) VALUES (1, ?) "
            "ON CONFLICT(id) DO UPDATE SET payload_json=excluded.payload_json, updated_at=CURRENT_TIMESTAMP",
            (json.dumps(profile, ensure_ascii=False),),
        )


def get_profile(db_path: str | Path | None = None) -> dict[str, Any]:
    with connect(db_path) as conn:
        row = conn.execute("SELECT payload_json FROM user_profile WHERE id=1").fetchone()
    return json.loads(row["payload_json"]) if row else {}


def clear_all_user_data(db_path: str | Path | None = None) -> None:
    """Delete all locally persisted journal entries and routine check-ins."""
    with connect(db_path) as conn:
        conn.execute("DELETE FROM journal")
        conn.execute("DELETE FROM routine_checkins")
        conn.execute("DELETE FROM scans")
        conn.execute("DELETE FROM routines")
        conn.execute("DELETE FROM user_profile")


def save_scan(scan: dict[str, Any], db_path: str | Path | None = None) -> None:
    with connect(db_path) as conn:
        conn.execute(
            "INSERT INTO scans(scan_date, source, payload_json) VALUES (?, ?, ?)",
            (str(scan.get("date", "")), str(scan.get("source", "YouCam")), json.dumps(scan, ensure_ascii=False)),
        )


def get_scans(db_path: str | Path | None = None, limit: int = 50) -> list[dict[str, Any]]:
    with connect(db_path) as conn:
        rows = conn.execute("SELECT payload_json FROM scans ORDER BY scan_date DESC, id DESC LIMIT ?", (limit,)).fetchall()
    return [json.loads(row["payload_json"]) for row in rows]


def save_routine(routine: dict[str, Any], db_path: str | Path | None = None) -> None:
    with connect(db_path) as conn:
        conn.execute(
            "INSERT INTO routines(saved_date, payload_json) VALUES (?, ?)",
            (str(routine.get("date", "")), json.dumps(routine, ensure_ascii=False)),
        )


def get_routines(db_path: str | Path | None = None, limit: int = 50) -> list[dict[str, Any]]:
    with connect(db_path) as conn:
        rows = conn.execute("SELECT payload_json FROM routines ORDER BY saved_date DESC, id DESC LIMIT ?", (limit,)).fetchall()
    return [json.loads(row["payload_json"]) for row in rows]
