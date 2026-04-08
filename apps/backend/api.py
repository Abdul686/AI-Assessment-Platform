from __future__ import annotations

import json
import os
import random
import secrets
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import yaml
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field

try:
    from .db import get_connection, get_database_path, init_db
    from .email_service import send_assignment_email
except ImportError:
    from db import get_connection, get_database_path, init_db
    from email_service import send_assignment_email


app = FastAPI(title="Aziro L&D Assessment API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIRS = [
    BASE_DIR.parent.parent / "data" / "assessments",
    BASE_DIR / "udemy_pipeline" / "Assessments_YAML",
]
DEFAULT_PUBLIC_TEST_BASE_URL = os.getenv(
    "PUBLIC_TEST_BASE_URL",
    "http://127.0.0.1:8000/take_test.html",
)
DEFAULT_API_PORT = int(os.getenv("API_PORT", "8011"))


class CandidateIn(BaseModel):
    name: str = Field(min_length=1)
    email: EmailStr
    employeeId: str = ""
    branch: str = ""


class TestConfigIn(BaseModel):
    questionType: str
    questionCount: int = Field(ge=1, le=100)
    timeLimit: int | None = Field(default=None, ge=1, le=600)
    aptitudeEnabled: str = ""
    difficultyLevel: str = ""
    sendMethod: str = ""
    linkExpiry: str = ""
    customMessage: str = ""


class TestCreateIn(BaseModel):
    course: str = Field(min_length=1)
    config: TestConfigIn
    candidates: list[CandidateIn] = Field(min_length=1)
    frontendBaseUrl: str | None = None


class SubmittedAnswerIn(BaseModel):
    questionId: int
    selectedAnswer: str | None = None


class SubmissionIn(BaseModel):
    answers: list[SubmittedAnswerIn]


def utc_now() -> datetime:
    return datetime.now(UTC)


def isoformat(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


def _list_assessment_files() -> list[Path]:
    files_by_name: dict[str, Path] = {}

    for data_dir in DATA_DIRS:
        if not data_dir.exists() or not data_dir.is_dir():
            continue

        for file_path in sorted(data_dir.glob("*.yaml")):
            files_by_name.setdefault(file_path.stem.lower(), file_path)

    return sorted(files_by_name.values(), key=lambda path: path.stem.lower())


def _find_course_file(course_name: str) -> Path | None:
    for file_path in _list_assessment_files():
        if file_path.stem.lower() == course_name.lower():
            return file_path
    return None


def _load_course_questions(course_name: str) -> list[dict[str, Any]]:
    selected_file = _find_course_file(course_name)
    if not selected_file:
        raise HTTPException(status_code=404, detail=f"Course not found: {course_name}")

    try:
        data = yaml.safe_load(selected_file.read_text(encoding="utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to parse YAML for {course_name}: {exc}")

    if not isinstance(data, list):
        raise HTTPException(status_code=400, detail="Invalid YAML format: expected a list of questions")

    valid_questions = []
    for item in data:
        if not isinstance(item, dict):
            continue
        question = item.get("question")
        options = item.get("options")
        correct_answer = item.get("correct_answer")
        if question and isinstance(options, dict) and correct_answer:
            valid_questions.append(item)

    if not valid_questions:
        raise HTTPException(status_code=404, detail="No valid MCQ entries found in this course")

    return valid_questions


def _expiry_to_datetime(label: str) -> datetime | None:
    normalized = (label or "").strip().lower()
    if normalized == "7 days":
        return utc_now() + timedelta(days=7)
    if normalized == "3 days":
        return utc_now() + timedelta(days=3)
    if normalized == "1 day":
        return utc_now() + timedelta(days=1)
    if normalized == "no expiry":
        return None
    return utc_now() + timedelta(days=7)


def _build_test_link(frontend_base_url: str | None, token: str) -> str:
    base = (frontend_base_url or DEFAULT_PUBLIC_TEST_BASE_URL).rstrip("?&")
    separator = "&" if "?" in base else "?"
    return f"{base}{separator}token={token}"


def _assignment_status(row: dict[str, Any]) -> str:
    expires_at = parse_iso(row.get("expires_at"))
    if row.get("submitted_at"):
        return "completed"
    if expires_at and utc_now() > expires_at:
        return "expired"
    if row.get("started_at"):
        return "started"
    return row.get("status") or "pending"


def _serialize_assignment(row: sqlite3.Row | dict[str, Any]) -> dict[str, Any]:
    data = dict(row)
    data["status"] = _assignment_status(data)
    return {
        "id": data["id"],
        "testId": data["test_id"],
        "candidateName": data["candidate_name"],
        "candidateEmail": data["candidate_email"],
        "employeeId": data["employee_id"],
        "branch": data["branch"],
        "token": data["token"],
        "testLink": data["test_link"],
        "expiresAt": data["expires_at"],
        "status": data["status"],
        "emailStatus": data["email_status"],
        "emailError": data["email_error"],
        "startedAt": data["started_at"],
        "submittedAt": data["submitted_at"],
        "score": data["score"],
        "totalQuestions": data["total_questions"],
        "percentage": data["percentage"],
        "createdAt": data["created_at"],
    }


def _serialize_test_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "courseName": row["course_name"],
        "questionType": row["question_type"],
        "questionCount": row["question_count"],
        "timeLimit": row["time_limit"],
        "aptitudeEnabled": row["aptitude_enabled"],
        "difficultyLevel": row["difficulty_level"],
        "sendMethod": row["send_method"],
        "linkExpiry": row["link_expiry"],
        "customMessage": row["custom_message"],
        "createdAt": row["created_at"],
        "status": row["status"],
    }


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "Aziro L&D Assessment API",
        "database": str(get_database_path().resolve()),
        "api_port": str(DEFAULT_API_PORT),
    }


@app.get("/api/courses")
def get_courses() -> dict[str, Any]:
    courses = [{"name": file_path.stem, "file": file_path.name} for file_path in _list_assessment_files()]
    return {"count": len(courses), "courses": courses}


@app.get("/api/questions")
def get_questions(
    course: str = Query(..., description="Course name (stem) from the assessments folder"),
    count: int = Query(15, ge=1, le=100),
) -> dict[str, Any]:
    questions = _load_course_questions(course)
    sample = random.sample(questions, min(len(questions), count))
    serialized = []
    for index, item in enumerate(sample, start=1):
        serialized.append(
            {
                "serial": index,
                "id": item.get("id"),
                "question": item.get("question"),
                "options": item.get("options"),
                "correct_answer": item.get("correct_answer"),
            }
        )

    return {
        "course": course,
        "requested_count": count,
        "available": len(questions),
        "questions": serialized,
    }


@app.post("/api/tests")
def create_test(payload: TestCreateIn) -> dict[str, Any]:
    available_questions = _load_course_questions(payload.course)
    required_question_count = 15
    if len(available_questions) < required_question_count:
        raise HTTPException(
            status_code=400,
            detail=(
                f"The selected course only has {len(available_questions)} valid MCQ questions. "
                f"At least {required_question_count} are required to create a test."
            ),
        )

    selected_questions = random.sample(
        available_questions,
        required_question_count,
    )
    created_at = utc_now()
    expires_at = _expiry_to_datetime(payload.config.linkExpiry)

    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO tests (
                course_name, question_type, question_count, time_limit, aptitude_enabled,
                difficulty_level, send_method, link_expiry, custom_message, created_at, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.course,
                "MCQ Only",
                required_question_count,
                payload.config.timeLimit,
                payload.config.aptitudeEnabled,
                payload.config.difficultyLevel,
                payload.config.sendMethod,
                payload.config.linkExpiry,
                payload.config.customMessage,
                isoformat(created_at),
                "created",
            ),
        )
        test_id = cursor.lastrowid

        for index, question in enumerate(selected_questions, start=1):
            cursor.execute(
                """
                INSERT INTO test_questions (
                    test_id, question_order, source_question_id, question_text, options_json, correct_answer
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    test_id,
                    index,
                    question.get("id"),
                    question.get("question"),
                    json.dumps(question.get("options", {})),
                    question.get("correct_answer"),
                ),
            )

        assignments = []
        for candidate in payload.candidates:
            token = secrets.token_urlsafe(24)
            test_link = _build_test_link(payload.frontendBaseUrl, token)
            email_status = "not_requested"
            email_error = None

            if "outlook" in payload.config.sendMethod.lower():
                email_result = send_assignment_email(
                    candidate_name=candidate.name,
                    candidate_email=str(candidate.email),
                    course_name=payload.course,
                    test_link=test_link,
                    expiry_label=payload.config.linkExpiry,
                    custom_message=payload.config.customMessage,
                )
                email_status = email_result.status
                email_error = email_result.error

            cursor.execute(
                """
                INSERT INTO test_assignments (
                    test_id, candidate_name, candidate_email, employee_id, branch, token,
                    test_link, expires_at, status, email_status, email_error, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    test_id,
                    candidate.name,
                    str(candidate.email),
                    candidate.employeeId,
                    candidate.branch,
                    token,
                    test_link,
                    isoformat(expires_at),
                    "pending",
                    email_status,
                    email_error,
                    isoformat(created_at),
                ),
            )
            assignment_id = cursor.lastrowid
            assignment_row = cursor.execute(
                "SELECT * FROM test_assignments WHERE id = ?",
                (assignment_id,),
            ).fetchone()
            assignments.append(_serialize_assignment(assignment_row))

        test_row = cursor.execute("SELECT * FROM tests WHERE id = ?", (test_id,)).fetchone()
        snapshot_rows = cursor.execute(
            "SELECT * FROM test_questions WHERE test_id = ? ORDER BY question_order",
            (test_id,),
        ).fetchall()

    return {
        "message": "Test created successfully.",
        "test": _serialize_test_row(test_row),
        "questionSnapshot": [
            {
                "id": row["id"],
                "order": row["question_order"],
                "sourceQuestionId": row["source_question_id"],
                "question": row["question_text"],
                "options": json.loads(row["options_json"]),
            }
            for row in snapshot_rows
        ],
        "assignments": assignments,
    }


@app.get("/api/tests")
def list_tests() -> dict[str, Any]:
    with get_connection() as connection:
        tests = connection.execute(
            "SELECT * FROM tests ORDER BY datetime(created_at) DESC, id DESC"
        ).fetchall()
        serialized_tests = []
        for test in tests:
            assignments = connection.execute(
                "SELECT * FROM test_assignments WHERE test_id = ? ORDER BY id DESC",
                (test["id"],),
            ).fetchall()
            serialized_tests.append(
                {
                    **_serialize_test_row(test),
                    "assignments": [_serialize_assignment(item) for item in assignments],
                }
            )
    return {"count": len(serialized_tests), "tests": serialized_tests}


@app.get("/api/tests/{test_id}")
def get_test(test_id: int) -> dict[str, Any]:
    with get_connection() as connection:
        test = connection.execute("SELECT * FROM tests WHERE id = ?", (test_id,)).fetchone()
        if not test:
            raise HTTPException(status_code=404, detail="Test not found")

        questions = connection.execute(
            "SELECT * FROM test_questions WHERE test_id = ? ORDER BY question_order",
            (test_id,),
        ).fetchall()
        assignments = connection.execute(
            "SELECT * FROM test_assignments WHERE test_id = ? ORDER BY id DESC",
            (test_id,),
        ).fetchall()

    return {
        "test": _serialize_test_row(test),
        "questions": [
            {
                "id": row["id"],
                "order": row["question_order"],
                "sourceQuestionId": row["source_question_id"],
                "question": row["question_text"],
                "options": json.loads(row["options_json"]),
            }
            for row in questions
        ],
        "assignments": [_serialize_assignment(item) for item in assignments],
    }


@app.get("/api/assignments/by-token/{token}")
def get_assignment_by_token(token: str) -> dict[str, Any]:
    with get_connection() as connection:
        assignment = connection.execute(
            "SELECT * FROM test_assignments WHERE token = ?",
            (token,),
        ).fetchone()
        if not assignment:
            raise HTTPException(status_code=404, detail="Invalid test link")

        test = connection.execute(
            "SELECT * FROM tests WHERE id = ?",
            (assignment["test_id"],),
        ).fetchone()
        questions = connection.execute(
            "SELECT * FROM test_questions WHERE test_id = ? ORDER BY question_order",
            (assignment["test_id"],),
        ).fetchall()

    assignment_data = _serialize_assignment(assignment)
    if assignment_data["status"] == "expired":
        raise HTTPException(status_code=410, detail="This test link has expired")

    return {
        "assignment": assignment_data,
        "test": {
            "id": test["id"],
            "courseName": test["course_name"],
            "questionType": test["question_type"],
            "timeLimit": test["time_limit"],
            "questionCount": test["question_count"],
            "aptitudeEnabled": test["aptitude_enabled"],
            "difficultyLevel": test["difficulty_level"],
        },
        "questions": [
            {
                "id": row["id"],
                "order": row["question_order"],
                "question": row["question_text"],
                "options": json.loads(row["options_json"]),
            }
            for row in questions
        ],
    }


@app.post("/api/assignments/by-token/{token}/start")
def start_assignment(token: str) -> dict[str, Any]:
    started_at = isoformat(utc_now())
    with get_connection() as connection:
        assignment = connection.execute(
            "SELECT * FROM test_assignments WHERE token = ?",
            (token,),
        ).fetchone()
        if not assignment:
            raise HTTPException(status_code=404, detail="Invalid test link")

        serialized = _serialize_assignment(assignment)
        if serialized["status"] == "expired":
            raise HTTPException(status_code=410, detail="This test link has expired")

        if not assignment["started_at"]:
            connection.execute(
                "UPDATE test_assignments SET started_at = ?, status = ? WHERE id = ?",
                (started_at, "started", assignment["id"]),
            )

        updated = connection.execute(
            "SELECT * FROM test_assignments WHERE id = ?",
            (assignment["id"],),
        ).fetchone()
    return {"assignment": _serialize_assignment(updated)}


@app.post("/api/assignments/by-token/{token}/submit")
def submit_assignment(token: str, payload: SubmissionIn) -> dict[str, Any]:
    submitted_at = isoformat(utc_now())

    with get_connection() as connection:
        assignment = connection.execute(
            "SELECT * FROM test_assignments WHERE token = ?",
            (token,),
        ).fetchone()
        if not assignment:
            raise HTTPException(status_code=404, detail="Invalid test link")

        serialized_assignment = _serialize_assignment(assignment)
        if serialized_assignment["status"] == "expired":
            raise HTTPException(status_code=410, detail="This test link has expired")
        if assignment["submitted_at"]:
            raise HTTPException(status_code=409, detail="This test has already been submitted")

        questions = connection.execute(
            "SELECT * FROM test_questions WHERE test_id = ? ORDER BY question_order",
            (assignment["test_id"],),
        ).fetchall()
        submitted_answers = {item.questionId: item.selectedAnswer for item in payload.answers}

        score = 0
        total_questions = len(questions)
        answer_rows = []

        for question in questions:
            selected_answer = submitted_answers.get(question["id"])
            is_correct = int((selected_answer or "").strip().upper() == question["correct_answer"].strip().upper())
            score += is_correct
            connection.execute(
                """
                INSERT INTO assignment_answers (
                    assignment_id, question_id, selected_answer, is_correct, submitted_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    assignment["id"],
                    question["id"],
                    selected_answer,
                    is_correct,
                    submitted_at,
                ),
            )
            answer_rows.append(
                {
                    "questionId": question["id"],
                    "selectedAnswer": selected_answer,
                    "correctAnswer": question["correct_answer"],
                    "isCorrect": bool(is_correct),
                }
            )

        percentage = round((score / total_questions) * 100, 2) if total_questions else 0.0
        connection.execute(
            """
            UPDATE test_assignments
            SET submitted_at = ?, status = ?, score = ?, total_questions = ?, percentage = ?
            WHERE id = ?
            """,
            (
                submitted_at,
                "completed",
                score,
                total_questions,
                percentage,
                assignment["id"],
            ),
        )
        updated_assignment = connection.execute(
            "SELECT * FROM test_assignments WHERE id = ?",
            (assignment["id"],),
        ).fetchone()

    return {
        "message": "Test submitted successfully.",
        "assignment": _serialize_assignment(updated_assignment),
        "result": {
            "score": score,
            "totalQuestions": total_questions,
            "percentage": percentage,
            "answers": answer_rows,
        },
    }


@app.get("/api/results")
def list_results() -> dict[str, Any]:
    with get_connection() as connection:
        completed_assignments = connection.execute(
            """
            SELECT ta.*, t.course_name
            FROM test_assignments ta
            JOIN tests t ON t.id = ta.test_id
            WHERE ta.submitted_at IS NOT NULL
            ORDER BY datetime(ta.submitted_at) DESC
            """
        ).fetchall()

    return {
        "count": len(completed_assignments),
        "results": [
            {
                **_serialize_assignment(row),
                "courseName": row["course_name"],
            }
            for row in completed_assignments
        ],
    }


@app.get("/api/results/{assignment_id}")
def get_result_detail(assignment_id: int) -> dict[str, Any]:
    with get_connection() as connection:
        assignment = connection.execute(
            """
            SELECT ta.*, t.course_name, t.question_type, t.time_limit, t.difficulty_level
            FROM test_assignments ta
            JOIN tests t ON t.id = ta.test_id
            WHERE ta.id = ?
            """,
            (assignment_id,),
        ).fetchone()
        if not assignment:
            raise HTTPException(status_code=404, detail="Result not found")
        if not assignment["submitted_at"]:
            raise HTTPException(status_code=400, detail="This test has not been submitted yet")

        answer_rows = connection.execute(
            """
            SELECT
                aa.question_id,
                aa.selected_answer,
                aa.is_correct,
                aa.submitted_at,
                tq.question_order,
                tq.question_text,
                tq.options_json,
                tq.correct_answer
            FROM assignment_answers aa
            JOIN test_questions tq ON tq.id = aa.question_id
            WHERE aa.assignment_id = ?
            ORDER BY tq.question_order
            """,
            (assignment_id,),
        ).fetchall()

    answers = []
    correct_count = 0
    for row in answer_rows:
        correct_count += int(row["is_correct"])
        options = json.loads(row["options_json"])
        answers.append(
            {
                "questionId": row["question_id"],
                "order": row["question_order"],
                "question": row["question_text"],
                "options": options,
                "selectedAnswer": row["selected_answer"],
                "selectedAnswerText": options.get(row["selected_answer"] or "", ""),
                "correctAnswer": row["correct_answer"],
                "correctAnswerText": options.get(row["correct_answer"] or "", ""),
                "isCorrect": bool(row["is_correct"]),
                "submittedAt": row["submitted_at"],
            }
        )

    total_questions = assignment["total_questions"] or len(answers)
    incorrect_count = max(total_questions - correct_count, 0)
    percentage = assignment["percentage"] or 0

    return {
        "assignment": _serialize_assignment(assignment),
        "test": {
            "id": assignment["test_id"],
            "courseName": assignment["course_name"],
            "questionType": assignment["question_type"],
            "timeLimit": assignment["time_limit"],
            "difficultyLevel": assignment["difficulty_level"],
        },
        "summary": {
            "score": assignment["score"],
            "totalQuestions": total_questions,
            "correctCount": correct_count,
            "incorrectCount": incorrect_count,
            "percentage": percentage,
            "status": "Pass" if percentage >= 60 else "Fail",
        },
        "answers": answers,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=DEFAULT_API_PORT, log_level="info")
