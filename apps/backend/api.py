from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import random
import yaml

app = FastAPI(title="Aziro-L&D Course Questions API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "assessments"


def _list_assessment_files():
    if not DATA_DIR.exists() or not DATA_DIR.is_dir():
        return []
    return sorted(DATA_DIR.glob("*.yaml"))


@app.get("/api/courses")
def get_courses():
    files = _list_assessment_files()
    courses = []
    for f in files:
        courses.append({
            "name": f.stem,
            "file": f.name,
        })
    return {"count": len(courses), "courses": courses}


@app.get("/api/questions")
def get_questions(course: str = Query(..., description="Course name (stem) from the assessments folder"), count: int = Query(15, ge=1, le=100)):
    selected_file = None
    for f in _list_assessment_files():
        if f.stem.lower() == course.lower():
            selected_file = f
            break
    if not selected_file:
        raise HTTPException(status_code=404, detail=f"Course not found: {course}")

    try:
        text = selected_file.read_text(encoding="utf-8")
        data = yaml.safe_load(text)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to parse YAML for {course}: {exc}")

    if not isinstance(data, list):
        raise HTTPException(status_code=400, detail="Invalid YAML format: expected a list of questions")

    mcq_items = [item for item in data if item.get("question") and item.get("options")]
    if not mcq_items:
        raise HTTPException(status_code=404, detail="No valid MCQ entries found in this course")

    sample = random.sample(mcq_items, min(len(mcq_items), count))
    for i, item in enumerate(sample, start=1):
        item["serial"] = i

    return {
        "course": course,
        "requested_count": count,
        "available": len(mcq_items),
        "questions": sample,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")