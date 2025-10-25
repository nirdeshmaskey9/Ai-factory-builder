from __future__ import annotations

from fastapi import APIRouter, Request, HTTPException, Path
from fastapi.templating import Jinja2Templates
from typing import List, Dict, Any

from ai_factory.memory.memory_agent import search_memories

templates = Jinja2Templates(directory="ai_factory/ui/templates")
router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/memory")
def memory_index(request: Request):
    q = request.query_params.get("q", "")
    limit = int(request.query_params.get("limit") or 20)
    results: List[Dict[str, Any]] = search_memories(q, limit=limit) if q else []
    # Pull stats via API-level helper to avoid duplicate logic
    from ai_factory.memory.memory_agent import stats as memory_stats
    s = memory_stats()
    return templates.TemplateResponse(
        "dashboard/memory/index.html",
        {"request": request, "q": q, "limit": limit, "results": results, "stats": s},
    )


@router.get("/memory/{id}")
def memory_detail(request: Request, id: int = Path(..., ge=1)):
    from ai_factory.memory.memory_db import SessionLocal, MemoryEntry
    with SessionLocal() as session:
        row = session.get(MemoryEntry, id)
        if not row or row.deleted:
            raise HTTPException(status_code=404, detail="not found")
        entry = {
            "id": row.id,
            "run_id": row.run_id,
            "goal": row.goal,
            "summary": row.summary,
            "tags": row.tags,
            "score": row.score,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
    # Related via recall
    from ai_factory.memory.memory_agent import recall_for_run
    related = recall_for_run(row.run_id, limit=6) if row.run_id else []
    return templates.TemplateResponse(
        "dashboard/memory/detail.html",
        {"request": request, "entry": entry, "related": related},
    )

