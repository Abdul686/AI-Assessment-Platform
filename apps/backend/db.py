from __future__ import annotations

import os
import sqlite3
import tempfile
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
PRIMARY_DB_PATH = DATA_DIR / "aziro_assessments.db"
FALLBACK_DB_PATH = Path(tempfile.gettempdir()) / f"aziro_assessments_runtime_{os.getpid()}.db"
ENV_DB_PATH = "AZIRO_ASSESSMENTS_DB_PATH"
_ACTIVE_DB_PATH: Path | None = None

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS tests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_name TEXT NOT NULL,
    question_type TEXT NOT NULL,
    question_count INTEGER NOT NULL,
    time_limit INTEGER,
    aptitude_enabled TEXT,
    difficulty_level TEXT,
    send_method TEXT,
    link_expiry TEXT,
    custom_message TEXT,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'created'
);

CREATE TABLE IF NOT EXISTS test_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_id INTEGER NOT NULL,
    question_order INTEGER NOT NULL,
    source_question_id TEXT,
    question_text TEXT NOT NULL,
    options_json TEXT NOT NULL,
    correct_answer TEXT NOT NULL,
    FOREIGN KEY (test_id) REFERENCES tests(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS test_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_id INTEGER NOT NULL,
    candidate_name TEXT NOT NULL,
    candidate_email TEXT NOT NULL,
    employee_id TEXT,
    branch TEXT,
    token TEXT NOT NULL UNIQUE,
    test_link TEXT NOT NULL,
    expires_at TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    email_status TEXT NOT NULL DEFAULT 'not_requested',
    email_error TEXT,
    started_at TEXT,
    submitted_at TEXT,
    score INTEGER,
    total_questions INTEGER,
    percentage REAL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (test_id) REFERENCES tests(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS assignment_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assignment_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    selected_answer TEXT,
    is_correct INTEGER NOT NULL DEFAULT 0,
    submitted_at TEXT NOT NULL,
    FOREIGN KEY (assignment_id) REFERENCES test_assignments(id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES test_questions(id) ON DELETE CASCADE,
    UNIQUE (assignment_id, question_id)
);
"""


def _candidate_db_paths() -> list[Path]:
    override = os.getenv(ENV_DB_PATH)
    if override:
        return [Path(override).expanduser()]

    # If the primary DB has a leftover rollback journal, prefer the temp fallback.
    # This avoids startup on a DB file that may later fail on writes.
    journal_path = PRIMARY_DB_PATH.with_name(f"{PRIMARY_DB_PATH.name}-journal")
    if journal_path.exists():
        return [FALLBACK_DB_PATH, PRIMARY_DB_PATH]

    return [PRIMARY_DB_PATH, FALLBACK_DB_PATH]


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


def _set_active_db_path(db_path: Path) -> None:
    global _ACTIVE_DB_PATH
    _ACTIVE_DB_PATH = db_path


def _probe_writable(connection: sqlite3.Connection) -> None:
    # Validate that the selected SQLite file can actually handle writes.
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS __db_probe (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            marker TEXT NOT NULL
        )
        """
    )
    connection.execute("INSERT INTO __db_probe (marker) VALUES (?)", ("ok",))
    connection.execute("DELETE FROM __db_probe WHERE id = last_insert_rowid()")
    connection.commit()


def get_database_path() -> Path:
    if _ACTIVE_DB_PATH is not None:
        return _ACTIVE_DB_PATH

    override = os.getenv(ENV_DB_PATH)
    if override:
        return Path(override).expanduser()

    return PRIMARY_DB_PATH


def get_connection() -> sqlite3.Connection:
    if _ACTIVE_DB_PATH is None:
        init_db()
    return _connect(get_database_path())


def init_db() -> None:
    last_error: sqlite3.OperationalError | None = None

    for db_path in _candidate_db_paths():
        try:
            with _connect(db_path) as connection:
                connection.executescript(SCHEMA_SQL)
                _probe_writable(connection)
            _set_active_db_path(db_path)
            return
        except sqlite3.OperationalError as exc:
            last_error = exc

    if last_error is not None:
        raise last_error
