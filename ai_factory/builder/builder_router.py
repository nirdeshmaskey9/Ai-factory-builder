from __future__ import annotations

from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Path, Query

from ai_factory.builder.builder_agent import rebuild
from ai_factory.builder.builder_store import get_revision, get_recent


router = APIRouter(prefix="/builder", tags=["builder"])


@router.post("/rebuild")
def run(payload: Dict[str, Any]):
    ev_id = (payload or {}).get("evaluation_id")
    if not isinstance(ev_id, int):
        raise HTTPException(status_code=400, detail="evaluation_id must be an integer")
    try:
        return rebuild(ev_id)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))


@router.get("/status/{revision_id}")
def status(revision_id: int = Path(..., ge=1)):
    row = get_revision(revision_id)
    if not row:
        raise HTTPException(status_code=404, detail="revision not found")
    return {
        "revision_id": row.id,
        "evaluation_id": row.evaluation_id,
        "old_score": row.old_score,
        "new_score": row.new_score,
        "status": row.status,
        "timestamp": row.timestamp.isoformat() if row.timestamp else None,
        "notes": row.notes,
    }


@router.get("/history")
def history(limit: int = Query(10, ge=1, le=100)):
    rows = get_recent(limit=limit)
    return [
        {
            "revision_id": r.id,
            "evaluation_id": r.evaluation_id,
            "old_score": r.old_score,
            "new_score": r.new_score,
            "status": r.status,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
        }
        for r in rows
    ]

