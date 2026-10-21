"""SQLite persistence for references, voice profiles and generation history."""
import json
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS reference_voices (
    id TEXT PRIMARY KEY,
    original_name TEXT NOT NULL,
    duration_s REAL NOT NULL,
    consent INTEGER NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS profiles (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE COLLATE NOCASE,
    reference_id TEXT REFERENCES reference_voices(id),
    settings TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS generations (
    id TEXT PRIMARY KEY,
    text TEXT NOT NULL,
    profile_id TEXT,
    profile_name TEXT,
    reference_id TEXT,
    settings TEXT NOT NULL,
    chunks INTEGER NOT NULL,
    duration_s REAL NOT NULL,
    gen_seconds REAL NOT NULL,
    device TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


class DuplicateNameError(ValueError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_id() -> str:
    return uuid.uuid4().hex


def is_valid_id(value: str) -> bool:
    try:
        return uuid.UUID(hex=value).hex == value
    except (ValueError, TypeError):
        return False


class Storage:
    def __init__(self, db_path: Path):
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        with self._lock, self._conn:
            self._conn.executescript(_SCHEMA)

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def _query(self, sql: str, params: tuple = ()) -> list[dict]:
        with self._lock:
            return [dict(r) for r in self._conn.execute(sql, params).fetchall()]

    def _execute(self, sql: str, params: tuple = ()) -> int:
        with self._lock, self._conn:
            return self._conn.execute(sql, params).rowcount

    # --- reference voices
    def add_reference(self, ref_id: str, original_name: str, duration_s: float) -> dict:
        self._execute(
            "INSERT INTO reference_voices VALUES (?, ?, ?, 1, ?)",
            (ref_id, original_name[:200], round(duration_s, 2), _now()),
        )
        return self.get_reference(ref_id)

    def get_reference(self, ref_id: str) -> dict | None:
        rows = self._query("SELECT * FROM reference_voices WHERE id = ?", (ref_id,))
        return rows[0] if rows else None

    def list_references(self) -> list[dict]:
        return self._query("SELECT * FROM reference_voices ORDER BY created_at DESC")

    # --- profiles
    @staticmethod
    def _profile(row: dict) -> dict:
        return {**row, "settings": json.loads(row["settings"])}

    def list_profiles(self) -> list[dict]:
        return [self._profile(r) for r in self._query("SELECT * FROM profiles ORDER BY name COLLATE NOCASE")]

    def get_profile(self, profile_id: str) -> dict | None:
        rows = self._query("SELECT * FROM profiles WHERE id = ?", (profile_id,))
        return self._profile(rows[0]) if rows else None

    def save_profile(self, profile_id: str | None, name: str, reference_id: str | None, settings: dict) -> dict:
        now = _now()
        try:
            if profile_id:
                self._execute(
                    "UPDATE profiles SET name = ?, reference_id = ?, settings = ?, updated_at = ? WHERE id = ?",
                    (name, reference_id, json.dumps(settings), now, profile_id),
                )
            else:
                profile_id = new_id()
                self._execute(
                    "INSERT INTO profiles VALUES (?, ?, ?, ?, ?, ?)",
                    (profile_id, name, reference_id, json.dumps(settings), now, now),
                )
        except sqlite3.IntegrityError as exc:
            raise DuplicateNameError(name) from exc
        return self.get_profile(profile_id)

    def delete_profile(self, profile_id: str) -> bool:
        return self._execute("DELETE FROM profiles WHERE id = ?", (profile_id,)) > 0

    # --- generations
    @staticmethod
    def _generation(row: dict) -> dict:
        return {**row, "settings": json.loads(row["settings"])}

    def add_generation(self, record: dict) -> dict:
        self._execute(
            "INSERT INTO generations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (record["id"], record["text"], record.get("profile_id"), record.get("profile_name"),
             record.get("reference_id"), json.dumps(record["settings"]), record["chunks"],
             round(record["duration_s"], 2), round(record["gen_seconds"], 1), record["device"], _now()),
        )
        return self.get_generation(record["id"])

    def get_generation(self, gen_id: str) -> dict | None:
        rows = self._query("SELECT * FROM generations WHERE id = ?", (gen_id,))
        return self._generation(rows[0]) if rows else None

    def list_generations(self, limit: int = 100) -> list[dict]:
        rows = self._query("SELECT * FROM generations ORDER BY created_at DESC, rowid DESC LIMIT ?", (limit,))
        return [self._generation(r) for r in rows]
