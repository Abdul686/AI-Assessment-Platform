from __future__ import annotations

import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "aziro_assessments.db"


def get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with get_connection() as connection:
        connection.executescript(
            """
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
        )
