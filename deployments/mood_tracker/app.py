from __future__ import annotations

import sqlite3
from pathlib import Path
from datetime import date, timedelta
from typing import List, Dict, Any

from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "mood.db"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS moods (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              date TEXT UNIQUE,
              mood INTEGER,
              note TEXT
            )
            """
        )


def get_conn() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


app = FastAPI(title="Daily Mood Tracker")
init_db()

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@app.get("/")
def index(request: Request):
    today = date.today().isoformat()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "today": today},
    )


@app.post("/log")
def log_mood(mood: int = Form(...), note: str = Form("")):
    d = date.today().isoformat()
    with get_conn() as conn:
        # Prevent duplicates per day; replace existing
        conn.execute(
            "INSERT INTO moods(date, mood, note) VALUES(?,?,?)\n"
            "ON CONFLICT(date) DO UPDATE SET mood=excluded.mood, note=excluded.note",
            (d, int(mood), note.strip()),
        )
    return RedirectResponse(url="/summary", status_code=303)


@app.get("/history")
def history(request: Request):
    with get_conn() as conn:
        rows = conn.execute("SELECT date, mood, note FROM moods ORDER BY date DESC").fetchall()
    items = [{"date": r[0], "mood": r[1], "note": r[2] or ""} for r in rows]
    return templates.TemplateResponse("history.html", {"request": request, "items": items})


def _weekly_average() -> Dict[str, Any]:
    today = date.today()
    start = today - timedelta(days=6)
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT mood FROM moods WHERE date >= ? AND date <= ? ORDER BY date ASC",
            (start.isoformat(), today.isoformat()),
        ).fetchall()
    moods: List[int] = [int(r[0]) for r in rows]
    avg = round(sum(moods) / len(moods), 2) if moods else 0.0
    return {"count": len(moods), "average": avg}


def _emoji(m: float) -> str:
    if m >= 4.5:
        return "😄"
    if m >= 3.5:
        return "🙂"
    if m >= 2.5:
        return "😐"
    if m >= 1.5:
        return "☹️"
    return "😔"


@app.get("/summary")
def summary(request: Request):
    stats = _weekly_average()
    data = {"average": stats["average"], "count": stats["count"], "emoji": _emoji(stats["average"]) }
    # Content negotiation: JSON if requested explicitly
    # Fast path: if no templates (headless), still return JSON
    try:
        return templates.TemplateResponse("summary.html", {"request": request, **data})
    except Exception:
        return JSONResponse(data)


@app.get("/api/summary")
def summary_json():
    stats = _weekly_average()
    return {"average": stats["average"], "count": stats["count"]}

