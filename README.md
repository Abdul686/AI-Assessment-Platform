# AI Assessment Platform

AI Assessment is a local web app for creating, managing, and reviewing training assessments for Udemy-based courses. It combines a FastAPI backend, a dashboard UI, and supporting scripts for syllabus extraction and MCQ generation.

## What's Inside

- `run.py` starts the app on a single local port and serves both the API and UI.
- `apps/backend/api.py` exposes the assessment API.
- `apps/frontend/dashboard` contains the web dashboard.
- `apps/backend/hiring_qs_gen` contains course syllabus and MCQ generation scripts.
- `data` and backend `data` folders store generated assets and assessment files.

## Requirements

- Python 3.10+ recommended
- A virtual environment is strongly recommended

## Install

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run the App

```powershell
python run.py
```

By default, the app starts on `http://127.0.0.1:8000/`.

To use a different port:

```powershell
python run.py --port 8001
```

## Available Pages

- Login
- Dashboard
- Create Test
- Review Test
- Take Test
- Generated Tests
- Evaluation
- Reports

## API

- Health check: `GET /api/health`
- Course list: `GET /api/courses`
- Assessment endpoints are exposed from the FastAPI backend.

## Course Content Generation

The backend includes utilities for scraping syllabus content and generating MCQs from course material:

- `apps/backend/hiring_qs_gen/Scrapper/fetch_syllabus.py`
- `apps/backend/hiring_qs_gen/Scrapper/updated_fetch.py`
- `apps/backend/hiring_qs_gen/generate_course_mcqs.py`

## Project Structure

```text
apps/
  backend/
  frontend/
data/
run.py
requirements.txt
```

## Notes

- If the UI directory is missing, `run.py` will stop with a clear error message.
- The app will reuse an already running instance if the requested port is busy.
- The frontend expects the backend health endpoint to be available at `/api/health`.
