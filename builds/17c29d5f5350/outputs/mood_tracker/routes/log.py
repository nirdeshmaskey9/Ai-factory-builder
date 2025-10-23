from fastapi import APIRouter, Form
from fastapi.responses import RedirectResponse
from ..database import get_conn
from ..models import TABLE_NAME

router = APIRouter(tags=["log"])

@router.post("/log")
def log_entry(mood: int = Form(...), note: str = Form('')):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO " + TABLE_NAME + " (date, mood, note) VALUES (date('now'), ?, ?)",
            [mood, note]
        )
        conn.commit()
    return RedirectResponse("/summary", status_code=303)

