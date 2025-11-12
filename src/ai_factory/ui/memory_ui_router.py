from __future__ import annotations

from fastapi import APIRouter, Request, HTTPException, Path
from fastapi.templating import Jinja2Templates
from typing import List, Dict, Any

from ai_factory.memory.memory_agent import search_memories

templates = Jinja2Templates(directory="src/ai_factory/ui/templates")
router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

# UI router for /ui/memory
ui_router = APIRouter(prefix="/ui", tags=["UI"])


@ui_router.get("/memory")
def ui_memory_viewer(request: Request):
    """Simple memory viewer page using Tailwind CSS."""
    q = request.query_params.get("q", "")
    limit = int(request.query_params.get("limit") or 20)
    
    # Get memory entries
    results: List[Dict[str, Any]] = []
    stats = {}
    
    try:
        if q:
            results = search_memories(q, limit=limit)
        else:
            # Get recent memory entries from database
            from ai_factory.memory.memory_db import SessionLocal, MemoryEntry
            from sqlalchemy import desc, select
            with SessionLocal() as session:
                stmt = (
                    select(MemoryEntry)
                    .where(MemoryEntry.deleted == 0)
                    .order_by(desc(MemoryEntry.created_at))
                    .limit(limit)
                )
                rows = list(session.scalars(stmt))
                results = [
                    {
                        "id": r.id,
                        "goal": r.goal or "",
                        "summary": r.summary or "(no summary)",
                        "tags": r.tags or "",
                        "score": r.score,
                        "created_at": r.created_at.isoformat() if r.created_at else None,
                        "run_id": r.run_id,
                    }
                    for r in rows
                ]
        
        # Normalize tags
        for r in results:
            tags = r.get("tags") or ""
            if isinstance(tags, list):
                tags = ",".join([str(t).strip() for t in tags if str(t).strip()])
            r["tags"] = tags
            r["summary"] = r.get("summary") or "(no summary available)"
        
        # Get stats
        from ai_factory.memory.memory_agent import stats as memory_stats
        stats = memory_stats()
    except Exception as e:
        print(f"[ERROR] Memory viewer error: {e}")
        # Continue with empty results
    
    return templates.TemplateResponse(
        request,
        "memory.html",
        {
            "q": q,
            "limit": limit,
            "results": results,
            "stats": stats,
        },
    )


@router.get("/memory")
def memory_index(request: Request):
    q = request.query_params.get("q", "")
    limit = int(request.query_params.get("limit") or 20)
    results: List[Dict[str, Any]] = search_memories(q, limit=limit) if q else []
    # Normalize tags/summary for safety
    for r in results:
        tags = r.get("tags") or ""
        if isinstance(tags, list):
            tags = ",".join([str(t).strip() for t in tags if str(t).strip()])
        r["tags"] = tags
        r["summary"] = r.get("summary") or "(no summary available)"
    # Pull stats via API-level helper to avoid duplicate logic
    from ai_factory.memory.memory_agent import stats as memory_stats
    s = memory_stats()
    try:
        return templates.TemplateResponse(
            request,
            "dashboard/memory/index.html",
            {"q": q, "limit": limit, "results": results, "stats": s},
        )
    except Exception as e:
        print(f"[ERROR] Memory dashboard render: {e}")
        raise HTTPException(status_code=500, detail="Memory dashboard render failed")


@router.get("/memory/{id}")
def memory_detail(request: Request, id: int = Path(..., ge=1)):
    from ai_factory.memory.memory_db import SessionLocal, MemoryEntry
    with SessionLocal() as session:
        row = session.get(MemoryEntry, id)
        if not row or row.deleted:
            raise HTTPException(status_code=404, detail="not found")
        # Normalize tags/summary for safety
        tags = row.tags or ""
        entry = {
            "id": row.id,
            "run_id": row.run_id,
            "goal": row.goal,
            "summary": row.summary or "(no summary available)",
            "tags": tags,
            "score": row.score,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
    # Related via recall
    from ai_factory.memory.memory_agent import recall_for_run
    related = recall_for_run(row.run_id, limit=6) if row.run_id else []
    return templates.TemplateResponse(
        request,
        "dashboard/memory/detail.html",
        {"entry": entry, "related": related},
    )


@router.get("/memory/insights")
def memory_insights(request: Request):
    from ai_factory.memory.memory_agent import stats as memory_stats
    s = memory_stats()
    return templates.TemplateResponse(
        request,
        "dashboard/memory/insights.html",
        {"stats": s},
    )


@router.get("/memory/timeline")
def memory_timeline(request: Request):
    return templates.TemplateResponse(
        request,
        "dashboard/memory/timeline.html",
        {},
    )


@router.get("/memory/context/{run_id}")
def memory_context_preview(request: Request, run_id: int = Path(..., ge=1)):
    from ai_factory.memory.memory_agent import recall_for_run
    rows = recall_for_run(run_id, limit=3)
    return templates.TemplateResponse(
        request,
        "dashboard/memory/components/context_preview.html",
        {"items": rows, "run_id": run_id},
    )
