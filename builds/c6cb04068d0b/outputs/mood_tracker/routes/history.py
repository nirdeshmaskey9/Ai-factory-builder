from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from database import get_conn
from models import TABLE_NAME

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[1] / "templates"))
router = APIRouter(tags=["history"])

@router.get("/history", response_class=HTMLResponse)
def history(request: Request):
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM " + TABLE_NAME + " ORDER BY date DESC").fetchall()
    return templates.TemplateResponse("history.html", {"request": request, "rows": rows})
