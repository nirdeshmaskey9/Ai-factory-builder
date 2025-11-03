from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from ai_factory.memory.dialogue_store import list_summaries


templates = Jinja2Templates(directory="ai_factory/ui/templates")
router = APIRouter(prefix="/ui", tags=["UI"])


@router.get("/memory_peek")
def memory_peek_page(request: Request):
    items = list_summaries()
    return templates.TemplateResponse(request, "dashboard/memory_peek.html", {"items": items})


@router.get("/user_snapshot")
def get_user_snapshot():
    import json
    from pathlib import Path
    p = Path("data/user_snapshot.json")
    if p.exists():
        try:
            return JSONResponse(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            pass
    return JSONResponse({"name": "You", "mood": "neutral", "focus": "", "timezone": "UTC"})


@router.post("/user_snapshot")
def set_user_snapshot(request: Request):
    import json
    from pathlib import Path
    try:
        body = json.loads((request._body if hasattr(request, "_body") else None) or "{}")
    except Exception:
        body = {}
    p = Path("data")
    p.mkdir(exist_ok=True)
    Path("data/user_snapshot.json").write_text(json.dumps(body or {}), encoding="utf-8")
    return JSONResponse({"ok": True})

