from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from database import get_conn
from models import TABLE_NAME

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[1] / "templates"))
router = APIRouter(tags=["summary"])

@router.get("/summary", response_class=HTMLResponse)
def summary(request: Request):
    from datetime import date, timedelta
today = date.today()
start = today - timedelta(days=6)
with get_conn() as conn:
    rows = conn.execute("SELECT mood FROM " + TABLE_NAME + " WHERE date >= ? AND date <= ? ORDER BY date ASC", (start.isoformat(), today.isoformat())).fetchall()
moods = [int(r[0]) for r in rows]
avg = round(sum(moods)/len(moods), 2) if moods else 0.0
# ASCII emoticons to avoid encoding issues on some consoles
emoji = ':D' if avg>=4.5 else (':)' if avg>=3.5 else (':|' if avg>=2.5 else (':(' if avg>=1.5 else ':/')))
count = len(moods)
    return templates.TemplateResponse("summary.html", {"request": request, "avg": avg, "count": count, "emoji": emoji})

@router.get("/api/summary", response_class=JSONResponse)
def api_summary():
    from datetime import date, timedelta
today = date.today()
start = today - timedelta(days=6)
with get_conn() as conn:
    rows = conn.execute("SELECT mood FROM " + TABLE_NAME + " WHERE date >= ? AND date <= ? ORDER BY date ASC", (start.isoformat(), today.isoformat())).fetchall()
moods = [int(r[0]) for r in rows]
avg = round(sum(moods)/len(moods), 2) if moods else 0.0
# ASCII emoticons to avoid encoding issues on some consoles
emoji = ':D' if avg>=4.5 else (':)' if avg>=3.5 else (':|' if avg>=2.5 else (':(' if avg>=1.5 else ':/')))
count = len(moods)
    return {"average": avg, "count": count, "emoji": emoji}
